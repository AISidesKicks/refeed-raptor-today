# RAG Overview for the Reserve Library

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

The reserve library has 100 documents, about 60,000 words, and more than 200 chunks. A person can read one document in a few minutes, but nobody can hold the whole library in their head. The librarian uses retrieval-augmented generation, or RAG, to find the right passages before it answers.

The pipeline is small. The question is embedded with EmbeddingGemma 2. The retriever scores every chunk with cosine similarity and keeps the top 20. The decision model, d1-3B, scores each chunk for relevance. The loop keeps the top 8. If the evidence is not sufficient, d1 chooses an action and LFM2.5 rewrites the question. The loop retries at most twice. LFM2.5 writes the answer with citations. d1 checks whether the answer is grounded in the retrieved text.

Everything runs on the island's GPU. There is no cloud model and no API key. The documents, the embeddings, the tree, and the traces stay on the reserve server. The only network call is the local llama.cpp router on port 8080.

The librarian is not a chatbot that knows the reserve. It is a reader that can point to the page. If the evidence is missing, it says so. That is the behavior the reserve wants.

The full method is documented in the lab's INTENT.md and in the methods wing of this corpus.

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
