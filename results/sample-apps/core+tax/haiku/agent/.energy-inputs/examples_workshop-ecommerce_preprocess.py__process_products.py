# Inputs for examples/workshop-ecommerce/preprocess.py::process_products, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import csv
import os
import random

from preprocess import process_products

# process_products reads its inputs from the relative path "dataset/...".
# Build that dataset under WORKDIR and chdir into WORKDIR from every thunk
# (setup, never timed) so the relative paths resolve.
_N_AISLES = 134
_N_DEPTS = 21
_N_PRODUCTS = 5000

_ADJECTIVES = ["Organic", "Fresh", "Natural", "Pure", "Premium", "Classic",
               "Sweet", "Salted", "Roasted", "Frozen", "Baby", "Extra",
               "Light", "Whole", "Ground", "Unsweetened"]
_NOUNS = ["Avocado", "Bananas", "Milk", "Bread", "Yogurt", "Cheese", "Tomato",
          "Chicken", "Coffee", "Juice", "Cereal", "Pasta", "Salsa", "Water",
          "Chocolate", "Almonds", "Strawberries", "Spinach", "Salmon", "Eggs",
          "Butter", "Rice", "Beans", "Soup", "Chips", "Ice Cream", "Tea",
          "Honey", "Olive Oil", "Blueberries", "Kale", "Lemon", "Onion"]
_FORMS = ["Bag of", "Pack of", "Box of", "Bunch of", "Can of", "Bottle of"]


def _build_dataset():
    dataset = WORKDIR / "dataset"
    dataset.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0)

    with open(dataset / "aisles.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["aisle_id", "aisle"])
        for aid in range(1, _N_AISLES + 1):
            w.writerow([aid, "{} {}".format(rng.choice(_ADJECTIVES).lower(),
                                            rng.choice(_NOUNS).lower())])

    with open(dataset / "departments.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["department_id", "department"])
        for did in range(1, _N_DEPTS + 1):
            w.writerow([did, "{} {}".format(rng.choice(_ADJECTIVES).lower(),
                                            rng.choice(_NOUNS).lower())])

    # A pool of names that get repeated, like the real Instacart dataset where
    # many rows share the same product name.
    pool = []
    for _ in range(1500):
        parts = []
        if rng.random() < 0.4:
            parts.append(rng.choice(_ADJECTIVES))
        if rng.random() < 0.25:
            parts.append(rng.choice(_FORMS))
        parts.append(rng.choice(_NOUNS))
        pool.append(" ".join(parts))
    # Names with characters that must be CSV-quoted / JSON-escaped.
    pool.extend(["Café au Lait, 2%", 'Ben & Jerry\'s "Half Baked"',
                 "Crème Brûlée", "Gelato \\ Sorbet", "辣味 拉面",
                 "Olive Oil - Extra Virgin"])

    with open(dataset / "products.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "product_name", "aisle_id", "department_id"])
        for pid in range(1, _N_PRODUCTS + 1):
            if rng.random() < 0.65:
                name = rng.choice(pool)
            else:
                name = "{} {} #{}".format(rng.choice(_ADJECTIVES),
                                          rng.choice(_NOUNS), pid)
            aid = rng.randint(1, _N_AISLES)
            did = (aid - 1) % _N_DEPTS + 1
            w.writerow([pid, name, aid, did])


_build_dataset()


def _out_dir(name):
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


_CASE_DIRS = [_out_dir("products_out_{}".format(i)) for i in range(8)]
_CHECK_DIRS = [_out_dir("products_check_{}".format(i)) for i in range(2)]


def _prep(output_dir, full, limit):
    # Setup, never timed: make the relative "dataset/..." paths resolve.
    os.chdir(WORKDIR)
    return (output_dir, full, limit)


def _prep_missing():
    os.chdir(WORKDIR)
    return (WORKDIR / "no_such_products_output_dir", False, 10)


def checks():
    return [
        # output_dir that does not exist: open() raises
        ("missing-output-dir", lambda: _prep_missing()),
        ("limit-zero", lambda: _prep(_CHECK_DIRS[0], False, 0)),
        ("limit-negative", lambda: _prep(_CHECK_DIRS[1], False, -1)),
    ]


def cases():
    return [
        ("limit-1", lambda: _prep(_CASE_DIRS[0], False, 1)),
        ("limit-10", lambda: _prep(_CASE_DIRS[1], False, 10)),
        ("limit-100", lambda: _prep(_CASE_DIRS[2], False, 100)),
        ("limit-500", lambda: _prep(_CASE_DIRS[3], False, 500)),
        ("limit-1500", lambda: _prep(_CASE_DIRS[4], False, 1500)),
        ("limit-3000", lambda: _prep(_CASE_DIRS[5], False, 3000)),
        ("limit-5000", lambda: _prep(_CASE_DIRS[6], False, 5000)),
        ("full-all", lambda: _prep(_CASE_DIRS[7], True, 10)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['full-all', 'limit-5000', 'limit-3000', 'limit-1500']
_KEEP_CHECKS = ['missing-output-dir', 'limit-zero', 'limit-negative']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
