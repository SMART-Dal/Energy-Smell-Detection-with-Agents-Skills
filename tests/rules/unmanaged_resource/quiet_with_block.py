"""The repair: every handle acquired in a `with` header.

This is the code the rule is asking for, so it has to stay quiet on it.  The
multi-item `with` and the `async with` are here because both put the opener
somewhere other than a plain assignment, and a rule that walked calls instead
of bindings would report all three.
"""

from __future__ import annotations

import json
import socket


def load_config(path):
    """Read a JSON config from disk."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def copy_file(source, destination):
    """Copy one file to another, both managed by the same statement."""
    with open(source, "rb") as reader, open(destination, "wb") as writer:
        writer.write(reader.read())


def banner(host, port, timeout=1.0):
    """Read a peer's greeting and hang up."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((host, port))
        return sock.recv(64)


async def fetch(session, url):
    """Read one response body, with the response managed by the caller's session."""
    async with session.get(url) as response:
        return await response.json()
