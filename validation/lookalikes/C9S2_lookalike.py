"""C9.S2 Oversized Data Retrieval -- LOOKS THE SAME, IS NOT: the rows nobody displays
are the rows the total is made of.

"Retrieving full result sets to display a small subset" and "issuing unbounded
queries without LIMIT" are both in the description, and `C9S2_select_columns`
measures a real projection at +95.5%.

The page shows twenty rows and the response also carries a total. Adding `LIMIT
20` to the query that feeds both makes the page right and the total the sum of
twenty rows. Nothing raises; the number on the screen is simply smaller than the
number in the database, which is the kind of defect that survives review.

Before bounding a query, find every consumer of its result. A `LIMIT` is correct
for a query whose rows are all rendered, and wrong for one that is also reduced
-- and the fix there is two queries, one of them an aggregate the engine can
answer from an index.
"""

import sqlite3

ROWS = 200_000


def _database():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, amount INTEGER)")
    connection.executemany("INSERT INTO sales VALUES (?, ?)",
                           [(i, i % 997) for i in range(ROWS)])
    connection.commit()
    return connection


DB = _database()


def before(connection, page_size):
    rows = connection.execute("SELECT id, amount FROM sales ORDER BY id").fetchall()
    return [r[0] for r in rows[:page_size]], sum(r[1] for r in rows)


def after(connection, page_size):
    rows = connection.execute(
        "SELECT id, amount FROM sales ORDER BY id LIMIT ?", (page_size,)).fetchall()
    return [r[0] for r in rows[:page_size]], sum(r[1] for r in rows)


def cases():
    return [("small-page", lambda: (DB, 20)),
            ("whole-page", lambda: (DB, ROWS)),
            ("edge",       lambda: (DB, 1))]
