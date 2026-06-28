"""PySide6 stub — one class per symbol the server's import chain touches.

Builders return ``types.ModuleType`` objects ready to insert into
``sys.modules``.
"""
from __future__ import annotations

import types


def build_pyside6_modules() -> dict[str, types.ModuleType]:
    """Return ``{module_name: module}`` for PySide6 top + sub-modules."""

    class Qt:
        class CheckState:
            Unchecked = 0
            PartiallyChecked = 1
            Checked = 2

    class QObject:
        def __init__(self, parent=None): pass

    class Signal:
        def __new__(cls, *types):
            return super().__new__(cls)

        def __get__(self, obj, objtype=None): return self

    @staticmethod
    def Slot(*types):
        def deco(fn): return fn
        return deco

    class QLocale:
        def __init__(self, locale=""): self._locale = locale
        def name(self): return self._locale

    class QStandardPaths:
        class StandardLocation:
            DownloadLocation = 14
            AppDataLocation = 17

        @staticmethod
        def writableLocation(_): return "/tmp/bili23"

    class QCoreApp:
        @staticmethod
        def translate(ctx, src, disamb=None, n=-1): return src

    class QPixmap:
        pass

    class QWidget:
        def __init__(self, parent=None): pass

    class QFileDialog:
        @staticmethod
        def getExistingDirectory(*a, **kw): return ""

    def _make(name: str, **attrs) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__package__ = name.rpartition(".")[0]
        mod.__path__ = []
        for k, v in attrs.items():
            setattr(mod, k, v)
        return mod

    return {
        "PySide6": _make("PySide6"),
        "PySide6.QtCore": _make("PySide6.QtCore",
                                QObject=QObject, Signal=Signal, Slot=Slot,
                                Qt=Qt(), QLocale=QLocale,
                                QCoreApplication=QCoreApp,
                                QStandardPaths=QStandardPaths,
                                ),
        "PySide6.QtGui": _make("PySide6.QtGui", QPixmap=QPixmap),
        "PySide6.QtWidgets": _make("PySide6.QtWidgets",
                                   QWidget=QWidget, QFileDialog=QFileDialog,
                                   ),
    }
