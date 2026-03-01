import unittest

from sqlstratum import GROUP_CONCAT, TOTAL, SELECT, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError
from sqlstratum.sqlite import using_sqlite


users = Table("users", col("id", int), col("email", str), col("org_id", int))
orgs = Table("orgs", col("id", int))


class TestDialectCapabilitiesContract(unittest.TestCase):
    def test_portable_predicates_compile_for_both_dialects(self):
        query = (
            SELECT(users.c.id)
            .FROM(users)
            .WHERE(users.c.id.IN([1, 2]), users.c.org_id.BETWEEN(10, 20))
        )
        sqlite_compiled = compile(query, dialect="sqlite")
        mysql_compiled = compile(query, dialect="mysql")
        self.assertIn("IN", sqlite_compiled.sql)
        self.assertIn("BETWEEN", sqlite_compiled.sql)
        self.assertIn("IN", mysql_compiled.sql)
        self.assertIn("BETWEEN", mysql_compiled.sql)

    def test_sqlite_only_aggregates_enforced_by_dialect(self):
        sqlite_query = using_sqlite(
            SELECT(TOTAL(users.c.id).AS("total_id"), GROUP_CONCAT(users.c.email).AS("emails")).FROM(users)
        )
        sqlite_compiled = compile(sqlite_query, dialect="sqlite")
        self.assertIn("TOTAL", sqlite_compiled.sql)
        self.assertIn("GROUP_CONCAT", sqlite_compiled.sql)

        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(SELECT(TOTAL(users.c.id).AS("total_id")).FROM(users), dialect="mysql")
        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(SELECT(GROUP_CONCAT(users.c.email).AS("emails")).FROM(users), dialect="mysql")

    def test_right_join_capability(self):
        query = SELECT(users.c.id, orgs.c.id.AS("org_id")).FROM(users).RIGHT_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
        mysql_compiled = compile(query, dialect="mysql")
        self.assertIn("RIGHT JOIN", mysql_compiled.sql)

        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(query, dialect="sqlite")

    def test_full_join_is_explicitly_rejected(self):
        query = SELECT(users.c.id, orgs.c.id.AS("org_id")).FROM(users).FULL_JOIN(orgs, ON=users.c.org_id == orgs.c.id)
        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(query, dialect="mysql")
        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(query, dialect="sqlite")

    def test_offset_without_limit_rejected_for_mysql_select_and_set_query(self):
        select_query = SELECT(users.c.id).FROM(users).OFFSET(5)
        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(select_query, dialect="mysql")

        set_query = SELECT(users.c.id).FROM(users).UNION(SELECT(users.c.id).FROM(users)).OFFSET(5)
        with self.assertRaises(UnsupportedDialectFeatureError):
            compile(set_query, dialect="mysql")


if __name__ == "__main__":
    unittest.main()
