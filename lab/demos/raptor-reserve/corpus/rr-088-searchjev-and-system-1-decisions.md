# SearchJev and System 1 Decisions

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

SearchJev is a 2026 research paper from Huawei, arXiv 2610.05107. It studies the small decisions that a search agent makes: is this passage relevant, is the evidence sufficient, what should I do next.

The paper's claim is that a generative model is a poor fit for those decisions. It spends tokens on every judgment, and its confidence is not calibrated. A decision model can answer a typed question in one forward pass, with zero generated output tokens, and return a probability.

Jev is TypeSafe's System-1 model. SearchJev is the research behind the idea. The local stand-in is Liquid's d1-3B, which is 3.1B parameters and runs on the same GPU as the writer.

llama.cpp exposes the capability at `POST /v1/systemone`. There are three question types. `noul` is a yes or no question and returns the probability of yes. `choice` picks one of several named options and returns the full distribution. `score` rates an ordered rubric and returns the expected level.

The paper reports 5.2 to 5.3 times faster decisions than same-size Qwen3.5 models, 41 to 74 percent lower expected calibration error, and a BrowseComp-Plus accuracy gain from 45 percent to up to 54 percent. Those numbers are the paper's, not the reserve's. The lab tests the same split on its own questions.

The reserve uses five decisions: relevant, sufficient, action, grounded, and confidence. The confidence band decides when to delegate to LFM2.5.

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
