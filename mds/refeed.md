# The refeed loop

One retrieval pass is often not enough. The evidence can be on the second page, in the wrong document, or about the wrong year. The refeed loop is the part of the lab that gets a second look, and it is deliberately small: one decision model, one writer model, at most two retries.

## The loop

```
question
  -> embed the question
  -> retrieve the top 20 chunks and summaries
  -> d1 scores every passage for relevance
  -> keep the top 8
  -> d1 decides whether the evidence is sufficient
       -> yes: write the answer
       -> no: d1 picks an action, LFM2.5 rewrites the query, retrieve again (max 2)
  -> the writer answers with citations
  -> d1 checks that the answer is grounded
  -> one repair pass if needed
```

The numbers live in `PipelineConfig` in `src/rptr/pipeline.py`:

```python
retrieve_limit: int = 20
evidence_limit: int = 8
max_refeeds: int = 2
relevance_floor: float = 0.35
sufficient_threshold: float = 0.50
grounded_threshold: float = 0.50
```

## Why two retries and not five

Every retry is a full relevance pass (5 router calls) plus a sufficiency call plus a rewrite call, and the writer runs at the end. Two retries means the loop can look at three rounds of evidence before it gives up. Five would mean six rounds for a question that was never going to be answered, and the trace would show a lot of expensive noise.

The refusal path is explicit. When the evidence is still thin after the last retry, the answer says so and lists the closest records it found, instead of guessing.

## The four actions

When the evidence is not sufficient, the decision model picks one of four actions:

| Action | Meaning |
| --- | --- |
| `keep` | The query is good, retrieve more passages with the same question |
| `broaden` | The query is too narrow, remove a constraint and search wider |
| `narrow` | The query is too broad, add the entity, place, or year |
| `decompose` | The question has several parts, split it into two searches |

LFM2.5 turns the action into one or two new queries. It never answers the question during the rewrite, and the prompt says so explicitly ("Do not answer the question"). The new queries are embedded and retrieved the same way, and the best passage from every round stays in the pool.

The `decompose` action is the interesting one for multi-hop questions. "Which storm damaged the boardwalk, and what did the repair cost?" needs a storm record and a repair record, and the two halves often live in different documents.

## Relevance is judged per query

A passage is judged against the query that found it, not against the whole question. The relevance call gets a neutral state, and every question carries its own search query:

```python
questions[f"p{index}"] = noul(
    "Is this passage relevant to the search query? ...\n\n"
    f"Search query: {query}\n\nPassage:\n" + hit.text
)
```

This matters after a rewrite. The question "How many osprey chicks fledged in 2025, and which ranger approved the drone flight?" is split into two queries, and the patrol log is relevant to the second one. Judged against the whole question it scored 0.15 and was dropped. Judged against the query that found it, it scores 0.79 and stays.

## Evidence selection

Eight passages survive the relevance step. They are not the top eight overall: the passages are taken in rounds, one per query at a time, so a compound question keeps a slot for every part of it.

The writer sees at most four of them, and the ones whose titles name the topic come first:

```python
def _writer_hits(selected, question, limit):
    terms = _terms(question)
    matched = [hit for hit in selected if terms & _terms(hit.title)]
    rest = [hit for hit in selected if hit not in matched]
    return (matched + rest)[:limit]
```

The title matches come first because they are the passages that talk about the subject of the question. The rest fill the remaining slots, because a passage with an unrelated title can still hold the missing fact.

This one rule removed most of the noise: the model no longer mixes a winter checklist into an answer about a wind limit.

The writer also gets excerpts, not full chunks. `_excerpt` keeps the paragraphs that match the question terms, drops the boilerplate paragraphs, and caps the result at about 150 words per passage. That is what keeps the prompt small enough to stay fast and cheap.

## The sufficiency check

The decision model answers one question: is the evidence enough? When the answer lands in the low confidence band, the writer model is asked to grade the evidence with one word.

The wording of that grade matters more than it looks:

```
Check what the question asks the reader to look up. Reply yes only if the
evidence holds that rule, name, or number. Facts that the question already
states do not have to be in the evidence.
```

The first version said "every fact the question asks for", and the grader refused to answer the wind question, because the 35 km/h wind was in the question and not in the evidence. The second version refuses the compound question, because the patrol log is missing. Both words are load bearing.

## The trace

Every run returns a trace, and the trace is the product:

| Step | What it carries |
| --- | --- |
| `retrieve` | The query, the attempt number, the hit ids |
| `relevance` | The probability, confidence, latency, and tokens for every passage |
| `sufficient` | The probability, the band, and whether it was delegated |
| `action` | The chosen action and the probabilities of all options |
| `rewrite` | The new queries |
| `write` | Characters written, raw characters, latency |
| `cite` | Inline citations or a sources footer |
| `grounded` | The probability, the band, and the repair decision |

Nothing in the loop is hidden. The trace is in the API response, in the UI, and in the committed recordings under `lab/demos/raptor-reserve/runs/`.

## What the loop buys

Measured on the 50 questions of the eval set, with the full loop:

| Measure | One-shot | One-shot plus the loop |
| --- | --- | --- |
| Answered | 50 of 50 | 50 of 50 |
| Citation hit rate | 0.96 | 0.94 |
| Mean refeeds | 0.00 | 0.00 |
| Mean latency | 0.39 s | 1.44 s |

That is the trade, not a victory. On a set of curated questions the first retrieval is usually enough, and the loop spends about a second more per answer. The loop fixes one question (`q05`), where the one-shot writer cites a mortality analysis instead of the season report, and breaks two (`q08`, `q29`), where the answer is supported by the record it cites but that record is not on the gold list. Both breaks are attribution differences, not hallucinations.

No question on the eval set needs a refeed any more. The loop is still there for the questions that do, and the script has one: "How many osprey chicks fledged in 2025, and which ranger approved the drone flight over Heron Marsh?" takes one refeed with a decompose action.

That turn is the demo beat. One-shot answers "67 osprey chicks" and cites two unrelated records. The loop decomposes the question, refetches, and answers 21 chicks with the osprey season report and the drone log, after one refeed. The comparison is committed in `evals/script.json`.

## Cost per question

For a question that is answered on the first pass:

- 1 embedding call
- 5 relevance calls (20 passages, 4 per call)
- 1 sufficiency call
- 1 write call
- 1 grounded call

That is 8 decision calls and one write. A question that needs a refeed adds the action call, the rewrite call, and one more round of retrieval. In the demo the whole loop finishes in about two seconds on the test card.

## The failure we know about

`q29` finds its gold document at rank 6, and `q47` at rank 14. Both are inside Recall@20, so the retrieval numbers look fine, but a writer that only sees the top 3 passages will miss them. That is the case for the refeed loop: the second look is what pulls a rank 6 passage into the evidence set.

The other failure is the writer being too generous. The answer can contain a true sentence and an extra sentence that the evidence does not support. The grounded check catches some of that, and one repair pass fixes some of the rest. The rest is why the reader should look at the trace, not just the answer.

Turn 6 is a known quality gap in the other direction. The question asks what the RAPTOR summary tree adds. The loop cites the metrics paragraph of the methods note and talks about summary nodes beating leaves. One-shot cites the definition paragraph and answers with the level structure. The loop's evidence selection is not always the best paragraph, even when both passages come from the same document.

Read next: [System 1 decisions](systemone.md), [the model stack](models.md), [the metrics](metrics.md).
