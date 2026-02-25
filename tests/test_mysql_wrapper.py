import unittest

from sqlstratum import MySQLRunner, SELECT, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError
from sqlstratum.mysql import using_mysql


users = Table("users", col("id", int), col("email", str))


class _FakeCursor:
    def __init__(self):
        self.description = (("id",), ("email",))
        self.rows = [(1, "a@b.com")]
        self.rowcount = 0
        self.lastrowid = None

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]


class _FakeConn:
    def __init__(self):
        self.cursor_obj = _FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        return None

    def rollback(self):
        return None


class TestMySQLWrapper(unittest.TestCase):
    def test_compile_rejects_default_sqlite_dialect(self):
        q = using_mysql(SELECT(users.c.id).FROM(users))
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q)
        self.assertIn("query bound to dialect 'mysql'", str(cm.exception))

    def test_compile_with_mysql_dialect(self):
        q = using_mysql(SELECT(users.c.id, users.c.email).FROM(users))
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `users`.`id`, `users`.`email` FROM `users`",
        )

    def test_mysql_runner_accepts_wrapped_query(self):
        runner = MySQLRunner(_FakeConn())
        q = using_mysql(SELECT(users.c.id, users.c.email).FROM(users))
        rows = runner.fetch_all(q)
        self.assertEqual(rows, [{"id": 1, "email": "a@b.com"}])


if __name__ == "__main__":
    unittest.main()
