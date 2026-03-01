# SQL Profile

This page summarizes the currently supported portable SQL surface.

## Portable Core (Implemented)
- DML: `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- Joins: `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN` (dialect-dependent)
- Filters: `WHERE`, `HAVING`
- Grouping/Sorting: `GROUP BY`, `ORDER BY`
- Pagination: `LIMIT`, `OFFSET`
- Predicates:
  - comparison: `=`, `!=`, `<`, `<=`, `>`, `>=`
  - null checks: `IS NULL`, `IS NOT NULL`
  - logical: `AND`, `OR`, `NOT`
  - set/range: `IN`, `NOT IN`, `BETWEEN`, `NOT BETWEEN`
  - existence: `EXISTS`, `NOT EXISTS`
- Set operations: `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`
- Portable aggregates: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`

## Dialect-Specific
- SQLite-only (explicit wrapper recommended): `TOTAL`, `GROUP_CONCAT`

## Dialect Notes
- `FULL OUTER JOIN`:
  - MySQL: not supported (compile-time error)
  - SQLite: currently guarded as unsupported in this profile
- `RIGHT JOIN`:
  - MySQL: supported
  - SQLite: guarded as unsupported in this profile

## Capability Contract Matrix
This matrix reflects compile-time contract tests in `tests/test_dialect_capabilities_contract.py`.
For execution-level checks on real MySQL servers, see [Testing](testing.md#real-mysql-integration-tests-opt-in).

| Feature | SQLite | MySQL | Notes |
|---|---|---|---|
| Portable predicates (`IN`, `BETWEEN`, `EXISTS`) | Yes | Yes | Compiles in both built-in dialects |
| `RIGHT JOIN` | No | Yes | SQLite raises `UnsupportedDialectFeatureError` |
| `FULL OUTER JOIN` | No | No | Explicitly rejected in both dialects |
| `TOTAL(...)` | Yes | No | SQLite extension aggregate |
| `GROUP_CONCAT(...)` | Yes | No | SQLite extension aggregate in SQLStratum profile |
| `OFFSET` without `LIMIT` | Yes | No | MySQL rejects for `SELECT` and set queries |

## Ordering Styles
Primary style:

```python
from sqlstratum import ASC, DESC

q = SELECT(users.c.id).FROM(users).ORDER_BY(DESC(users.c.created_at), ASC(users.c.id))
```

Alternative fluent style:

```python
q = SELECT(users.c.id).FROM(users).ORDER_BY(users.c.created_at).DESC().THEN(users.c.id).ASC()
```

Both styles can be mixed.
