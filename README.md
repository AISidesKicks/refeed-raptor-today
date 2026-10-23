# Refeed Raptor

![A paper raptor being fed documents by a robot arm in a server room](docs/refeed-raptor.png)

A local RAG lab: a RAPTOR summary tree, a small refeed loop, and a System-1 decision model. No cloud model, no API key.

- Public overview: `docs/index.html`
- Calibration page: `docs/calibration.html`
- Design intent: `INTENT.md`
- First corpus: `lab/demos/raptor-reserve/`
- Eval reports: `lab/demos/raptor-reserve/evals/`
- Metrics reference: `mds/metrics.md`
- Demo video: `docs/assets/videos/refeed-loop.mp4`

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
- Replay: the seven scripted turns. Recorded mode needs no model, no embeddings, and no GPU. Live mode reruns the turn.
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

On the 50-question eval set, three modes:

| Mode | What it does | Citation hit | Mean latency |
| --- | --- | --- | --- |
| One-shot RAPTOR | top 6 passages, one write, no judge | 0.96 | 0.39 s |
| RAPTOR plus the loop | judge, maybe refeed, write, cite, ground | 0.94 | 1.44 s |

Retrieval on the same questions:

| Retriever | Recall@5 | Recall@10 | Recall@20 | MRR |
| --- | --- | --- | --- | --- |
| Keyword | 0.98 | 0.98 | 1.00 | 0.829 |
| RAPTOR | 0.96 | 0.98 | 1.00 | 0.861 |

The loop is slower and one citation hit worse on this curated set. It fixes `q05`, breaks `q08` and `q29` on citation attribution, and both modes miss `q47`. The failures are in `docs/index.html` and `mds/metrics.md`, not hidden.

The loop earns its keep on turn 7 of the demo: one-shot answers 67 osprey chicks with two unrelated records, the loop answers 21 with the season report and the drone log after one refeed. The comparison is committed in `evals/script.json`.

The out-of-corpus set has 12 general-knowledge questions. The loop returned "not enough evidence" for all 12, at a mean of 1.1 s.

Calibration: the first sufficiency probability has a Brier score of 0.055 over the 50 questions, with 4 decisions delegated to LFM. The reliability curve is `docs/calibration.html`.

Reproduce it with:

```bash
pixi run eval-modes
pixi run eval-unknown
pixi run eval-script
pixi run calibrate
```

The eval reports are committed under `lab/demos/raptor-reserve/evals/`, with every per-question row.

## Traces

Every run exports OpenTelemetry spans when a collector is configured:

```bash
pixi run phoenix-up
RPTR_OTLP_ENDPOINT=http://127.0.0.1:6006/v1/traces pixi run serve
```

The parent span is the run, the child spans are the steps of the decision trace, and the API result carries the trace id. See `mds/opentelemetry.md`.

## Recordings

The model-backed script turns are committed in `lab/demos/raptor-reserve/runs/`. Regenerate them when the corpus or a prompt changes:

```bash
pixi run record
```

Each recording keeps the answer, citations, retrieval results, and the full decision trace. Recorded replay is the mode for the demo video and for readers who only want to click through the pipeline.

## Deep dives

One file per technology, in `mds/`:

| File | Topic |
| --- | --- |
| `mds/metrics.md` | Retrieval, answer, calibration, and cost metrics |
| `mds/systemone.md` | The decision model, the confidence band, and the delegation |
| `mds/refeed.md` | The loop: retrieve, judge, rewrite, retry, cite, check |
| `mds/raptor.md` | The RAPTOR summary tree |
| `mds/umap-gmm.md` | UMAP and GMM for the clusters |
| `mds/llamacpp.md` | The local llama.cpp router |
| `mds/models.md` | EmbeddingGemma 2, LFM2.5, d1-3B |
| `mds/sqlite-numpy.md` | SQLite, numpy, and the corpus fingerprint |
| `mds/fastapi-app.md` | The app, the tabs, the recorded replay |
| `mds/place-contract.md` | The demo place format for coding agents |

## Development

```bash
pixi run test
pixi run ruff check src tests
```

The corpus generator is the source of truth. The Markdown in `corpus/` is the build output.

## License

The code is MIT (`LICENSE`). The corpus is CC BY 4.0. The models keep their own licenses. See `NOTICE.md` for the full list.
