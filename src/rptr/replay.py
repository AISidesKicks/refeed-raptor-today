"""Replay one autoplay turn against the model-free index.

The full player will read recorded traces with the writer and the decision
model. This helper is the fallback: it runs the same question through the
keyword baseline and returns the script's expected answer next to the evidence.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .place import ScriptTurn
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
