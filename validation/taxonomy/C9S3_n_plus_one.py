"""C9.S3 Inefficient Retrieval Paths -- N+1 queries against one join.

The previous version stood a dict in for the store, on the theory that "the
per-call cost is the point, not the medium". Measured, that was wrong: with a
dict behind it, `fetch_one` is a method call and a hash probe, batching saves
nothing, and building the batch dict costs -- so the file reported a 5% loss
that was a fact about dicts and not about retrieval.

This card's whole claim is that an external operation costs orders of magnitude
more than anything in-process, so the medium *is* the point. `sqlite3` is in the
standard library, needs no network, and a query really does parse, plan and
execute. It understates a networked store, which has latency on top, so a saving
measured here is a floor rather than a ceiling.

Both variants return the same list of `(order_id, customer_name)` in the same
order.
"""

import sqlite3

CUSTOMERS = 2_000
ORDERS = 20_000


def _database():
    """One in-memory database, built at import so it is outside every window."""
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT);"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER);"
    )
    connection.executemany(
        "INSERT INTO customers VALUES (?, ?)",
        [(i, f"customer-{i}") for i in range(CUSTOMERS)],
    )
    connection.executemany(
        "INSERT INTO orders VALUES (?, ?)",
        [(i, i % CUSTOMERS) for i in range(ORDERS)],
    )
    connection.commit()
    return connection


DB = _database()


def before(connection, limit):
    """One query for the orders, then one more for each order's customer."""
    orders = connection.execute(
        "SELECT id, customer_id FROM orders ORDER BY id LIMIT ?", (limit,)
    ).fetchall()
    out = []
    for order_id, customer_id in orders:
        row = connection.execute(
            "SELECT name FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        out.append((order_id, row[0]))
    return out


def after(connection, limit):
    """One query, joined at the source."""
    return connection.execute(
        "SELECT o.id, c.name FROM orders o "
        "JOIN customers c ON c.id = o.customer_id "
        "ORDER BY o.id LIMIT ?",
        (limit,),
    ).fetchall()


def cases():
    # The connection is read-only here, so one shared handle is safe and
    # rebuilding it per repetition would dominate the measurement.
    return [
        ("many-rows", lambda: (DB, ORDERS)),
        ("few-rows", lambda: (DB, 20)),
        ("one-row", lambda: (DB, 1)),
    ]
