# Refeed Raptor

> A small, local, funny RAG lab. A raptor gets fed documents, chews them into a summary tree, and refeeds when the answer is not good enough.

**Status:** research complete, the first corpus is built. The stack and the loop are locked. The first place is a 100-document synthetic corpus called `raptor-reserve`. The app, the Docker stack, and the replay player are next.

This is an educational project. The goal is not to build the biggest RAG system. The goal is to make the small one legible, then show what the extra machinery buys and what it costs.

---

## 1. Why this exists

Simple RAG is easy to understand: embed the documents, search for the nearest chunks, put them in the prompt, answer.

Then the tutorials add loops, query rewriting, rerankers, graph indexes, and summary trees like RAPTOR. The reader loses the thread. The system looks like a pile of parts, and the parts are hidden behind a framework.

This project is the opposite:

- One small loop.
- One summary tree.
- One local stack.
- Every step visible.
- Every decision measured.

The reader can watch the raptor eat, see why it refeeds, and check whether the second bite was better.

The voice is informal but technical enough to explore. The code is small enough to read in an afternoon. The diagrams are simple. The jokes are mostly about the dinosaur.

---

## 2. What we are building

A local RAG lab with four faces:

1. **A recorded video.** The primary public artifact. A short screencast that shows one question fail one-shot RAG, then succeed through the refeed loop.
2. **An interactive app.** Clone the repo, start the stack, ask your own question, watch the retrieval, the decisions, the rewrite, and the answer.
3. **A replay mode.** The same player reads a recorded event trace. No models, no GPU, no downloads. This is what the static site and the video recording use.
4. **An agent harness.** A folder contract and an `AGENTS.md` playbook so an AI coding agent can add a new place, validate it, record it, and publish it.

The public site is a GitHub Pages site at `refeed.raptor.report`. The lab runs on the visitor's machine. There is no cloud LLM and no API key.

---

## 3. The two loops

### 3.1 The small loop

The small loop happens while the user waits, in milliseconds to seconds. It is run-time loop engineering:

1. Retrieve.
2. Judge the evidence.
3. If the evidence is weak, rewrite the query and retrieve again.
4. Answer only when the evidence is good enough, or when the loop hits its limit.

The small loop is the heart of this project. It is a fixed pipeline, not an open-ended agent. The model does not decide whether to call a tool. Our code decides the steps, and the decision model supplies the cheap judgments.

### 3.2 The big loop

The big loop happens asynchronously over days or weeks:

- Log the failures.
- Collect thumbs-down flags and corrections.
- Rebuild the summary tree when the corpus changes.
- Re-evaluate the retriever, the reranker, and the query rewriter.
- Re-index or retrain the parts that keep failing.

The big loop is a goal, not v1. The project should leave a clean seam for it: every run writes a trace, every trace has a stable schema, and every failure can become an eval case.

### 3.3 One-shot vs refeed

| Feature | One-shot RAG | Refeed loop RAG |
|---|---|---|
| Workflow | Linear: retrieve, answer, generate | Cyclic: retrieve, judge, maybe retrieve again, answer |
| Handling failure | Accepts the first draft even when the evidence is weak | Detects the gap, rewrites, and retries |
| Query flexibility | Uses the user's original wording | Rewrites the query based on the retrieved material |
| Token cost | Low and predictable | Higher, because the loop makes extra model calls |
| Latency | Low and predictable | Higher, but each extra step is a visible trade |
| Debuggability | A single prompt and a single answer | A trace with retrieval, decisions, rewrites, and costs |

The point of the project is to show that the trade is real, and to measure it instead of guessing.

---

## 4. System 1 decides, System 2 writes

This is the central research idea, and the reason the project is not another wrapper around a chat model.

### 4.1 The research

**Jev** is TypeSafe's System-1 decision model. The research behind it is **SearchJev: A Fast and Calibrated System-1 Model for Search Agents** (Huawei, arXiv 2610.05107, submitted 4 October 2026).

The finding:

