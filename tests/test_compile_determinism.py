import unittest

from sqlstratum import COUNT, OR, SELECT, Table, col, compile


users = Table(
    "users",
    col("id", int),
    col("email", str),
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


class TestCompileDeterminism(unittest.TestCase):
    def test_repeated_compile_select_join_is_deterministic(self):
        q = (
            SELECT(users.c.id, users.c.email, orgs.c.name.AS("org_name"))
            .FROM(users)
            .JOIN(orgs, ON=users.c.org_id == orgs.c.id)
            .WHERE(
                users.c.active.is_true(),
                users.c.email.contains("acme"),
                users.c.age >= 18,
                OR(users.c.role == "admin", users.c.role == "owner"),
            )
            .ORDER_BY(users.c.id.ASC())
            .LIMIT(25)
            .OFFSET(0)
        )
        first = compile(q)
        for _ in range(25):
            current = compile(q)
            self.assertEqual(current.sql, first.sql)
            self.assertEqual(current.params, first.params)

    def test_repeated_compile_aggregate_is_deterministic(self):
        q = (
            SELECT(orgs.c.id, orgs.c.name, COUNT(users.c.id).AS("user_count"))
            .FROM(orgs)
            .JOIN(users, ON=users.c.org_id == orgs.c.id)
            .WHERE(orgs.c.active.is_true())
            .GROUP_BY(orgs.c.id, orgs.c.name)
            .HAVING(COUNT(users.c.id) >= 3)
            .ORDER_BY(COUNT(users.c.id).DESC())
        )
        first = compile(q)
        for _ in range(25):
            current = compile(q)
            self.assertEqual(current.sql, first.sql)
            self.assertEqual(current.params, first.params)


if __name__ == "__main__":
    unittest.main()
