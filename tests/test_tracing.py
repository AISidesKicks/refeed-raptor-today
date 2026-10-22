from __future__ import annotations

import sqlite3
from typing import ClassVar

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from rptr import pipeline, tracing
from rptr.llm import ChatResult, Decision
from rptr.pipeline import answer_question
from rptr.retrieval import RetrievalHit


class FakeRouter:
    def embed(self, texts, model=None):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def systemone(self, state, questions, model=None):
        answers = {}
        for key in questions:
            answers[key] = Decision("noul", 0.9, raw={"latency_ms": 1})
        return answers

    def chat(
        self,
        messages,
        model=None,
        max_tokens=768,
        temperature=0.0,
        extra=None,
        skip_reasoning=False,
    ):
        return ChatResult("Elin Ward approved the flight [rr-034:000].", model, latency_ms=5)


def _hit(node_id: str = "rr-034:000", text: str = "Elin Ward approved the flight.") -> RetrievalHit:
    return RetrievalHit(
        node_id=node_id,
        kind="chunk",
        level=0,
        title="Patrol Log",
        text=text,
        doc_ids=("rr-034",),
        children=(),
        score=0.9,
        rank=1,
    )


class _Place:
    id = "raptor-reserve"
    title = "Raptor Reserve"
    models: ClassVar[dict] = {
        "judge": "d1-3b",
        "writer": "lfm2-8b",
        "embedding": "embeddinggemma-2",
    }


def _place():
    return _Place()


def test_tracing_is_off_without_the_endpoint(monkeypatch):
    monkeypatch.delenv("RPTR_OTLP_ENDPOINT", raising=False)
    tracing.reset()
    assert tracing.enabled() is False
    with tracing.span("raptor.answer") as span:
        assert span is None
    assert tracing.trace_id(None) is None


def test_answer_question_reports_no_trace_id_when_tracing_is_off(monkeypatch):
    monkeypatch.delenv("RPTR_OTLP_ENDPOINT", raising=False)
    tracing.reset()
    monkeypatch.setattr(pipeline, "collapsed_search", lambda *args, **kwargs: [_hit()])
    conn = sqlite3.connect(":memory:")
    result = answer_question(FakeRouter(), conn, _place(), "Which ranger approved it?")
    conn.close()
    assert result["trace_id"] is None


def test_run_is_exported_as_spans(monkeypatch):
    monkeypatch.setenv("RPTR_OTLP_ENDPOINT", "http://127.0.0.1:6006/v1/traces")
    exporter = InMemorySpanExporter()
    tracing.reset()
    tracing.use_exporter(exporter)
    monkeypatch.setattr(pipeline, "collapsed_search", lambda *args, **kwargs: [_hit()])
    try:
        conn = sqlite3.connect(":memory:")
        result = answer_question(FakeRouter(), conn, _place(), "Which ranger approved it?")
        conn.close()
    finally:
        tracing.reset()

    names = [span.name for span in exporter.get_finished_spans()]
    assert "raptor.answer" in names
    assert any(name.startswith("rptr.") for name in names)
    assert result["trace_id"]
    parent = next(span for span in exporter.get_finished_spans() if span.name == "raptor.answer")
    assert parent.attributes["rptr.place"] == "raptor-reserve"
