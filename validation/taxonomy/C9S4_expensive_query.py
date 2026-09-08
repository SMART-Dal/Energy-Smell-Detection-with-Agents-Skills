"""C9.S4 Expensive Query Pattern -- a predicate that defeats its own index.

The previous version compared filtering a Python list after retrieval against
filtering it inside a stub method. Both ran the same comprehension over the same
list, so it measured the cost of a lambda and lost; nothing about it reached the
query engine, which is the only place this root cause lives.

`WHERE lower(email) = ?` cannot use an index on `email`, so the engine scans
every row; with the values already normalised, dropping the call makes the same
query an index lookup. That is the card's first repair example, executed by a
real planner. `sqlite3` is in the standard library and needs no network.

Both variants return the same rows. The emails are stored lower-cased, which is
the precondition the card insists on -- without it the repair silently stops
matching, and the right fix is a functional index instead.
"""

import sqlite3

USERS = 200_000


def _database():
    """One in-memory database with a usable index, built at import."""
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
    connection.executemany(
        "INSERT INTO users VALUES (?, ?)",
        [(i, f"user{i}@example.com") for i in range(USERS)],
    )
    connection.execute("CREATE INDEX users_email ON users (email)")
    connection.commit()
    return connection


DB = _database()


def before(connection, addresses):
    """`lower()` on the column makes the index unusable: a full scan per lookup."""
    out = []
    for address in addresses:
        row = connection.execute(
            "SELECT id FROM users WHERE lower(email) = ?", (address.lower(),)
        ).fetchone()
        out.append(row[0] if row else None)
    return out


def after(connection, addresses):
    """The same question asked of the column directly, so the index applies."""
    out = []
    for address in addresses:
        row = connection.execute(
            "SELECT id FROM users WHERE email = ?", (address.lower(),)
        ).fetchone()
        out.append(row[0] if row else None)
    return out


def cases():
    hits = [f"User{i * 977 % USERS}@Example.com" for i in range(200)]
    return [
        ("many-lookups", lambda: (DB, list(hits))),
        ("one-lookup", lambda: (DB, hits[:1])),
    ]
