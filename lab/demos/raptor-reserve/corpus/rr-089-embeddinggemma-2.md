# EmbeddingGemma 2

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

EmbeddingGemma 2 is Google's open multimodal embedding model. The full model has 740M parameters: a 270M text backbone, a 170M vision encoder, and a 300M audio encoder. It maps text, images, video, and audio into one 768-dimensional space.

The text model has an 8K token context, mean pooling, and Matryoshka representation learning. The output can be truncated to 512, 256, or 128 dimensions and re-normalized. The model supports more than 100 languages and code. The license is Apache 2.0.

The reserve uses the text-only GGUF. The Q8_0 file is 310 MB. It needs llama.cpp build b11455 or newer because the architecture is `gemma-embedding2`. The model supports 8K context; the reserve configures 4096 because a chunk is about 512 tokens and the smaller cache is faster.

The settings matter. Pooling must be mean. The context is 4096 in the reserve config. Batch size and micro-batch size are both 4096. If the batch is smaller than the longest chunk, the encoder rejects the input with `input is too large to process`.

Text inputs use prefixes. Queries use `task: search result | query: ...`. Documents use `title: ... | text: ...`. The prefix is not decoration; it moves the query and the document into the same task space.

The reserve uses full 768-dimensional vectors. The corpus is small enough that the storage saving from truncation is not worth the quality risk.

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
