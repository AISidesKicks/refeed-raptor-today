# File Naming and Manifest

Category: Data and methods
Date: 2026-06-01
Author: Samir Haddad
Source: Raptor Reserve internal record

The corpus uses a simple naming scheme: `rr-###-slug.md`. The number is the document id. The slug is a lowercase, hyphenated version of the title. There are no spaces, no uppercase letters, and no special characters.

Each file starts with a level-one heading, then four metadata lines: Category, Date, Author, and Source. The body follows. The metadata is repeated in `manifest.json` so the loader does not have to parse Markdown.

The manifest lists every document with id, title, category, date, author, path, license, and word count. It also records the place id, the corpus version, and the generator. The manifest is generated; do not edit it by hand.

The place folder has `demo.toml`, `corpus/`, `script.jsonl`, and `eval.jsonl`. The script is the autoplay. The eval is the question set. The corpus is the documents and the manifest.

The validator checks the file name, the heading, the metadata, the manifest entry, the word count, and the gold document ids. A file that is not in the manifest is an error. A manifest entry with no file is an error.

The generator is `tools/build_corpus.py`. Run it from the place folder. The output is deterministic. Commit the generated files with the generator.

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