- Search agents repeatedly make short decisions: is this passage relevant, is the evidence sufficient, what should I do next.
- A generative model handles those decisions badly. It spends tokens on every judgment, and its confidence is poorly calibrated.
- A small decision model can answer typed questions in one forward pass, with zero generated output tokens, and return calibrated probabilities.
- The big model keeps planning, query generation, and answer writing.

The numbers in the paper:

- 5.2 to 5.3 times faster decisions than same-size Qwen3.5 models.
- 41 to 74 percent lower expected calibration error.
- On BrowseComp-Plus, answer accuracy from 45 percent to up to 54 percent, with 3.7 to 4.7 times faster active search.

Whether those numbers transfer to our small corpus is exactly what the lab should measure. The claim is not the point. The measurable split is.

### 4.2 The local API

llama.cpp now has a native `POST /v1/systemone` endpoint. It follows the TypeSafe System One API and supports three question types:

| Type | Question | Answer |
|---|---|---|
| `noul` | Yes or no | Probability of yes, in `[0, 1]` |
| `choice` | Pick one of named options | Chosen option, full probability distribution, confidence |
| `score` | Rate on an ordered rubric | Expected level, full distribution, confidence |

A response carries the answer, the probabilities, and a confidence value. Decision models report `output_modalities: ["decisions"]` in `/v1/models`, so the app can detect them before loading. A language model that classifies with prompts does not get this capability. Only a native decision model does.

There is also `/v1/rerank` for classic cross-encoders such as bge and Qwen3-Reranker. We do not need it. A decision model can score relevance with calibrated confidence, which a cross-encoder cannot. That is the "new reranking" angle for the blog: the reranker becomes a judge, and the judge can say how sure it is.

### 4.3 The two models

| Role | Model | Why |
|---|---|---|
| System 1 | **d1-3B** | Local, 3.1B, 32K context, calibrated, 8 ms per decision on an RTX 4090, multimodal, same Liquid family as LFM |
| System 2 | **LFM2.5-8B-A1B** | Local, 8.3B total and 1.5B active, 128K context, hybrid architecture, good enough writing, fast on a 12 GB card |

d1-3B is not a chat model. It does not write text. It answers the typed questions and returns probabilities. That constraint is a feature: it keeps the loop cheap and the roles honest.

LFM2.5 is a reasoning model. For summaries and query rewrites, disable reasoning. For the final answer, reasoning is optional and should be measured, not assumed.

### 4.4 Where the decisions go

The loop uses five decisions:

| Decision | Type | Question |
|---|---|---|
| `relevant` | `noul` | Is this passage relevant to the question? |
| `sufficient` | `noul` | Is the evidence enough to answer? |
| `action` | `choice` | Should we keep, broaden, narrow, or decompose the query? |
| `grounded` | `noul` | Is the drafted answer supported by the retrieved context? |
| `confidence` | derived | How sure is the decision model, and should we delegate to System 2? |

The "delegate" band is the interesting part. If confidence is high, accept the decision. If confidence is low, ask the big model. That is the dual-system design from the paper, and it is easy to show on screen.

---

## 5. The stack

### 5.1 Locked choices

| Piece | Choice | Notes |
|---|---|---|
| Embeddings | **EmbeddingGemma 2** Q8_0 | 768 dimensions, 8K max context, mean pooling, 310 MB text-only GGUF |
| Writer | **LFM2.5-8B-A1B** Q4_K_M | 8.3B total, 1.5B active, 128K context, 5.16 GB |
| Judge | **d1-3B** Q8_0 | 3.1B, 32K context, 2.87 GB, one forward pass per decision |
| Server | One **llama.cpp router** with three presets | One CUDA context, one port, one set of logs |
| Storage | **SQLite plus numpy cosine** | No vector database, one inspectable file per place |
| App | **FastAPI, static HTML, WebSocket** | Boring on purpose, easy for agents to edit |
| Observability | **Arize Phoenix** | One Docker image, traces plus evals |
| Runtime | **pixi** workspace `rptr` | Python 3.12, project-local environment |
| Containers | Prefix **`rptr-`** | `rptr-llm`, `rptr-app`, `rptr-phoenix`, `rptr-build` |

The current `pixi.toml` is a skeleton with Python 3.12 only. The first build step adds the app and test dependencies.

