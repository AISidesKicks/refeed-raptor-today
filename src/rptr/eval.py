"""Evaluate a place on its question sets.

Three modes share the same questions:

- BM25 over chunks, the model-free floor.
- EmbeddingGemma 2 over the collapsed RAPTOR tree.
- The full loop: retrieve, judge, refeed, write, cite, check groundedness.

Retrieval is scored with recall at 5, 10, and 20 plus MRR. A summary node
counts as a hit when any of its source documents is in the gold set, because a
summary is a valid route to the document.

`--answers` runs the loop and reports citation coverage and decision data.
`--modes` adds the one-shot baseline and compares all three modes per question.
`--unknown` runs the out-of-corpus questions and reports the refusal rate.
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
from .pipeline import PipelineConfig, answer_oneshot, answer_question
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


def _step(result: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next(
        (step for step in result.get("trace", []) if step.get("step") == name),
        None,
    )


def _decision_data(result: dict[str, Any]) -> dict[str, Any]:
    """The first sufficiency decision and the actions the loop chose."""

    sufficient = _step(result, "sufficient")
    return {
        "sufficiency": {
            key: sufficient.get(key)
            for key in ("probability", "confidence", "band", "delegated", "source", "accepted")
        }
        if sufficient
        else None,
        "actions": [
            step.get("choice")
            for step in result.get("trace", [])
            if step.get("step") == "action"
        ],
        "rewrites": [
            step.get("queries")
            for step in result.get("trace", [])
            if step.get("step") == "rewrite"
        ],
    }


def answer_metrics(
    conn: sqlite3.Connection,
    place: Place,
    router: LlamaRouter,
    config: PipelineConfig | None = None,
    label: str = "answer",
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, question in enumerate(place.questions, start=1):
        print(f"{label} {index}/{len(place.questions)}: {question.id}")
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
                "answer": result["answer"][:400],
                "warning": result.get("warning"),
                "total_ms": int(result["timings"]["total_ms"]),
                **_decision_data(result),
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


def oneshot_metrics(
    conn: sqlite3.Connection,
    place: Place,
    router: LlamaRouter,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    """Answer every question in one pass, with no loop."""

    results: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, question in enumerate(place.questions, start=1):
        print(f"oneshot {index}/{len(place.questions)}: {question.id}")
        result = answer_oneshot(router, conn, place, question.question, config)
        cited_docs = {
            doc_id for citation in result.get("citations", []) for doc_id in citation["doc_ids"]
        }
        gold = set(question.gold)
        results.append(
            {
                "id": question.id,
                "type": question.type,
                "gold": list(question.gold),
                "citation_hit": bool(cited_docs & gold),
                "cited_docs": sorted(cited_docs),
                "answer": result["answer"][:400],
                "total_ms": int(result["timings"]["total_ms"]),
            }
        )
    total = len(results)
    return {
        "place_id": place.id,
        "mode": "oneshot",
        "questions": total,
        "citation_hit_rate": round(
            sum(1 for result in results if result["citation_hit"]) / total, 4
        )
        if total
        else 0.0,
        "mean_latency_ms": int(sum(result["total_ms"] for result in results) / total)
        if total
        else 0,
        "wall_ms": int((time.monotonic() - started) * 1000),
        "results": results,
    }


def unknown_metrics(
    conn: sqlite3.Connection,
    place: Place,
    router: LlamaRouter,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    """Run questions the corpus cannot answer and count the refusals."""

    results: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, question in enumerate(place.unknown_questions, start=1):
        print(f"unknown {index}/{len(place.unknown_questions)}: {question.id}")
        result = answer_question(router, conn, place, question.question, config)
        refused = not bool(result["can_answer"])
        cited_docs = {
            doc_id for citation in result.get("citations", []) for doc_id in citation["doc_ids"]
        }
        results.append(
            {
                "id": question.id,
                "question": question.question,
                "refused": refused,
                "refeeds": int(result["refeeds"]),
                "answer": result["answer"][:400],
                "cited_docs": sorted(cited_docs),
                "warning": result.get("warning"),
                "total_ms": int(result["timings"]["total_ms"]),
            }
        )
    total = len(results)
    return {
        "place_id": place.id,
        "mode": "unknown",
        "questions": total,
        "refused": sum(1 for result in results if result["refused"]),
        "refusal_rate": round(
            sum(1 for result in results if result["refused"]) / total, 4
        )
        if total
        else 0.0,
        "mean_latency_ms": int(sum(result["total_ms"] for result in results) / total)
        if total
        else 0,
        "wall_ms": int((time.monotonic() - started) * 1000),
        "results": results,
    }


def script_metrics(
    conn: sqlite3.Connection,
    place: Place,
    router: LlamaRouter,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    """Run every script turn twice: one-shot and the loop.

    The demo claims that the loop changes an answer. This is the measurement
    behind that claim, turn by turn.
    """

    results: list[dict[str, Any]] = []
    for turn in place.script:
        print(f"script {turn.turn}/{len(place.script)}: {turn.visitor[:60]}")
        oneshot = answer_oneshot(router, conn, place, turn.visitor, config)
        loop = answer_question(router, conn, place, turn.visitor, config)
        results.append(
            {
                "turn": turn.turn,
                "visitor": turn.visitor,
                "expect": turn.expect,
                "oneshot": {
                    "answer": oneshot["answer"],
                    "citations": [item["node_id"] for item in oneshot["citations"]],
                    "total_ms": int(oneshot["timings"]["total_ms"]),
                },
                "loop": {
                    "answer": loop["answer"],
                    "citations": [item["node_id"] for item in loop["citations"]],
                    "refeeds": int(loop["refeeds"]),
                    "can_answer": bool(loop["can_answer"]),
                    "total_ms": int(loop["timings"]["total_ms"]),
                },
                "changed": oneshot["answer"].strip() != loop["answer"].strip(),
                "loop_refeeded": int(loop["refeeds"]) > 0,
            }
        )
    return {
        "place_id": place.id,
        "mode": "script",
        "turns": len(results),
        "changed": sum(1 for row in results if row["changed"]),
        "refeeded": sum(1 for row in results if row["loop_refeeded"]),
        "results": results,
    }


def compare_modes(
    place: Place,
    keyword: dict[str, Any],
    oneshot: dict[str, Any],
    loop: dict[str, Any],
) -> dict[str, Any]:
    """Join the three modes per question, so the wins and losses are visible."""

    keyword_by_id = {row["id"]: row for row in keyword["results"]}
    oneshot_by_id = {row["id"]: row for row in oneshot["results"]}
    loop_by_id = {row["id"]: row for row in loop["results"]}
    rows: list[dict[str, Any]] = []
    for question in place.questions:
        kw = keyword_by_id.get(question.id, {})
        os_ = oneshot_by_id.get(question.id, {})
        lp = loop_by_id.get(question.id, {})
        rank = kw.get("first_rank")
        rows.append(
            {
                "id": question.id,
                "question": question.question,
                "type": question.type,
                "keyword_rank": rank,
                "keyword_hit_at_5": bool(rank is not None and rank <= 5),
                "oneshot_citation_hit": bool(os_.get("citation_hit")),
                "loop_citation_hit": bool(lp.get("citation_hit")),
                "loop_refeeds": int(lp.get("refeeds") or 0),
            }
        )
    total = len(rows) or 1
    fixed = [row["id"] for row in rows if row["loop_citation_hit"] and not row["oneshot_citation_hit"]]
    broke = [row["id"] for row in rows if row["oneshot_citation_hit"] and not row["loop_citation_hit"]]
    missed = [
        row["id"]
        for row in rows
        if not row["loop_citation_hit"] and not row["oneshot_citation_hit"]
    ]
    return {
        "place_id": place.id,
        "questions": len(rows),
        "keyword_hit_at_5": round(sum(1 for row in rows if row["keyword_hit_at_5"]) / total, 4),
        "oneshot_citation_hit_rate": round(
            sum(1 for row in rows if row["oneshot_citation_hit"]) / total, 4
        ),
        "loop_citation_hit_rate": round(
            sum(1 for row in rows if row["loop_citation_hit"]) / total, 4
        ),
        "oneshot_mean_latency_ms": oneshot["mean_latency_ms"],
        "loop_mean_latency_ms": loop["mean_latency_ms"],
        "loop_mean_refeeds": loop["mean_refeeds"],
        "loop_answered": loop["answered"],
        "loop_fixed": fixed,
        "loop_broke": broke,
        "both_missed": missed,
        "rows": rows,
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
    parser.add_argument(
        "--modes",
        action="store_true",
        help="Compare keyword, one-shot, and the full loop (slow).",
    )
    parser.add_argument(
        "--unknown",
        action="store_true",
        help="Run the out-of-corpus questions and report the refusal rate.",
    )
    parser.add_argument(
        "--script",
        action="store_true",
        help="Compare one-shot and the loop on the demo script turns (slow).",
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
                answers: dict[str, Any] | None = None
                if args.answers or args.modes:
                    answers = answer_metrics(conn, place, router)
                    payload["answers"] = answers
                    print(
                        f"loop     {answers['answered']}/{answers['questions']} answered  "
                        f"citation hit {answers['citation_hit_rate']:.4f}  "
                        f"mean refeeds {answers['mean_refeeds']:.2f}  "
                        f"mean {answers['mean_latency_ms']} ms"
                    )
                if args.modes:
                    oneshot = oneshot_metrics(conn, place, router)
                    payload["oneshot"] = oneshot
                    print(
                        f"oneshot  citation hit {oneshot['citation_hit_rate']:.4f}  "
                        f"mean {oneshot['mean_latency_ms']} ms"
                    )
                    comparison = compare_modes(place, keyword, oneshot, answers or {})
                    payload["comparison"] = comparison
                    print(
                        f"fixed    {len(comparison['loop_fixed'])} questions: "
                        f"{', '.join(comparison['loop_fixed']) or 'none'}"
                    )
                    print(
                        f"broke    {len(comparison['loop_broke'])} questions: "
                        f"{', '.join(comparison['loop_broke']) or 'none'}"
                    )
                if args.unknown:
                    if not place.unknown_questions:
                        print("unknown  no questions in this place")
                    else:
                        unknown = unknown_metrics(conn, place, router)
                        payload["unknown"] = unknown
                        print(
                            f"unknown  refused {unknown['refused']}/{unknown['questions']}  "
                            f"rate {unknown['refusal_rate']:.4f}  "
                            f"mean {unknown['mean_latency_ms']} ms"
                        )
                if args.script:
                    script = script_metrics(conn, place, router)
                    payload["script"] = script
                    print(
                        f"script   {script['changed']}/{script['turns']} turns changed  "
                        f"{script['refeeded']} refeeded"
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
