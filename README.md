# Refeed Raptor

A local RAG lab: a RAPTOR summary tree, a small refeed loop, and a System-1 decision model. No cloud model, no API key.

- Public overview: `docs/index.html`
- Design intent: `INTENT.md`
- First corpus: `lab/demos/raptor-reserve/`
- Metrics reference: `mds/metrics.md`

## Quick start

The environment is a pixi workspace named `rptr`.

```bash
pixi install
pixi run build-corpus
pixi run serve
```

Open `http://localhost:8000`. If port 8000 is taken, pick another:

```bash
RPTR_PORT=8765 pixi run serve
```

The server indexes the corpus on startup. To build the SQLite index without starting the server:

```bash
pixi run index
```

The reader is model-free. It has four tabs:

- Ask: keyword search over the chunks.
- Replay: step through the six autoplay turns.
- Corpus: read all 100 documents.
- Eval: run the keyword baseline on the 50 questions.

The embedding retriever, the RAPTOR tree, the decision model, and the refeed loop are next. The keyword baseline is the comparison floor. On the current 50 questions it gets Recall@5 0.98 and MRR 0.83, so the models have to beat a strong floor.

## Status

The corpus, the eval set, and the model-free reader are in place. The GPU stack and the recorded replay are next.

## License

The corpus is CC BY 4.0. The code license is separate.