### 5.2 Why one router

llama.cpp can run in router mode. One process serves several models, and the `"model"` field in the request chooses which preset answers. The presets live in an INI file:

- `embeddinggemma-2`: encoder, mean pooling, 4096 configured context (8K max).
- `lfm2-8b`: chat, summaries, rewrites, answers.
- `d1-3b`: decisions, `/v1/systemone`.

The router keeps one CUDA context and one OpenAI-compatible port. It can load models on demand, keep them warm, or sleep them after idle. For the demo, keep all three warm. For a smaller card, sleep the LFM between turns.

### 5.3 The 12 GB budget

| Model | Quant | Weights |
|---|---|---|
| LFM2.5-8B-A1B | Q4_K_M | 5.16 GB |
| d1-3B | Q8_0 | 2.87 GB |
| EmbeddingGemma 2 | Q8_0 | 0.31 GB |
| **Total** | | **about 8.3 GB** |

LFM2.5 uses 24 layers, but only 6 are full attention. Its 32K KV cache is small. d1 only needs a short context for decisions. On a 12 GB card there is room for the weights, the KV caches, and the CUDA overhead.

If the card is smaller:

- d1-3B Q4_K_M is 1.67 GB.
- LFM2.5 Q4_0 is 4.84 GB.
- Reduce context to 16K before reducing the quant. The judge and the retriever need room more than the writer needs a long leash.

### 5.4 Build requirements

This is the part that breaks first.

- **EmbeddingGemma 2** needs llama.cpp build **b11455 or newer**, because it uses the `gemma-embedding2` architecture.
- **d1-3B** needs a build with `lfm2-d1` decision support.
- The latest release at the time of writing is **b11819** (22 October 2026).
- An older b7xxx build is too old for both. It will fail with `unknown model architecture`, or it will be missing `/v1/systemone`, and the failure looks like a broken model file.

The cuda13 GHCR image publishes a moving `server-cuda13` tag. We did not find per-build cuda13 tags. Pin the image by digest for reproducibility:

```text
ghcr.io/ggml-org/llama.cpp:server-cuda13@sha256:dfe42bda81c6bd53df864dfcf65e2423e9703f9991c238cfa7aaa893063e2977
```

That digest is the one verified for this project on 22 October 2026. The tag moves. The digest does not.

EmbeddingGemma 2 is picky:

- `pooling = mean`, not the default.
- `ctx-size = 4096`. The model supports 8192, but our chunks are about 512 tokens and the smaller context keeps the cache small. Raise it if a chunk grows.
- `batch-size` and `ubatch-size` both 4096. If the batch is smaller than the longest chunk, the encoder rejects it with `input is too large to process`.

### 5.5 What we deliberately do not use

- **No cloud LLM.** The whole point is a local stack.
- **No LangChain or LlamaIndex in the loop.** The loop is 150 lines and should stay readable. Frameworks hide the exact thing the reader came to see.
- **No vector database.** A few hundred chunks do not need Qdrant, Chroma, or LanceDB. SQLite plus a numpy matrix is faster to explain and fast enough to run.
- **No OpenViking or memory server.** Memory is a different project.
- **No tool calling.** The pipeline is fixed. The decision model is not allowed to invent a tool call.
- **No fine-tuning.** v1 uses the models as shipped.

---

## 6. How the raptor eats: RAPTOR

RAPTOR means **Recursive Abstractive Processing for Tree-Organized Retrieval** (Sarthi et al., ICLR 2024). The paper recursively embeds, clusters, and summarizes chunks. The result is a tree with different levels of abstraction, and retrieval can use any level.

### 6.1 The build

1. **Chunk.** Split the place's documents into about 512-token chunks with a small overlap. Keep the source path and the character offsets.
2. **Embed.** Send the chunks to EmbeddingGemma 2 and store the vectors.
3. **Cluster.** Reduce the vectors with UMAP, then fit a Gaussian mixture. Soft clustering is the paper's choice: a chunk can belong to more than one cluster.
4. **Summarize.** For each cluster, ask LFM2.5 for a short summary. The prompt says what the summary is for: preserve names, numbers, and claims, drop the boilerplate.
5. **Recurse.** Embed the summaries, cluster them, summarize again. Stop at the root or at a maximum depth, whichever comes first.
6. **Store.** Every node gets an `id`, `level`, `parent_id`, `text`, `source`, and embedding. The tree is a table, not a directory of files.

