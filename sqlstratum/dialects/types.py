"""Dialect compiler protocol for query compilation."""
from __future__ import annotations

from typing import Any, Protocol

from ..ast import Compiled


class DialectCompiler(Protocol):
    """A dialect compiler turns a query AST into SQL + bound params."""

    def compile(self, query: Any) -> Compiled:
        ...
