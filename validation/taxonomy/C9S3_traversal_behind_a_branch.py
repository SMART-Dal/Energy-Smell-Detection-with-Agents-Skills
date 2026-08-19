"""C9.S3 Inefficient Retrieval Paths -- the relation is read for two rows in
ten thousand.

The card's first `NOT a smell when` clause: an N+1 traversal guarded by a
branch that almost never fires costs two round trips, where prefetching fetches
everything. `before` is the guarded N+1 and `after` is the prefetch, so a
negative reading says the repair is worse than the pattern -- and the deciding
fact is the branch's selectivity, not the shape.

`most-need-it` flips that, so both sides of the card's claim are in one file.
"""

import sqlite3

ORDERS = 20_000


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, flagged INTEGER);"
        "CREATE TABLE customers (id INTEGER PRIMARY KEY, email TEXT);"
    )
    connection.executemany("INSERT INTO customers VALUES (?, ?)",
                           [(i, f"c{i}@example.com") for i in range(2_000)])
    connection.commit()
    return connection


DB = _database()


def _load_orders(connection, flag_ratio):
    step = max(1, int(1 / flag_ratio)) if flag_ratio else ORDERS + 1
    return [(i, i % 2_000, 1 if i % step == 0 else 0) for i in range(ORDERS)]


def before(connection, orders):
    total = 0
    for order_id, customer_id, flagged in orders:
        if flagged:
            row = connection.execute(
                "SELECT email FROM customers WHERE id = ?", (customer_id,)).fetchone()
            total += len(row[0])
    return total


def after(connection, orders):
    emails = dict(connection.execute("SELECT id, email FROM customers"))
    total = 0
    for order_id, customer_id, flagged in orders:
        if flagged:
            total += len(emails[customer_id])
    return total


def cases():
    return [("few-need-it",  lambda: (DB, _load_orders(DB, 0.0002))),
            ("most-need-it", lambda: (DB, _load_orders(DB, 1.0))),
            ("edge",         lambda: (DB, []))]
