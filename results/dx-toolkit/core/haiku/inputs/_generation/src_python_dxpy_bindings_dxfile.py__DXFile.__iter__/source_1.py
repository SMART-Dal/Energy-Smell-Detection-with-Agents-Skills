import random
from io import BytesIO

from dxpy.bindings.dxfile import DXFile

# ---------------------------------------------------------------------------
# Helpers to build realistic ASCII file content (the repository stores text
# files; DXFile.__iter__ reads them line by line).
# ---------------------------------------------------------------------------

# Map every byte to a printable ASCII character (32..126), so the payload has
# no embedded newlines/control bytes and no multi-byte UTF-8 sequences that
# could be split across a read chunk boundary.
_TBL = bytes((32 + (b % 95)) for b in range(256))


def _rand_ascii(n, rng):
    if n <= 0:
        return ""
    return rng.getrandbits(8 * n).to_bytes(n, "big").translate(_TBL).decode("ascii")


# A pool of random text used to slice lines out of (keeps generation fast).
_POOL = _rand_ascii(300_000, random.Random(0x5EED))


def _text(n_lines, lo, hi, seed, trailing_newline=True):
    rng = random.Random(seed)
    plen = len(_POOL)
    out = []
    for _ in range(n_lines):
        L = rng.randint(lo, hi)
        if L >= plen:
            out.append(_rand_ascii(L, rng))
        else:
            start = rng.randrange(plen - L)
            out.append(_POOL[start:start + L])
    s = "\n".join(out)
    if trailing_newline:
        s += "\n"
    return s


def _make_file(data, bufsize, binary=False):
    """Build a read-mode DXFile whose read buffer already holds all the data."""
    f = DXFile(mode="rb" if binary else "r", read_buffer_size=bufsize)
    f._binary_mode = binary
    f._file_length = len(data)
    f._pos = 0
    f._read_buf = BytesIO(data)
    return f


# label, n_lines, min_len, max_len, read_buffer_size, trailing_newline, crlf
_SPECS = [
    ("many-lines",       20000, 20,     60,     8192,  True,  False),
    ("long-lines",       300,   1500,   2000,   8192,  True,  False),
    ("small-buffer",     15000, 20,     80,     512,   True,  False),
    ("no-trailing-nl",   16000, 30,     70,     4096,  False, False),
    ("blank-lines",      40000, 0,      3,      2048,  True,  False),
    ("crlf-lines",       15000, 20,     60,     8192,  True,  True),
    ("single-long-line", 1,     500000, 500000, 4096,  False, False),
    ("big-many-lines",   40000, 10,     30,     16384, True,  False),
]


def _build_cases():
    result = []
    for idx, (label, n, lo, hi, buf, trail, crlf) in enumerate(_SPECS):
        text = _text(n, lo, hi, 1000 + idx, trailing_newline=trail)
        if crlf:
            text = text.replace("\n", "\r\n")
        data = text.encode("ascii")
        f = _make_file(data, buf)

        def thunk(f=f, data=data):
            # __iter__ consumes the buffer and advances _pos: restore both so
            # every repeated call does exactly the same work.
            f._read_buf = BytesIO(data)
            f._pos = 0
            return (f,)

        result.append((label, thunk))
    return result


_CASES = _build_cases()


def cases():
    return list(_CASES)


def checks():
    def mk(data, binary=False, buf=8192):
        return _make_file(data, buf, binary=binary)

    return [
        ("empty-file", lambda: (mk(b""),)),
        ("binary-mode", lambda: (mk(b"hello\nworld\n", binary=True),)),
        ("one-line-no-newline", lambda: (mk(b"only one line"),)),
    ]
