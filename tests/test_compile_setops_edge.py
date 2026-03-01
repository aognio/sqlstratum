import unittest

from sqlstratum import ASC, DESC, SELECT, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError


users = Table("users", col("id", int), col("email", str), col("org_id", int))
admins = Table("admins", col("id", int), col("email", str), col("org_id", int))


class TestCompileSetOpsEdge(unittest.TestCase):
    def test_setop_with_primary_ordering_style(self):
        q1 = SELECT(users.c.id, users.c.email).FROM(users)
        q2 = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q1.UNION_ALL(q2).ORDER_BY(DESC(users.c.email), ASC(users.c.id)).LIMIT(10).OFFSET(5)
        c = compile(q)
        self.assertIn('UNION ALL', c.sql)
        self.assertIn('ORDER BY "users"."email" DESC, "users"."id" ASC', c.sql)
        self.assertEqual(c.params, {"p0": 10, "p1": 5})

    def test_setop_with_fluent_ordering_style(self):
        q1 = SELECT(users.c.id).FROM(users)
        q2 = SELECT(admins.c.id).FROM(admins)
        q = q1.INTERSECT(q2).ORDER_BY(users.c.id).ASC()
        c = compile(q, dialect="mysql")
        self.assertIn('INTERSECT', c.sql)
        self.assertIn('ORDER BY `users`.`id` ASC', c.sql)

    def test_nested_setop_is_compiled(self):
        q1 = SELECT(users.c.id).FROM(users)
        q2 = SELECT(admins.c.id).FROM(admins)
        q3 = SELECT(users.c.org_id).FROM(users)
        q = q1.UNION(q2).EXCEPT(q3)
        c = compile(q)
        self.assertIn('UNION', c.sql)
        self.assertIn('EXCEPT', c.sql)

    def test_mysql_setop_offset_without_limit_raises(self):
        q1 = SELECT(users.c.id).FROM(users)
        q2 = SELECT(admins.c.id).FROM(admins)
        q = q1.UNION_ALL(q2).OFFSET(10)
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q, dialect="mysql")
        self.assertIn("OFFSET without LIMIT", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
