```python
import random
import create_category_ctrs
from create_category_ctrs import write_news_category_ctr_update

# The function writes to this module-level path.  Point it under WORKDIR.
create_category_ctrs.news_category_ctr_update_file = str(WORKDIR / "news_category_ctr_update.json")


def _make_map(n, id_extra_len, cat_len, seed, alphabet="0123456789abcdef", mixed=False):
    rng = random.Random(seed)
    d = {}
    for i in range(n):
        if mixed:
            il = rng.randint(0, id_extra_len)
            cl = rng.randint(1, cat_len)
        else:
            il = id_extra_len
            cl = cat_len
        news_id = f"N{i:08d}" + "".join(rng.choices(alphabet, k=il))
        category = "".join(rng.choices(alphabet, k=cl))
        d[news_id] = category
    return d


_CASES = [
    ("tiny-short", _make_map(1_000, 0, 6, 0)),
    ("small-medium", _make_map(2_000, 10, 10, 1)),
    ("medium-long-ids", _make_map(3_000, 30, 5, 2)),
    ("medium-long-cats", _make_map(5_000, 5, 50, 3)),
    ("large-very-long", _make_map(8_000, 100, 100, 4)),
    ("large-diverse-chars", _make_map(
        12_000, 20, 20, 5,
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    )),
    ("large-mixed", _make_map(15_000, 50, 50, 6, mixed=True)),
    ("large-simple", _make_map(20_000, 0, 8, 7)),
]


def checks():
    return [
        ("empty", lambda: ({},)),
        ("single", lambda: ({"N1": "sports"},)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        (label, lambda d=d: (d,)) for label, d in _CASES
    ]
```