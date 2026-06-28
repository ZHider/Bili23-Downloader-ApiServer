"""Reusable download-URL resolver that imports Bili23 project modules directly.

Synchronous, no Qt signals — returns the same dict `parse_download_info()` would.
"""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urlencode

from util.network.request import SyncNetWorkRequest
from util.parse.parser.base import ParserBase
from util.parse.episode.tree import Attribute
from util.common.enum import DownloadType, MediaType
from util.common.config import config
from util.download.task.info import TaskInfo
from util.download.parse.video_info import VideoInfoParser
from util.download.parse.audio_info import AudioInfoParser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WBI key management
# ---------------------------------------------------------------------------


def init_wbi_keys() -> None:
    """Fetch `img_key` / `sub_key` from Bilibili nav API and set on config.

    Safe to call multiple times (updates keys in-place).
    """
    request = SyncNetWorkRequest("https://api.bilibili.com/x/web-interface/nav")
    response = request.run()

    data = response.get("data", {})
    wbi = data.get("wbi_img", {})
    img_url = wbi.get("img_url", "")
    sub_url = wbi.get("sub_url", "")

    from pathlib import Path
    config.set(config.img_key, Path(img_url).stem, save=False)
    config.set(config.sub_key, Path(sub_url).stem, save=False)

    logger.info("WBI keys initialised (img_key=%s, sub_key=%s)",
                config.get(config.img_key)[:8], config.get(config.sub_key)[:8])


def ensure_wbi_keys() -> None:
    """Initialise WBI keys if they are empty."""
    if not config.get(config.img_key) or not config.get(config.sub_key):
        init_wbi_keys()


# ---------------------------------------------------------------------------
# Cookie helpers (minimal — log-in not required for most content)
# ---------------------------------------------------------------------------

def apply_cookies(cookies: dict[str, str] | None = None) -> None:
    """Apply Bilibili session cookies to the global httpx client.

    When *cookies* is ``None`` only the anonymous defaults are set.
    Pass logged-in cookies (``SESSDATA``, ``bili_jct``, ``DedeUserID``)
    to access age-restricted or premium content.
    """
    from util.network.request import _ensure_client, _apply_cookies

    base = {
        "_uuid": config.get(config.uuid),
        "b_lsid": config.get(config.b_lsid),
        "buvid3": config.get(config.buvid3),
        "buvid4": config.get(config.buvid4),
        "CURRENT_FNVAL": "4048",
        "CURRENT_QUALITY": "0",
    }

    if cookies:
        base.update(cookies)
    elif config.get(config.is_login):
        base.update({
            "bili_jct": config.get(config.bili_jct),
            "DedeUserID": config.get(config.DedeUserID),
            "DedeUserID__ckMd5": config.get(config.DedeUserID__ckMd5),
            "SESSDATA": config.get(config.SESSDATA),
        })

    client = _ensure_client()
    _apply_cookies(client, base)
    logger.info("Cookies applied (logged-in: %s)", bool(cookies or config.get(config.is_login)))


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------

