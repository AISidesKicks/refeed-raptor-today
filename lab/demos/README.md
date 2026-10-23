# Demo places

A demo place is a self-contained corpus and script that the Refeed Raptor app can load. The app does not know about the Raptor Reserve. It reads a place folder and runs the same pipeline for any corpus that follows this contract.

The first place is `raptor-reserve/`. It is the reference implementation.

## Folder layout

```text
lab/demos/<place>/
  demo.toml
  corpus/
    <id>-<slug>.md
    manifest.json
  script.jsonl
  eval.jsonl
  unknown.jsonl     # optional, out-of-corpus questions
  evals/            # optional, committed eval reports
    modes.json
    unknown.json
    script.json
  runs/             # optional, committed recordings for replay
    index.json
    turn-01.json
  NOTICE.md
  README.md
  tools/            # optional, for generated corpora
```

## `demo.toml`

The place metadata. The loader reads this file first.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Lowercase, hyphenated place id. Must match the folder name. |
| `title` | string | Human-readable place name. |
| `blurb` | string | One sentence for the place picker. |
| `corpus` | string | Relative path to the corpus folder, usually `corpus`. |
| `script` | string | Relative path to the autoplay script. |
| `eval` | string | Relative path to the eval questions. |
| `unknown` | string | Optional. Relative path to the out-of-corpus questions. |
| `license` | string | SPDX id for the corpus, for example `CC-BY-4.0`. |
| `version` | integer | Contract version. Start at `1`. |
| `starter_questions` | array | Three to six questions for the UI. |
| `[models]` | table | `embedding`, `writer`, and `judge` model ids. |

The model table is descriptive. The runner uses the router presets from the app config, not the place file, so a place cannot silently switch to a different model.

## `corpus/`

Each document is a UTF-8 Markdown file.

```markdown
# Document title

Category: Field operations
Date: 2026-05-01
Author: Elin Ward
Source: Raptor Reserve internal record

The body starts here.
```

Rules:

- The first line is a level-one heading.
- The next lines are `Category:`, `Date:`, `Author:`, and `Source:`.
- Dates are ISO 8601.
- The body is prose, with section headings when it helps.
- The file name is `<id>-<slug>.md`. Use lowercase and hyphens.
- The id is stable. Do not renumber a document after publishing it.

`manifest.json` is the machine-readable list. It has `place`, `title`, `version`, `license`, `generated_by`, and a `documents` array. Each document entry has `id`, `title`, `category`, `date`, `author`, `path`, `license`, `words`, and `chunks_estimate`.

The manifest is generated. Do not edit it by hand. The generator is the source of truth.

### Length

The reference target is 500 to 800 words per document, with section headings. At 512-token chunks with 64 overlap, that is two to four chunks per document. A 100-document place then has about 200 to 300 chunks, enough for a three-level RAPTOR tree.

A short note is allowed only when it is linked from a longer document. A corpus of 150-word notes is one chunk per document and does not show the hierarchy.

## `script.jsonl`

One JSON object per line. The autoplay player reads the `visitor` field and shows the rest as notes.

```json
{"turn":1,"visitor":"How many osprey chicks fledged in 2025?","note":"A direct lookup.","expect":"21 chicks from 14 pairs."}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `turn` | integer | Order in the recording. |
| `visitor` | string | The question shown to the viewer. |
| `note` | string | Why this turn matters. Optional. |
| `expect` | string | Short expected answer for the recording. Optional. |

Use three to six turns. The script is a demo, not the eval. It should show one easy question, one multi-hop question, and one question where the refeed loop changes the outcome.

## `eval.jsonl`

One JSON object per line.

```json
{"id":"q01","question":"How many osprey chicks fledged in 2025?","type":"single","gold":["rr-012"],"expected":"21 chicks","notes":""}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Unique question id. |
| `question` | string | The question. |
| `type` | `single` or `multi` | One-hop or multi-hop. |
| `gold` | array | The minimum set of document ids a perfect retriever should find. |
| `expected` | string | Short reference answer. |
| `notes` | string | Why the question is hard. Optional. |

The reference set has 50 questions: 30 place-specific, 10 methods, and 10 multi-hop. A smaller place can use fewer, but the runner reports the count and the mix so the comparison is honest.

