import unittest

from sqlstratum import EXISTS, NOT_EXISTS, SELECT, Table, col, compile


users = Table("users", col("id", int), col("org_id", int), col("age", int))
orgs = Table("orgs", col("id", int), col("active", int))
legacy_orgs = Table("legacy_orgs", col("id", int), col("active", int))


class TestCompilePredicatesEdge(unittest.TestCase):
    def test_in_empty_list_and_not_in_empty_list(self):
        q1 = SELECT(users.c.id).FROM(users).WHERE(users.c.org_id.IN([]))
        c1 = compile(q1)
        self.assertEqual(c1.sql, 'SELECT "users"."id" FROM "users" WHERE 1=0')
        self.assertEqual(c1.params, {})

        q2 = SELECT(users.c.id).FROM(users).WHERE(users.c.org_id.NOT_IN([]))
        c2 = compile(q2)
        self.assertEqual(c2.sql, 'SELECT "users"."id" FROM "users" WHERE 1=1')
        self.assertEqual(c2.params, {})

    def test_in_single_scalar(self):
        q = SELECT(users.c.id).FROM(users).WHERE(users.c.org_id.IN(7))
        c = compile(q)
        self.assertEqual(c.sql, 'SELECT "users"."id" FROM "users" WHERE "users"."org_id" IN (:p0)')
        self.assertEqual(c.params, {"p0": 7})

    def test_in_subquery_with_set_query(self):
        q_left = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.active == 1)
        q_right = SELECT(legacy_orgs.c.id).FROM(legacy_orgs).WHERE(legacy_orgs.c.active == 1)
        q = SELECT(users.c.id).FROM(users).WHERE(users.c.org_id.IN(q_left.UNION_ALL(q_right)))
        c = compile(q)
        self.assertIn('IN (SELECT "orgs"."id"', c.sql)
        self.assertIn('UNION ALL', c.sql)

    def test_exists_not_exists_with_set_query(self):
        q_left = SELECT(orgs.c.id).FROM(orgs).WHERE(orgs.c.id == users.c.org_id)
        q_right = SELECT(legacy_orgs.c.id).FROM(legacy_orgs).WHERE(legacy_orgs.c.id == users.c.org_id)
        sub = q_left.UNION(q_right)
        q = SELECT(users.c.id).FROM(users).WHERE(EXISTS(sub), NOT_EXISTS(sub))
        c = compile(q, dialect="mysql")
        self.assertIn('EXISTS (', c.sql)
        self.assertIn('NOT EXISTS (', c.sql)
        self.assertIn('UNION', c.sql)


if __name__ == "__main__":
    unittest.main()
