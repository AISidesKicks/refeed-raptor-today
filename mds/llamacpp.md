# llama.cpp as the local router

Everything the lab does with a model goes through one llama.cpp server on `127.0.0.1:8080`. One process, three presets, one CUDA context. There is no cloud client anywhere in the code and no API key anywhere in the repo.

## The pinned image

```yaml
image: ghcr.io/ggml-org/llama.cpp:server-cuda13-b11804@sha256:dfe42bda81c6bd53df864dfcf65e2423e9703f9991c238cfa7aaa893063e2977
```

The tag is the v0.7.x line of llama.cpp, built on 22 October 2026. The digest is there so the pull is reproducible even if the tag moves.

Two version rules matter:

- EmbeddingGemma 2 needs a build from b11455 or newer, because it uses the `gemma-embedding2` architecture. An older build fails with `unknown model architecture`.
- d1-3B needs a build with `lfm2-d1` decision support, which means the `/v1/systemone` endpoint has to exist.

If one of them is missing, the failure looks like a broken model file. It is not. Check the build number first.

## The three presets

The presets live in `docker/presets.ini`. The section name is the model id that the app sends in the request body.

```ini
[embeddinggemma-2]
model = /models/embeddinggemma-2-Q8_0.gguf
embeddings = true
pooling = mean
ctx-size = 4096
n-gpu-layers = all

[lfm2-8b]
model = /models/LFM2.5-8B-A1B-Q4_K_M.gguf
ctx-size = 16384
temp = 0.2
n-gpu-layers = all

[d1-3b]
model = /models/d1-3B-Q8_0.gguf
ctx-size = 8192
cache-ram = 0
n-gpu-layers = all
```

Three details worth copying:

- `embeddings = true` and `pooling = mean`. The embedder has to run in embedding mode. A chat server that returns text for an embedding request is a broken setup.
- `cache-ram = 0` for d1-3B. Decision requests generate no tokens, so a prompt cache is pure waste.
- `parallel = 1` and `sleep-idle-seconds = -1`. One request at a time keeps the KV budget small, and the model does not fall asleep in the middle of a recorded turn.

The models are mounted read-only, so the router can never write into the model directory.

## The three endpoints

| Endpoint | Used by | Payload |
| --- | --- | --- |
| `POST /v1/embeddings` | EmbeddingGemma 2 | `input`, `model` |
| `POST /v1/chat/completions` | LFM2.5 | `messages`, `model`, `temperature`, `max_tokens` |
| `POST /v1/systemone` | d1-3B | `state`, `questions` |

The client is one file, `src/rptr/llm.py`. It is a typed wrapper, not a framework. It raises a `RouterError` with a readable message when the router is down, and it does not retry, because a retry that hides a broken stack is worse than a failure.

## Closing the reasoning block

LFM2.5 is a reasoning model. It always opens a `<think>` block, which is noise for a summary or a rewrite. The client closes it with a prefilled assistant turn:

```python
if skip_reasoning:
    payload_messages.append({"role": "assistant", "content": "</think>"})
```

After the generation, the same marker is stripped from the text. This is what makes the summaries reproducible.

## Health and models

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/v1/models
```

The app shows the same thing in its header: router status and the number of loaded models. The compose file has a healthcheck that polls `/health` every 30 seconds, with a 180 second start period because loading three models from disk is not instant.

## Downloading the weights

`docker/download-models.sh` fetches the three GGUF files, resumes partial downloads, and verifies the SHA-256 before it renames a file into place.

```bash
pixi run models        # download what is missing
pixi run models-check  # verify without downloading
```

The manifest in the script carries the size and the hash of each file, so a truncated download fails loudly instead of producing a broken model later.

## The trace collector

The compose file also defines `rptr-phoenix`, an Arize Phoenix container on ports 6006 and 4317, and there are pixi tasks to start and stop it. With `RPTR_OTLP_ENDPOINT` set, every run is exported to it as OpenTelemetry spans. See [OpenTelemetry and Phoenix](opentelemetry.md).

Read next: [the model stack](models.md), [the app](fastapi-app.md).
