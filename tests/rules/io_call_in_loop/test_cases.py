"""Cases for io_call_in_loop."""

import asyncio

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


async def fetch_together(session, urls):
    # The repair, not the smell: the round trips overlap under `gather`.
    return await asyncio.gather(*(session.get(url) for url in urls))


async def fetch_one_at_a_time(session, urls):
    # Same calls, awaited in place, so they are still serial.
    return [await session.get(url) for url in urls]


def scrape(urls, out):
    # `from urllib.request import urlopen` binds the function itself, so the
    # call is an `ast.Name` and an attribute-only rule never saw it.
    for u in urls:
        out.append(urlopen(u))


def rewind_frames(frames, buffer):
    # An in-memory undo buffer. `rollback` was trusted on its name alone.
    for f in frames:
        if f.is_corrupt:
            buffer.rollback()


async def poll_each(worklist, session):
    # `wait_for` awaits one awaitable with a deadline; it dispatches nothing,
    # so a timeout should not silence the rule.
    for item in worklist:
        await asyncio.wait_for(session.get(item), timeout=1.0)


def render_to_memory(rows):
    # Quiet. `stream` is in IO_RECEIVERS and `write` is in AMBIGUOUS_IO_CALLS,
    # so the name heuristic reports this as leaving the process -- but the unit
    # binds it to `StringIO`, which never does. A binding the unit can see
    # outranks the name; a parameter still falls back to the name, because
    # nothing here can tell what was passed in.
    import io
    stream = io.StringIO()
    for row in rows:
        stream.write(row.text)
    return stream.getvalue()


def drain_a_local_queue(items):
    # Quiet for the same reason: `pool` names a `queue.Queue`, not a connection
    # pool.
    import queue
    pool = queue.Queue()
    for item in items:
        pool.get()
