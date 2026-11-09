```python
import itertools
import os
import random

import pandas as pd

# The function under test reads "dataset/orders.csv" relative to the current
# working directory, so we place the whole dataset under WORKDIR and chdir there.
os.chdir(WORKDIR)

_DATASET = WORKDIR / "dataset"
_DATASET.mkdir(parents=True, exist_ok=True)
_OUT = WORKDIR / "out"
_OUT.mkdir(parents=True, exist_ok=True)

_oid = itertools.count(1)


def _gen_set(name, n_orders, avg_items, seed, match=True):
    """Build realistic orders + order_products rows for one eval_set."""
    rng = random.Random(seed)
    orders = []
    products = []
    for _ in range(n_orders):
        oid = next(_oid)
        orders.append(
            (
                oid,
                rng.randint(1, 200000),
                name,
                rng.randint(0, 6),
                rng.randint(0, 23),
                None if rng.random() < 0.07 else rng.randint(0, 30),
            )
        )
        k = int(rng.gauss(avg_items, max(1.0, avg_items * 0.5)))
        k = max(1, min(k, 40))
        a2c = list(range(1, k + 1))
        rng.shuffle(a2c)
        target = oid if match else oid + 10_000_000
        for a in a2c:
            products.append((target, rng.randint(1, 50000), a, rng.randint(0, 1)))
    return orders, products


_SETS = {
    "prior": _gen_set("prior", 15000, 4.0, 1),
    "train": _gen_set("train", 5000, 4.0, 2),
    "test": _gen_set("test", 500, 4.0, 3),
    "val": _gen_set("val", 300, 4.0, 4),
    # orders whose product rows never match -> left-merge produces NaN arrays
    "orphan": _gen_set("orphan", 3000, 3.0, 5, match=False),
    # orders present but with no order_products file at all
    "nofile": _gen_set("nofile", 2000, 3.0, 6),
}

_all_orders = [o for orders, _ in _SETS.values() for o in orders]
random.Random(99).shuffle(_all_orders)

with open(_DATASET / "orders.csv", "w") as f:
    f.write(
        "order_id,user_id,eval_set,order_dow,order_hour_of_day,"
        "days_since_prior_order\n"
    )
    for oid, uid, es, dow, hod, dspo in _all_orders:
        f.write(f"{oid},{uid},{es},{dow},{hod},{'' if dspo is None else dspo}\n")

for _name, (_orders, _products) in _SETS.items():
    if _name == "nofile":
        continue
    with open(_DATASET / f"order_products__{_name}.csv", "w") as f:
        f.write("order_id,product_id,add_to_cart_order,reordered\n")
        for oid, pid, a2c, reo in _products:
            f.write(f"{oid},{pid},{a2c},{reo}\n")


def checks():
    return [
        ("no-eval-sets", lambda: (_OUT, [], False, 10)),
        ("limit-zero", lambda: (_OUT, ["val"], False, 0)),
        ("absent-eval-set", lambda: (_OUT, ["does-not-exist"], True, 5)),
    ]


def cases():
    return [
        ("prior-limit-10", lambda: (_OUT, ["prior"], False, 10)),
        ("prior-and-train", lambda: (_OUT, ["prior", "train"], False, 10)),
        ("train-limit-300", lambda: (_OUT, ["train"], False, 300)),
        ("mixed-three-sets", lambda: (_OUT, ["val", "test", "train"], False, 50)),
        ("test-full", lambda: (_OUT, ["test"], True, 10)),
        ("val-full", lambda: (_OUT, ["val"], True, 10)),
        ("orphan-orders", lambda: (_OUT, ["orphan"], False, 10)),
        ("missing-products-file", lambda: (_OUT, ["nofile"], False, 10)),
    ]
```