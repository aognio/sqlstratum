import unittest

from sqlstratum import SELECT, COUNT, TOTAL, GROUP_CONCAT, Table, col, compile


users = Table(
    "users",
    col("id", int),
    col("org_id", int),
)

orgs = Table(
    "orgs",
    col("id", int),
    col("name", str),
)


class TestCompileAggregate(unittest.TestCase):
    def test_group_and_order(self):
        q = (
            SELECT(orgs.c.id, orgs.c.name, COUNT(users.c.id).AS("user_count"))
            .FROM(orgs)
            .JOIN(users, ON=users.c.org_id == orgs.c.id)
            .GROUP_BY(orgs.c.id, orgs.c.name)
            .ORDER_BY(COUNT(users.c.id))
            .DESC()
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "orgs"."id", "orgs"."name", COUNT("users"."id") AS "user_count" '
            'FROM "orgs" JOIN "users" ON "users"."org_id" = "orgs"."id" '
            'GROUP BY "orgs"."id", "orgs"."name" ORDER BY COUNT("users"."id") DESC',
        )
        self.assertEqual(compiled.params, {})

    def test_having(self):
        q = (
            SELECT(orgs.c.id, orgs.c.name, COUNT(users.c.id).AS("user_count"))
            .FROM(orgs)
            .JOIN(users, ON=users.c.org_id == orgs.c.id)
            .GROUP_BY(orgs.c.id, orgs.c.name)
            .HAVING(COUNT(users.c.id) >= 10)
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "orgs"."id", "orgs"."name", COUNT("users"."id") AS "user_count" '
            'FROM "orgs" JOIN "users" ON "users"."org_id" = "orgs"."id" '
            'GROUP BY "orgs"."id", "orgs"."name" HAVING COUNT("users"."id") >= :p0',
        )
        self.assertEqual(compiled.params, {"p0": 10})

    def test_total_aggregate(self):
        q = SELECT(TOTAL(users.c.id).AS("total_users")).FROM(users)
        compiled = compile(q, dialect="sqlite")
        self.assertEqual(
            compiled.sql,
            'SELECT TOTAL("users"."id") AS "total_users" FROM "users"',
        )
        self.assertEqual(compiled.params, {})

    def test_group_concat_default_separator(self):
        q = SELECT(GROUP_CONCAT(orgs.c.name).AS("names")).FROM(orgs)
        compiled = compile(q, dialect="sqlite")
        self.assertEqual(
            compiled.sql,
            'SELECT GROUP_CONCAT("orgs"."name") AS "names" FROM "orgs"',
        )
        self.assertEqual(compiled.params, {})

    def test_group_concat_with_separator(self):
        q = SELECT(GROUP_CONCAT(orgs.c.name, " | ").AS("names")).FROM(orgs)
        compiled = compile(q, dialect="sqlite")
        self.assertEqual(
            compiled.sql,
            'SELECT GROUP_CONCAT("orgs"."name", :p0) AS "names" FROM "orgs"',
        )
        self.assertEqual(compiled.params, {"p0": " | "})


if __name__ == "__main__":
    unittest.main()
