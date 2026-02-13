import sqlite3
import tempfile
import unittest

from sqlstratum import INSERT, SELECT, Table, col
from sqlstratum.runner import Runner


users = Table(
    "users",
    col("id", int),
    col("email", str),
)


class TestTransactions(unittest.TestCase):
    def test_rollback(self):
        conn = sqlite3.connect(":memory:")
        runner = Runner(conn)
        runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")

        try:
            with runner.transaction():
                runner.execute(INSERT(users).VALUES(email="x@y.com"))
                raise RuntimeError("boom")
        except RuntimeError:
            pass

        rows = runner.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
        self.assertEqual(rows, [])
        conn.close()

    def test_persistent_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            conn = sqlite3.connect(tmp.name)
            runner = Runner(conn)
            runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
            runner.execute(INSERT(users).VALUES(email="persisted"))
            conn.close()

            conn2 = sqlite3.connect(tmp.name)
            runner2 = Runner(conn2)
            rows = runner2.fetch_all(SELECT(users.c.id, users.c.email).FROM(users))
            self.assertEqual(rows, [{"id": 1, "email": "persisted"}])
            conn2.close()


if __name__ == "__main__":
    unittest.main()
