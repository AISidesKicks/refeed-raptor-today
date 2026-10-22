# Data Dictionary

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

The corpus uses five tables.

`documents` stores id, title, category, date, author, path, license, and word count. The id is the stable key. The path is relative to the place folder.

`chunks` stores id, doc_id, text, start, end, token count, and embedding. A chunk belongs to one document. The start and end are character offsets in the document text.

`nodes` stores id, level, parent_id, text, source_docs, and embedding. A node is a RAPTOR summary. Level 0 is a chunk. Level 1 and above are summaries. `source_docs` is a list of document ids.

`decisions` stores id, run_id, question_id, type, answer, probability, confidence, latency, and model. The type is `noul`, `choice`, or `score`.

`runs` stores id, question, config, iterations, prompt_tokens, completion_tokens, latency, answer, and stop_reason.

The eval file adds `id`, `question`, `type`, `gold_docs`, `expected`, and `notes`. Gold docs must exist in `documents`. The validate command checks this.

All ids are lowercase strings. Timestamps are ISO 8601 in UTC. Embeddings are float32 arrays stored as little-endian bytes. The manifest is the source of truth for the document list.

The dictionary is a contract between the corpus, the index, and the app. If a field changes, the builder, the loader, and the eval runner must change together. A field that is not in the dictionary is not part of the public API. The data manager reviews the dictionary before every corpus release.

## Question

This document answers a practical question for the reserve's library: how does this part of the pipeline work, and when is it worth using? The goal is not to sell a model or a framework. The goal is to explain one piece of the retrieval pipeline so a reader can run it, measure it, and decide whether it is worth the cost.

## Method

The method is a small local stack: EmbeddingGemma 2 for embeddings, a SQLite store, numpy cosine search, and a RAPTOR summary tree. The writer is LFM2.5-8B-A1B. The decision model is d1-3B. The app is FastAPI plus static HTML. No cloud model and no API key.

## What the numbers mean

Retrieval numbers describe whether the right passage was found. Answer numbers describe whether the final text is supported. Calibration numbers describe whether the model knows how sure it is. A good demo reports all three, not just the answer quality.

## Limitations

The corpus is small and synthetic. The results are a lab result, not a benchmark. A judge model can prefer its own output. A reranker can look good because the gold passages are easy. The project reports the cost and the failure cases next to the wins.

## Practical use

Use the method when the corpus is small enough to inspect and the question needs evidence. Do not use it when a keyword search or a single document is enough. The librarian guide (rr-095) shows how to ask a question that the loop can actually answer.

## Further reading

The primary sources are the RAPTOR paper (arXiv 2401.18059), the SearchJev paper (arXiv 2610.05107), the EmbeddingGemma 2 model card, the LFM2.5 model card, and the d1-3B model card. The lab's INTENT.md has the full reference list.
