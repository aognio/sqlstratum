"""Public compile entrypoint with dialect dispatch."""
from __future__ import annotations

from typing import Any

from .ast import Compiled
from .dialects import get_dialect


def compile(query: Any, dialect: str = "sqlite") -> Compiled:
    """Compile a query using the selected dialect compiler."""
    compiler = get_dialect(dialect)
    return compiler.compile(query)
