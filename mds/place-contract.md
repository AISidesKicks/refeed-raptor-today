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

1. Copy `lab/demos/raptor-reserve/` to `lab/demos/<place>/`.
2. Replace the corpus, the manifest, the questions, the script, and `demo.toml`.
3. Regenerate the corpus with the generator.
4. Run `pixi run test` and fix the loader errors.
5. Run `pixi run index`, `pixi run embed`, and `pixi run build-tree`.
6. Run `pixi run eval` and compare with the reference place.
7. Run `pixi run record --place <place>` and commit the `runs/` folder.

Steps 5 to 7 need the router, because they embed, summarise, and answer. Steps 1 to 4 do not.

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
{"id": "q29", "question": "...", "gold": ["rr-042"], "expect": "..."}
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
