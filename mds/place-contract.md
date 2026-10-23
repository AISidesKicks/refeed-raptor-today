# The place contract

A "place" is a small corpus with a reader around it. The first one is Raptor Reserve, 100 fictional documents about a bird reserve. The point of the contract is that an AI coding agent can add a new place without reading the whole repository.

The rules live in `lab/demos/README.md`, and the loader in `src/rptr/place.py` enforces them.

## The folder

```
lab/demos/raptor-reserve/
  demo.toml          metadata, starter questions, the model stack
  corpus/            the documents and manifest.json
  script.jsonl       the autoplay turns
  eval.jsonl         the questions with gold document ids
  unknown.jsonl      the out-of-corpus refusal set
  evals/             the committed three-mode and refusal reports
  runs/              the committed recordings
  tools/             the corpus generator
  NOTICE.md          licenses and provenance
  README.md          build notes
```

Two rules that matter most:

- The generator in `tools/` is the source of truth. The Markdown in `corpus/` is the build output. Commit both.
- Never hard-code facts about a place in `src/` or in the app. The app reads places from disk and does not know that a peregrine named Juniper exists.

## The loader

`load_place` reads `demo.toml`, walks the corpus, parses the script and the eval set, and raises `PlaceError` with a readable message when something is wrong:

- a missing required key in `demo.toml`
- an empty corpus
- a document that is not in the manifest
- a question with no gold document
- a script turn with no visitor text

The loader is the validator. `pixi run test` runs it against every place in the repository, so a broken place fails the test suite before anything else runs.

## Adding a place

The short version is in `lab/demos/README.md`. This section is the reasoning behind it, plus a worked second place.

### A second place, end to end

Suppose the second place is a fictional coastal observatory. The pitch is one line: "A 60-year-old station that is deciding which two monitoring programmes to keep when the grant shrinks." That sentence already implies the documents: a charter, instrument logs, storm reports, programme reviews, staff rota, and a budget.

The corpus plan is a table with 8 rows and 100 documents. The generator writes each bucket from a small data table, so the 100 documents are deterministic and a reviewer can change one number and rebuild.

`demo.toml` is the same shape as the reference place:

```toml
id = "tidewater-observatory"
title = "Tidewater Observatory"
blurb = "A fictional coastal station deciding which monitoring programmes to keep."
corpus = "corpus"
script = "script.jsonl"
eval = "eval.jsonl"
unknown = "unknown.jsonl"
license = "CC-BY-4.0"
version = 1

starter_questions = [
  "Which sensor failed first in the 2025 storm?",
  "Is the west buoy open to visitors in January?",
  "A gale warning is issued at 45 km/h. Which programmes pause?",
  "Which two programmes does the 2027 budget keep?",
  "What does the sufficiency check decide?",
]

[models]
embedding = "embeddinggemma-2"
writer = "lfm2-8b"
judge = "d1-3b"
```

The starter questions are not decoration. Each one is a different demo beat: a log lookup, a rule with a date, a threshold, a budget decision with two hops, and a methods question. If a starter question has no clean answer, the corpus is not ready.

The eval set follows the reference mix: 20 direct facts, 8 rules, 7 date-bounded, 10 multi-hop, 5 methods. The multi-hop questions are the ones worth writing first, because they decide the corpus shape. "Which storm damaged the boardwalk, and what did the repair cost?" forces one document to hold the event and another to hold the cost. If no such pair exists, the refeed loop has nothing to do.

The refusal set is the mirror image: 12 questions the corpus cannot answer. Use plain questions the model knows ("What is the currency of Japan?"), not nonsense. A refusal on a plain question is evidence that the pipeline chose not to answer. A refusal on nonsense proves only that the keyword filter works.

The script is six turns: direct lookup, rule, multi-hop, tree question, refusal, and one turn where the loop changes the answer. Turn 6 is the one to record twice, because it is the only turn that proves the loop is worth its latency.

### What makes a corpus good

A corpus is not a pile of documents. It needs four properties:

1. **Facts that are not in pretraining.** Invent the place and the numbers. A real island with real birds can be answered from memory, which makes the retrieval invisible.
2. **A rule and a record.** The rule lives in a policy note, the record lives in a log, and the question needs both. This is what a refeed is for.
3. **One canonical copy of each fact.** Duplicates turn a correct answer into a citation miss, because the metric only rewards the gold document.
4. **A methods shelf.** Ten to sixteen documents about the pipeline itself give the eval a second family of questions and give the reader a reason to trust the trace.

The target length is 500 to 800 words per document. At 512-token chunks with 64 overlap, that is two to four chunks per document and 200 to 300 chunks for the whole place. A 150-word note is one chunk, and a corpus of one-chunk documents cannot show a tree.

### What makes a question good

A good eval question has a short answer, an obvious gold document, and a wording that does not repeat the title. The useful archetypes:

