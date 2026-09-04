"""Cases for lock_in_loop."""

import threading


def tally(self, items):
    # Acquired once per item rather than once for the batch.
    for item in items:
        with self._lock:
            self._counts[item.kind] = self._counts.get(item.kind, 0) + 1


def drain(self, queue):
    # The explicit acquire/release pair is the same acquisition.
    while queue:
        self._lock.acquire()
        try:
            self._pending.append(queue.pop())
        finally:
            self._lock.release()


def merge(self, items):
    # Held once around the whole loop: this is the repair.
    with self._lock:
        for item in items:
            self._counts[item.kind] = 1


def snapshot(self):
    # Outside any loop.
    with self._lock:
        return dict(self._counts)


def write_rows(rows, handle):
    # A `with` in a loop that is not a lock at all.
    for row in rows:
        with open(row.path) as source:
            handle.write(source.read())


def build_locks(count):
    # Constructing locks is not acquiring them.
    return [threading.Lock() for _ in range(count)]


def process_chunks(chunks, memory_block):
    # "lock" is a substring of "block", and matching it that way reported an
    # ordinary buffer as lock contention.
    for chunk in chunks:
        with memory_block:
            chunk.write()


def stamp_ticks(ticks, system_clock):
    # And of "clock".
    for t in ticks:
        with system_clock:
            t.stamp()
