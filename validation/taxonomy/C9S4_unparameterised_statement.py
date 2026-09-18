"""C9.S4 Expensive Query Pattern -- a statement the plan cache can never hit.

Interpolating the id into the SQL text makes every iteration a textually
distinct statement, so the engine parses and plans each one from scratch. The
parameterised form is one statement with a bound value, prepared once and
reused.

This is a different cost from the other two measured files in this root cause:
they change what the engine *does* with a query, where this changes how often
it has to decide what to do at all. It is also the one shape here that is an
injection vector, which is usually the reason it gets fixed.
"""

import sqlite3

ROWS = 20_000


def _database():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, total INTEGER)")
    connection.executemany(
        "INSERT INTO orders VALUES (?, ?)", [(i, i * 3) for i in range(ROWS)]
    )
    connection.commit()
    return connection


DB = _database()


def before(connection, order_ids):
    total = 0
    for order_id in order_ids:
        row = connection.execute(
            f"SELECT total FROM orders WHERE id = {order_id}"
        ).fetchone()
        total += row[0]
    return total


def after(connection, order_ids):
    total = 0
    for order_id in order_ids:
        row = connection.execute(
            "SELECT total FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        total += row[0]
    return total


def cases():
    return [("many-statements", lambda: (DB, list(range(4_000)))),
            ("few-statements",  lambda: (DB, list(range(40))))]