| Archetype | Good example | Why it works |
| --- | --- | --- |
| Direct fact | "How many hectares does the reserve cover?" | one document, one number |
| Rule | "A drone flight is planned with a 35 km/h wind. May it proceed?" | the limit and the flight record are separate |
| Date-bounded | "What was the 2024 operating deficit?" | the latest year is the wrong answer |
| Multi-hop | "Which storm damaged the boardwalk, and what did the repair cost?" | two documents, both required |
| Methods | "What does the sufficiency check decide?" | tests the corpus, not the reserve |
| Near-miss | "Which ranger approved the 2027 drone flight?" | the year does not exist, so a careful system refuses |

The bad ones are just as instructive:

- "Tell me about the reserve." No gold document, so no score.
- "What is the reserve's name?" The title answers it.
- "List every bird." Too broad for a citation and for an 80-word answer.
- "Is the reserve good?" An opinion, which the writer will invent.
- A fact that appears in six documents. The gold list names one, so five correct answers score as misses.

The test is simple: hide the corpus and ask whether the question is answerable from general knowledge. If yes, it is a refusal question, not an eval question.

### The refusal set

Refusal is a feature, not a failure. A RAG system that always answers is not brave, it is unmeasured. The reference set has 12 general-knowledge questions with no gold documents. The loader rejects a gold id in this file on purpose: an answerable question cannot test refusal.

Report the refusal rate with the same care as the citation rate. A rate of 1.0 on 12 questions is a small sample and should be labeled as such. If the system answers one of them, keep the answer in the report. The failure is the interesting part.

### The agent playbook

An AI coding agent can add a place in one pass if it follows this order:

1. Write the pitch and the corpus table. Do not write prose yet.
2. Copy `demo.toml`, rename the files, and remove the Raptor content.
3. Write `tools/build_corpus.py` with one template and one data table per bucket.
4. Build the corpus and run the loader. Fix the cheap errors first.
5. Read three documents at random. If they sound like a brochure, add a decision, a date, and a number.
6. Write the 10 multi-hop questions first, then the direct facts.
7. Write the refusal set from general knowledge, not from the corpus.
8. Write the script, with one turn that needs a refeed.
9. Run `pixi run test`, then index, embed, and build the tree.
10. Run the three-mode eval and the refusal eval. Read the fixed and broke lists.
11. Record the script turns and check three citations by hand.
12. Commit the generator, the corpus, the eval, the refusal set, the script, the runs, and the reports in that order.

The expensive mistakes are all content mistakes, not code mistakes: a fact the model already knows, a question with no gold, a duplicate fact, or a script where every turn succeeds on the first pass.

### Validation checklist

| Check | Done when |
| --- | --- |
| Loader | `load_place` prints the expected document, question, and refusal counts |
| Corpus | 100 documents, 500 to 800 words each, one header per file |
| Manifest | every Markdown file is listed, every gold id exists |
| Questions | 30 to 50, mixed types, each with a non-empty expected answer |
| Refusals | 8 to 15, no gold ids, plain general knowledge |
| Retrieval | Recall@20 shows the gold document is reachable |
| Loop | the report has at least one fixed or broke question, or the set is too easy |
| Recordings | one JSON per turn, replay works with the router stopped |
| Docs | `NOTICE.md` names the license and the fiction, `README.md` names the best demo turn |

If the contract is missing a field, change the contract, the loader, and the reference place in the same commit. Do not hide a special case in the app.


## The model stack in `demo.toml`

The place declares which models it wants:

```toml
[models]
embedding = "embeddinggemma-2"
writer = "lfm2-8b"
judge = "d1-3b"
```

These names are the preset names in `docker/presets.ini`. A place can therefore ask for a different writer without touching the code.

## The eval set

`eval.jsonl` is the measurement contract. Every line has a question, the gold document ids, and the expected answer:

```json
{"id": "q29", "question": "...", "gold": ["rr-042"], "expected": "..."}
```

The gold ids are document ids, not chunk ids. A gold document is a hit when any of its chunks is retrieved, which is the right unit for a corpus of 500 word documents.

The reference set has 50 questions: 30 about the reserve, 10 about the methods, 10 multi-hop. The keyword baseline and the tree retrieval are measured on exactly the same set, which is the only reason the numbers in the README can be compared.

## The script

`script.jsonl` is the autoplay: the questions a visitor sees, in order, with a note about what each turn shows.

```json
{"turn": 3, "visitor": "A drone flight is planned for tomorrow with a 35 km/h wind. May it proceed?", "note": "The wind limit and the flight rules are in different places. This is the refeed candidate.", "expect": "No. Drone flights are cancelled at 28 km/h."}
```

The script is a teaching script. Each turn is chosen to show one behaviour: a direct lookup, a question with two hops, a rule question, a question the tree answers better than the keyword floor.

## The runs

`runs/` holds one JSON file per turn plus an `index.json` manifest. The recording is the artifact that makes the lab work without a GPU, and it is committed on purpose. See [the app](fastapi-app.md) for how it is served.

Read next: [the app](fastapi-app.md), [the metrics](metrics.md).
