# Latest Release: SQLStratum 0.4.0

This document is non-normative.

The canonical release record is `CHANGELOG.md`. This file is intentionally looser: it explains the
latest release in prose, shows how the pieces fit together, and includes larger worked examples than
would be appropriate in the changelog itself.

## Release Summary

`0.4.0` is the release where the query DSL becomes materially more expressive without giving up the
project's core constraints:

- deterministic compilation
- explicit dialect boundaries
- safe parameter binding
- runner-owned execution and hydration

The release adds three major user-facing capabilities:

1. richer portable predicates
2. real set operations
3. a more explicit ordering API

It also tightens the MySQL story with better capability guardrails, better runner ergonomics, real
server integration coverage, and safer release automation.

## Why This Release Matters

Earlier SQLStratum releases established the AST, compiler registry, SQLite runner, MySQL adapters,
and dialect wrappers. `0.4.0` makes the query layer more complete for application code that wants to
stay inside the DSL instead of falling back to raw SQL.

That shows up most clearly in four places:

- subquery-heavy filtering now reads naturally
- cross-query composition is more practical
- ordering is explicit instead of implicit
- MySQL behavior is better documented and better tested

## Portable Predicates

The headline query-language addition is portable predicate support for:

- `IN`
- `NOT IN`
- `BETWEEN`
- `NOT BETWEEN`
- `EXISTS`
- `NOT EXISTS`

That means common application filtering patterns stay inside the AST instead of escaping to hand-made
SQL fragments.

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

For direct value lists, the same API works without changing shape:

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

And because predicates stay part of the AST, the compiler still owns parameter binding:

```python
from sqlstratum import compile

compiled = compile(q, dialect="mysql")
print(compiled.sql)
print(compiled.params)
```

## Set Operations

`0.4.0` also adds first-class support for:

- `UNION`
- `UNION ALL`
- `INTERSECT`
- `EXCEPT`

This is an important shift because it lets SQLStratum model a broader range of reporting and
cross-source query composition directly in the DSL.

```python
from sqlstratum import SELECT, Table, col

users = Table("users", col("id", int), col("email", str))
admins = Table("admins", col("id", int), col("email", str))

q_users = SELECT(users.c.id, users.c.email).FROM(users)
q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)

q = q_users.UNION_ALL(q_admins)
```

Set queries can then carry ordering, limits, offsets, and hydration the same way ordinary select
queries do:

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

This release also tightens MySQL behavior here. Global `ORDER BY` clauses for set queries are now
rendered using output columns rather than table-qualified names, which is required for correct MySQL
execution.

## Ordering API

Before `0.4.0`, ordering support existed, but this release makes the API explicit and ergonomic.

The recommended style is now to pass explicit wrappers:

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

The clause-fluent style is still supported:

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

Mixed style is valid too:

```python
q = (
    SELECT(users.c.id, users.c.email)
    .FROM(users)
    .ORDER_BY(DESC(users.c.created_at), users.c.email)
    .ASC()
)
```

The design intent is simple: ordering direction should be explicit. SQLStratum now enforces that
more consistently, especially around set queries and dialect-specific compilation paths.

## Join Guardrails

This release adds `RIGHT_JOIN` and `FULL_JOIN` to the public DSL surface, but with explicit dialect
capability guardrails instead of pretending that every backend supports every join shape.

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

Compiling for MySQL works:

```python
from sqlstratum import compile

compiled = compile(q, dialect="mysql")
print(compiled.sql)
```

But unsupported combinations fail explicitly:

```python
from sqlstratum.errors import UnsupportedDialectFeatureError

try:
    compile(q, dialect="sqlite")
except UnsupportedDialectFeatureError as exc:
    print(exc)
```

The same idea applies to `FULL_JOIN`: the API exists, but unsupported dialects reject it with a
clear error instead of silently generating invalid SQL.

## Cross-Dialect Contract

`0.4.0` leans harder into the idea that SQLStratum should be explicit about what is portable and what
is not.

That contract now has stronger test coverage and clearer documentation. A few examples:

- portable predicates compile across SQLite and MySQL
- `RIGHT JOIN` is accepted for MySQL and rejected for SQLite
- `FULL OUTER JOIN` is guarded rather than hand-waved
- SQLite-only aggregates such as `TOTAL(...)` and `GROUP_CONCAT(...)` are rejected by the MySQL compiler
- MySQL still rejects `OFFSET` without `LIMIT`

That means the project is not trying to flatten dialect differences away. It is trying to make them
explicit, testable, and predictable.

## MySQL Execution Story

The MySQL execution boundary is still intentionally separate from the AST and compiler, but `0.4.0`
does more to make the runtime experience practical.

The optional extras now account for common MySQL 8 authentication setups:

```bash
pip install sqlstratum[pymysql]
pip install sqlstratum[asyncmy]
pip install sqlstratum[mysql]
```

Those extras now include `cryptography`, which matters for `caching_sha2_password` and
`sha256_password` authentication.

Sync execution:

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

Async execution:

```python
from sqlstratum import AsyncMySQLRunner, SELECT, Table, col

users = Table("users", col("id", int), col("email", str))

runner = await AsyncMySQLRunner.connect(
    url="mysql+asyncmy://app:secret@127.0.0.1:3306/appdb"
)

row = await runner.fetch_one(SELECT(users.c.id, users.c.email).FROM(users))
value = await runner.scalar(SELECT(users.c.id).FROM(users).LIMIT(1))
```

The important architectural point remains unchanged: the runner is still the execution boundary.
Compilation and AST building stay deterministic and side-effect free.

## Real MySQL Integration Coverage

This release does not stop at compile-time snapshots.

It also adds opt-in real MySQL integration coverage for both sync and async runners. That matters
because some SQL differences only show up against a real server, not just in generated strings.

The Docker-backed integration flow looks like this:

```bash
docker compose -f docker/compose.yml up -d mysql

SQLSTRATUM_RUN_MYSQL_INTEGRATION=1 \
SQLSTRATUM_TEST_MYSQL_URL_SYNC='mysql+pymysql://sqlstratum:sqlstratum_pass@127.0.0.1:3306/sqlstratum_it' \
SQLSTRATUM_TEST_MYSQL_URL_ASYNC='mysql+asyncmy://sqlstratum:sqlstratum_pass@127.0.0.1:3306/sqlstratum_it' \
python -m unittest tests.test_mysql_integration_real
```

This real-server coverage now exercises more than just connection smoke tests. It validates actual
predicate execution, set-query execution, ordering behavior, `fetch_one`, and `scalar` against MySQL.

## Release Automation And Packaging

`0.4.0` also improves the maintainer path to shipping.

The release pipeline already ran tests, builds, and `twine check`, but this release tightens that
workflow by cleaning release artifacts before the build/check steps. That avoids accidentally mixing
old and new distributions during `poe release` or `poe release-dry-run`.

The release dry-run remains straightforward:

```bash
poe release-dry-run
```

And the full release path stays:

```bash
poe release
```

The packaging metadata was also updated to modern SPDX-style license configuration so the project is
better aligned with current setuptools guidance.

## A More Complete Example

Putting the major pieces together, a more representative `0.4.0` query might look like this:

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

That example is a good summary of what `0.4.0` brings to the table: more expressive composition,
stronger portability contracts, and a still-explicit boundary between query construction and
execution.

## Closing Note

`0.4.0` is not a radical redesign. It is a consolidation release.

It takes the SQLStratum shape established in earlier versions and makes it practical for a broader
class of real application queries, while still refusing to hide dialect differences or compromise on
deterministic compilation.

For the authoritative release record, read `CHANGELOG.md`.
