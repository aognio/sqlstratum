import unittest
from unittest import mock

from sqlstratum import INSERT, SELECT, Table, col
from sqlstratum.runner_mysql import MySQLRunner


users = Table(
    "users",
    col("id", int),
    col("email", str),
)


class FakeSyncCursor:
    def __init__(self):
        self.description = None
        self.rows = []
        self.fetchone_row = None
        self.rowcount = 0
        self.lastrowid = None
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.fetchone_row


class FakeSyncConnection:
    def __init__(self):
        self.cursor_obj = FakeSyncCursor()
        self.commit_calls = 0
        self.rollback_calls = 0

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1


class FakePyMySQLModule:
    def __init__(self):
        self.calls = []
        self.connection = FakeSyncConnection()

    def connect(self, **kwargs):
        self.calls.append(kwargs)
        return self.connection


class TestMySQLRunner(unittest.TestCase):
    def test_missing_dependency_raises(self):
        with mock.patch("sqlstratum.runner_mysql._import_pymysql", side_effect=ImportError("x")):
            with self.assertRaises(RuntimeError) as cm:
                MySQLRunner.connect(
                    host="127.0.0.1",
                    user="u",
                    password="p",
                    database="db",
                )
        self.assertIn("sqlstratum[pymysql]", str(cm.exception))

    def test_fetch_all_with_tuple_rows(self):
        conn = FakeSyncConnection()
        conn.cursor_obj.description = (("id",), ("email",))
        conn.cursor_obj.rows = [(1, "a@b.com"), (2, "b@c.com")]

        runner = MySQLRunner(conn)
        q = SELECT(users.c.id, users.c.email).FROM(users)
        rows = runner.fetch_all(q)

        self.assertEqual(rows, [{"id": 1, "email": "a@b.com"}, {"id": 2, "email": "b@c.com"}])
        self.assertEqual(conn.commit_calls, 0)

    def test_connect_uses_pymysql_module(self):
        fake = FakePyMySQLModule()
        with mock.patch("sqlstratum.runner_mysql._import_pymysql", return_value=fake):
            runner = MySQLRunner.connect(
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

    def test_execute_commits_outside_tx(self):
        conn = FakeSyncConnection()
        conn.cursor_obj.rowcount = 1
        conn.cursor_obj.lastrowid = 5

        runner = MySQLRunner(conn)
        result = runner.execute(INSERT(users).VALUES(email="x@y.com"))

        self.assertEqual(conn.commit_calls, 1)
        self.assertEqual(result.rowcount, 1)
        self.assertEqual(result.lastrowid, 5)

    def test_transaction_rolls_back_on_error(self):
        conn = FakeSyncConnection()
        runner = MySQLRunner(conn)

        with self.assertRaises(RuntimeError):
            with runner.transaction():
                raise RuntimeError("boom")

        self.assertEqual(conn.rollback_calls, 1)


if __name__ == "__main__":
    unittest.main()
