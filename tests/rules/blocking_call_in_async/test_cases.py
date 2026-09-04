"""Cases for blocking_call_in_async."""

import threading
import time

import requests
from requests import get
from time import sleep


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


async def poll_status(url):
    # `from time import sleep` binds the function itself, so the call is a
    # bare name and a rule reading only `module.attr` never saw it.
    sleep(1)
    return get(url)


async def run_pipeline():
    # The blocking call is inside a nested `def` handed to a thread, so it
    # never runs on the event loop. That is the repair, not the fault.
    def worker():
        time.sleep(10)

    threading.Thread(target=worker).start()
