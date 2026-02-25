# Dialect Wrappers

Use explicit wrappers when a query should be tied to a specific dialect.

- `using_sqlite(query)` binds query intent to SQLite.
- `using_mysql(query)` binds query intent to MySQL.

This keeps the core DSL portable while making dialect-specific intent explicit.

## Examples

```python
from sqlstratum import SELECT, compile
from sqlstratum.mysql import using_mysql

q = using_mysql(SELECT(users.c.id, users.c.email).FROM(users))
compiled = compile(q, dialect="mysql")
```

Wrappers are chain-friendly, so query-builder methods still work after wrapping:

```python
q = using_mysql(SELECT(users.c.id).FROM(users)).WHERE(users.c.id == 1)
```

```python
from sqlstratum import SELECT, compile
from sqlstratum.sqlite import using_sqlite, TOTAL

q = using_sqlite(SELECT(TOTAL(users.c.id).AS("n")).FROM(users))
compiled = compile(q)  # defaults to sqlite
```

## Guardrails

If a wrapped query is compiled with a different dialect, SQLStratum raises
`UnsupportedDialectFeatureError` with a clear hint.

Example:

```python
compile(using_sqlite(query), dialect="mysql")
# UnsupportedDialectFeatureError: query bound to dialect 'sqlite'
```

## Why wrappers

- Prevents accidental cross-dialect usage.
- Makes backend-specific behavior visible at call-site.
- Scales cleanly as more dialects are added.

## DX And Extensibility

- Explicit intent at call-site: `using_sqlite(...)` and `using_mysql(...)` immediately show when a query is dialect-specific.
- Early, clear failures: mismatched compile dialects fail fast with actionable `UnsupportedDialectFeatureError` messages.
- Cleaner portable core: shared DSL stays focused on cross-dialect constructs, while backend-specific features stay out of default paths.
- Better discoverability: dialect features live in predictable namespaces (`sqlstratum.sqlite`, `sqlstratum.mysql`).
- Lower debugging cost: incompatibilities surface at compile boundary, not later during runtime debugging in app code.
- Consistent growth model: new dialect wrappers can follow the same pattern (`using_postgres`, `using_sqlserver`, etc.) without redesigning the public API.
- Easier team onboarding: developers can quickly distinguish portable queries from backend-bound queries.
- Preserves layering: wrappers bind dialect intent only; AST/compile determinism and runner execution boundaries remain unchanged.
