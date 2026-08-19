"""C9.S4 Expensive Query Pattern -- `UNION` where `UNION ALL` would do.

The card names this directly: `UNION` sorts and deduplicates where `UNION ALL`
does not, and the repair is only correct when the inputs are provably disjoint.
Here they are -- the two tables hold different id ranges -- and `overlapping`
is the case where they are not, so `after` keeps `UNION` on that path and the
file measures the precondition rather than assuming it.
"""

import sqlite3

ROWS = 60_000


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE active (id INTEGER);"
        "CREATE TABLE archived (id INTEGER);"
        "CREATE TABLE overlap_a (id INTEGER);"
        "CREATE TABLE overlap_b (id INTEGER);"
    )
    connection.executemany("INSERT INTO active VALUES (?)", [(i,) for i in range(ROWS)])
    connection.executemany("INSERT INTO archived VALUES (?)",
                           [(i,) for i in range(ROWS, 2 * ROWS)])
    connection.executemany("INSERT INTO overlap_a VALUES (?)", [(i,) for i in range(ROWS)])
    connection.executemany("INSERT INTO overlap_b VALUES (?)",
                           [(i,) for i in range(ROWS // 2, ROWS + ROWS // 2)])
    connection.commit()
    return connection


DB = _database()


def before(connection, disjoint):
    left, right = ("active", "archived") if disjoint else ("overlap_a", "overlap_b")
    return len(connection.execute(
        f"SELECT id FROM {left} UNION SELECT id FROM {right}").fetchall())


def after(connection, disjoint):
    if disjoint:
        return len(connection.execute(
            "SELECT id FROM active UNION ALL SELECT id FROM archived").fetchall())
    return len(connection.execute(
        "SELECT id FROM overlap_a UNION SELECT id FROM overlap_b").fetchall())


def cases():
    return [("disjoint",    lambda: (DB, True)),
            ("overlapping", lambda: (DB, False)),
            ("edge",        lambda: (DB, True))]
