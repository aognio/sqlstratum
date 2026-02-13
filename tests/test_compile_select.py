import unittest

from sqlstratum import SELECT, OR, Table, col, compile


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
    col("age", int),
    col("role", str),
    col("org_id", int),
)


class TestCompileSelect(unittest.TestCase):
    def test_simple_select(self):
        q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 1)
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" WHERE "users"."id" = :p0',
        )
        self.assertEqual(compiled.params, {"p0": 1})

    def test_implicit_and_and_or(self):
        q = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(
                users.c.active.is_true(),
                users.c.email.contains("gmail"),
                users.c.age >= 18,
                OR(users.c.role == "admin", users.c.role == "owner"),
            )
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'WHERE "users"."active" = :p0 AND "users"."email" LIKE :p1 '
            'AND "users"."age" >= :p2 AND ("users"."role" = :p3 OR "users"."role" = :p4)',
        )
        self.assertEqual(
            compiled.params,
            {"p0": True, "p1": "%gmail%", "p2": 18, "p3": "admin", "p4": "owner"},
        )

    def test_pagination(self):
        q = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(users.c.active.is_true())
            .ORDER_BY(users.c.id.ASC())
            .LIMIT(50)
            .OFFSET(0)
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'WHERE "users"."active" = :p0 ORDER BY "users"."id" ASC LIMIT :p1 OFFSET :p2',
        )
        self.assertEqual(compiled.params, {"p0": True, "p1": 50, "p2": 0})


if __name__ == "__main__":
    unittest.main()
