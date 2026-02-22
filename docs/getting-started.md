# Getting Started

## Install
```bash
pip install sqlstratum
```

## First Query
```python
import sqlite3

from sqlstratum import SELECT, Table, col, Runner

users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
)

conn = sqlite3.connect(":memory:")
runner = Runner(conn)
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

SQLStratum focuses on queries. DDL statements such as `CREATE TABLE` or `ALTER TABLE` are intended
to live in a complementary library with similar design goals that is currently in the works.
