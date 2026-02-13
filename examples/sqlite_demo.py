import sqlite3

from sqlstratum import SELECT, INSERT, COUNT, Table, col, Runner


users = Table(
    "users",
    col("id", int),
    col("email", str),
    col("active", int),
)


def main() -> None:
    conn = sqlite3.connect(":memory:")
    runner = Runner(conn)
    runner.exec_ddl("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, active INTEGER)")

    runner.execute(INSERT(users).VALUES(email="a@b.com", active=1))
    runner.execute(INSERT(users).VALUES(email="c@d.com", active=0))

    q = SELECT(users.c.id, users.c.email).FROM(users).WHERE(users.c.active.is_true())
    print(runner.fetch_all(q))

    q2 = SELECT(COUNT(users.c.id).AS("n")).FROM(users)
    print(runner.fetch_one(q2))


if __name__ == "__main__":
    main()
