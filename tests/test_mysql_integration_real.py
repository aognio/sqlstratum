import os
import unittest

from sqlstratum import ASC, EXISTS, SELECT, Table, col
from sqlstratum.runner_mysql import MySQLRunner
from sqlstratum.runner_mysql_async import AsyncMySQLRunner


users = Table("sqlstratum_it_users", col("id", int), col("email", str), col("active", int))
admins = Table("sqlstratum_it_admins", col("id", int), col("email", str))


def _integration_enabled() -> bool:
    return os.getenv("SQLSTRATUM_RUN_MYSQL_INTEGRATION", "").lower() in {"1", "true", "yes"}


class TestRealMySQLSyncIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _integration_enabled():
            raise unittest.SkipTest("Set SQLSTRATUM_RUN_MYSQL_INTEGRATION=1 to run real MySQL integration tests.")
        url = os.getenv("SQLSTRATUM_TEST_MYSQL_URL_SYNC")
        if not url:
            raise unittest.SkipTest("Set SQLSTRATUM_TEST_MYSQL_URL_SYNC for sync MySQL integration tests.")
        cls.runner = MySQLRunner.connect(url=url)

    @classmethod
    def tearDownClass(cls):
        close = getattr(cls.runner.connection, "close", None)
        if callable(close):
            close()

    def setUp(self):
        self.runner.exec_ddl("DROP TABLE IF EXISTS sqlstratum_it_admins")
        self.runner.exec_ddl("DROP TABLE IF EXISTS sqlstratum_it_users")
        self.runner.exec_ddl(
            "CREATE TABLE sqlstratum_it_users (id INT PRIMARY KEY, email VARCHAR(200) NOT NULL, active INT NOT NULL)"
        )
        self.runner.exec_ddl(
            "CREATE TABLE sqlstratum_it_admins (id INT PRIMARY KEY, email VARCHAR(200) NOT NULL)"
        )
        self.runner.exec_ddl(
            "INSERT INTO sqlstratum_it_users (id, email, active) VALUES "
            "(1, 'a@example.com', 1), (2, 'b@example.com', 0), (3, 'c@example.com', 1)"
        )
        self.runner.exec_ddl(
            "INSERT INTO sqlstratum_it_admins (id, email) VALUES "
            "(1, 'a@example.com'), (4, 'd@example.com')"
        )

    def test_predicates_and_exists_execute(self):
        active_admins = SELECT(admins.c.id).FROM(admins).WHERE(admins.c.id == users.c.id)
        query = (
            SELECT(users.c.id, users.c.email)
            .FROM(users)
            .WHERE(users.c.active == 1, EXISTS(active_admins))
            .ORDER_BY(ASC(users.c.id))
        )
        rows = self.runner.fetch_all(query)
        self.assertEqual(rows, [{"id": 1, "email": "a@example.com"}])

    def test_set_operations_execute(self):
        q_users = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id.IN([1, 3]))
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        query = q_users.UNION_ALL(q_admins).ORDER_BY(ASC(users.c.id))
        rows = self.runner.fetch_all(query)
        self.assertEqual([row["id"] for row in rows], [1, 1, 3, 4])


class TestRealMySQLAsyncIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if not _integration_enabled():
            self.skipTest("Set SQLSTRATUM_RUN_MYSQL_INTEGRATION=1 to run real MySQL integration tests.")
        url = os.getenv("SQLSTRATUM_TEST_MYSQL_URL_ASYNC")
        if not url:
            self.skipTest("Set SQLSTRATUM_TEST_MYSQL_URL_ASYNC for async MySQL integration tests.")
        self.runner = await AsyncMySQLRunner.connect(url=url)

        await self.runner.exec_ddl("DROP TABLE IF EXISTS sqlstratum_it_admins")
        await self.runner.exec_ddl("DROP TABLE IF EXISTS sqlstratum_it_users")
        await self.runner.exec_ddl(
            "CREATE TABLE sqlstratum_it_users (id INT PRIMARY KEY, email VARCHAR(200) NOT NULL, active INT NOT NULL)"
        )
        await self.runner.exec_ddl(
            "CREATE TABLE sqlstratum_it_admins (id INT PRIMARY KEY, email VARCHAR(200) NOT NULL)"
        )
        await self.runner.exec_ddl(
            "INSERT INTO sqlstratum_it_users (id, email, active) VALUES "
            "(1, 'a@example.com', 1), (2, 'b@example.com', 0), (3, 'c@example.com', 1)"
        )
        await self.runner.exec_ddl(
            "INSERT INTO sqlstratum_it_admins (id, email) VALUES "
            "(1, 'a@example.com'), (4, 'd@example.com')"
        )

    async def asyncTearDown(self):
        close = getattr(self.runner.connection, "close", None)
        if callable(close):
            close()

    async def test_async_set_operations_execute(self):
        q_users = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.id.IN([1, 3]))
        q_admins = SELECT(admins.c.id, admins.c.email).FROM(admins)
        query = q_users.UNION_ALL(q_admins).ORDER_BY(ASC(users.c.id))
        rows = await self.runner.fetch_all(query)
        self.assertEqual([row["id"] for row in rows], [1, 1, 3, 4])

