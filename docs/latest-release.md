# Latest Release

# SQLStratum 0.4.0

`0.4.0` is the release where the query DSL becomes materially more expressive without giving up the
project's core constraints:

- deterministic compilation
- explicit dialect boundaries
- safe parameter binding
- runner-owned execution and hydration

If you want the canonical release record, read `CHANGELOG.md`. This page is the documentation-side
walkthrough of what changed and how to use it.

## What Changed

This release adds four major pieces of capability:

1. portable predicates such as `IN`, `BETWEEN`, and `EXISTS`
2. set operations such as `UNION ALL`, `INTERSECT`, and `EXCEPT`
3. a more explicit ordering API
4. a stronger MySQL execution and validation story

## Portable Predicates

The most visible DSL expansion is portable support for:

- `IN`
- `NOT IN`
- `BETWEEN`
- `NOT BETWEEN`
- `EXISTS`
- `NOT EXISTS`

That means more filtering logic stays inside the AST instead of escaping to handwritten SQL.

```python
from sqlstratum import EXISTS, NOT_EXISTS, SELECT, Table, col

users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("org_id", int),
    col("age", int),
)

orgs = Table(
    "orgs",
    col("id", int),
    col("active", int),
)

active_orgs = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.active == 1)
org_for_user = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == users.c.org_id)

q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(
        users.c.org_id.IN(active_orgs),
        users.c.age.BETWEEN(18, 65),
        EXISTS(org_for_user),
        NOT_EXISTS(SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == 9999)),
    )
)
```

Direct value lists use the same shape:

```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(
        users.c.id.IN([1, 2, 3]),
        users.c.age.NOT_BETWEEN(0, 12),
    )
)
```

## Set Operations

`0.4.0` also brings first-class support for:

- `UNION`
- `UNION ALL`
- `INTERSECT`
- `EXCEPT`

That makes cross-query composition practical without leaving the DSL.

```python
from sqlstratum import SELECT, Table, col

users = Table("users", col("id", int), col("email", str))
admins = Table("admins", col("id", int), col("email", str))

q_users = SELECT(users.c.id, users.c.email).FROM(users)
q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)

q = q_users.UNION_ALL(q_admins)
```

Set queries can still take ordering, limits, offsets, and hydration:

```python
from sqlstratum import ASC, DESC

q = (
    q_users.UNION_ALL(q_admins)
    .ORDER_BY(DESC(users.c.email), ASC(users.c.id))
    .LIMIT(25)
    .OFFSET(0)
    .hydrate(dict)
)
```

On MySQL specifically, `0.4.0` also fixes global set-query ordering so `ORDER BY` is rendered using
output columns, which is required for valid execution on real MySQL servers.

## Ordering API

The recommended ordering style is now explicit:

```python
from sqlstratum import ASC, DESC, SELECT, Table, col

users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("created_at", str),
)

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

The fluent alternative still works:

```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .ORDER_BY(users.c.created_at)
    .DESC()
    .THEN(users.c.email)
    .ASC()
    .THEN(users.c.id)
    .ASC()
)
```

Mixed style remains valid too:

```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .ORDER_BY(DESC(users.c.created_at), users.c.email)
    .ASC()
)
```

## Dialect Guardrails

This release expands the public join surface while staying explicit about dialect differences.

```python
from sqlstratum import SELECT, Table, col

users = Table("users", col("id", int), col("org_id", int))
orgs = Table("orgs", col("id", int))

q = (
    SELECT(users.c.id, orgs.c.id.AS("org_id"))
    .FROM(users)
    .RIGHT_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
)
```

Compiling for MySQL is valid:

```python
from sqlstratum import compile

compiled = compile(q, dialect="mysql")
print(compiled.sql)
```

Compiling unsupported combinations still raises a dialect error rather than pretending the feature is
portable when it is not.

## MySQL Execution

`0.4.0` tightens the MySQL runtime path for both sync and async runners.

Install extras:

```bash
pip install sqlstratum[pymysql]
pip install sqlstratum[asyncmy]
pip install sqlstratum[mysql]
```

These extras now include `cryptography`, which is commonly required by MySQL 8 authentication
schemes such as `caching_sha2_password`.

Sync usage:

```python
from sqlstratum import MySQLRunner, SELECT, Table, col

users = Table("users", col("id", int), col("email", str))

runner = MySQLRunner.connect(
    host="127.0.0.1",
    port=3306,
    user="app",
    password="secret",
    database="appdb",
)

rows = runner.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
```

Async usage:

```python
from sqlstratum import AsyncMySQLRunner, SELECT, Table, col

users = Table("users", col("id", int), col("email", str))

runner = await AsyncMySQLRunner.connect(
    url="mysql+asyncmy://app:secret@127.0.0.1:3306/appdb"
)

row = await runner.fetch_one(SELECT(users.c.id, users.c.email).FROM(users))
value = await runner.scalar(SELECT(users.c.id).FROM(users).LIMIT(1))
```

## Real MySQL Integration Coverage

This release does not stop at compile-time snapshots. It also expands opt-in real-server MySQL
coverage for both sync and async runners.

```bash
docker compose -f docker/compose.yml up -d mysql

SQLSTRATUM_RUN_MYSQL_INTEGRATION=1 \
SQLSTRATUM_TEST_MYSQL_URL_SYNC='mysql+pymysql://sqlstratum:sqlstratum_pass@127.0.0.1:3306/sqlstratum_it' \
SQLSTRATUM_TEST_MYSQL_URL_ASYNC='mysql+asyncmy://sqlstratum:sqlstratum_pass@127.0.0.1:3306/sqlstratum_it' \
python -m unittest tests.test_mysql_integration_real
```

That integration coverage now exercises:

- predicate execution
- set-query execution
- multi-column ordering on set queries
- `fetch_one`
- `scalar`
- sync and async execution paths

## Release Automation

`0.4.0` also tightens the maintainer release flow.

The release dry-run is still:

```bash
poe release-dry-run
```

But the build/check path now cleans release artifacts first so checks and uploads operate on the
current version only.

The full release command remains:

```bash
poe release
```

## A Complete Example

Here is a more representative `0.4.0` query that combines the new pieces:

```python
from sqlstratum import ASC, DESC, EXISTS, NOT_EXISTS, SELECT, Table, col

users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("org_id", int),
    col("active", int),
    col("age", int),
)

admins = Table(
    "admins",
    col("id", int),
    col("email", str),
)

orgs = Table(
    "orgs",
    col("id", int),
    col("active", int),
)

active_orgs = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.active == 1)
org_for_user = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == users.c.org_id)

eligible_users = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .WHERE(
        users.c.active == 1,
        users.c.org_id.IN(active_orgs),
        users.c.age.BETWEEN(18, 65),
        EXISTS(org_for_user),
        NOT_EXISTS(SELECT(admins.c.id).FROM(admins).WHERE(admins.c.id == users.c.id)),
    )
)

admin_rows = SELECT(admins.c.id, admins.c.email).FROM(admins)

q = (
    eligible_users
    .UNION_ALL(admin_rows)
    .ORDER_BY(DESC(users.c.email), ASC(users.c.id))
    .LIMIT(50)
)
```

For the formal release record, return to `CHANGELOG.md`.
