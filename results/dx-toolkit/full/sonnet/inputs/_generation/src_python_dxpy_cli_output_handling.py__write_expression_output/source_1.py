import random

from dxpy.cli.output_handling import write_expression_output

_OUT = WORKDIR / "expr_outputs"
_OUT.mkdir(exist_ok=True)


def _fresh(name):
    """Return a path under WORKDIR that does not exist yet (remove leftovers)."""
    p = _OUT / name
    if p.exists():
        p.unlink()
    return str(p)


def _numeric_rows(n, cols, seed):
    rng = random.Random(seed)
    names = ["col{}".format(j) for j in range(cols)]
    rows = []
    for _ in range(n):
        row = {}
        for j in range(cols):
            if j % 3 == 0:
                row[names[j]] = rng.randint(-10 ** 6, 10 ** 6)
            elif j % 3 == 1:
                row[names[j]] = round(rng.uniform(-1000.0, 1000.0), 6)
            else:
                row[names[j]] = "s" + str(rng.randrange(10 ** 5))
        rows.append(row)
    return names, rows


def _quoting_rows(n, seed):
    rng = random.Random(seed)
    names = ["a", "b", "c", "d", "e", "f"]
    specials = [",", '"', "\n", "\r\n", ";", "|", "\t", "'"]

    def val():
        parts = []
        for _ in range(rng.randint(0, 5)):
            parts.append(chr(rng.randrange(97, 123)))
            parts.append(rng.choice(specials))
        return "".join(parts)

    return names, [{nm: val() for nm in names} for _ in range(n)]


def _unicode_rows(n, seed):
    rng = random.Random(seed)
    names = ["name", "cafe", "emoji", "num", "nonecol", "mixed", "long", "short"]
    words = ["naive", "日本語", "Ω≈ç√", "😀🎉", "Straße", "Привет", "café"]
    rows = []
    for _ in range(n):
        row = {}
        for nm in names:
            r = rng.random()
            if r < 0.15:
                row[nm] = None
            elif r < 0.40:
                row[nm] = rng.choice(words)
            elif r < 0.70:
                row[nm] = rng.randint(0, 10 ** 9)
            else:
                row[nm] = rng.choice(words) + str(rng.randrange(1000))
        rows.append(row)
    return names, rows


_SQL = (
    "SELECT "
    + ", ".join("col{}".format(j) for j in range(200))
    + " FROM "
    + ", ".join("tbl{}".format(j) for j in range(50))
    + " WHERE "
    + " AND ".join("col{} > {}".format(j, j) for j in range(200))
    + " GROUP BY "
    + ", ".join("col{}".format(j) for j in range(0, 200, 7))
    + ";"
)


def checks():
    return [
        ("empty-no-colnames", lambda: call(_fresh("empty.csv"), ",", False, [])),
        ("sql-not-a-string", lambda: call(_fresh("bad.sql"), ",", True, [{"a": 1}])),
        (
            "bad-delim-no-save",
            lambda: call(
                _fresh("bad.txt"),
                "|",
                False,
                [{"a": 1}],
                save_uncommon_delim_to_txt=False,
            ),
        ),
    ]


def cases():
    names1, rows1 = _numeric_rows(5000, 8, 1)
    names2, rows2 = _numeric_rows(4000, 6, 2)
    names3, rows3 = _numeric_rows(4000, 6, 3)
    names4, rows4 = _numeric_rows(5000, 10, 4)
    names6, rows6 = _numeric_rows(300, 150, 6)
    names7, rows7 = _quoting_rows(3000, 7)
    names8, rows8 = _unicode_rows(4000, 8)

    return [
        ("csv-typical", lambda: call(_fresh("typical.csv"), ",", False, rows1)),
        ("tsv", lambda: call(_fresh("data.tsv"), "\t", False, rows2)),
        ("pipe-txt", lambda: call(_fresh("pipe.txt"), "|", False, rows3)),
        (
            "colnames-given",
            lambda: call(_fresh("named.csv"), ",", False, rows4, colnames=list(names4)),
        ),
        ("sql-to-file", lambda: call(_fresh("query.sql"), ",", True, _SQL)),
        ("wide-150-cols", lambda: call(_fresh("wide.csv"), ",", False, rows6)),
        ("quoting-stress", lambda: call(_fresh("quote.csv"), ",", False, rows7)),
        ("stdout-unicode-none", lambda: call("-", ",", False, rows8)),
    ]
