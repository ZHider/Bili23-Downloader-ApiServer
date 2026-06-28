"""FastAPI route definitions for the Bili23 download-URL resolver.

All endpoint functions are decorated on a module-level ``APIRouter``
and registered in ``serve.py`` via ``app.include_router(router)``.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from session import use_session, clean_expired_sessions, create_session
from worker import resolve_download_url, get_video_meta
from util.parse.episode.tree import Attribute
from util.common.enum import DownloadType

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/api/health")
async def health():
    """Simple liveness check."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------

@router.get("/api/info")
async def info(
    bvid: str = Query(..., description="BV-id, e.g. BV1GJ411m7dN"),
    session_id: str | None = Query(None, description="Session id from POST /api/cookies"),
):
    """Fetch video metadata (title, cid, pages, owner, duration, pic, etc.)."""
    use_session(session_id)

    try:
        data = get_video_meta(bvid)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.exception("Unhandled error fetching info for %s", bvid)
        raise HTTPException(status_code=500, detail=str(exc))

    return data


# ---------------------------------------------------------------------------
# Download (by BV only, auto-resolve cid)
# ---------------------------------------------------------------------------

@router.get("/api/download")
async def download(
    bvid: str = Query(..., description="BV-id, e.g. BV1GJ411m7dN"),
    session_id: str | None = Query(None, description="Session id from POST /api/cookies"),
    video_quality_id: int = Query(
        200,
        description="Desired video quality id "
        "(200=auto, 127=8K, 126=DOLBY, 120=4K, 116=1080P60, 80=1080P, 64=720P, 32=480P, 16=360P)",
    ),
    video_codec_id: int = Query(
        20,
        description="Desired video codec id (20=auto, 12=avc/h264, 13=hevc/h265, 14=av1)",
    ),
    audio_quality_id: int = Query(
        30300,
        description="Desired audio quality id "
        "(30300=auto, 30251=FLAC, 30250=Dolby, 30280=Hi-Res, 30232=192k, 30216=132k, 30200=64k)",
    ),
):
    """Download by BV only — auto-resolve cid internally.

    For multi-P videos returns ``pages[]`` with per-part download info.
    """
    use_session(session_id)

    try:
        meta = get_video_meta(bvid)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.exception("Unhandled error fetching info for %s", bvid)
        raise HTTPException(status_code=500, detail=str(exc))

    pages = meta.get("pages") or [{"cid": meta["cid"], "part": meta.get("title", "")}]
    attr = Attribute.VIDEO_BIT

    resolved_pages = []
    for p in pages:
        cid = p["cid"]
        try:
            result = resolve_download_url(
                bvid=bvid, cid=cid,
                attribute=attr,
                download_type=DownloadType.VIDEO | DownloadType.AUDIO,
                video_quality_id=video_quality_id,
                video_codec_id=video_codec_id,
                audio_quality_id=audio_quality_id,
            )
        except RuntimeError:
            result = None

        resolved_pages.append({
            "part": p.get("part", ""),
            "cid": cid,
            **(result or {}),
        })

    return {
        "title": meta.get("title", ""),
        "owner": meta.get("owner", {}).get("name", ""),
        "duration": meta.get("duration", 0),
        "pic": meta.get("pic", ""),
        "tname": meta.get("tname", ""),
        "pages": resolved_pages,
    }


# ---------------------------------------------------------------------------
# Parse (exact bvid + cid)
# ---------------------------------------------------------------------------

@router.get("/api/parse")
async def parse(
    bvid: str = Query(..., description="BV-id"),
    cid: int = Query(..., description="Episode/chapter cid"),
    session_id: str | None = Query(None, description="Session id from POST /api/cookies"),
    aid: int = Query(0, description="aid (required for cheese)"),
    ep_id: int = Query(0, description="ep_id (required for cheese)"),
    type: str = Query("video", description='Content type: "video" | "bangumi" | "cheese"'),
    video_quality_id: int = Query(200, description="Desired video quality id"),
    video_codec_id: int = Query(20, description="Desired video codec id"),
    audio_quality_id: int = Query(30300, description="Desired audio quality id"),
):
    """Resolve download URLs for a single episode (bvid + cid)."""
    use_session(session_id)

    _type_map = {
        "video": Attribute.VIDEO_BIT,
        "bangumi": Attribute.BANGUMI_BIT,
        "cheese": Attribute.CHEESE_BIT,
    }
    attr = _type_map.get(type)
    if attr is None:
        raise HTTPException(status_code=400, detail=f"Unsupported type '{type}'.")

    try:
        result = resolve_download_url(
            bvid=bvid, cid=cid, aid=aid, ep_id=ep_id,
            attribute=attr,
            download_type=DownloadType.VIDEO | DownloadType.AUDIO,
            video_quality_id=video_quality_id,
            video_codec_id=video_codec_id,
            audio_quality_id=audio_quality_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.exception("Unhandled error resolving %s cid=%d", bvid, cid)
        raise HTTPException(status_code=500, detail=str(exc))

    if not result["download_list"]:
        raise HTTPException(status_code=404, detail="No downloadable stream found")

    return result


# ---------------------------------------------------------------------------
# Cookies
# ---------------------------------------------------------------------------

@router.post("/api/cookies")
async def set_cookies(
    SESSDATA: str | None = None,
    bili_jct: str | None = None,
    DedeUserID: str | None = None,
) -> str:
    """Inject Bilibili login cookies and return a session id.

    Pass the returned string as ``session_id`` to ``/api/info``,
    ``/api/download``, or ``/api/parse`` to use this login session.
    Sessions expire after 10 minutes.
    """
    clean_expired_sessions()

    cookies = {}
    if SESSDATA:
        cookies["SESSDATA"] = SESSDATA
    if bili_jct:
        cookies["bili_jct"] = bili_jct
    if DedeUserID:
        cookies["DedeUserID"] = DedeUserID

    session_id = create_session(cookies)
    logged_in = bool(cookies.get("SESSDATA"))
    logger.info("Created session %s (logged-in: %s)", session_id[:8], logged_in)

    return session_id
