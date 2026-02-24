import unittest

from sqlstratum.connection_url import parse_mysql_url, parse_sqlite_url


class TestSQLiteUrlParsing(unittest.TestCase):
    def test_memory_url(self):
        self.assertEqual(parse_sqlite_url("sqlite:///:memory:"), ":memory:")

    def test_relative_path_url(self):
        self.assertEqual(parse_sqlite_url("sqlite:///data/app.db"), "data/app.db")

    def test_absolute_path_url(self):
        self.assertEqual(parse_sqlite_url("sqlite:////var/lib/app.db"), "/var/lib/app.db")

    def test_rejects_query(self):
        with self.assertRaises(ValueError):
            parse_sqlite_url("sqlite:///data/app.db?mode=ro")

    def test_rejects_wrong_scheme(self):
        with self.assertRaises(ValueError):
            parse_sqlite_url("mysql://user:pass@localhost/db")

    def test_rejects_hostname(self):
        with self.assertRaises(ValueError):
            parse_sqlite_url("sqlite://localhost/data.db")


class TestMySQLUrlParsing(unittest.TestCase):
    def test_sync_scheme_with_default_port(self):
        parsed = parse_mysql_url("mysql+pymysql://u:p@127.0.0.1/db", async_mode=False)
        self.assertEqual(parsed["port"], 3306)
        self.assertEqual(parsed["database"], "db")

    def test_async_scheme(self):
        parsed = parse_mysql_url("mysql+asyncmy://u:p@127.0.0.1:3307/db", async_mode=True)
        self.assertEqual(parsed["port"], 3307)

    def test_mysql_base_scheme_allowed(self):
        parsed = parse_mysql_url("mysql://u:p@127.0.0.1/db", async_mode=False)
        self.assertEqual(parsed["host"], "127.0.0.1")

    def test_percent_decoding(self):
        parsed = parse_mysql_url("mysql://user%40x:p%23s@localhost/my%2Ddb", async_mode=False)
        self.assertEqual(parsed["user"], "user@x")
        self.assertEqual(parsed["password"], "p#s")
        self.assertEqual(parsed["database"], "my-db")

    def test_rejects_query(self):
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://u:p@localhost/db?charset=utf8mb4", async_mode=False)

    def test_rejects_invalid_scheme_for_mode(self):
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql+asyncmy://u:p@localhost/db", async_mode=False)
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql+pymysql://u:p@localhost/db", async_mode=True)

    def test_rejects_missing_parts(self):
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://u:p@/db", async_mode=False)
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://:p@localhost/db", async_mode=False)
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://u@localhost/db", async_mode=False)
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://u:p@localhost", async_mode=False)

    def test_rejects_extra_path_segments(self):
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://u:p@localhost/db/extra", async_mode=False)

    def test_rejects_invalid_port(self):
        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://u:p@localhost:bad/db", async_mode=False)


if __name__ == "__main__":
    unittest.main()
