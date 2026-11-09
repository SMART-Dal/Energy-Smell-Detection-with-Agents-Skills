```python
import os
import random

from dxpy.cli.output_handling import write_expression_output  # noqa: F401


def _clean(path):
    if os.path.exists(path):
        os.remove(path)


def _special(rng, i, j):
    r = rng.random()
    if r < 0.10:
        return None
    if r < 0.30:
        return "a,b{}".format(i)
    if r < 0.50:
        return 'he said "hi" {}'.format(i)
    if r < 0.70:
        return "line1\nline2_{}".format(i)
    if r < 0.85:
        return "tab\tsep{}".format(i)
    return "plain_{}_{}".format(i, j)


def _gen_rows(n, cols, seed, special=False):
    rng = random.Random(seed)
    names = ["col{}".format(j) for j in range(cols)]
    rows = []
    for i in range(n):
        row = {}
        for j in range(cols):
            row[names[j]] = _special(rng, i, j) if special else rng.randint(-10 ** 9, 10 ** 9)
        rows.append(row)
    return rows


def _big_sql(n_terms):
    parts = [
        "SELECT col_{0} FROM t_{0} WHERE a = {0} AND b LIKE '%x%' AND c IS NOT NULL".format(i)
        for i in range(n_terms)
    ]
    return " UNION ALL ".join(parts) + ";"


def _file_thunk(path, delim, sql, data, **kw):
    def thunk():
        _clean(path)
        return call(path, delim, sql, data, **kw)
    return thunk


_CSV_WIDE = _gen_rows(12000, 6, 0)
_TSV = _gen_rows(10000, 8, 1)
_PIPE = _gen_rows(15000, 5, 2)
_REORDER = _gen_rows(12000, 7, 3)
_REORDER_COLS = ["col{}".format(j) for j in range(6, -1, -1)]
_QUOTED = _gen_rows(8000, 6, 4, special=True)
_SQL_BIG = _big_sql(12000)
_SQL_SMALL = _big_sql(800)
_STDOUT_ROWS = _gen_rows(3000, 4, 5)

_P1 = str(WORKDIR / "case_csv_wide.csv")
_P2 = str(WORKDIR / "case_tsv.tsv")
_P3 = str(WORKDIR / "case_pipe.txt")
_P4 = str(WORKDIR / "case_reorder.csv")
_P5 = str(WORKDIR / "case_quoted.csv")
_P6 = str(WORKDIR / "case_query.sql")


def checks():
    return [
        ("empty-rows-list", _file_thunk(str(WORKDIR / "chk_empty.csv"), ",", False, [])),
        ("single-row-none", _file_thunk(str(WORKDIR / "chk_one.csv"), ",", False, [{"x": None, "y": "1"}])),
        ("empty-sql", _file_thunk(str(WORKDIR / "chk_sql.sql"), ",", True, "")),
    ]


def cases():
    return [
        ("csv-file-wide", _file_thunk(_P1, ",", False, _CSV_WIDE)),
        ("tsv-file", _file_thunk(_P2, "\t", False, _TSV)),
        ("pipe-delim-txt", _file_thunk(_P3, "|", False, _PIPE)),
        ("reordered-colnames", _file_thunk(_P4, None, False, _REORDER, colnames=_REORDER_COLS)),
        ("quoting-stress", _file_thunk(_P5, ",", False, _QUOTED)),
        ("sql-to-file", _file_thunk(_P6, ",", True, _SQL_BIG)),
        ("sql-to-stdout", lambda: call("-", ",", True, _SQL_SMALL)),
        ("csv-to-stdout", lambda: call("-", ",", False, _STDOUT_ROWS)),
    ]
```