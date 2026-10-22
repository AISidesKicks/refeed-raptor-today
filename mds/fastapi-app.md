# The app

The reader is a FastAPI app with a static HTML page. No LangChain, no LlamaIndex, no agent framework. The reason is simple: the interesting parts of this lab are the decisions, and a framework hides them.

```bash
pixi run serve
```

That starts `uvicorn rptr.app:app` on port 8000. The server does three things on startup: it loads the places, it makes sure the index matches the corpus, and it opens the database. Everything else happens per request.

## The routes

| Route | What it does |
| --- | --- |
| `GET /` | The reader page |
| `GET /api/places` | Every place with its summary |
| `GET /api/places/{id}` | One place: documents, script, capabilities |
| `GET /api/places/{id}/documents` | The corpus list |
| `GET /api/places/{id}/documents/{doc_id}` | One document with its chunks |
| `GET /api/places/{id}/script` | The scripted turns |
| `GET /api/places/{id}/replay/{turn}` | A recorded turn, or a live run |
| `GET /api/places/{id}/eval/keyword` | The keyword baseline on the eval set |
| `GET /api/places/{id}/eval/raptor` | The tree retrieval on the eval set |
| `POST /api/ask` | One question, one answer, one trace |
| `WS /ws/ask` | The same, with the trace streamed while it runs |

The capabilities endpoint tells the UI what the machine can do right now:

```json
{"keyword": true, "raptor": true, "tree": true, "recorded": true}
```

`tree` is false when the place has no summary nodes yet. `recorded` is false when the place has no committed runs. The UI uses those flags to disable buttons instead of failing later.

## The four tabs

- **Ask.** The live path. Write a question, pick the mode, watch the trace arrive over the WebSocket.
- **Replay.** The six scripted turns. The mode dropdown has three values: `recorded` (the committed JSON, no model needed), `live` (run the turn again through the stack), and `keyword` (the model-free floor).
- **Corpus.** All 100 documents with their chunks. This is where the reader can check whether an answer is right.
- **Eval.** Run the keyword baseline or the tree retrieval over the 50 questions and see the metrics.

## The recorded mode

This is the part that makes the lab portable. The turns are committed as JSON under `lab/demos/raptor-reserve/runs/`:

```
runs/
  index.json
  turn-01.json
  turn-02.json
  ...
  turn-06.json
```

Each file holds the question, the expected answer, the final result, the citations, the retrieved passages, and the full trace. The replay endpoint serves it directly:

```python
replay = recorded_turn(place, turn)
```

So a reader can clone the repo, start the app without a GPU, and click through the whole pipeline. The demo video is a recording of that mode. The live mode is there for anyone who wants to break it.

## The fingerprint on startup

The app never rebuilds the index behind your back. It compares the corpus fingerprint with the one in the database, and it only rebuilds when the corpus actually changed:

```python
if stored_fingerprint != place.fingerprint():
    rebuild_index(...)
```

That keeps the restart cheap and keeps the recorded runs honest. A recorded turn belongs to a specific corpus, and the fingerprint says which one.

## The frontend

One HTML file, one CSS file, one JavaScript file. It is served from `src/rptr/static/`, and the app has its own raptor favicon.

The JavaScript is plain and small: a `fetch` wrapper, a renderer for the trace, a renderer for the citations, and a WebSocket client that appends trace steps as they arrive. There is no build step, so the frontend can be edited and reloaded without a toolchain.

## The tests

```bash
pixi run test
```

35 tests, all fast, none of them need a GPU:

- the place loader and its validation rules
- the index and the fingerprint migration
- the chunker and the search
- the pipeline: refusals, citations, polarity cleanup, the confidence band, the delegation
- the app: the API routes, the replay endpoint, the capabilities

The pipeline tests use a fake router, so the decision logic is tested without a model. That is only possible because the router is a thin client with a small interface.

Read next: [the place contract](place-contract.md), [the refeed loop](refeed.md).
