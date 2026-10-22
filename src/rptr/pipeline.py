"""The refeed loop: retrieve, judge, rewrite, write, check.

The control flow is fixed Python. The models supply judgments, not decisions
about which step to run next. d1 answers the typed questions, LFM writes the
queries and the answer. Every step is appended to the trace, because the trace
is the lesson.
"""

from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from .llm import Decision, LlamaRouter, choice, noul
from .place import Place
from .retrieval import RetrievalHit, collapsed_search

CITATION_RE = re.compile(r"\[([A-Za-z0-9:._-]+)\]")
BRACKET_RE = re.compile(r"\[([^\[\]\n]{1,80})\]")

ACTION_OPTIONS = {
    "keep": "The query is good; retrieve more passages with the same question.",
    "broaden": "The query is too narrow; remove a constraint and search wider.",
    "narrow": "The query is too broad; add the specific entity, place, or year.",
    "decompose": "The question has several parts; split it into two searches.",
}


@dataclass(frozen=True)
class PipelineConfig:
    retrieve_limit: int = 20
    evidence_limit: int = 8
    max_refeeds: int = 2
    relevance_floor: float = 0.35
    sufficient_threshold: float = 0.50
    grounded_threshold: float = 0.50
    high_confidence: float = 0.75
    low_confidence: float = 0.30
    delegate_low_confidence: bool = True
    writer_max_tokens: int = 900
    writer_evidence_limit: int = 3


def _confidence(probability: float) -> float:
    """Turn a noul probability into a distance from the decision boundary."""

    return abs(probability - 0.5) * 2.0


def _band(confidence: float, config: PipelineConfig) -> str:
    if confidence >= config.high_confidence:
        return "high"
    if confidence >= config.low_confidence:
        return "middle"
    return "low"


def _evidence_text(hits: list[RetrievalHit]) -> str:
    blocks = []
    for hit in hits:
        docs = ", ".join(hit.doc_ids)
        blocks.append(f"[{hit.node_id}] {hit.title} (source: {docs})\n{hit.text}")
    return "\n\n".join(blocks)


_STOPWORDS = {
    "about", "after", "again", "against", "also", "and", "are", "because",
    "been", "before", "being", "between", "both", "but", "can", "could", "did",
    "does", "doing", "for", "from", "had", "has", "have", "how", "into", "its",
    "may", "might", "more", "most", "not", "now", "off", "one", "only", "other",
    "our", "out", "over", "same", "should", "some", "such", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "those", "through",
    "too", "under", "until", "very", "was", "were", "what", "when", "where",
    "which", "while", "who", "why", "will", "with", "would", "you", "your",
}


def _terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9'./-]*", text.casefold())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _is_boilerplate(paragraph: str, terms: set[str]) -> bool:
    lowered = paragraph.casefold().replace("\u2019", "'")
    if "is the standard procedure for this part of the field program" in lowered:
        return True
    if "it does not replace the safety plan" in lowered:
        return True
    if "the primary sources are" in lowered:
        return True
    return "the method is a small local stack" in lowered and not (
        terms & {"stack", "model", "models", "embedding", "embeddings", "writer", "app"}
    )


def _excerpt(hit: RetrievalHit, terms: set[str], max_words: int = 150) -> str:
    """Keep the paragraphs that match the question, not the whole template."""

    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", hit.text) if item.strip()]
    paragraphs = [item for item in paragraphs if not _is_boilerplate(item, terms)]
    if len(paragraphs) <= 1:
        text = " ".join(paragraphs) if paragraphs else hit.text
    else:
        ranked = []
        for index, paragraph in enumerate(paragraphs):
            overlap = len(_terms(paragraph) & terms)
            score = overlap / (len(_terms(paragraph)) ** 0.5 + 1)
            if index == 0:
                score += 0.15
            ranked.append((score, index, paragraph))
        chosen = sorted(sorted(ranked, reverse=True)[:3], key=lambda item: item[1])
        text = " ".join(paragraph for _, _, paragraph in chosen)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]).rstrip(" ,;:") + "."
    return text


