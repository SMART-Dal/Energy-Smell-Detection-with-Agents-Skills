# Inputs for news/src/python/evaluate.py::read_impressions_file, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from evaluate import read_impressions_file


def _write(path, n_lines, seed, imp_spec, pool, prefix="N", width=6):
    rng = random.Random(seed)
    with path.open("w", encoding="utf-8") as f:
        for i in range(n_lines):
            k = imp_spec(rng) if callable(imp_spec) else imp_spec
            user_id = "U{}".format(rng.randrange(10**7))
            impressions = " ".join(
                "{}{:0{w}d}-{}".format(prefix, rng.randrange(pool), rng.randint(0, 1), w=width)
                for _ in range(k)
            )
            f.write("\t".join([str(i), user_id, str(1500000000 + i), "", impressions]) + "\n")


# ---- measured workloads (built once, at import time) ----
_F_TYPICAL = WORKDIR / "imp_typical.tsv"
_write(_F_TYPICAL, 1000, 0, 10, 50000)

_F_DENSE = WORKDIR / "imp_dense.tsv"
_write(_F_DENSE, 300, 1, 100, 20000)

_F_LONGIDS = WORKDIR / "imp_longids.tsv"
_write(_F_LONGIDS, 500, 2, 40, 10**6, width=10)

_F_SPARSE = WORKDIR / "imp_sparse.tsv"
_write(_F_SPARSE, 4000, 3, 1, 80000)

_F_LABELS = WORKDIR / "imp_labels.tsv"
_write(_F_LABELS, 1000, 4, 30, 30000)

_F_MEDIUM = WORKDIR / "imp_medium.tsv"
_write(_F_MEDIUM, 2000, 5, 5, 100000)

_F_MIXED = WORKDIR / "imp_mixed.tsv"
_write(_F_MIXED, 1500, 6, lambda r: r.randint(1, 59), 40000)

_F_DUPS = WORKDIR / "imp_dups.tsv"
_write(_F_DUPS, 800, 7, 50, 10)

# ---- small edge inputs (never measured) ----
_C_EMPTY = WORKDIR / "imp_empty.tsv"
_C_EMPTY.write_text("", encoding="utf-8")

_C_ONE = WORKDIR / "imp_one.tsv"
_write(_C_ONE, 1, 99, 1, 100)

_C_MISSING = WORKDIR / "imp_does_not_exist.tsv"


def checks():
    return [
        ("empty-file", lambda: (str(_C_EMPTY),)),
        ("single-line", lambda: (str(_C_ONE),)),
        ("missing-file", lambda: (str(_C_MISSING),)),
    ]


def cases():
    return [
        ("typical", lambda: (str(_F_TYPICAL),)),
        ("dense", lambda: (str(_F_DENSE),)),
        ("long-news-ids", lambda: (str(_F_LONGIDS),)),
        ("one-per-line", lambda: (str(_F_SPARSE),)),
        ("many-labels", lambda: (str(_F_LABELS),)),
        ("medium-sparse", lambda: (str(_F_MEDIUM),)),
        ("mixed-lengths", lambda: (str(_F_MIXED),)),
        ("duplicate-news", lambda: (str(_F_DUPS),)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['mixed-lengths', 'duplicate-news', 'many-labels', 'one-per-line']
_KEEP_CHECKS = ['empty-file', 'single-line', 'missing-file']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
