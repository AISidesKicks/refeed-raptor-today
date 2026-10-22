"""Data and methods documents for the Raptor Reserve corpus."""

from common import Doc, W

DOCS = [
    Doc(
        "rr-086",
        "RAG Overview for the Reserve Library",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
The reserve library has 100 documents, about 60,000 words, and more than 200 chunks. A person can read one document in a few minutes, but nobody can hold the whole library in their head. The librarian uses retrieval-augmented generation, or RAG, to find the right passages before it answers.

The pipeline is small. The question is embedded with EmbeddingGemma 2. The retriever scores every chunk with cosine similarity and keeps the top 20. The decision model, d1-3B, scores each chunk for relevance. The loop keeps the top 8. If the evidence is not sufficient, d1 chooses an action and LFM2.5 rewrites the question. The loop retries at most twice. LFM2.5 writes the answer with citations. d1 checks whether the answer is grounded in the retrieved text.

Everything runs on the island's GPU. There is no cloud model and no API key. The documents, the embeddings, the tree, and the traces stay on the reserve server. The only network call is the local llama.cpp router on port 8080.

The librarian is not a chatbot that knows the reserve. It is a reader that can point to the page. If the evidence is missing, it says so. That is the behavior the reserve wants.

The full method is documented in the lab's INTENT.md and in the methods wing of this corpus.
""",
    ),
    Doc(
        "rr-087",
        "RAPTOR Summary Tree",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
RAPTOR stands for Recursive Abstractive Processing for Tree-Organized Retrieval. The paper is arXiv 2401.18059 by Sarthi and colleagues, published at ICLR 2024.

The method is simple. Split the corpus into chunks. Embed the chunks. Cluster the embeddings. Summarize each cluster. Embed the summaries. Cluster again. Repeat until the tree has a root. Retrieval can search the leaves, the summaries, or every level at once.

The reserve's tree has three levels. Level 0 is the chunks, about 512 tokens each with a 64-token overlap. Level 1 is about 20 cluster summaries. Level 2 is about 5 higher summaries. The root is one page. The tree is stored in SQLite, not in a vector database.

The default retrieval mode is the collapsed tree: search every level at once and let the scores decide. The paper reports that this works better than walking down from the root. It is also easier to debug.

The paper reports a 20 percentage point absolute gain on the QuALITY benchmark when RAPTOR is paired with GPT-4. The reserve does not assume that number transfers. The lab measures its own recall, answer quality, and cost on the 50-question eval set.

The tree is rebuilt when the corpus changes. The build is deterministic: same documents, same seed, same tree.
""",
    ),
    Doc(
        "rr-088",
        "SearchJev and System 1 Decisions",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
SearchJev is a 2026 research paper from Huawei, arXiv 2610.05107. It studies the small decisions that a search agent makes: is this passage relevant, is the evidence sufficient, what should I do next.

The paper's claim is that a generative model is a poor fit for those decisions. It spends tokens on every judgment, and its confidence is not calibrated. A decision model can answer a typed question in one forward pass, with zero generated output tokens, and return a probability.

Jev is TypeSafe's System-1 model. SearchJev is the research behind the idea. The local stand-in is Liquid's d1-3B, which is 3.1B parameters and runs on the same GPU as the writer.

llama.cpp exposes the capability at `POST /v1/systemone`. There are three question types. `noul` is a yes or no question and returns the probability of yes. `choice` picks one of several named options and returns the full distribution. `score` rates an ordered rubric and returns the expected level.

The paper reports 5.2 to 5.3 times faster decisions than same-size Qwen3.5 models, 41 to 74 percent lower expected calibration error, and a BrowseComp-Plus accuracy gain from 45 percent to up to 54 percent. Those numbers are the paper's, not the reserve's. The lab tests the same split on its own questions.

The reserve uses five decisions: relevant, sufficient, action, grounded, and confidence. The confidence band decides when to delegate to LFM2.5.
""",
    ),
    Doc(
        "rr-089",
        "EmbeddingGemma 2",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
EmbeddingGemma 2 is Google's open multimodal embedding model. The full model has 740M parameters: a 270M text backbone, a 170M vision encoder, and a 300M audio encoder. It maps text, images, video, and audio into one 768-dimensional space.

The text model has an 8K token context, mean pooling, and Matryoshka representation learning. The output can be truncated to 512, 256, or 128 dimensions and re-normalized. The model supports more than 100 languages and code. The license is Apache 2.0.

The reserve uses the text-only GGUF. The Q8_0 file is 310 MB. It needs llama.cpp build b11455 or newer because the architecture is `gemma-embedding2`. The model supports 8K context; the reserve configures 4096 because a chunk is about 512 tokens and the smaller cache is faster.

The settings matter. Pooling must be mean. The context is 4096 in the reserve config. Batch size and micro-batch size are both 4096. If the batch is smaller than the longest chunk, the encoder rejects the input with `input is too large to process`.

Text inputs use prefixes. Queries use `task: search result | query: ...`. Documents use `title: ... | text: ...`. The prefix is not decoration; it moves the query and the document into the same task space.

The reserve uses full 768-dimensional vectors. The corpus is small enough that the storage saving from truncation is not worth the quality risk.
""",
    ),
    Doc(
        "rr-090",
        "LFM2.5-8B-A1B",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
LFM2.5-8B-A1B is Liquid AI's local reasoning and writing model. It has 8.3B total parameters and 1.5B active parameters. The context window is 128K tokens. The architecture has 24 layers: 18 double-gated convolution layers and 6 grouped-query attention layers.

The reserve uses the Q4_K_M GGUF, which is 5.16 GB. The model fits on a 12 GB card alongside d1-3B and EmbeddingGemma 2. The recommended sampling settings are temperature 0.2, top_k 80, and repeat penalty 1.05.

The model writes the cluster summaries, the query rewrites, and the final answer. For summaries and rewrites, reasoning is disabled. For the final answer, reasoning is optional and is measured, not assumed. A reasoning trace can improve a hard answer, but it also adds tokens and latency.

The model is not a judge. It does not decide whether a passage is relevant or whether the evidence is sufficient. Those decisions go to d1-3B. Keeping the roles separate is the point of the System 1 and System 2 design.

The license is the LFM Open License. Check the model card before commercial use. The reserve uses the model locally and does not send data to Liquid.

The writer is the most expensive part of the loop. The metrics page reports its token cost and latency next to the answer quality.
""",
    ),
    Doc(
        "rr-091",
        "d1-3B",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
d1-3B is Liquid AI's local decision model. It has 3.1B parameters and a 32K context. It is multimodal, with a vision encoder, and it is trained for typed decisions rather than prose.

The model is not a chat model. It does not write paragraphs. It answers a question with a probability, a choice, or a score. That constraint is what makes it cheap: one forward pass, no generated output tokens, and a calibrated confidence.

On an RTX 4090, Liquid reports about 8 ms per decision. The reserve uses the Q8_0 GGUF, which is 2.87 GB. The model is small enough to stay warm beside the writer and the embedder.

The architecture is `lfm2`. The decision variant is `lfm2-d1`. The llama.cpp build must support it. An older build will fail with an unknown architecture or will not expose `/v1/systemone`.

The reserve uses d1 for five decisions: relevance, sufficiency, action, groundedness, and confidence. The action question is a `choice` among keep, broaden, narrow, and decompose. The other four are `noul` questions. A `score` question is available for ordered rubrics.

The license is the LFM Open License. Check the model card before commercial use.

d1 is the referee, not the writer. If it is unsure, the loop delegates to LFM2.5 and records the delegation.
""",
    ),
    Doc(
        "rr-092",
        "Retrieval Metrics",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
Retrieval metrics answer one question: did the system find the passage that contains the answer?

Recall@k is the fraction of gold passages that appear in the top k. Precision@k is the fraction of the top k that are relevant. Hit@k is 1 if at least one gold passage is in the top k, and 0 otherwise. MRR is the mean of 1 divided by the rank of the first relevant result. nDCG@k rewards relevant results near the top and handles graded relevance.

RAG systems also use context precision and context recall. Context precision asks how much of the retrieved context is useful. Context recall asks how much of the needed context was retrieved. Both are usually judged by a model, so they inherit the judge's biases.

The reserve reports Recall@5, Recall@10, and Recall@20, plus MRR and nDCG@10. Recall is the primary metric because a missing passage cannot be fixed by a better prompt. Precision matters because a crowded context distracts the writer and costs tokens.

The RAPTOR report adds a level breakdown: how often a summary node beats a leaf, and whether the winning level matches the question type. A "what is this about" question should prefer a summary. A "what exactly happened" question should prefer a leaf.

The lab compares one-shot RAG, RAPTOR retrieval, and RAPTOR plus the refeed loop on the same 50 questions.
""",
    ),
    Doc(
        "rr-093",
        "Answer Metrics",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
Answer metrics answer a different question: is the final text correct and supported?

Faithfulness asks whether every claim in the answer is supported by the retrieved context. Groundedness is the same idea with a stricter focus on citations. Answer relevance asks whether the answer actually addresses the question. Correctness asks whether it matches the expected answer. Completeness asks whether it covers the important parts. Hallucination rate counts claims that are not supported by any source. Citation accuracy checks whether the cited node really contains the claim.

The reserve uses a judge model for the first pass and a human spot check for a sample. The judge is not trusted blindly. A model can prefer its own writing, favor the first answer it sees, or reward length. The lab records the judge, the prompt, and the order of the answers.

The answer must cite node ids. A claim without a citation is treated as unsupported. If the loop cannot find enough evidence, the correct answer is "I could not find enough evidence," not a confident guess.

The metrics page reports the answer score next to the token cost and the latency. A small gain that doubles the cost is not automatically a win.

The reserve's librarian uses the same rules. It answers from the retrieved records, names the documents, and says when the records are silent.
""",
    ),
    Doc(
        "rr-094",
        "Calibration Metrics",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
Calibration asks whether a model's confidence matches its accuracy. A model that says 80 percent should be right about 80 percent of the time.

The Brier score is the mean squared error of the probability forecasts. Lower is better. Expected calibration error, or ECE, bins the predictions and averages the gap between confidence and accuracy. A reliability diagram plots the two. The confidence distribution shows whether the model uses the whole range or always says 0.9.

Calibration matters because the loop uses confidence to decide when to delegate. If d1 says "not sufficient" with 0.95 confidence, the loop can rewrite without asking the writer. If it says 0.55, the loop should delegate or ask a human.

The reserve reports decision accuracy, Brier score, ECE, the confidence distribution, the delegation rate, and decision latency. The paper reports 41 to 74 percent lower ECE for decision models than for same-size generative models. The lab measures its own numbers on the 50-question eval set.

A model can be accurate and overconfident. That is the dangerous case, because the loop will trust a wrong judgment. The calibration dashboard is the first place to look when the refeed loop behaves strangely.

The delegation band is a configuration, not a law. The lab shows how the answer changes when the band moves.
""",
    ),
    Doc(
        "rr-095",
        "Librarian Guide",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
The reserve librarian answers questions about the corpus. It is not a general chatbot. It works best when the question names a document, a date, a place, a person, or a number.

Good questions are specific. "How many osprey chicks fledged in 2025?" is better than "Tell me about ospreys." "Which ranger approved the drone flight on 12 September 2026?" is better than "Who runs the drones?" "A drone flight is planned with a 35 km/h wind. May it proceed?" is better than "What is the drone policy?"

The librarian retrieves the top passages, judges their relevance, and checks whether the evidence is sufficient. If it is not, it rewrites the question and tries again, at most twice. It answers with citations to the node ids and the source documents.

The librarian will not answer from pretraining. If the corpus is silent, it says so. It will not guess a number, a date, or a name. It will not cite a document it did not read.

The trace shows every step: the retrieved nodes, the decision probabilities, the rewrite, the final answer, and the cost. A reader can open a node and check the claim.

The best way to test the librarian is to ask a question whose answer only exists in the fictional records. If it answers correctly, retrieval worked.
""",
    ),
    Doc(
        "rr-096",
        "Data Dictionary",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
The corpus uses five tables.

`documents` stores id, title, category, date, author, path, license, and word count. The id is the stable key. The path is relative to the place folder.

`chunks` stores id, doc_id, text, start, end, token count, and embedding. A chunk belongs to one document. The start and end are character offsets in the document text.

`nodes` stores id, level, parent_id, text, source_docs, and embedding. A node is a RAPTOR summary. Level 0 is a chunk. Level 1 and above are summaries. `source_docs` is a list of document ids.

`decisions` stores id, run_id, question_id, type, answer, probability, confidence, latency, and model. The type is `noul`, `choice`, or `score`.

`runs` stores id, question, config, iterations, prompt_tokens, completion_tokens, latency, answer, and stop_reason.

The eval file adds `id`, `question`, `type`, `gold_docs`, `expected`, and `notes`. Gold docs must exist in `documents`. The validate command checks this.

All ids are lowercase strings. Timestamps are ISO 8601 in UTC. Embeddings are float32 arrays stored as little-endian bytes. The manifest is the source of truth for the document list.

The dictionary is a contract between the corpus, the index, and the app. If a field changes, the builder, the loader, and the eval runner must change together. A field that is not in the dictionary is not part of the public API. The data manager reviews the dictionary before every corpus release.
""",
    ),
    Doc(
        "rr-097",
        "File Naming and Manifest",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
The corpus uses a simple naming scheme: `rr-###-slug.md`. The number is the document id. The slug is a lowercase, hyphenated version of the title. There are no spaces, no uppercase letters, and no special characters.

Each file starts with a level-one heading, then four metadata lines: Category, Date, Author, and Source. The body follows. The metadata is repeated in `manifest.json` so the loader does not have to parse Markdown.

The manifest lists every document with id, title, category, date, author, path, license, and word count. It also records the place id, the corpus version, and the generator. The manifest is generated; do not edit it by hand.

The place folder has `demo.toml`, `corpus/`, `script.jsonl`, and `eval.jsonl`. The script is the autoplay. The eval is the question set. The corpus is the documents and the manifest.

The validator checks the file name, the heading, the metadata, the manifest entry, the word count, and the gold document ids. A file that is not in the manifest is an error. A manifest entry with no file is an error.

The generator is `tools/build_corpus.py`. Run it from the place folder. The output is deterministic. Commit the generated files with the generator.
""",
    ),
    Doc(
        "rr-098",
        "Privacy and Sensitive Data",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
The public corpus contains no visitor names, phone numbers, email addresses, payment details, or home addresses. Staff names are fictional. The reserve's real visitor logs are not part of the corpus.

Nest locations are stored at reduced precision in public datasets. The internal database keeps the exact coordinates, but the public manifest and the corpus text do not. A map in a public document shows territories at 1 km resolution.

Visitor photos are used only with written permission. Camera trap images of people are deleted unless they are part of a safety incident. The retention period for visitor logs is two years. The retention period for incident reports is ten years.

Sensitive data is stored in a separate schema with access controls. The data manager reviews access every quarter. A researcher who needs exact nest coordinates signs a data-sharing agreement and a confidentiality agreement.

The corpus is public under CC BY 4.0. The archive originals are not part of the corpus. The archive has its own access rules (rr-084).

If you find personal information in the corpus, contact the data manager. The reserve will remove it and rebuild the index.
""",
    ),
    Doc(
        "rr-099",
        "Evaluation Question Bank",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
The eval set has 50 questions. Thirty are reserve-specific: the answer exists only in the fictional records. Ten are about the methods wing: RAPTOR, SearchJev, EmbeddingGemma 2, LFM2.5, d1-3B, and the metrics. Ten are multi-hop: they need two documents, such as a wind limit plus a flight plan.

Each question has an id, a question, a type, a list of gold documents, and a short expected answer. The type is `single` or `multi`. The gold documents are the minimum set a perfect retriever should find. The expected answer is a string, not a paragraph.

The validate command checks three things: every gold document exists, every question has a non-empty expected answer, and the question ids are unique. The eval runner reports Recall@k, MRR, nDCG, answer correctness, and the refeed count.

The bank is small enough to run on a laptop and large enough to catch a broken retriever. It is not a benchmark. A score on this set is a lab result, not a claim about the world.

The lab runs the same 50 questions through one-shot RAG, RAPTOR retrieval, and RAPTOR plus the refeed loop. The comparison is the point.
""",
    ),
    Doc(
        "rr-100",
        "Glossary",
        "Data and methods",
        "2026-06-01",
        W["data_manager"],
        f"""
RAG: Retrieval-Augmented Generation. Retrieve passages, put them in the prompt, generate an answer.

One-shot RAG: one retrieval, one answer, no critic and no retry.

Refeed loop: retrieve, judge, rewrite if needed, retrieve again, answer. The small loop in this project.

RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval. Chunk, embed, cluster, summarize, recurse, and retrieve from the tree.

Summary tree: the RAPTOR output. Leaves are chunks; higher levels are summaries.

Collapsed tree: search every level at once instead of walking down from the root.

Chunk: a fixed-size slice of a document, with a small overlap.

Embedding: a vector that represents the meaning of a text or an image.

Cosine similarity: the cosine of the angle between two vectors. Higher means more similar.

System 1: fast, cheap, automatic judgment. In this project, d1-3B.

System 2: slow, expensive reasoning and writing. In this project, LFM2.5-8B-A1B.

Decision model: a model trained to answer typed questions with probabilities, not to generate prose.

`noul`: a yes or no question. The answer is the probability of yes.

`choice`: a question with named options. The answer is the chosen option plus the distribution.

`score`: a rating on an ordered rubric. The answer is the expected level plus the distribution.

Calibration: whether confidence matches accuracy. ECE is the expected calibration error. Brier is the mean squared error of the forecasts.

Recall@k, Precision@k, MRR, nDCG@k: retrieval metrics.

Faithfulness, groundedness, answer relevance, correctness, completeness: answer metrics.

Span: one timed operation in a trace. Retrieval, decision, rewrite, and answer are spans.
""",
    ),
]
