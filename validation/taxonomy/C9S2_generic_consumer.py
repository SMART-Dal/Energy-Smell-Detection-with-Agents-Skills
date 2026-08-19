"""C9.S2 Oversized Data Retrieval -- the consumer uses every column.

The card's first `NOT a smell when` clause and what it calls the commonest way
to get this wrong: the consumer is generic, so every column is used by code
that names none of them. Projecting here does not save a transfer, it breaks
the serialiser -- so `after` fetches the same columns and the only difference
is that it asks for them by name.

Expected to read as nothing, which is the answer that stops an agent projecting
a query it has not read the consumer of.
"""

import sqlite3

COLUMNS = 40
ROWS = 20_000
_NAMES = ", ".join(f"c{i}" for i in range(COLUMNS))


def _database():
    connection = sqlite3.connect(":memory:")
    schema = ", ".join(f"c{i} TEXT" for i in range(COLUMNS))
    connection.execute(f"CREATE TABLE wide (id INTEGER PRIMARY KEY, {schema})")
    placeholders = ", ".join("?" * (COLUMNS + 1))
    connection.executemany(
        f"INSERT INTO wide VALUES ({placeholders})",
        [(i, *[f"v{i}-{c}" for c in range(COLUMNS)]) for i in range(ROWS)],
    )
    connection.commit()
    return connection


DB = _database()


def _serialise(row):
    return sum(len(str(value)) for value in row)      # reflects over everything


def before(connection, limit):
    rows = connection.execute("SELECT * FROM wide LIMIT ?", (limit,)).fetchall()
    return sum(_serialise(r) for r in rows)


def after(connection, limit):
    rows = connection.execute(
        f"SELECT id, {_NAMES} FROM wide LIMIT ?", (limit,)).fetchall()
    return sum(_serialise(r) for r in rows)


def cases():
    return [("many-rows", lambda: (DB, ROWS)),
            ("few-rows",  lambda: (DB, 20)),
            ("edge",      lambda: (DB, 0))]
