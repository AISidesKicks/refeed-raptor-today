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
7. Run `eval.jsonl` through the same retriever and loop.

The place is data. The app is the reader. Do not add a branch in `src/` for a specific place.

## How an AI agent adds a place

1. Copy `raptor-reserve/` to `lab/demos/<new-place>/`.
2. Replace `corpus/`, `eval.jsonl`, `script.jsonl`, `NOTICE.md`, `README.md`, and `demo.toml`.
3. Keep the field names and the manifest shape.
4. Build the corpus with the place's own generator, or write the Markdown by hand.
5. Run the loader validation. Fix every missing file, missing gold id, and empty answer.
6. Ask the three demo questions from `demo.toml` and check the citations by hand.

If the contract is missing a field, change the contract, the loader, and the reference place together. Do not hide a special case in the app.

## Rules

- No cloud model and no API key.
- No third-party text without a license. Summarize and link instead.
- No em dashes or en dashes. Use plain hyphens.
- English only for v1.
- The corpus is public; do not put visitor names, contact details, or exact nest coordinates in it.
- The eval is a lab instrument, not a benchmark. Report the sample size with every score.
