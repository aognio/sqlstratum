# Testing

SQLStratum uses layered tests to match its architecture:

- Unit/compiler tests: deterministic SQL + parameter snapshots.
- Runner tests: execution behavior and hydration boundaries.
- Dialect contract tests: explicit cross-dialect capability guarantees.
- Integration tests (opt-in): real MySQL server checks for sync/async runners.

## Default Test Suite
Run the full default suite:

```bash
python -m unittest
```

This includes compiler, runner, hydration, and dialect capability contract tests.

## Real MySQL Integration Tests (Opt-In)
Real MySQL tests are intentionally disabled by default.

You can start a local MySQL instance with Docker Compose:

```bash
docker compose -f docker/compose.yml up -d mysql
```

Enable and run:

```bash
SQLSTRATUM_RUN_MYSQL_INTEGRATION=1 \
SQLSTRATUM_TEST_MYSQL_URL_SYNC='mysql+pymysql://user:pass@127.0.0.1:3306/db' \
SQLSTRATUM_TEST_MYSQL_URL_ASYNC='mysql+asyncmy://user:pass@127.0.0.1:3306/db' \
python -m unittest tests.test_mysql_integration_real
```

With the default compose config, use:

```bash
SQLSTRATUM_RUN_MYSQL_INTEGRATION=1 \
SQLSTRATUM_TEST_MYSQL_URL_SYNC='mysql+pymysql://sqlstratum:sqlstratum_pass@127.0.0.1:3306/sqlstratum_it' \
SQLSTRATUM_TEST_MYSQL_URL_ASYNC='mysql+asyncmy://sqlstratum:sqlstratum_pass@127.0.0.1:3306/sqlstratum_it' \
python -m unittest tests.test_mysql_integration_real
```

## Release Validation Checks
Before publishing:

```bash
python -m unittest
mkdocs build --clean
python -m build --no-isolation
python -m twine check dist/*
```
