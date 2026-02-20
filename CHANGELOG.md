# Changelog

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