```text
documents
  -> chunks          level 0, the leaves
  -> summaries       level 1
  -> summaries       level 2
  -> root summary    level N
```

### 6.2 Retrieval

The default is the **collapsed tree**: search every level at once and let the scores decide. It is simpler than tree traversal, and the RAPTOR paper reports that it works well. Tree traversal is a second mode, not the default, because it is easier to explain the collapsed tree and easier to debug a flat search.

The retriever returns the top 20 nodes with their level, source, and score. The decision model then reranks them. The level is part of the explanation: a summary node answers "what is this document about", a leaf answers "what exactly does it say".

### 6.3 Why we implement it ourselves

The original RAPTOR repository is MIT licensed and already supports pluggable summarization, QA, and embedding models. It is a good reference. But its default path is OpenAI-shaped, and the code is more than this lab needs.

The LlamaIndex RAPTOR pack is convenient, but it hides the clustering and summarization, and it has a known mismatch with the paper's tree traversal. That is the wrong trade for a teaching project.

Our version is small:

- `src/rptr/chunk.py`
- `src/rptr/embed.py`
- `src/rptr/tree.py`
- `src/rptr/store.py`

Each file should be readable on its own. The notebook or the lab page can show the intermediate clusters, the summaries, and the tree.

---

## 7. How the refeed works

The loop is a fixed pipeline. The model supplies judgments, not control flow.

```text
question
  -> embed the question
  -> retrieve top 20 nodes from the collapsed tree
  -> d1: relevant? for each node (noul)
  -> keep the top 8 by P(relevant)
  -> d1: sufficient? (noul)
       yes -> LFM writes the answer with citations
       no  -> d1: action? (choice: keep, broaden, narrow, decompose)
              LFM rewrites the query
              retrieve again
              repeat, at most 2 refeeds
  -> d1: grounded? (noul)
       yes -> return the answer
       no  -> one repair pass, then return the answer with a warning
```

### 7.1 The rules

- **Maximum two refeeds.** More than two is usually a corpus problem, not a query problem.
- **Every decision is logged.** The question, the probabilities, the confidence, the chosen option, the latency, and the model.
- **Every answer cites its nodes.** The citation is the node id and the source path. No citation, no claim.
- **The loop can stop early.** If the first retrieval is sufficient and the answer is grounded, there is no refeed. That is the happy path, and it should be the common one.
- **The loop can fail loudly.** If the evidence never becomes sufficient, return "I could not find enough evidence" and show what was tried. A confident wrong answer is the failure mode this project exists to prevent.

### 7.2 The confidence band

The decision model returns a probability and a confidence. The app uses a simple band:

- **High confidence**: accept the decision.
- **Middle confidence**: accept, but mark the step as uncertain in the trace.
- **Low confidence**: delegate the judgment to LFM2.5 with a longer prompt, and record that delegation.

The thresholds are configuration, not magic. The lab should show how the answer changes when the band moves. That is a better lesson than a single "correct" threshold.

---

## 8. Demo modes

The demo is a **recorded video** first, because that is what people watch. The repo adds three more ways to experience the same thing.

### 8.1 Video

- A short screencast, recorded from the live app or the replay player.
- Hosted like the parallax auto-debate video: `docs/assets/videos/refeed-loop.mp4` with a poster frame.
- The page uses a plain HTML5 video element, with captions and a transcript link.
- The video is the public artifact. It must work without a GPU, a clone, or a model download.

### 8.2 Interactive

The visitor clones the repo and runs the stack:

```bash
pixi install
docker compose --profile llm --profile app --profile obs up -d
pixi run demo:seed
pixi run demo
```

Then they open the lab, ask a question, and watch the loop. The app shows the retrieved nodes, the decision scores, the rewrite, the answer, and the cost.

### 8.3 Replay

The same player reads a recorded event trace. No models, no GPU, no downloads.

