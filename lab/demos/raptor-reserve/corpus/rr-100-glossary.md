# Glossary

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

RAG: Retrieval-Augmented Generation. Retrieve passages, put them in the prompt, generate an answer.

One-shot RAG: one retrieval, one answer, no critic and no retry.

Refeed loop: retrieve, judge, rewrite if needed, retrieve again, answer. The small loop in this project.

RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval. Chunk, embed, cluster, summarize, recurse, and retrieve from the tree.

Summary tree: the RAPTOR output. Leaves are chunks; higher levels are summaries.

Collapsed tree: search every level at once instead of walking down from the root.

Chunk: a fixed-size slice of a document, with a small overlap.

Embedding: a vector that represents the meaning of a text or an image.

Cosine similarity: the cosine of the angle between two vectors. Higher means more similar.

System 1: fast, cheap, automatic judgment. In this project, d1-3B.

System 2: slow, expensive reasoning and writing. In this project, LFM2.5-8B-A1B.

Decision model: a model trained to answer typed questions with probabilities, not to generate prose.

`noul`: a yes or no question. The answer is the probability of yes.

`choice`: a question with named options. The answer is the chosen option plus the distribution.

`score`: a rating on an ordered rubric. The answer is the expected level plus the distribution.

Calibration: whether confidence matches accuracy. ECE is the expected calibration error. Brier is the mean squared error of the forecasts.

Recall@k, Precision@k, MRR, nDCG@k: retrieval metrics.

Faithfulness, groundedness, answer relevance, correctness, completeness: answer metrics.

Span: one timed operation in a trace. Retrieval, decision, rewrite, and answer are spans.

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
