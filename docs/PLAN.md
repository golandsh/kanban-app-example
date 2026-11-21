# Project Implementation Plan

## Architecture Decisions

- **Server & Port**: FastAPI on port `8000`, serving the static Next.js build at `/` and API routes under `/api/*`.
- **Containerization**: `Dockerfile` + `docker-compose.yml` using `uv` for Python dependency management inside the container.
- **Local Python**: `pyenv` (Python `3.15.2`) with `.python-version` and a local `.venv` for running backend tests and tooling on the host.
- **Scripts**: Mac-only shell scripts (`scripts/start.sh`, `scripts/stop.sh`) wrapping Docker Compose.
- **Database**: SQLite stored in a mounted Docker volume (`./data` -> `/app/data/kanban.db`) so data persists across container restarts.
- **Authentication**: Hardcoded MVP credentials (`user` / `password`) using a simple HTTP-only session cookie managed by FastAPI.
- **AI**: OpenRouter API (`OPENROUTER_API_KEY` from `.env`) with `nvidia/nemotron-3-ultra-550b-a55b:free` and Structured Outputs.
- **Testing**: Target ~80% test coverage where sensible; focus on valuable tests and avoid unnecessary tests just to hit a coverage number.

---

## Part 1: Plan

- [x] Review `AGENTS.md` and `docs/PLAN.md`
- [x] Inspect existing `frontend/` codebase
- [x] Create `frontend/AGENTS.md` documenting existing frontend structure, components, state, and tests
- [x] Enrich `docs/PLAN.md` with detailed checklists, tests, and success criteria for Parts 1-10
- [x] Obtain user review and approval of the plan

**Tests & Verification**:
- Verify `docs/PLAN.md` and `frontend/AGENTS.md` accurately reflect repo state and all user requirements.

**Success Criteria**:
- User explicitly approves the plan before Part 2 begins.

---

## Part 2: Scaffolding

- [x] Configure local Python via `pyenv` (`3.15.2` in `.python-version`) and create a local `.venv` in `backend/` for running `pytest` on the host
- [x] Initialize Python project in `backend/` with `pyproject.toml` (FastAPI, `uvicorn`, `httpx`, `pytest`) managed via `uv` in Docker
- [x] Create `backend/app/main.py` with `/health`, `/api/hello`, and static file serving from a static directory (with a temporary `hello world` HTML page that calls `/health`)
- [x] Create `Dockerfile` (multi-stage or Node + Python `uv` setup) and `docker-compose.yml` exposing port `8000`, loading `.env`, and mounting `./data:/app/data`
- [x] Create Mac-only `scripts/start.sh` (`docker compose up --build -d`) and `scripts/stop.sh` (`docker compose down`) with executable permissions

**Tests & Verification**:
- `pytest` unit test for `/api/health` returning `200` and `{"status": "ok"}`.
- Run `./scripts/start.sh`, verify `http://localhost:8000/` serves the hello world page and its `/api/health` fetch succeeds, then run `./scripts/stop.sh`.

**Success Criteria**:
- Container builds cleanly with `uv`, starts/stops via `scripts/`, serves static HTML at `/`, and responds to `/api/health` on port `8000`.

---

## Part 3: Add in Frontend

- [x] Configure `frontend/next.config.ts` with `output: "export"` for static HTML/JS/CSS export (`frontend/out/`)
- [x] Update `Dockerfile` to build `frontend/` (`npm ci && npm run build`) and copy `frontend/out/` into the backend static directory served by FastAPI at `/`
- [x] Verify SPA/static asset routing in FastAPI so `/`, `/_next/*`, and `favicon.ico` resolve cleanly

**Tests & Verification**:
- Frontend unit/integration tests: `npm run test:unit` in `frontend/` passes.
- Docker integration check: start container via `scripts/start.sh`, verify `http://localhost:8000/` serves the built Kanban HTML and `/_next/*` assets, and `/health` and `/api/hello` respond `200`.

**Success Criteria**:
- Full demo Kanban board is served statically by FastAPI at `http://localhost:8000/` inside Docker, with all unit and E2E tests passing.

---

## Part 4: Add in a Fake User Sign-In Experience

- [x] Add backend auth routes in FastAPI:
  - `POST /api/auth/login` (validates `username == "user"` and `password == "password"`, sets HTTP-only session cookie)
  - `POST /api/auth/logout` (clears session cookie)
  - `GET /api/auth/me` (returns current user or `401`)
- [x] Add frontend login gate and sign-out UI:
  - Check `/api/auth/me` on load; show clean login form matching the color scheme (`#032147`, `#209dd7`, `#753991`, `#ecad0a`) when unauthenticated
  - Render `<KanbanBoard />` with a Sign Out button in the header when authenticated
- [x] Add backend unit tests for login (valid/invalid credentials), `/api/auth/me`, and logout
- [x] Add frontend unit/integration tests covering unauthenticated gate, login with `user`/`password`, invalid login error, and logout

**Tests & Verification**:
- `pytest` passes all auth endpoint tests.
- `npm run test:unit` verifies login -> board -> logout flow.

**Success Criteria**:
- Hitting `/` while signed out shows the login screen; signing in with `user` / `password` shows the Kanban board; signing out returns to the login screen.

