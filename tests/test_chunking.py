import pytest

from rptr.chunking import chunk_text


def test_long_block_uses_overlap():
    text = " ".join(f"w{index}" for index in range(10))

    chunks = chunk_text(text, "doc", max_words=5, overlap_words=1)

    assert [chunk.words for chunk in chunks] == [5, 5, 2]
    assert chunks[0].text.endswith("w4")
    assert chunks[1].text.startswith("w4")
    assert chunks[2].text.startswith("w8")


def test_paragraphs_merge_and_split():
    text = ("alpha " * 300).strip() + "\n\n" + ("beta " * 300).strip()

    chunks = chunk_text(text, "doc", max_words=380, overlap_words=48)

    assert len(chunks) == 2
    assert chunks[0].words == 300
    assert chunks[1].words == 348
    assert all(chunk.words <= 380 for chunk in chunks)
    assert chunks[1].text.startswith("alpha")


def test_empty_text_returns_no_chunks():
    assert chunk_text("", "doc") == []


def test_overlap_must_be_smaller_than_chunk():
    with pytest.raises(ValueError):
        chunk_text("a b c", "doc", max_words=10, overlap_words=10)
