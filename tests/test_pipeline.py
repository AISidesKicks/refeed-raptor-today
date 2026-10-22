from types import SimpleNamespace

import numpy as np
import pytest

from rptr import pipeline
from rptr.llm import ChatResult, Decision
from rptr.pipeline import (
    PipelineConfig,
    _citations,
    _fix_polarity,
    _polish_answer,
    _select,
    _trim_answer,
    answer_question,
)
from rptr.retrieval import RetrievalHit


class FakeRouter:
    def __init__(self):
        self.sufficiency = [0.2, 0.9]
        self.chat_prompts = []
        self.systemone_calls = 0

    def embed(self, texts, model="embeddinggemma-2", batch_size=16):
        return np.ones((len(texts), 2), dtype=np.float32) / np.sqrt(2)

    def systemone(self, state, questions, model="d1-3b"):
        self.systemone_calls += 1
        answers = {}
        for key, question in questions.items():
            if key == "sufficient":
                value = self.sufficiency.pop(0)
                answers[key] = Decision("noul", value, raw={"latency_ms": 1})
            elif key == "action":
                answers[key] = Decision(
                    "choice",
                    "broaden",
                    probabilities={"broaden": 0.9, "keep": 0.1},
                    confidence=0.8,
                    raw={"latency_ms": 1},
                )
            elif key == "grounded":
                answers[key] = Decision("noul", 0.9, raw={"latency_ms": 1})
            elif question["type"] == "noul":
                answers[key] = Decision("noul", 0.92, raw={"latency_ms": 1})
        return answers

    def chat(self, messages, model="lfm2-8b", max_tokens=768, temperature=0.2, extra=None, skip_reasoning=False):
        prompt = messages[-1]["content"]
        self.chat_prompts.append(prompt)
        if "Previous search:" in prompt:
            return ChatResult("drone wind limit", model, latency_ms=1)
        return ChatResult("The wind limit is 30 km/h [c1].", model, latency_ms=1)


def fake_hits():
    return [
        RetrievalHit(
            node_id="c1",
            kind="chunk",
            level=0,
            title="Drone rules",
            text="The drone wind limit is 30 km/h.",
            doc_ids=("rr-032",),
            children=(),
            score=0.9,
            rank=1,
        ),
        RetrievalHit(
            node_id="c2",
            kind="summary",
            level=1,
            title="Field operations",
            text="Drone flights are approved by a ranger.",
            doc_ids=("rr-032", "rr-034"),
            children=("c1",),
            score=0.8,
            rank=2,
        ),
    ]


def test_answer_question_refeeds_and_cites(monkeypatch):
    monkeypatch.setattr(pipeline, "collapsed_search", lambda *args, **kwargs: fake_hits())
    place = SimpleNamespace(
        id="test",
        title="Test Reserve",
        models={"judge": "d1", "writer": "lfm", "embedding": "emb"},
    )
    router = FakeRouter()
    result = answer_question(
        router,
        None,
        place,
        "What is the drone wind limit?",
        PipelineConfig(max_refeeds=1, delegate_low_confidence=False),
    )

    assert result["can_answer"] is True
    assert result["refeeds"] == 1
    assert result["citations"][0]["node_id"] == "c1"
    steps = [item["step"] for item in result["trace"]]
    assert steps.count("retrieve") == 2
    assert "action" in steps
    assert "rewrite" in steps
    assert "write" in steps
    assert "grounded" in steps
    assert result["warning"] is None


def test_answer_question_refuses_when_evidence_stays_insufficient(monkeypatch):
    monkeypatch.setattr(pipeline, "collapsed_search", lambda *args, **kwargs: fake_hits())
    place = SimpleNamespace(
        id="test",
        title="Test Reserve",
        models={"judge": "d1", "writer": "lfm", "embedding": "emb"},
    )
    router = FakeRouter()
    router.sufficiency = [0.1, 0.1]
    result = answer_question(
        router,
        None,
        place,
        "What is the drone wind limit?",
        PipelineConfig(max_refeeds=1, delegate_low_confidence=False),
    )
    assert result["can_answer"] is False
    assert "could not find enough evidence" in result["answer"]
    assert result["refeeds"] == 1


def test_citations_drop_unknown_ids():
    hits = fake_hits()
    cited, unknown = _citations("A fact [c1], another [bogus], repeat [c1].", hits)
    assert [item["node_id"] for item in cited] == ["c1"]
    assert unknown == ["bogus"]


def test_missing_decision_raises(monkeypatch):
    monkeypatch.setattr(pipeline, "collapsed_search", lambda *args, **kwargs: fake_hits())

    class Broken(FakeRouter):
        def systemone(self, state, questions, model="d1-3b"):
            return {
                key: Decision("noul", 0.9, raw={"latency_ms": 1})
                for key, question in questions.items()
                if question["type"] == "noul" and key != "sufficient"
            }

    place = SimpleNamespace(
        id="test", title="Test", models={"judge": "d1", "writer": "lfm", "embedding": "emb"}
    )
    with pytest.raises(RuntimeError):
        answer_question(Broken(), None, place, "question")


def test_trim_answer_stops_at_a_sentence():
    text = "One short sentence. " + "word " * 300 + "end."
    trimmed = _trim_answer(text, max_words=20)
    assert trimmed == "One short sentence."


def test_select_prefers_chunks_over_summaries():
    hits = fake_hits()
    scores = {"c1": 0.9, "c2": 0.95}
    selected = _select({hit.node_id: hit for hit in hits}, scores, PipelineConfig())
    assert [hit.node_id for hit in selected] == ["c1"]


def test_polish_answer_adds_a_period_after_a_bare_no():
    text = "No [rr-032:001] The wind is above the limit."
    assert _polish_answer(text, "May the flight proceed?").startswith("No. [rr-032:001]")


def test_fix_polarity_corrects_a_contradictory_yes():
    text = "Yes. The wind is 35 km/h, which exceeds the limit, so the flight cannot proceed."
    assert _fix_polarity(text).startswith("No.")
    assert _fix_polarity("Yes. The flight may proceed.").startswith("Yes.")


def test_polish_answer_keeps_no_for_a_yes_no_question():
    text = "No. The wind is 35 km/h, which exceeds the limit, so the flight cannot proceed."
    assert _polish_answer(text, "May it proceed?").startswith("No.")


def test_polish_answer_strips_yes_from_a_factual_question():
    text = "Yes [rr-034:000]. Elin Ward approved the flight."
    assert _polish_answer(text, "Which ranger approved the flight?") == (
        "Elin Ward approved the flight."
    )


def test_polish_answer_drops_a_trailing_no():
    text = "The total was 21 chicks. No."
    assert _polish_answer(text, "How many chicks fledged?") == (
        "The total was 21 chicks."
    )


def test_polish_answer_drops_a_trailing_no_before_a_citation():
    text = "The bird was treated for lead poisoning. No. [rr-037:000]"
    assert _polish_answer(text, "Why was the bird in the news?") == (
        "The bird was treated for lead poisoning."
    )
