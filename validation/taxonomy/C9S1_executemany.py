"""C9.S1 Fragmented I/O Operations -- one insert per row against `executemany`.

The card's named bulk form, measured against a real engine rather than a stub.
Each `execute` parses and plans; `executemany` does that once and loops in C.
It also names the trade the finding has to state: one transaction that fails
loses everything where a thousand lose one.
"""

import sqlite3


def _fresh():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE events (id INTEGER, payload TEXT)")
    return connection


def before(rows):
    connection = _fresh()
    for row in rows:
        connection.execute("INSERT INTO events VALUES (?, ?)", row)
    connection.commit()
    return connection.execute("SELECT count(*) FROM events").fetchone()[0]


def after(rows):
    connection = _fresh()
    connection.executemany("INSERT INTO events VALUES (?, ?)", rows)
    connection.commit()
    return connection.execute("SELECT count(*) FROM events").fetchone()[0]


def cases():
    return [("many-rows", lambda: ([(i, f"p{i}") for i in range(20_000)],)),
            ("few-rows",  lambda: ([(i, f"p{i}") for i in range(20)],))]
