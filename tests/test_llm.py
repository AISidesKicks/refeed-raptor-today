import json

import httpx
import numpy as np

from rptr.llm import LlamaRouter, RouterError, choice, noul


def make_router(handler):
    return LlamaRouter(transport=httpx.MockTransport(handler))


def test_embed_returns_normalized_rows_in_order():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        payload = json.loads(request.content)
        data = [
            {"index": index, "embedding": [3.0, 4.0] if text == "a" else [1.0, 0.0]}
            for index, text in enumerate(payload["input"])
        ]
        return httpx.Response(200, json={"data": list(reversed(data))})

    router = make_router(handler)
    matrix = router.embed(["a", "b"])
    assert matrix.shape == (2, 2)
    assert np.allclose(matrix[0], [0.6, 0.8])
    assert np.allclose(matrix[1], [1.0, 0.0])


def test_systemone_parses_all_question_types():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "d1-3b"
        assert set(payload["questions"]) == {"yes", "pick", "level"}
        return httpx.Response(
            200,
            json={
                "answers": {
                    "yes": {"type": "noul", "noul": 0.83},
                    "pick": {
                        "type": "choice",
                        "choice": "hold",
                        "probabilities": {"fly": 0.1, "hold": 0.9},
                        "confidence": 0.8,
                    },
                    "level": {"type": "score", "score": 2.5},
                },
                "usage": {"input_tokens": 12},
            },
        )

    router = make_router(handler)
    decisions = router.systemone(
        "state",
        {
            "yes": noul("is it true?"),
            "pick": choice("what?", {"fly": None, "hold": None}),
            "level": {"type": "score", "instructions": "how?", "criteria": ["a", "b", "c", "d"]},
        },
    )
    assert decisions["yes"].value == 0.83
    assert decisions["pick"].value == "hold"
    assert decisions["pick"].confidence == 0.8
    assert decisions["level"].value == 2.5


def test_chat_and_unreachable_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": " ready "}}],
                "model": "lfm2-8b",
                "usage": {"prompt_tokens": 3, "completion_tokens": 1},
            },
        )

    router = make_router(handler)
    result = router.chat([{"role": "user", "content": "hi"}], max_tokens=4)
    assert result.text == "ready"
    assert result.completion_tokens == 1


def test_error_body_becomes_router_error():
    router = make_router(lambda request: httpx.Response(501, text="not a decision model"))
    try:
        router.systemone("state", {"q": noul("is it?")})
    except RouterError as exc:
        assert "501" in str(exc)
        assert "not a decision model" in str(exc)
    else:
        raise AssertionError("expected RouterError")
