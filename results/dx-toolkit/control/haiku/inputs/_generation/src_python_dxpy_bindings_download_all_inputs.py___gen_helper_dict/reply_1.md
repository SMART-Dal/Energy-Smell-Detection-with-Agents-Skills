```python
import json
import os
import random
from pathlib import Path

import dxpy
from dxpy.utils import file_load_utils
from dxpy.bindings.download_all_inputs import _gen_helper_dict

_PROJ = "project-000000000000000000000000"

# The function under test reads a job-input JSON file discovered through the
# repository's own file_load_utils.get_input_json_file().  Point that at a file
# we control, but also write to whatever path it reports so the call path used
# during timing really finds our data.
os.environ["DX_INPUT"] = str(WORKDIR / "job_input.json")

_paths = [WORKDIR / "job_input.json", Path(os.getcwd()) / "job_input.json"]
try:
    _ret = file_load_utils.get_input_json_file()
except Exception:
    _ret = None
if isinstance(_ret, bytes):
    try:
        _ret = _ret.decode()
    except Exception:
        _ret = None
if isinstance(_ret, str) and _ret.strip():
    _pp = Path(_ret)
    if not _pp.is_absolute():
        _pp = Path(os.getcwd()) / _pp
    _paths.insert(0, _pp)

_INPUT_PATHS = []
for _p in _paths:
    if _p not in _INPUT_PATHS:
        _INPUT_PATHS.append(_p)


def _write_input(data):
    text = json.dumps(data)
    for p in _INPUT_PATHS:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        except Exception:
            pass


def _link(i, fn):
    return {"$dnanexus_link": {"project": _PROJ,
                               "id": "file-%024d" % i,
                               "name": fn}}


def _builders():
    """Plausible shapes for a job-input JSON; we keep the one the real
    analyzer accepts (found by calling the repository's own code)."""
    return [
        # plain local paths
        lambda sf: {n: fn for n, fn in sf},
        # {"name": ...}
        lambda sf: {n: {"name": fn} for n, fn in sf},
        # already-resolved description
        lambda sf: {n: {"path": fn,
                        "basename": os.path.basename(fn),
                        "prefix": os.path.basename(fn).split(".")[0]}
                   for n, fn in sf},
        # bare file id
        lambda sf: {n: "file-%024d" % i for i, (n, fn) in enumerate(sf)},
        # link as a string
        lambda sf: {n: {"$dnanexus_link": "file-%024d" % i}
                   for i, (n, fn) in enumerate(sf)},
        # link dict with id + name
        lambda sf: {n: {"$dnanexus_link": {"id": "file-%024d" % i, "name": fn}}
                   for i, (n, fn) in enumerate(sf)},
        # link dict with project + id
        lambda sf: {n: {"$dnanexus_link": {"project": _PROJ,
                                           "id": "file-%024d" % i}}
                   for i, (n, fn) in enumerate(sf)},
        # full link dict
        lambda sf: {n: _link(i, fn) for i, (n, fn) in enumerate(sf)},
        # link dict plus a sibling name
        lambda sf: {n: {"$dnanexus_link": {"project": _PROJ,
                                           "id": "file-%024d" % i},
                        "name": fn}
                   for i, (n, fn) in enumerate(sf)},
        # nested under "inputs"
        lambda sf: {"inputs": {n: _link(i, fn) for i, (n, fn) in enumerate(sf)}},
    ]


_SAMPLE = [("in_a", "alpha.txt"), ("in_b", "beta.csv"), ("in_c", "gamma.tar.gz")]


def _validate(builder):
    try:
        data = builder(_SAMPLE)
    except Exception:
        return False
    try:
        _write_input(data)
    except Exception:
        return False
    try:
        out = _gen_helper_dict([n for n, _ in _SAMPLE])
    except Exception:
        return False
    if not isinstance(out, dict):
        return False
    for n, _fn in _SAMPLE:
        for suf in ("_path", "_name", "_prefix"):
            if n + suf not in out:
                return False
    return True


_BUILDER = None
for _b in _builders():
    if _validate(_b):
        _BUILDER = _b
        break
if _BUILDER is None:
    _BUILDER = _builders()[0]

# ---------------------------------------------------------------------------
# Real workload: a job-input JSON with many file inputs.
# ---------------------------------------------------------------------------
_N = 20000
_EXT = [".txt", ".csv", ".tar.gz", ".json", "", ".bam", ".vcf.gz", ".fastq"]


def _fname(i):
    base = "sample%d" % i
    if i % 11 == 0:
        base = "long_" + ("x" * (i % 40)) + "_" + base
    return base + _EXT[i % len(_EXT)]


_PAIRS = [("in_%d" % i, _fname(i)) for i in range(_N)]
_write_input(_BUILDER(_PAIRS))

_POOL = ["in_%d" % i for i in range(_N)]


def _uniq(n, seed):
    return random.Random(seed).sample(_POOL, n)


def _dups(total, distinct, seed):
    rng = random.Random(seed)
    chosen = rng.sample(_POOL, distinct)
    return [chosen[rng.randrange(distinct)] for _ in range(total)]


def _misses(n, seed):
    return ["absent_%d_%d" % (seed, i) for i in range(n)]


def _mix(hits, misses, seed):
    r = list(hits) + list(misses)
    random.Random(seed).shuffle(r)
    return r


_C1 = _uniq(5000, 1)
_C2 = _uniq(15000, 2)
_C3 = _uniq(20000, 3)
_C4 = _dups(20000, 5000, 4)
_C5 = _mix(_uniq(10000, 5), _misses(10000, 5), 51)
_C6 = _mix(_uniq(2000, 6), _misses(18000, 6), 61)
_C7 = _misses(20000, 7)
_C8 = _dups(30000, 10, 8)


def checks():
    return [
        ("empty",          lambda: ([],)),
        ("single-missing", lambda: (["not_present"],)),
        ("none",           lambda: (None,)),
    ]


def cases():
    return [
        ("unique-5k",        lambda: (_C1,)),
        ("unique-15k",       lambda: (_C2,)),
        ("unique-20k",       lambda: (_C3,)),
        ("dup-20k-5k",       lambda: (_C4,)),
        ("half-miss-20k",    lambda: (_C5,)),
        ("mostly-miss-20k",  lambda: (_C6,)),
        ("all-miss-20k",     lambda: (_C7,)),
        ("dup-30k-10",       lambda: (_C8,)),
    ]
```