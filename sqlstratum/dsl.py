"""Public DSL constructors and query chaining."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Tuple

from .ast import DeleteQuery, InsertQuery, Join, SelectQuery, SetQuery, Subquery, UpdateQuery, tupled
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
        hydration=None,
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


def _right_join(self: SelectQuery, source: Source, ON: Predicate) -> SelectQuery:
    joins = self.joins + (Join("RIGHT", source, ON),)
    return replace(self, joins=joins)


def _full_join(self: SelectQuery, source: Source, ON: Predicate) -> SelectQuery:
    joins = self.joins + (Join("FULL", source, ON),)
    return replace(self, joins=joins)


def _where(self: SelectQuery, *predicates: Predicate) -> SelectQuery:
    where = self.where + tupled(predicates)
    return replace(self, where=where)


def _group_by(self: SelectQuery, *cols: Expression) -> SelectQuery:
    return replace(self, group_by=self.group_by + tupled(cols))


def _having(self: SelectQuery, *predicates: Predicate) -> SelectQuery:
    return replace(self, having=self.having + tupled(predicates))


class _OrderByPending:
    def __init__(self, query: Any, expr: Expression):
        self._query = query
        self._expr = expr

    def __sqlstratum_order_pending__(self) -> bool:
        return True

    def ASC(self) -> "_OrderByChain":
        spec = OrderSpec(self._expr, "ASC")
        return _OrderByChain(replace(self._query, order_by=self._query.order_by + (spec,)))

    def DESC(self) -> "_OrderByChain":
        spec = OrderSpec(self._expr, "DESC")
        return _OrderByChain(replace(self._query, order_by=self._query.order_by + (spec,)))


class _OrderByChain:
    def __init__(self, query: Any):
        self._query = query

    def __sqlstratum_query__(self) -> SelectQuery:
        return self._query

    def THEN(self, expr: Any) -> Any:
        if isinstance(expr, OrderSpec):
            return _OrderByChain(replace(self._query, order_by=self._query.order_by + (expr,)))
        return _OrderByPending(self._query, expr)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._query, name)


def _order_by(self: SelectQuery, *items: Any) -> Any:
    if not items:
        raise ValueError("ORDER_BY requires at least one expression or OrderSpec")

    specs: Tuple[OrderSpec, ...] = tuple()
    pending_expr: Any = None

    for idx, item in enumerate(items):
        is_last = idx == len(items) - 1
        if isinstance(item, OrderSpec):
            specs = specs + (item,)
            continue
        if not is_last:
            raise ValueError(
                "Unqualified ORDER_BY expressions are only allowed as the last item. "
                "Use .ASC()/.DESC() for earlier items."
            )
        pending_expr = item

    query = replace(self, order_by=self.order_by + specs)
    if pending_expr is None:
        return query
    return _OrderByPending(query, pending_expr)


def _limit(self: SelectQuery, n: int) -> SelectQuery:
    return replace(self, limit=n)


def _offset(self: SelectQuery, n: int) -> SelectQuery:
    return replace(self, offset=n)


def _distinct(self: SelectQuery) -> SelectQuery:
    return replace(self, distinct=True)


def _as(self: SelectQuery, alias: str) -> Subquery:
    return Subquery(self, alias)


def _hydrate(self: SelectQuery, target: HydrationTarget) -> SelectQuery:
    return replace(self, hydration=target)


def _union(self: Any, other: Any) -> SetQuery:
    return SetQuery(self, "UNION", other, order_by=tuple(), limit=None, offset=None, hydration=None)


def _union_all(self: Any, other: Any) -> SetQuery:
    return SetQuery(self, "UNION ALL", other, order_by=tuple(), limit=None, offset=None, hydration=None)


def _intersect(self: Any, other: Any) -> SetQuery:
    return SetQuery(self, "INTERSECT", other, order_by=tuple(), limit=None, offset=None, hydration=None)


def _except(self: Any, other: Any) -> SetQuery:
    return SetQuery(self, "EXCEPT", other, order_by=tuple(), limit=None, offset=None, hydration=None)


def _set_limit(self: SetQuery, n: int) -> SetQuery:
    return replace(self, limit=n)


def _set_offset(self: SetQuery, n: int) -> SetQuery:
    return replace(self, offset=n)


def _set_hydrate(self: SetQuery, target: HydrationTarget) -> SetQuery:
    return replace(self, hydration=target)


SelectQuery.FROM = _from  # type: ignore[attr-defined]
SelectQuery.JOIN = _join  # type: ignore[attr-defined]
SelectQuery.LEFT_JOIN = _left_join  # type: ignore[attr-defined]
SelectQuery.RIGHT_JOIN = _right_join  # type: ignore[attr-defined]
SelectQuery.FULL_JOIN = _full_join  # type: ignore[attr-defined]
SelectQuery.WHERE = _where  # type: ignore[attr-defined]
SelectQuery.GROUP_BY = _group_by  # type: ignore[attr-defined]
SelectQuery.HAVING = _having  # type: ignore[attr-defined]
SelectQuery.ORDER_BY = _order_by  # type: ignore[attr-defined]
SelectQuery.LIMIT = _limit  # type: ignore[attr-defined]
SelectQuery.OFFSET = _offset  # type: ignore[attr-defined]
SelectQuery.DISTINCT = _distinct  # type: ignore[attr-defined]
SelectQuery.AS = _as  # type: ignore[attr-defined]
SelectQuery.hydrate = _hydrate  # type: ignore[attr-defined]
SelectQuery.UNION = _union  # type: ignore[attr-defined]
SelectQuery.UNION_ALL = _union_all  # type: ignore[attr-defined]
SelectQuery.INTERSECT = _intersect  # type: ignore[attr-defined]
SelectQuery.EXCEPT = _except  # type: ignore[attr-defined]

SetQuery.ORDER_BY = _order_by  # type: ignore[attr-defined]
SetQuery.LIMIT = _set_limit  # type: ignore[attr-defined]
SetQuery.OFFSET = _set_offset  # type: ignore[attr-defined]
SetQuery.hydrate = _set_hydrate  # type: ignore[attr-defined]
SetQuery.UNION = _union  # type: ignore[attr-defined]
SetQuery.UNION_ALL = _union_all  # type: ignore[attr-defined]
SetQuery.INTERSECT = _intersect  # type: ignore[attr-defined]
SetQuery.EXCEPT = _except  # type: ignore[attr-defined]


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
