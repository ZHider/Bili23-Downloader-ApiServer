# Bili23 Downloader — API Server

> **[中文版本](README-zh.md)**

Expose [Bili23-Downloader](https://github.com/ScottSloan/Bili23-Downloader)'s download-URL resolution as a REST API — no GUI, no browser, no PySide6.

```bash
git clone https://github.com/ZHider/Bili23-Downloader-ApiServer.git
cd Bili23-Downloader-ApiServer
git submodule update --init   # pull the embedded Bili23-Downloader source
uv sync                       # install deps from lockfile (~20 packages, no Qt)
uv run python -m serve        # start server on http://127.0.0.1:8000
```

## Requirements

- Python 3.10.x
- `uv` (recommended package manager, [install](https://docs.astral.sh/uv/#installation)) or `pip`

## Quick Start

```bash
git clone https://github.com/ZHider/Bili23-Downloader-ApiServer.git
cd Bili23-Downloader-ApiServer
git submodule update --init
uv sync
uv run python -m serve
```

Or using plain pip:

```bash
pip install -r requirements.txt
python -m serve
```

The server is also registered as a CLI script — after install:

```bash
bili23-server
# or
python -m bili23_server
```

## API

All endpoints are documented interactively at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI).

| Endpoint | Description |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/info?bvid=xxx` | Video metadata (title, cid, owner, pages, duration) |
| `GET /api/download?bvid=xxx` | Download URLs for all P-sections (auto-resolve cid) |
| `GET /api/parse?bvid=xxx&cid=xxx` | Download URLs for a specific episode |
| `POST /api/cookies` | Inject Bilibili login cookies, returns `session_id` |

### Examples

```bash
# Get video info
curl -s "http://127.0.0.1:8000/api/info?bvid=BV1E3411C7HM"

# Get download URLs (auto-resolve cid)
curl -s "http://127.0.0.1:8000/api/download?bvid=BV1E3411C7HM"

# Get download URLs for a specific episode
curl -s "http://127.0.0.1:8000/api/parse?bvid=BV1E3411C7HM&cid=423747920"
```

### Login (optional)

```bash
# Create a session with your Bilibili cookies
SID=$(curl -s -X POST http://127.0.0.1:8000/api/cookies \
  -d "SESSDATA=abc&bili_jct=def&DedeUserID=123")

# Use the session for age-restricted content
curl -s "http://127.0.0.1:8000/api/download?bvid=BVxxx&session_id=$SID"
```

Sessions expire after 10 minutes.

## Architecture

```
┌─────────────┐   import      ┌──────────────┐
│  serve.py   │──────────────▶│  worker.py   │
│  __main__.py│               │  (wrapper)   │
│  (entry)    │               └──────┬───────┘
└──────┬──────┘                      │
       │                             │ from util.*
       │ routes.py                   ▼
       │ session.py          ┌──────────────────────┐
       │ pyproject.toml      │ Bili23-Downloader    │
       │ uv.lock             │ (git submodule)      │
       │ requirements.txt    │ src/                 │
       │                     └──────────────────────┘
       ▼
┌──────────────┐   intercepts
│  stubs/      │── PySide6 / qfluentwidgets
│  (import     │   at import time
│   hooks)     │
└──────────────┘
```

**Reuses the parent project's code directly** — the server does not duplicate or rewrite any download logic. It wraps `VideoInfoParser`, `AudioInfoParser`, `QueryWorker`, `SyncNetWorkRequest`, and `ParserBase` from the original codebase (pulled as a [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules)).

**No GUI dependencies** — PySide6 and qfluentwidgets are stubbed at import time via `sys.modules` hooks. The server only depends on `httpx`, `fastapi`, `uvicorn`, and `psutil` (~20 packages including transitive deps, no Qt components).

**Reproducible installs** — `uv.lock` is committed to the repo. `uv sync` always resolves the exact same dependency tree. For pip users, `requirements.txt` is kept in sync via `uv export --frozen --no-dev`.

## Development

```bash
uv sync --group dev  # includes flake8, autopep8
uv run flake8        # lint check
uv run autopep8 --aggressive --in-place *.py stubs/*.py

# keep requirements.txt in sync after changing dependencies
uv export --frozen --no-dev --output-file requirements.txt
```

## License

GPL-3.0 — same as the parent [Bili23-Downloader](https://github.com/ScottSloan/Bili23-Downloader).
