# AGENTS

## Project Intent
SQLStratum is a modern, typed, deterministic SQL query builder / compiler + runner + hydration pipeline.
It is designed as a foundation layer for apps and ORMs, with a focus on determinism, composability, and
predictable parameter binding.

## Non-Goals
- Not an ORM (no identity map, relationships, lazy loading)
- Not a migrations/DDL system
- Not a full database abstraction layer for every backend yet (SQLite first)
- Not a SQL string templating engine

## Repo Map (Current)
- `sqlstratum/ast.py`: core AST nodes and compiled result types
- `sqlstratum/expr.py`: expressions, predicates, aggregates, ordering
- `sqlstratum/meta.py`: `Table`/`Column` metadata and column access
- `sqlstratum/dsl.py`: public DSL constructors and chaining helpers
- `sqlstratum/compile.py`: AST -> SQL + params compilation
- `sqlstratum/runner.py`: SQLite execution boundary + transactions
- `sqlstratum/hydrate.py`: hydration targets + projection key rules
- `tests/`: compile, hydration, runner, and SQLite integration tests
- `examples/`: minimal usage demos

## Development Workflow
- Branch-per-release convention: `release/0.1.x-<short-name>`
- Keep PRs focused: one feature or bug fix per branch
- Update/add tests with every change (no exceptions)
- Avoid expanding scope beyond the roadmap
- Favor small, verifiable steps

## Invariants (Do Not Break)
- Deterministic SQL output for identical AST inputs
- Parameter binding must be safe; never interpolate raw user strings
- Aliasing rules: avoid ambiguous columns; encourage explicit aliases in joins
- Runner is the execution boundary; avoid leaking DB concerns into AST/compile layers

## Testing Expectations
- Run tests with `python -m unittest`
- Add compile snapshot tests and SQLite execution tests when relevant
- For bugs, add minimal repro tests with expected compiled SQL + params

## Debugging Ergonomics
- `SQLSTRATUM_DEBUG=1` enables per-query logging at the Runner boundary (requires logging level DEBUG)
