"""C11.S4 Blocking The Main Thread -- the blocking call is two helpers below
the coroutine.

The card's cross-unit example: `publish` is a clean coroutine with an `await`
in its loop and nothing in it blocks. The blocking sits two calls down, in a
helper whose name suggests a dictionary lookup. This is what the shape looks
like in real code and it is only findable by reading the call path -- nothing
sees past `self._enrich(record)`.

The repair moves the whole enrichment pass to an executor rather than the one
call, because a per-record executor hop costs more than the lookup does.
"""

import asyncio
import time


class Reporter:
    __slots__ = ("delay", "sent")

    def __init__(self, delay):
        self.delay = delay
        self.sent = 0

    def _region_for(self, key):
        time.sleep(self.delay)                 # blocking: a file seek and read
        return key % 7

    def _enrich(self, record):
        return record + self._region_for(record)

    async def _send(self, record):
        await asyncio.sleep(0)
        self.sent += record
        return record


def before(records, delay):
    reporter = Reporter(delay)

    async def publish():
        for record in records:
            await reporter._send(reporter._enrich(record))
        return reporter.sent

    return asyncio.run(publish())


def after(records, delay):
    reporter = Reporter(delay)

    async def publish():
        loop = asyncio.get_running_loop()
        enriched = await loop.run_in_executor(
            None, lambda: [reporter._enrich(r) for r in records])
        for record in enriched:
            await reporter._send(record)
        return reporter.sent

    return asyncio.run(publish())


def cases():
    return [("many-records", lambda: (list(range(400)), 0.001)),
            ("one-record",   lambda: ([1], 0.001)),
            ("edge",         lambda: ([], 0.001))]
