# Changelog

## Unreleased
### Added
- Added portable predicate support for:
  - `IN` / `NOT IN`
  - `BETWEEN` / `NOT BETWEEN`
  - `EXISTS` / `NOT EXISTS`
- Added set operations:
  - `UNION`
  - `UNION ALL`
  - `INTERSECT`
  - `EXCEPT`
- Added explicit ordering wrapper functions:
  - `ASC(expr)`
  - `DESC(expr)`
- Added SQL profile documentation page (`docs/sql-profile.md`).
- Added dialect capability contract tests (`tests/test_dialect_capabilities_contract.py`).
- Added opt-in real MySQL integration tests for sync/async runners (`tests/test_mysql_integration_real.py`).
- Added GitHub Actions CI workflow to run tests, docs build, package build, and `twine check`.

### Changed
- Added `RIGHT_JOIN` and `FULL_JOIN` DSL APIs with dialect capability guardrails.
- Updated docs to make `ORDER_BY(DESC(...), ASC(...))` the primary ordering style.
- Enforced MySQL `OFFSET`-without-`LIMIT` guardrail consistently for set queries.
- Documented cross-dialect capability contract in README and SQL profile docs.

## 0.3.2 - 2026-02-25
### Added
- Added explicit dialect wrappers:
  - `using_sqlite(...)` in `sqlstratum.sqlite`
  - `using_mysql(...)` in `sqlstratum.mysql`
- Added dialect binding utilities to preserve wrapper intent through compile and runner boundaries.
- Added SQLite extension helpers in explicit namespace:
  - `TOTAL(...)`
  - `GROUP_CONCAT(...)`
- Added a dedicated docs page for wrapper behavior and guardrails (`docs/dialect-wrappers.md`).

### Changed
- Made wrapped queries chain-friendly (query methods continue to work after wrapping).
- Added clear errors for conflicting nested wrapper bindings.
- Hardened MySQL compiler guardrails for SQLite-only aggregates.
- Expanded interaction test coverage across wrappers, compile, runners, and hydration.

## 0.3.1 - 2026-02-24
### Added
- Added connection URL parsing helpers for SQLite and MySQL.
- Added connection URL support for:
  - `SQLiteRunner.connect(path=...|url=...)`
  - `MySQLRunner.connect(...)`
  - `AsyncMySQLRunner.connect(...)`
- Added validation matrix documentation for accepted/rejected URL forms.

### Changed
- Added `SQLiteRunner` as the canonical SQLite runner name and kept `Runner` as a compatibility alias.
- Enforced connection configuration exclusivity: callers must provide either URL or individual parameters, not both.
- Improved URL validation and error messaging (missing auth/database, invalid scheme/port, unsupported query/fragment).

## 0.3.0 - 2026-02-22
### Added
- Added a dialect registry (`sqlstratum/dialects/`) and compiler dispatch in `compile(...)`.
- Added built-in MySQL compiler adapter with deterministic named parameters.
- Added structured dialect errors via `UnsupportedDialectFeatureError`.
- Added optional MySQL runners:
  - `MySQLRunner` (sync, `PyMySQL`)
  - `AsyncMySQLRunner` (async, `asyncmy`)
- Added optional dependency groups: `pymysql`, `asyncmy`, and `mysql`.

### Changed
- Moved SQLite compiler implementation under `sqlstratum/dialects/sqlite/`.
- Exposed `list_dialects()` in the top-level API.

## 0.2.2
### Added
- Added compile determinism stress tests covering repeated compilation of complex queries.

### Changed
- Aligned project metadata/docs to `0.2.2`.

## 0.2.1
### Changed
- Updated release automation to run tests before build/upload.
- Added a dry-run release workflow (`poe release-dry-run`) for non-publishing validation.
- Switched package discovery to `setuptools` auto-find (`sqlstratum*`) to prevent missed subpackages.

### Fixed
- Aligned project metadata/docs to `0.2.1`.

## 0.2.0
- Release target prepared.
- `0.1.1` is yanked on PyPI due to incorrect semantic versioning for feature-level changes.
- Users should migrate to `0.2.0`.

## 0.1.1
> This release is yanked on PyPI.

- Naming discipline: hydration helpers are now lowercase to reflect application-layer concerns.
- `SelectQuery.HYDRATE(...)` is now `SelectQuery.hydrate(...)`.
- ALL CAPS identifiers are reserved strictly for SQL DSL constructs.
- Added optional Pydantic v2 hydration adapter (`sqlstratum.hydrate.pydantic`).
