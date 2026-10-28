```python
import random

from dxpy.bindings.dxworkflow import DXWorkflow


def _build_stages(n, seed=0, name_frac=0.85):
    """Build a realistic list of workflow stage descriptors."""
    rng = random.Random(seed)
    stages = []
    for i in range(n):
        stg = {"id": "stage-{:012x}".format(rng.getrandbits(48))}
        if rng.random() < name_frac:
            stg["name"] = "Stage {}".format(i)
        stages.append(stg)
    return stages


def _wf(stages):
    wf = DXWorkflow()
    wf.stages = stages
    return wf


# ---- module level setup (never timed) ----
_S1 = _build_stages(1, seed=1)
_W1 = _wf(_S1)

_S20 = _build_stages(20, seed=2)
_W20 = _wf(_S20)

_S5K = _build_stages(5000, seed=3)
_W5K = _wf(_S5K)

_S100K = _build_stages(100000, seed=4)
# force the exact names/ids the cases below rely on
_S100K[0]["name"] = "Stage 0"
_S100K[-1]["name"] = "Stage 99999"
_S100K[99998]["name"] = "stage-ffffffffffff"   # regex-matching name, hit only by the name scan
_W100K = _wf(_S100K)


def checks():
    return [
        ("empty-workflow-index", lambda: (_wf([]), 0)),
        ("missing-stage-name",   lambda: (_W1, "no_such_stage")),
        ("none-stage",           lambda: (_W1, None)),
    ]


def cases():
    return [
        ("tiny-index",             lambda: (_W1, 0)),
        ("small-str-index",        lambda: (_W20, "19")),
        ("medium-id-hit-end",      lambda: (_W5K, _S5K[-1]["id"])),
        ("large-index-int",        lambda: (_W100K, 99999)),
        ("large-id-hit-start",     lambda: (_W100K, _S100K[0]["id"])),
        ("large-id-miss-name-hit", lambda: (_W100K, "stage-ffffffffffff")),
        ("large-name-hit-start",   lambda: (_W100K, _S100K[0]["name"])),
        ("large-name-hit-end",     lambda: (_W100K, _S100K[-1]["name"])),
    ]
```