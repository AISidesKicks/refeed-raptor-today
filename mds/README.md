# Deep dives

Short notes on one technology each. The tone is informal, the numbers come from the lab itself, and every file points at the code that does the work.

| File | Topic |
| --- | --- |
| [metrics.md](metrics.md) | Retrieval, answer, calibration, and cost metrics, and how to read them |
| [systemone.md](systemone.md) | The decision model: typed questions, probabilities, the confidence band, and two background videos |
| [refeed.md](refeed.md) | The loop: retrieve, judge, rewrite, retry, cite, check |
| [raptor.md](raptor.md) | The summary tree: build, summaries, collapsed retrieval, what it buys |
| [umap-gmm.md](umap-gmm.md) | UMAP and the Gaussian mixture that make the clusters |
| [llamacpp.md](llamacpp.md) | One local router, three presets, and the pinned build |
| [models.md](models.md) | EmbeddingGemma 2, LFM2.5, and d1-3B, and why each one has a job |
| [sqlite-numpy.md](sqlite-numpy.md) | The database, the vectors, and the fingerprint |
| [fastapi-app.md](fastapi-app.md) | The app, the four tabs, the recorded replay, and the tests |
| [place-contract.md](place-contract.md) | The demo place format and how an agent adds a new place |

The order that makes sense for a reader: the metrics first (so the numbers mean something), then the loop, then the tree, then the stack that runs it.

Every number in these files was measured on the first corpus with the model stack in `docker/presets.ini`. When the stack or the corpus changes, the numbers have to be re-measured and the files updated. A deep dive with stale numbers is worse than no deep dive.
