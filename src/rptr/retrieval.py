"""Collapsed-tree retrieval over chunks and RAPTOR summaries.

The default retriever searches every level at once: 200 leaves plus the summary
nodes. The score decides which level wins. That is the RAPTOR paper's collapsed
tree, and it is easier to explain than a descent rule.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

import numpy as np

from .embed import cosine_search
from .store import chunk_rows, load_embeddings, tree_nodes


@dataclass(frozen=True)
class RetrievalHit:
    node_id: str
    kind: str
    level: int
    title: str
    text: str
    doc_ids: tuple[str, ...]
    children: tuple[str, ...]
    score: float
    rank: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "level": self.level,
            "title": self.title,
            "text": self.text,
            "doc_ids": list(self.doc_ids),
            "children": list(self.children),
            "score": round(self.score, 4),
            "rank": self.rank,
        }


def load_retrieval_index(
    conn: sqlite3.Connection,
    place_id: str,
) -> tuple[list[str], np.ndarray, dict[str, dict[str, Any]]]:
    """Return ids, vectors, and metadata for leaves and summaries."""

    chunk_ids, chunk_vectors = load_embeddings(conn, place_id, "chunk")
    summary_ids, summary_vectors = load_embeddings(conn, place_id, "summary")
    if not chunk_ids:
        raise ValueError(f"{place_id}: no chunk embeddings; run `pixi run embed` first")

    rows = {str(row["id"]): row for row in chunk_rows(conn, place_id)}
    meta: dict[str, dict[str, Any]] = {}
    for node_id in chunk_ids:
        row = rows.get(node_id)
        if row is None:
            raise ValueError(f"{place_id}: embedding for unknown chunk {node_id}")
        meta[node_id] = {
            "kind": "chunk",
            "level": 0,
            "title": str(row["doc_title"]),
            "text": str(row["text"]),
            "doc_ids": (str(row["doc_id"]),),
            "children": (),
        }
    for node in tree_nodes(conn, place_id):
        meta[str(node["id"])] = {
            "kind": str(node["kind"]),
            "level": int(node["level"]),
            "title": str(node["title"]),
            "text": str(node["text"]),
            "doc_ids": tuple(str(item) for item in node["doc_ids"]),
            "children": tuple(str(item) for item in node["children"]),
        }

    ids = list(chunk_ids) + list(summary_ids)
    pieces = [matrix for matrix in (chunk_vectors, summary_vectors) if matrix.size]
    matrix = np.vstack(pieces)
    missing = [node_id for node_id in ids if node_id not in meta]
    if missing:
        raise ValueError(f"{place_id}: vectors without metadata: {missing[:3]}")
    return ids, matrix, meta


def collapsed_search(
    conn: sqlite3.Connection,
    place_id: str,
    query_vector: np.ndarray,
    limit: int = 20,
) -> list[RetrievalHit]:
    ids, matrix, meta = load_retrieval_index(conn, place_id)
    if matrix.shape[1] != query_vector.shape[0]:
        raise ValueError(
            f"{place_id}: query has {query_vector.shape[0]} dims but the index has "
            f"{matrix.shape[1]}; re-run `pixi run embed`"
        )
    hits: list[RetrievalHit] = []
    for rank, hit in enumerate(cosine_search(ids, matrix, query_vector, limit), start=1):
        item = meta[hit.node_id]
        hits.append(
            RetrievalHit(
                node_id=hit.node_id,
                kind=str(item["kind"]),
                level=int(item["level"]),
                title=str(item["title"]),
                text=str(item["text"]),
                doc_ids=tuple(item["doc_ids"]),
                children=tuple(item["children"]),
                score=hit.score,
                rank=rank,
            )
        )
    return hits
