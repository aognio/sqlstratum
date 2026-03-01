import sqlite3
import unittest

from sqlstratum import (
    SELECT,
    INSERT,
    UPDATE,
    DELETE,
    OR,
    COUNT,
    Table,
    col,
)
from sqlstratum.runner import Runner


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("full_name", str),
    col("active", int),
    col("age", int),
    col("role", str),
    col("org_id", int),
)

orgs = Table(
    "orgs",
    col("id", int),
    col("name", str),
    col("active", int),
)


class TestSQLiteIntegration(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.runner = Runner(self.conn)
        self.runner.exec_ddl(
            "CREATE TABLE orgs (id INTEGER PRIMARY KEY, name TEXT, active INTEGER)"
        )
        self.runner.exec_ddl(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, full_name TEXT, active INTEGER, age INTEGER, role TEXT, org_id INTEGER)"
        )
        self.conn.executemany(
            "INSERT INTO orgs (id, name, active) VALUES (?, ?, ?)",
            [(1, "Acme", 1), (2, "Idle", 0)],
        )
        self.conn.executemany(
            "INSERT INTO users (id, email, full_name, active, age, role, org_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "a@acme.com", "A", 1, 30, "admin", 1),
                (2, "b@acme.com", "B", 1, 21, "owner", 1),
                (3, "c@idle.com", "C", 0, 19, "user", 2),
            ],
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_reference_queries(self):
        q1 = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1)
        row = self.runner.fetch_one(q1)
        self.assertEqual(row, {"id": 1, "email": "a@acme.com"})

        q2 = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(users.c.active.is_true(), users.c.email.contains("acme"), users.c.age >= 18)
        )
        rows = self.runner.fetch_all(q2)
        self.assertEqual(len(rows), 2)

        q3 = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(users.c.active.is_true(), OR(users.c.role == "admin", users.c.role == "owner"))
        )
        self.assertEqual(len(self.runner.fetch_all(q3)), 2)

        q4 = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(users.c.active.is_true())
            .ORDER_BY(users.c.id)
            .ASC()
            .LIMIT(50)
            .OFFSET(0)
        )
        rows = self.runner.fetch_all(q4)
        self.assertEqual([r["id"] for r in rows], [1, 2])

        q5 = (
            SELECT(users.c.id, users.c.email, orgs.c.name.AS("org_name"))
            .FROM(users)
            .JOIN(orgs, ON=users.c.org_id == orgs.c.id)
            .WHERE(orgs.c.active.is_true())
        )
        rows = self.runner.fetch_all(q5)
        self.assertEqual(rows[0]["org_name"], "Acme")

        q6 = (
            SELECT(users.c.id, users.c.email, orgs.c.name.AS("org_name"))
            .FROM(users)
            .LEFT_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
            .WHERE(orgs.c.name.is_null())
        )
        self.assertEqual(self.runner.fetch_all(q6), [])

        q7 = (
            SELECT(orgs.c.id, orgs.c.name, COUNT(users.c.id).AS("user_count"))
            .FROM(orgs)
            .JOIN(users, ON=users.c.org_id == orgs.c.id)
            .GROUP_BY(orgs.c.id, orgs.c.name)
            .ORDER_BY(COUNT(users.c.id))
            .DESC()
        )
        rows = self.runner.fetch_all(q7)
        self.assertEqual(rows[0]["user_count"], 2)

        q8 = (
            SELECT(orgs.c.id, orgs.c.name, COUNT(users.c.id).AS("user_count"))
            .FROM(orgs)
            .JOIN(users, ON=users.c.org_id == orgs.c.id)
            .GROUP_BY(orgs.c.id, orgs.c.name)
            .HAVING(COUNT(users.c.id) >= 10)
        )
        self.assertEqual(self.runner.fetch_all(q8), [])

        active_users = (
            SELECT(users.c.id, users.c.org_id)
            .FROM(users)
            .WHERE(users.c.active.is_true())
            .AS("active_users")
        )
        q9 = (
            SELECT(active_users.c.org_id, COUNT(active_users.c.id).AS("n"))
            .FROM(active_users)
            .GROUP_BY(active_users.c.org_id)
        )
        rows = self.runner.fetch_all(q9)
        self.assertEqual(rows, [{"org_id": 1, "n": 2}])

    def test_dml(self):
        q = INSERT(users).VALUES(email="a@b.com", full_name="A", active=1)
        res = self.runner.execute(q)
        self.assertIsNotNone(res.lastrowid)

        q = UPDATE(users).SET(full_name="B").WHERE(users.c.id == res.lastrowid)
        self.runner.execute(q)

        q = DELETE(users).WHERE(users.c.id == res.lastrowid)
        self.runner.execute(q)


if __name__ == "__main__":
    unittest.main()
