import logging
import os
import sqlite3
import unittest

from sqlstratum import SELECT, Table, col
from sqlstratum.runner import Runner


users = Table(
    "users",
    col("id", int),
    col("email", str),
)


class TestRunnerDebugLogging(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.runner = Runner(self.conn)
        self.runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
        self.conn.execute("INSERT INTO users (id, email) VALUES (?, ?)", (1, "a@b.com"))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def _set_env(self, value):
        old = os.environ.get("SQLSTRATUM_DEBUG")
        if value is None:
            os.environ.pop("SQLSTRATUM_DEBUG", None)
        else:
            os.environ["SQLSTRATUM_DEBUG"] = value

        def restore():
            if old is None:
                os.environ.pop("SQLSTRATUM_DEBUG", None)
            else:
                os.environ["SQLSTRATUM_DEBUG"] = old

        self.addCleanup(restore)

    def test_debug_logs_emitted_when_enabled(self):
        self._set_env("1")
        q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1)
        with self.assertLogs("sqlstratum", level="DEBUG") as cm:
            self.runner.fetch_one(q)
        self.assertTrue(any("SELECT" in line for line in cm.output))
        self.assertTrue(any("p0" in line for line in cm.output))

    def test_debug_logs_suppressed_when_disabled(self):
        self._set_env("0")
        q = SELECT(users.c.id).FROM(users).WHERE(users.c.id == 1)
        with self.assertRaises(AssertionError):
            with self.assertLogs("sqlstratum", level="DEBUG"):
                self.runner.fetch_one(q)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
