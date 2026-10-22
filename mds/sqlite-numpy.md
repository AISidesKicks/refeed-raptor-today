# SQLite and numpy

The lab stores the corpus, the chunks, the vectors, and the tree in one SQLite file, and it searches the vectors with numpy. No vector database, no service to install, no extra port. The rule from the project brief is simple: no hidden state, and the whole lab should be copyable with one file.

## The schema

Five tables, all in `data/rptr.sqlite3`:

```sql
places      -- one row per demo place, with a corpus fingerprint
documents   -- the parsed documents of a place
chunks      -- the 200 leaves with their text and word counts
embeddings  -- float32 vectors, one row per node
tree_nodes  -- the summary nodes, their level, children, and source docs
```

Two settings are set on every connection:

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")
```

WAL means the reader does not block while the indexer writes. Foreign keys mean a chunk cannot point at a document that does not exist.

The indexes are boring and worth it:

```sql
CREATE INDEX IF NOT EXISTS idx_chunks_place ON chunks(place_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(place_id, doc_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_place ON embeddings(place_id, kind);
CREATE INDEX IF NOT EXISTS idx_tree_place ON tree_nodes(place_id, level);
```

## The vectors

A vector is a float32 blob with the node id, the model name, and the dimension next to it:

```python
save_embeddings(conn, place.id, "chunk", model, ids, matrix)
```

The table holds 223 rows for the first place: 200 chunks and 23 summaries. The `kind` column is what makes the collapsed search possible, because the retriever loads both kinds and puts them in one matrix.

## The search

The search is a matrix multiply:

```python
scores = matrix @ query
```

With a normalised matrix that is the cosine similarity. 223 vectors is about 0.2 milliseconds of work, so there is nothing to optimise and nothing to benchmark yet.

This is the part of the lab that will not survive a bigger corpus. A full scan is O(n). At 200,000 chunks you want an HNSW index or a real vector store. The lab keeps the simple version on purpose, because a reader can see exactly what happens, and because the honest comparison is against a keyword baseline on a corpus small enough to read by hand.

## The fingerprint

The index is keyed by a content fingerprint, not by a timestamp:

```python
place.fingerprint  # sha256 over the sorted corpus files
```

On startup the app compares the fingerprint of the corpus on disk with the one in the database. If they match, the embeddings and the tree stay. If they do not, the index for that place is dropped and rebuilt. That is why restarting the server does not cost you twenty minutes of embedding, and why changing one document rebuilds everything instead of leaving a half old index behind.

## Chunking

`src/rptr/chunking.py` splits on paragraph breaks first and only cuts inside a paragraph when the paragraph is too long. The target is 380 words, roughly 512 tokens, with a 48 word overlap so that a fact near a boundary still appears whole in one chunk.

The word count is an estimate for the token count, and the estimate is good enough for the corpus. A real tokenizer would be better, and the code says so in the module docstring.

## What we keep out of the database

- The model weights. They live in `models/` and are gitignored.
- The corpus text as a separate copy. The documents table is derived from the Markdown in the place, and the Markdown is the source of truth.
- The recordings of the demo turns. Those are committed as JSON, because a recording is an artifact of a run, not a build output.

## Why not a vector database

A vector database would add a container, a port, a schema migration, and a new failure mode, and the lab would still be a demo. SQLite with numpy gives the same answers for this corpus, keeps the lab to one command, and keeps the whole index in a file that fits in a commit or an email.

Read next: [the RAPTOR tree](raptor.md), [the app](fastapi-app.md).
