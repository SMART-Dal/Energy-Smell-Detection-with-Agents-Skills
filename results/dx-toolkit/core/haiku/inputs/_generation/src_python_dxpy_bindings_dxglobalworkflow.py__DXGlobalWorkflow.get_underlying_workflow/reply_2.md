```python
import random

from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow
from dxpy.bindings.dxworkflow import DXWorkflow

# ---------------------------------------------------------------------------
# Helpers: build real handler objects without going through the constructor
# (the repository's constructor chain blows the recursion limit in this
# environment; setting the object's fields directly builds a genuine,
# fully-populated handler).
# ---------------------------------------------------------------------------
_GWF_ID = "globalworkflow-000000000000000000000001"


def _wfid(n):
    return "workflow-" + ("%024d" % (int(n) % (10 ** 24)))


def _make_gwf(workflows_by_region):
    gwf = DXGlobalWorkflow.__new__(DXGlobalWorkflow)
    gwf._dxid = _GWF_ID
    gwf._proj = None
    gwf._workflows_by_region = workflows_by_region
    gwf._workflow_desc_by_region = {}
    return gwf


def _make_wf(wfid):
    w = DXWorkflow.__new__(DXWorkflow)
    w._dxid = wfid
    w._proj = None
    return w


def _gen_describe(n_regions, seed, extras=0):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        entry = {"workflow": _wfid(seed * 1000000 + i + 1)}
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
_RICH = _gen_describe(800, 4, extras=12)
_BIG_20K = _gen_describe(20000, 3)

_CACHE_SMALL = {
    "aws:us-east-1": _make_wf(_wfid(1001)),
    "aws:eu-west-1": _make_wf(_wfid(1002)),
    "aws:ap-southeast-2": _make_wf(_wfid(1003)),
}
_CACHE_10K = {
    "aws:cached-%06d" % i: _make_wf(_wfid(200000 + i))
    for i in range(10000)
}


# ---------------------------------------------------------------------------
# thunks
# ---------------------------------------------------------------------------
def _compute_thunk(region, describe_output):
    return lambda: (_make_gwf({}), region, describe_output)


def _cached_thunk(cache, region, describe_output=None):
    return lambda: (_make_gwf(dict(cache)), region, describe_output)


# ---------------------------------------------------------------------------
# edge cases (not measured)
# ---------------------------------------------------------------------------
def checks():
    return [
        ("region-none", lambda: (_make_gwf({}), None, _SINGLE)),
        ("class-mismatch", lambda: (
            _make_gwf({}),
            "aws:us-east-1",
            {"class": "workflow",
             "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(1)}}},
        )),
        ("region-not-enabled", lambda: (_make_gwf({}), "aws:sa-east-1", _THREE)),
    ]


# ---------------------------------------------------------------------------
# measured cases
# ---------------------------------------------------------------------------
def cases():
    return [
        ("single-region",          _compute_thunk("aws:us-east-1", _SINGLE)),
        ("three-regions",          _compute_thunk("aws:region-000001", _THREE)),
        ("twenty-thousand-regions", _compute_thunk("aws:region-010000", _BIG_20K)),
        ("cache-hit-small-first",  _cached_thunk(_CACHE_SMALL, "aws:us-east-1")),
        ("cache-hit-small-last",   _cached_thunk(_CACHE_SMALL, "aws:ap-southeast-2")),
        ("cache-hit-large-first",  _cached_thunk(_CACHE_10K, "aws:cached-000000")),
        ("cache-hit-large-middle", _cached_thunk(_CACHE_10K, "aws:cached-005000", _RICH)),
        ("cache-hit-large-last",   _cached_thunk(_CACHE_10K, "aws:cached-009999")),
    ]
```