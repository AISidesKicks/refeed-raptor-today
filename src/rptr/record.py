"""Record scripted turns so the demo can replay without any model.

The recording is a JSON file per turn under `lab/demos/<place>/runs/`. It keeps
the question, the expected answer, the full result, and the decision trace. The
app reads it directly in recorded mode: no router, no GPU, no embeddings needed.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from .config import Settings
from .llm import LlamaRouter
from .pipeline import PipelineConfig, answer_question
from .place import Place, discover_places
from .store import connect, embedding_count, init_db, tree_nodes


def record_place(
    router: LlamaRouter,
    conn: sqlite3.Connection,
    place: Place,
    config: PipelineConfig | None = None,
    overwrite: bool = True,
) -> dict[str, Any]:
    runs_dir = place.root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    recorded_at = datetime.now(UTC).isoformat()
    turns: list[dict[str, Any]] = []

    for script_turn in place.script:
        path = runs_dir / f"turn-{script_turn.turn:02d}.json"
        if path.exists() and not overwrite:
            print(f"{place.id}: turn {script_turn.turn} exists, skipped")
            continue
        print(f"{place.id}: recording turn {script_turn.turn}")
        result = answer_question(router, conn, place, script_turn.visitor, config)
        payload = {
            "format": 1,
            "place_id": place.id,
            "turn": script_turn.turn,
            "visitor": script_turn.visitor,
            "note": script_turn.note,
            "expect": script_turn.expect,
            "recorded_at": recorded_at,
            "models": place.models,
            "result": result,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        turns.append(
            {
                "turn": script_turn.turn,
                "visitor": script_turn.visitor,
                "can_answer": result["can_answer"],
                "refeeds": result["refeeds"],
                "total_ms": result["timings"]["total_ms"],
                "file": path.name,
            }
        )

    index = {
        "format": 1,
        "place_id": place.id,
        "title": place.title,
        "recorded_at": recorded_at,
        "models": place.models,
        "chunks": conn.execute(
            "SELECT COUNT(*) AS count FROM chunks WHERE place_id = ?", (place.id,)
        ).fetchone()["count"],
        "embeddings": embedding_count(conn, place.id, "chunk"),
        "summary_nodes": len(tree_nodes(conn, place.id)),
        "turns": turns,
    }
    (runs_dir / "index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Record scripted turns for replay.")
    parser.add_argument("--place", help="Record one place id instead of all places.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep existing turn files instead of replacing them.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    places = discover_places(settings.places_dir)
    if args.place:
        places = [place for place in places if place.id == args.place]
    if not places:
        raise SystemExit("no places found")

    init_conn = connect(settings.database_path)
    try:
        init_db(init_conn)
    finally:
        init_conn.close()

    with LlamaRouter(base_url=args.base_url) as router:
        router.wait_until_ready()
        for place in places:
            conn = connect(settings.database_path)
            try:
                if embedding_count(conn, place.id, "chunk") == 0:
                    raise SystemExit(
                        f"{place.id}: no embeddings; run `pixi run embed` and "
                        "`pixi run build-tree` first"
                    )
                report = record_place(
                    router,
                    conn,
                    place,
                    overwrite=not args.keep,
                )
                print(json.dumps(report, indent=2))
            finally:
                conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
