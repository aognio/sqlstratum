# Changelog

## 0.1.1
- Naming discipline: hydration helpers are now lowercase to reflect application-layer concerns.
- `SelectQuery.HYDRATE(...)` is now `SelectQuery.hydrate(...)`.
- ALL CAPS identifiers are reserved strictly for SQL DSL constructs.
- Added optional Pydantic v2 hydration adapter (`sqlstratum.hydrate.pydantic`).
