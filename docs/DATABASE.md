# Database Design

## Overview

- **Engine**: SQLite (local file via Python `sqlite3`, no ORM).
- **Location**: `/app/data/kanban.db` inside Docker (persisted on host at `./data/kanban.db`), configurable via `DATABASE_PATH` environment variable for testing.
- **Multi-user & Single-board**: Supports multiple users in `users`, with a 1-to-1 relationship (`UNIQUE(user_id)`) in `boards` so each user has one Kanban board stored as JSON.

## Schema

```sql
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
```

### Design Notes

- `users.username` is `UNIQUE` for fast lookup from the authenticated session (`username`).
- `boards.user_id` has a `UNIQUE` constraint + `FOREIGN KEY` to `users(id)`, enforcing 1 board per user for the MVP while remaining multi-user ready.
- `boards.board_json` stores the serialized `BoardData` JSON matching `frontend/src/lib/kanban.ts`.

## Board JSON Structure

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"] },
    { "id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"] },
    { "id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"] },
    { "id": "col-review", "title": "Review", "cardIds": ["card-6"] },
    { "id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

- **Columns**: Fixed 5 columns; titles can be renamed; `cardIds` preserves card order.
- **Cards**: Keyed by `id`, each containing `id`, `title`, and `details`.

## Initialization & Auto-Creation

1. On startup (or first DB access), ensure parent directory exists (`Path(db_path).parent.mkdir(parents=True, exist_ok=True)`).
2. Connect to SQLite with `PRAGMA foreign_keys = ON`.
3. Execute `CREATE TABLE IF NOT EXISTS` for `users` and `boards`.
4. Seed default MVP user (`username = "user"`) if not present, and seed their default `boards` row with `initialData` JSON if they do not yet have a board.
5. Future schema changes can be handled cleanly with `ALTER TABLE` or additive migrations as needed.
