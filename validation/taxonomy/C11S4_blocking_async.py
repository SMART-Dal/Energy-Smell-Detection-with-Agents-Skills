"""C11.S4 Blocking The Main Thread -- time.sleep inside a coroutine.

The clearest energy-vs-time case in the taxonomy: `time.sleep` stalls the whole
loop so nothing else progresses, while `asyncio.sleep` yields.
"""

import asyncio
import time


def before(n, delay):
    async def one():
        time.sleep(delay)
        return 1

    async def main():
        return sum(await asyncio.gather(*[one() for _ in range(n)]))

    return asyncio.run(main())


def after(n, delay):
    async def one():
        await asyncio.sleep(delay)
        return 1

    async def main():
        return sum(await asyncio.gather(*[one() for _ in range(n)]))

    return asyncio.run(main())


def cases():
    return [("many-waits", lambda: (200, 0.002)), ("one-wait", lambda: (1, 0.002))]