def resolve_download_url(
    bvid: str,
    cid: int,
    *,
    attribute: int = Attribute.VIDEO_BIT,
    aid: int = 0,
    ep_id: int = 0,
    download_type: int = DownloadType.VIDEO | DownloadType.AUDIO,
    video_quality_id: int = 200,
    video_codec_id: int = 20,
    audio_quality_id: int = 30300,
) -> dict:
    """Return parsed download URLs for a single Bilibili episode.

    Parameters
    ----------
    bvid : str
        BV-id of the video (e.g. ``"BV1GJ411m7dN"``).
    cid : int
        Episode / chapter identifier (from the initial meta-data API).
    attribute : int, optional
        One of ``Attribute.VIDEO_BIT``, ``Attribute.BANGUMI_BIT``,
        ``Attribute.CHEESE_BIT``.  Defaults to video.
    aid : int
        ``aid`` — required for cheese episodes.
    ep_id : int
        ``ep_id`` — required for cheese episodes.
    download_type : int, optional
        Bitmask of what to resolve (default = video + audio).
    video_quality_id : int, optional
        Desired video quality id (default ``200`` = auto).
    video_codec_id : int, optional
        Desired video codec id (default ``20`` = auto).
    audio_quality_id : int, optional
        Desired audio quality id (default ``30300`` = auto).

    Returns
    -------
    dict
        ``{"total_size": int, "download_queue": [str, …], "download_list": {…}}``
    """
    ensure_wbi_keys()

    # --- build a minimal TaskInfo ----------------------------------------
    task = TaskInfo()
    task.Basic.task_id = str(uuid.uuid4())[:8]
    task.Episode.attribute = attribute
    task.Episode.bvid = bvid
    task.Episode.cid = cid
    task.Episode.aid = aid
    task.Episode.ep_id = ep_id
    task.Download.type = download_type
    task.Download.video_quality_id = video_quality_id
    task.Download.video_codec_id = video_codec_id
    task.Download.audio_quality_id = audio_quality_id
    task.Download.merge_video_audio = True
    task.Download.keep_original_files = False

    # --- call the playurl API --------------------------------------------
    if attribute & Attribute.VIDEO_BIT:
        info_data = _get_video_playurl(task)
    elif attribute & Attribute.BANGUMI_BIT:
        info_data = _get_bangumi_playurl(task)
    elif attribute & Attribute.CHEESE_BIT:
        info_data = _get_cheese_playurl(task)
    else:
        raise ValueError(f"Unsupported attribute value: {attribute}")

    # detect media type (DASH / MP4 / FLV)
    if "dash" in info_data:
        task.Download.media_type = MediaType.DASH
    elif info_data.get("format", "").startswith("mp4"):
        task.Download.media_type = MediaType.MP4
    elif info_data.get("format", "").startswith("flv"):
        task.Download.media_type = MediaType.FLV
    else:
        task.Download.media_type = MediaType.UNKNOWN

    # --- parse video stream ----------------------------------------------
    total_size = 0
    download_list: dict[str, dict] = {}

    if task.Download.type & DownloadType.VIDEO:
        parser = VideoInfoParser(info_data, task)
        for entry in parser.parse_info():
            total_size += entry.get("file_size", 0)
            download_list[entry["file_key"]] = entry

    # --- parse audio stream ----------------------------------------------
    if task.Download.type & DownloadType.AUDIO:
        parser = AudioInfoParser(info_data, task)
        for entry in parser.parse_info():
            total_size += entry.get("file_size", 0)
            download_list[entry["file_key"]] = entry

    return {
        "total_size": total_size,
        "download_queue": list(download_list.keys()),
        "download_list": download_list,
    }


# ---------------------------------------------------------------------------
# Internal per-type API helpers
# ---------------------------------------------------------------------------

def get_video_meta(bvid: str) -> dict:
    """Fetch video metadata (title, cid, pages, etc.) from Bilibili.

    Returns the raw ``data`` field of the ``x/web-interface/wbi/view`` API
    -- this is the same data ``VideoParser`` uses in Stage 1.
    """
    ensure_wbi_keys()

    params = {"bvid": bvid}
    url = f"https://api.bilibili.com/x/web-interface/wbi/view?{_PARSER_BASE.enc_wbi(params)}"
    resp = SyncNetWorkRequest(url).run()
    _check_api_response(resp)
    return resp["data"]


#: Shared instance — only uses the pure-Python helpers from ParserBase.
_PARSER_BASE = ParserBase()


def _get_video_playurl(task: TaskInfo) -> dict:
    params = {
        "bvid": task.Episode.bvid,
        "cid": task.Episode.cid,
        "qn": task.Download.video_quality_id,
        "fnver": 0,
        "fnval": 4048,
        "fourk": 1,
    }
    url = f"https://api.bilibili.com/x/player/wbi/playurl?{_PARSER_BASE.enc_wbi(params)}"
    resp = SyncNetWorkRequest(url).run()
    _check_api_response(resp)
    return resp["data"]


def _get_bangumi_playurl(task: TaskInfo) -> dict:
    params = {
        "bvid": task.Episode.bvid,
        "cid": task.Episode.cid,
        "qn": task.Download.video_quality_id,
        "fnver": 0,
        "fnval": 12240,
        "fourk": 1,
    }
    url = f"https://api.bilibili.com/pgc/player/web/playurl?{urlencode(params)}"
    resp = SyncNetWorkRequest(url).run()
    _check_api_response(resp)
    return resp["result"]


def _get_cheese_playurl(task: TaskInfo) -> dict:
    params = {
        "avid": task.Episode.aid,
        "cid": task.Episode.cid,
        "qn": task.Download.video_quality_id,
        "fnver": 0,
        "fnval": 16,
        "fourk": 1,
        "ep_id": task.Episode.ep_id,
    }
    url = f"https://api.bilibili.com/pugv/player/web/playurl?{urlencode(params)}"
    resp = SyncNetWorkRequest(url).run()
    _check_api_response(resp)
    return resp["data"]


def _check_api_response(response: dict) -> None:
    code = response.get("code", -1)
    if code != 0:
        msg = response.get("message", f"API error (code={code})")
        raise RuntimeError(msg)