- The trace is JSONL, one event per line.
- The player is the same code in live and replay mode.
- The static GitHub Pages site uses replay for the on-page demo.
- A visitor can replay a place before deciding to run the full stack.

### 8.4 Agent-customizable

A coding agent can add a new place, validate it, record it, and publish it. The contract is in `lab/demos/README.md` and the root `AGENTS.md`.

The agent does not need to understand the whole codebase. It needs:

- The folder contract.
- The validation command.
- The recording command.
- The list of allowed model calls.

### 8.5 The event stream

Live and replay share one event vocabulary:

| Event | What it carries |
|---|---|
| `typing` | The visitor's question, character by character |
| `line` | A scripted line in the demo, with an optional note |
| `retrieval` | Node ids, levels, scores, source paths |
| `decision` | Question id, chosen answer, probabilities, confidence, latency |
| `rewrite` | Old query, new query, action, reason |
| `delta` | A token of the answer |
| `answer` | Final answer, citations, stop reason |
| `metrics` | Iterations, tokens, latency, cost estimate |
| `done` | The summary of the run |

The player supports **skip** and **takeover**, like the parallax watch mode. Skip moves to the next scripted turn. Takeover lets the visitor type their own question.

---

## 9. The agent harness

### 9.1 A place is a folder

```text
lab/demos/<place>/
  demo.toml        title, blurb, corpus dir, starter questions, model stack
  corpus/          the documents that make this place
  script.jsonl     visitor turns for the autoplay
  eval.jsonl       questions, gold passages, expected claims
```

A place is a small world. It has documents, a script, and a way to measure whether the raptor understood it.

### 9.2 The commands

```bash
pixi run demo:validate <place>   # schema, build the index, run the evals
pixi run demo:replay <place>     # play the recorded or generated trace
pixi run demo:record <place>     # capture the event trace
pixi run demo:index              # regenerate the site's demo registry
```

The validate command is the important one. It should fail loudly if:

- The corpus is empty or has unsupported files.
- A question has no gold passage.
- A script references a place that does not exist.
- The model stack in `demo.toml` is not available.

### 9.3 The agent playbook

The root `AGENTS.md` tells a coding agent how to work here:

1. Read `lab/demos/README.md`.
2. Create the place folder.
3. Add 10 to 30 documents to `corpus/`.
4. Add 10 to 30 questions to `eval.jsonl`, each with gold passages.
5. Add 3 to 6 visitor turns to `script.jsonl`.
6. Run `pixi run demo:validate <place>`.
7. Fix the failures.
8. Run `pixi run demo:record <place>`.
9. Add the place to the site registry.

The commands are non-interactive and idempotent. The agent can run them without a human in the loop.

### 9.4 Why this matters

The visitor can point their own agent at the repo and say "add a place about the ocean" or "make the raptor answer questions about my notes". The repo is the harness, not just the demo. That is the customization story.

---

## 10. Metrics

The canonical reference will be `mds/metrics.md` (to be written). This section is the map, not the manual.

Four groups:

### 10.1 Retrieval

- Recall@k, Precision@k, Hit@k.
- MRR and nDCG@k.
- Context precision and context recall.
- Retrieval share by level: how often a summary node beats a leaf.

### 10.2 Answer

- Faithfulness and groundedness.
- Answer relevance.
- Correctness.
- Completeness.
- Hallucination rate.
- Citation accuracy: does the answer cite the node it actually used?

### 10.3 System 1

- Decision accuracy.
- Brier score.
- Expected calibration error.
- Confidence distribution.
- Delegation rate: how often the loop asks System 2.
- Decision latency.

This is the novel section. It is where a decision model earns its place, and where a generative judge is exposed.

### 10.4 Loop and tree

- Iterations to pass.
- Refeed trigger rate.
- Rewrite gain: recall after the rewrite minus recall before.
- Marginal gain per iteration.
- Token cost per answer.
- Wall-clock latency per step.
- RAPTOR level coverage, compression ratio, cluster coherence, and retrieval share by level.

### 10.5 The comparison that matters

Run the same questions through:

1. One-shot RAG.
2. RAPTOR retrieval without the loop.
3. RAPTOR plus the loop.

