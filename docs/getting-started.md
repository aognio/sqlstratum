# Getting Started

## Install
```bash
pip install sqlstratum
```

## First Query
```python
import sqlite3

from sqlstratum import SELECT, Table, col, SQLiteRunner

users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
)

conn = sqlite3.connect(":memory:")
runner = SQLiteRunner(conn)
runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, active INTEGER)")

q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(users.c.active.is_true())
    .hydrate(dict)
)

rows = runner.fetch_all(q)
print(rows)
```

## Compile For Another Dialect
SQLStratum keeps execution SQLite-first today, but you can compile SQL for supported dialects.

```python
from sqlstratum import compile

compiled = compile(
    SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1),
    dialect="mysql",
)
print(compiled.sql)
```

## Optional MySQL Execution
Install optional connectors as needed:

```bash
pip install sqlstratum[pymysql]
pip install sqlstratum[asyncmy]
```

Then use `MySQLRunner` (sync) or `AsyncMySQLRunner` (async) for query execution.

```python
from sqlstratum import SELECT, Table, col, MySQLRunner

users = Table("users", col("id", int), col("email", str))

runner = MySQLRunner.connect(
    host="127.0.0.1",
    port=3306,
    user="orm_admin",
    password="OrmAdmin456!",
    database="cities_db",
)

rows = runner.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
print(rows)
```

URL form is also supported (and mutually exclusive with individual parameters):
```python
runner = MySQLRunner.connect(url="mysql+pymysql://orm_admin:OrmAdmin456!@127.0.0.1:3306/cities_db")
```

Supported URL forms:
- SQLite: `sqlite:///relative/path.db`, `sqlite:////absolute/path.db`, `sqlite:///:memory:`
- MySQL sync: `mysql://...` or `mysql+pymysql://...`
- MySQL async: `mysql://...` or `mysql+asyncmy://...`

Note: URL query parameters/fragments are not supported yet.

### URL Validation Matrix
| URL | Sync MySQLRunner | Async AsyncMySQLRunner | SQLiteRunner | Notes |
|---|---|---|---|---|
| `sqlite:///:memory:` | No | No | Yes | In-memory SQLite |
| `sqlite:///data/app.db` | No | No | Yes | Relative SQLite path |
| `sqlite:////var/lib/app.db` | No | No | Yes | Absolute SQLite path |
| `mysql://user:pass@127.0.0.1:3306/cities_db` | Yes | Yes | No | Generic MySQL scheme |
| `mysql+pymysql://user:pass@127.0.0.1:3306/cities_db` | Yes | No | No | Explicit sync driver |
| `mysql+asyncmy://user:pass@127.0.0.1:3306/cities_db` | No | Yes | No | Explicit async driver |
| `mysql://user:pass@127.0.0.1` | No | No | No | Rejected: missing database |
| `mysql://user@127.0.0.1:3306/cities_db` | No | No | No | Rejected: missing password |
| `sqlite://localhost/data.db` | No | No | No | Rejected: hostname not allowed |
| `mysql://user:pass@127.0.0.1:3306/cities_db?charset=utf8mb4` | No | No | No | Rejected: query params unsupported |

SQLStratum focuses on queries. DDL statements such as `CREATE TABLE` or `ALTER TABLE` are intended
to live in a complementary library with similar design goals that is currently in the works.
