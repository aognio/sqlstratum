"""SQLite compiler for sqlstratum AST."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from . import ast
from .expr import (
    AliasExpr,
    BinaryPredicate,
    Function,
    Literal,
    LogicalPredicate,
    NotPredicate,
    OrderSpec,
    UnaryPredicate,
)
from .meta import Column, Table
from .types import Predicate


@dataclass(frozen=True)
class Compiled(ast.Compiled):
    pass


def compile(query: Any, dialect: str = "sqlite") -> Compiled:
    if dialect != "sqlite":
        raise ValueError("Only sqlite dialect is supported in v0.1")
    compiler = _Compiler()
    sql = compiler.compile_query(query)
    return Compiled(sql=sql, params=compiler.params)


class _Compiler:
    def __init__(self) -> None:
        self.params: Dict[str, Any] = {}
        self._param_index = 0

    def compile_query(self, query: Any) -> str:
        if isinstance(query, ast.SelectQuery):
            return self._compile_select(query)
        if isinstance(query, ast.InsertQuery):
            return self._compile_insert(query)
        if isinstance(query, ast.UpdateQuery):
            return self._compile_update(query)
        if isinstance(query, ast.DeleteQuery):
            return self._compile_delete(query)
        raise TypeError(f"Unsupported query type: {type(query)}")

    def _compile_select(self, query: ast.SelectQuery) -> str:
        parts: List[str] = []
        distinct = "DISTINCT " if query.distinct else ""
        projections = ", ".join(self._compile_projection(p) for p in query.projections)
        parts.append(f"SELECT {distinct}{projections}")
        if query.from_ is not None:
            parts.append("FROM " + self._compile_source(query.from_))
        for join in query.joins:
            join_sql = "JOIN" if join.kind == "INNER" else "LEFT JOIN"
            parts.append(f"{join_sql} {self._compile_source(join.source)} ON {self._compile_predicate(join.on)}")
        if query.where:
            parts.append("WHERE " + self._compile_and_list(query.where))
        if query.group_by:
            parts.append("GROUP BY " + ", ".join(self._compile_expr(e) for e in query.group_by))
        if query.having:
            parts.append("HAVING " + self._compile_and_list(query.having))
        if query.order_by:
            parts.append("ORDER BY " + ", ".join(self._compile_order(o) for o in query.order_by))
        if query.limit is not None:
            parts.append("LIMIT " + self._bind(query.limit))
        if query.offset is not None:
            parts.append("OFFSET " + self._bind(query.offset))
        return " ".join(parts)

    def _compile_insert(self, query: ast.InsertQuery) -> str:
        columns = ", ".join(self._quote(k) for k, _ in query.values)
        values = ", ".join(self._bind(v) for _, v in query.values)
        return f"INSERT INTO {self._compile_table(query.table)} ({columns}) VALUES ({values})"

    def _compile_update(self, query: ast.UpdateQuery) -> str:
        sets = ", ".join(f"{self._quote(k)} = {self._bind(v)}" for k, v in query.values)
        parts = [f"UPDATE {self._compile_table(query.table)} SET {sets}"]
        if query.where:
            parts.append("WHERE " + self._compile_and_list(query.where))
        return " ".join(parts)

    def _compile_delete(self, query: ast.DeleteQuery) -> str:
        parts = [f"DELETE FROM {self._compile_table(query.table)}"]
        if query.where:
            parts.append("WHERE " + self._compile_and_list(query.where))
        return " ".join(parts)

    def _compile_projection(self, expr: Any) -> str:
        return self._compile_expr(expr)

    def _compile_source(self, source: Any) -> str:
        if isinstance(source, Table):
            return self._compile_table(source)
        if isinstance(source, ast.Subquery):
            return f"({self._compile_select(source.query)}) AS {self._quote(source.alias)}"
        raise TypeError(f"Unsupported source type: {type(source)}")

    def _compile_table(self, table: Table) -> str:
        if table.alias:
            return f"{self._quote(table.name)} AS {self._quote(table.alias)}"
        return self._quote(table.name)

    def _compile_expr(self, expr: Any) -> str:
        if isinstance(expr, Column):
            return self._compile_column(expr)
        if isinstance(expr, AliasExpr):
            return f"{self._compile_expr(expr.expr)} AS {self._quote(expr.alias)}"
        if isinstance(expr, Function):
            args = ", ".join(self._compile_expr(a) for a in expr.args)
            return f"{expr.name}({args})"
        if isinstance(expr, OrderSpec):
            return self._compile_order(expr)
        if isinstance(expr, Literal):
            return self._bind(expr.value)
        if isinstance(expr, ast.Subquery):
            return f"({self._compile_select(expr.query)})"
        return self._compile_predicate(expr)

    def _compile_predicate(self, pred: Predicate) -> str:
        if isinstance(pred, BinaryPredicate):
            return f"{self._compile_expr(pred.left)} {pred.op} {self._compile_expr(pred.right)}"
        if isinstance(pred, UnaryPredicate):
            return f"{self._compile_expr(pred.expr)} {pred.op}"
        if isinstance(pred, LogicalPredicate):
            inner = f" {pred.op} ".join(self._compile_predicate(p) for p in pred.predicates)
            return f"({inner})"
        if isinstance(pred, NotPredicate):
            return f"NOT ({self._compile_predicate(pred.predicate)})"
        raise TypeError(f"Unsupported predicate type: {type(pred)}")

    def _compile_and_list(self, preds: Iterable[Predicate]) -> str:
        parts = [self._compile_predicate(p) for p in preds]
        return " AND ".join(parts)

    def _compile_order(self, order: OrderSpec) -> str:
        return f"{self._compile_expr(order.expr)} {order.direction}"

    def _compile_column(self, col: Column) -> str:
        if col.table.alias:
            return f"{self._quote(col.table.alias)}.{self._quote(col.name)}"
        return f"{self._quote(col.table.name)}.{self._quote(col.name)}"

    def _quote(self, ident: str) -> str:
        escaped = ident.replace('"', '""')
        return f'"{escaped}"'

    def _bind(self, value: Any) -> str:
        name = f"p{self._param_index}"
        self._param_index += 1
        self.params[name] = value
        return f":{name}"
