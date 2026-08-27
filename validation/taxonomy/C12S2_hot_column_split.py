"""C12.S2 Sparse Element Access -- one field of a wide record, over a large
array.

The file this replaces measured hoisting a gather out of a loop. That is a real
saving, but it is C3.S2 wearing this card's name: the win came from doing the
gather once instead of twenty times, and nothing about it was a cache-line
question.

This is the cache-line question. `samples` is a structured array of eight
float64 fields, so consecutive `value` fields are 64 bytes apart: every read
pulls in a whole line and uses eight of its sixty-four bytes. The repair is the
one the card names -- store the field that is actually read as its own
contiguous array -- so the same values are walked with a stride of 8 bytes
instead of 64. Same elements, same count, same order; only the spacing differs.

Both layouts are built at import, outside every measured window, because
building them costs far more than walking them and would otherwise be all this
measured. The repair a reader would commit is a change of declaration, and that
is what is compared.

`cache-resident` is the precondition seen from the other side: a small array is
already in L2, there are no misses to avoid, and the split can only cost the
memory it duplicates.
"""

import numpy as np

ROWS = 2_000_000
_FIELDS = [(f"f{i}", np.float64) for i in range(8)]


def _interleaved(n):
    array = np.zeros(n, dtype=np.dtype(_FIELDS))
    array["f0"] = np.arange(n, dtype=np.float64)
    return array


_WIDE = _interleaved(ROWS)
_COLUMN = np.ascontiguousarray(_WIDE["f0"])

_WIDE_SMALL = _interleaved(2_000)
_COLUMN_SMALL = np.ascontiguousarray(_WIDE_SMALL["f0"])


def before(wide, _column, count):
    """One field read out of a 64-byte record: one useful value per cache line."""
    return round(float(wide["f0"][:count].sum()), 3)


def after(_wide, column, count):
    """The same values, stored contiguously: eight useful values per line."""
    return round(float(column[:count].sum()), 3)


def cases():
    return [("large",          lambda: (_WIDE, _COLUMN, ROWS)),
            ("cache-resident", lambda: (_WIDE_SMALL, _COLUMN_SMALL, 2_000)),
            ("edge",           lambda: (_WIDE_SMALL, _COLUMN_SMALL, 1))]
