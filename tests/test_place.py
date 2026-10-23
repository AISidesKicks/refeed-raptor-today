import json
from pathlib import Path

import pytest

from rptr.place import PlaceError, _load_unknown_questions, load_place

PLACE = Path(__file__).resolve().parents[1] / "lab" / "demos" / "raptor-reserve"


def test_load_reference_place():
    place = load_place(PLACE)

    assert place.id == "raptor-reserve"
    assert len(place.documents) == 100
    assert len(place.questions) == 50
    assert len(place.script) == 7
    assert len(place.unknown_questions) == 12
    assert all(not question.gold for question in place.unknown_questions)
    assert all(question.expected == "refusal" for question in place.unknown_questions)
    assert place.words >= 50000
    assert all(question.gold for question in place.questions)
    assert all(document.words >= 500 for document in place.documents)
    assert len({document.id for document in place.documents}) == 100


def test_missing_demo_file(tmp_path):
    with pytest.raises(PlaceError):
        load_place(tmp_path)


def test_document_metadata_is_parsed():
    place = load_place(PLACE)
    charter = next(document for document in place.documents if document.id == "rr-001")

    assert charter.title == "Reserve Charter"
    assert charter.category == "Governance"
    assert charter.author == "Board of Trustees"
    assert charter.source == "Raptor Reserve internal record"
    assert charter.text.startswith("Raptor Reserve is a nonprofit")


def test_unknown_question_with_gold_is_rejected(tmp_path):
    path = tmp_path / "unknown.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "u01",
                "question": "What is the capital of France?",
                "type": "unknown",
                "expected": "refusal",
                "gold": ["rr-001"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(PlaceError, match="must not have gold"):
        _load_unknown_questions(path)


def test_unknown_question_needs_an_expected_outcome(tmp_path):
    path = tmp_path / "unknown.jsonl"
    path.write_text(
        json.dumps({"id": "u01", "question": "What is the capital of France?"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(PlaceError, match="needs id, question, and expected"):
        _load_unknown_questions(path)


def test_unknown_question_ids_are_unique(tmp_path):
    path = tmp_path / "unknown.jsonl"
    record = {"id": "u01", "question": "Who painted the Mona Lisa?", "expected": "refusal"}
    path.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(PlaceError, match="duplicate question id"):
        _load_unknown_questions(path)
