# Notices and licenses

Refeed Raptor is an educational lab. The repository mixes original text, generated text, model weights, and software with different licenses. This file separates them.

## Corpus

The Raptor Reserve corpus in `lab/demos/raptor-reserve/corpus/` is original synthetic text. It is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

Attribution: AISidesKicks, Refeed Raptor, 2026.

The Markdown files are build output. The generator in `lab/demos/raptor-reserve/tools/` is the source of truth. If you reuse the corpus, keep the attribution and note any changes.

## Code

The Python, HTML, CSS, and shell code in this repository is under the MIT License. See `LICENSE`.

The corpus keeps its own license. The code and the corpus are separate, so a reader can reuse the lab without reusing the text, and the other way around.

## Models and runtime

The repository does not redistribute model weights. `docker/download-models.sh` downloads them from their publishers.

| Component | License | Notes |
| --- | --- | --- |
| EmbeddingGemma 2 | Apache 2.0 | Text embeddings, 768 dimensions |
| LFM2.5-8B-A1B | LFM Open License 1.0 | Writer and summarizer |
| d1-3B | LFM Open License 1.0 | System-1 decision model |
| llama.cpp | MIT | Local router and inference server |
| FastAPI | MIT | Web app framework |
| numpy | BSD-3-Clause | Cosine search |
| scikit-learn | BSD-3-Clause | Clustering |
| umap-learn | BSD-3-Clause | Dimensionality reduction |
| Arize Phoenix | Elastic License 2.0 | Optional local tracing |

The model licenses are controlled by their publishers. Check the model cards before redistribution or commercial use.

## Fictional content

Raptor Reserve is a fictional place. The bird species are real. Events, people, budgets, and records in the corpus are invented for the lab. Do not use the corpus as a source of real conservation or safety advice.

## Image

The hero image `docs/refeed-raptor.png` and the favicon icons in `docs/favicon.png` and `docs/assets/images/` are project assets generated for this lab.

The demo video `docs/assets/videos/refeed-loop.mp4` is a screen recording of this app. It contains no third-party footage.
