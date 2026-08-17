"""A socket, not a file: the same leak with a different opener.

Worth its own case because sockets are the handles that actually hurt.  A file
descriptor left to the collector is a nuisance; a socket left to the collector
holds a connection open on the peer as well, and a prober called in a loop runs
the process out of descriptors long before memory becomes an issue.

`sock.connect(...)` is deliberately here as well: it is a call to something the
rule knows as an opener, but it is a statement rather than a binding, so it
must not produce a second report on the same handle.
"""

from __future__ import annotations

import socket


def probe(host, port, timeout=1.0):
    """Ask one host whether it answers, and return its banner."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # EXPECT
    sock.settimeout(timeout)
    sock.connect((host, port))
    sock.sendall(b"PING\r\n")
    return sock.recv(64).decode("ascii", "replace")
