# Evaluation Question Bank

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

The eval set has 50 questions. Thirty are reserve-specific: the answer exists only in the fictional records. Ten are about the methods wing: RAPTOR, SearchJev, EmbeddingGemma 2, LFM2.5, d1-3B, and the metrics. Ten are multi-hop: they need two documents, such as a wind limit plus a flight plan.

Each question has an id, a question, a type, a list of gold documents, and a short expected answer. The type is `single` or `multi`. The gold documents are the minimum set a perfect retriever should find. The expected answer is a string, not a paragraph.

The validate command checks three things: every gold document exists, every question has a non-empty expected answer, and the question ids are unique. The eval runner reports Recall@k, MRR, nDCG, answer correctness, and the refeed count.

The bank is small enough to run on a laptop and large enough to catch a broken retriever. It is not a benchmark. A score on this set is a lab result, not a claim about the world.

The lab runs the same 50 questions through one-shot RAG, RAPTOR retrieval, and RAPTOR plus the refeed loop. The comparison is the point.

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

## Record note

This record is maintained by Samir Haddad. The current version is the one listed in the corpus manifest. Questions about the record go to the data manager (rr-096).
