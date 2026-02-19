# Changelog

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
