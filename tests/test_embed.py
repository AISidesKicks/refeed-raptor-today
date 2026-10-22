import numpy as np

from rptr.embed import chunk_text_for_embedding, cosine_search


def test_chunk_text_keeps_the_document_title():
    text = chunk_text_for_embedding("Reserve Charter", "The reserve opens at dawn.")
    assert text.startswith("Reserve Charter")
    assert "opens at dawn" in text


def test_cosine_search_orders_and_limits():
    matrix = np.array([[1.0, 0.0], [0.8, 0.6], [0.0, 1.0]], dtype=np.float32)
    hits = cosine_search(["a", "b", "c"], matrix, np.array([1.0, 0.0]), limit=2)
    assert [hit.node_id for hit in hits] == ["a", "b"]
    assert hits[0].score == 1.0


def test_cosine_search_empty_input():
    hits = cosine_search([], np.zeros((0, 3)), np.zeros(3), limit=5)
    assert hits == []
