import os
import random

from dxpy.cli.output_handling import write_expression_output


def _fresh(path):
    # the function errors if the file already exists -> remove it first
    try:
        os.remove(path)
    except OSError:
        pass
    return path


_P_CSV = str(WORKDIR / "expr_out_csv.out")
_P_TSV = str(WORKDIR / "expr_out_tsv.out")
_P_PIPE = str(WORKDIR / "expr_out_pipe.out")
_P_SQL = str(WORKDIR / "expr_out_sql.out")
_P_WIDE = str(WORKDIR / "expr_out_wide.out")
_P_COLNAMES = str(WORKDIR / "expr_out_colnames.out")


def _rows(n, ncols, seed, null_ratio=0.05):
    rng = random.Random(seed)
    cols = ["col{}".format(j) for j in range(ncols)]
    rows = []
    for _ in range(n):
        row = {}
        for c in cols:
            r = rng.random()
            if r < null_ratio:
                row[c] = None
            elif r < null_ratio + 0.15:
                row[c] = rng.randint(-10**6, 10**6)
            elif r < null_ratio + 0.2:
                row[c] = rng.choice([True, False])
            else:
                row[c] = "val_{}_{}".format(rng.randint(0, 10**9), rng.randint(0, 99))
        rows.append(row)
    return rows


_ROWS_CSV = _rows(8000, 8, 0)
_ROWS_TSV = _rows(10000, 6, 1)
_ROWS_PIPE = _rows(8000, 5, 2)
_ROWS_STDOUT = _rows(5000, 4, 3)
_ROWS_WIDE = _rows(1000, 50, 4)
_ROWS_COLNAMES = _rows(8000, 6, 5)
_COLNAMES = list(_ROWS_COLNAMES[0].keys())

_SQL = (
    "SELECT "
    + ", ".join("col{}".format(j) for j in range(300))
    + " FROM expression_table WHERE "
    + " AND ".join("col{} > {}".format(j, j) for j in range(300))
    + ";"
)


def checks():
    return [
        ("empty-list", lambda: (_fresh(_P_CSV), ",", False, [])),
        ("single-row", lambda: (_fresh(_P_CSV), ",", False, [{"a": 1, "b": None}])),
        ("no-delim", lambda: (_fresh(_P_CSV), None, False, [{"a": 1}])),
    ]


def cases():
    return [
        ("csv-file", lambda: (_fresh(_P_CSV), ",", False, _ROWS_CSV)),
        ("tsv-file", lambda: (_fresh(_P_TSV), "\t", False, _ROWS_TSV)),
        ("pipe-txt-file", lambda: (_fresh(_P_PIPE), "|", False, _ROWS_PIPE)),
        ("sql-file", lambda: (_fresh(_P_SQL), ",", True, _SQL)),
        ("sql-stdout", lambda: ("-", ",", True, _SQL)),
        ("csv-stdout", lambda: ("-", ",", False, _ROWS_STDOUT)),
        ("wide-cols", lambda: (_fresh(_P_WIDE), ",", False, _ROWS_WIDE)),
        (
            "colnames-given",
            lambda: call(_fresh(_P_COLNAMES), ",", False, _ROWS_COLNAMES, colnames=_COLNAMES),
        ),
    ]
