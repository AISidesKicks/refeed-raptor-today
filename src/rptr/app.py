"""FastAPI reader for the local RAG lab.

The first slice is model-free. It loads the place, indexes the corpus into
SQLite, and answers with the BM25 baseline. The endpoints are already shaped
for the model-backed pipeline: one ask path, one replay path, one eval path,
and a WebSocket for the interactive UI.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import tracing
from .config import Settings
from .eval import keyword_metrics, raptor_metrics
from .index import build_index
from .llm import LlamaRouter, RouterError
from .pipeline import PipelineConfig
from .pipeline import answer_question as raptor_answer
from .place import Place, discover_places
from .replay import has_recordings, recorded_turn, replay_turn
from .search import search_rows
from .store import (
    chunk_rows,
    connect,
    document,
    documents,
    embedding_count,
    place_detail,
    place_summaries,
    tree_nodes,
)


class AskRequest(BaseModel):
    place_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)
    mode: Literal["keyword", "raptor"] = "keyword"


def answer_keyword(
    settings: Settings,
    place_id: str,
    question: str,
    limit: int,
) -> dict[str, Any]:
    conn = connect(settings.database_path)
    try:
        if place_detail(conn, place_id) is None:
            raise HTTPException(status_code=404, detail=f"unknown place: {place_id}")
        hits = search_rows(chunk_rows(conn, place_id), question, limit=limit)
        if hits:
            top = hits[0]
            answer = (
                f"Keyword baseline found {len(hits)} passages. The top match is "
                f"{top.doc_title} ({top.doc_id}). The embedding retriever and the "
                "refeed loop are not loaded in this mode."
            )
        else:
            answer = (
                "Keyword baseline found no matching passages. "
                "Try a more specific question or a rare term from the corpus."
            )
        return {
            "place_id": place_id,
            "question": question,
            "mode": "keyword",
            "answer": answer,
            "results": [asdict(hit) for hit in hits],
            "note": "Model-free baseline. This is not the RAPTOR plus refeed answer.",
        }
    finally:
        conn.close()


def answer_raptor(
    app: FastAPI,
    settings: Settings,
    place_id: str,
    question: str,
    limit: int,
) -> dict[str, Any]:
    conn = connect(settings.database_path)
    try:
        detail = place_detail(conn, place_id)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"unknown place: {place_id}")
        place = getattr(app.state, "places", {}).get(place_id)
        if place is None:
            raise HTTPException(status_code=404, detail=f"unknown place: {place_id}")
        if embedding_count(conn, place_id, "chunk") == 0:
            raise HTTPException(
                status_code=409,
                detail="this place has no embeddings; run `pixi run embed` and `pixi run build-tree`",
            )
        router: LlamaRouter = app.state.router
        return raptor_answer(
            router,
            conn,
            place,
            question,
            PipelineConfig(evidence_limit=limit),
        )
    except RouterError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        conn.close()


def place_capabilities(
    conn, place_id: str, place: Place | None = None
) -> dict[str, bool]:
    return {
        "keyword": True,
        "raptor": embedding_count(conn, place_id, "chunk") > 0,
        "tree": len(tree_nodes(conn, place_id)) > 0,
        "recorded": bool(place is not None and has_recordings(place)),
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        build_index(settings)
        app.state.settings = settings
        app.state.places = {
            place.id: place for place in discover_places(settings.places_dir)
        }
        app.state.router = LlamaRouter()
        try:
            yield
        finally:
            app.state.router.close()

    app = FastAPI(title="Refeed Raptor", version="0.1.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    def place_or_404(place_id: str) -> Place:
        place = getattr(app.state, "places", {}).get(place_id)
        if place is None:
            raise HTTPException(status_code=404, detail=f"unknown place: {place_id}")
        return place

    @app.get("/", include_in_schema=False)
    def index_page() -> FileResponse:
        return FileResponse(settings.static_dir / "index.html")

    @app.get("/api/places")
    def list_places() -> list[dict[str, Any]]:
        conn = connect(settings.database_path)
        try:
            return place_summaries(conn)
        finally:
            conn.close()

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        try:
            status = app.state.router.health()
            models = app.state.router.models()
            return {
                "router": status,
                "models": models,
                "reachable": True,
                "otel": tracing.enabled(),
            }
        except RouterError as exc:
            return {
                "router": {"status": "down"},
                "models": [],
                "reachable": False,
                "error": str(exc),
                "otel": tracing.enabled(),
            }

    @app.get("/api/places/{place_id}")
    def get_place(place_id: str) -> dict[str, Any]:
        place = place_or_404(place_id)
        conn = connect(settings.database_path)
        try:
            detail = place_detail(conn, place_id)
            if detail is None:
                raise HTTPException(status_code=404, detail=f"unknown place: {place_id}")
            detail["capabilities"] = place_capabilities(conn, place_id, place)
        finally:
            conn.close()
        detail["starter_questions"] = list(place.starter_questions)
        detail["script"] = [asdict(turn) for turn in place.script]
        detail["models"] = place.models
        return detail

    @app.get("/api/places/{place_id}/documents")
    def list_documents(place_id: str) -> list[dict[str, Any]]:
        place_or_404(place_id)
        conn = connect(settings.database_path)
        try:
            return documents(conn, place_id)
        finally:
            conn.close()

    @app.get("/api/places/{place_id}/documents/{doc_id}")
    def get_document(place_id: str, doc_id: str) -> dict[str, Any]:
        place_or_404(place_id)
        conn = connect(settings.database_path)
        try:
            row = document(conn, place_id, doc_id)
        finally:
            conn.close()
        if row is None:
            raise HTTPException(status_code=404, detail=f"unknown document: {doc_id}")
        return row

    @app.get("/api/places/{place_id}/script")
    def get_script(place_id: str) -> list[dict[str, Any]]:
        place = place_or_404(place_id)
        return [asdict(turn) for turn in place.script]

    @app.get("/api/places/{place_id}/replay/{turn}")
    def get_replay(
        place_id: str,
        turn: int,
        mode: Literal["keyword", "raptor", "recorded"] = "keyword",
    ) -> dict[str, Any]:
        place = place_or_404(place_id)
        script_turn = next((item for item in place.script if item.turn == turn), None)
        if script_turn is None:
            raise HTTPException(status_code=404, detail=f"unknown turn: {turn}")
        if mode == "recorded":
            payload = recorded_turn(place, turn)
            if payload is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"no recording for turn {turn}; run `pixi run record` "
                        "with the local models"
                    ),
                )
            return payload
        conn = connect(settings.database_path)
        try:
            if mode == "raptor":
                response = answer_raptor(
                    app, settings, place_id, script_turn.visitor, limit=8
                )
                return {
                    "turn": script_turn.turn,
                    "visitor": script_turn.visitor,
                    "note": script_turn.note,
                    "expect": script_turn.expect,
                    "mode": "raptor",
                    "result": response,
                }
            replay = replay_turn(conn, place_id, script_turn, limit=5)
        finally:
            conn.close()
        return asdict(replay)

    @app.get("/api/places/{place_id}/eval/keyword")
    def get_keyword_eval(place_id: str) -> dict[str, Any]:
        place = place_or_404(place_id)
        conn = connect(settings.database_path)
        try:
            return keyword_metrics(conn, place)
        finally:
            conn.close()

    @app.get("/api/places/{place_id}/eval/raptor")
    def get_raptor_eval(place_id: str) -> dict[str, Any]:
        place = place_or_404(place_id)
        conn = connect(settings.database_path)
        try:
            if embedding_count(conn, place_id, "chunk") == 0:
                raise HTTPException(
                    status_code=409,
                    detail="this place has no embeddings; run `pixi run embed`",
                )
            return raptor_metrics(conn, place, app.state.router)
        except RouterError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        finally:
            conn.close()

    @app.post("/api/ask")
    def ask(request: AskRequest) -> dict[str, Any]:
        question = request.question.strip()
        if request.mode == "raptor":
            return answer_raptor(
                app, settings, request.place_id, question, request.limit
            )
        return answer_keyword(settings, request.place_id, question, request.limit)

    @app.websocket("/ws/ask")
    async def websocket_ask(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                payload = await websocket.receive_json()
                place_id = str(payload.get("place_id", "")).strip()
                question = str(payload.get("question", "")).strip()
                mode = str(payload.get("mode", "keyword"))
                if not place_id or not question:
                    await websocket.send_json(
                        {"error": "place_id and question are required"}
                    )
                    continue
                try:
                    limit = max(1, min(int(payload.get("limit", 8)), 20))
                    if mode == "raptor":
                        response = await asyncio.to_thread(
                            answer_raptor,
                            app,
                            settings,
                            place_id,
                            question,
                            limit,
                        )
                    else:
                        response = await asyncio.to_thread(
                            answer_keyword,
                            settings,
                            place_id,
                            question,
                            limit,
                        )
                except HTTPException as exc:
                    response = {"error": exc.detail}
                await websocket.send_json(response)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
