"""Build the local SQLite index from the place folders."""

from __future__ import annotations

import argparse

from .chunking import chunk_text
from .config import Settings
from .place import Place, PlaceError, discover_places
from .store import connect, index_place, init_db


def build_index(settings: Settings, place_id: str | None = None) -> dict[str, int]:
    """Index every discovered place, or one place, and return chunk counts."""

    places = discover_places(settings.places_dir)
    if place_id is not None:
        places = [place for place in places if place.id == place_id]
    if not places:
        raise PlaceError(f"no places found in {settings.places_dir}")

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(settings.database_path)
    counts: dict[str, int] = {}
    try:
        init_db(conn)
        for place in places:
            counts[place.id] = _index_one(conn, place)
    finally:
        conn.close()
    return counts


def _index_one(conn, place: Place) -> int:
    chunks_by_doc = {
        document.id: chunk_text(document.text, document.id)
        for document in place.documents
    }
    total = index_place(conn, place, chunks_by_doc)
    print(
        f"{place.id}: {len(place.documents)} documents, "
        f"{place.words:,} words, {total} chunks"
    )
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the local Raptor index.")
    parser.add_argument("--place", help="Index one place id instead of all places.")
    args = parser.parse_args()
    settings = Settings.from_env()
    counts = build_index(settings, args.place)
    print(f"indexed {len(counts)} place(s) into {settings.database_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
