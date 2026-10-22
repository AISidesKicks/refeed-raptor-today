"""BM25 keyword search.

This is the model-free baseline. It is deliberately simple: lowercase tokens,
a small stopword list, and BM25 over the chunks. The real retriever uses
EmbeddingGemma 2 and the RAPTOR tree. Keeping both lets the eval show what the
embeddings add.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    {
        "a", "about", "after", "again", "against", "all", "also", "am", "an",
        "and", "any", "are", "as", "at", "be", "because", "been", "before",
        "being", "below", "between", "both", "but", "by", "can", "could", "did",
        "do", "does", "doing", "down", "during", "each", "few", "for", "from",
        "further", "had", "has", "have", "having", "he", "her", "here", "hers",
        "herself", "him", "himself", "his", "how", "i", "if", "in", "into",
        "is", "it", "its", "itself", "just", "me", "more", "most", "my",
        "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
        "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same",
        "she", "should", "so", "some", "such", "than", "that", "the", "their",
        "theirs", "them", "themselves", "then", "there", "these", "they", "this",
        "those", "through", "to", "too", "under", "until", "up", "very", "was",
        "we", "were", "what", "when", "where", "which", "while", "who", "whom",
        "why", "will", "with", "would", "you", "your", "yours", "yourself",
        "yourselves",
    }
)


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    doc_id: str
    doc_title: str
    category: str
    text: str
    score: float
    rank: int


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_RE.findall(text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def search_rows(
    rows: Iterable[dict[str, Any]],
    query: str,
    limit: int = 8,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[SearchHit]:
    """Score chunks against a query and return the best matches."""

    if limit <= 0:
        return []
    materialized = list(rows)
    query_terms = list(dict.fromkeys(tokenize(query)))
    if not materialized or not query_terms:
        return []

    docs: list[tuple[dict[str, Any], list[str]]] = []
    for row in materialized:
        text_tokens = tokenize(str(row.get("text", "")))
        title_tokens = tokenize(str(row.get("doc_title", "")))
        # Give the title a small field boost without dropping the body.
        docs.append((row, text_tokens + title_tokens + title_tokens))

    count = len(docs)
    average_length = sum(len(tokens) for _, tokens in docs) / max(count, 1)
    document_frequency = {
        term: sum(1 for _, tokens in docs if term in tokens) for term in query_terms
    }

    scored: list[tuple[float, dict[str, Any]]] = []
    for row, tokens in docs:
        length = len(tokens)
        score = 0.0
        for term in query_terms:
            frequency = tokens.count(term)
            if frequency == 0:
                continue
            df = document_frequency[term]
            idf = math.log(1.0 + (count - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1.0 - b + b * length / max(average_length, 1.0))
            score += idf * (frequency * (k1 + 1.0)) / denominator
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
    hits: list[SearchHit] = []
    for rank, (score, row) in enumerate(scored[:limit], start=1):
        hits.append(
            SearchHit(
                chunk_id=str(row["id"]),
                doc_id=str(row["doc_id"]),
                doc_title=str(row.get("doc_title", "")),
                category=str(row.get("category", "")),
                text=str(row.get("text", "")),
                score=round(score, 4),
                rank=rank,
            )
        )
    return hits
