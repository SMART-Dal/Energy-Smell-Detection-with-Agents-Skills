import random

from dxpy.bindings.dxfile import DXFile

_BUF = 1 << 20  # 1 MiB


def _rand_bytes(n, seed):
    rng = random.Random(seed)
    try:
        return rng.randbytes(n)
    except AttributeError:
        return bytes(bytearray(rng.getrandbits(8) for _ in range(n)))


def _make(bufsize, prefill=0, seed=0):
    """Build a fresh DXFile whose write buffer size is already resolved.

    Setting ``_write_bufsize`` on the instance makes ``_ensure_write_bufsize``
    a no-op, so no apiserver request is made.  A fresh instance per call keeps
    the amount of unflushed data (and therefore the code path) identical on
    every call.
    """
    f = DXFile()
    f._write_bufsize = bufsize
    if prefill:
        f._write_buf.write(_rand_bytes(prefill, seed))
    return f


# Payloads are built once, at module level (never timed).
_D_900K = _rand_bytes(900_000, 1)
_D_500K = _rand_bytes(500_000, 2)
_D_32K = _rand_bytes(32_000, 3)
_D_1K = _rand_bytes(1_000, 4)
_D_250K = _rand_bytes(250_000, 5)
_D_700K = _rand_bytes(700_000, 6)
_D_64K = _rand_bytes(64_000, 7)
_D_10 = _rand_bytes(10, 8)


def checks():
    return [
        # empty write: buffered, nothing to flush
        ("empty", lambda: (_make(_BUF), b"")),
        # single byte
        ("one-byte", lambda: (_make(_BUF), b"\x00")),
        # wrong type: hits the isinstance(data, bytes) assertion
        ("non-bytes", lambda: (_make(_BUF), "not bytes")),
    ]


def cases():
    return [
        # large payload into a very large, empty buffer
        ("big-huge-buffer", lambda: (_make(16 << 20), _D_900K)),
        # large buffer that already holds data, so tell() != 0
        ("big-prefilled", lambda: (_make(16 << 20, 900_000, 11), _D_500K)),
        # payload exactly fills the remaining space (boundary of <=)
        ("exact-remaining", lambda: (_make(1_800_000, 900_000, 12), _D_900K)),
        # small buffer, small payload
        ("small-buffer", lambda: (_make(64 << 10), _D_32K)),
        # medium buffer with a fairly large payload
        ("medium", lambda: (_make(4 << 20), _D_700K)),
        # same as big-huge-buffer but synchronous (multithread=False)
        ("multithread-false", lambda: (_make(8 << 20), _D_900K, False)),
        # tiny buffer and tiny payload
        ("tiny", lambda: (_make(4 << 10), _D_1K)),
        # buffer half full, payload comfortably fits the rest
        ("half-buffer", lambda: (_make(1 << 20, 500_000, 13), _D_250K)),
    ]
