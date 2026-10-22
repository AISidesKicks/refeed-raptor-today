"""SQLite storage for places, documents, and chunks.

The lab uses SQLite plus a numpy brute-force cosine search once the embedder is
loaded. This module is the durable part: it keeps the corpus and the chunks in
one file so the reader, the replay player, and the eval can share them.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .chunking import Chunk
from .place import Place

SCHEMA = """
CREATE TABLE IF NOT EXISTS places (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    blurb TEXT NOT NULL,
    root TEXT NOT NULL,
    version INTEGER NOT NULL,
    license TEXT NOT NULL,
    documents INTEGER NOT NULL,
    words INTEGER NOT NULL,
    questions INTEGER NOT NULL,
    loaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    author TEXT NOT NULL,
    source TEXT NOT NULL,
    path TEXT NOT NULL,
    words INTEGER NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (place_id, id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    text TEXT NOT NULL,
    words INTEGER NOT NULL,
    token_estimate INTEGER NOT NULL,
    PRIMARY KEY (place_id, id)
);

CREATE INDEX IF NOT EXISTS idx_documents_place ON documents(place_id);
CREATE INDEX IF NOT EXISTS idx_chunks_place ON chunks(place_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(place_id, doc_id);
"""


def connect(path: Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def index_place(
    conn: sqlite3.Connection,
    place: Place,
    chunks_by_doc: dict[str, list[Chunk]],
) -> int:
    """Replace one place in the index and return the number of chunks."""

    loaded_at = datetime.now(UTC).isoformat()
    total_chunks = 0
    with conn:
        conn.execute("DELETE FROM chunks WHERE place_id = ?", (place.id,))
        conn.execute("DELETE FROM documents WHERE place_id = ?", (place.id,))
        conn.execute("DELETE FROM places WHERE id = ?", (place.id,))
        conn.execute(
            """
            INSERT INTO places
                (id, title, blurb, root, version, license, documents, words, questions, loaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                place.id,
                place.title,
                place.blurb,
                str(place.root),
                place.version,
                place.license,
                len(place.documents),
                place.words,
                len(place.questions),
                loaded_at,
            ),
        )
        for document in place.documents:
            conn.execute(
                """
                INSERT INTO documents
                    (id, place_id, title, category, date, author, source, path, words, text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    place.id,
                    document.title,
                    document.category,
                    document.date,
                    document.author,
                    document.source,
                    document.path,
                    document.words,
                    document.text,
                ),
            )
            for chunk in chunks_by_doc.get(document.id, []):
                conn.execute(
                    """
                    INSERT INTO chunks
                        (id, place_id, doc_id, ordinal, text, words, token_estimate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.id,
                        place.id,
                        chunk.doc_id,
                        chunk.ordinal,
                        chunk.text,
                        chunk.words,
                        chunk.token_estimate,
                    ),
                )
                total_chunks += 1
    return total_chunks


def place_summaries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, title, blurb, license, version, documents, words, questions
        FROM places
        ORDER BY title
        """
    ).fetchall()
    return [dict(row) for row in rows]


def place_detail(conn: sqlite3.Connection, place_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, title, blurb, license, version, documents, words, questions, loaded_at
        FROM places
        WHERE id = ?
        """,
        (place_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def documents(
    conn: sqlite3.Connection,
    place_id: str,
    include_text: bool = False,
) -> list[dict[str, Any]]:
    columns = "id, title, category, date, author, source, path, words"
    if include_text:
        columns += ", text"
    rows = conn.execute(
        f"SELECT {columns} FROM documents WHERE place_id = ? ORDER BY id",
        (place_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def document(conn: sqlite3.Connection, place_id: str, doc_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, title, category, date, author, source, path, words, text
        FROM documents
        WHERE place_id = ? AND id = ?
        """,
        (place_id, doc_id),
    ).fetchone()
    return dict(row) if row is not None else None


def chunk_rows(conn: sqlite3.Connection, place_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT c.id, c.doc_id, c.text, c.words, c.token_estimate,
               d.title AS doc_title, d.category
        FROM chunks c
        JOIN documents d ON d.place_id = c.place_id AND d.id = c.doc_id
        WHERE c.place_id = ?
        ORDER BY c.id
        """,
        (place_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def chunk_count(conn: sqlite3.Connection, place_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM chunks WHERE place_id = ?",
        (place_id,),
    ).fetchone()
    return int(row["count"]) if row is not None else 0
