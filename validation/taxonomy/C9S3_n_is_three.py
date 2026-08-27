"""C9.S3 Inefficient Retrieval Paths -- N is three.

The N+1 pattern is one query for the list and one per row, and
`C9S3_n_plus_one` measures the join at +79.7% over twenty thousand orders. The
shape is unmistakable and the arithmetic is in the name.

There are three orders on this screen. The prefetch replaces three parameterised
lookups -- which sqlite answers from the primary-key index in microseconds --
with a query that reads the whole customers table and builds a dict of two
thousand entries, of which three are used. Both round-trip counts are small and
the prefetch moves more data than the N+1 did.

The finding needs N. An N+1 over a paginated view, a detail page, or a
three-element list is a shape without a cost, and the repair for it is a bigger
query than the one it replaced.
"""

import sqlite3

CUSTOMERS = 2_000


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT);"
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER);"
    )
    connection.executemany("INSERT INTO customers VALUES (?, ?)",
                           [(i, f"customer-{i}") for i in range(CUSTOMERS)])
    connection.executemany("INSERT INTO orders VALUES (?, ?)",
                           [(i, i % CUSTOMERS) for i in range(20_000)])
    connection.commit()
    return connection


DB = _database()


def before(connection, limit):
    """One query per order -- N of them, and N is the whole question."""
    orders = connection.execute(
        "SELECT id, customer_id FROM orders ORDER BY id LIMIT ?", (limit,)).fetchall()
    out = []
    for order_id, customer_id in orders:
        row = connection.execute(
            "SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        out.append((order_id, row[0]))
    return out


def after(connection, limit):
    """Prefetch: one query for the orders, one for every customer that exists."""
    orders = connection.execute(
        "SELECT id, customer_id FROM orders ORDER BY id LIMIT ?", (limit,)).fetchall()
    names = dict(connection.execute("SELECT id, name FROM customers"))
    return [(order_id, names[customer_id]) for order_id, customer_id in orders]


def cases():
    return [("three-orders",   lambda: (DB, 3)),
            ("many-orders",    lambda: (DB, 4_000)),
            ("edge",           lambda: (DB, 1))]
