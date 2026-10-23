from types import SimpleNamespace

import pytest

from rptr import eval as eval_module
from rptr.eval import compare_modes, unknown_metrics
from rptr.place import Question


def _question(question_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=question_id, question=f"Question {question_id}?", type="single")


def test_compare_modes_names_the_fixes_and_the_regressions():
    place = SimpleNamespace(id="test", questions=[_question("q1"), _question("q2"), _question("q3")])
    keyword = {
        "results": [
            {"id": "q1", "first_rank": 2},
            {"id": "q2", "first_rank": 7},
            {"id": "q3", "first_rank": 14},
        ]
    }
    oneshot = {
        "results": [
            {"id": "q1", "citation_hit": False},
            {"id": "q2", "citation_hit": True},
            {"id": "q3", "citation_hit": False},
        ],
        "mean_latency_ms": 100,
    }
    loop = {
        "results": [
            {"id": "q1", "citation_hit": True, "refeeds": 0},
            {"id": "q2", "citation_hit": False, "refeeds": 0},
            {"id": "q3", "citation_hit": False, "refeeds": 1},
        ],
        "mean_latency_ms": 300,
        "mean_refeeds": 0.33,
        "answered": 3,
    }

    comparison = compare_modes(place, keyword, oneshot, loop)

    assert comparison["loop_fixed"] == ["q1"]
    assert comparison["loop_broke"] == ["q2"]
    assert comparison["both_missed"] == ["q3"]
    assert comparison["keyword_hit_at_5"] == pytest.approx(1 / 3, abs=1e-4)
    assert comparison["oneshot_citation_hit_rate"] == pytest.approx(1 / 3, abs=1e-4)
    assert comparison["loop_citation_hit_rate"] == pytest.approx(1 / 3, abs=1e-4)
    assert comparison["loop_mean_refeeds"] == 0.33


def test_unknown_metrics_counts_the_refusals(monkeypatch):
    place = SimpleNamespace(
        id="test",
        unknown_questions=(
            Question(id="u1", question="Who painted the Mona Lisa?", type="unknown", gold=(), expected="refusal"),
            Question(id="u2", question="What is the capital of France?", type="unknown", gold=(), expected="refusal"),
            Question(id="u3", question="Who wrote Pride and Prejudice?", type="unknown", gold=(), expected="refusal"),
        ),
    )

    def fake_answer(router, conn, place, question, config=None):
        refused = "Mona Lisa" not in question
        return {
            "can_answer": not refused,
            "answer": "not enough evidence" if refused else "Paris [rr-001:000]",
            "citations": [] if refused else [{"node_id": "rr-001:000", "doc_ids": ["rr-001"]}],
            "refeeds": 0,
            "warning": None,
            "timings": {"total_ms": 10},
        }

    monkeypatch.setattr(eval_module, "answer_question", fake_answer)

    report = unknown_metrics(None, place, None)

    assert report["questions"] == 3
    assert report["refused"] == 2
    assert report["refusal_rate"] == pytest.approx(2 / 3, abs=1e-4)
    assert [row["id"] for row in report["results"] if not row["refused"]] == ["u1"]
