import random
from io import BytesIO

from dxpy.bindings.dxfile import DXFile

# ---------------------------------------------------------------------------
# Realistic ASCII text payloads (repository stores text files; __iter__ reads
# them line by line).  Every byte maps to printable ASCII so no embedded
# control bytes / multi-byte sequences confuse the byte<->char accounting.
# ---------------------------------------------------------------------------
_TBL = bytes((32 + (b % 95)) for b in range(256))

_POOL_RNG = random.Random(0x5EED)
_POOL = _POOL_RNG.getrandbits(8 * 200000).to_bytes(200000, "big").translate(_TBL).decode("ascii")


def _rand_ascii(n, rng):
    if n <= 0:
        return ""
    return rng.getrandbits(8 * n).to_bytes(n, "big").translate(_TBL).decode("ascii")


def _text(n_lines, lo, hi, seed, trailing_newline=True):
    rng = random.Random(seed)
    plen = len(_POOL)
    out = []
    for _ in range(n_lines):
        L = rng.randint(lo, hi)
        if L >= plen:
            out.append(_rand_ascii(L, rng))
        else:
            start = rng.randrange(plen - L + 1)
            out.append(_POOL[start:start + L])
    s = "\n".join(out)
    if trailing_newline:
        s += "\n"
    return s


def _make_file(data, binary=False):
    """Read-mode DXFile whose read buffer already holds the whole payload.

    ``_read_bufsize`` is set to the payload length so the single prefilled
    part satisfies every read: read() never requests a download and therefore
    never calls describe()/the network.
    """
    f = DXFile(mode="rb" if binary else "r")
    f._dxid = "file-000000000000000000000000"
    f._binary_mode = binary
    f._file_length = len(data)
    f._pos = 0
    f._read_buf = BytesIO(data)
    f._read_bufsize = max(len(data), 1)
    f._cur_part = 1
    return f


# label, n_lines, min_len, max_len, trailing_newline, crlf
_SPECS = [
    ("many-lines",        20000, 20,      60,       True,  False),
    ("long-lines",        300,   1500,    2000,     True,  False),
    ("no-trailing-nl",    16000, 30,      70,       False, False),
    ("blank-lines",       40000, 0,       3,        True,  False),
    ("crlf-lines",        15000, 20,      60,       True,  True),
    ("single-long-line",  1,     2000000, 2000000,  False, False),
    ("big-many-lines",    40000, 10,      30,       True,  False),
    ("very-long-lines",   200,   3000,    5000,     True,  False),
]


def _build_cases():
    result = []
    for idx, (label, n, lo, hi, trail, crlf) in enumerate(_SPECS):
        text = _text(n, lo, hi, 1000 + idx, trailing_newline=trail)
        if crlf:
            text = text.replace("\n", "\r\n")
        data = text.encode("ascii")
        f = _make_file(data)

        def thunk(f=f, data=data):
            # read() advances _pos and drains the buffer; restore both so
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
    return [
        ("empty-file", lambda: (_make_file(b""),)),
        ("binary-mode", lambda: (_make_file(b"hello\nworld\n", binary=True),)),
        ("one-line-no-newline", lambda: (_make_file(b"only one line"),)),
    ]
