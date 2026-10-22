# Raptor Reserve

The first demo place for Refeed Raptor.

- 100 original English documents: 85 reserve records and 15 data and methods documents.
- 50 eval questions: 30 reserve-specific, 10 methods, and 10 multi-hop.
- Every document is about 470 to 800 words, with section headings.
- About 200 chunks at 512 tokens with 64 overlap, enough for a three-level RAPTOR tree.
- License: CC BY 4.0. See `NOTICE.md`.

## Build

```bash
python tools/build_corpus.py
```

The builder writes `corpus/*.md`, `corpus/manifest.json`, and `eval.jsonl`. It is deterministic. The source modules in `tools/` are the source of truth; the generated Markdown is the build output.

## Files

- `demo.toml` - place metadata, starter questions, and the model stack.
- `corpus/` - the 100 documents and `manifest.json`.
- `script.jsonl` - the six autoplay turns.
- `eval.jsonl` - the 50 questions with gold documents and expected answers.
- `tools/` - the generator, the seed world, and the long-form expansion.

## Why the documents are long

RAPTOR needs enough chunks to build a tree. A 150-word note is one chunk and does not show the hierarchy. The corpus targets 500 words per document, which gives two chunks at 512 tokens with 64 overlap. The full corpus is about 200 chunks.

## What is fictional

The island, the reserve, the staff, the budget, the counts, and the incidents are fictional. The bird species are real. The methods wing summarizes public research and does not copy it.

## What to ask

Start with the questions in `demo.toml`. The best demo question is the drone wind question: it needs the wind limit from the checklist and the flight approval from the patrol log, so one-shot retrieval often misses it. That is where the refeed loop earns its keep.
