# The model stack

Three models, three jobs. The lab picks models by role, not by leaderboard, and the role decides everything else: context size, temperature, quantisation, and how many calls per question the loop is allowed to make.

| Role | Model | Quant | Size | Job |
| --- | --- | --- | --- | --- |
| Embeddings | EmbeddingGemma 2 | Q8_0 | 310 MB | Turn text into 768 numbers |
| Writer | LFM2.5-8B-A1B | Q4_K_M | 5.2 GB | Summaries, rewrites, the final answer |
| Decisions | d1-3B | Q8_0 | 2.9 GB | Answer typed questions with probabilities |

About 8.3 GB of weights in total. The three loaded presets use about 11.1 GB of the 12 GB card, which leaves very little room for a second copy of the writer.

## EmbeddingGemma 2

The encoder. Text only, 768 dimensions, mean pooling, 4096 token context. A chunk is about 512 tokens, so the context is comfortable.

Q8_0 is a good trade here. Embeddings are cheap to run and the file is small, so there is no reason to quantise it further. The corpus is embedded once, and the query is embedded on every question.

The model needs a recent llama.cpp build because of the `gemma-embedding2` architecture. See [llama.cpp as the local router](llamacpp.md).

## LFM2.5-8B-A1B

The writer. 8.3B parameters in total, about 1.5B active per token, a large context window, and a hybrid architecture that mixes attention and convolution. For the lab it matters that it is fast enough to run on a 12 GB card next to the other two models.

The lab uses it for three different jobs, with three different settings:

| Job | Temperature | Why |
| --- | --- | --- |
| Cluster summaries | 0.1 | Near deterministic, so the tree is reproducible |
| Query rewrites | 0.2 | A little room to reword, but never to invent a new topic |
| The final answer | 0.0 | The same question should give the same answer |

The final answer also gets a tight budget: at most 80 words, at most three leaf chunks, citations on every factual sentence. A writer with a short leash answers better than a writer with a long one, because the model cannot wander into the rest of the corpus.

## d1-3B

The decision model. It answers typed questions with probabilities and does not write text at all. The lab calls it 5 times for relevance, once for sufficiency, once for the action, and once for the grounded check. That is why the small model is the right one: it is called a lot and it has to be cheap and predictable.

Details about the questions, the confidence band, and the delegation to the writer are in [System 1 decisions](systemone.md).

## Why three models and not one

One model would be simpler to install and to explain. It would also be worse at everything:

- A 3B model writes shorter and more literal answers, and it forgets citations.
- An 8B model makes every relevance judgement cost about 30 times more, and its probabilities are less meaningful because it was trained to be chatty.
- Separating the roles also separates the measurements. The latency of a decision is not mixed with the latency of a write, so the trace shows where the time actually goes.

The one rule that keeps this honest: no model ever sees the corpus as a chat. The writer sees at most three excerpts. The decision model sees one passage or one evidence set.

## Licenses

| Model | License |
| --- | --- |
| EmbeddingGemma 2 | Apache 2.0 |
| LFM2.5-8B-A1B | LFM Open License 1.0 |
| d1-3B | LFM Open License 1.0 |
| llama.cpp | MIT |

The repository does not redistribute any weights. The download script fetches them from their publishers. See `NOTICE.md` for the full list.

## What we would change first

- The writer context is 16K, but the writer only ever sees about 1,500 tokens. The context could shrink and free memory for a larger batch.
- EmbeddingGemma 2 runs at 4096 tokens, which is more than a chunk needs. A smaller context would make the encoder faster.
- d1-3B is quantised to Q8_0. A Q4 build would save about 1.5 GB and might not cost much accuracy on yes or no questions. That is an experiment, not a plan.

Read next: [the refeed loop](refeed.md), [the metrics](metrics.md).