The table shows what each addition bought, and what it cost. That is the article.

The metrics page must also warn about the ways the numbers lie:

- A judge scoring its own output.
- A reranker that looks good because the gold passages are easy.
- A loop that improves one metric while making the answer too long.
- A cost number that ignores the GPU and the wall clock.

---

## 11. Chosen direction: the Raptor Reserve corpus

The first place is a 100-document synthetic corpus called `raptor-reserve`. It is English only, and every document is original text written for this project. The corpus has two wings:

| Wing | Docs | What it is | Why |
|---|---|---|---|
| Reserve records | 85 | A fictional island reserve: charter, species, patrols, incidents, research, visitors, infrastructure, history | The local model cannot know these facts from pretraining, so retrieval is the only way to answer |
| Data and methods | 15 | Original summaries of RAPTOR, SearchJev, the local models, the metrics, plus the reserve's data dictionary and evaluation notes | Ties the corpus to the lab and gives the demo a technical layer |

The reserve records use real species (peregrine falcon, osprey, northern harrier, short-eared owl, and so on), but the island, the staff, the counts, and the incidents are fictional. The data and methods wing cites the public sources and does not copy them.

### 11.1 Why this corpus

- **License-clean.** All prose is original. The methods wing summarizes public research and links to it. No third-party text is reproduced.
- **Unknown to the model.** The reserve facts are invented, so LFM2.5 and d1-3B cannot answer from pretraining. A correct answer is evidence that retrieval worked.
- **Coherent.** One island, one staff, one budget, one set of dates. The tree has something real to cluster.
- **Extensible.** The generator is a Python script with a seed world. An agent can add a document, a question, or a whole place.
- **Good for video.** A reserve with drones, storms, lead poisoning, and a lighthouse is more watchable than a pile of API docs.

### 11.2 The shape

- 10 governance documents.
- 15 species and ecology documents.
- 15 field operations documents.
- 15 research and monitoring documents.
- 10 visitor and education documents.
- 10 infrastructure and logistics documents.
- 10 history and culture documents.
- 15 data and methods documents.

Every document targets **500 to 800 words** and uses section headings. At 512-token chunks with 64 overlap, that is 2 to 4 chunks per document, or about 200 to 300 chunks for the corpus. That is the minimum for a meaningful three-level RAPTOR tree. A 150-word note is allowed only when it is linked to a longer document, and it does not count toward the length target.

### 11.3 The eval set

`eval.jsonl` has 50 questions:

- 30 reserve-specific questions, whose answers exist only in the fictional records.
- 10 methods questions about RAPTOR, SearchJev, and the local models.
- 10 multi-hop questions that need two documents, such as a wind limit plus a flight plan.

Each question lists its gold document ids and a short expected answer. The validate command checks that every gold id exists.

### 11.4 The license

The corpus is released under CC BY 4.0. The `NOTICE.md` in the place folder states that the text is original, names the public sources used for the methods wing, and explains that no third-party text is reproduced. The code license is separate and still to be chosen.

The corpus is a lab artifact, not a final dataset. It is large enough to show the tree and small enough to inspect. The generator is the source of truth; the Markdown files are the build output.

---

## 12. Open goals

- **Bigger summarizer profile.** LFM2.5-24B-A2B or a similar model, started only for tree building, behind a `big` Compose profile. The interface stays the same.
- **Model fallback.** If LFM2.5 disappoints on summaries, or tool calling becomes necessary later, try Granite 4.x or Gemma 4 behind the same preset interface. The loop and the metrics should not care which writer answers.
- **The big loop.** Log failures, turn them into eval cases, rebuild the tree, and compare the new tree with the old one.
- **Graph RAG comparison.** Build a small entity graph and compare it with the summary tree on the same questions. The point is to show when a graph helps and when it is ceremony.
- **Multimodal tier.** The full EmbeddingGemma 2 model accepts text, images, video, and audio, and d1-3B accepts images. The 310 MB Q8_0 GGUF is the text backbone, so a multimodal tier needs a multimodal build or a separate image model. Add it only after the text loop is solid.
- **Calibration dashboard.** Plot decision confidence against correctness. Show the delegation band. This is the most educational page in the project.
- **Video automation.** Record the replay with Playwright, convert with ffmpeg, and publish the mp4 and the poster. Keep a manual path for the first video.
- **QuALITY evaluation.** A credible benchmark run, with the same three configurations as the demo.
- **More places.** Ocean, museum, space station, whatever the visitor's agent can dream up.

