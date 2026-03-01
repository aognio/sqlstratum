import unittest

from sqlstratum import ASC, DESC, SELECT, Table, col, compile
from sqlstratum.mysql import using_mysql


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("created_at", str),
)


class TestOrderingBuilder(unittest.TestCase):
    def test_single_asc(self):
        q = SELECT(users.c.id).FROM(users).ORDER_BY(users.c.id).ASC()
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id" FROM "users" ORDER BY "users"."id" ASC',
        )

    def test_single_desc(self):
        q = SELECT(users.c.id).FROM(users).ORDER_BY(users.c.id).DESC()
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `users`.`id` FROM `users` ORDER BY `users`.`id` DESC",
        )

    def test_then_chaining(self):
        q = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .ORDER_BY(users.c.created_at)
            .DESC()
            .THEN(users.c.email)
            .ASC()
            .THEN(users.c.id)
            .ASC()
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'ORDER BY "users"."created_at" DESC, "users"."email" ASC, "users"."id" ASC',
        )

    def test_then_chain_allows_other_clauses_after_direction(self):
        q = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .ORDER_BY(users.c.id)
            .ASC()
            .LIMIT(10)
            .OFFSET(0)
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'ORDER BY "users"."id" ASC LIMIT :p0 OFFSET :p1',
        )
        self.assertEqual(compiled.params, {"p0": 10, "p1": 0})

    def test_order_by_requires_direction(self):
        q = SELECT(users.c.id).FROM(users).ORDER_BY(users.c.id)
        with self.assertRaises(ValueError) as cm:
            compile(q)
        self.assertIn("ORDER_BY requires an explicit direction", str(cm.exception))

    def test_legacy_comma_style_still_supported(self):
        q = SELECT(users.c.id, users.c.email).FROM(users).ORDER_BY(
            DESC(users.c.created_at),
            ASC(users.c.email),
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'ORDER BY "users"."created_at" DESC, "users"."email" ASC',
        )

    def test_mixed_style_supported(self):
        q = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .ORDER_BY(DESC(users.c.created_at), users.c.email)
            .ASC()
            .THEN(DESC(users.c.id))
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users" '
            'ORDER BY "users"."created_at" DESC, "users"."email" ASC, "users"."id" DESC',
        )

    def test_multiple_unqualified_order_expressions_raise(self):
        with self.assertRaises(ValueError) as cm:
            SELECT(users.c.id).FROM(users).ORDER_BY(users.c.id, users.c.email)
        self.assertIn("Unqualified ORDER_BY expressions are only allowed as the last item", str(cm.exception))

    def test_wrapped_pending_order_by_still_requires_direction(self):
        q = using_mysql(SELECT(users.c.id).FROM(users).ORDER_BY(users.c.id))
        with self.assertRaises(ValueError) as cm:
            compile(q, dialect="mysql")
        self.assertIn("ORDER_BY requires an explicit direction", str(cm.exception))

    def test_set_query_pending_order_by_requires_direction(self):
        left = SELECT(users.c.id).FROM(users)
        right = SELECT(users.c.id).FROM(users)
        q = left.UNION(right).ORDER_BY(users.c.id)
        with self.assertRaises(ValueError):
            compile(q)


if __name__ == "__main__":
    unittest.main()
