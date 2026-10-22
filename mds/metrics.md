# RAG metrics for Refeed Raptor

A RAG demo can look good with one nice answer. The point of this page is to show where retrieval, the refeed loop, and the decision model help, where they do not, and what the help costs.

The short version: report retrieval, answer quality, calibration, and cost together. A better answer that doubles the latency is a trade, not a win. A confident wrong answer is worse than an unsure right one, because the loop will trust it.

## The four questions

Every run should answer four questions.

1. Did we find the evidence? This is retrieval.
2. Did the answer use the evidence? This is answer quality.
3. Did the model know when it was unsure? This is calibration.
4. What did it cost? This is the system view.

A run that reports only question 2 is a demo. A run that reports all four is an experiment.

## A run record

Record these fields before you compare anything:

- place id and corpus version
- eval set id and question count
- model ids and quantization
- chunk size and overlap
- tree shape and build seed
- loop configuration: top 20, keep 8, max 2 refeeds, confidence bands
- commit hash
- date and hardware

If two runs differ in more than one of these fields, the comparison is a story, not a result.

## Retrieval metrics

Retrieval metrics ask whether the right passage was found. They are cheap to compute and they explain most answer failures.

| Metric | What it means | When to use |
| --- | --- | --- |
| Recall@k | Fraction of gold passages in the top k. | Primary retrieval metric. A missing passage cannot be fixed by a better prompt. |
| Precision@k | Fraction of the top k that is relevant. | Context budget and distraction. A crowded context costs tokens and can confuse the writer. |
| Hit@k | 1 if at least one gold passage is in the top k, 0 otherwise. | A quick sanity check for single-document questions. |
| MRR | Mean of 1 / rank of the first relevant result. | When the first good result matters more than the rest. |
| nDCG@k | Graded relevance with a discount for lower ranks. | When some passages are more useful than others. |
| Context precision | Share of the retrieved context that is useful. | Judge-based evaluation of the prompt. |
| Context recall | Share of the needed context that was retrieved. | Judge-based evaluation of the prompt. |

Recall is the main metric for this project. If the gold document is not in the top 20, the loop has nothing to work with. Precision is the second metric, because the writer only sees the top 8 after the relevance filter.

### Document level and span level

Be explicit about the unit. The eval file lists gold document ids. The retriever scores chunks. A chunk hit is mapped to its document. A document-level hit is not a span-level hit: the retriever can find the right document and the wrong paragraph.

Report both when you can:

- Document Recall@k: did any chunk from a gold document appear?
- Span Recall@k: did the chunk that contains the answer appear?

If you only have document labels, say so. Do not call a document hit an answer hit.

### RAPTOR level metrics

The tree adds a level to the retrieval question. Report:

- **Level coverage**: the share of retrieved nodes from level 0 (chunks), level 1, and level 2.
- **Level lift**: recall at a fixed k with the tree minus recall with leaves only.
- **Level match**: whether a broad question retrieved a summary and a detail question retrieved a leaf.
- **Collapsed tree vs tree walk**: the same questions, two retrieval modes.

A summary node that wins on a detail question is a warning. A leaf that wins on a broad question is also a warning. The level mix is part of the result, not a detail.

## Answer metrics

Answer metrics ask whether the final text is correct and supported.

| Metric | What it means | Notes |
| --- | --- | --- |
| Faithfulness | Every claim is supported by the retrieved context. | The core RAG metric. |
| Groundedness | The answer sticks to the sources and the citations. | Stricter than faithfulness when citations are required. |
| Answer relevance | The answer addresses the question. | A correct but off-topic answer scores low. |
| Correctness | The answer matches the expected answer. | Use a short reference and a judge or a human. |
| Completeness | The answer covers the important parts. | A short answer can be correct and incomplete. |
| Citation accuracy | The cited node really contains the claim. | Check by hand on a sample. |
| Hallucination rate | Unsupported claims divided by total claims. | Report the count, not only the rate. |

### Judge caveats

A judge model is useful, but it is not neutral.

