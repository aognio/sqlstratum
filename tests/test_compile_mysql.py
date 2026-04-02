import unittest

from sqlstratum import (
    ASC,
    COUNT,
    DELETE,
    DESC,
    EXISTS,
    GROUP_CONCAT,
    INSERT,
    NOT_EXISTS,
    SELECT,
    TOTAL,
    UPDATE,
    Table,
    col,
    compile,
)
from sqlstratum.errors import UnsupportedDialectFeatureError


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
)
admins = Table(
    "admins",
    col("id", int),
    col("email", str),
)


class TestCompileMySQL(unittest.TestCase):
    def test_simple_select_mysql(self):
        q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id == 7)
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `users`.`id`, `users`.`email` FROM `users` WHERE `users`.`id` = %(p0)s",
        )
        self.assertEqual(compiled.params, {"p0": 7})

    def test_dml_mysql(self):
        inserted = compile(
            INSERT(users).VALUES(email="a@b.com", active=1),
            dialect="mysql",
        )
        self.assertEqual(
            inserted.sql,
            "INSERT INTO `users` (`email`, `active`) VALUES (%(p0)s, %(p1)s)",
        )
        self.assertEqual(inserted.params, {"p0": "a@b.com", "p1": 1})

        updated = compile(
            UPDATE(users).SET(email="b@c.com").WHERE(users.c.id == 1),
            dialect="mysql",
        )
        self.assertEqual(
            updated.sql,
            "UPDATE `users` SET `email` = %(p0)s WHERE `users`.`id` = %(p1)s",
        )
        self.assertEqual(updated.params, {"p0": "b@c.com", "p1": 1})

        deleted = compile(DELETE(users).WHERE(users.c.id == 2), dialect="mysql")
        self.assertEqual(
            deleted.sql,
            "DELETE FROM `users` WHERE `users`.`id` = %(p0)s",
        )
        self.assertEqual(deleted.params, {"p0": 2})

    def test_mysql_offset_requires_limit(self):
        q = SELECT(users.c.id).FROM(users).OFFSET(10)
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q, dialect="mysql")
        self.assertIn("OFFSET without LIMIT", str(cm.exception))

    def test_unknown_dialect(self):
        q = SELECT(users.c.id).FROM(users)
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q, dialect="oracle")
        msg = str(cm.exception)
        self.assertIn("dialect", msg)
        self.assertIn("mysql", msg)
        self.assertIn("sqlite", msg)

    def test_sqlite_only_aggregates_raise(self):
        q1 = SELECT(TOTAL(users.c.id).AS("n")).FROM(users)
        with self.assertRaises(UnsupportedDialectFeatureError) as cm1:
            compile(q1, dialect="mysql")
        self.assertIn("TOTAL aggregate", str(cm1.exception))

        q2 = SELECT(GROUP_CONCAT(users.c.email).AS("emails")).FROM(users)
        with self.assertRaises(UnsupportedDialectFeatureError) as cm2:
            compile(q2, dialect="mysql")
        self.assertIn("GROUP_CONCAT aggregate", str(cm2.exception))

    def test_mysql_select_with_group_having_limit_and_offset(self):
        q = (
            SELECT(users.c.active, COUNT(users.c.id).AS("n"))
            .FROM(users)
            .WHERE(users.c.active == 1)
            .GROUP_BY(users.c.active)
            .HAVING(COUNT(users.c.id) > 2)
            .ORDER_BY(DESC(users.c.active))
            .LIMIT(10)
            .OFFSET(5)
        )
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `users`.`active`, COUNT(`users`.`id`) AS `n` "
            "FROM `users` "
            "WHERE `users`.`active` = %(p0)s "
            "GROUP BY `users`.`active` "
            "HAVING COUNT(`users`.`id`) > %(p1)s "
            "ORDER BY `users`.`active` DESC "
            "LIMIT %(p2)s OFFSET %(p3)s",
        )
        self.assertEqual(compiled.params, {"p0": 1, "p1": 2, "p2": 10, "p3": 5})

    def test_mysql_subquery_source_compiles_with_alias(self):
        active_users = (
            SELECT(users.c.id.AS("user_id"))
            .FROM(users)
            .WHERE(users.c.active == 1)
            .AS("active_users")
        )
        q = SELECT(active_users.c.user_id).FROM(active_users)
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `active_users`.`user_id` "
            "FROM (SELECT `users`.`id` AS `user_id` FROM `users` WHERE `users`.`active` = %(p0)s) "
            "AS `active_users`",
        )
        self.assertEqual(compiled.params, {"p0": 1})

    def test_mysql_set_query_orders_by_projection_aliases(self):
        q1 = SELECT(users.c.id.AS("entity_id"), users.c.email.AS("entity_email")).FROM(users)
        q2 = SELECT(admins.c.id.AS("entity_id"), admins.c.email.AS("entity_email")).FROM(admins)
        q = q1.UNION_ALL(q2).ORDER_BY(DESC(users.c.email.AS("entity_email")), ASC(users.c.id.AS("entity_id")))
        compiled = compile(q, dialect="mysql")
        self.assertIn(
            "ORDER BY `entity_email` DESC, `entity_id` ASC",
            compiled.sql,
        )

    def test_mysql_exists_and_not_exists_accept_set_query(self):
        sub = SELECT(users.c.id).FROM(users).UNION(SELECT(admins.c.id).FROM(admins))
        q = SELECT(users.c.id).FROM(users).WHERE(EXISTS(sub), NOT_EXISTS(sub))
        compiled = compile(q, dialect="mysql")
        self.assertIn("EXISTS (SELECT `users`.`id` FROM `users` UNION SELECT `admins`.`id` FROM `admins`)", compiled.sql)
        self.assertIn(
            "NOT EXISTS (SELECT `users`.`id` FROM `users` UNION SELECT `admins`.`id` FROM `admins`)",
            compiled.sql,
        )

    def test_mysql_set_query_orders_by_unqualified_output_column_names(self):
        q1 = SELECT(users.c.id, users.c.email).FROM(users)
        q2 = SELECT(admins.c.id, admins.c.email).FROM(admins)
        q = q1.UNION_ALL(q2).ORDER_BY(ASC(users.c.email), DESC(users.c.id))
        compiled = compile(q, dialect="mysql")
        self.assertIn("ORDER BY `email` ASC, `id` DESC", compiled.sql)


if __name__ == "__main__":
    unittest.main()
