import json
from pathlib import Path
from fastapi.testclient import TestClient
import httpx

from app.main import app


def _login(client: TestClient) -> None:
    res = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert res.status_code == 200


def test_ai_ping_requires_auth() -> None:
    client = TestClient(app)
    assert client.post("/api/ai/ping").status_code == 401


def test_ai_ping_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = TestClient(app)
    _login(client)

    res = client.post("/api/ai/ping")
    assert res.status_code == 500


def test_ai_ping_success(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(url: str, json: dict, headers: dict, timeout: float):
        assert "openrouter.ai" in url
        assert headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "model": json["model"],
                "choices": [{"message": {"content": "4"}}],
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = TestClient(app)
    _login(client)

    res = client.post("/api/ai/ping")
    assert res.status_code == 200
    assert res.json()["reply"] == "4"


def test_ai_chat_requires_auth(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "kanban.db"))
    client = TestClient(app)
    res = client.post("/api/ai/chat", json={"message": "Hello"})
    assert res.status_code == 401


def test_ai_chat_only_leaves_board_unchanged(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "kanban.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(_url: str, json: dict, headers: dict, timeout: float):
        assert json["response_format"]["type"] == "json_schema"
        assert any(m["role"] == "system" and "col-backlog" in m["content"] for m in json["messages"])
        return httpx.Response(
            200,
            json={
                "model": json["model"],
                "choices": [
                    {
                        "message": {
                            "content": '{"reply": "You have 8 cards.", "board_update": null}'
                        }
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = TestClient(app)
    _login(client)

    res = client.post(
        "/api/ai/chat",
        json={
            "message": "How many cards do I have?",
            "history": [{"role": "user", "content": "Hi"}],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["reply"] == "You have 8 cards."
    assert body["updated"] is False
    assert len(body["board"]["cards"]) == 8


def test_ai_chat_updates_and_persists_board(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "kanban.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    client = TestClient(app)
    _login(client)

    initial_board = client.get("/api/board").json()
    updated_board = {
        **initial_board,
        "cards": {
            **initial_board["cards"],
            "card-ai-1": {
                "id": "card-ai-1",
                "title": "AI Created Task",
                "details": "Added via chat",
            },
        },
        "columns": [
            {
                **initial_board["columns"][0],
                "cardIds": [*initial_board["columns"][0]["cardIds"], "card-ai-1"],
            },
            *initial_board["columns"][1:],
        ],
    }

    structured = json.dumps(
        {
            "reply": "Added 'AI Created Task' to Backlog.",
            "board_update": updated_board,
        }
    )

    def fake_post(_url: str, json: dict, headers: dict, timeout: float):
        return httpx.Response(
            200,
            json={
                "model": json["model"],
                "choices": [{"message": {"content": structured}}],
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    res = client.post("/api/ai/chat", json={"message": "Add a task to Backlog"})
    assert res.status_code == 200
    body = res.json()
    assert body["updated"] is True
    assert "card-ai-1" in body["board"]["cards"]

    persisted = client.get("/api/board").json()
    assert "card-ai-1" in persisted["cards"]


def test_ai_chat_invalid_structured_output_returns_502(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "kanban.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(_url: str, json: dict, headers: dict, timeout: float):
        return httpx.Response(
            200,
            json={
                "model": json["model"],
                "choices": [{"message": {"content": "not valid json"}}],
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = TestClient(app)
    _login(client)

    res = client.post("/api/ai/chat", json={"message": "Hello"})
    assert res.status_code == 502
