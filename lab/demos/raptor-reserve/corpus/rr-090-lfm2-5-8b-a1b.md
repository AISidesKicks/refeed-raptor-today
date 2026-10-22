# LFM2.5-8B-A1B

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

LFM2.5-8B-A1B is Liquid AI's local reasoning and writing model. It has 8.3B total parameters and 1.5B active parameters. The context window is 128K tokens. The architecture has 24 layers: 18 double-gated convolution layers and 6 grouped-query attention layers.

The reserve uses the Q4_K_M GGUF, which is 5.16 GB. The model fits on a 12 GB card alongside d1-3B and EmbeddingGemma 2. The recommended sampling settings are temperature 0.2, top_k 80, and repeat penalty 1.05.

The model writes the cluster summaries, the query rewrites, and the final answer. For summaries and rewrites, reasoning is disabled. For the final answer, reasoning is optional and is measured, not assumed. A reasoning trace can improve a hard answer, but it also adds tokens and latency.

The model is not a judge. It does not decide whether a passage is relevant or whether the evidence is sufficient. Those decisions go to d1-3B. Keeping the roles separate is the point of the System 1 and System 2 design.

The license is the LFM Open License. Check the model card before commercial use. The reserve uses the model locally and does not send data to Liquid.

The writer is the most expensive part of the loop. The metrics page reports its token cost and latency next to the answer quality.

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
