# SQLStratum v0.1 Notes

## Design decisions
- Immutable AST: query and expression nodes are frozen dataclasses, and chaining returns new objects.
- Deterministic compilation: parameters are named `:p0`, `:p1`, ... in traversal order.
- Identifier quoting: double quotes for all table/column/alias identifiers.
- Hydration is separate from compilation: the runner applies hydration based on projection keys.
- Collision policy: duplicate projection keys raise a `HydrationError`; use `AS()` to disambiguate.
- Column access style: use `table.c.column` to avoid name collisions with `Table` attributes.

## Limitations
- SQLite-only dialect.
- No DDL AST (DDL runs via `Runner.exec_ddl`).
- No ORMs, schema reflection, migrations, or async support.
- Functions without `AS()` cannot be hydrated.
