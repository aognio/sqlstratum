"""SQLite-specific wrappers and expressions."""
from __future__ import annotations

from typing import Optional

from .dialect_binding import bind_dialect
from .expr import Expr, Function, Literal, ensure_expr


def using_sqlite(query):
    return bind_dialect(query, "sqlite")


def TOTAL(expr: Expr) -> Function:
    return Function("TOTAL", (ensure_expr(expr),))


def GROUP_CONCAT(expr: Expr, separator: Optional[str] = None) -> Function:
    if separator is None:
        return Function("GROUP_CONCAT", (ensure_expr(expr),))
    return Function("GROUP_CONCAT", (ensure_expr(expr), Literal(separator)))
