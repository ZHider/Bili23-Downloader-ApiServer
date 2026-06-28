"""Stub installer — call ``install_stubs()`` before any project import.

Structure
---------
* ``stubs/__init__.py`` — installer + catch-all finder
* ``stubs/_helpers.py`` — ``_ConfigItem``, ``make_module()``
* ``stubs/config.py``   — ``_QConfigStub`` + ``build_config_module()``
* ``stubs/pyside6.py``  — ``build_pyside6_modules()``
"""
from __future__ import annotations

import sys

from ._helpers import make_module
from .config import build_config_module
from .pyside6 import build_pyside6_modules


class _CatchAll:
    """Return empty modules for any PySide6/qfluentwidgets sub-module."""
    @staticmethod
    def find_spec(fullname, path=None, target=None):
        if fullname.startswith("PySide6") or fullname.startswith("qfluentwidgets"):
            if fullname not in sys.modules:
                sys.modules[fullname] = make_module(fullname)
        return None


def install_stubs() -> None:
    """Must be called **before** any import from the ``util`` package."""

    # 1. Prevent util/__init__.py side effect (import util.ffmpeg)
    sys.modules["util.ffmpeg"] = make_module("util.ffmpeg", __package="util")

    # 2. Stub util.common.config (never run real 490-line config.py)
    sys.modules["util.common.config"] = build_config_module()

    # 3. PySide6 stubs (QtCore, QtGui, QtWidgets)
    for name, mod in build_pyside6_modules().items():
        sys.modules[name] = mod

    # 4. Catch any remaining deep sub-modules
    sys.meta_path.insert(0, _CatchAll())
