# SQLStratum

SQLStratum is a modern, typed, deterministic SQL query builder and compiler for Python with a
SQLite runner and hydration pipeline. It exists to give applications and ORMs a reliable foundation
layer with composable SQL, predictable parameter binding, and explicit execution boundaries.

## Highlights
- Deterministic SQL compilation for identical AST inputs
- Typed, composable DSL for SELECT/INSERT/UPDATE/DELETE
- Safe parameter binding (no raw interpolation)
- Hydration targets for structured results
- SQLite-first execution via a small Runner API

Get started in a few minutes:
- [Getting started](getting-started.md)
- [Hydration](hydration.md)
- [Debugging](debugging.md)