- **Self-preference**: a model prefers its own writing. Do not use the writer as the only judge.
- **Position bias**: the first answer in a pairwise prompt wins more often. Swap the order and average.
- **Length bias**: longer answers can look more complete. Control for length or score completeness separately.
- **Prompt sensitivity**: a small wording change can move the score. Keep the judge prompt fixed and versioned.
- **Cost**: a judge pass costs tokens and latency. A 50-question set is cheap; a 5,000-question set is not.

Use a judge that is not the writer, or use a human sample. In this project, d1-3B is a decision model, not a prose judge. It can answer typed questions about support, but the final answer score should come from a separate judge pass or a human spot check.

A good pattern is:

1. Judge all answers with a fixed judge.
2. Hand-check 20 percent, stratified by score.
3. Report the agreement between the judge and the human.
4. If agreement is low, fix the rubric before trusting the score.

## Calibration metrics

Calibration asks whether confidence matches accuracy. A model that says 80 percent should be right about 80 percent of the time.

| Metric | What it means | Direction |
| --- | --- | --- |
| Brier score | Mean squared error of the probability forecasts. | Lower is better. |
| ECE | Expected calibration error. Bin the predictions and average the gap between confidence and accuracy. | Lower is better. |
| Reliability diagram | Confidence versus accuracy, one point per bin. | Should follow the diagonal. |
| Confidence distribution | How often the model uses each confidence range. | A model that always says 0.9 is not calibrated. |
| Decision accuracy | Share of typed decisions that are correct. | Higher is better. |
| Delegation rate | Share of decisions sent to the writer or a human. | A trade between cost and quality. |

The loop uses confidence to decide when to delegate. A simple band:

- High confidence: accept the decision and continue.
- Middle confidence: delegate to the writer or ask for a rewrite.
- Low confidence: stop, ask a human, or return "not enough evidence."

The bands are a configuration. The eval should show what happens when they move.

A model can be accurate and overconfident. That is the dangerous case, because the loop will trust a wrong judgment. The calibration dashboard is the first place to look when the refeed loop behaves strangely.

The SearchJev paper reports 41 to 74 percent lower ECE for decision models than for same-size generative models. That is the paper's result, not this lab's. Measure your own.

## Loop metrics

The refeed loop is the part that is supposed to earn its keep. Measure it directly.

| Metric | What it means |
| --- | --- |
| Refeed trigger rate | Share of questions that refeed at least once. |
| Rewrite gain | Answer score after the rewrite minus the score before it. |
| Marginal gain | Gain per extra iteration. The second refeed should be worth its cost. |
| Stop reason | Sufficient, max iterations, no new evidence, or error. |
| Average iterations | Mean number of retrieve-judge-rewrite cycles. |
| Decision latency | Time per d1 call. |
| Answer latency | Total time from question to final answer. |
| Token cost | Prompt and completion tokens for the writer and the judge. |

The key comparison is:

1. One-shot RAG: one retrieval, one answer.
2. RAPTOR retrieval: the tree, still one answer.
3. RAPTOR plus the loop: retrieve, judge, rewrite, answer.

Use the same 50 questions, the same models, and the same chunking. Report the paired difference, not two independent averages.

A loop that raises the answer score by 2 points and the latency by 80 percent is not automatically a win. Show the trade.

## RAPTOR metrics

The tree is a structural intervention. Measure the structure as well as the answer.

| Metric | What it means |
| --- | --- |
| Tree shape | Leaves, level 1 nodes, level 2 nodes, root. |
| Compression ratio | Source tokens divided by summary tokens. |
| Summary faithfulness | Do the summaries preserve the source facts? Sample and check. |
| Cluster coherence | Are the chunks in a cluster about the same thing? Sample and check. |
| Level coverage | Which levels are retrieved for which question types. |
| Retrieval lift | Recall at a fixed k with the tree minus recall with leaves only. |
| Build cost | Summary tokens, build time, and storage. |

The paper reports a 20 percentage point absolute gain on QuALITY when RAPTOR is paired with GPT-4. That number is a reason to try the method, not a result for this corpus. The lab measures its own.

A tree can hurt. A bad summary can replace a good chunk. A cluster can mix two topics and produce a vague node. The failure cases are part of the report.

## System metrics

The system view keeps the demo honest about the local constraint.

