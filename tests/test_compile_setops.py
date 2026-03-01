import unittest

from sqlstratum import SELECT, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError


users = Table("users", col("id", int), col("email", str), col("org_id", int))
admins = Table("admins", col("id", int), col("email", str), col("org_id", int))
orgs = Table("orgs", col("id", int))


class TestCompileSetOps(unittest.TestCase):
    def test_union_all_with_order_and_limit(self):
        q1 = SELECT(users.c.id, users.c.email).FROM(users)
        q2 = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q1.UNION_ALL(q2).ORDER_BY(users.c.email).ASC().LIMIT(5)
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'UNION ALL '
            'SELECT "admins"."id", "admins"."email" FROM "admins" '
            'ORDER BY "users"."email" ASC LIMIT :p0',
        )
        self.assertEqual(compiled.params, {"p0": 5})

    def test_intersect_and_except(self):
        q1 = SELECT(users.c.id).FROM(users)
        q2 = SELECT(admins.c.id).FROM(admins)
        intersected = compile(q1.INTERSECT(q2), dialect="mysql")
        self.assertIn("INTERSECT", intersected.sql)
        excepted = compile(q1.EXCEPT(q2), dialect="mysql")
        self.assertIn("EXCEPT", excepted.sql)

    def test_right_join_mysql(self):
        q = (
            SELECT(users.c.id, orgs.c.id.AS("org_id"))
            .FROM(users)
            .RIGHT_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
        )
        compiled = compile(q, dialect="mysql")
        self.assertIn("RIGHT JOIN", compiled.sql)

    def test_full_join_mysql_raises(self):
        q = (
            SELECT(users.c.id, orgs.c.id.AS("org_id"))
            .FROM(users)
            .FULL_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
        )
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q, dialect="mysql")
        self.assertIn("FULL OUTER JOIN", str(cm.exception))

    def test_right_join_sqlite_raises(self):
        q = (
            SELECT(users.c.id, orgs.c.id.AS("org_id"))
            .FROM(users)
            .RIGHT_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
        )
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q, dialect="sqlite")
        self.assertIn("RIGHT OUTER JOIN", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
