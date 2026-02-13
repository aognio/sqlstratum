import unittest

from sqlstratum import SELECT, Table, col, compile


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("org_id", int),
)

orgs = Table(
    "orgs",
    col("id", int),
    col("name", str),
    col("active", int),
)


class TestCompileJoin(unittest.TestCase):
    def test_inner_join(self):
        q = (
            SELECT(users.c.id, users.c.email, orgs.c.name.AS("org_name"))
            .FROM(users)
            .JOIN(orgs, ON=users.c.org_id == orgs.c.id)
            .WHERE(orgs.c.active.is_true())
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email", "orgs"."name" AS "org_name" '
            'FROM "users" JOIN "orgs" ON "users"."org_id" = "orgs"."id" '
            'WHERE "orgs"."active" = :p0',
        )
        self.assertEqual(compiled.params, {"p0": True})

    def test_left_join_null(self):
        q = (
            SELECT(users.c.id, users.c.email, orgs.c.name.AS("org_name"))
            .FROM(users)
            .LEFT_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
            .WHERE(orgs.c.name.is_null())
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email", "orgs"."name" AS "org_name" '
            'FROM "users" LEFT JOIN "orgs" ON "users"."org_id" = "orgs"."id" '
            'WHERE "orgs"."name" IS NULL',
        )
        self.assertEqual(compiled.params, {})


if __name__ == "__main__":
    unittest.main()
