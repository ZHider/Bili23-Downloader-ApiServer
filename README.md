# Bili23 Downloader — API Server

> **[中文版本](README-zh.md)**

Expose [Bili23-Downloader](https://github.com/ScottSloan/Bili23-Downloader)'s download-URL resolution as a REST API — no GUI, no browser, no PySide6.


```bash
cd api-server && uv sync && uv run python -m serve
# → http://127.0.0.1:8000
```

## Requirements

- Python 3.10.x
- `uv` (package manager, [install](https://docs.astral.sh/uv/#installation))

## Quick Start

```bash
git clone https://github.com/ScottSloan/Bili23-Downloader.git
cd Bili23-Downloader/api-server
uv sync                # install dependencies (~20 packages, no Qt)
uv run python -m serve # start server on http://127.0.0.1:8000
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
┌─────────────┐   imports     ┌──────────────┐
│  serve.py   │──────────────▶│  worker.py   │
│  (entry)    │               │  (wrapper)   │
└──────┬──────┘               └──────┬───────┘
       │                            │
       │ routes.py                  │ from util.*
       │ session.py                 ▼
       │                     ┌──────────────┐
       │                     │ Bili23-      │
       │                     │ Downloader   │
       │                     │ src/         │
       │                     └──────────────┘
       │
       ▼
┌──────────────┐   intercepts
│  stubs/      │── PySide6 / qfluentwidgets
│  (import     │   at import time
│   hooks)     │
└──────────────┘
```

**Reuses the parent project's code directly** — the server does not duplicate or rewrite any download logic. It wraps `VideoInfoParser`, `AudioInfoParser`, `QueryWorker`, `SyncNetWorkRequest`, and `ParserBase` from the original codebase.

**No GUI dependencies** — PySide6 and qfluentwidgets are stubbed at import time via `sys.modules` hooks. The server only depends on `httpx`, `fastapi`, `uvicorn`, and `psutil` (~20 packages total).

## Development

```bash
uv sync --group dev  # includes flake8, autopep8
uv run flake8        # lint check
uv run autopep8 --aggressive --in-place *.py stubs/*.py
```

## License

GPL-3.0 — same as the parent [Bili23-Downloader](https://github.com/ScottSloan/Bili23-Downloader).
