"""Paragraph-aware chunking for the local index.

The real embedder uses tokens. This first slice uses words and a token estimate
so the corpus can be inspected without loading EmbeddingGemma 2. The chunk
target is 380 words, about 512 tokens, with a 48-word overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    ordinal: int
    text: str
    words: int
    token_estimate: int


def _split_blocks(text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def _tail_words(text: str, count: int) -> list[str]:
    if count <= 0:
        return []
    return text.split()[-count:]


def _split_long_block(block: str, max_words: int, overlap_words: int) -> list[str]:
    words = block.split()
    if len(words) <= max_words:
        return [block]
    pieces: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        pieces.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(end - overlap_words, start + 1)
    return pieces


def chunk_text(
    text: str,
    doc_id: str,
    max_words: int = 380,
    overlap_words: int = 48,
) -> list[Chunk]:
    """Split a document into readable chunks with a small overlap."""

    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be between 0 and max_words")

    pieces: list[str] = []
    current: list[str] = []
    current_words = 0

    for block in _split_blocks(text):
        block_words = len(block.split())
        if block_words > max_words:
            if current:
                pieces.append("\n\n".join(current))
                current = []
                current_words = 0
            pieces.extend(_split_long_block(block, max_words, overlap_words))
            continue

        if current and current_words + block_words > max_words:
            pieces.append("\n\n".join(current))
            tail = _tail_words(pieces[-1], overlap_words)
            available = max_words - block_words
            if available <= 0:
                tail = []
            elif len(tail) > available:
                tail = tail[-available:]
            current = [" ".join(tail)] if tail else []
            current_words = len(tail)

        current.append(block)
        current_words += block_words

    if current:
        pieces.append("\n\n".join(current))

    chunks: list[Chunk] = []
    for ordinal, piece in enumerate(piece.strip() for piece in pieces if piece.strip()):
        words = len(piece.split())
        chunks.append(
            Chunk(
                id=f"{doc_id}:{ordinal:03d}",
                doc_id=doc_id,
                ordinal=ordinal,
                text=piece,
                words=words,
                token_estimate=round(words * 1.3),
            )
        )
    return chunks
