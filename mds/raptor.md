# The RAPTOR summary tree

Plain RAG searches chunks. RAPTOR also builds a tree of summaries above the chunks, so a question that wants the shape of the corpus can match a summary and a question that wants one exact number can still match the chunk. The paper is arXiv 2401.18059 (Sarthi and colleagues, ICLR 2024). This file is about how the lab builds it, not about the paper.

## What the tree looks like here

The first corpus is 100 documents and 52,188 words. The chunker turns it into 200 leaves.

| Level | Nodes | What it is |
| --- | --- | --- |
| 0 | 200 | The chunks, about 380 words each with a 48 word overlap |
| 1 | 20 | One summary per cluster of chunks |
| 2 | 2 | Summaries of the summaries |
| 3 | 1 | The root, one page about the whole place |

So the index holds 223 vectors: 200 chunk embeddings and 23 summary embeddings. The whole thing fits in a laptop and rebuilds in minutes.

## The build

`pixi run build-tree` does the following:

1. Load the chunk embeddings that `pixi run embed` already wrote.
2. Reduce the vectors. UMAP when it works, PCA as the fallback.
3. Cluster them with a Gaussian mixture.
4. Ask LFM2.5 for one summary per cluster.
5. Embed the summaries and repeat from step 2.
6. Stop when one root is left, then store the tree.

The recursion is the RAPTOR idea. Each level is a different resolution of the same corpus, and every level lives in the same vector space as the leaves.

Details on the clustering are in [UMAP and GMM](umap-gmm.md).

## The summary prompt

The summary is evidence, so it has to keep the facts and lose the padding:

```
Summarize the records below for {place}.

Rules:
- 120 to 220 words.
- Keep every name, date, number, and decision that could answer a question.
- Merge duplicates, but do not merge two different claims into one.
- If records disagree, keep the disagreement.
- Return only the summary.
```

The system prompt adds two more rules: drop repeated boilerplate, never invent a fact. The model runs at temperature 0.1 with the reasoning block closed, so the same corpus produces the same tree.

The "keep the disagreement" line matters more than it looks. The corpus has records that conflict on purpose, because a summary that smooths them out is a summary that lies.

## Collapsed retrieval

The retriever does not walk the tree. It searches every level at once:

```python
chunk_ids, chunk_vectors = load_embeddings(conn, place_id, "chunk")
summary_ids, summary_vectors = load_embeddings(conn, place_id, "summary")
```

All 223 vectors go into one matrix. The query is embedded with the same model, cosine similarity picks the top nodes, and the score decides which level wins. A question about "what is this place" can land on a level 1 summary. A question about "how many chicks fledged in 2025" lands on the leaf with the number.

Collapsed retrieval is easier to explain than the descent rule from the paper, and for 223 nodes the difference in quality is small. The lab measures the tree against a keyword baseline on the same 50 questions, so the numbers are comparable:

| Mode | Recall@5 | Recall@10 | Recall@20 | MRR |
| --- | --- | --- | --- | --- |
| Keyword | 0.98 | 0.98 | 1.00 | 0.829 |
| RAPTOR | 0.96 | 0.98 | 1.00 | 0.861 |

The tree is better at ranking the right passage (MRR) and it finds every gold document by rank 20. The keyword floor still wins Recall@5 by one question. That is the honest picture of a 100 document corpus: the tree is not magic, it is a different ranking.

## Leaves are evidence, summaries are routes

One rule in the pipeline does most of the work: the writer never reads a summary if a chunk passed the relevance floor.

```python
leaves = [hit for hit in eligible if hit.kind == "chunk"]
summaries = [hit for hit in eligible if hit.kind != "chunk"]
kept = leaves[: config.evidence_limit]
if not kept:
    kept = summaries[: config.evidence_limit]
```

Summaries are good for finding a neighbourhood. They are bad at holding exact numbers, because a summary is a compression. So the summary is used as a route, and the leaf is used as the evidence.

## Rebuilding

The tree is a build output, like the corpus. It is not in git, because it is 223 vectors that a build script can reproduce.

```bash
pixi run index       # chunk the documents
pixi run embed       # embed the chunks
pixi run build-tree  # cluster, summarize, recurse
```

The build is deterministic. Same documents, same seed (42), same tree. If the corpus changes, the fingerprint in the `places` table changes and the index is rebuilt on the next start.

## Costs and limits

- The build calls LFM2.5 once per cluster, so a tree of 23 summaries is 23 write calls. For a corpus with 10,000 documents this is the expensive part.
- A summary can drift from its chunks. The lab keeps the disagreements in the prompt to reduce that, but the drift is real and it is a good reason to keep summaries out of the answer.
- The vector count is small enough that a plain numpy cosine scan is fine. At a million chunks you want an index, not a full scan. See [SQLite and numpy](sqlite-numpy.md).

Read next: [the refeed loop](refeed.md), [UMAP and GMM](umap-gmm.md).
