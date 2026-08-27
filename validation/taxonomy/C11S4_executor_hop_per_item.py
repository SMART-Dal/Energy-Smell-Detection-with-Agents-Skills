"""C11.S4 Blocking The Main Thread -- an executor hop per item
costs more than the block it removes.

"Offload heavy work to background threads" is the description, and
`C11S4_blocking_two_calls_down` does it correctly: it moves the *whole*
enrichment pass to an executor in one hop, and the card says explicitly that a
per-record hop would cost more than the lookup does.

This is the per-record hop. Every `run_in_executor` submits to a pool, wakes a
worker, waits on a future and hands the result back through the event loop, and
the work being offloaded is a few microseconds of arithmetic. The loop is
unblocked and the total energy is higher, item by item.

The unit to offload is the batch, not the element. Where the blocking call is
short and frequent, the honest finding is often "this does not need an executor
at all" -- and where it is long, one hop around the loop beats N hops inside it.
"""

import asyncio


def _classify(value):
    total = 0
    for i in range(1, 40):
        total += (value * i) % 17
    return total % 5


def before(values):
    async def main():
        total = 0
        for value in values:
            total += _classify(value)         # blocking, in the coroutine
            await asyncio.sleep(0)
        return total

    return asyncio.run(main())


def after(values):
    async def main():
        loop = asyncio.get_running_loop()
        total = 0
        for value in values:
            total += await loop.run_in_executor(None, _classify, value)
        return total

    return asyncio.run(main())


def cases():
    return [("many-items", lambda: (list(range(4_000)),)),
            ("few-items",  lambda: (list(range(40)),)),
            ("edge",       lambda: ([],))]
