import unittest

from sqlstratum import SELECT, Table, col, compile
from sqlstratum.errors import UnsupportedDialectFeatureError
from sqlstratum.mysql import using_mysql
from sqlstratum.runner import SQLiteRunner
from sqlstratum.sqlite import GROUP_CONCAT, TOTAL, using_sqlite


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("org_id", int),
)


class TestDialectWrapperInteractions(unittest.TestCase):
    def test_wrapper_preserves_chain_after_where(self):
        q = using_mysql(SELECT(users.c.id, users.c.email).FROM(users)).WHERE(users.c.id == 5)
        compiled = compile(q, dialect="mysql")
        self.assertEqual(
            compiled.sql,
            "SELECT `users`.`id`, `users`.`email` FROM `users` WHERE `users`.`id` = %(p0)s",
        )
        self.assertEqual(compiled.params, {"p0": 5})

    def test_wrapper_preserves_chain_after_hydrate(self):
        q = using_sqlite(SELECT(users.c.id, users.c.email).FROM(users)).hydrate(dict)
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT "users"."id", "users"."email" FROM "users"',
        )
        self.assertEqual(compiled.params, {})

    def test_nested_same_wrapper_is_allowed(self):
        q = using_sqlite(using_sqlite(SELECT(users.c.id).FROM(users)))
        compiled = compile(q)
        self.assertEqual(compiled.sql, 'SELECT "users"."id" FROM "users"')

    def test_nested_conflicting_wrapper_raises(self):
        q = using_sqlite(using_mysql(SELECT(users.c.id).FROM(users)))
        with self.assertRaises(UnsupportedDialectFeatureError) as cm:
            compile(q)
        self.assertIn("conflicting nested dialect bindings", str(cm.exception))

    def test_sqlite_specific_aggregates_work_with_wrapper(self):
        q = using_sqlite(
            SELECT(
                TOTAL(users.c.id).AS("total_id"),
                GROUP_CONCAT(users.c.email, ",").AS("emails"),
            ).FROM(users)
        )
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'SELECT TOTAL("users"."id") AS "total_id", GROUP_CONCAT("users"."email", :p0) AS "emails" FROM "users"',
        )
        self.assertEqual(compiled.params, {"p0": ","})

    def test_sqlite_runner_accepts_wrapped_hydrated_query(self):
        runner = SQLiteRunner.connect(path=":memory:")
        try:
            runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, org_id INTEGER)")
            runner.exec_ddl("INSERT INTO users (id, email, org_id) VALUES (1, 'a@b.com', 7)")

            q = (
                using_sqlite(SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.org_id == 7))
                .hydrate(lambda m: f"{m['id']}|{m['email']}")
            )
            result = runner.fetch_one(q)
            self.assertEqual(result, "1|a@b.com")
        finally:
            runner.connection.close()


if __name__ == "__main__":
    unittest.main()
