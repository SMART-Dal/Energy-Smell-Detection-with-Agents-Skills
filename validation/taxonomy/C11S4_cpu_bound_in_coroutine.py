"""C11.S4 Blocking The Main Thread -- CPU work in a coroutine, moved to an
executor.

The card's second repair example, and it warns the result is different in kind:
because the work is CPU-bound and the interpreter lock is held, the executor
improves *responsiveness* rather than throughput. The expectation is therefore
that time does not fall much and may rise, while what the loop can do
concurrently changes -- and the honest reading may be a small loss, which is
the finding.

`concurrent-tasks` is where the blocking has victims; `single-task` is where it
has none and the executor hop can only cost.
"""

import asyncio


def _render(n):
    total = 0
    for i in range(n):
        total += (i * 7919) % 10_007
    return total


def before(tasks, work):
    async def one():
        return _render(work)

    async def main():
        return sum(await asyncio.gather(*[one() for _ in range(tasks)]))

    return asyncio.run(main())


def after(tasks, work):
    async def one():
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _render, work)

    async def main():
        return sum(await asyncio.gather(*[one() for _ in range(tasks)]))

    return asyncio.run(main())


def cases():
    return [("concurrent-tasks", lambda: (40, 20_000)),
            ("single-task",      lambda: (1, 400_000)),
            ("edge",             lambda: (0, 10))]
