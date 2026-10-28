```python
import os
import random

from dxpy.cli.output_handling import write_expression_output

_OUTDIR = WORKDIR / "expr_out"
_OUTDIR.mkdir(parents=True, exist_ok=True)


def _mk_rows(n, keys, seed, special=False):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        d = {}
        for name in keys:
            if special:
                r = rng.random()
                if r < 0.08:
                    d[name] = ""
                elif r < 0.16:
                    d[name] = None
                elif r < 0.24:
                    d[name] = 'a,b"c\nd'
                elif r < 0.30:
                    d[name] = rng.randint(0, 10 ** 12)
                else:
                    d[name] = "val_%d_%s" % (i, name)
            else:
                d[name] = rng.randint(-10 ** 12, 10 ** 12)
        rows.append(d)
    return rows


_KEYS_A = ["col%d" % j for j in range(5)]
_KEYS_B = ["col%d" % j for j in range(4)]
_KEYS_C = ["col%d" % j for j in range(15)]
_KEYS_E = ["col%d" % j for j in range(6)]
_KEYS_G = ["col%d" % j for j in range(25)]
_KEYS_H = ["col0"]

_ROWS_A = _mk_rows(40_000, _KEYS_A, 0)
_ROWS_B = _mk_rows(40_000, _KEYS_B, 1)
_ROWS_C = _mk_rows(15_000, _KEYS_C, 2)
_ROWS_E = _mk_rows(25_000, _KEYS_E, 4, special=True)
_ROWS_G = _mk_rows(8_000, _KEYS_G, 5)
_ROWS_H = _mk_rows(60_000, _KEYS_H, 6)
_COLS_A_REV = list(reversed(_KEYS_A))

_SQL_TEXT = ("SELECT " + ", ".join(_KEYS_C) + " FROM t WHERE x > 0;\n") * 40_000


def _clean(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _case(path, *rest, **kw):
    def thunk():
        _clean(path)
        if kw:
            return call(path, *rest, **kw)
        return (path,) + rest
    return thunk


def checks():
    return [
        ("no-rows", _case(_OUTDIR / "chk_empty.csv", ",", False, [])),
        ("sql-not-string", _case(_OUTDIR / "chk_sql.sql", ",", True, [{"a": 1}])),
        ("single-row", _case(_OUTDIR / "chk_one.csv", ",", False, [{"a": 1, "b": 2}])),
    ]


def cases():
    return [
        ("csv-5col-40k", _case(_OUTDIR / "a.csv", ",", False, _ROWS_A)),
        ("tsv-4col-40k", _case(_OUTDIR / "b.tsv", "\t", False, _ROWS_B)),
        ("semicolon-txt-15col", _case(_OUTDIR / "c.txt", ";", False, _ROWS_C)),
        ("colnames-reordered", _case(_OUTDIR / "d.csv", ",", False, _ROWS_A,
                                     colnames=_COLS_A_REV)),
        ("special-values-6col", _case(_OUTDIR / "e.csv", ",", False, _ROWS_E)),
        ("sql-large-query", _case(_OUTDIR / "f.sql", ",", True, _SQL_TEXT)),
        ("wide-25col-8k", _case(_OUTDIR / "g.csv", ",", False, _ROWS_G)),
        ("single-col-60k", _case(_OUTDIR / "h.csv", ",", False, _ROWS_H)),
    ]
```