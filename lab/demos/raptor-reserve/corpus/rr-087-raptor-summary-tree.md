# RAPTOR Summary Tree

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

RAPTOR stands for Recursive Abstractive Processing for Tree-Organized Retrieval. The paper is arXiv 2401.18059 by Sarthi and colleagues, published at ICLR 2024.

The method is simple. Split the corpus into chunks. Embed the chunks. Cluster the embeddings. Summarize each cluster. Embed the summaries. Cluster again. Repeat until the tree has a root. Retrieval can search the leaves, the summaries, or every level at once.

The reserve's tree has three levels. Level 0 is the chunks, about 512 tokens each with a 64-token overlap. Level 1 is about 20 cluster summaries. Level 2 is about 5 higher summaries. The root is one page. The tree is stored in SQLite, not in a vector database.

The default retrieval mode is the collapsed tree: search every level at once and let the scores decide. The paper reports that this works better than walking down from the root. It is also easier to debug.

The paper reports a 20 percentage point absolute gain on the QuALITY benchmark when RAPTOR is paired with GPT-4. The reserve does not assume that number transfers. The lab measures its own recall, answer quality, and cost on the 50-question eval set.

The tree is rebuilt when the corpus changes. The build is deterministic: same documents, same seed, same tree.

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
