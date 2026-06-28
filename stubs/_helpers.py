"""Shared helpers used by multiple stub modules."""
from __future__ import annotations

import types


class _ConfigItem:
    """Minimal descriptor with ``__bool__`` support.

    qfluentwidgets' ``ConfigItem.__get__`` returns the descriptor itself
    even on instance access.  ``QConfig.get(item)`` reads the stored value.
    """

    def __init__(self, group: str, name: str, default,
                 validator=None, restart: bool = False):
        self._default = default
        self._value = default

    def __get__(self, instance, owner=None):
        return self

    def __set__(self, instance, value):
        self._value = value

    def __bool__(self):
        return bool(self._value)


def make_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__package__ = name.rpartition(".")[0]
    mod.__path__ = []
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod
