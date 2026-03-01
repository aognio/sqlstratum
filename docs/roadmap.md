# Roadmap

SQLStratum is in early development. SQLite is the most mature backend and MySQL has initial runtime
support. The roadmap below is incremental, with explicit layering preserved (AST/compile, runner, hydration).

## Near-Term Releases

### 0.2.2 (Patch)
- Harden release and packaging workflows (build/check/publish reliability).
- Increase deterministic compile test coverage for complex queries.
- Improve docs for deprecation policy and migration paths.

### 0.3.0 (Shipped)
- Added dialect registry and built-in compiler adapters (`sqlite`, `mysql`).
- Added optional MySQL runners (`PyMySQL` sync and `asyncmy` async) with connector-specific extras.
- Expanded compile/test coverage for multi-dialect determinism.

### 0.3.1 (Shipped)
- Added `SQLiteRunner` canonical naming with `Runner` compatibility alias.
- Added URL-based connection support for SQLite and MySQL runners.
- Added strict connection option validation and expanded docs/test coverage.

### 0.3.2 (Shipped)
- Added explicit dialect wrappers (`using_sqlite`, `using_mysql`).
- Added dialect-binding guardrails and chain-friendly wrapper behavior.
- Expanded interaction test coverage for wrappers with compile, runners, and hydration.

### 0.3.x (Current line)
- Added portable predicates (`IN`, `NOT IN`, `BETWEEN`, `NOT BETWEEN`, `EXISTS`, `NOT EXISTS`).
- Added set operations (`UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`).
- Added ordering API support for:
  - primary style: `ORDER_BY(DESC(...), ASC(...))`
  - fluent style: `.ORDER_BY(...).ASC().THEN(...).DESC()`
- Added dialect capability contract tests and opt-in real MySQL integration tests.

## Multi-Dialect Start

### 0.4.0 (Feature, PostgreSQL Compiler MVP)
- Add PostgreSQL compiler adapter with deterministic parameter binding.
- Add dialect capability matrix updates and compile snapshot tests for PostgreSQL.
- Preserve architecture boundaries:
  - AST/compile deterministic core
  - runner execution boundary
  - hydration post-execution layer

### 0.5.0 (Feature, MySQL Hardening)
- Expand MySQL execution integration coverage across real server scenarios.
- Improve connector parity and error semantics across sync/async runners.
- Continue keeping dialect-specific behavior out of core abstractions.

## Longer-Term
- Explore optional runtime packages per backend while keeping `sqlstratum` as stable facade.
- Evaluate complementary DDL/migrations library aligned with SQLStratum design principles.
- Strengthen plugin contracts for dialect and integration extensions.

This roadmap will evolve with production feedback and contributor capacity.
