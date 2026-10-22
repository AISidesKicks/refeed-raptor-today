# Calibration Metrics

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

Calibration asks whether a model's confidence matches its accuracy. A model that says 80 percent should be right about 80 percent of the time.

The Brier score is the mean squared error of the probability forecasts. Lower is better. Expected calibration error, or ECE, bins the predictions and averages the gap between confidence and accuracy. A reliability diagram plots the two. The confidence distribution shows whether the model uses the whole range or always says 0.9.

Calibration matters because the loop uses confidence to decide when to delegate. If d1 says "not sufficient" with 0.95 confidence, the loop can rewrite without asking the writer. If it says 0.55, the loop should delegate or ask a human.

The reserve reports decision accuracy, Brier score, ECE, the confidence distribution, the delegation rate, and decision latency. The paper reports 41 to 74 percent lower ECE for decision models than for same-size generative models. The lab measures its own numbers on the 50-question eval set.

A model can be accurate and overconfident. That is the dangerous case, because the loop will trust a wrong judgment. The calibration dashboard is the first place to look when the refeed loop behaves strangely.

The delegation band is a configuration, not a law. The lab shows how the answer changes when the band moves.

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
