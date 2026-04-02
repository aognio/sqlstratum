"""Type-checker-friendly Protocols for sqlstratum DSL."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol, TYPE_CHECKING, runtime_checkable, TypeVar

if TYPE_CHECKING:
    from .expr import AliasExpr, BinaryPredicate, LogicalPredicate, NotPredicate, UnaryPredicate


@runtime_checkable
class Expression(Protocol):
    def AS(self, alias: str) -> "AliasExpr": ...

    def __eq__(self, other: Any) -> "BinaryPredicate": ...

    def __ne__(self, other: Any) -> "BinaryPredicate": ...

    def __lt__(self, other: Any) -> "BinaryPredicate": ...

    def __le__(self, other: Any) -> "BinaryPredicate": ...

    def __gt__(self, other: Any) -> "BinaryPredicate": ...

    def __ge__(self, other: Any) -> "BinaryPredicate": ...


@runtime_checkable
class Source(Protocol):
    alias: Optional[str]
    c: Any


RowMapping = Dict[str, Any]
T = TypeVar("T")
Hydrator = Callable[[RowMapping], T]
HydrationTarget = Callable[[RowMapping], Any] | type[Any] | None
if TYPE_CHECKING:
    Predicate = BinaryPredicate | UnaryPredicate | LogicalPredicate | NotPredicate
else:  # pragma: no cover - typing only
    Predicate = Any
