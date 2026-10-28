import random

from dxpy.utils.pretty_print import format_table


def _table(nrows, ncols, seed, max_len=20, unicode_frac=0.0, dup_frac=0.0):
    rng = random.Random(seed)
    rows = []
    pool = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            k = rng.random()
            if dup_frac and k < dup_frac and pool:
                row.append(rng.choice(pool))
                continue
            k2 = rng.random()
            if k2 < unicode_frac:
                val = "".join(rng.choice("abc\n\t\\\x01\x7fé") for _ in range(rng.randint(1, max_len)))
            elif k2 < 0.45:
                val = rng.randint(-10**9, 10**9)
            elif k2 < 0.75:
                val = round(rng.uniform(-1e6, 1e6), 4)
            else:
                val = "".join(rng.choice("abcdefghij") for _ in range(rng.randint(1, max_len)))
            row.append(val)
            if len(pool) < 200:
                pool.append(val)
        rows.append(row)
    return rows


def _names(n, seed, long_frac=0.0):
    rng = random.Random(seed)
    names = []
    for i in range(n):
        if long_frac and rng.random() < long_frac:
            names.append("a_very_long_column_name_%d_that_exceeds_width" % i)
        else:
            names.append("col_%d" % i)
    return names


_TYPICAL = _table(100, 8, 0)
_LARGE = _table(4000, 12, 1)
_UNICODE = _table(600, 6, 2, unicode_frac=0.75, max_len=25)
_TRUNC = _table(900, 10, 3, max_len=40)
_SPEC_TABLE = _table(400, 6, 4)
_DIMS = _table(1200, 7, 5)
_NOHEAD = _table(2500, 9, 6)
_DUPS = _table(3000, 6, 7, dup_frac=0.5)

_COL_SPECS = [
    {'name': 'count', 'type': 'integer'},
    {'name': 'ratio', 'type': 'float'},
    {'name': 'label', 'type': 'string'},
    {'name': 'flag', 'type': 'boolean'},
    {'name': 'u32', 'type': 'uint32'},
]


def checks():
    return [
        ("empty-with-names", lambda: ([], ["A", "B"])),
        ("single-cell", lambda: ([["x"]],)),
        ("none-and-odd-types", lambda: ([[None, 1.5, True], [2, None, False]], ["a", "b", "c"])),
    ]


def cases():
    return [
        ("typical-named",
         lambda: (_TYPICAL, _names(8, 0))),
        ("large-12col",
         lambda: (_LARGE, _names(12, 1))),
        ("unicode-heavy",
         lambda: (_UNICODE, _names(6, 2, long_frac=0.34))),
        ("narrow-truncation",
         lambda: call(_TRUNC, _names(10, 3), max_col_width=8)),
        ("column-specs",
         lambda: call(_SPEC_TABLE, column_specs=_COL_SPECS)),
        ("report-dimensions",
         lambda: call(_DIMS, _names(7, 5), report_dimensions=True)),
        ("no-column-names",
         lambda: (_NOHEAD,)),
        ("many-duplicates",
         lambda: call(_DUPS, _names(6, 7), max_col_width=16)),
    ]
