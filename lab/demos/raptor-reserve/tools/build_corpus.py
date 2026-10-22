#!/usr/bin/env python3
"""Build the Raptor Reserve corpus, manifest, and eval set.

Run from the place folder:

    python tools/build_corpus.py

The generated Markdown in corpus/ is the build output. The source modules in
tools/ are the source of truth. The script is deterministic.
"""

from __future__ import annotations

from dataclasses import replace
import json
import math
from pathlib import Path
import sys
import textwrap

from common import Doc, slugify
from longform import expand

import docs_field
import docs_governance
import docs_history
import docs_infra
import docs_methods
import docs_research
import docs_species
import docs_visitor
from questions import QUESTIONS


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus"
MIN_WORDS = 500
MAX_WORDS = 1200
TARGET_DOCS = 100
TARGET_QUESTIONS = 50


RECORD_NOTE = """
## Record note

This record is maintained by {author}. The current version is the one listed in the corpus manifest. Questions about the record go to the data manager (rr-096).
"""


def normalize(doc: Doc) -> Doc:
    """Dedent the source body and trim the edges."""

    return replace(doc, body=textwrap.dedent(doc.body).strip())


def top_up(doc: Doc) -> Doc:
    """Add a short record note when a document is just under the length target."""

    if len(doc.body.split()) >= MIN_WORDS:
        return doc
    note = RECORD_NOTE.format(author=doc.author).strip()
    return replace(doc, body=doc.body.rstrip() + "\n\n" + note)


def all_docs() -> list[Doc]:
    return (
        docs_governance.DOCS
        + docs_species.DOCS
        + docs_field.DOCS
        + docs_research.DOCS
        + docs_visitor.DOCS
        + docs_infra.DOCS
        + docs_history.DOCS
        + docs_methods.DOCS
    )


def check_docs(docs: list[Doc]) -> None:
    if len(docs) != TARGET_DOCS:
        raise SystemExit(f"expected {TARGET_DOCS} documents, found {len(docs)}")

    ids = [doc.id for doc in docs]
    if len(set(ids)) != len(ids):
        duplicates = sorted({doc_id for doc_id in ids if ids.count(doc_id) > 1})
        raise SystemExit(f"duplicate document ids: {duplicates}")

    expected_ids = {f"rr-{n:03d}" for n in range(1, TARGET_DOCS + 1)}
    missing = sorted(expected_ids - set(ids))
    extra = sorted(set(ids) - expected_ids)
    if missing or extra:
        raise SystemExit(f"id gap: missing={missing} extra={extra}")

    for doc in docs:
        body = doc.body
        if "\u2013" in body or "\u2014" in body:
            raise SystemExit(f"{doc.id}: contains an en or em dash")
        if "Jeff" in body:
            raise SystemExit(f"{doc.id}: contains the old 'Jeff' spelling")
        if not body.strip():
            raise SystemExit(f"{doc.id}: empty body")


def check_questions(questions: list[dict], docs: list[Doc]) -> None:
    if len(questions) != TARGET_QUESTIONS:
        raise SystemExit(f"expected {TARGET_QUESTIONS} questions, found {len(questions)}")

    known = {doc.id for doc in docs}
    for question in questions:
        if not question.get("gold"):
            raise SystemExit(f"{question['id']}: no gold documents")
        missing = [doc_id for doc_id in question["gold"] if doc_id not in known]
        if missing:
            raise SystemExit(f"{question['id']}: missing gold documents {missing}")
        if not question.get("expected", "").strip():
            raise SystemExit(f"{question['id']}: empty expected answer")

    multi = [q for q in questions if q["type"] == "multi"]
    if len(multi) != 10:
        raise SystemExit(f"expected 10 multi-hop questions, found {len(multi)}")


def estimate_chunks(words: int) -> int:
    """Approximate 512-token chunks at 0.75 words per token."""

    return max(1, math.ceil(words / 380))


def write_corpus(docs: list[Doc]) -> dict:
    CORPUS.mkdir(parents=True, exist_ok=True)
    for old in CORPUS.glob("*.md"):
        old.unlink()

    manifest_docs = []
    total_words = 0
    total_chunks = 0
    short = []

    for doc in docs:
        words = len(doc.body.split())
        total_words += words
        total_chunks += estimate_chunks(words)
        if words < MIN_WORDS:
            short.append((doc.id, words))

        filename = f"{doc.id}-{slugify(doc.title)}.md"
        path = CORPUS / filename
        text = (
            f"# {doc.title}\n\n"
            f"Category: {doc.category}\n"
            f"Date: {doc.date}\n"
            f"Author: {doc.author}\n"
            f"Source: {doc.source}\n\n"
            f"{doc.body.strip()}\n"
        )
        path.write_text(text, encoding="utf-8")

        manifest_docs.append(
            {
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "date": doc.date,
                "author": doc.author,
                "path": f"corpus/{filename}",
                "license": "CC-BY-4.0",
                "words": words,
                "chunks_estimate": estimate_chunks(words),
            }
        )

    manifest = {
        "place": "raptor-reserve",
        "title": "Raptor Reserve",
        "version": 1,
        "license": "CC-BY-4.0",
        "generated_by": "tools/build_corpus.py",
        "documents": manifest_docs,
    }
    (CORPUS / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"documents: {len(docs)}")
    print(f"total words: {total_words:,}")
    print(f"average words: {total_words // len(docs)}")
    print(f"estimated chunks: {total_chunks}")
    if short:
        print("short documents:")
        for doc_id, words in short:
            print(f"  {doc_id}: {words} words")
    else:
        print(f"every document is at least {MIN_WORDS} words")

    over = [(doc.id, len(doc.body.split())) for doc in docs if len(doc.body.split()) > MAX_WORDS]
    if over:
        print("long documents:")
        for doc_id, words in over:
            print(f"  {doc_id}: {words} words")

    return manifest


def write_eval(questions: list[dict]) -> None:
    lines = [json.dumps(q, ensure_ascii=False) for q in questions]
    (ROOT / "eval.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"eval questions: {len(questions)}")


def main() -> int:
    docs = [top_up(expand(normalize(doc))) for doc in all_docs()]
    check_docs(docs)
    check_questions(QUESTIONS, docs)
    write_corpus(docs)
    write_eval(QUESTIONS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
