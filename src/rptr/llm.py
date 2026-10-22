"""Client for the local llama.cpp router.

One process serves three presets: the embedder, the writer, and the decision
model. The router picks the preset from the `model` field, so this module is a
thin typed wrapper around three endpoints:

- `POST /v1/embeddings` for EmbeddingGemma 2
- `POST /v1/chat/completions` for LFM2.5
- `POST /v1/systemone` for d1-3B

No cloud client, no API key, no retries that hide a broken stack. If the router
is down, the error says how to start it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Self

import httpx
import numpy as np

from .text import plain_hyphens

DEFAULT_BASE_URL = "http://127.0.0.1:8080"


class RouterError(RuntimeError):
    """The local router returned an error or could not be reached."""


@dataclass(frozen=True)
class Decision:
    """One typed answer from the decision model."""

    kind: str
    value: Any
    probabilities: dict[str, float] = field(default_factory=dict)
    confidence: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "probabilities": dict(self.probabilities),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ChatResult:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


def noul(instructions: str, true_label: str = "yes", false_label: str = "no") -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true_label, "false": false_label},
    }


def choice(instructions: str, options: dict[str, str | None]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": options}


class LlamaRouter:
    """Synchronous client for one llama.cpp router."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 600.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
            headers={"Content-Type": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise RouterError(
                f"cannot reach the local llama.cpp router at {self.base_url}. "
                "Start it with `pixi run llm-up` and check `pixi run llm-logs`."
            ) from exc
        if response.status_code >= 400:
            detail = response.text.strip()
            raise RouterError(f"{method} {path} returned {response.status_code}: {detail}")
        try:
            return response.json()
        except ValueError as exc:
            raise RouterError(f"{method} {path} returned invalid JSON") from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def models(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/v1/models")
        return list(payload.get("data", []))

    def wait_until_ready(self, timeout: float = 240.0, interval: float = 2.0) -> None:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                if self.health().get("status") == "ok":
                    return
            except RouterError as exc:
                last_error = exc
            time.sleep(interval)
        raise RouterError(f"router did not become ready within {timeout:.0f}s: {last_error}")

    def embed(
        self,
        texts: list[str],
        model: str = "embeddinggemma-2",
        batch_size: int = 16,
    ) -> np.ndarray:
        """Return one L2-normalized row per text, in input order."""

        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        rows: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            payload = self._request(
                "POST",
                "/v1/embeddings",
                json={"model": model, "input": batch},
            )
            data = payload.get("data")
            if not isinstance(data, list) or len(data) != len(batch):
                raise RouterError("embedding response did not match the input batch")
            ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
            rows.extend(list(item["embedding"]) for item in ordered)
        matrix = np.asarray(rows, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        return matrix / np.maximum(norms, 1e-12)

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "lfm2-8b",
        max_tokens: int = 768,
        temperature: float = 0.2,
        top_p: float = 0.9,
        extra: dict[str, Any] | None = None,
        skip_reasoning: bool = False,
    ) -> ChatResult:
        payload_messages = list(messages)
        if skip_reasoning:
            # LFM2.5 always opens a think block. Prefilling a closed block moves
            # generation straight to the answer and keeps summaries deterministic.
            payload_messages.append({"role": "assistant", "content": "</think>"})
        payload: dict[str, Any] = {
            "model": model,
            "messages": payload_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }
        if extra:
            payload.update(extra)
        started = time.monotonic()
        response = self._request("POST", "/v1/chat/completions", json=payload)
        latency_ms = int((time.monotonic() - started) * 1000)
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RouterError("chat response had no choices")
        message = choices[0].get("message", {})
        text = str(message.get("content") or "").strip()
        if skip_reasoning and text.startswith("</think>"):
            text = text[len("</think>") :].strip()
        text = plain_hyphens(text)
        usage = response.get("usage") or {}
        return ChatResult(
            text=text,
            model=str(response.get("model", model)),
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
        )

    def systemone(
        self,
        state: str,
        questions: dict[str, dict[str, Any]],
        model: str = "d1-3b",
    ) -> dict[str, Decision]:
        if not questions:
            return {}
        payload = {"model": model, "state": state, "questions": questions}
        started = time.monotonic()
        response = self._request("POST", "/v1/systemone", json=payload)
        latency_ms = int((time.monotonic() - started) * 1000)
        answers = response.get("answers")
        if not isinstance(answers, dict):
            raise RouterError("systemone response had no answers")
        decisions: dict[str, Decision] = {}
        for key, answer in answers.items():
            if not isinstance(answer, dict):
                continue
            kind = str(answer.get("type", questions.get(key, {}).get("type", "")))
            probabilities = {
                str(name): float(value)
                for name, value in (answer.get("probabilities") or {}).items()
            }
            confidence = answer.get("confidence")
            if kind == "noul":
                value: Any = float(answer.get("noul", 0.0))
            elif kind == "choice":
                value = str(answer.get("choice", ""))
            elif kind == "score":
                value = float(answer.get("score", 0.0))
            else:
                value = answer
            decisions[key] = Decision(
                kind=kind,
                value=value,
                probabilities=probabilities,
                confidence=float(confidence) if confidence is not None else None,
                raw={
                    "latency_ms": latency_ms,
                    "input_tokens": int((response.get("usage") or {}).get("input_tokens") or 0),
                },
            )
        return decisions
