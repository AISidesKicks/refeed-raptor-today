import pytest

from rptr.calibration import _bands, _bins, _brier, _sample, build_page


def _rows():
    return [
        {
            "id": "q1",
            "type": "single",
            "citation_hit": True,
            "sufficiency": {
                "probability": 0.95,
                "confidence": 0.9,
                "band": "high",
                "source": "d1",
                "accepted": True,
            },
        },
        {
            "id": "q2",
            "type": "single",
            "citation_hit": False,
            "sufficiency": {
                "probability": 0.45,
                "confidence": 0.1,
                "band": "low",
                "source": "lfm",
                "accepted": False,
            },
        },
    ]


def test_brier_score_is_the_mean_squared_error():
    sample = _sample(_rows())

    assert _brier(sample) == pytest.approx(((0.95 - 1) ** 2 + (0.45 - 0) ** 2) / 2)


def test_bins_keep_the_counts_and_the_observed_rate():
    bins = _bins(_sample(_rows()))

    assert bins[9]["count"] == 1
    assert bins[9]["observed"] == 1.0
    assert bins[4]["count"] == 1
    assert bins[4]["observed"] == 0.0
    assert sum(item["count"] for item in bins) == 2


def test_bands_split_the_delegated_questions():
    bands = {item["band"]: item for item in _bands(_sample(_rows()))}

    assert bands["high"]["count"] == 1
    assert bands["high"]["delegated"] == 0
    assert bands["low"]["count"] == 1
    assert bands["low"]["delegated"] == 1


def test_page_has_the_numbers_and_the_caveat():
    page = build_page("test-place", _rows())

    assert "<title>Calibration" in page
    assert "0.103" in page
    assert "test-place" in page
    assert "citation hit" in page
    assert "not a faithfulness score" in page
