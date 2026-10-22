"""Evaluate retrieval on the place's question set.

Two retrievers share the same 50 questions:

- BM25 over chunks, the model-free floor.
- EmbeddingGemma 2 over the collapsed RAPTOR tree.

The numbers are recall at 5, 10, and 20, plus MRR. A summary node counts as a
hit when any of its source documents is in the gold set, because a summary is a
valid route to the document.

`--answers` also runs the full refeed loop and reports citation coverage. That
is slower: it makes several model calls per question.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .config import Settings
from .llm import LlamaRouter
from .pipeline import PipelineConfig, answer_question
from .place import Place, discover_places
from .retrieval import collapsed_search
from .search import search_rows
from .store import chunk_rows, connect


def _summary(results: list[dict[str, Any]], total: int) -> dict[str, Any]:
    def recall_at(k: int) -> float:
        if total == 0:
            return 0.0
        hits = sum(
            1
            for result in results
            if result["first_rank"] is not None and result["first_rank"] <= k
        )
        return round(hits / total, 4)

    mrr = (
        round(
            sum(
                1 / result["first_rank"]
                for result in results
                if result["first_rank"] is not None
            )
            / total,
            4,
        )
        if total
        else 0.0
    )
    return {
        "questions": total,
        "recall_at_5": recall_at(5),
        "recall_at_10": recall_at(10),
        "recall_at_20": recall_at(20),
        "mrr": mrr,
    }


def _by_type(results: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault(result["type"], []).append(result)
    return {
        name: _summary(items, len(items))
        for name, items in sorted(grouped.items())
    }


def keyword_metrics(conn: sqlite3.Connection, place: Place, limit: int = 20) -> dict[str, Any]:
    rows = chunk_rows(conn, place.id)
    results: list[dict[str, Any]] = []
    for question in place.questions:
        hits = search_rows(rows, question.question, limit=limit)
        first_rank = next(
            (hit.rank for hit in hits if hit.doc_id in set(question.gold)),
            None,
        )
        results.append(
            {
                "id": question.id,
                "question": question.question,
                "type": question.type,
                "gold": list(question.gold),
                "first_rank": first_rank,
            }
        )
    payload = _summary(results, len(results))
    payload.update(
        {
            "place_id": place.id,
            "mode": "keyword",
            "by_type": _by_type(results),
            "results": results,
        }
    )
    return payload


def raptor_metrics(
    conn: sqlite3.Connection,
    place: Place,
    router: LlamaRouter,
    limit: int = 20,
) -> dict[str, Any]:
    embed_model = place.models.get("embedding", "embeddinggemma-2")
    vectors = router.embed([question.question for question in place.questions], model=embed_model)
    results: list[dict[str, Any]] = []
    for question, vector in zip(place.questions, vectors, strict=True):
        hits = collapsed_search(conn, place.id, vector, limit=limit)
        gold = set(question.gold)
        first = next((hit for hit in hits if gold & set(hit.doc_ids)), None)
        results.append(
            {
                "id": question.id,
                "question": question.question,
                "type": question.type,
                "gold": list(question.gold),
                "first_rank": first.rank if first else None,
                "first_node": first.node_id if first else None,
                "first_kind": first.kind if first else None,
                "top": [
                    {
                        "rank": hit.rank,
                        "node_id": hit.node_id,
                        "kind": hit.kind,
                        "level": hit.level,
                        "score": round(hit.score, 4),
                        "doc_ids": list(hit.doc_ids),
                    }
                    for hit in hits[:5]
                ],
            }
        )
    payload = _summary(results, len(results))
    payload.update(
        {
            "place_id": place.id,
            "mode": "raptor",
            "by_type": _by_type(results),
            "results": results,
        }
    )
    return payload


def answer_metrics(
    conn: sqlite3.Connection,
    place: Place,
    router: LlamaRouter,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, question in enumerate(place.questions, start=1):
        print(f"answer {index}/{len(place.questions)}: {question.id}")
        result = answer_question(router, conn, place, question.question, config)
        cited_docs = {
            doc_id for citation in result.get("citations", []) for doc_id in citation["doc_ids"]
        }
        gold = set(question.gold)
        results.append(
            {
                "id": question.id,
                "type": question.type,
                "gold": list(question.gold),
                "can_answer": bool(result["can_answer"]),
                "refeeds": int(result["refeeds"]),
                "citation_hit": bool(cited_docs & gold),
                "cited_docs": sorted(cited_docs),
                "warning": result.get("warning"),
                "total_ms": int(result["timings"]["total_ms"]),
            }
        )
    total = len(results)
    return {
        "place_id": place.id,
        "questions": total,
        "answered": sum(1 for result in results if result["can_answer"]),
        "citation_hit_rate": round(
            sum(1 for result in results if result["citation_hit"]) / total, 4
        )
        if total
        else 0.0,
        "mean_refeeds": round(sum(result["refeeds"] for result in results) / total, 3)
        if total
        else 0.0,
        "mean_latency_ms": int(sum(result["total_ms"] for result in results) / total)
        if total
        else 0,
        "wall_ms": int((time.monotonic() - started) * 1000),
        "results": results,
    }


def _print_metrics(label: str, payload: dict[str, Any]) -> None:
    print(
        f"{label:8} R@5 {payload['recall_at_5']:.4f}  "
        f"R@10 {payload['recall_at_10']:.4f}  "
        f"R@20 {payload['recall_at_20']:.4f}  "
        f"MRR {payload['mrr']:.4f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the local RAG lab.")
    parser.add_argument("--place", help="Evaluate one place id instead of all places.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--answers",
        action="store_true",
        help="Run the full refeed loop for every question (slow).",
    )
    parser.add_argument("--output", type=Path, help="Write the full JSON report here.")
    args = parser.parse_args()

    settings = Settings.from_env()
    places = discover_places(settings.places_dir)
    if args.place:
        places = [place for place in places if place.id == args.place]
    if not places:
        raise SystemExit("no places found")

    report: dict[str, Any] = {"places": []}
    with LlamaRouter(base_url=args.base_url) as router:
        router.wait_until_ready()
        for place in places:
            conn = connect(settings.database_path)
            try:
                keyword = keyword_metrics(conn, place, limit=args.limit)
                raptor = raptor_metrics(conn, place, router, limit=args.limit)
                payload: dict[str, Any] = {
                    "place_id": place.id,
                    "keyword": keyword,
                    "raptor": raptor,
                }
                _print_metrics("keyword", keyword)
                _print_metrics("raptor", raptor)
                if args.answers:
                    answers = answer_metrics(conn, place, router)
                    payload["answers"] = answers
                    print(
                        f"answers  {answers['answered']}/{answers['questions']} answered  "
                        f"citation hit {answers['citation_hit_rate']:.4f}  "
                        f"mean refeeds {answers['mean_refeeds']:.2f}"
                    )
                report["places"].append(payload)
            finally:
                conn.close()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
