"""FastAPI server entry point.

Start with::

    cd api-server && uv run python -m serve
"""
from __future__ import annotations

import sys
from pathlib import Path

# ---- add parent project's src/ to sys.path before *any* project import ----
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# ---- stub out PySide6 / qfluentwidgets so they never need to be installed ----
from stubs import install_stubs
install_stubs()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from session import _sessions
from routes import router
from worker import init_wbi_keys, apply_cookies

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI):
    logger.info("Initialising WBI keys …")
    try:
        init_wbi_keys()
    except Exception:
        logger.warning("WBI key init failed (will retry on first request)")

    logger.info("Applying anonymous cookies …")
    try:
        apply_cookies()
    except Exception:
        logger.warning("Cookie init failed")

    yield

    _sessions.clear()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bili23 Downloader — URL Resolver",
    version="2.0.0",
    lifespan=_lifespan,
)

app.include_router(router)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start uvicorn (used by ``python -m serve`` and the ``bili23-server`` script)."""
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    uvicorn.run(
        "serve:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
