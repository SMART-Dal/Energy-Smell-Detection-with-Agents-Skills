"""C9.S3 Inefficient Retrieval Paths -- the join that returns more than N+1 did.

The card's second `NOT a smell when` clause and the reflex repair being the
wrong one: joining across two one-to-many relations returns items x notes rows
per order, which can be far more data than the round trips cost. The
prefetch-style answer -- one query per relation, joined in Python -- is what
`before` does here, and `after` is the single join.

A negative reading is the card being right. That is the point of the file.
"""

import sqlite3

ORDERS = 400
ITEMS = 8
NOTES = 8


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY);"
        "CREATE TABLE items (order_id INTEGER, sku TEXT);"
        "CREATE TABLE notes (order_id INTEGER, body TEXT);"
    )
    connection.executemany("INSERT INTO orders VALUES (?)", [(i,) for i in range(ORDERS)])
    connection.executemany("INSERT INTO items VALUES (?, ?)",
                           [(i, f"sku{j}") for i in range(ORDERS) for j in range(ITEMS)])
    connection.executemany("INSERT INTO notes VALUES (?, ?)",
                           [(i, f"note{j}") for i in range(ORDERS) for j in range(NOTES)])
    connection.commit()
    return connection


DB = _database()


def before(connection, limit):
    """One query per relation, joined in Python -- `prefetch_related` style."""
    items, notes = {}, {}
    for order_id, sku in connection.execute(
            "SELECT order_id, sku FROM items WHERE order_id < ?", (limit,)):
        items.setdefault(order_id, []).append(sku)
    for order_id, body in connection.execute(
            "SELECT order_id, body FROM notes WHERE order_id < ?", (limit,)):
        notes.setdefault(order_id, []).append(body)
    total = 0
    for (order_id,) in connection.execute(
            "SELECT id FROM orders WHERE id < ?", (limit,)):
        total += len(items.get(order_id, ())) + len(notes.get(order_id, ()))
    return total


def after(connection, limit):
    """One join, which multiplies the two relations against each other."""
    seen_items, seen_notes = set(), set()
    for order_id, sku, body in connection.execute(
        "SELECT o.id, i.sku, n.body FROM orders o "
        "JOIN items i ON i.order_id = o.id "
        "JOIN notes n ON n.order_id = o.id WHERE o.id < ?", (limit,)
    ):
        seen_items.add((order_id, sku))
        seen_notes.add((order_id, body))
    return len(seen_items) + len(seen_notes)


def cases():
    # All three cases used to pass `(DB,)`, so the file measured one thing three
    # times. The fan-out is what decides this root cause, and the fan-out grows
    # with the number of orders the join covers: items x notes rows per order.
    return [("many-orders", lambda: (DB, ORDERS)),
            ("few-orders",  lambda: (DB, 20)),
            ("one-order",   lambda: (DB, 1))]
