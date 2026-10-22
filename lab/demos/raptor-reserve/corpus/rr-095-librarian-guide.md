# Librarian Guide

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

The reserve librarian answers questions about the corpus. It is not a general chatbot. It works best when the question names a document, a date, a place, a person, or a number.

Good questions are specific. "How many osprey chicks fledged in 2025?" is better than "Tell me about ospreys." "Which ranger approved the drone flight on 12 September 2026?" is better than "Who runs the drones?" "A drone flight is planned with a 35 km/h wind. May it proceed?" is better than "What is the drone policy?"

The librarian retrieves the top passages, judges their relevance, and checks whether the evidence is sufficient. If it is not, it rewrites the question and tries again, at most twice. It answers with citations to the node ids and the source documents.

The librarian will not answer from pretraining. If the corpus is silent, it says so. It will not guess a number, a date, or a name. It will not cite a document it did not read.

The trace shows every step: the retrieved nodes, the decision probabilities, the rewrite, the final answer, and the cost. A reader can open a node and check the claim.

The best way to test the librarian is to ask a question whose answer only exists in the fictional records. If it answers correctly, retrieval worked.

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
