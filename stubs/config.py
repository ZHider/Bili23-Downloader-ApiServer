"""Core config stub — replaces the 490-line ``util/common/config.py``.

Provides a minimal ``_QConfigStub`` with all ConfigItem attributes the server
path accesses, and ``_build_config_module()`` that builds the stub module.
"""
from __future__ import annotations
import types
from ._helpers import _ConfigItem


class _AreaConfigItem:
    """ConfigItem stub for ``area`` — lazily imports ``Area`` enum."""

    def __get__(self, instance, owner=None):
        return self

    def __set__(self, instance, value):
        instance._area_value = value

    def __bool__(self):
        return True


class _QConfigStub:
    """Minimal ``QConfig`` — in-memory value store, no file persistence."""

    # ---- Cookie ----
    img_key = _ConfigItem("Cookie", "img_key", "")
    sub_key = _ConfigItem("Cookie", "sub_key", "")
    bili_jct = _ConfigItem("Cookie", "bili_jct", "")
    DedeUserID = _ConfigItem("Cookie", "DedeUserID", "")
    DedeUserID__ckMd5 = _ConfigItem("Cookie", "DedeUserID__ckMd5", "")
    SESSDATA = _ConfigItem("Cookie", "SESSDATA", "")
    is_login = _ConfigItem("Cookie", "is_login", False)
    uuid = _ConfigItem("Cookie", "uuid", "")
    b_lsid = _ConfigItem("Cookie", "b_lsid", "")
    b_nut = _ConfigItem("Cookie", "b_nut", "")
    buvid_fp = _ConfigItem("Cookie", "buvid_fp", "")
    buvid3 = _ConfigItem("Cookie", "buvid3", "")
    buvid4 = _ConfigItem("Cookie", "buvid4", "")
    bili_ticket = _ConfigItem("Cookie", "bili_ticket", "")
    bili_ticket_expires = _ConfigItem("Cookie", "bili_ticket_expires", 0)

    # ---- Download ----
    download_video_stream = _ConfigItem("Download", "download_video_stream", True)
    download_audio_stream = _ConfigItem("Download", "download_audio_stream", True)
    video_quality_id = _ConfigItem("Download", "video_quality_id", 200)
    video_codec_id = _ConfigItem("Download", "video_codec_id", 20)
    audio_quality_id = _ConfigItem("Download", "audio_quality_id", 30300)
    video_quality_priority = _ConfigItem("Download", "video_quality_priority",
                                         [120, 116, 80, 64, 32, 16])
    video_codec_priority = _ConfigItem("Download", "video_codec_priority",
                                       [13, 12, 14])
    audio_quality_priority = _ConfigItem("Download", "audio_quality_priority",
                                         [30251, 30232, 30216, 30200])
    merge_video_audio = _ConfigItem("Download", "merge_video_audio", True)
    keep_original_files = _ConfigItem("Download", "keep_original_files", False)

    # ---- Advanced ----
    proxy_enabled = _ConfigItem("Advanced", "proxy_enabled", False)
    proxy_type = _ConfigItem("Advanced", "proxy_type", "http")
    proxy_server = _ConfigItem("Advanced", "proxy_server", "")
    proxy_uname = _ConfigItem("Advanced", "proxy_uname", "")
    proxy_password = _ConfigItem("Advanced", "proxy_password", "")
    proxy_port = _ConfigItem("Advanced", "proxy_port", 0)
    user_agent = _ConfigItem("Advanced", "user_agent",
                             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36")
    prefer_cdn_server_provider = _ConfigItem("Advanced", "prefer_cdn_server_provider_", True)
    cn_cdn_server_list = _ConfigItem("Advanced", "cn_cdn_server_list", [])
    ov_cdn_server_list = _ConfigItem("Advanced", "ov_cdn_server_list", [])
    area = _AreaConfigItem()

    def get(self, item) -> object:
        if isinstance(item, _AreaConfigItem):
            from util.common.enum import Area
            return Area.CN
        return item._value if isinstance(item, _ConfigItem) else item

    def set(self, item, value, save: bool = True) -> None:
        if isinstance(item, _AreaConfigItem):
            item._area_value = value
            return
        if isinstance(item, _ConfigItem):
            item._value = value


def build_config_module() -> types.ModuleType:
    """Build ``util.common.config`` stub module."""
    import logging
    mod = types.ModuleType("util.common.config")
    mod.config = _QConfigStub()
    mod.ConfigItem = _ConfigItem
    mod.DefaultValue = type("DefaultValue", (), {})()
    mod.logger = logging.getLogger("config")
    mod.APPConfig = _QConfigStub
    mod.__package__ = "util.common"
    mod.__path__ = []
    return mod
