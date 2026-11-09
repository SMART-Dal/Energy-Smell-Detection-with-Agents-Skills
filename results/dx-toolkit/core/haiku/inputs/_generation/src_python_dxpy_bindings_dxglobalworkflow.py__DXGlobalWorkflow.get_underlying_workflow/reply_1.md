```python
import random

import dxpy
from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow

_GWF_ID = "globalworkflow-000000000000000000000001"


def _wfid(n):
    """Build a syntactically valid DXWorkflow id."""
    return "workflow-" + ("%024d" % (int(n) % (10 ** 24)))


def _gen_describe(n_regions, seed, extras=0):
    """Build a realistic global-workflow describe output with n_regions entries."""
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        entry = {"workflow": _wfid(seed * 100000 + i + 1)}
        for j in range(extras):
            entry["meta_%d" % j] = rng.getrandbits(40)
        regions["aws:region-%06d" % i] = entry
    return {
        "class": "globalworkflow",
        "id": _GWF_ID,
        "name": "global-workflow-%d" % seed,
        "version": "1.0.0",
        "regionalOptions": regions,
    }


# ---------------------------------------------------------------------------
# module-level input data (built once, never timed)
# ---------------------------------------------------------------------------
_SINGLE = {
    "class": "globalworkflow",
    "id": _GWF_ID,
    "name": "simple-global-workflow",
    "version": "1.0.0",
    "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(11)}},
}

_THREE = _gen_describe(3, 1)
_BIG_5K = _gen_describe(5000, 2)
_BIG_20K = _gen_describe(20000, 3)
_RICH = _gen_describe(800, 4, extras=12)

_CACHE_SMALL = {
    "aws:us-east-1": dxpy.DXWorkflow(_wfid(1001)),
    "aws:eu-west-1": dxpy.DXWorkflow(_wfid(1002)),
    "aws:ap-southeast-2": dxpy.DXWorkflow(_wfid(1003)),
}
_CACHE_10K = {
    "aws:cached-%06d" % i: dxpy.DXWorkflow(_wfid(100000 + i))
    for i in range(10000)
}


# ---------------------------------------------------------------------------
# thunks
# ---------------------------------------------------------------------------
def _plain_thunk(region, describe_output):
    return lambda: (DXGlobalWorkflow(), region, describe_output)


def _cached_thunk(cache, region, describe_output=None):
    def _thunk():
        gwf = DXGlobalWorkflow()
        gwf._workflows_by_region = dict(cache)
        return (gwf, region, describe_output)
    return _thunk


# ---------------------------------------------------------------------------
# edge cases (not measured)
# ---------------------------------------------------------------------------
def checks():
    return [
        ("region-none", lambda: (DXGlobalWorkflow(), None, _SINGLE)),
        ("class-mismatch", lambda: (
            DXGlobalWorkflow(),
            "aws:us-east-1",
            {"class": "workflow",
             "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(1)}}},
        )),
        ("region-not-enabled", lambda: (DXGlobalWorkflow(), "aws:sa-east-1", _THREE)),
    ]


# ---------------------------------------------------------------------------
# measured cases
# ---------------------------------------------------------------------------
def cases():
    return [
        ("single-region", _plain_thunk("aws:us-east-1", _SINGLE)),
        ("three-regions", _plain_thunk("aws:region-000001", _THREE)),
        ("five-thousand-regions", _plain_thunk("aws:region-004999", _BIG_5K)),
        ("twenty-thousand-regions", _plain_thunk("aws:region-010000", _BIG_20K)),
        ("rich-region-entries", _plain_thunk("aws:region-000400", _RICH)),
        ("cache-hit-small", _cached_thunk(_CACHE_SMALL, "aws:ap-southeast-2")),
        ("cache-hit-large-cache", _cached_thunk(_CACHE_10K, "aws:cached-005000", _BIG_5K)),
        ("cache-miss-large-cache", _cached_thunk(_CACHE_10K, "aws:region-004999", _BIG_5K)),
    ]
```