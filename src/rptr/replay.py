"""Replay an autoplay turn.

Two paths share the player: a committed recording built by the full pipeline,
and a model-free keyword fallback that runs the question against the index.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from .place import Place, ScriptTurn
from .search import SearchHit, search_rows
from .store import chunk_rows


@dataclass(frozen=True)
class ReplayTurn:
    turn: int
    visitor: str
    note: str
    expect: str
    hits: tuple[SearchHit, ...]


def replay_turn(
    conn: sqlite3.Connection,
    place_id: str,
    script_turn: ScriptTurn,
    limit: int = 5,
) -> ReplayTurn:
    hits = search_rows(chunk_rows(conn, place_id), script_turn.visitor, limit=limit)
    return ReplayTurn(
        turn=script_turn.turn,
        visitor=script_turn.visitor,
        note=script_turn.note,
        expect=script_turn.expect,
        hits=tuple(hits),
    )


def recorded_turn(place: Place, turn: int) -> dict[str, Any] | None:
    """Load one committed recording. No model, no database, no GPU."""

    path = place.root / "runs" / f"turn-{turn:02d}.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("place_id") != place.id or int(payload.get("turn", 0)) != turn:
        raise ValueError(f"{path}: recording does not match place and turn")
    return payload


def has_recordings(place: Place) -> bool:
    return any((place.root / "runs").glob("turn-*.json"))
