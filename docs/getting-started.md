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

For SQLite-only features, bind intent explicitly:
```python
from sqlstratum.sqlite import using_sqlite, TOTAL

q = using_sqlite(SELECT(TOTAL(users.c.id).AS("n")).FROM(users))
compiled = compile(q)  # sqlite intent
```

For MySQL intent, bind explicitly as well:
```python
from sqlstratum.mysql import using_mysql

q = using_mysql(SELECT(users.c.id, users.c.email).FROM(users))
compiled = compile(q, dialect="mysql")
```

See [Dialect wrappers](dialect-wrappers.md) for behavior and guardrails.

## Ordering
Primary style:

```python
from sqlstratum import ASC, DESC

q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .ORDER_BY(
        DESC(users.c.created_at),
        ASC(users.c.email),
        ASC(users.c.id),
    )
)
```

Alternative fluent style:
```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .ORDER_BY(users.c.id)
    .ASC()
    .THEN(users.c.email)
    .DESC()
)
```

Mixed style is supported too:
```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .ORDER_BY(DESC(users.c.created_at), users.c.email)
    .ASC()
)
```

`ORDER_BY(...)` with a bare expression requires a following `.ASC()` or `.DESC()` before compile/execute.

## Predicates And Set Operations
```python
from sqlstratum import EXISTS, SELECT

active_orgs = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.active == 1)
sub = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == users.c.org_id)

q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(
        users.c.org_id.IN(active_orgs),
        users.c.age.BETWEEN(18, 65),
        EXISTS(sub),
    )
)

q2 = SELECT(users.c.id).FROM(users).UNION_ALL(SELECT(admins.c.id).FROM(admins))
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
    user="app",
    password="secret",
    database="appdb",
)

rows = runner.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
print(rows)
```

URL form is also supported (and mutually exclusive with individual parameters):
```python
runner = MySQLRunner.connect(url="mysql+pymysql://app:secret@127.0.0.1:3306/appdb")
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

## Capability Contract
For a concise matrix of portable vs dialect-specific behavior, see
[SQL profile](sql-profile.md#capability-contract-matrix).
