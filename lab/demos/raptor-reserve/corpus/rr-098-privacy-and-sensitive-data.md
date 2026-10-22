# Privacy and Sensitive Data

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

The public corpus contains no visitor names, phone numbers, email addresses, payment details, or home addresses. Staff names are fictional. The reserve's real visitor logs are not part of the corpus.

Nest locations are stored at reduced precision in public datasets. The internal database keeps the exact coordinates, but the public manifest and the corpus text do not. A map in a public document shows territories at 1 km resolution.

Visitor photos are used only with written permission. Camera trap images of people are deleted unless they are part of a safety incident. The retention period for visitor logs is two years. The retention period for incident reports is ten years.

Sensitive data is stored in a separate schema with access controls. The data manager reviews access every quarter. A researcher who needs exact nest coordinates signs a data-sharing agreement and a confidentiality agreement.

The corpus is public under CC BY 4.0. The archive originals are not part of the corpus. The archive has its own access rules (rr-084).

If you find personal information in the corpus, contact the data manager. The reserve will remove it and rebuild the index.

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

## Record note

This record is maintained by Samir Haddad. The current version is the one listed in the corpus manifest. Questions about the record go to the data manager (rr-096).
