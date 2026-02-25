"""Helpers for binding queries to an explicit dialect wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from .errors import UnsupportedDialectFeatureError
from . import ast


def _is_query_object(value: Any) -> bool:
    return isinstance(
        value,
        (ast.SelectQuery, ast.InsertQuery, ast.UpdateQuery, ast.DeleteQuery, ast.Subquery),
    )


@dataclass(frozen=True)
class DialectBoundQuery:
    query: Any
    dialect: str

    def _rewrap(self, value: Any) -> Any:
        if isinstance(value, DialectBoundQuery):
            return value
        if _is_query_object(value):
            return DialectBoundQuery(query=value, dialect=self.dialect)
        return value

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self.query, name)
        if not callable(attr):
            return attr

        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            result = attr(*args, **kwargs)
            return self._rewrap(result)

        return _wrapped


def bind_dialect(query: Any, dialect: str) -> DialectBoundQuery:
    return DialectBoundQuery(query=query, dialect=dialect.lower())


def unwrap_query(query: Any, dialect: str) -> Tuple[Any, str]:
    requested = dialect.lower()
    current = query
    bound: Optional[str] = None

    while isinstance(current, DialectBoundQuery):
        if bound is None:
            bound = current.dialect
        elif current.dialect != bound:
            raise UnsupportedDialectFeatureError(
                requested,
                f"conflicting nested dialect bindings ('{bound}' and '{current.dialect}')",
                hint="Use a single dialect wrapper for a query.",
            )
        current = current.query

    if bound is not None and requested != bound:
        raise UnsupportedDialectFeatureError(
            requested,
            f"query bound to dialect '{bound}'",
            hint=f"Compile/execute this query with dialect='{bound}'.",
        )

    return current, bound or requested
