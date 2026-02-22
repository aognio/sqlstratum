# Roadmap

SQLStratum is in early development and currently targets SQLite. The roadmap below is intended to be
practical and incremental, with explicit layering preserved (AST/compile, runner, hydration).

## Near-Term Releases

### 0.2.2 (Patch)
- Harden release and packaging workflows (build/check/publish reliability).
- Increase deterministic compile test coverage for complex queries.
- Improve docs for deprecation policy and migration paths.

### 0.3.0 (Feature)
- Introduce dialect registry and built-in compiler adapters (`sqlite`, `mysql` compile-only MVP).
- Add optional MySQL runners (`PyMySQL` sync and `asyncmy` async) with connector-specific extras.
- Expand compile snapshot coverage for multi-dialect determinism.

### 0.3.1 (Patch)
- Tighten error messaging for unsupported dialect features.
- Add more guardrails around public API and deprecation warnings.

## Multi-Dialect Start

### 0.4.0 (Feature, PostgreSQL MVP Start)
- Introduce PostgreSQL dialect compiler MVP behind dialect namespace.
- Focus on SELECT/INSERT/UPDATE/DELETE parity for core DSL constructs.
- Keep hydration and runner boundaries unchanged.

### 0.4.1 (Patch)
- Add PostgreSQL compile snapshots and compatibility fixes.
- Improve docs and migration guidance for early adopters.

### 0.5.0 (Feature, MySQL Runtime Start)
- Add a MySQL runner boundary once connection/transaction semantics are validated.
- Extend MySQL coverage from compile-only to execution integration tests.
- Continue keeping dialect-specific behavior out of core abstractions.

## Longer-Term
- Explore optional runtime packages per backend while keeping `sqlstratum` as stable facade.
- Evaluate complementary DDL/migrations library aligned with SQLStratum design principles.
- Strengthen plugin contracts for dialect and integration extensions.

This roadmap will evolve with production feedback and contributor capacity.
