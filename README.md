# Refeed Raptor

A local RAG lab: a RAPTOR summary tree, a small refeed loop, and a System-1 decision model. No cloud model, no API key.

- Public overview: `docs/index.html`
- Design intent: `INTENT.md`
- First corpus: `lab/demos/raptor-reserve/`
- Metrics reference: `mds/metrics.md`

## Quick start

The environment is a pixi workspace named `rptr`. The models run in Docker with the `rptr-` prefix.

```bash
pixi install
pixi run models
pixi run llm-up
pixi run index
pixi run embed
pixi run build-tree
pixi run serve
```

Open `http://localhost:8000`. If port 8000 is taken, pick another:

```bash
RPTR_PORT=8765 pixi run serve
```

The app has four tabs:

- Ask: live RAPTOR retrieval plus the refeed loop, or the keyword floor.
- Replay: the six scripted turns. Recorded mode needs no model, no embeddings, and no GPU. Live mode reruns the turn.
- Corpus: read all 100 documents.
- Eval: run the keyword baseline or RAPTOR retrieval on the 50 questions.

The first startup indexes the corpus. The index is keyed by a content fingerprint, so a restart does not wipe the embeddings or the tree.

## Model stack

One llama.cpp router, three presets, one port on `127.0.0.1:8080`.

| Part | Choice |
| --- | --- |
| Embeddings | EmbeddingGemma 2, Q8_0, 768 dimensions |
| Writer | LFM2.5-8B-A1B, Q4_K_M |
| Decisions | d1-3B, Q8_0, typed `noul` and `choice` calls |
| Server | llama.cpp v0.7.x, image `server-cuda13-b11804` |
| Storage | SQLite plus numpy cosine |
| App | FastAPI, WebSocket, static HTML |

The test card is a 12 GB GPU. The three loaded presets use about 11.1 GB.

## Current metrics

On the 50-question eval set:

| Mode | Recall@5 | Recall@10 | Recall@20 | MRR |
| --- | --- | --- | --- | --- |
| Keyword | 0.98 | 0.98 | 1.00 | 0.829 |
| RAPTOR | 0.96 | 0.98 | 1.00 | 0.861 |

RAPTOR ranks the right passage better and finds every gold document by rank 20. The keyword floor wins Recall@5 by one question. The two known misses are documented in `docs/index.html`.

## Recordings

The model-backed script turns are committed in `lab/demos/raptor-reserve/runs/`. Regenerate them when the corpus or a prompt changes:

```bash
pixi run record
```

Each recording keeps the answer, citations, retrieval results, and the full decision trace. Recorded replay is the mode for the demo video and for readers who only want to click through the pipeline.

## Development

```bash
pixi run test
pixi run ruff check src tests
```

The corpus generator is the source of truth. The Markdown in `corpus/` is the build output.

## License

The corpus is CC BY 4.0. The models keep their own licenses. The code license is separate and not chosen yet. See `NOTICE.md`.
