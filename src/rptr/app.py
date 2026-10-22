"""FastAPI reader for the local RAG lab.

The first slice is model-free. It loads the place, indexes the corpus into
SQLite, and answers with the BM25 baseline. The endpoints are already shaped
for the model-backed pipeline: one ask path, one replay path, one eval path,
and a WebSocket for the interactive UI.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings
from .index import build_index
from .place import Place, discover_places
from .replay import replay_turn
from .search import search_rows
from .store import (
    chunk_rows,
    connect,
    document,
    documents,
    place_detail,
    place_summaries,
)


class AskRequest(BaseModel):
    place_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)


def answer_question(
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


def keyword_eval(settings: Settings, place: Place) -> dict[str, Any]:
    conn = connect(settings.database_path)
    try:
        rows = chunk_rows(conn, place.id)
        results: list[dict[str, Any]] = []
        for question in place.questions:
            hits = search_rows(rows, question.question, limit=20)
            first_rank = next(
                (hit.rank for hit in hits if hit.doc_id in set(question.gold)),
                None,
            )
            results.append(
                {
                    "id": question.id,
                    "question": question.question,
                    "type": question.type,
                    "gold": list(question.gold),
                    "first_rank": first_rank,
                }
            )
        total = len(results)

        def recall_at(k: int) -> float:
            if total == 0:
                return 0.0
            hits = sum(
                1
                for result in results
                if result["first_rank"] is not None and result["first_rank"] <= k
            )
            return round(hits / total, 4)

        mrr = (
            round(
                sum(
                    1 / result["first_rank"]
                    for result in results
                    if result["first_rank"] is not None
                )
                / total,
                4,
            )
            if total
            else 0.0
        )
        return {
            "place_id": place.id,
            "mode": "keyword",
            "questions": total,
            "recall_at_5": recall_at(5),
            "recall_at_10": recall_at(10),
            "recall_at_20": recall_at(20),
            "mrr": mrr,
            "results": results,
        }
    finally:
        conn.close()


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
        yield

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

    @app.get("/api/places/{place_id}")
    def get_place(place_id: str) -> dict[str, Any]:
        place = place_or_404(place_id)
        conn = connect(settings.database_path)
        try:
            detail = place_detail(conn, place_id)
        finally:
            conn.close()
        if detail is None:
            raise HTTPException(status_code=404, detail=f"unknown place: {place_id}")
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
    def get_replay(place_id: str, turn: int) -> dict[str, Any]:
        place = place_or_404(place_id)
        script_turn = next((item for item in place.script if item.turn == turn), None)
        if script_turn is None:
            raise HTTPException(status_code=404, detail=f"unknown turn: {turn}")
        conn = connect(settings.database_path)
        try:
            replay = replay_turn(conn, place_id, script_turn, limit=5)
        finally:
            conn.close()
        return asdict(replay)

    @app.get("/api/places/{place_id}/eval/keyword")
    def get_keyword_eval(place_id: str) -> dict[str, Any]:
        place = place_or_404(place_id)
        return keyword_eval(settings, place)

    @app.post("/api/ask")
    def ask(request: AskRequest) -> dict[str, Any]:
        return answer_question(
            settings,
            request.place_id,
            request.question.strip(),
            request.limit,
        )

    @app.websocket("/ws/ask")
    async def websocket_ask(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                payload = await websocket.receive_json()
                place_id = str(payload.get("place_id", "")).strip()
                question = str(payload.get("question", "")).strip()
                if not place_id or not question:
                    await websocket.send_json(
                        {"error": "place_id and question are required"}
                    )
                    continue
                try:
                    limit = max(1, min(int(payload.get("limit", 8)), 20))
                    response = answer_question(settings, place_id, question, limit)
                except HTTPException as exc:
                    response = {"error": exc.detail}
                await websocket.send_json(response)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
