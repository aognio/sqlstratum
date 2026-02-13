import unittest

from sqlstratum import INSERT, UPDATE, DELETE, Table, col, compile


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("full_name", str),
    col("active", int),
)


class TestCompileDML(unittest.TestCase):
    def test_insert(self):
        q = INSERT(users).VALUES(email="a@b.com", full_name="A", active=1)
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'INSERT INTO "users" ("email", "full_name", "active") VALUES (:p0, :p1, :p2)',
        )
        self.assertEqual(compiled.params, {"p0": "a@b.com", "p1": "A", "p2": 1})

    def test_update(self):
        q = UPDATE(users).SET(full_name="B").WHERE(users.c.id == 1)
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'UPDATE "users" SET "full_name" = :p0 WHERE "users"."id" = :p1',
        )
        self.assertEqual(compiled.params, {"p0": "B", "p1": 1})

    def test_delete(self):
        q = DELETE(users).WHERE(users.c.id == 1)
        compiled = compile(q)
        self.assertEqual(
            compiled.sql,
            'DELETE FROM "users" WHERE "users"."id" = :p0',
        )
        self.assertEqual(compiled.params, {"p0": 1})


if __name__ == "__main__":
    unittest.main()