---

## 13. Non-goals

- No cloud LLM, no API key, no hosted inference.
- No LangChain or LlamaIndex in the v1 loop.
- No vector database in v1.
- No auth, no multi-user, no accounts.
- No tool calling from the model.
- No fine-tuning.
- No attempt to beat a benchmark in v1.
- No claim that the loop is always better. The project measures the trade.

---

## 14. Communication goal

The demo has to be legible. This is the "improving the communication" goal, written down so it does not get lost.

### 14.1 What the viewer should understand

After the video, a viewer should be able to answer:

1. Why did one-shot RAG fail on this question?
2. What did the summary tree add?
3. What did the refeed loop add?
4. Why was a 3B decision model enough for the loop?
5. What did the extra steps cost in latency and tokens?

If the video does not answer those five questions, it is not done.

### 14.2 The video beats

1. **The question.** A question that needs two documents and one summary. One-shot RAG gets it wrong or incomplete.
2. **The first bite.** Show the retrieved chunks, the scores, and the levels.
3. **The judgment.** Show d1 saying "not sufficient", with the probability and the confidence.
4. **The refeed.** Show the action, the rewritten query, and the second retrieval.
5. **The answer.** Show the grounded answer, the citations, and the cost.

### 14.3 The on-screen rules

- Every step has a label: `retrieve`, `judge`, `refeed`, `answer`.
- Every number has a unit and a tooltip.
- Every decision shows the probability and the confidence.
- Every citation points to a node the viewer can inspect.
- No jargon without a plain-language gloss. The glossary is in this file and on the site.
- The raptor metaphor is seasoning, not a substitute for the explanation.

### 14.4 The site

- A hero video with a poster and a transcript.
- A short "what you are looking at" panel.
- A "run it yourself" block with the exact commands.
- A "point your agent at it" block with the folder contract.
- A metrics page that links back to `mds/metrics.md`.
- A lab index that lists the places, the questions, and the results.

The voice stays informal. The claims stay small. The numbers stay visible.

---

## 15. Decisions locked

- [x] Local only. No cloud LLM.
- [x] EmbeddingGemma 2 for embeddings.
- [x] LFM2.5-8B-A1B for summaries, rewrites, and answers.
- [x] d1-3B for System-1 decisions.
- [x] One llama.cpp router with three presets.
- [x] SQLite plus numpy cosine, no vector database.
- [x] Plain Python plus FastAPI, no agent framework in the loop.
- [x] Arize Phoenix for traces and evals.
- [x] 100 original English documents for `raptor-reserve`, 85 reserve records and 15 data and methods, CC BY 4.0.
- [x] Recorded video first, then interactive, replay, and agent modes.
- [x] `rptr-` prefix for Docker resources, pixi workspace `rptr`.
- [x] No tool calling, no fine-tuning, no auth, no multi-user.

---

## 16. References

### Primary sources

- RAPTOR paper: https://arxiv.org/abs/2401.18059
- RAPTOR reference implementation: https://github.com/parthsarthi03/raptor
- SearchJev paper: https://arxiv.org/abs/2610.05107
- TypeSafe System One API: https://docs.typesafe.ai/api/system-one
- llama.cpp server documentation: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- llama.cpp INI presets: https://github.com/ggml-org/llama.cpp/blob/master/docs/preset.md
- EmbeddingGemma 2 model card: https://huggingface.co/google/embeddinggemma-2
- EmbeddingGemma 2 GGUF: https://huggingface.co/ggml-org/embeddinggemma-2-GGUF
- LFM2.5-8B-A1B: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B
- LFM2.5-8B-A1B GGUF: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF
- d1-3B: https://huggingface.co/LiquidAI/d1-3B
- d1-3B GGUF: https://huggingface.co/LiquidAI/d1-3B-GGUF
- Liquid d1 announcement: https://www.liquid.ai/blog/d1-open
- Arize Phoenix self-hosting: https://arize.com/docs/phoenix/self-hosting
- Arize Phoenix evaluation: https://arize.com/docs/phoenix/evaluation/llm-evals

