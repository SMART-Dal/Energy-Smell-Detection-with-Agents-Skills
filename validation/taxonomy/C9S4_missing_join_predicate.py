"""C9.S4 Expensive Query Pattern -- a Cartesian product from a missing join
condition.

The card's first named structure, and it insists the finding needs the row
counts: a Cartesian product between two three-row tables is nine rows. So the
two cases are the same query against a table that makes it expensive and one
that makes it trivial, which is the difference between a finding and a shape.
"""

import sqlite3


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE big_a (id INTEGER, key INTEGER);"
        "CREATE TABLE big_b (id INTEGER, key INTEGER);"
        "CREATE TABLE tiny_a (id INTEGER, key INTEGER);"
        "CREATE TABLE tiny_b (id INTEGER, key INTEGER);"
    )
    connection.executemany("INSERT INTO big_a VALUES (?, ?)",
                           [(i, i % 500) for i in range(1_500)])
    connection.executemany("INSERT INTO big_b VALUES (?, ?)",
                           [(i, i % 500) for i in range(1_500)])
    connection.executemany("INSERT INTO tiny_a VALUES (?, ?)",
                           [(i, i) for i in range(3)])
    connection.executemany("INSERT INTO tiny_b VALUES (?, ?)",
                           [(i, i) for i in range(3)])
    connection.commit()
    return connection


DB = _database()


def before(connection, big):
    a, b = ("big_a", "big_b") if big else ("tiny_a", "tiny_b")
    rows = connection.execute(f"SELECT x.id, y.id FROM {a} x, {b} y").fetchall()
    return sum(1 for xi, yi in rows if xi == yi)


def after(connection, big):
    a, b = ("big_a", "big_b") if big else ("tiny_a", "tiny_b")
    rows = connection.execute(
        f"SELECT x.id, y.id FROM {a} x JOIN {b} y ON y.id = x.id").fetchall()
    return len(rows)


def cases():
    return [("big-tables",  lambda: (DB, True)),
            ("tiny-tables", lambda: (DB, False)),
            ("edge",        lambda: (DB, False))]
