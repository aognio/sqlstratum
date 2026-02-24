# SQLStratum

<p align="center">
  <img src="https://raw.githubusercontent.com/aognio/sqlstratum/main/assets/images/SQLStratum-Logo-500x500-transparent.png" alt="SQLStratum logo" />
</p>

SQLStratum is a modern, typed, deterministic SQL query builder and compiler for Python with execution
runners and a hydration pipeline. It exists to give applications and ORMs a reliable foundation
layer with composable SQL, predictable parameter binding, and explicit execution boundaries.

## Key Features
- Deterministic compilation: identical AST inputs produce identical SQL + params
- Typed, composable DSL for SELECT/INSERT/UPDATE/DELETE
- Safe parameter binding (no raw interpolation)
- Hydration targets for structured results
- SQLite execution via `Runner` plus optional MySQL sync/async runners
- Dialect-aware compilation entrypoint (`compile(..., dialect="sqlite" | "mysql")`)
- Optional MySQL runners for sync (`PyMySQL`) and async (`asyncmy`) execution
- Testable compiled output and runtime behavior

## Non-Goals
- Not an ORM (no identity map, relationships, lazy loading)
- Not a migrations/DDL system
- Not a full database abstraction layer for every backend yet (SQLite is most mature; MySQL is early support)
- Not a SQL string templating engine

SQLStratum focuses on queries. DDL statements such as `CREATE TABLE` or `ALTER TABLE` are intended to
live in a complementary library with similar design goals that is currently in the works.

## Quickstart
```python
import sqlite3

from sqlstratum import SELECT, INSERT, Table, col, SQLiteRunner

users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
)

conn = sqlite3.connect(":memory:")
runner = SQLiteRunner(conn)
runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, active INTEGER)")

runner.execute(INSERT(users).VALUES(email="a@b.com", active=1))
runner.execute(INSERT(users).VALUES(email="c@d.com", active=0))

q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(users.c.active.is_true())
    .hydrate(dict)
)

rows = runner.fetch_all(q)
print(rows)
```

## Why `Table` objects?
SQLStratum’s `Table` objects are the schema anchor for the typed, deterministic query builder. They
provide column metadata and a stable namespace for column access, which enables predictable SQL
generation and safe parameter binding. They also support explicit aliasing to avoid ambiguous column
names in joins.

## Project Structure
- AST: immutable query nodes in `sqlstratum/ast.py`
- Compiler: SQL + params generation in `sqlstratum/compile.py`
- Dialects: compiler adapters and registry in `sqlstratum/dialects/`
- Runners: SQLite in `sqlstratum/runner.py`, MySQL sync in `sqlstratum/runner_mysql.py`, MySQL async in `sqlstratum/runner_mysql_async.py`
- Hydration: projection rules and targets in `sqlstratum/hydrate/`

## Dialect Compilation
`compile(query, dialect=...)` now dispatches through a dialect registry.

Supported built-ins:
- `sqlite`: full support used by `SQLiteRunner` (with `Runner` compatibility alias)
- `mysql`: compiler support plus optional runtime runners (`MySQLRunner`, `AsyncMySQLRunner`)

Example:
```python
compiled = compile(
    SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1),
    dialect="mysql",
)
print(compiled.sql)
# SELECT `users`.`id`, `users`.`email` FROM `users` WHERE `users`.`id` = %(p0)s
```

## MySQL Runners (Optional)
Install one or both connectors:
```bash
pip install sqlstratum[pymysql]
pip install sqlstratum[asyncmy]
# or both
pip install sqlstratum[mysql]
```

Synchronous runner (`PyMySQL`):
```python
from sqlstratum import MySQLRunner

runner = MySQLRunner.connect(
    host="127.0.0.1",
    port=3306,
    user="app",
    password="secret",
    database="appdb",
)
rows = runner.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
```

Or with URL:
```python
runner = MySQLRunner.connect(url="mysql+pymysql://app:secret@127.0.0.1:3306/appdb")
```

Asynchronous runner (`asyncmy`):
```python
from sqlstratum import AsyncMySQLRunner

runner = await AsyncMySQLRunner.connect(
    host="127.0.0.1",
    port=3306,
    user="app",
    password="secret",
    database="appdb",
)
rows = await runner.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
```

Or with URL:
```python
runner = await AsyncMySQLRunner.connect(url="mysql+asyncmy://app:secret@127.0.0.1:3306/appdb")
```

SQLite URL form:
```python
from sqlstratum import SQLiteRunner

runner = SQLiteRunner.connect(url="sqlite:///app.db")
# or in-memory
runner = SQLiteRunner.connect(url="sqlite:///:memory:")
```

