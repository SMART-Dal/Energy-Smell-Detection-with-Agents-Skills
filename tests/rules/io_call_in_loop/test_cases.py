"""Cases for io_call_in_loop."""

import requests


def load_rows(cursor, queries):
    # An unambiguous name: nothing else is called `fetchall`.
    out = []
    for query in queries:
        cursor.execute(query)
        out.append(cursor.fetchall())
    return out


def save_each(self, rows):
    # Ambiguous name on a receiver that plainly lives outside the process.
    for row in rows:
        self.conn.execute("INSERT INTO events VALUES (?)", (row.id,))


def fetch_all(urls):
    # The receiver is an imported I/O module.
    return [requests.get(url) for url in urls]


def collect_cached(keys, cache):
    # `dict.get` in a loop is the commonest expression in Python.
    out = []
    for key in keys:
        value = cache.get(key)
        if value is not None:
            out.append(value)
    return out


def index_rows(self, rows):
    # `.get()` on a plain attribute is not I/O.
    out = {}
    for row in rows:
        out[row.key] = self.rows.get(row.key)
    return out


def load_once(cursor, query):
    # Outside any loop.
    cursor.execute(query)
    return cursor.fetchall()


def append_all(target, rows):
    # `insert` on a list is not a database write.
    for row in rows:
        target.insert(0, row)
    return target
