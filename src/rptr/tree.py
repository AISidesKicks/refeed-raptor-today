"""Build the RAPTOR summary tree.

Leaves are the 200 chunks. The builder clusters them, asks LFM2.5 for one
summary per cluster, embeds the summaries, and repeats until a small root is
left. UMAP plus a Gaussian mixture keeps the clusters local and soft, like the
paper, without pulling in a framework.

The tree is stored in SQLite. Leaves live in `chunks`; summary nodes live in
`tree_nodes`, and their vectors live in `embeddings` with kind `summary`.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import warnings
from typing import Any

import numpy as np

from .config import Settings
from .embed import chunk_text_for_embedding
from .llm import LlamaRouter
from .place import Place, discover_places
from .store import (
    chunk_rows,
    connect,
    delete_embeddings,
    init_db,
    load_embeddings,
    replace_tree,
    save_embeddings,
)

SUMMARY_SYSTEM = (
    "You compress evidence for a retrieval tree. Preserve names, dates, numbers, "
    "places, and explicit claims. Drop repeated boilerplate. Never invent a fact. "
    "Write plain prose without a preamble."
)

SUMMARY_PROMPT = """Summarize the records below for {place}.

Rules:
- 120 to 220 words.
- Keep every name, date, number, and decision that could answer a question.
- Merge duplicates, but do not merge two different claims into one.
- If records disagree, keep the disagreement.
- Return only the summary.

Records:
{records}
"""

ROOT_PROMPT = """Write one root summary of {place} from the summaries below.

Rules:
- 180 to 260 words.
- Say what the corpus covers, which places and programs matter, and which
  numbers or rules a reader is likely to ask about.
- Do not invent anything that is not in the summaries.
- Return only the summary.