Every `gold` id must exist in the manifest. Every question must have a non-empty `expected` answer. The loader validates both on startup.

## `unknown.jsonl`

The negative controls. These are questions the corpus cannot answer, and the expected outcome is a refusal.

```json
{"id":"u01","question":"What is the capital of France?","type":"unknown","expected":"refusal"}
```

Rules:

- No `gold` field, or an empty one. The loader rejects a gold id here on purpose: a question with a gold document is answerable, so it does not test refusal.
- 8 to 15 questions is enough. More does not make the score more precise, it just makes the run slower.
- Pick facts the model probably knows from pretraining. If the question is nonsense, a keyword retriever rejects it for the wrong reason. If it is about the place's domain but absent from the corpus, that is also a fair test, and usually the harder one.
- Do not reuse an eval question with the gold removed. The wording leaks the answer shape.

`pixi run eval-unknown` runs the set through the loop and reports the refusal rate. The reference place refuses 12 of 12.

## `evals/`

The committed reports. They are generated, never edited by hand:

- `modes.json`: keyword, one-shot, and loop results on the eval set, plus calibration data and the per-question comparison.
- `unknown.json`: the refusal run.
- `script.json`: one-shot versus loop on every script turn.

Commit them so a reader can check a number without a GPU. Regenerate them when the corpus, a prompt, or a model changes, and commit the new files in the same commit as the change. A stale report is worse than no report.

## `runs/`

The recorded replay. Run `pixi run record` with the router up, then commit the
JSON files. One file per script turn:

```text
runs/turn-01.json
```

Each file keeps the visitor question, the note, the expected answer, the model
ids, and the full result with the decision trace. `runs/index.json` lists the
turns, the timestamp, the chunk count, and the tree size.

Recorded mode needs no model, no embeddings, and no GPU. It is the mode for the
video and for a reader who only wants to click through the demo. Live mode runs
the same turn through the pipeline again. The keyword mode stays as the
model-free retrieval floor, not as a scripted answer.

If the corpus or a prompt changes, run `pixi run record` again and commit the new
files. Do not hand-edit a recording.

## `NOTICE.md`

State the license, the provenance, and what is fictional. If the corpus summarizes public research, list the sources and confirm that no third-party text is copied.

## `README.md`

Explain what the place is, how to build it, what is fictional, and which question is the best demo. Keep it short.

## How the runner loads a place

1. Read `demo.toml`.
2. Load `corpus/manifest.json`.
3. Read each document and split it into 512-token chunks with 64 overlap.
4. Embed the chunks with EmbeddingGemma 2.
5. Build or load the RAPTOR tree.
6. Serve the starter questions and the script.
7. Replay `runs/` when it exists, or run the turn live.
8. Run `eval.jsonl` through the same retriever and loop.

The place is data. The app is the reader. Do not add a branch in `src/` for a specific place.

## How an AI agent adds a place

An agent can do this without reading the rest of the repository. Work in this order, and stop at the loader validation before spending any GPU time.

### 1. Pick a place and a question it can answer

The place needs one property: facts that are not in the model's pretraining. A fictional institution, a made-up island, a future date, an invented product line. Real public facts from Wikipedia are the wrong choice because the writer can answer without the corpus.

Write the one-sentence pitch first. If the pitch is "a museum", the corpus will be a pile of brochures. If it is "a museum deciding which 12 of 4,000 letters to display for its centenary, with loan rules that conflict with conservation rules", the corpus has decisions in it and the questions write themselves.

### 2. Copy the shape, not the content

```bash
mkdir -p lab/demos/<place>/{corpus,tools}
cp lab/demos/raptor-reserve/demo.toml lab/demos/<place>/demo.toml
```

Do not copy the Raptor corpus, the runs, the evals, or the NOTICE. Copying the contract files is fine. A place that keeps another place's facts will fail the "answer must come from this corpus" check.

### 3. Plan the corpus on one table

A 100-document corpus is easier to write when the shape fits on one screen. A worked plan for a second place, a fictional coastal observatory:

