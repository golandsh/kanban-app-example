# Kanban Studio

Single-board Kanban project management app with FastAPI, Next.js, SQLite, and OpenRouter AI.

## Running with Docker

Requires Docker Desktop (with `docker compose`) and a `.env` file in the project root containing `OPENROUTER_API_KEY`.

```bash
./scripts/start.sh              # Build and start at http://localhost:8000
./scripts/stop.sh               # Stop and remove containers
```

Useful Docker Compose commands:

```bash
docker compose ps               # Check container status
docker compose logs -f          # Tail container logs
docker compose up --build -d    # Rebuild and start in background
docker compose down             # Stop containers (keeps ./data volume)
```

SQLite data is persisted on the host in `./data` (mounted to `/app/data`).

## pyenv Cheat Sheet

| Command | Purpose |
| --- | --- |
| `pyenv versions` | List installed Python versions |
| `pyenv install --list` | List available Python versions to install |
| `pyenv install 3.15.2` | Install a specific Python version |
| `pyenv local 3.15.2` | Pin Python version for current directory (`.python-version`) |
| `pyenv global 3.15.2` | Set default Python version globally |
| `pyenv which python` | Show path to active Python executable |

### Local Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```
