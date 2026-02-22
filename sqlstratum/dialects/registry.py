"""Runtime dialect registry used by the public compile entrypoint."""
from __future__ import annotations

from typing import Dict

from ..errors import UnsupportedDialectFeatureError
from .types import DialectCompiler


_REGISTRY: Dict[str, DialectCompiler] = {}


def register_dialect(name: str, compiler: DialectCompiler) -> None:
    _REGISTRY[name.lower()] = compiler


def get_dialect(name: str) -> DialectCompiler:
    key = name.lower()
    try:
        return _REGISTRY[key]
    except KeyError as exc:
        supported = ", ".join(sorted(_REGISTRY)) or "none"
        raise UnsupportedDialectFeatureError(
            key,
            "dialect",
            hint=f"Supported dialects: {supported}",
        ) from exc


def list_dialects() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))
