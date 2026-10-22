# System 1 decisions

The loop needs a lot of small judgements: is this passage relevant, is the evidence enough, what should the next search do, is the answer supported by the text we found. The lab does not ask the writer model for those. It asks a decision model that cannot write prose.

That is the whole idea behind a System-1 model: it answers a typed question with a probability instead of generating text. Two short videos from IBM Technology cover the same idea from the research side.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/YGgNBcIgI4s" title="What Is Jev? The AI Model That Doesn't Generate Text" frameborder="0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

[What Is Jev? The AI Model That Doesn't Generate Text](https://www.youtube.com/watch?v=YGgNBcIgI4s) - IBM Technology.

<iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/_yO_Q7qo0HQ" title="The Problem with Jev: Can You Trust AI Decisions?" frameborder="0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

[The Problem with Jev: Can You Trust AI Decisions?](https://www.youtube.com/watch?v=_yO_Q7qo0HQ) - IBM Technology.

The second video is the important one for this lab. A decision model that returns a probability is easy to trust and easy to check, until you ask what the number means. The whole point of the confidence band below is to answer that question in code, not in a prompt.

## The local stand-in

The lab runs `d1-3B` (Q8_0, about 2.9 GB on disk) as the System-1 model. It sits on the same GPU as the writer, it serves from the same llama.cpp router, and it never sees the corpus as a chat. It only gets a state string and a list of typed questions.

The role matters more than the model. Any model that can answer a typed question with a probability could sit here:

- the same LFM2.5 writer with a strict output format
- a bigger classifier with a prompt
- a small dedicated model like d1-3B

The lab uses the small one, because the loop calls it 20 times per attempt.

## The two question types

The router exposes `/v1/systemone`, which takes a `state` string and a dict of questions. Each question has a type. There are only two types in the lab.

A `noul` is a yes or no question with custom labels:

```python
noul(
    "Does the evidence contain enough facts to answer the question specifically, "
    "including the name, number, or rule that the question asks for?"
)
```

A `choice` is a pick one from a fixed set:

```python
choice(
    "The evidence is not sufficient. What should the next search do?",
    {
        "keep": "The query is good; retrieve more passages with the same question.",
        "broaden": "The query is too narrow; remove a constraint and search wider.",
        "narrow": "The query is too broad; add the specific entity, place, or year.",
        "decompose": "The question has several parts; split it into two searches.",
    },
)
```

Both come back with a value, the probabilities of every option, and a confidence. The helper functions live in `src/rptr/llm.py`.

## The five decisions

| Decision | Type | Question |
| --- | --- | --- |
| `relevant` | `noul` | Is this passage relevant to the question? |
| `sufficient` | `noul` | Is the evidence enough to answer? |
| `action` | `choice` | Should we keep, broaden, narrow, or decompose? |
| `grounded` | `noul` | Is the drafted answer supported by the retrieved text? |
| `confidence` | derived | How sure is the decision, and should we delegate? |

The relevance step is batched. The router takes many typed questions in one call, so 20 passages cost 5 requests with 4 passages each, not 20 requests.

## From probability to confidence

A raw probability is awkward to compare across questions. `0.51` for one question and `0.51` for another can mean very different things. The lab converts a probability into a distance from the decision boundary:

```python
def _confidence(probability: float) -> float:
    return abs(probability - 0.5) * 2.0
```

So `0.5` becomes `0.0` confidence, `0.75` becomes `0.5`, and `0.0` or `1.0` become `1.0`. The confidence is in the range 0 to 1 and it means one thing only: how far the model is from a coin flip.

The bands are configuration, not magic numbers:

| Band | Confidence | What the loop does |
| --- | --- | --- |
| high | 0.75 and up | Accept the decision. |
| middle | 0.30 to 0.75 | Accept the decision, mark the step as uncertain in the trace. |
| low | under 0.30 | Hand the judgement to the writer model. |

The thresholds live in `PipelineConfig` in `src/rptr/pipeline.py`:

```python
high_confidence: float = 0.75
low_confidence: float = 0.30
delegate_low_confidence: bool = True
```

Moving the band is the easiest experiment in the lab. Lower `low_confidence` and the writer model gets more say. Raise it and the loop trusts the small model more.

## When the writer takes over

Delegation is not "the writer rewrites the answer". It is "the writer answers the question that the small model was unsure about".

Two steps delegate today:

- Sufficiency. When the sufficiency decision lands in the low band, LFM2.5 gets the evidence and one line of instructions: the evidence must contain the specific fact needed to answer. The trace records `delegated: true` and `source: lfm`.
- Groundedness. Only a negative grounded decision in the low band is delegated. A negative decision that the small model is sure about is trusted, because a sure "no" is useful information.

The trace keeps the probability, the confidence, the band, and the source of the final answer. That is the audit trail. If the answer is wrong, you can see which step went soft.

## Why not let the writer do it all

The writer model is 8.3B parameters with a large context window. It can read 20 passages and judge sufficiency in one pass, and it will sound more confident while doing it. The problem is that confidence and calibration are different things. A model that writes a confident sentence about thin evidence gives you no signal that it was unsure. A probability gives you exactly that signal.

So the lab splits the work by price and by auditability:

- cheap, many, numeric, auditable decisions go to d1-3B
- expensive, few, creative, hard to audit work goes to LFM2.5

If you want to see the cost side, the trace records the latency of every decision call and every write.

## What still goes wrong

The decision model is not the weakest link in every case. Two known failures in the current corpus:

- The relevance step says a passage about a different species is relevant, because the passage really is about birds.
- The sufficiency step says yes when the evidence has the topic but not the number.

Both failures are visible in the trace, and both are the reason the writer sees at most three title-matched leaf chunks. The small model picks the neighbourhood, the writer stays inside the evidence that the title actually matches.

## Code map

| File | What is in it |
| --- | --- |
| `src/rptr/llm.py` | `noul`, `choice`, `LlamaRouter.systemone`, the `Decision` dataclass |
| `src/rptr/pipeline.py` | The five decisions, the confidence function, the bands, the delegation |
| `src/rptr/tree.py` | Uses the writer model for summaries, never for decisions |
| `mds/metrics.md` | Brier score, ECE, and how to read the calibration numbers |

Read next: [the refeed loop](refeed.md) and [the model stack](models.md).