---

## Part 5: Database Modeling

- [x] Design SQLite schema supporting multiple users (for future) and 1 Kanban board per user stored as JSON (e.g., `users` table and `boards` table with `user_id`, `board_json`, `updated_at`)
- [x] Document the schema, JSON structure, initialization behavior, and migration/creation strategy in `docs/DATABASE.md`
- [x] Obtain user sign-off on `docs/DATABASE.md` before writing Part 6

**Tests & Verification**:
- Review `docs/DATABASE.md` against all business requirements (multi-user ready, 1 board per user, fixed columns that can be renamed, cards with title/details, SQLite local DB).

**Success Criteria**:
- User approves `docs/DATABASE.md`.

---

## Part 6: Backend

- [x] Implement SQLite database module in `backend/app/db.py` (auto-creates `/app/data/kanban.db` and tables + seeds default `user` and initial board JSON if missing)
- [x] Protect board API routes with the session cookie dependency (`401` if unauthenticated)
- [x] Implement board API routes:
  - `GET /api/board` (returns the authenticated user's Kanban board JSON)
  - `PUT /api/board` (validates and persists the updated Kanban board JSON)
- [x] Write comprehensive `pytest` unit/integration tests using a temporary SQLite DB covering DB auto-creation, initial seed data, `GET /api/board`, `PUT /api/board`, validation errors, and `401` when unauthenticated

**Tests & Verification**:
- `pytest` passes all DB and board API tests with clean isolation.

**Success Criteria**:
- Backend creates the SQLite DB automatically if missing, persists board reads/writes per user, and passes all unit tests.

---

## Part 7: Frontend + Backend

- [ ] Update `KanbanBoard.tsx` to load board state from `GET /api/board` on mount (with loading/error states)
- [ ] Persist all board mutations (`PUT /api/board`): drag-and-drop move, column rename, add card, edit card, delete card
- [ ] Add card editing UI in `KanbanCard.tsx` (edit title and details inline or via compact edit mode) per business requirements
- [ ] Update frontend unit/integration tests (mocking `/api/board`) to verify loading, renaming, adding, editing, moving, and deleting cards

**Tests & Verification**:
- `npm run test:unit` and `pytest` pass.
- Verify persistence across container restart (`scripts/stop.sh` + `scripts/start.sh`) via `./data` SQLite volume.

**Success Criteria**:
- Kanban board is fully persistent end-to-end across reloads and container restarts, including card editing.

---

## Part 8: AI Connectivity

- [ ] Add OpenRouter client helper in `backend/app/ai.py` using `OPENROUTER_API_KEY` from `.env` and model `nvidia/nemotron-3-ultra-550b-a55b:free`
- [ ] Add a minimal connectivity test endpoint or CLI/pytest check (e.g., `POST /api/ai/ping` or `pytest` integration test) sending `"What is 2+2?"`
- [ ] Verify `.env` is passed into the Docker container via `docker-compose.yml`

**Tests & Verification**:
- Automated unit test with mocked OpenRouter HTTP response.
- Live connectivity check against OpenRouter confirming `"2+2"` returns `"4"` inside the Docker environment.

**Success Criteria**:
- Backend successfully calls OpenRouter using `OPENROUTER_API_KEY` and receives a valid response.

---

## Part 9: Backend AI + Structured Outputs

- [ ] Define Pydantic schemas for AI chat request (`message`, `history`) and Structured Output response (`reply: str`, `board_update: BoardData | None`)
- [ ] Implement `POST /api/ai/chat` (auth-protected):
  - Loads the user's current board JSON from SQLite
  - Sends system prompt + current board JSON + conversation history + user message to OpenRouter requesting Structured Outputs
  - Parses and validates the structured response; if `board_update` is present, validates it and persists it to SQLite
  - Returns `{ reply, board }` (or `{ reply, updated, board }`) to the caller
- [ ] Write thorough `pytest` tests covering:
  - Chat-only response (`board_update: null`, DB unchanged)
  - Board mutation response (create/edit/move cards, DB updated)
  - Invalid/malformed LLM output handling and `401` when unauthenticated

**Tests & Verification**:
- `pytest` passes all `/api/ai/chat` unit tests (mocked OpenRouter) and a live smoke test verifying structured output parsing and board update.

**Success Criteria**:
- `/api/ai/chat` reliably returns structured responses and persists AI-driven Kanban updates to SQLite.

---

## Part 10: AI Chat Sidebar UI

- [ ] Build a clean, collapsible/docked AI Chat Sidebar component matching the app color palette (`#032147`, `#209dd7`, `#753991`, `#ecad0a`)
- [ ] Maintain conversation history in the sidebar, send messages to `POST /api/ai/chat`, and show loading/error states
- [ ] Automatically refresh `KanbanBoard` state whenever the AI response includes an updated board
- [ ] Add frontend unit/integration tests for the chat sidebar (sending messages, rendering replies, triggering board refresh on `board_update`)

**Tests & Verification**:
- `npm run test:unit` and `pytest` all pass.
- Verify in Docker on `http://localhost:8000/`.

**Success Criteria**:
- Users can chat with the AI in the sidebar, the AI can create/edit/move cards, and the Kanban board refreshes automatically and persists changes.
