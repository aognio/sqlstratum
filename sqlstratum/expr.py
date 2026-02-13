"""Expression and predicate nodes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple


class Expr:
    def __eq__(self, other: Any) -> "BinaryPredicate":  # type: ignore[override]
        return BinaryPredicate(self, "=", ensure_expr(other))

    def __ne__(self, other: Any) -> "BinaryPredicate":  # type: ignore[override]
        return BinaryPredicate(self, "!=", ensure_expr(other))

    def __lt__(self, other: Any) -> "BinaryPredicate":
        return BinaryPredicate(self, "<", ensure_expr(other))

    def __le__(self, other: Any) -> "BinaryPredicate":
        return BinaryPredicate(self, "<=", ensure_expr(other))

    def __gt__(self, other: Any) -> "BinaryPredicate":
        return BinaryPredicate(self, ">", ensure_expr(other))

    def __ge__(self, other: Any) -> "BinaryPredicate":
        return BinaryPredicate(self, ">=", ensure_expr(other))

    def AS(self, alias: str) -> "AliasExpr":
        return AliasExpr(self, alias)

    def ASC(self) -> "OrderSpec":
        return OrderSpec(self, "ASC")

    def DESC(self) -> "OrderSpec":
        return OrderSpec(self, "DESC")


@dataclass(frozen=True)
class AliasExpr(Expr):
    expr: Expr
    alias: str


@dataclass(frozen=True)
class Literal(Expr):
    value: Any


@dataclass(frozen=True)
class BinaryPredicate:
    left: Expr
    op: str
    right: Expr


@dataclass(frozen=True)
class UnaryPredicate:
    expr: Expr
    op: str


@dataclass(frozen=True)
class LogicalPredicate:
    op: str  # "AND" or "OR"
    predicates: Tuple["Predicate", ...]


@dataclass(frozen=True)
class NotPredicate:
    predicate: "Predicate"


@dataclass(frozen=True)
class Function(Expr):
    name: str
    args: tuple


@dataclass(frozen=True)
class OrderSpec:
    expr: Expr
    direction: str


def ensure_expr(value: Any) -> Expr:
    from .meta import Column
    if isinstance(value, Expr) or isinstance(value, Column):
        return value  # type: ignore[return-value]
    return Literal(value)


# Aggregate helpers

def COUNT(expr: Optional[Expr] = None) -> Function:
    if expr is None:
        return Function("COUNT", (Literal(1),))
    return Function("COUNT", (ensure_expr(expr),))


def SUM(expr: Expr) -> Function:
    return Function("SUM", (ensure_expr(expr),))


def AVG(expr: Expr) -> Function:
    return Function("AVG", (ensure_expr(expr),))


def MIN(expr: Expr) -> Function:
    return Function("MIN", (ensure_expr(expr),))


def MAX(expr: Expr) -> Function:
    return Function("MAX", (ensure_expr(expr),))


Predicate = BinaryPredicate | UnaryPredicate | LogicalPredicate | NotPredicate
