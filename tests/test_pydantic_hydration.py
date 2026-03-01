import importlib
import unittest
from unittest import mock

from sqlstratum import SELECT, Table, col
from sqlstratum.hydrate import pydantic as pydantic_hydrate
from sqlstratum.runner import SQLiteRunner


class TestPydanticHydration(unittest.TestCase):
    def test_missing_pydantic_raises(self):
        class DummyModel:
            @classmethod
            def model_validate(cls, obj):
                return obj

        with mock.patch(
            "sqlstratum.hydrate.pydantic._import_pydantic",
            side_effect=ImportError("no pydantic"),
        ):
            with self.assertRaises(RuntimeError) as cm:
                pydantic_hydrate.hydrate_model(DummyModel, {"id": 1})
        self.assertIn("pip install sqlstratum[pydantic]", str(cm.exception))

    def test_is_pydantic_available_false_when_missing(self):
        with mock.patch(
            "sqlstratum.hydrate.pydantic._import_pydantic",
            side_effect=ImportError("no pydantic"),
        ):
            self.assertFalse(pydantic_hydrate.is_pydantic_available())

    def test_hydrate_model_and_models(self):
        try:
            pydantic = importlib.import_module("pydantic")
        except Exception:
            self.skipTest("Pydantic not installed")

        class User(pydantic.BaseModel):
            id: int
            email: str

        row = {"id": "1", "email": "a@b.com"}
        user = pydantic_hydrate.hydrate_model(User, row)
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.email, "a@b.com")

        users = pydantic_hydrate.hydrate_models(User, [row])
        self.assertEqual(users, [user])

    def test_using_pydantic_wrapper(self):
        try:
            pydantic = importlib.import_module("pydantic")
        except Exception:
            self.skipTest("Pydantic not installed")

        class User(pydantic.BaseModel):
            id: int
            email: str

        class DummyQuery:
            def __init__(self):
                self.target = None

            def hydrate(self, target):
                self.target = target
                return self

        query = DummyQuery()
        wrapped = pydantic_hydrate.using_pydantic(query)
        result = wrapped.hydrate(User)
        self.assertIs(result, query)
        self.assertIsNotNone(query.target)
        hydrated = query.target({"id": "2", "email": "b@c.com"})
        self.assertIsInstance(hydrated, User)
        self.assertEqual(hydrated.id, 2)
        self.assertEqual(hydrated.email, "b@c.com")

    def test_using_pydantic_with_sqlite_runner(self):
        try:
            pydantic = importlib.import_module("pydantic")
        except Exception:
            self.skipTest("Pydantic not installed")

        class User(pydantic.BaseModel):
            id: int
            email: str

        users = Table("users", col("id", int), col("email", str))
        runner = SQLiteRunner.connect(path=":memory:")
        try:
            runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
            runner.exec_ddl("INSERT INTO users (id, email) VALUES (1, 'a@b.com')")
            q = pydantic_hydrate.using_pydantic(SELECT(users.c.id, users.c.email).FROM(users)).hydrate(User)
            row = runner.fetch_one(q)
            self.assertIsInstance(row, User)
            self.assertEqual(row.id, 1)
            self.assertEqual(row.email, "a@b.com")
        finally:
            runner.connection.close()


if __name__ == "__main__":
    unittest.main()
