# Inputs for examples/mcp-server-app/script/generate_data.py::save_vespa_feed, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import os
import random

from generate_data import save_vespa_feed

# The repository's own caller runs the script from examples/mcp-server-app/script,
# so the hard-coded "../dataset" resolves to a directory next to the script.
# We reproduce that layout under WORKDIR: run from WORKDIR/"run" so that
# "../dataset" lands inside WORKDIR.
_RUN_DIR = WORKDIR / "run"
_OUT_DIR = WORKDIR / "dataset"


def _prep():
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(_RUN_DIR)


_prep()

_ALPHA = "abcdefghijklmnopqrstuvwxyz "
_UNI = "åäöéèñ日本語テストαβγ"


def _items(n, doc_type, seed, n_fields=8, text_len=16,
           nested=False, unicode_heavy=False, numeric=False):
    rng = random.Random(seed)
    items = []
    for i in range(n):
        item = {f"{doc_type}_id": f"{doc_type}-{i:07d}"}
        for j in range(n_fields):
            key = f"field_{j}"
            r = rng.random()
            if numeric:
                item[key] = rng.randint(0, 10 ** 9) if r < 0.5 else round(rng.uniform(0, 1e6), 4)
            elif nested and r < 0.6:
                item[key] = [f"tag{rng.randrange(5000)}" for _ in range(rng.randint(0, 8))]
            elif unicode_heavy:
                item[key] = "".join(rng.choices(_UNI, k=text_len))
            else:
                item[key] = "".join(rng.choices(_ALPHA, k=text_len))
        items.append(item)
    return items


# Built once, at import time; the function never mutates its arguments.
_C1 = _items(15000, "job", 0, n_fields=6, text_len=12)
_C2 = _items(4000, "job", 1, n_fields=30, text_len=20)
_C3 = _items(3000, "candidate", 2, n_fields=12, nested=True)
_C4 = _items(1500, "candidate", 3, n_fields=10, text_len=200)
_C5 = _items(6000, "job", 4, n_fields=10, unicode_heavy=True, text_len=30)
_C6 = _items(8000, "candidate", 5, n_fields=8, numeric=True)
_C7 = _items(25000, "job", 6, n_fields=4, text_len=10)
_C8 = _items(2000, "candidate", 7, n_fields=20, text_len=40, nested=True)


def _case(items, doc_type, filename):
    def thunk():
        _prep()
        return (items, doc_type, filename)
    return thunk


def checks():
    return [
        ("empty", _case([], "job", "checks_empty.jsonl")),
        ("single", _case([{"job_id": "j-1"}], "job", "checks_single.jsonl")),
        ("missing-id", _case([{"title": "no id here"}], "job", "checks_missing.jsonl")),
    ]


def cases():
    return [
        ("jobs-many-small", _case(_C1, "job", "c1.jsonl")),
        ("jobs-wide-fields", _case(_C2, "job", "c2.jsonl")),
        ("candidates-nested", _case(_C3, "candidate", "c3.jsonl")),
        ("candidates-longtext", _case(_C4, "candidate", "c4.jsonl")),
        ("jobs-unicode", _case(_C5, "job", "c5.jsonl")),
        ("candidates-numeric", _case(_C6, "candidate", "c6.jsonl")),
        ("jobs-huge", _case(_C7, "job", "c7.jsonl")),
        ("candidates-mixed", _case(_C8, "candidate", "c8.jsonl")),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['jobs-huge', 'jobs-many-small', 'jobs-unicode', 'candidates-numeric']
_KEEP_CHECKS = ['empty', 'single', 'missing-id']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
