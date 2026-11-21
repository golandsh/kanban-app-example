from pathlib import Path
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app


def _auth_client(tmp_path: Path, monkeypatch) -> TestClient:
    db_file = tmp_path / "nested" / "kanban.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    client = TestClient(app)
    res = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert res.status_code == 200
    return client


def test_init_db_creates_missing_database_and_seeds(tmp_path: Path) -> None:
    db_file = tmp_path / "new_dir" / "kanban.db"
    assert not db_file.exists()

    init_db(db_file)
    assert db_file.exists()


def test_board_requires_auth(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "kanban.db"))
    client = TestClient(app)

    assert client.get("/api/board").status_code == 401
    assert (
        client.put("/api/board", json={"columns": [], "cards": {}}).status_code == 401
    )


def test_get_board_returns_seeded_data(tmp_path: Path, monkeypatch) -> None:
    client = _auth_client(tmp_path, monkeypatch)

    response = client.get("/api/board")
    assert response.status_code == 200
    data = response.json()
    assert len(data["columns"]) == 5
    assert len(data["cards"]) == 8
    assert data["columns"][0]["title"] == "Backlog"


def test_put_board_persists_changes(tmp_path: Path, monkeypatch) -> None:
    client = _auth_client(tmp_path, monkeypatch)

    updated = {
        "columns": [
            {"id": "col-backlog", "title": "Inbox", "cardIds": ["card-1"]},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Updated card",
                "details": "Persisted in SQLite.",
            }
        },
    }

    put_res = client.put("/api/board", json=updated)
    assert put_res.status_code == 200
    assert put_res.json() == updated

    get_res = client.get("/api/board")
    assert get_res.status_code == 200
    assert get_res.json() == updated


def test_put_board_rejects_invalid_payload(tmp_path: Path, monkeypatch) -> None:
    client = _auth_client(tmp_path, monkeypatch)

    response = client.put("/api/board", json={"invalid": True})
    assert response.status_code == 422
