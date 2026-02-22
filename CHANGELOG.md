# Changelog

## 0.3.0 - 2026-02-22
### Added
- Added a dialect registry (`sqlstratum/dialects/`) and compiler dispatch in `compile(...)`.
- Added built-in MySQL compiler adapter (compile-only MVP) with deterministic named parameters.
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
