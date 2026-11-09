# Inputs for examples/workshop-ecommerce/preprocess.py::process_users, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import csv
import os
import random
from pathlib import Path

from preprocess import process_users


# ---------------------------------------------------------------------------
# Output directory the function writes users.jsonl into (kept under WORKDIR).
# ---------------------------------------------------------------------------
_OUT = WORKDIR / "out"
_OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Dataset builders.  process_users reads the fixed relative paths
# "dataset/orders.csv" and "dataset/order_products__train.csv", so every case
# gets its own directory containing a `dataset/` folder and the thunk chdirs
# into it before the timed call.
# ---------------------------------------------------------------------------
def _write_dataset(base, n_orders, n_users, n_products, items_lo, items_hi,
                   seed, unmatched_frac=0.0):
    rng = random.Random(seed)
    ddir = base / "dataset"
    ddir.mkdir(parents=True, exist_ok=True)

    with open(ddir / "orders.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "order_id", "user_id", "eval_set", "order_number",
            "order_dow", "order_hour_of_day", "days_since_prior_order",
        ])
        for oid in range(n_orders):
            w.writerow([
                oid,
                rng.randrange(n_users),
                "train",
                rng.randint(1, 25),
                rng.randrange(7),
                rng.randrange(24),
                round(rng.uniform(0.0, 30.0), 2),
            ])

    n_unmatched = int(n_orders * unmatched_frac)
    with open(ddir / "order_products__train.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "product_id", "add_to_cart_order", "reordered"])
        for oid in range(n_orders):
            for _ in range(rng.randint(items_lo, items_hi)):
                w.writerow([
                    oid,
                    rng.randrange(n_products),
                    rng.randint(1, 40),
                    rng.randint(0, 1),
                ])
        # Rows whose order_id is not present in orders.csv -> NaN user_id after
        # the left merge (dropped by groupby), a real path in this dataset.
        for _ in range(n_unmatched):
            w.writerow([
                n_orders + rng.randrange(5000),
                rng.randrange(n_products),
                rng.randint(1, 40),
                rng.randint(0, 1),
            ])

    return base


# Built once at import time; thunks only chdir and hand back the arguments.
_D_SMALL = _write_dataset(WORKDIR / "ds_small", 2_000, 500, 1_000, 1, 5, 0)
_D_MED = _write_dataset(WORKDIR / "ds_med", 15_000, 4_000, 4_000, 1, 6, 1)
_D_FULL = _write_dataset(WORKDIR / "ds_full", 1_500, 150, 500, 1, 5, 2)
_D_LIM1 = _write_dataset(WORKDIR / "ds_lim1", 5_000, 1_000, 2_000, 1, 5, 3)
_D_LIM200 = _write_dataset(WORKDIR / "ds_lim200", 10_000, 3_000, 3_000, 1, 6, 4)
_D_FEW = _write_dataset(WORKDIR / "ds_few", 3_000, 30, 300, 3, 10, 5)
_D_DUP = _write_dataset(WORKDIR / "ds_dup", 5_000, 1_000, 100, 2, 8, 6)
_D_UNM = _write_dataset(WORKDIR / "ds_unm", 8_000, 2_000, 2_000, 1, 5, 7,
                        unmatched_frac=0.3)
_D_EMPTY = _write_dataset(WORKDIR / "ds_empty", 0, 1, 1, 1, 1, 8)


def _mk(dataset_dir, out_dir, full, limit):
    """Return a thunk that makes `dataset_dir` the cwd and yields the args."""
    def thunk():
        os.chdir(str(dataset_dir))
        return (out_dir, full, limit)
    return thunk


def checks():
    return [
        # header-only CSVs: no orders, no products -> empty groupby
        ("empty-dataset", _mk(_D_EMPTY, _OUT, False, 10)),
        # limit == 0 -> loop breaks after the first user
        ("limit-zero", _mk(_D_SMALL, _OUT, False, 0)),
        # output directory does not exist -> open() raises
        ("missing-output-dir", _mk(_D_SMALL, WORKDIR / "no_such_dir", False, 5)),
    ]


def cases():
    return [
        ("small-limit10", _mk(_D_SMALL, _OUT, False, 10)),
        ("medium-limit10", _mk(_D_MED, _OUT, False, 10)),
        ("full-150-users", _mk(_D_FULL, _OUT, True, 10)),
        ("limit-1", _mk(_D_LIM1, _OUT, False, 1)),
        ("limit-200", _mk(_D_LIM200, _OUT, False, 200)),
        ("few-users-heavy", _mk(_D_FEW, _OUT, False, 10)),
        ("many-duplicates", _mk(_D_DUP, _OUT, False, 50)),
        ("unmatched-orders", _mk(_D_UNM, _OUT, False, 10)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['few-users-heavy', 'full-150-users', 'limit-200', 'many-duplicates']
_KEEP_CHECKS = ['empty-dataset', 'limit-zero', 'missing-output-dir']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
