```python
import random
import socket

from dxpy.dxlog import DXLogHandler


# ---------------------------------------------------------------------------
# Build a real DXLogHandler instance.  Its __init__ connects two AF_UNIX
# datagram sockets, so we create the log endpoints it expects under WORKDIR
# (the execution environment normally provides /opt/dnanexus/log/*).
# ---------------------------------------------------------------------------
_PRI_PATH = WORKDIR / "dxlog_priority.sock"
_BLK_PATH = WORKDIR / "dxlog_bulk.sock"

for _p in (_PRI_PATH, _BLK_PATH):
    try:
        _p.unlink()
    except OSError:
        pass

_priority_endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
_priority_endpoint.bind(str(_PRI_PATH))
_bulk_endpoint = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
_bulk_endpoint.bind(str(_BLK_PATH))

_HANDLER = DXLogHandler(priority_log_address=str(_PRI_PATH),
                        bulk_log_address=str(_BLK_PATH))


# ---------------------------------------------------------------------------
# Message generators.  json.dumps() (ensure_ascii=True) escapes every
# non-ASCII character, so the number of *bytes* the truncation loop has to
# chew through depends strongly on the character mix.
# ---------------------------------------------------------------------------
_ASCII_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " .,;:!?-_/\\[]{}()=+*&^%$#@~`'\"|<>"
)

_RANGES_CTRL = [(0x00, 0x20)]                              # 1 byte -> \u00XX
_RANGES_ASCII = [(0x20, 0x7F)]                             # 1 byte -> itself
_RANGES_2 = [(0x80, 0x800)]                                # 2 bytes -> \uXXXX
_RANGES_3 = [(0x800, 0xD800), (0xE000, 0x10000)]           # 3 bytes -> \uXXXX
_RANGES_4 = [(0x10000, 0x110000)]                          # 4 bytes -> \uXXXX\uXXXX


def _ascii(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_ASCII_ALPHABET, k=n))


def _from_ranges(n, ranges, seed):
    rng = random.Random(seed)
    out = []
    nr = len(ranges)
    for _ in range(n):
        lo, hi = ranges[rng.randrange(nr)]
        out.append(chr(rng.randrange(lo, hi)))
    return "".join(out)


def _mixed(n, seed):
    rng = random.Random(seed)
    pools = [_RANGES_CTRL, _RANGES_ASCII, _RANGES_2, _RANGES_3, _RANGES_4]
    out = []
    for _ in range(n):
        pool = pools[rng.randrange(len(pools))]
        lo, hi = pool[rng.randrange(len(pool))]
        out.append(chr(rng.randrange(lo, hi)))
    return "".join(out)


# Built once, reused by every call (strings are immutable, no copy needed).
_MSG_ASCII_100K = _ascii(100_000, 0)
_MSG_ASCII_200K = _ascii(200_000, 1)
_MSG_ASCII_BOUNDARY = "a" * 8014
_MSG_CTRL_20K = _from_ranges(20_000, _RANGES_CTRL, 2)
_MSG_2BYTE_20K = _from_ranges(20_000, _RANGES_2, 3)
_MSG_3BYTE_20K = _from_ranges(20_000, _RANGES_3, 4)
_MSG_4BYTE_20K = _from_ranges(20_000, _RANGES_4, 5)
_MSG_MIXED_30K = _mixed(30_000, 6)


def checks():
    return [
        ("empty",       lambda: (_HANDLER, "")),
        ("single-char", lambda: (_HANDLER, "x")),
        ("none",        lambda: (_HANDLER, None)),
    ]


def cases():
    return [
        ("ascii-100k",          lambda: (_HANDLER, _MSG_ASCII_100K)),
        ("ascii-200k",          lambda: (_HANDLER, _MSG_ASCII_200K)),
        ("ascii-boundary-8014", lambda: (_HANDLER, _MSG_ASCII_BOUNDARY)),
        ("control-20k",         lambda: (_HANDLER, _MSG_CTRL_20K)),
        ("two-byte-20k",        lambda: (_HANDLER, _MSG_2BYTE_20K)),
        ("three-byte-20k",      lambda: (_HANDLER, _MSG_3BYTE_20K)),
        ("four-byte-20k",       lambda: (_HANDLER, _MSG_4BYTE_20K)),
        ("mixed-30k",           lambda: (_HANDLER, _MSG_MIXED_30K)),
    ]
```