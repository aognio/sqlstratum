"""Metadata objects: Table and Column."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .expr import Expr

@dataclass(frozen=True)
class Column(Expr):
    name: str
    py_type: type
    table: "Table"

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Column({self.table.name}.{self.name})"

    # Comparison operators build predicates (defined in expr.py)
    def __eq__(self, other: Any) -> "BinaryPredicate":  # type: ignore[override]
        from .expr import BinaryPredicate, ensure_expr
        return BinaryPredicate(self, "=", ensure_expr(other))

    def __ne__(self, other: Any) -> "BinaryPredicate":  # type: ignore[override]
        from .expr import BinaryPredicate, ensure_expr
        return BinaryPredicate(self, "!=", ensure_expr(other))

    def __lt__(self, other: Any) -> "BinaryPredicate":
        from .expr import BinaryPredicate, ensure_expr
        return BinaryPredicate(self, "<", ensure_expr(other))

    def __le__(self, other: Any) -> "BinaryPredicate":
        from .expr import BinaryPredicate, ensure_expr
        return BinaryPredicate(self, "<=", ensure_expr(other))

    def __gt__(self, other: Any) -> "BinaryPredicate":
        from .expr import BinaryPredicate, ensure_expr
        return BinaryPredicate(self, ">", ensure_expr(other))

    def __ge__(self, other: Any) -> "BinaryPredicate":
        from .expr import BinaryPredicate, ensure_expr
        return BinaryPredicate(self, ">=", ensure_expr(other))

    def is_null(self) -> "UnaryPredicate":
        from .expr import UnaryPredicate
        return UnaryPredicate(self, "IS NULL")

    def is_not_null(self) -> "UnaryPredicate":
        from .expr import UnaryPredicate
        return UnaryPredicate(self, "IS NOT NULL")

    def contains(self, text: str) -> "BinaryPredicate":
        from .expr import BinaryPredicate, Literal
        return BinaryPredicate(self, "LIKE", Literal(f"%{text}%"))

    def is_true(self) -> "BinaryPredicate":
        from .expr import BinaryPredicate, Literal
        return BinaryPredicate(self, "=", Literal(True))

    def is_false(self) -> "BinaryPredicate":
        from .expr import BinaryPredicate, Literal
        return BinaryPredicate(self, "=", Literal(False))

class Table:
    def __init__(self, name: str, *columns: Column, alias: Optional[str] = None, columns_list: Optional[Iterable[Column]] = None):
        self.name = name
        self.alias = alias
        if columns_list is not None:
            cols = list(columns_list)
        else:
            cols = list(columns)
        self._columns: Dict[str, Column] = {}
        for col in cols:
            if col.table is not self:
                object.__setattr__(col, "table", self)  # type: ignore[misc]
            self._columns[col.name] = col
        self.c = _ColumnAccessor(self._columns)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Table({self.name})"

    def AS(self, alias: str) -> "Table":
        return Table(self.name, columns_list=self._columns.values(), alias=alias)

    @property
    def columns(self) -> List[Column]:
        return list(self._columns.values())


def col(name: str, py_type: type) -> Column:
    # Placeholder table; Table will reset table reference on init.
    dummy = Table("__dummy__")
    return Column(name=name, py_type=py_type, table=dummy)


class _ColumnAccessor:
    def __init__(self, columns: Dict[str, Column]):
        self._columns = columns

    def __getattr__(self, item: str) -> Column:
        try:
            return self._columns[item]
        except KeyError as exc:
            raise AttributeError(item) from exc
