import unittest

from sqlstratum import SELECT, Table, col
from sqlstratum.runner import SQLiteRunner
from sqlstratum.runner_mysql import MySQLRunner
from sqlstratum.runner_mysql_async import AsyncMySQLRunner


users = Table("users", col("id", int), col("email", str))
admins = Table("admins", col("id", int), col("email", str))


class _FakeSyncCursor:
    def __init__(self):
        self.description = (("id",), ("email",))
        self.rows = []
        self.rowcount = 0
        self.lastrowid = None

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class _FakeSyncConnection:
    def __init__(self):
        self.cursor_obj = _FakeSyncCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        return None

    def rollback(self):
        return None


class _FakeAsyncCursor:
    def __init__(self):
        self.description = (("id",), ("email",))
        self.rows = []
        self.rowcount = 0
        self.lastrowid = None

    async def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    async def fetchall(self):
        return self.rows

    async def fetchone(self):
        return self.rows[0] if self.rows else None


class _FakeAsyncCursorContext:
    def __init__(self, cursor):
        self._cursor = cursor

    async def __aenter__(self):
        return self._cursor

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeAsyncConnection:
    def __init__(self):
        self.cursor_obj = _FakeAsyncCursor()

    def cursor(self):
        return _FakeAsyncCursorContext(self.cursor_obj)

    async def commit(self):
        return None

    async def rollback(self):
        return None


class TestSQLiteSetQueryHydration(unittest.TestCase):
    def setUp(self):
        self.runner = SQLiteRunner.connect(path=":memory:")
        self.runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
        self.runner.exec_ddl("CREATE TABLE admins (id INTEGER PRIMARY KEY, email TEXT)")
        self.runner.exec_ddl("INSERT INTO users (id, email) VALUES (1, 'a@x.com')")
        self.runner.exec_ddl("INSERT INTO admins (id, email) VALUES (2, 'b@y.com')")

    def tearDown(self):
        self.runner.connection.close()

    def test_set_query_inherits_left_hydration(self):
        q_users = SELECT(users.c.id, users.c.email).FROM(users).hydrate(
            lambda row: f"{row['id']}:{row['email']}"
        )
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q_users.UNION_ALL(q_admins).ORDER_BY(users.c.id).ASC()
        rows = self.runner.fetch_all(q)
        self.assertEqual(rows, ["1:a@x.com", "2:b@y.com"])

    def test_set_query_hydration_overrides_left_hydration(self):
        q_users = SELECT(users.c.id, users.c.email).FROM(users).hydrate(
            lambda row: f"{row['id']}:{row['email']}"
        )
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q_users.UNION_ALL(q_admins).hydrate(dict).ORDER_BY(users.c.id).ASC()
        rows = self.runner.fetch_all(q)
        self.assertEqual(rows, [{"id": 1, "email": "a@x.com"}, {"id": 2, "email": "b@y.com"}])


class TestMySQLSetQueryHydration(unittest.TestCase):
    def test_sync_runner_uses_left_hydration_for_set_query(self):
        conn = _FakeSyncConnection()
        conn.cursor_obj.rows = [(1, "a@x.com"), (2, "b@y.com")]
        runner = MySQLRunner(conn)

        q_users = SELECT(users.c.id, users.c.email).FROM(users).hydrate(
            lambda row: f"{row['id']}:{row['email']}"
        )
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q_users.UNION_ALL(q_admins).ORDER_BY(users.c.id).ASC()
        rows = runner.fetch_all(q)

        self.assertEqual(rows, ["1:a@x.com", "2:b@y.com"])

    def test_sync_runner_set_query_hydration_override(self):
        conn = _FakeSyncConnection()
        conn.cursor_obj.rows = [(1, "a@x.com")]
        runner = MySQLRunner(conn)

        q_users = SELECT(users.c.id, users.c.email).FROM(users).hydrate(
            lambda row: f"{row['id']}:{row['email']}"
        )
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q_users.UNION_ALL(q_admins).hydrate(dict).ORDER_BY(users.c.id).ASC()
        rows = runner.fetch_all(q)

        self.assertEqual(rows, [{"id": 1, "email": "a@x.com"}])


class TestAsyncMySQLSetQueryHydration(unittest.IsolatedAsyncioTestCase):
    async def test_async_runner_uses_left_hydration_for_set_query(self):
        conn = _FakeAsyncConnection()
        conn.cursor_obj.rows = [(1, "a@x.com"), (2, "b@y.com")]
        runner = AsyncMySQLRunner(conn)

        q_users = SELECT(users.c.id, users.c.email).FROM(users).hydrate(
            lambda row: f"{row['id']}:{row['email']}"
        )
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q_users.UNION_ALL(q_admins).ORDER_BY(users.c.id).ASC()
        rows = await runner.fetch_all(q)

        self.assertEqual(rows, ["1:a@x.com", "2:b@y.com"])

    async def test_async_runner_set_query_hydration_override(self):
        conn = _FakeAsyncConnection()
        conn.cursor_obj.rows = [(1, "a@x.com")]
        runner = AsyncMySQLRunner(conn)

        q_users = SELECT(users.c.id, users.c.email).FROM(users).hydrate(
            lambda row: f"{row['id']}:{row['email']}"
        )
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q_users.UNION_ALL(q_admins).hydrate(dict).ORDER_BY(users.c.id).ASC()
        rows = await runner.fetch_all(q)

        self.assertEqual(rows, [{"id": 1, "email": "a@x.com"}])


if __name__ == "__main__":
    unittest.main()
