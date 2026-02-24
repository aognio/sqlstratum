import unittest
from unittest import mock

from sqlstratum import AsyncMySQLRunner, MySQLRunner, Runner, SQLiteRunner


class FakePyMySQLModule:
    def __init__(self):
        self.calls = []

    def connect(self, **kwargs):
        self.calls.append(kwargs)
        return object()


class FakeAsyncMySQLModule:
    def __init__(self):
        self.calls = []

    async def connect(self, **kwargs):
        self.calls.append(kwargs)
        return object()


class TestConnectionOptions(unittest.TestCase):
    def test_sqlite_runner_alias(self):
        self.assertIs(Runner, SQLiteRunner)

    def test_sqlite_connect_url(self):
        with mock.patch("sqlite3.connect") as m:
            SQLiteRunner.connect(url="sqlite:///:memory:")
        m.assert_called_once_with(":memory:")

    def test_sqlite_connect_rejects_mixed(self):
        with self.assertRaises(ValueError):
            SQLiteRunner.connect(":memory:", url="sqlite:///:memory:")

    def test_mysql_connect_url(self):
        fake = FakePyMySQLModule()
        with mock.patch("sqlstratum.runner_mysql._import_pymysql", return_value=fake):
            MySQLRunner.connect(url="mysql+pymysql://u:p@127.0.0.1:3307/db")
        call = fake.calls[0]
        self.assertEqual(call["host"], "127.0.0.1")
        self.assertEqual(call["user"], "u")
        self.assertEqual(call["password"], "p")
        self.assertEqual(call["database"], "db")
        self.assertEqual(call["port"], 3307)

    def test_mysql_connect_rejects_mixed(self):
        with self.assertRaises(ValueError):
            MySQLRunner.connect(url="mysql://u:p@127.0.0.1/db", host="127.0.0.1")


class TestAsyncConnectionOptions(unittest.IsolatedAsyncioTestCase):
    async def test_async_mysql_connect_url(self):
        fake = FakeAsyncMySQLModule()
        with mock.patch("sqlstratum.runner_mysql_async._import_asyncmy", return_value=fake):
            await AsyncMySQLRunner.connect(url="mysql+asyncmy://u:p@127.0.0.1:3307/db")
        call = fake.calls[0]
        self.assertEqual(call["host"], "127.0.0.1")
        self.assertEqual(call["user"], "u")
        self.assertEqual(call["password"], "p")
        self.assertEqual(call["database"], "db")
        self.assertEqual(call["port"], 3307)

    async def test_async_mysql_connect_rejects_mixed(self):
        with self.assertRaises(ValueError):
            await AsyncMySQLRunner.connect(url="mysql://u:p@127.0.0.1/db", host="127.0.0.1")


if __name__ == "__main__":
    unittest.main()
