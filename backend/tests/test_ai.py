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