Summaries:
{records}
"""


def _reduce(vectors: np.ndarray) -> np.ndarray:
    """Reduce dimensions for clustering. UMAP when it is worth it, PCA otherwise."""

    count, dims = vectors.shape
    components = max(2, min(5, dims - 1))
    if count >= 25:
        try:
            from umap import UMAP

            return UMAP(
                n_neighbors=min(15, count - 1),
                n_components=components,
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            ).fit_transform(vectors)
        except Exception as exc:  # noqa: BLE001 - UMAP has no stable error type
            warnings.warn(f"UMAP failed ({exc}); falling back to PCA", stacklevel=2)
    from sklearn.decomposition import PCA

    return PCA(n_components=min(components, count - 1), random_state=42).fit_transform(vectors)


def cluster_vectors(vectors: np.ndarray, target_size: int = 10, max_clusters: int = 24) -> list[list[int]]:
    """Soft GMM clustering. Returns a non-empty member list per cluster."""

    count = len(vectors)
    if count <= 1:
        return [list(range(count))]
    components = max(2, min(max_clusters, math.ceil(count / target_size)))
    components = min(components, count)
    if components <= 1:
        return [list(range(count))]

    reduced = _reduce(vectors)
    from sklearn.mixture import GaussianMixture

    model = GaussianMixture(
        n_components=components,
        covariance_type="diag",
        random_state=42,
        n_init=3,
    )
    model.fit(reduced)
    probabilities = model.predict_proba(reduced)

    clusters: list[list[int]] = []
    for component in range(components):
        order = np.argsort(-probabilities[:, component])
        members = [int(index) for index in order if probabilities[index, component] >= 0.10]
        # A soft cluster can be large. Cap it so the summary prompt stays small.
        members = sorted(members[:12])
        if not members:
            members = [int(order[0])]
        clusters.append(members)
    return clusters


def summarize(
    router: LlamaRouter,
    model: str,
    place_title: str,
    nodes: list[dict[str, Any]],
    root: bool = False,
) -> str:
    records = "\n\n".join(
        f"[{node['id']}] {node.get('title', '')}\n{node['text']}" for node in nodes
    )
    prompt = (ROOT_PROMPT if root else SUMMARY_PROMPT).format(
        place=place_title,
        records=records,
    )
    result = router.chat(
        [
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        model=model,
        max_tokens=600,
        temperature=0.1,
        skip_reasoning=True,
    )
    text = result.text.strip()
    if len(text.split()) < 20:
        raise ValueError(
            f"summary was too short for cluster of {len(nodes)} nodes "
            f"({len(text.split())} words, {result.completion_tokens} tokens)"
        )
    return text


def build_tree(
    router: LlamaRouter,
    conn: sqlite3.Connection,
    place: Place,
    max_depth: int = 2,
    target_size: int = 10,
) -> dict[str, Any]:
    """Build the tree and return a small report."""

    model = place.models.get("writer", "lfm2-8b")
    rows = chunk_rows(conn, place.id)
    if not rows:
        raise ValueError(f"{place.id}: no chunks; run `pixi run index` first")
    leaf_ids, leaf_vectors = load_embeddings(conn, place.id, "chunk")
    if not leaf_ids:
        raise ValueError(f"{place.id}: no chunk embeddings; run `pixi run embed` first")
    if len(leaf_ids) != len(rows):
        raise ValueError(
            f"{place.id}: {len(rows)} chunks but {len(leaf_ids)} embeddings; "
            "re-run `pixi run embed`"
        )

    row_by_id = {str(row["id"]): row for row in rows}
    order = [str(row["id"]) for row in rows]
    vectors_by_id = {node_id: leaf_vectors[index] for index, node_id in enumerate(leaf_ids)}
    current: list[dict[str, Any]] = []
    for node_id in order:
        row = row_by_id[node_id]
        current.append(
            {
                "id": node_id,
                "level": 0,
                "kind": "chunk",
                "title": str(row["doc_title"]),
                "text": str(row["text"]),
                "doc_ids": [str(row["doc_id"])],
                "children": [],
                "cluster": 0,
            }
        )

    delete_embeddings(conn, place.id, "summary")
    summaries: list[dict[str, Any]] = []
    level = 0
    cluster_count = 0

    while len(current) > 6 and level < max_depth:
        level += 1
        matrix = np.vstack([vectors_by_id[node["id"]] for node in current])
        clusters = cluster_vectors(matrix, target_size=target_size)
        cluster_count += len(clusters)
        next_nodes: list[dict[str, Any]] = []
        texts: list[str] = []
        for cluster_id, members in enumerate(clusters):
            selected = [current[index] for index in members]
            text = summarize(router, model, place.title, selected)
            node_id = f"sum-l{level}-{cluster_id:02d}"
            doc_ids = sorted({doc for node in selected for doc in node["doc_ids"]})
            node = {
                "id": node_id,
                "level": level,
                "kind": "summary",
                "title": f"Level {level} cluster {cluster_id + 1}",
                "text": text,
                "doc_ids": doc_ids,
                "children": [node["id"] for node in selected],
                "cluster": cluster_id,
            }
            next_nodes.append(node)
            texts.append(chunk_text_for_embedding(node["title"], text))
            print(f"{place.id}: level {level} cluster {cluster_id + 1}/{len(clusters)}")

        fresh = router.embed(texts, model=place.models.get("embedding", "embeddinggemma-2"))
        save_embeddings(
            conn,
            place.id,
            "summary",
            place.models.get("embedding", "embeddinggemma-2"),
            [node["id"] for node in next_nodes],
            fresh,
        )
        for node, vector in zip(next_nodes, fresh, strict=True):
            vectors_by_id[node["id"]] = vector
        summaries.extend(next_nodes)
        current = next_nodes

    if len(current) > 1:
        level += 1
        text = summarize(router, model, place.title, current, root=True)
        root = {
            "id": "sum-root",
            "level": level,
            "kind": "root",
            "title": "Root summary",
            "text": text,
            "doc_ids": sorted({doc for node in current for doc in node["doc_ids"]}),
            "children": [node["id"] for node in current],
            "cluster": 0,
        }
        vector = router.embed([chunk_text_for_embedding(root["title"], text)], model=place.models.get("embedding", "embeddinggemma-2"))
        save_embeddings(
            conn,
            place.id,
            "summary",
            place.models.get("embedding", "embeddinggemma-2"),
            [root["id"]],
            vector,
        )
        summaries.append(root)
        print(f"{place.id}: root summary over {len(root['children'])} nodes")

    replace_tree(conn, place.id, summaries)
    return {
        "place_id": place.id,
        "chunks": len(rows),
        "summary_nodes": len(summaries),
        "clusters": cluster_count,
        "levels": level,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the RAPTOR summary tree.")
    parser.add_argument("--place", help="Build one place id instead of all places.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--target-size", type=int, default=10)
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
                report = build_tree(
                    router,
                    conn,
                    place,
                    max_depth=args.max_depth,
                    target_size=args.target_size,
                )
                print(report)
            finally:
                conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
