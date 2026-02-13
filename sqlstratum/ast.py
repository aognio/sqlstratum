"""AST node definitions for sqlstratum."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple, TypeVar

from .meta import Column
from .expr import OrderSpec
from .types import Expression, HydrationTarget, Predicate, Source


@dataclass(frozen=True)
class Compiled:
    sql: str
    params: Dict[str, Any]


@dataclass(frozen=True)
class SelectQuery:
    projections: Tuple[Expression, ...]
    from_: Optional[Source]
    joins: Tuple["Join", ...]
    where: Tuple[Predicate, ...]
    group_by: Tuple[Expression, ...]
    having: Tuple[Predicate, ...]
    order_by: Tuple[OrderSpec, ...]
    limit: Optional[int]
    offset: Optional[int]
    distinct: bool
    hydrate: HydrationTarget


@dataclass(frozen=True)
class Join:
    kind: str  # "INNER" or "LEFT"
    source: Source
    on: Predicate


@dataclass(frozen=True)
class InsertQuery:
    table: Any
    values: Tuple[Tuple[str, Any], ...]


@dataclass(frozen=True)
class UpdateQuery:
    table: Any
    values: Tuple[Tuple[str, Any], ...]
    where: Tuple[Predicate, ...]


@dataclass(frozen=True)
class DeleteQuery:
    table: Any
    where: Tuple[Predicate, ...]


@dataclass(frozen=True)
class Subquery:
    query: SelectQuery
    alias: str
    c: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "c", _SubqueryColumnAccessor(self.alias))

    def __getattr__(self, item: str) -> Column:
        return getattr(self.c, item)


@dataclass(frozen=True)
class _SubqueryTable:
    name: str
    alias: Optional[str] = None


class _SubqueryColumnAccessor:
    def __init__(self, alias: str) -> None:
        self._alias = alias

    def __getattr__(self, item: str) -> Column:
        return Column(name=item, py_type=object, table=_SubqueryTable(self._alias))


@dataclass(frozen=True)
class ExecutionResult:
    rowcount: int
    lastrowid: Optional[int]


T = TypeVar("T")


def tupled(items: Iterable[T]) -> Tuple[T, ...]:
    return tuple(items)
