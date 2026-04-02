import sqlite3
import unittest

from sqlstratum import EXISTS, NOT_EXISTS, SELECT, Table, col
from sqlstratum.runner import SQLiteRunner


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("org_id", int),
    col("age", int),
)

orgs = Table(
    "orgs",
    col("id", int),
    col("active", int),
)

admins = Table(
    "admins",
    col("id", int),
    col("email", str),
)


class TestSQLiteIntegrationNewFeatures(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.runner = SQLiteRunner(self.conn)
        self.runner.exec_ddl("CREATE TABLE orgs (id INTEGER PRIMARY KEY, active INTEGER)")
        self.runner.exec_ddl(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, org_id INTEGER, age INTEGER)"
        )
        self.runner.exec_ddl("CREATE TABLE admins (id INTEGER PRIMARY KEY, email TEXT)")

        self.conn.executemany("INSERT INTO orgs (id, active) VALUES (?, ?)", [(1, 1), (2, 0), (3, 1)])
        self.conn.executemany(
            "INSERT INTO users (id, email, org_id, age) VALUES (?, ?, ?, ?)",
            [
                (1, "a@acme.com", 1, 25),
                (2, "b@acme.com", 1, 17),
                (3, "c@idle.com", 2, 45),
                (4, "d@other.com", 3, 33),
            ],
        )
        self.conn.executemany(
            "INSERT INTO admins (id, email) VALUES (?, ?)",
            [(2, "b@acme.com"), (4, "d@other.com")],
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_in_between_exists_not_exists(self):
        active_orgs = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.active == 1)
        org_for_user = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == users.c.org_id)

        q = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(
                users.c.org_id.IN(active_orgs),
                users.c.age.BETWEEN(18, 40),
                EXISTS(org_for_user),
                NOT_EXISTS(SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == 9999)),
            )
            .ORDER_BY(users.c.id)
            .ASC()
        )

        rows = self.runner.fetch_all(q)
        self.assertEqual(rows, [{"id": 1, "email": "a@acme.com"}, {"id": 4, "email": "d@other.com"}])

    def test_union_all_execution(self):
        q_users = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id.IN([1, 2]))
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)

        q = (
            q_users.UNION_ALL(q_admins)
            .ORDER_BY(users.c.id)
            .ASC()
        )

        rows = self.runner.fetch_all(q)
        self.assertEqual([r["id"] for r in rows], [1, 2, 2, 4])


if __name__ == "__main__":
    unittest.main()