- Prompt tokens and completion tokens.
- Time to first token.
- Total latency, p50 and p95.
- Peak VRAM.
- Model load time.
- Tree build time.
- SQLite and index size.
- Outbound network calls. The target is zero except localhost.
- Energy or power draw, if the hardware can measure it.

A local stack has a fixed memory budget. The three models and one CUDA context should fit on the 12 GB card. If a change pushes the stack over the budget, the change is not free.

## How to report a run

Use one table with one row per configuration.

| Config | Recall@5 | Recall@10 | MRR | nDCG@10 | Answer | Faithful | Citation | ECE | Delegation | Tokens | p50 ms | p95 ms | Refeed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| One-shot | | | | | | | | | | | | | |
| RAPTOR | | | | | | | | | | | | | |
| RAPTOR + loop | | | | | | | | | | | | | |

Add the sample size, the eval version, the model versions, and the commit under the table. With 50 questions, one question is 2 percentage points. Do not report a 2-point difference as a breakthrough.

Show three failure cases next to the wins:

- A question where retrieval missed the gold document.
- A question where the loop rewrote a good query into a worse one.
- A question where the answer was correct but the citation was wrong.

The failure cases are the most useful part of the report.

## Common traps

- **Judge self-preference.** The writer likes its own answers.
- **Position bias.** The first answer in a pairwise prompt wins.
- **Gold leakage.** The question or the prompt contains the answer.
- **Easy negatives.** The retriever looks good because the distractors are weak.
- **Small n.** A 50-question set cannot support a 1-point claim.
- **One metric.** Recall can rise while answer quality falls.
- **Ignoring cost.** A loop that triples latency needs a reason.
- **Synthetic corpus as benchmark.** This corpus is a lab instrument.
- **Same model writes and judges.** Use a separate judge or a human sample.
- **Different question sets.** Compare runs on the same questions.
- **Retrieval hit as answer win.** Finding the passage is not the same as using it.

## A minimal local eval

The smallest useful loop:

1. Load the 50 questions from `eval.jsonl`.
2. Run one-shot RAG, RAPTOR, and RAPTOR plus the loop.
3. Record Recall@5, Recall@10, MRR, nDCG@10, answer score, faithfulness, citation accuracy, ECE, delegation rate, tokens, and latency.
4. Save the runs to SQLite and trace them in Phoenix.
5. Replay the traces without the models.
6. Put the table and the three failure cases in the report.

The eval is part of the app, not a notebook. It should run on the same commit as the demo.

## References

- RAPTOR: arXiv 2401.18059
- SearchJev: arXiv 2610.05107
- RAGAS: arXiv 2309.15217
- ARES: arXiv 2311.09476
- BEIR: arXiv 2104.08663
- MTEB: arXiv 2210.07316
- Phoenix documentation: https://docs.arize.com/phoenix
- EmbeddingGemma 2 model card: https://huggingface.co/google/embeddinggemma-2
- LFM2.5-8B-A1B model card: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B
- d1-3B model card: https://huggingface.co/LiquidAI/d1-3B


---

## The numbers from the lab

Retrieval on the 50 questions of the eval set:

| Mode | Recall@5 | Recall@10 | Recall@20 | MRR |
|---|---|---|---|---|
| Keyword | 0.98 | 0.98 | 1.00 | 0.829 |
| RAPTOR | 0.96 | 0.98 | 1.00 | 0.861 |

The full loop, same 50 questions, one answer per question:

| Measure | Value |
|---|---|
| Answered | 50 of 50 |
| Citation hit rate | 0.94 |
| Mean refeeds | 0.00 |
| Mean latency | 1.5 s |
| Slowest answer | 4.3 s |

The citation hit rate is the share of answers that cite a document that holds the gold answer. It is not a faithfulness score: a faithful answer can cite the wrong document, and an unfaithful answer can cite the right one. The lab measures the first because it is cheap and automatic. A human check of the recorded turns is still the last word.

Reproduce it with:

```bash
pixi run eval -- --place raptor-reserve --answers --output scratch/answers.json
```

The command writes the full report, including the per question rows, so the numbers can be checked one by one.
