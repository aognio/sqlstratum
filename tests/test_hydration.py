import json
import sqlite3
import unittest
from dataclasses import dataclass

from sqlstratum import SELECT, Table, col
from sqlstratum.hydrate import HydrationError
from sqlstratum.runner import Runner


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("full_name", str),
)


class TestHydration(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.runner = Runner(self.conn)
        self.runner.exec_ddl(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, full_name TEXT)"
        )
        self.conn.execute("INSERT INTO users (id, email, full_name) VALUES (1, 'a@b.com', 'A')")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_dict_and_json(self):
        q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1).hydrate(dict)
        rows = self.runner.fetch_all(q)
        self.assertEqual(rows, [{"id": 1, "email": "a@b.com"}])
        json.dumps(rows)

    def test_dataclass(self):
        @dataclass
        class User:
            id: int
            email: str

        q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1).hydrate(User)
        row = self.runner.fetch_one(q)
        self.assertEqual(row, User(id=1, email="a@b.com"))

    def test_callable(self):
        q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1).hydrate(
            lambda m: f"{m['id']}:{m['email']}"
        )
        row = self.runner.fetch_one(q)
        self.assertEqual(row, "1:a@b.com")

    def test_duplicate_keys(self):
        orgs = Table("orgs", col("id", int), col("name", str))
        self.runner.exec_ddl("CREATE TABLE orgs (id INTEGER PRIMARY KEY, name TEXT)")
        self.conn.execute("INSERT INTO orgs (id, name) VALUES (1, 'Org')")
        self.conn.commit()
        q = (
            SELECT(users.c.id, orgs.c.id)
            .FROM(users)
            .JOIN(orgs, ON=users.c.id == orgs.c.id)
        )
        with self.assertRaises(HydrationError):
            self.runner.fetch_all(q)


if __name__ == "__main__":
    unittest.main()
