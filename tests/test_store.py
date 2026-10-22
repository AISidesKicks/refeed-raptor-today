from dataclasses import replace
from pathlib import Path

import numpy as np

from rptr.chunking import chunk_text
from rptr.place import load_place
from rptr.store import (
    chunk_count,
    chunk_rows,
    connect,
    document,
    documents,
    embedding_count,
    index_place,
    init_db,
    place_detail,
    save_embeddings,
)

PLACE = Path(__file__).resolve().parents[1] / "lab" / "demos" / "raptor-reserve"


def build_database(tmp_path):
    place = load_place(PLACE)
    conn = connect(tmp_path / "test.sqlite3")
    init_db(conn)
    chunks = {
        doc.id: chunk_text(doc.text, doc.id) for doc in place.documents
    }
    index_place(conn, place, chunks)
    return place, conn


def test_index_and_read_back(tmp_path):
    place, conn = build_database(tmp_path)
    try:
        detail = place_detail(conn, place.id)
        assert detail is not None
        assert detail["documents"] == 100
        assert detail["questions"] == 50
        assert chunk_count(conn, place.id) == 200

        listing = documents(conn, place.id)
        assert len(listing) == 100
        assert "text" not in listing[0]

        full = documents(conn, place.id, include_text=True)
        assert "text" in full[0]

        charter = document(conn, place.id, "rr-001")
        assert charter is not None
        assert charter["title"] == "Reserve Charter"

        rows = chunk_rows(conn, place.id)
        assert len(rows) == 200
        assert rows[0]["doc_title"]
    finally:
        conn.close()


def test_reindex_keeps_embeddings_for_unchanged_place(tmp_path):
    place, conn = build_database(tmp_path)
    try:
        save_embeddings(conn, place.id, "chunk", "fake", ["rr-001:000"], np.ones((1, 4)))
        chunks = {doc.id: chunk_text(doc.text, doc.id) for doc in place.documents}
        index_place(conn, place, chunks)
        assert chunk_count(conn, place.id) == 200
        assert embedding_count(conn, place.id, "chunk") == 1

        changed = replace(place, version=place.version + 1)
        index_place(conn, changed, chunks)
        assert chunk_count(conn, place.id) == 200
        assert embedding_count(conn, place.id, "chunk") == 0
    finally:
        conn.close()
