import unittest

from sqlstratum import SELECT, SQLiteRunner, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError
from sqlstratum.sqlite import using_sqlite, TOTAL


users = Table("users", col("id", int), col("email", str))


class TestSQLiteWrapper(unittest.TestCase):
    def test_compile_uses_bound_dialect(self):
        q = using_sqlite(SELECT(TOTAL(users.c.id).AS("n")).FROM(users))
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT TOTAL("users"."id") AS "n" FROM "users"',
        )

    def test_compile_rejects_conflicting_dialect(self):
        q = using_sqlite(SELECT(users.c.id).FROM(users))
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q, dialect="mysql")
        self.assertIn("query bound to dialect 'sqlite'", str(cm.exception))

    def test_sqlite_runner_accepts_wrapped_query(self):
        runner = SQLiteRunner.connect(path=":memory:")
        runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
        runner.exec_ddl("INSERT INTO users (id, email) VALUES (1, 'a@b.com')")

        q = using_sqlite(SELECT(users.c.id, users.c.email).FROM(users))
        rows = runner.fetch_all(q)
        self.assertEqual(rows, [{"id": 1, "email": "a@b.com"}])


if __name__ == "__main__":
    unittest.main()
