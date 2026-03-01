import unittest

from sqlstratum import EXISTS, NOT_EXISTS, SELECT, Table, col, compile


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


class TestCompilePredicates(unittest.TestCase):
    def test_in_not_in_literals(self):
        q = (
            SELECT(users.c.id)
            .FROM(users)
            .WHERE(users.c.org_id.IN([1, 2, 3]), users.c.age.NOT_IN([9, 10]))
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id" FROM "users" WHERE "users"."org_id" IN (:p0, :p1, :p2) AND "users"."age" NOT IN (:p3, :p4)',
        )
        self.assertEqual(compiled.params, {"p0": 1, "p1": 2, "p2": 3, "p3": 9, "p4": 10})

    def test_between_and_not_between(self):
        q = (
            SELECT(users.c.id)
            .FROM(users)
            .WHERE(users.c.age.BETWEEN(18, 65), users.c.org_id.NOT_BETWEEN(100, 200))
        )
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `users`.`id` FROM `users` WHERE `users`.`age` BETWEEN %(p0)s AND %(p1)s AND `users`.`org_id` NOT BETWEEN %(p2)s AND %(p3)s",
        )
        self.assertEqual(compiled.params, {"p0": 18, "p1": 65, "p2": 100, "p3": 200})

    def test_in_with_subquery(self):
        active_orgs = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.active == 1)
        q = SELECT(users.c.id).FROM(users).WHERE(users.c.org_id.IN(active_orgs))
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id" FROM "users" WHERE "users"."org_id" IN (SELECT "orgs"."id" FROM "orgs" WHERE "orgs"."active" = :p0)',
        )
        self.assertEqual(compiled.params, {"p0": 1})

    def test_exists_not_exists(self):
        sub = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == users.c.org_id)
        q = SELECT(users.c.id).FROM(users).WHERE(EXISTS(sub), NOT_EXISTS(sub))
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id" FROM "users" WHERE EXISTS (SELECT "orgs"."id" FROM "orgs" WHERE "orgs"."id" = "users"."org_id") AND NOT EXISTS (SELECT "orgs"."id" FROM "orgs" WHERE "orgs"."id" = "users"."org_id")',
        )


if __name__ == "__main__":
    unittest.main()
