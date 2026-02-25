"""Public compile entrypoint with dialect dispatch."""
from __future__ import annotations

from typing import Any

from .ast import Compiled
from .dialects import get_dialect
from .dialect_binding import unwrap_query


def compile(query: Any, dialect: str = "sqlite") -> Compiled:
    """Compile a query using the selected dialect compiler."""
    unwrapped_query, resolved_dialect = unwrap_query(query, dialect)
    compiler = get_dialect(resolved_dialect)
    return compiler.compile(unwrapped_query)
