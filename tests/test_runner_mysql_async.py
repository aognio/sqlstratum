import unittest
from unittest import mock

from sqlstratum import INSERT, SELECT, Table, col
from sqlstratum.runner_mysql_async import AsyncMySQLRunner


users = Table(
    "users",
    col("id", int),
    col("email", str),
)


class FakeAsyncCursor:
    def __init__(self):
        self.description = None
        self.rows = []
        self.fetchone_row = None
        self.rowcount = 0
        self.lastrowid = None
        self.executed = []

    async def execute(self, sql, params=None):
        self.executed.append((sql, params))

    async def fetchall(self):
        return self.rows

    async def fetchone(self):
        return self.fetchone_row


class FakeAsyncCursorContext:
    def __init__(self, cursor):
        self._cursor = cursor

    async def __aenter__(self):
        return self._cursor

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeAsyncConnection:
    def __init__(self):
        self.cursor_obj = FakeAsyncCursor()
        self.commit_calls = 0
        self.rollback_calls = 0

    def cursor(self):
        return FakeAsyncCursorContext(self.cursor_obj)

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


class FakeAsyncMySQLModule:
    def __init__(self):
        self.calls = []
        self.connection = FakeAsyncConnection()

    async def connect(self, **kwargs):
        self.calls.append(kwargs)
        return self.connection


class TestAsyncMySQLRunner(unittest.IsolatedAsyncioTestCase):
    async def test_missing_dependency_raises(self):
        with mock.patch("sqlstratum.runner_mysql_async._import_asyncmy", side_effect=ImportError("x")):
            with self.assertRaises(RuntimeError) as cm:
                await AsyncMySQLRunner.connect(
                    host="127.0.0.1",
                    user="u",
                    password="p",
                    database="db",
                )
        self.assertIn("sqlstratum[asyncmy]", str(cm.exception))

    async def test_fetch_all_with_tuple_rows(self):
        conn = FakeAsyncConnection()
        conn.cursor_obj.description = (("id",), ("email",))
        conn.cursor_obj.rows = [(1, "a@b.com")]

        runner = AsyncMySQLRunner(conn)
        q = SELECT(users.c.id, users.c.email).FROM(users)
        rows = await runner.fetch_all(q)

        self.assertEqual(rows, [{"id": 1, "email": "a@b.com"}])
        self.assertEqual(conn.commit_calls, 0)

    async def test_connect_uses_asyncmy_module(self):
        fake = FakeAsyncMySQLModule()
        with mock.patch("sqlstratum.runner_mysql_async._import_asyncmy", return_value=fake):
            runner = await AsyncMySQLRunner.connect(
                host="127.0.0.1",
                user="u",
                password="p",
                database="db",
                port=3307,
            )
        self.assertIs(runner.connection, fake.connection)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0]["autocommit"], False)
        self.assertEqual(fake.calls[0]["port"], 3307)

    async def test_execute_commits_outside_tx(self):
        conn = FakeAsyncConnection()
        conn.cursor_obj.rowcount = 1
        conn.cursor_obj.lastrowid = 11

        runner = AsyncMySQLRunner(conn)
        result = await runner.execute(INSERT(users).VALUES(email="x@y.com"))

        self.assertEqual(conn.commit_calls, 1)
        self.assertEqual(result.rowcount, 1)
        self.assertEqual(result.lastrowid, 11)

    async def test_transaction_rolls_back_on_error(self):
        conn = FakeAsyncConnection()
        runner = AsyncMySQLRunner(conn)

        with self.assertRaises(RuntimeError):
            async with runner.transaction():
                raise RuntimeError("boom")

        self.assertEqual(conn.rollback_calls, 1)


if __name__ == "__main__":
    unittest.main()