### Background reading

- Loop engineering for RAG: https://towardsdatascience.com/loop-engineering-for-rag-the-small-loops-inside-each-step-the-big-loops-across-the-pipeline/
- Four retrieval techniques: https://thoughtworks.medium.com/https-www-thoughtworks-com-insights-blog-generative-ai-four-retrieval-techniques-improve-rag-f641e2b1db6c
- RAG with a feedback loop: https://diamant-ai.com/tutorials/rag-techniques-retrieval-with-feedback-loop

### Project references

- Memory lab: https://github.com/AISidesKicks/mem-codedorf-dev
- Parallax observer: https://github.com/AISidesKicks/truth.parallax.observer

What we borrow from the memory lab:

- The model profile pattern: one shell file per model, environment overrides win.
- The pixi and `scratch/` conventions.
- The lab structure: one experiment, one write-up, one result file.

What we borrow from the parallax observer:

- The llama.cpp router with INI presets.
- The EmbeddingGemma 2 configuration: mean pooling, 4096 configured context, matching batch.
- The autoplay pattern: scripted turns, live answers, skip and takeover.
- The docs and lab structure, the prefixes, and the tone.

What we change:

- No OpenViking, no memory server, no debate agents.
- No PydanticAI in the loop for v1. Plain Python is clearer for a teaching loop.
- No Qdrant or external vector store. SQLite and numpy are enough.
- No Granite or Qwen model in v1. One LFM family for the two LLMs, plus EmbeddingGemma 2 for embeddings.

### Source hygiene

The old `INTENT.md` contained a citation to arXiv 2603.01417 and several LinkedIn links. The arXiv id was not verified for this document, and the LinkedIn links are unstable. Check them before publishing. The primary sources above are the ones to trust.

---

## 17. Glossary

- **RAG**: Retrieval-Augmented Generation. Retrieve documents, put them in the prompt, generate an answer.
- **One-shot RAG**: One retrieval, one answer. No critic, no retry.
- **Refeed loop**: Retrieve, judge, rewrite if needed, retrieve again, answer. The small loop in this project.
- **RAPTOR**: Recursive Abstractive Processing for Tree-Organized Retrieval. Chunk, embed, cluster, summarize, recurse, and retrieve from the tree.
- **Summary tree**: The RAPTOR output. Leaves are chunks, higher levels are summaries.
- **Collapsed tree**: Search all levels of the tree at once instead of walking down from the root.
- **System 1**: Fast, cheap, automatic judgment. In this project, d1-3B.
- **System 2**: Slow, expensive reasoning and writing. In this project, LFM2.5-8B-A1B.
- **Decision model**: A model trained to answer typed questions with probabilities, not to generate prose.
- **`noul`**: A yes/no question. The answer is the probability of yes.
- **`choice`**: A question with named options. The answer is the chosen option plus the distribution.
- **`score`**: A rating on an ordered rubric. The answer is the expected level plus the distribution.
- **Calibration**: Whether a model's confidence matches its accuracy. A model that says 80 percent should be right about 80 percent of the time.
- **ECE**: Expected Calibration Error. The average gap between confidence and accuracy across bins.
- **Brier score**: A proper scoring rule for probabilistic forecasts. Lower is better.
- **Recall@k**: Of the relevant documents, how many are in the top k.
- **Precision@k**: Of the top k documents, how many are relevant.
- **MRR**: Mean Reciprocal Rank. How high the first relevant result sits, averaged over queries.
- **nDCG@k**: Normalized Discounted Cumulative Gain. Rewards relevant results near the top.
- **Faithfulness**: Whether the answer is supported by the retrieved context.
- **Context precision**: How much of the retrieved context is relevant.
- **Context recall**: How much of the needed context was retrieved.
- **Phoenix span**: One timed operation in a trace. Retrieval, decision, rewrite, and answer are spans.
