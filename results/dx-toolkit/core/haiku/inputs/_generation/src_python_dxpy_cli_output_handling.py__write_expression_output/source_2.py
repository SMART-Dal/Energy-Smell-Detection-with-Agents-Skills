import random


def _path(name):
    """A fixed output path under WORKDIR; removed so the function can write it."""
    p = WORKDIR / (name + ".out")
    if p.exists():
        p.unlink()
    return str(p)


def _mk_rows(n, cols, seed, none_ratio=0.0):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        d = {}
        for j in range(cols):
            r = rng.random()
            if r < none_ratio:
                d["col{}".format(j)] = None
            elif r < 0.45:
                d["col{}".format(j)] = rng.randint(-10 ** 6, 10 ** 6)
            elif r < 0.75:
                d["col{}".format(j)] = "val_{}_{}".format(i, rng.randint(0, 999))
            else:
                d["col{}".format(j)] = rng.uniform(-1e6, 1e6)
        rows.append(d)
    return rows


def _mk_special_rows(n, seed):
    rng = random.Random(seed)
    specials = [
        "a,b",
        'say "hi"',
        "line1\nline2",
        "tab\there",
        "plain",
        "unicode-\u00e9\u4e2d\u6587",
        "",
        "  spaces  ",
        "semi;colon",
    ]
    rows = []
    for i in range(n):
        d = {}
        for j in range(6):
            r = rng.random()
            if r < 0.15:
                d["c{}".format(j)] = None
            elif r < 0.6:
                d["c{}".format(j)] = specials[rng.randrange(len(specials))]
            else:
                d["c{}".format(j)] = rng.randint(0, 10 ** 9)
        rows.append(d)
    return rows


# ---- module level data, built once (setup is never timed) --------------------
_CSV_ROWS = _mk_rows(3000, 8, 0)
_TSV_ROWS = _mk_rows(3000, 6, 1)
_UNCOMMON_ROWS = _mk_rows(2500, 5, 2)
_COLNAMES_ROWS = _mk_rows(3000, 8, 3)
_COLS = list(_COLNAMES_ROWS[0].keys())
_SPECIAL_ROWS = _mk_special_rows(2500, 4)
_MANYCOLS_ROWS = _mk_rows(300, 200, 5)

_SQL = (
    "SELECT "
    + ", ".join("col{}".format(i) for i in range(200))
    + " FROM t WHERE "
    + " AND ".join("col{} > {}".format(i, i) for i in range(200))
    + " ORDER BY col0;\n"
) * 50


def checks():
    return [
        # empty list -> IndexError inside the function (no file written)
        ("empty-rows", lambda: (_path("chk_empty"), ",", False, [])),
        # a single row
        ("single-row", lambda: (_path("chk_one"), ",", False, [{"a": 1, "b": 2}])),
        # SQL query string written to stdout
        ("sql-stdout", lambda: ("-", ",", True, "SELECT 1 AS x")),
    ]


def cases():
    return [
        ("csv-file", lambda: (_path("csv"), ",", False, _CSV_ROWS)),
        ("tsv-file", lambda: (_path("tsv"), "\t", False, _TSV_ROWS)),
        ("uncommon-delim", lambda: (_path("txt"), "|", False, _UNCOMMON_ROWS)),
        ("sql-file", lambda: (_path("sql"), ",", True, _SQL)),
        ("sql-stdout", lambda: ("-", ",", True, _SQL)),
        (
            "explicit-colnames",
            lambda: call(
                _path("cols"), ",", False, _COLNAMES_ROWS, colnames=list(_COLS)
            ),
        ),
        ("special-chars", lambda: (_path("special"), ",", False, _SPECIAL_ROWS)),
        ("many-columns", lambda: (_path("wide"), ",", False, _MANYCOLS_ROWS)),
    ]
