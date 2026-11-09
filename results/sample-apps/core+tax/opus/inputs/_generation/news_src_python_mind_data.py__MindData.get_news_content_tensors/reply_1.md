```python
import random
from mind_data import MindData


def _build_instance(num_docs, coverage, seed, value_max, shuffled=True):
    """Create a MindData instance with the two fields the method reads."""
    rng = random.Random(seed)
    inst = MindData.__new__(MindData)
    inst.news_map = {f"N{i}": i for i in range(num_docs)}

    n_content = int(round(num_docs * coverage))
    if shuffled:
        indices = list(range(num_docs))
        rng.shuffle(indices)
        indices = indices[:n_content]
    else:
        indices = list(range(n_content))

    content = {}
    for idx in indices:
        content[idx] = {
            "category_index": rng.randrange(value_max),
            "subcategory_index": rng.randrange(value_max),
            "entity_index": rng.randrange(value_max),
        }
    inst.news_content = content
    return inst


# Build all measured inputs once, at import time.  The method does not mutate
# the instance, so the same object can be reused for every timed call.
_CASES = [
    ("small-full",           _build_instance(5_000,  1.0,  0, 100,       shuffled=False)),
    ("medium-full",          _build_instance(15_000, 1.0,  1, 1_000,     shuffled=True)),
    ("large-full",           _build_instance(24_000, 1.0,  2, 10**6,     shuffled=True)),
    ("medium-half",          _build_instance(20_000, 0.5,  3, 1_000,     shuffled=True)),
    ("large-sparse",         _build_instance(24_000, 0.1,  4, 1_000,     shuffled=True)),
    ("dense-random-values",  _build_instance(22_000, 0.9,  5, 10**9,     shuffled=True)),
    ("small-sparse-seq",     _build_instance(10_000, 0.2,  6, 100,       shuffled=False)),
    ("max-full-seq",         _build_instance(24_000, 1.0,  7, 10**12,    shuffled=False)),
]


def checks():
    inst_empty = MindData.__new__(MindData)
    inst_empty.news_map = {}
    inst_empty.news_content = {}

    inst_one = MindData.__new__(MindData)
    inst_one.news_map = {"N0": 0}
    inst_one.news_content = {
        0: {"category_index": 1, "subcategory_index": 2, "entity_index": 3}
    }

    inst_bad = MindData.__new__(MindData)
    inst_bad.news_map = {"N0": 0}
    inst_bad.news_content = {
        0: {"category_index": 1, "subcategory_index": 2}  # missing entity_index
    }

    return [
        ("empty",       lambda: (inst_empty,)),
        ("single",      lambda: (inst_one,)),
        ("missing-key", lambda: (inst_bad,)),
    ]


def cases():
    return [(label, (lambda inst=inst: (inst,))) for label, inst in _CASES]
```