# Retrieval Metrics

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

Retrieval metrics answer one question: did the system find the passage that contains the answer?

Recall@k is the fraction of gold passages that appear in the top k. Precision@k is the fraction of the top k that are relevant. Hit@k is 1 if at least one gold passage is in the top k, and 0 otherwise. MRR is the mean of 1 divided by the rank of the first relevant result. nDCG@k rewards relevant results near the top and handles graded relevance.

RAG systems also use context precision and context recall. Context precision asks how much of the retrieved context is useful. Context recall asks how much of the needed context was retrieved. Both are usually judged by a model, so they inherit the judge's biases.

The reserve reports Recall@5, Recall@10, and Recall@20, plus MRR and nDCG@10. Recall is the primary metric because a missing passage cannot be fixed by a better prompt. Precision matters because a crowded context distracts the writer and costs tokens.

The RAPTOR report adds a level breakdown: how often a summary node beats a leaf, and whether the winning level matches the question type. A "what is this about" question should prefer a summary. A "what exactly happened" question should prefer a leaf.

The lab compares one-shot RAG, RAPTOR retrieval, and RAPTOR plus the refeed loop on the same 50 questions.

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
