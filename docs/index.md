# SQLStratum

SQLStratum is a modern, typed, deterministic SQL query builder and compiler for Python with
execution runners and a hydration pipeline. It exists to give applications and ORMs a reliable foundation
layer with composable SQL, predictable parameter binding, and explicit execution boundaries.

!!! info "Latest release"
    `0.4.0` expands the query DSL with portable predicates, set operations, explicit ordering helpers,
    stronger dialect guardrails, and broader MySQL runtime coverage. Start with
    [Latest release](latest-release.md) for the narrative walkthrough.

## Highlights
- Deterministic SQL compilation for identical AST inputs
- Typed, composable DSL for SELECT/INSERT/UPDATE/DELETE
- Portable predicates: `IN`, `NOT IN`, `BETWEEN`, `NOT BETWEEN`, `EXISTS`, `NOT EXISTS`
- Set operations: `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`
- Safe parameter binding (no raw interpolation)
- Hydration targets for structured results
- SQLite runner plus initial MySQL sync/async runners
- Dialect-aware compilation (`sqlite`, `mysql`)
- Explicit dialect capability contract and guardrails
- Opt-in real MySQL integration test coverage for runners

## What's New In 0.4.0

### Richer query composition
- Portable predicates now cover `IN`, `NOT IN`, `BETWEEN`, `NOT BETWEEN`, `EXISTS`, and `NOT EXISTS`.
- Set queries now support `UNION`, `UNION ALL`, `INTERSECT`, and `EXCEPT`.
- Ordering is more explicit through `ASC(...)`, `DESC(...)`, and the fluent `.ASC()/.DESC().THEN(...)` chain.

### Stronger dialect behavior
- `RIGHT_JOIN` is available with dialect guardrails.
- `FULL OUTER JOIN` remains explicit and guarded instead of silently compiling invalid SQL.
- The SQL capability contract is documented and tested directly.

### Better MySQL ergonomics
- Sync and async MySQL runners are documented as part of the main story.
- Optional MySQL extras now cover common MySQL 8 authentication setups.
- Real MySQL integration coverage validates more than simple connection smoke tests.

## Recommended Reading Path

If you are new to the project:
- [Getting started](getting-started.md)
- [Latest release](latest-release.md)
- [SQL profile](sql-profile.md)

If you are evaluating dialect and runtime behavior:
- [Dialect wrappers](dialect-wrappers.md)
- [Testing](testing.md)
- [Debugging](debugging.md)

Get started in a few minutes:
- [Getting started](getting-started.md)
- [Latest release](latest-release.md)
- [SQL profile](sql-profile.md)
- [Dialect wrappers](dialect-wrappers.md)
- [Hydration](hydration.md)
- [Debugging](debugging.md)
- [Testing](testing.md)
