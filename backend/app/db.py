import os
import sqlite3
from pathlib import Path

from app.schemas import BoardData

DEFAULT_DB_PATH = "/app/data/kanban.db"

DEFAULT_BOARD = BoardData.model_validate(
    {
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
            {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
            {
                "id": "col-progress",
                "title": "In Progress",
                "cardIds": ["card-4", "card-5"],
            },
            {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
            {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Align roadmap themes",
                "details": "Draft quarterly themes with impact statements and metrics.",
            },
            "card-2": {
                "id": "card-2",
                "title": "Gather customer signals",
                "details": "Review support tags, sales notes, and churn feedback.",
            },
            "card-3": {
                "id": "card-3",
                "title": "Prototype analytics view",
                "details": "Sketch initial dashboard layout and key drill-downs.",
            },
            "card-4": {
                "id": "card-4",
                "title": "Refine status language",
                "details": "Standardize column labels and tone across the board.",
            },
            "card-5": {
                "id": "card-5",
                "title": "Design card layout",
                "details": "Add hierarchy and spacing for scanning dense lists.",
            },
            "card-6": {
                "id": "card-6",
                "title": "QA micro-interactions",
                "details": "Verify hover, focus, and loading states.",
            },
            "card-7": {
                "id": "card-7",
                "title": "Ship marketing page",
                "details": "Final copy approved and asset pack delivered.",
            },
            "card-8": {
                "id": "card-8",
                "title": "Close onboarding sprint",
                "details": "Document release notes and share internally.",
            },
        },
    }
)


def get_db_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    path = db_path or get_db_path()
    with _connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                board_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)",
            ("user",),
        )
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("user",),
        ).fetchone()
        if row is not None:
            conn.execute(
                "INSERT OR IGNORE INTO boards (user_id, board_json) VALUES (?, ?)",
                (row["id"], DEFAULT_BOARD.model_dump_json()),
            )


def get_board(username: str, db_path: Path | None = None) -> BoardData:
    path = db_path or get_db_path()
    init_db(path)
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)",
            (username,),
        )
        user_row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        assert user_row is not None
        board_row = conn.execute(
            "SELECT board_json FROM boards WHERE user_id = ?",
            (user_row["id"],),
        ).fetchone()
        if board_row is None:
            default_json = DEFAULT_BOARD.model_dump_json()
            conn.execute(
                "INSERT INTO boards (user_id, board_json) VALUES (?, ?)",
                (user_row["id"], default_json),
            )
            return DEFAULT_BOARD
        return BoardData.model_validate_json(board_row["board_json"])


def save_board(
    username: str, board: BoardData, db_path: Path | None = None
) -> BoardData:
    path = db_path or get_db_path()
    init_db(path)
    board_json = board.model_dump_json()
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)",
            (username,),
        )
        user_row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        assert user_row is not None
        conn.execute(
            """
            INSERT INTO boards (user_id, board_json, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                board_json = excluded.board_json,
                updated_at = datetime('now')
            """,
            (user_row["id"], board_json),
        )
    return board
