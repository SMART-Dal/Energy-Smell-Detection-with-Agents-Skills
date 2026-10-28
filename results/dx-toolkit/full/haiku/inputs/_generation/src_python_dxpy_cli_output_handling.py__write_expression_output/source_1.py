import os
import random

from dxpy.cli.output_handling import write_expression_output

# The repository's callers pass output paths; when arg_output is None the function
# falls back to os.getcwd().  Point cwd at WORKDIR so anything written stays there.
os.chdir(WORKDIR)

_COLS = ["feature_id", "sample_A", "sample_B", "sample_C", "sample_D"]


def _expr_rows(n, cols, seed, none_ratio=0.0):
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        row = {}
        for c in cols:
            if none_ratio and rng.random() < none_ratio:
                row[c] = None
            elif c == "feature_id":
                row[c] = "feat_{}".format(rng.randrange(10 ** 6))
            else:
                row[c] = round(rng.uniform(0.0, 5000.0), 4)
        rows.append(row)
    return rows


def _clean(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _thunk_file(path, delim, data, colnames=None):
    def thunk():
        _clean(path)
        if colnames is None:
            return (path, delim, False, data)
        return call(path, delim, False, data, colnames=colnames)
    return thunk


def _thunk_sql_file(path, sql_text):
    def thunk():
        _clean(path)
        return (path, ",", True, sql_text)
    return thunk


def _thunk_filename(name, delim, data):
    if delim == ",":
        suffix = ".csv"
    elif delim == "\t":
        suffix = ".tsv"
    else:
        suffix = ".txt"
    actual = os.path.join(os.getcwd(), name + suffix)

    def thunk():
        _clean(actual)
        return (None, delim, False, data, True, name)
    return thunk


def _make_sql(n_lines):
    lines = ["SELECT * FROM expression_data WHERE"]
    for i in range(n_lines):
        lines.append("  (sample_{0} > {0} AND sample_{0} < {1}) OR".format(i, i + 1000))
    lines.append("  1=1;")
    return "\n".join(lines)


_ROWS_A = _expr_rows(18000, _COLS, 0)
_ROWS_B = _expr_rows(8000, _COLS, 1)
_ROWS_C = _expr_rows(15000, _COLS, 2)
_ROWS_D = _expr_rows(15000, _COLS, 3)
_ROWS_E = _expr_rows(10000, _COLS, 4)
_ROWS_F = _expr_rows(16000, _COLS, 5, none_ratio=0.3)
_SQL = _make_sql(5000)

_P1 = str(WORKDIR / "out_a.csv")
_P2 = str(WORKDIR / "out_c.txt")
_P3 = str(WORKDIR / "out_d.csv")
_P5 = str(WORKDIR / "out_sql.sql")
_P6 = str(WORKDIR / "out_f.csv")


def checks():
    return [
        ("empty-with-colnames",
         _thunk_file(str(WORKDIR / "chk_empty.csv"), ",", [], colnames=_COLS)),
        ("none-data",
         lambda: (str(WORKDIR / "chk_none.csv"), ",", False, None)),
        ("single-row",
         _thunk_file(str(WORKDIR / "chk_single.csv"), ",", [{"a": 1, "b": 2}])),
    ]


def cases():
    return [
        ("file-csv-18k", _thunk_file(_P1, ",", _ROWS_A)),
        ("stdout-tsv-8k", lambda: ("-", "\t", False, _ROWS_B)),
        ("sql-file", _thunk_sql_file(_P5, _SQL)),
        ("sql-stdout", lambda: ("-", ",", True, _SQL)),
        ("uncommon-delim-15k", _thunk_file(_P2, "|", _ROWS_C)),
        ("colnames-15k", _thunk_file(_P3, ",", _ROWS_D, colnames=_COLS)),
        ("filename-only-10k", _thunk_filename("dataset_out", ",", _ROWS_E)),
        ("none-values-16k", _thunk_file(_P6, ",", _ROWS_F)),
    ]
