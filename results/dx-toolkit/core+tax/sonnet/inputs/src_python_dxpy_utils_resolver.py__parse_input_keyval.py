# Inputs for src/python/dxpy/utils/resolver.py::parse_input_keyval, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import json
import random

from dxpy.utils.resolver import parse_input_keyval


def _json_config(n_items, seed):
    rng = random.Random(seed)
    obj = {
        "name": "workflow-input",
        "items": [
            {
                "id": "item%d" % i,
                "value": rng.choice(["alpha", "beta", "gamma"])
                         + "-" * rng.randint(1, 5)
                         + str(rng.randint(0, 10 ** 6)),
                "count": rng.randint(0, 10 ** 6),
                "nested": {
                    "a": rng.random(),
                    "b": [rng.randint(0, 9) for _ in range(rng.randint(0, 4))],
                },
            }
            for i in range(n_items)
        ],
    }
    return json.dumps(obj)


# Realistic CLI "-i<input name>=<input value>" style strings plus stress variants.
_SIMPLE = "reads=reads.fastq.gz"
_JSON = "config=" + _json_config(150, 0)
_DENSE = "opts=" + "key=val;" * 3000
_ESCAPED = "input=" + "\\=" * 5000
_BACKSLASH_RUNS = "path=" + ("\\" * 20 + "=") * 3000 + "x"
_NAME_ESCAPED = ("n\\=x" * 3000) + "=value"
_QUERY = "url=" + "&".join("k%d=v%d" % (i, i) for i in range(3000))
_LONG = "name=" + "x" * 200000


def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-equals", lambda: ("plainvalue",)),
        ("empty-value", lambda: ("name=",)),
    ]


def cases():
    return [
        ("simple", lambda: (_SIMPLE,)),
        ("json-config", lambda: (_JSON,)),
        ("dense-equals", lambda: (_DENSE,)),
        ("escaped-equals", lambda: (_ESCAPED,)),
        ("backslash-runs", lambda: (_BACKSLASH_RUNS,)),
        ("name-escaped", lambda: (_NAME_ESCAPED,)),
        ("query-string", lambda: (_QUERY,)),
        ("long-value", lambda: (_LONG,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['backslash-runs', 'query-string', 'dense-equals', 'escaped-equals']
_KEEP_CHECKS = ['empty', 'no-equals', 'empty-value']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
