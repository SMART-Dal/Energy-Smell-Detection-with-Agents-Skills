import os
import random

from dxpy.cli.output_handling import write_expression_output


def _mkrows(n, cols, seed, none_ratio=0.0, special_ratio=0.0):
    rng = random.Random(seed)
    keys = [f"col{j}" for j in range(cols)]
    rows = []
    for _ in range(n):
        row = {}
        for k in keys:
            r = rng.random()
            if r < none_ratio:
                row[k] = None
            elif rng.random() < special_ratio:
                row[k] = rng.choice(
                    ["a,b", 'c"d', "e\nf", "g\th", "i;j", "  spaced  ", "plain"]
                )
            else:
                row[k] = rng.randint(-10**9, 10**9)
        rows.append(row)
    return rows


# vizserver-style results: list of dicts, all with the same keys
D1 = _mkrows(20000, 4, 0)
D2 = _mkrows(15000, 6, 1)
D3 = _mkrows(10000, 5, 2, special_ratio=0.4)
D5 = _mkrows(20000, 3, 3)
COLNAMES5 = [f"col{j}" for j in range(3)]
D6 = _mkrows(5000, 20, 4)
D7 = _mkrows(10000, 5, 5, none_ratio=0.3)
D8 = _mkrows(3000, 4, 6)

_rng_sql = random.Random(7)
SQL = (
    "SELECT * FROM expression_data WHERE "
    + " AND ".join(f"col{i} > {_rng_sql.randint(0, 10**6)}" for i in range(40000))
    + ";"
)

P1 = str(WORKDIR / "out_csv_large.csv")
P2 = str(WORKDIR / "out_tsv_large.tsv")
P3 = str(WORKDIR / "out_pipe_special.txt")
P4 = str(WORKDIR / "out_query.sql")
P5 = str(WORKDIR / "out_colnames.csv")
P6 = str(WORKDIR / "out_many_cols.csv")
P7 = str(WORKDIR / "out_none_values.tsv")

CHK_EMPTY = str(WORKDIR / "chk_empty.csv")
CHK_SINGLE = str(WORKDIR / "chk_single.csv")
CHK_SQL = str(WORKDIR / "chk_query.sql")


def _fresh(path):
    try:
        os.remove(path)
    except OSError:
        pass
    return path


def checks():
    return [
        ("empty-rows", lambda: (_fresh(CHK_EMPTY), ",", False, [])),
        ("single-row", lambda: (_fresh(CHK_SINGLE), ",", False, [{"a": 1, "b": None}])),
        ("sql-empty-string", lambda: (_fresh(CHK_SQL), None, True, "")),
    ]


def cases():
    return [
        ("csv-large", lambda: (_fresh(P1), ",", False, D1)),
        ("tsv-large", lambda: (_fresh(P2), "\t", False, D2)),
        ("pipe-special", lambda: (_fresh(P3), "|", False, D3)),
        ("sql-file", lambda: (_fresh(P4), None, True, SQL)),
        ("colnames", lambda: call(_fresh(P5), ",", False, D5, colnames=COLNAMES5)),
        ("many-cols", lambda: (_fresh(P6), ",", False, D6)),
        ("none-values", lambda: (_fresh(P7), "\t", False, D7)),
        ("stdout", lambda: ("-", ",", False, D8)),
    ]