| Bucket | Docs | What is in it |
| --- | --- | --- |
| Governance | 8 | Charter, board minutes, budget, partnerships |
| Site and instruments | 18 | Tide gauges, radar, buoys, calibration logs, failures |
| Monitoring programmes | 20 | Shorebirds, seagrass, water quality, fish surveys |
| Weather and storms | 15 | Storm reports, closures, damage, repairs |
| Visitors and access | 10 | Hours, permits, ferry, safety rules |
| Staff and training | 8 | Roles, certifications, on-call rota |
| Data and methods | 16 | RAPTOR, embeddings, the writer, d1, metrics, eval design |
| History | 5 | Founding, land transfer, past closures |

That is 100. Each row gives the generator a fixed number of documents, and the numbers add up, which keeps the build deterministic.

The methods bucket is not decoration. It gives the eval a second question family ("what does the summary tree add?", "when does the judge delegate?") and it gives the reader a reason to trust the pipeline descriptions.

### 4. Write the generator, not the documents

`tools/build_corpus.py` should be deterministic: same input, same 100 files, same manifest. A template per bucket plus a data table per bucket is enough.

- Write the Markdown with the required header.
- Compute the word count.
- Estimate chunks.
- Write `manifest.json` last, from the files that were written.

Commit the generator and the generated Markdown. A reviewer can read the output; the next agent can change the input.

### 5. Design the eval before the answers

The 50-question reference set has a mix worth copying:

| Type | Count | What it tests | Example |
| --- | --- | --- | --- |
| Direct fact | 20 | one document, one fact | "How many hectares does the reserve cover?" |
| Rule or threshold | 8 | a number plus a condition | "A drone flight is planned with a 35 km/h wind. May it proceed?" |
| Date-bounded | 7 | the right period, not the latest | "What was the 2024 operating deficit?" |
| Multi-hop | 10 | two documents, both required | "Which storm damaged the boardwalk, and what did the repair cost?" |
| Methods | 5 | the pipeline's own vocabulary | "What does the sufficiency check decide?" |

Good questions share three traits: the answer is one or two sentences, the gold document is obvious to a careful reader, and the wording does not appear verbatim in the document title.

Bad questions are worth naming too:

- "Tell me about the reserve." No gold document, no score.
- "What is the reserve's name?" The title answers it, so retrieval is not tested.
- "List every bird." Too broad for a 400-character citation and for an 80-word answer.
- "Is the reserve good?" An opinion. The writer will invent one.
- A question whose fact appears in six documents. The gold list names one, so the other five count as citation misses even when the answer is right.

A useful check: hide the corpus and ask whether the question is answerable from general knowledge. If yes, it belongs in `unknown.jsonl`, not `eval.jsonl`.

### 6. Write the script as a story, not a sample

Three to six turns is the contract. The reference script uses seven, which is the maximum that still fits a short video:

1. A direct lookup that proves the corpus is live.
2. A rule question with a number and a condition.
3. A multi-hop question where the first retrieval misses one document.
4. A question the summary tree answers better than the keyword floor.
5. A question with a clean refusal, or a near-miss that shows the warning.
6. A question where the loop changes the answer, with the refeed visible.

Turn 6 is the one to record twice: once with `answer_oneshot` and once with the loop. If the two answers are identical, the script does not have a refeed demo yet.

### 7. Validate before spending GPU time

```bash
pixi run python - <<'PY'
from rptr.place import load_place
place = load_place("lab/demos/<place>")
print(place.summary())
PY
pixi run test
```

The loader catches the cheap failures: a missing header, a gold id that is not in the manifest, a duplicate question id, a script turn with no visitor text. Fix all of them before indexing.

Then:

```bash
pixi run index
pixi run embed
pixi run build-tree
pixi run eval -- --place <place> --output scratch/<place>-retrieval.json
pixi run eval -- --place <place> --modes --unknown --output lab/demos/<place>/evals/modes.json
pixi run eval -- --place <place> --script --output lab/demos/<place>/evals/script.json
pixi run record --place <place>
```

Check three things by hand before committing the recordings:

- Every citation points at a document that visibly supports the sentence.
- The refusal set actually refuses. If it answers, the corpus is too close to the question or the threshold is too loose.
- The refeed turn has a before and after. The `script.json` report shows both.

### 8. Commit in the order a reviewer reads

