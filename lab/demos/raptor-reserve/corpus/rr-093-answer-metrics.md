# Answer Metrics

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

Answer metrics answer a different question: is the final text correct and supported?

Faithfulness asks whether every claim in the answer is supported by the retrieved context. Groundedness is the same idea with a stricter focus on citations. Answer relevance asks whether the answer actually addresses the question. Correctness asks whether it matches the expected answer. Completeness asks whether it covers the important parts. Hallucination rate counts claims that are not supported by any source. Citation accuracy checks whether the cited node really contains the claim.

The reserve uses a judge model for the first pass and a human spot check for a sample. The judge is not trusted blindly. A model can prefer its own writing, favor the first answer it sees, or reward length. The lab records the judge, the prompt, and the order of the answers.

The answer must cite node ids. A claim without a citation is treated as unsupported. If the loop cannot find enough evidence, the correct answer is "I could not find enough evidence," not a confident guess.

The metrics page reports the answer score next to the token cost and the latency. A small gain that doubles the cost is not automatically a win.

The reserve's librarian uses the same rules. It answers from the retrieved records, names the documents, and says when the records are silent.

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
