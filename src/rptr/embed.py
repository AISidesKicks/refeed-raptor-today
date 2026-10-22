"""Embed chunks with EmbeddingGemma 2 and search the vectors with numpy.

The place is small: 200 chunks is a 200 by 768 matrix, about 600 KB. A dot
product is faster than a vector database and much easier to inspect. Vectors
live in SQLite so the index survives a restart.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass

import numpy as np

from .config import Settings
from .llm import LlamaRouter
from .place import Place, discover_places
from .store import chunk_rows, connect, init_db, save_embeddings


@dataclass(frozen=True)
class VectorHit:
    node_id: str
    score: float
    index: int


def cosine_search(ids: list[str], matrix: np.ndarray, query: np.ndarray, limit: int) -> list[VectorHit]:
    """Brute-force cosine search. Both sides are already normalized."""

    if not ids or matrix.size == 0 or limit <= 0:
        return []
    scores = matrix @ query.astype(np.float32, copy=False)
    order = np.argsort(-scores)[:limit]
    return [
        VectorHit(node_id=ids[int(index)], score=float(scores[int(index)]), index=int(index))
        for index in order
    ]


def chunk_text_for_embedding(title: str, text: str) -> str:
    """Give the encoder the document title as context, not just the paragraph."""

    return f"{title}\n\n{text}"


def embed_place(
    router: LlamaRouter,
    conn: sqlite3.Connection,
    place: Place,
    batch_size: int = 16,
) -> int:
    rows = chunk_rows(conn, place.id)
    if not rows:
        raise ValueError(f"{place.id}: no chunks in the index; run `pixi run index` first")
    model = place.models.get("embedding", "embeddinggemma-2")
    ids = [str(row["id"]) for row in rows]
    texts = [chunk_text_for_embedding(str(row["doc_title"]), str(row["text"])) for row in rows]
    matrix = router.embed(texts, model=model, batch_size=batch_size)
    saved = save_embeddings(conn, place.id, "chunk", model, ids, matrix)
    print(f"{place.id}: embedded {saved} chunks with {model} ({matrix.shape[1]} dims)")
    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed the chunks with the local router.")
    parser.add_argument("--place", help="Embed one place id instead of all places.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--batch-size", type=int, default=16)
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
                embed_place(router, conn, place, batch_size=args.batch_size)
            finally:
                conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
