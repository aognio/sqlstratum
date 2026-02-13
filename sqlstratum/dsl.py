"""Public DSL constructors and query chaining."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Tuple

from .ast import DeleteQuery, InsertQuery, Join, SelectQuery, Subquery, UpdateQuery, tupled
from .expr import LogicalPredicate, NotPredicate, OrderSpec
from .meta import Table
from .types import Expression, HydrationTarget, Predicate, Source


def SELECT(*projections: Expression) -> SelectQuery:
    return SelectQuery(
        projections=tupled(projections),
        from_=None,
        joins=tuple(),
        where=tuple(),
        group_by=tuple(),
        having=tuple(),
        order_by=tuple(),
        limit=None,
        offset=None,
        distinct=False,
        hydrate=None,
    )


def INSERT(table: Table) -> "InsertBuilder":
    return InsertBuilder(table)


def UPDATE(table: Table) -> "UpdateBuilder":
    return UpdateBuilder(table)


def DELETE(table: Table) -> "DeleteBuilder":
    return DeleteBuilder(table)


def OR(*predicates: Predicate) -> LogicalPredicate:
    return LogicalPredicate("OR", tupled(predicates))


def AND(*predicates: Predicate) -> LogicalPredicate:
    return LogicalPredicate("AND", tupled(predicates))


def NOT(predicate: Predicate) -> NotPredicate:
    return NotPredicate(predicate)


# Query chaining methods added via monkey-patching style functions

def _from(self: SelectQuery, source: Source) -> SelectQuery:
    return replace(self, from_=source)


def _join(self: SelectQuery, source: Source, ON: Predicate) -> SelectQuery:
    joins = self.joins + (Join("INNER", source, ON),)
    return replace(self, joins=joins)


def _left_join(self: SelectQuery, source: Source, ON: Predicate) -> SelectQuery:
    joins = self.joins + (Join("LEFT", source, ON),)
    return replace(self, joins=joins)


def _where(self: SelectQuery, *predicates: Predicate) -> SelectQuery:
    where = self.where + tupled(predicates)
    return replace(self, where=where)


def _group_by(self: SelectQuery, *cols: Expression) -> SelectQuery:
    return replace(self, group_by=self.group_by + tupled(cols))


def _having(self: SelectQuery, *predicates: Predicate) -> SelectQuery:
    return replace(self, having=self.having + tupled(predicates))


def _order_by(self: SelectQuery, *order_specs: OrderSpec) -> SelectQuery:
    return replace(self, order_by=self.order_by + tupled(order_specs))


def _limit(self: SelectQuery, n: int) -> SelectQuery:
    return replace(self, limit=n)


def _offset(self: SelectQuery, n: int) -> SelectQuery:
    return replace(self, offset=n)


def _distinct(self: SelectQuery) -> SelectQuery:
    return replace(self, distinct=True)


def _as(self: SelectQuery, alias: str) -> Subquery:
    return Subquery(self, alias)


def _hydrate(self: SelectQuery, target: HydrationTarget) -> SelectQuery:
    return replace(self, hydrate=target)


SelectQuery.FROM = _from  # type: ignore[attr-defined]
SelectQuery.JOIN = _join  # type: ignore[attr-defined]
SelectQuery.LEFT_JOIN = _left_join  # type: ignore[attr-defined]
SelectQuery.WHERE = _where  # type: ignore[attr-defined]
SelectQuery.GROUP_BY = _group_by  # type: ignore[attr-defined]
SelectQuery.HAVING = _having  # type: ignore[attr-defined]
SelectQuery.ORDER_BY = _order_by  # type: ignore[attr-defined]
SelectQuery.LIMIT = _limit  # type: ignore[attr-defined]
SelectQuery.OFFSET = _offset  # type: ignore[attr-defined]
SelectQuery.DISTINCT = _distinct  # type: ignore[attr-defined]
SelectQuery.AS = _as  # type: ignore[attr-defined]
SelectQuery.HYDRATE = _hydrate  # type: ignore[attr-defined]


class InsertBuilder:
    def __init__(self, table: Table):
        self.table = table

    def VALUES(self, **values: Any) -> InsertQuery:
        return InsertQuery(self.table, tuple(values.items()))


class UpdateBuilder:
    def __init__(self, table: Table):
        self.table = table

    def SET(self, **values: Any) -> "UpdateWhereBuilder":
        return UpdateWhereBuilder(self.table, tuple(values.items()))


class UpdateWhereBuilder:
    def __init__(self, table: Table, values: Tuple[Tuple[str, Any], ...]):
        self.table = table
        self.values = values

    def WHERE(self, *predicates: Predicate) -> UpdateQuery:
        return UpdateQuery(self.table, self.values, tupled(predicates))


class DeleteBuilder:
    def __init__(self, table: Table):
        self.table = table

    def WHERE(self, *predicates: Predicate) -> DeleteQuery:
        return DeleteQuery(self.table, tupled(predicates))
