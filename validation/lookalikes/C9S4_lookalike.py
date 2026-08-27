"""C9.S4 Expensive Query Pattern -- LOOKS THE SAME, IS NOT: the inputs are not disjoint.

"Using UNION (which sorts and deduplicates) instead of UNION ALL when the
underlying queries produce disjoint results" is the description's own example,
and `C9S4_union_all` measures the swap at +44.2% on tables that really are
disjoint.

These two tables overlap by half. `UNION ALL` returns every duplicate, so the
count is larger than the number of distinct ids and every downstream figure
built on it is inflated. The query is faster and the answer is different.

The word to check is "provably". Disjointness has to come from a constraint --
a partition key, a status column with a check constraint, non-overlapping date
ranges -- and not from the current contents of the tables. Where it cannot be
proved, the deduplication is doing work the caller needs.
"""

import sqlite3

ROWS = 60_000


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE left_side (id INTEGER);"
        "CREATE TABLE right_side (id INTEGER);"
        "CREATE TABLE far_side (id INTEGER);"
    )
    connection.executemany("INSERT INTO left_side VALUES (?)",
                           [(i,) for i in range(ROWS)])
    connection.executemany("INSERT INTO right_side VALUES (?)",
                           [(i,) for i in range(ROWS // 2, ROWS + ROWS // 2)])
    connection.executemany("INSERT INTO far_side VALUES (?)",
                           [(i,) for i in range(ROWS, 2 * ROWS)])
    connection.commit()
    return connection


DB = _database()


def before(connection, other):
    return connection.execute(
        f"SELECT id FROM left_side UNION SELECT id FROM {other}").fetchone()[0], \
        len(connection.execute(
            f"SELECT id FROM left_side UNION SELECT id FROM {other}").fetchall())


def after(connection, other):
    return connection.execute(
        f"SELECT id FROM left_side UNION ALL SELECT id FROM {other}").fetchone()[0], \
        len(connection.execute(
            f"SELECT id FROM left_side UNION ALL SELECT id FROM {other}").fetchall())


def cases():
    return [("overlapping", lambda: (DB, "right_side")),
            ("disjoint",    lambda: (DB, "far_side")),
            ("edge",        lambda: (DB, "far_side"))]