Connection config rule: provide either a URL or individual connection parameters, never both in one call.
Currently supported URL forms:
- SQLite: `sqlite:///relative/path.db`, `sqlite:////absolute/path.db`, `sqlite:///:memory:`
- MySQL sync: `mysql://user:pass@host:3306/db` or `mysql+pymysql://...`
- MySQL async: `mysql://user:pass@host:3306/db` or `mysql+asyncmy://...`

URL query parameters/fragments are intentionally rejected for now to keep connection parsing explicit and deterministic.

| URL | Sync MySQLRunner | Async AsyncMySQLRunner | SQLiteRunner |
|---|---|---|---|
| `sqlite:///:memory:` | No | No | Yes |
| `sqlite:///data/app.db` | No | No | Yes |
| `sqlite:////var/lib/app.db` | No | No | Yes |
| `mysql://user:pass@127.0.0.1:3306/cities_db` | Yes | Yes | No |
| `mysql+pymysql://user:pass@127.0.0.1:3306/cities_db` | Yes | No | No |
| `mysql+asyncmy://user:pass@127.0.0.1:3306/cities_db` | No | Yes | No |

Both runners execute through the same SQL AST + compiler pipeline. Compilation remains deterministic;
execution and hydration stay at the runner boundary.

## SQL Debugging
SQLStratum can log executed SQL statements (compiled SQL + parameters + duration), but logging is
intentionally gated to avoid noisy output in production. Debug output requires two conditions:
- Environment variable gate: `SQLSTRATUM_DEBUG` must be truthy (`"1"`, `"true"`, `"yes"`,
  case-insensitive).
- Logger gate: the `sqlstratum` logger must be DEBUG-enabled.

Why it does not work by default: Python logging defaults to WARNING level, so even if
`SQLSTRATUM_DEBUG=1` is set, DEBUG logs will not appear unless logging is configured.

To enable debugging in a development app:

Step 1 - set the environment variable:
```
SQLSTRATUM_DEBUG=1
```

Step 2 - configure logging early in the app:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
# or
logging.getLogger("sqlstratum").setLevel(logging.DEBUG)
```

Output looks like:
```
SQL: <compiled sql> | params={<sorted params>} | duration_ms=<...>
```

Architectural intent: logging happens at the Runner boundary (after execution). AST building and
compilation remain deterministic and side-effect free, preserving separation of concerns.

## Pydantic Hydration (Optional)
SQLStratum does not depend on Pydantic, but it provides an optional hydration adapter for Pydantic
v2 models.

Install:
```
pip install sqlstratum[pydantic]
```

Example:
```python
from pydantic import BaseModel
from sqlstratum.hydrate.pydantic import hydrate_model, using_pydantic

class User(BaseModel):
    id: int
    email: str

row = {"id": "1", "email": "a@b.com"}
user = hydrate_model(User, row)

q = using_pydantic(
    SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1)
).hydrate(User)
user_row = runner.fetch_one(q)
```

## Logo Inspiration

Vinicunca (Rainbow Mountain) in Peru’s Cusco Region — a high-altitude day hike from
Cusco at roughly 5,036 m (16,500 ft). See [Vinicunca](https://en.wikipedia.org/wiki/Vinicunca) for
background.

## Versioning / Roadmap
Current version: `0.3.1`.
Design notes and current limitations are tracked in `NOTES.md`. Planned release milestones,
including PostgreSQL and cross-dialect parity work, are documented in `docs/roadmap.md`.

## Authorship
[Antonio Ognio](https://github.com/aognio/) is the maintainer and author of SQLStratum. ChatGPT is used for brainstorming,
architectural thinking, documentation drafting, and project management advisory. Codex (CLI/agentic
coding) is used to implement many code changes under Antonio's direction and review. The maintainer
reviews and curates changes; AI tools are assistants, not owners, and accountability remains with the
maintainer.

## License
MIT License.

## Contributing
PRs are welcome. Please read `CONTRIBUTING.md` for the workflow and expectations.

## Documentation
Install docs dependencies:
```bash
python -m pip install -r docs/requirements.txt
```

Run the local docs server:
```bash
mkdocs serve
```

Build the static site:
```bash
mkdocs build --clean
```

Read the Docs will build documentation automatically once the repository is imported.

## Release Automation
Install dev dependencies:
```bash
python -m pip install -e ".[dev]"
```

Run the full release pipeline:
```bash
poe release
```

This runs, in order:
- `python -m unittest`
- `python -m build --no-isolation`
- `python -m twine check dist/*`
- `python -m twine upload dist/*`

For a non-publishing verification pass:
```bash
poe release-dry-run
```
