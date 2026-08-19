"""C9.S2 Oversized Data Retrieval -- `SELECT *` where two columns are used.

Measured against a real engine, so the deserialisation the card calls the
largest and least visible share is actually happening: a wide row becomes one
Python object per column, and the ones nothing reads are allocated and freed
unread.
"""

import sqlite3

COLUMNS = 40
ROWS = 40_000


def _database():
    connection = sqlite3.connect(":memory:")
    names = ", ".join(f"c{i} TEXT" for i in range(COLUMNS))
    connection.execute(f"CREATE TABLE wide (id INTEGER PRIMARY KEY, {names})")
    placeholders = ", ".join("?" * (COLUMNS + 1))
    connection.executemany(
        f"INSERT INTO wide VALUES ({placeholders})",
        [(i, *[f"v{i}-{c}" for c in range(COLUMNS)]) for i in range(ROWS)],
    )
    connection.commit()
    return connection


DB = _database()


def before(connection, limit):
    rows = connection.execute("SELECT * FROM wide LIMIT ?", (limit,)).fetchall()
    return sum(r[0] for r in rows)


def after(connection, limit):
    rows = connection.execute("SELECT id FROM wide LIMIT ?", (limit,)).fetchall()
    return sum(r[0] for r in rows)


def cases():
    return [("many-rows", lambda: (DB, ROWS)),
            ("few-rows",  lambda: (DB, 20)),
            ("edge",      lambda: (DB, 0))]
