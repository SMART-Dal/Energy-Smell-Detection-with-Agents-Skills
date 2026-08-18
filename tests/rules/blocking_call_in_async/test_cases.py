"""Cases for blocking_call_in_async."""

import time

import requests


async def poll(url, interval):
    # `time.sleep` stalls the loop; `asyncio.sleep` is the repair.
    while True:
        check(url)
        time.sleep(interval)


async def fetch_all(urls):
    # A synchronous HTTP client inside a coroutine.
    return [requests.get(url) for url in urls]


async def wait_properly(interval):
    # Already awaiting the async form.
    import asyncio
    await asyncio.sleep(interval)


def poll_sync(url, interval):
    # Not a coroutine, so the event loop is not involved.
    while True:
        check(url)
        time.sleep(interval)


async def handle(request):
    # Cheap synchronous CPU work is not blocking the loop in any real sense.
    payload = parse(request.body)
    return await store(payload)
