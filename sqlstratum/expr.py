"""Expression and predicate nodes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple


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

    def IN(self, values: Any) -> "InPredicate":
        return InPredicate(self, tupled_values(values), negated=False)

    def NOT_IN(self, values: Any) -> "InPredicate":
        return InPredicate(self, tupled_values(values), negated=True)

    def BETWEEN(self, low: Any, high: Any) -> "BetweenPredicate":
        return BetweenPredicate(self, ensure_expr(low), ensure_expr(high), negated=False)

    def NOT_BETWEEN(self, low: Any, high: Any) -> "BetweenPredicate":
        return BetweenPredicate(self, ensure_expr(low), ensure_expr(high), negated=True)


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
class InPredicate:
    expr: Expr
    values: tuple
    negated: bool


@dataclass(frozen=True)
class BetweenPredicate:
    expr: Expr
    low: Expr
    high: Expr
    negated: bool


@dataclass(frozen=True)
class ExistsPredicate:
    query: Any
    negated: bool


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


def tupled_values(values: Any) -> tuple:
    from . import ast
    if hasattr(values, "projections") and hasattr(values, "from_"):
        return (values,)
    if isinstance(values, ast.SetQuery):
        return (values,)
    if isinstance(values, (list, tuple, set)):
        return tuple(ensure_expr(v) for v in values)
    return (ensure_expr(values),)


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


def ASC(expr: Expr) -> OrderSpec:
    return OrderSpec(ensure_expr(expr), "ASC")


def DESC(expr: Expr) -> OrderSpec:
    return OrderSpec(ensure_expr(expr), "DESC")


def EXISTS(query: Any) -> ExistsPredicate:
    return ExistsPredicate(query=query, negated=False)


def NOT_EXISTS(query: Any) -> ExistsPredicate:
    return ExistsPredicate(query=query, negated=True)


def TOTAL(expr: Expr) -> Function:
    return Function("TOTAL", (ensure_expr(expr),))


def GROUP_CONCAT(expr: Expr, separator: Optional[str] = None) -> Function:
    if separator is None:
        return Function("GROUP_CONCAT", (ensure_expr(expr),))
    return Function("GROUP_CONCAT", (ensure_expr(expr), Literal(separator)))


Predicate = (
    BinaryPredicate
    | UnaryPredicate
    | LogicalPredicate
    | NotPredicate
    | InPredicate
    | BetweenPredicate
    | ExistsPredicate
)