1. `feat(place): add <place> corpus and generator`
2. `feat(place): add <place> eval and refusal set`
3. `feat(place): add <place> script`
4. `chore(place): record <place> turns`
5. `docs(place): add the <place> build notes`

The loader, the generator, and the manifest go together. The runs and the eval reports go after the content is stable.

If the contract is missing a field, change the contract, the loader, and the reference place together. Do not hide a special case in the app.

## Corpus recipes

Six shapes that produce different questions. Pick one, then change the names:

| Place | Corpus shape | The question it makes possible |
| --- | --- | --- |
| Coastal observatory | Instrument logs, storm reports, monitoring programmes | "The 2025 storm closed the west buoy for 11 days. Which sensor failed first?" |
| Harbour museum | Collection records, loan agreements, conservation reports | "May the 1841 chart travel to the winter exhibition?" |
| Alpine hut network | Weather, bookings, hut maintenance, rescue logs | "Is the north hut open on 12 January, and who is on call?" |
| City archive | Permits, council minutes, inspection reports | "Which permit allowed the pier repair, and when did it expire?" |
| Seed bank | Accessions, germination trials, cold-room logs | "Which accession has the lowest germination rate, and when was it last tested?" |
| Space weather station | Instrument status, alert thresholds, outage reports | "The solar wind is 720 km/s. Which alert level applies?" |

Each one has the same structure: a rule, a record, and a date. The facts are invented, so the model cannot answer from memory.

## Common pitfalls

- **Facts from pretraining.** If a real encyclopedia knows it, the writer can answer without retrieval, and the eval measures the model instead of the corpus. Invent the institution and the numbers.
- **One fact per document.** A corpus where every question is a direct lookup cannot show a refeed loop. Put one fact in a log and the rule that interprets it in a policy note.
- **The title gives the answer away.** "Annual Osprey Fledging Report 2025" is a fine document, but a question that repeats the title can be answered from the title alone. Ask about the number, not the report.
- **The same fact in six documents.** The citation hit counts gold documents. If the fact is duplicated, a correct answer can cite a non-gold copy and score as a miss. Either keep one canonical document or list every duplicate in `gold`.
- **A gold id that is too broad.** A 40-page annual report as the gold document makes the score generous and the trace hard to read. Prefer the specific record.
- **Stale dates.** A generator with a hard-coded year will drift. Write the year once, at the top of the generator.
- **A refusal set of nonsense.** "What is the capital of the moon?" is rejected by any retriever. Use a plain question the model knows, so a refusal means the pipeline chose not to answer.
- **A script with no failure.** If every turn succeeds on the first pass, the video has nothing to show. Keep one turn that needs a refeed, and one that refuses.
- **Em dashes and en dashes.** Use plain hyphens.
- **Private data.** No visitor names, contact details, exact nest coordinates, or real personnel records.

## Validation checklist

| Check | Command | Done when |
| --- | --- | --- |
| Loader accepts the place | `pixi run test` | the new place loads with no error |
| Corpus is complete | `pixi run python -c "..."` | 100 documents, 500 to 800 words each |
| Eval is complete | same script | 30 to 50 questions, every gold id exists |
| Refusal set is clean | same script | 8 to 15 questions, no gold ids |
| Retrieval runs | `pixi run index && pixi run embed && pixi run build-tree` | chunk count and tree size match the manifest estimate |
| Eval runs | `pixi run eval -- --place <place>` | Recall@20 is high enough to measure the writer, not the retriever |
| Loop comparison runs | `pixi run eval -- --place <place> --modes` | the report has a fixed and a broke list, or both are empty and the set is too easy |
| Refusal runs | `pixi run eval -- --place <place> --unknown` | refusal rate is reported, even if it is not 1.0 |
| Recordings exist | `pixi run record --place <place>` | one JSON per turn plus `index.json` |
| Replay works offline | open the app with the router stopped | every recorded turn plays |

## Rules

- No cloud model and no API key.
- No third-party text without a license. Summarize and link instead.
- No em dashes or en dashes. Use plain hyphens.
- English only for v1.
- The corpus is public; do not put visitor names, contact details, or exact nest coordinates in it.
- The eval is a lab instrument, not a benchmark. Report the sample size with every score.
