import os
import random

from dxpy.exceptions import err_exit


def _cleanup(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _prep(path, args):
    """Remove the output file (the function errors out if it exists), then
    return the argument tuple for the call."""
    _cleanup(path)
    return args


def _rows(n, cols, seed, null_ratio=0.0, special=False):
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        row = {}
        for c in range(cols):
            name = "col{}".format(c)
            if rng.random() < null_ratio:
                row[name] = None
            elif special:
                row[name] = rng.choice(
                    [
                        "a,b",
                        'he said "hi"',
                        "line1\nline2",
                        "plain value",
                        "tab\there",
                        "semi;colon",
                        "  padded  ",
                    ]
                )
            else:
                row[name] = rng.randint(0, 10 ** 6)
        rows.append(row)
    return rows


# ---- module level workloads (built once) ----------------------------------
_CSV_ROWS = _rows(10000, 5, 0)
_TSV_ROWS = _rows(8000, 6, 1)
_PIPE_ROWS = _rows(6000, 5, 2)
_NULL_ROWS = _rows(6000, 8, 3, null_ratio=0.5)
_SPECIAL_ROWS = _rows(5000, 6, 4, special=True)
_NULL_COLNAMES = ["col{}".format(i) for i in range(7, -1, -1)]

_SQL = (
    "SELECT "
    + ", ".join("col{}".format(i) for i in range(60))
    + " FROM expression_data WHERE "
    + " AND ".join("col{} > {}".format(i, i * 13) for i in range(60))
    + " ORDER BY col0;"
)

_P_CSV = WORKDIR / "out_csv.csv"
_P_TSV = WORKDIR / "out_tsv.tsv"
_P_PIPE = WORKDIR / "out_pipe.txt"
_P_SQL = WORKDIR / "out_query.sql"
_P_NULL = WORKDIR / "out_null.csv"
_P_SPECIAL = WORKDIR / "out_special.csv"


def checks():
    empty = WORKDIR / "chk_empty.csv"
    single = WORKDIR / "chk_single.csv"
    sqlbad = WORKDIR / "chk_bad.sql"
    return [
        # list of dicts with no rows -> indexing [0] fails
        ("empty-list", lambda: _prep(empty, (empty, ",", False, []))),
        # a single tiny row, with a None value
        ("single-row", lambda: _prep(single, (single, ",", False, [{"a": 1, "b": None}]))),
        # arg_sql=True but the payload is not a string
        ("sql-non-string", lambda: _prep(sqlbad, (sqlbad, ",", True, ["not", "a", "string"]))),
    ]


def cases():
    return [
        # plain CSV file output, the common path
        ("csv-file", lambda: _prep(_P_CSV, (_P_CSV, ",", False, _CSV_ROWS))),
        # tab delimiter -> .tsv
        ("tsv-file", lambda: _prep(_P_TSV, (_P_TSV, "\t", False, _TSV_ROWS))),
        # uncommon delimiter -> .txt (save_uncommon_delim_to_txt default True)
        ("pipe-file", lambda: _prep(_P_PIPE, (_P_PIPE, "|", False, _PIPE_ROWS))),
        # SQL query written to a file
        ("sql-file", lambda: _prep(_P_SQL, (_P_SQL, ",", True, _SQL))),
        # SQL query written to stdout
        ("sql-stdout", lambda: ("-", ",", True, _SQL)),
        # list of dicts written to stdout
        ("csv-stdout", lambda: ("-", ",", False, _CSV_ROWS)),
        # many None values plus explicit (reordered) column names
        (
            "nulls-colnames",
            lambda: _prep(
                _P_NULL,
                (_P_NULL, ",", False, _NULL_ROWS, True, None, err_exit, _NULL_COLNAMES),
            ),
        ),
        # values needing quoting: commas, quotes, newlines, tabs
        ("special-chars", lambda: _prep(_P_SPECIAL, (_P_SPECIAL, ",", False, _SPECIAL_ROWS))),
    ]
