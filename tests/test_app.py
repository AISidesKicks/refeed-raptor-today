from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from rptr.app import create_app
from rptr.config import Settings

PLACE = Path(__file__).resolve().parents[1] / "lab" / "demos" / "raptor-reserve"


def make_client(tmp_path):
    settings = replace(
        Settings.from_env(),
        data_dir=tmp_path,
        database_path=tmp_path / "app.sqlite3",
    )
    return TestClient(create_app(settings))


def test_places_and_detail(tmp_path):
    with make_client(tmp_path) as client:
        places = client.get("/api/places")
        assert places.status_code == 200
        payload = places.json()
        assert len(payload) == 1
        assert payload[0]["id"] == "raptor-reserve"

        detail = client.get("/api/places/raptor-reserve")
        assert detail.status_code == 200
        body = detail.json()
        assert body["documents"] == 100
        assert len(body["starter_questions"]) == 5
        assert len(body["script"]) == 6
        assert body["capabilities"]["recorded"] is True


def test_ask_and_websocket(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/ask",
            json={
                "place_id": "raptor-reserve",
                "question": "How many osprey chicks fledged in 2025?",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == "keyword"
        assert body["results"]
        assert any(hit["doc_id"] == "rr-012" for hit in body["results"])

        with client.websocket_connect("/ws/ask") as websocket:
            websocket.send_json(
                {
                    "place_id": "raptor-reserve",
                    "question": "How many osprey chicks fledged in 2025?",
                }
            )
            message = websocket.receive_json()
            assert message["mode"] == "keyword"
            assert message["results"]


def test_replay_corpus_and_eval(tmp_path):
    with make_client(tmp_path) as client:
        replay = client.get("/api/places/raptor-reserve/replay/1")
        assert replay.status_code == 200
        turn = replay.json()
        assert "osprey" in turn["visitor"].lower()
        assert turn["hits"]

        recorded = client.get("/api/places/raptor-reserve/replay/1?mode=recorded")
        assert recorded.status_code == 200
        recording = recorded.json()
        assert recording["place_id"] == "raptor-reserve"
        assert recording["turn"] == 1
        assert "21" in recording["result"]["answer"]
        assert recording["result"]["citations"]

        missing = client.get("/api/places/raptor-reserve/replay/9?mode=recorded")
        assert missing.status_code == 404

        docs = client.get("/api/places/raptor-reserve/documents")
        assert docs.status_code == 200
        assert len(docs.json()) == 100

        charter = client.get("/api/places/raptor-reserve/documents/rr-001")
        assert charter.status_code == 200
        assert charter.json()["title"] == "Reserve Charter"

        evaluation = client.get("/api/places/raptor-reserve/eval/keyword")
        assert evaluation.status_code == 200
        summary = evaluation.json()
        assert summary["questions"] == 50
        assert 0.0 <= summary["recall_at_10"] <= 1.0
        assert 0.0 <= summary["mrr"] <= 1.0


def test_landing_page(tmp_path):
    with make_client(tmp_path) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Local RAG reader" in response.text
