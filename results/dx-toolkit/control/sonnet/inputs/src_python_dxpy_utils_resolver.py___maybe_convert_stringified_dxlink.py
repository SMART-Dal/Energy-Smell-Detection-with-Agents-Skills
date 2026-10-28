# Inputs for src/python/dxpy/utils/resolver.py::_maybe_convert_stringified_dxlink, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import json
import random


def _rand_dict(n, seed):
    rng = random.Random(seed)
    return {"k%d" % i: rng.randrange(10**9) for i in range(n)}


def _nested(depth, width, seed):
    rng = random.Random(seed)
    node = [rng.randrange(1000) for _ in range(width)]
    for _ in range(depth):
        node = [node, rng.randrange(1000)]
    return json.dumps(node)


# ---- module-level data (built once, never timed) ----

_BIG_DICT = json.dumps(_rand_dict(80_000, 0))

_rng = random.Random(1)
_BIG_ARRAY = json.dumps([_rng.randrange(10**9) for _ in range(200_000)])

_NESTED = _nested(40, 300, 2)

_PAD = _rand_dict(60_000, 3)

_d = dict(_PAD)
_d["$dnanexus_link"] = "file-abcdefghijklmnopqrstuvwx"
_LINK_STRING = json.dumps(_d)

_d = dict(_PAD)
_d["$dnanexus_link"] = {"project": "project-abcdefghijklmnopqrstuvwx",
                        "id": "file-abcdefghijklmnopqrstuvwx"}
_LINK_DICT_PID = json.dumps(_d)

_d = dict(_PAD)
_d["$dnanexus_link"] = {"id": "file-abcdefghijklmnopqrstuvwx"}
_LINK_DICT_PARTIAL = json.dumps(_d)

_d = dict(_PAD)
_d["$dnanexus_link"] = {"project": "project-abcdefghijklmnopqrstuvwx", "id": 12345}
_LINK_DICT_BAD = json.dumps(_d)

# unterminated JSON string: json.loads scans the whole buffer before failing
_INVALID = '"' + "x" * 2_000_000


def checks():
    return [
        ("none",         lambda: (None,)),
        ("empty-string", lambda: ("",)),
        ("int",          lambda: (12345,)),
    ]


def cases():
    return [
        ("plain-path",         lambda: ("project-xxxx:file-yyyy",)),
        ("big-dict-no-link",   lambda: (_BIG_DICT,)),
        ("big-array-no-link",  lambda: (_BIG_ARRAY,)),
        ("nested-array",       lambda: (_NESTED,)),
        ("link-string",        lambda: (_LINK_STRING,)),
        ("link-dict-pid",      lambda: (_LINK_DICT_PID,)),
        ("link-dict-partial",  lambda: (_LINK_DICT_PARTIAL,)),
        ("invalid-json",       lambda: (_INVALID,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['big-dict-no-link', 'big-array-no-link', 'link-dict-pid', 'link-dict-partial']
_KEEP_CHECKS = ['none', 'empty-string', 'int']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
