# UMAP and GMM for the summary tree

RAPTOR needs clusters of chunks, because one summary is written per cluster. The lab builds them with UMAP and a Gaussian mixture model. The paper uses an algorithm from the summarisation literature; this is a smaller version that is easy to read and easy to reproduce.

## Why reduce the dimensions

The chunk embeddings are 768 numbers each. Clustering in 768 dimensions with 200 points is possible but noisy: distance in a high dimensional space gets less and less meaningful, and the clusters come out fuzzy.

`src/rptr/tree.py` reduces first:

```python
from umap import UMAP

return UMAP(
    n_neighbors=min(15, count - 1),
    n_components=components,
    min_dist=0.0,
    metric="cosine",
    random_state=42,
).fit_transform(vectors)
```

The seed is 42 and it never changes. The same corpus gives the same tree, which is what makes the recorded runs reproducible.

Two guards sit around it. UMAP only runs when there are at least 25 vectors, and the reduced dimension count is `max(2, min(5, dims - 1))`, so a tiny corpus does not get a reduction that is larger than the data.

If UMAP fails for any reason, the builder warns and falls back to PCA:

```python
except Exception as exc:
    warnings.warn(f"UMAP failed ({exc}); falling back to PCA", stacklevel=2)
return PCA(n_components=min(components, count - 1), random_state=42).fit_transform(vectors)
```

A fallback that warns is fine. A fallback that is silent is a lie in the trace.

## Why a Gaussian mixture

A Gaussian mixture model is a soft clustering. Every point gets a probability for every cluster, not just one label. That matters for the tree, because a chunk that sits between two topics can end up in a summary that mixes both, or in the one where it fits better. The lab keeps the hard assignment, but the soft probabilities are what make the clusters local instead of random.

```python
model = GaussianMixture(
    n_components=components,
    covariance_type="diag",
    random_state=42,
    n_init=3,
)
model.fit(reduced)
probabilities = model.predict_proba(reduced)
```

The number of clusters is derived from the target size of a level. The builder wants roughly 10 nodes per level, and it caps the number of clusters at 24, so a small corpus does not end up with one summary per chunk.

The membership test is the soft part. A chunk joins a cluster when its probability for that cluster is at least 0.10, and every cluster is capped at 12 members so the summary prompt stays small:

```python
order = np.argsort(-probabilities[:, component])
members = [int(index) for index in order if probabilities[index, component] >= 0.10]
members = sorted(members[:12])
```

The recursion stops when six nodes or fewer are left, and the last level is written as one root page.

## The tree that comes out

For the first corpus, with 200 chunks:

- 20 clusters at level 1 (200 chunks divided by the target size of 10)
- 2 clusters at level 2 (20 summaries divided by 10)
- 1 root at level 3, written from the two level 2 summaries

The clusters are not random. They group by topic: the raptor records with the raptor records, the drone checklists with the flight logs, the metrics documents with the methods documents. That is the property that makes the summaries worth writing.

## The alternatives and why they were not used

| Option | Why not |
| --- | --- |
| k-means | Hard assignment, spherical clusters, sensitive to the initialisation. The GMM gives a probability, and the seed makes it reproducible. |
| Agglomerative clustering | Works well on small sets, but the number of clusters has to be fixed up front, and the dendrogram is hard to read. |
| Pure UMAP with a density cut | Needs another threshold, and the cut is hard to explain to a reader. |
| Embedding the summaries only | A summary that is not embedded cannot be retrieved. Every summary gets its own vector. |

## The cost

The reduction and the clustering run on the CPU in about a second for 200 vectors. That is the cheap part. The expensive part is the 23 summary writes that follow.

The interesting research question is not whether UMAP is the right tool, but how much the tree depends on it. A good follow-up experiment: build the tree with k-means, build it with the GMM, and compare the retrieval metrics on the same 50 questions. The lab has the numbers to do it in an afternoon.

Read next: [the RAPTOR tree](raptor.md), [SQLite and numpy](sqlite-numpy.md).
