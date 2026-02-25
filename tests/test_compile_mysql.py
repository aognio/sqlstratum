import unittest

from sqlstratum import DELETE, INSERT, SELECT, UPDATE, TOTAL, GROUP_CONCAT, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
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


if __name__ == "__main__":
    unittest.main()
