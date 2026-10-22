from pathlib import Path

import pytest

from rptr.place import PlaceError, load_place

PLACE = Path(__file__).resolve().parents[1] / "lab" / "demos" / "raptor-reserve"


def test_load_reference_place():
    place = load_place(PLACE)

    assert place.id == "raptor-reserve"
    assert len(place.documents) == 100
    assert len(place.questions) == 50
    assert len(place.script) == 7
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