def _writer_hits(
    selected: list[RetrievalHit], question: str, limit: int
) -> list[RetrievalHit]:
    """Keep the passages whose titles name the question's topic."""

    terms = _terms(question)
    matched = [hit for hit in selected if terms & _terms(hit.title)]
    return (matched or selected)[:limit]


def _writer_evidence(hits: list[RetrievalHit], question: str) -> str:
    terms = _terms(question)
    blocks = []
    for hit in hits:
        excerpt = _excerpt(hit, terms)
        blocks.append(f"[{hit.node_id}] {hit.title}\n{excerpt}")
    return "\n\n".join(blocks)


def _dedupe(hits: list[RetrievalHit], limit: int) -> list[RetrievalHit]:
    seen: set[str] = set()
    unique: list[RetrievalHit] = []
    for hit in hits:
        if hit.node_id in seen:
            continue
        seen.add(hit.node_id)
        unique.append(hit)
        if len(unique) >= limit:
            break
    return unique


def _merge(pool: dict[str, RetrievalHit], hits: list[RetrievalHit]) -> None:
    for hit in hits:
        previous = pool.get(hit.node_id)
        if previous is None or hit.score > previous.score:
            pool[hit.node_id] = hit


def _relevance(
    router: LlamaRouter,
    model: str,
    question: str,
    hits: list[RetrievalHit],
    batch_size: int = 4,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    scores: dict[str, float] = {}
    calls: list[dict[str, Any]] = []
    for start in range(0, len(hits), batch_size):
        batch = hits[start : start + batch_size]
        questions = {
            f"p{index}": noul(
                "Is this passage relevant to the question? A passage is relevant "
                "if it contains a fact, rule, name, number, or claim that helps "
                "answer the question.\n\nPassage:\n" + hit.text
            )
            for index, hit in enumerate(batch)
        }
        decisions = router.systemone(question, questions, model=model)
        for index, hit in enumerate(batch):
            decision = decisions.get(f"p{index}")
            if decision is None:
                continue
            probability = float(decision.value)
            scores[hit.node_id] = probability
            calls.append(
                {
                    "node_id": hit.node_id,
                    "probability": round(probability, 4),
                    "confidence": round(_confidence(probability), 4),
                    "latency_ms": int(decision.raw.get("latency_ms", 0)),
                    "input_tokens": int(decision.raw.get("input_tokens", 0)),
                }
            )
    return scores, calls


def _select(
    pool: dict[str, RetrievalHit],
    scores: dict[str, float],
    config: PipelineConfig,
    question: str = "",
) -> list[RetrievalHit]:
    terms = _terms(question)

    def selection_score(hit: RetrievalHit) -> float:
        score = scores.get(hit.node_id, 0.0)
        title_terms = _terms(hit.title)
        if terms and title_terms:
            score += 0.15 * len(terms & title_terms) / len(title_terms)
        return score

    ranked = sorted(
        pool.values(),
        key=lambda hit: (-selection_score(hit), -hit.score, hit.node_id),
    )
    eligible = [
        hit for hit in ranked if scores.get(hit.node_id, 0.0) >= config.relevance_floor
    ]
    # Summaries are routes, not evidence. Prefer leaves for exact numbers and
    # rules; keep a summary only when too few chunks pass the floor.
    leaves = [hit for hit in eligible if hit.kind == "chunk"]
    summaries = [hit for hit in eligible if hit.kind != "chunk"]
    kept = leaves[: config.evidence_limit]
    if not kept:
        kept = summaries[: config.evidence_limit]
    return kept


def _delegate(
    router: LlamaRouter,
    model: str,
    question: str,
    evidence: str,
    criterion: str,
) -> tuple[bool, str]:
    prompt = (
        f"Question: {question}\n\n"
        f"Criterion: {criterion}\n\n"
        f"Evidence:\n{evidence}\n\n"
        "Reply with one word: yes or no."
    )
    result = router.chat(
        [
            {
                "role": "system",
                "content": "You are a strict grader. Reply with one word only.",
            },
            {"role": "user", "content": prompt},
        ],
        model=model,
        max_tokens=100,
        temperature=0.0,
        skip_reasoning=True,
    )
    first = result.text.strip().lower().split()
    answer = first[0].strip(".,:;") if first else ""
    return answer == "yes", result.text.strip()


def _rewrite(
    router: LlamaRouter,
    model: str,
    question: str,
    action: str,
    previous_query: str,
    selected: list[RetrievalHit],
) -> list[str]:
    count = 2 if action == "decompose" else 1
    titles = "\n".join(f"- {hit.title}" for hit in selected[:6]) or "- none"
    prompt = (
        f"Question: {question}\n"
        f"Chosen action: {action} ({ACTION_OPTIONS.get(action, '')})\n"
        f"Previous search: {previous_query}\n"
        f"Evidence titles so far:\n{titles}\n\n"
        f"Write {count} search {'queries' if count > 1 else 'query'} for a local "
        "document index. Use words that are likely to appear in the records. "
        "Do not answer the question. Return one query per line, no bullets, no quotes."
    )
    result = router.chat(
        [
            {
                "role": "system",
                "content": "You write short search queries. Return only the queries.",
            },
            {"role": "user", "content": prompt},
        ],
        model=model,
        max_tokens=200,
        temperature=0.2,
        skip_reasoning=True,
    )
    lines = [line.strip(" -\"'") for line in result.text.splitlines() if line.strip()]
    queries = [line for line in lines if len(line.split()) >= 2][:count]
    return queries or [question]


def _write_answer(
    router: LlamaRouter,
    model: str,
    place: Place,
    question: str,
    selected: list[RetrievalHit],
    max_tokens: int,
) -> str:
    evidence = _writer_evidence(selected, question)
    prompt = (
        f"Question: {question}\n\n"
        f"Evidence from {place.title}:\n{evidence}\n\n"
        "Answer in at most 80 words. Start with the fact that answers the question, "
        "not with a restatement of the question, an explanation of a name, or Yes "
        "or No unless the question is a yes or no question. Answer every part "
        "of the question. Include the exact names, dates, numbers, durations, and "
        "unit labels from the evidence when they answer it, and copy proper names "
        "exactly as written. Do not mention rules, procedures, "
        "or background that the question did not ask for, and do not comment on "
        "other actions that were not asked about. If the question asks what a "
        "component adds or how it works, explain its role and structure, not an "
        "evaluation report or a metric. For a yes or no rule question, "
        "compare the stated value with the stated limit. If the value is above a "
        "limit, the action is not allowed: start with No. Do not say the decision "
        "cannot be made when the evidence contains both the rule and the value. "
        "Use only the evidence above. Put the node id in square brackets after "
        "each factual sentence, using the id exactly as shown at the start of the "
        "evidence block, for example [rr-032:001]. If two records disagree, say "
        "so. If the evidence does not answer the question, say what is missing "
        "instead of guessing."
    )
    result = router.chat(
        [
            {
                "role": "system",
                "content": (
                    f"You are the reference librarian for {place.title}. You answer "
                    "only from the supplied records, never from general knowledge. "
                    "Every factual sentence needs a citation. Answer only what was asked. "
                    "A stated limit applies to a stated value; compare the two "
                    "before you write."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
        skip_reasoning=True,
    )
    return result.text


def _fix_polarity(text: str) -> str:
    """Correct a known failure: a yes/no opener that contradicts the body."""

    match = re.match(r"^(\s*)(Yes|No)(\b[.,:]?\s*)", text, re.IGNORECASE)
    if not match or match.group(2).lower() != "yes":
        return text
    body = text[match.end() :].lower()
    negative = (
        "cannot proceed",
        "can not proceed",
        "not allowed",
        "is not permitted",
        "must not",
        "prohibited",
        "exceeds the stated limit",
        "exceeds the limit",
    )
    if any(phrase in body for phrase in negative):
        return f"{match.group(1)}No{match.group(3)}" + text[match.end() :]
    return text


def _is_yes_no_question(question: str) -> bool:
    last = re.split(r"[.;]\s+|,\s+", question.strip())[-1].strip()
    return bool(
        re.match(
            r"^(is|are|was|were|do|does|did|can|could|may|might|should|would|will|"
            r"has|have|had|must)\b",
            last,
            re.IGNORECASE,
        )
    )


def _polish_answer(text: str, question: str) -> str:
    """Remove stray yes/no openers from factual questions and tails from any."""

    text = _fix_polarity(text)
    text = re.sub(
        r"^(No|Yes)(?![.,:;!?])\s+(?=(?:\[|\d|[A-Z]))",
        r"\1. ",
        text,
        count=1,
    )
    if len(text.split()) > 4:
        text = re.sub(
            r"\s+\b(Yes|No)\b[.!]?(?:\s*\[[^\]]+\])*\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        )
    if not _is_yes_no_question(question):
        text = re.sub(
            r"^\s*(Yes|No)\s*(?:[.,:;!-]\s*|(?=\[))",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
    text = re.sub(r"^\[[^\]]+\][.,;:]?\s+(?=\S)", "", text, count=1)
    if len(text.split()) > 4:
        text = re.sub(r"\n\s*\[[^\]]+\][.,;:]?\s*$", "", text, count=1)
    return text.strip()


def _trim_answer(text: str, max_words: int = 90) -> str:
    """Keep the answer near the requested length, cutting at a sentence end."""

    words = text.split()
    if len(words) <= max_words:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept: list[str] = []
    count = 0
    for sentence in sentences:
        size = len(sentence.split())
        if count + size > max_words:
            break
        kept.append(sentence)
        count += size
    if not kept:
        return " ".join(words[:max_words]).rstrip(" ,;:") + "."
    return " ".join(kept).strip()


def _compact_evidence(hits: list[RetrievalHit], limit: int = 4, chars: int = 900) -> str:
    blocks = []
    for hit in hits[:limit]:
        text = hit.text if len(hit.text) <= chars else hit.text[:chars].rsplit(" ", 1)[0] + "..."
        blocks.append(f"[{hit.node_id}] {hit.title}\n{text}")
    return "\n\n".join(blocks)


def _repair(
    router: LlamaRouter,
    model: str,
    question: str,
    answer: str,
    selected: list[RetrievalHit],
) -> str:
    prompt = (
        f"Question: {question}\n\n"
        f"Draft answer:\n{answer}\n\n"
        f"Evidence:\n{_compact_evidence(selected)}\n\n"
        "Rewrite the draft so every factual sentence is supported by the evidence. "
        "Remove anything the evidence does not support. Keep the citations, and add "
        "a citation where one is missing. If a claim cannot be supported, delete it. "
        "Return only the corrected answer, never the evidence and never a preamble."
    )
    result = router.chat(
        [
            {
                "role": "system",
                "content": "You repair answers against evidence. Do not add outside facts.",
            },
            {"role": "user", "content": prompt},
        ],
        model=model,
        max_tokens=800,
        temperature=0.0,
        skip_reasoning=True,
    )
    return result.text


def _normalize_citations(answer: str, selected: list[RetrievalHit]) -> str:
    """Keep node ids, translate known titles, drop labels the model invented."""

    valid = {hit.node_id for hit in selected}
    by_title: dict[str, str] = {}
    for hit in selected:
        by_title.setdefault(hit.title.casefold(), hit.node_id)

    def replace(match: re.Match[str]) -> str:
        token = match.group(1).strip()
        if token in valid:
            return match.group(0)
        mapped = by_title.get(token.casefold())
        if mapped:
            return f"[{mapped}]"
        return ""

    cleaned = BRACKET_RE.sub(replace, answer)
    cleaned = re.sub(
        r"\((?:source:\s*)?rr-\d{3}(?::\d{3})?\)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _ensure_citations(
    answer: str,
    selected: list[RetrievalHit],
) -> tuple[str, str]:
    """Return an answer with citations and how they were attached.

    The writer is asked to cite inline. When it ignores that, a short source
    footer keeps the claim traceable instead of pretending the answer is bare.
    """

    cited, _ = _citations(answer, selected)
    if cited:
        return answer, "inline"
    haystack = answer.casefold()
    preferred = [hit for hit in selected if hit.title.casefold() in haystack]
    ordered = preferred + sorted(selected, key=lambda hit: hit.rank)
    sources: list[str] = []
    for hit in ordered:
        if hit.node_id not in sources:
            sources.append(hit.node_id)
        if len(sources) == 3:
            break
    return f"{answer.rstrip()}\n\nSources: " + ", ".join(f"[{item}]" for item in sources), "footer"


def _citations(
    answer: str,
    selected: list[RetrievalHit],
) -> tuple[list[dict[str, Any]], list[str]]:
    by_id = {hit.node_id: hit for hit in selected}
    cited: list[dict[str, Any]] = []
    unknown: list[str] = []
    seen: set[str] = set()
    for match in CITATION_RE.finditer(answer):
        node_id = match.group(1)
        if node_id in seen:
            continue
        seen.add(node_id)
        hit = by_id.get(node_id)
        if hit is None:
            unknown.append(node_id)
            continue
        cited.append(
            {
                "node_id": hit.node_id,
                "title": hit.title,
                "doc_ids": list(hit.doc_ids),
                "level": hit.level,
            }
        )
    return cited, unknown


def answer_question(
    router: LlamaRouter,
    conn: sqlite3.Connection,
    place: Place,
    question: str,
    config: PipelineConfig | None = None,
) -> dict[str, Any]:
    config = config or PipelineConfig()
    judge_model = place.models.get("judge", "d1-3b")
    writer_model = place.models.get("writer", "lfm2-8b")
    embed_model = place.models.get("embedding", "embeddinggemma-2")
    started = time.monotonic()
    trace: list[dict[str, Any]] = []
    pool: dict[str, RetrievalHit] = {}
    scores: dict[str, float] = {}
    relevance_calls: list[dict[str, Any]] = []
    queries = [question]
    refeeds = 0
    sufficient = False
    selected: list[RetrievalHit] = []

    for attempt in range(config.max_refeeds + 1):
        retrieval_started = time.monotonic()
        for query in queries:
            vector = router.embed([query], model=embed_model)[0]
            hits = collapsed_search(conn, place.id, vector, limit=config.retrieve_limit)
            _merge(pool, hits)
        trace.append(
            {
                "step": "retrieve",
                "attempt": attempt,
                "queries": list(queries),
                "hits": len(pool),
                "top_score": round(max((hit.score for hit in pool.values()), default=0.0), 4),
                "latency_ms": int((time.monotonic() - retrieval_started) * 1000),
            }
        )
        if not pool:
            trace.append({"step": "refuse", "reason": "no passages retrieved"})
            return {
                "place_id": place.id,
                "question": question,
                "mode": "raptor",
                "answer": "I could not find any passages for that question in this corpus.",
                "can_answer": False,
                "warning": "no retrieval hits",
                "citations": [],
                "results": [],
                "trace": trace,
                "refeeds": refeeds,
                "timings": {"total_ms": int((time.monotonic() - started) * 1000)},
            }

        new_scores, calls = _relevance(router, judge_model, question, list(pool.values()))
        scores.update(new_scores)
        relevance_calls.extend(calls)
        selected = _select(pool, scores, config, question)
        trace.append(
            {
                "step": "relevance",
                "attempt": attempt,
                "scored": len(calls),
                "kept": len(selected),
                "min_kept": round(min((scores.get(hit.node_id, 0.0) for hit in selected), default=0.0), 4),
                "latency_ms": sum(call["latency_ms"] for call in calls),
                "scores": calls,
            }
        )
        if not selected:
            trace.append({"step": "refuse", "reason": "no passage passed the relevance floor"})
            return {
                "place_id": place.id,
                "question": question,
                "mode": "raptor",
                "answer": (
                    "I found candidate passages, but the decision model judged none of "
                    "them relevant enough to answer."
                ),
                "can_answer": False,
                "warning": "all passages below the relevance floor",
                "citations": [],
                "results": [hit.as_dict() for hit in pool.values()],
                "trace": trace,
                "refeeds": refeeds,
                "timings": {"total_ms": int((time.monotonic() - started) * 1000)},
            }

        evidence = _evidence_text(selected)
        sufficiency_started = time.monotonic()
        decision = router.systemone(
            f"Question: {question}\n\nEvidence:\n{evidence}",
            {
                "sufficient": noul(
                    "Does the evidence contain enough facts to answer the question "
                    "specifically, including the name, number, or rule that the "
                    "question asks for?"
                )
            },
            model=judge_model,
        ).get("sufficient")
        if decision is None:
            raise RuntimeError("decision model returned no sufficiency answer")
        trace_entry = {
            "step": "sufficient",
            "attempt": attempt,
            "probability": round(float(decision.value), 4),
            "confidence": round(_confidence(float(decision.value)), 4),
            "band": _band(_confidence(float(decision.value)), config),
            "delegated": False,
            "source": "d1",
            "latency_ms": int(decision.raw.get("latency_ms", 0)),
        }
        sufficient = float(decision.value) >= config.sufficient_threshold
        if trace_entry["band"] == "low" and config.delegate_low_confidence:
            delegated, raw = _delegate(
                router,
                writer_model,
                question,
                evidence,
                "The evidence must contain the specific fact needed to answer.",
            )
            trace_entry.update(
                {"delegated": True, "source": "lfm", "delegate_answer": raw[:300]}
            )
            sufficient = delegated
        trace_entry["accepted"] = sufficient
        trace_entry["elapsed_ms"] = int((time.monotonic() - sufficiency_started) * 1000)
        trace.append(trace_entry)

        if sufficient or attempt >= config.max_refeeds:
            break

        action_decision: Decision = router.systemone(
            f"Question: {question}\n\nEvidence so far:\n{evidence}",
            {
                "action": choice(
                    "The evidence is not sufficient. What should the next search do?",
                    ACTION_OPTIONS,
                )
            },
            model=judge_model,
        )["action"]
        action = str(action_decision.value)
        trace.append(
            {
                "step": "action",
                "attempt": attempt,
                "choice": action,
                "probabilities": action_decision.probabilities,
                "confidence": action_decision.confidence,
                "latency_ms": int(action_decision.raw.get("latency_ms", 0)),
            }
        )
        queries = _rewrite(router, writer_model, question, action, queries[0], selected)
        refeeds += 1
        trace.append({"step": "rewrite", "attempt": attempt, "queries": queries})

    if not sufficient:
        closest = ", ".join(f"{hit.title} [{hit.node_id}]" for hit in selected[:4])
        return {
            "place_id": place.id,
            "question": question,
            "mode": "raptor",
            "answer": (
                "I could not find enough evidence to answer that after "
                f"{refeeds} refeed(s). The closest records were: {closest}."
            ),
            "can_answer": False,
            "warning": "evidence stayed insufficient",
            "citations": [],
            "results": [
                {**hit.as_dict(), "relevance": round(scores.get(hit.node_id, 0.0), 4)}
                for hit in selected
            ],
            "trace": trace,
            "refeeds": refeeds,
            "timings": {"total_ms": int((time.monotonic() - started) * 1000)},
        }

    write_started = time.monotonic()
    writer_hits = _writer_hits(selected, question, config.writer_evidence_limit)
    raw_answer = _write_answer(
        router,
        writer_model,
        place,
        question,
        writer_hits,
        config.writer_max_tokens,
    )
    answer = _polish_answer(_trim_answer(raw_answer), question)
    trace.append(
        {
            "step": "write",
            "attempt": refeeds,
            "chars": len(answer),
            "raw_chars": len(raw_answer),
            "latency_ms": int((time.monotonic() - write_started) * 1000),
        }
    )
    answer = _normalize_citations(answer, writer_hits)
    answer, citation_mode = _ensure_citations(answer, writer_hits)
    trace.append({"step": "cite", "mode": citation_mode})

    evidence = _evidence_text(writer_hits)
    judge_evidence = _compact_evidence(writer_hits)
    grounded_decision = router.systemone(
        f"Question: {question}\n\nAnswer:\n{answer}\n\nEvidence:\n{judge_evidence}",
        {
            "grounded": noul(
                "Is every factual claim in the answer supported by the evidence? "
                "Ignore phrasing and citation style."
            )
        },
        model=judge_model,
    ).get("grounded")
    if grounded_decision is None:
        raise RuntimeError("decision model returned no groundedness answer")
    grounded = float(grounded_decision.value) >= config.grounded_threshold
    grounded_confidence = _confidence(float(grounded_decision.value))
    grounded_band = _band(grounded_confidence, config)
    trace.append(
        {
            "step": "grounded",
            "probability": round(float(grounded_decision.value), 4),
            "confidence": round(grounded_confidence, 4),
            "band": grounded_band,
            "delegated": False,
            "source": "d1",
            "accepted": grounded,
            "latency_ms": int(grounded_decision.raw.get("latency_ms", 0)),
        }
    )
    warning = None
    if not grounded and grounded_band == "low" and config.delegate_low_confidence:
        delegated, raw = _delegate(
            router,
            writer_model,
            question,
            judge_evidence,
            "Every factual claim in the answer must be supported by the evidence.",
        )
        trace[-1].update({"delegated": True, "source": "lfm", "delegate_answer": raw[:300]})
        trace[-1]["accepted"] = delegated
        grounded = delegated

    if not grounded:
        repaired = _repair(router, writer_model, question, answer, writer_hits)
        echoed = len(repaired) > 2200 or "\nEvidence:" in repaired
        if echoed:
            trace.append({"step": "repair", "rejected": True, "chars": len(repaired)})
            warning = "repair echoed the evidence; kept the draft answer"
        else:
            answer = _polish_answer(
                _trim_answer(_normalize_citations(repaired, writer_hits)), question
            )
            answer, citation_mode = _ensure_citations(answer, writer_hits)
            trace.append(
                {"step": "repair", "chars": len(answer), "citation_mode": citation_mode}
            )
        check = router.systemone(
            f"Question: {question}\n\nAnswer:\n{answer}\n\nEvidence:\n{judge_evidence}",
            {
                "grounded": noul(
                    "Is every factual claim in the repaired answer supported by the evidence?"
                )
            },
            model=judge_model,
        ).get("grounded")
        if check is not None:
            repaired_probability = float(check.value)
            trace.append(
                {
                    "step": "grounded_after_repair",
                    "probability": round(repaired_probability, 4),
                    "confidence": round(_confidence(repaired_probability), 4),
                    "accepted": repaired_probability >= config.grounded_threshold,
                    "latency_ms": int(check.raw.get("latency_ms", 0)),
                }
            )
            if repaired_probability < config.grounded_threshold:
                warning = "answer may contain claims that the evidence does not support"
        else:
            warning = "answer may contain claims that the evidence does not support"

    answer = _polish_answer(answer, question)
    citations, unknown = _citations(answer, selected)
    if not citations:
        warning = (warning + "; " if warning else "") + "answer has no citations"
    if unknown:
        warning = (warning + "; " if warning else "") + "unknown citation ids: " + ", ".join(unknown)

    return {
        "place_id": place.id,
        "question": question,
        "mode": "raptor",
        "answer": answer,
        "can_answer": True,
        "warning": warning,
        "citations": citations,
        "results": [
            {**hit.as_dict(), "relevance": round(scores.get(hit.node_id, 0.0), 4)}
            for hit in selected
        ],
        "trace": trace,
        "refeeds": refeeds,
        "timings": {"total_ms": int((time.monotonic() - started) * 1000)},
    }
