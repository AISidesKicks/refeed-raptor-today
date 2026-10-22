from pathlib import Path

from rptr.chunking import chunk_text
from rptr.place import load_place
from rptr.search import search_rows
from rptr.store import chunk_rows, connect, index_place, init_db

PLACE = Path(__file__).resolve().parents[1] / "lab" / "demos" / "raptor-reserve"


def build_rows(tmp_path):
    place = load_place(PLACE)
    conn = connect(tmp_path / "search.sqlite3")
    init_db(conn)
    chunks = {
        doc.id: chunk_text(doc.text, doc.id) for doc in place.documents
    }
    index_place(conn, place, chunks)
    return chunk_rows(conn, place.id), conn


def test_osprey_question_finds_the_species_doc(tmp_path):
    rows, conn = build_rows(tmp_path)
    try:
        hits = search_rows(
            rows,
            "How many osprey chicks fledged at the reserve in 2025?",
            limit=10,
        )
        assert hits
        assert any(hit.doc_id == "rr-012" for hit in hits)
    finally:
        conn.close()


def test_drone_question_finds_both_sides_of_the_multi_hop(tmp_path):
    rows, conn = build_rows(tmp_path)
    try:
        hits = search_rows(
            rows,
            "A drone flight is planned with a 35 km/h wind. May it proceed?",
            limit=10,
        )
        doc_ids = {hit.doc_id for hit in hits}
        assert "rr-032" in doc_ids
        assert "rr-034" in doc_ids
    finally:
        conn.close()


def test_unknown_term_returns_nothing(tmp_path):
    rows, conn = build_rows(tmp_path)
    try:
        assert search_rows(rows, "xyzzy plugh", limit=10) == []
    finally:
        conn.close()
