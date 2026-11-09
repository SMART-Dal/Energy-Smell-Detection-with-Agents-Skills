```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


# ---------------------------------------------------------------------------
# Building the object under test.
#
# SimMapGenerator.__init__ downloads/loads the ColPali model (network), which
# the method under test never touches: it only reads `self.n_patch` and
# `self.processor.image_seq_length`.  So we create the instance without running
# __init__ and set only those two data fields.
# ---------------------------------------------------------------------------
def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    processor = types.SimpleNamespace()
    if image_seq_length is not None:
        processor.image_seq_length = image_seq_length
    inst.processor = processor
    return inst


def _query_embs(n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_tokens, 128, generator=g)


def _cell(rng, patch, qt, as_str):
    return {
        "address": {
            "patch": str(patch) if as_str else patch,
            "querytoken": str(qt) if as_str else qt,
        },
        "value": rng.uniform(-1.0, 1.0),
    }


def _build(n_maps, n_tokens, patch_hi, n_patch=32, image_seq_length=1024,
           seed=0, as_str=True, full=True, cells_per_map=None, patch_pool=None):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, image_seq_length)
    q = _query_embs(n_tokens, seed)
    maps = []
    for _ in range(n_maps):
        if full:
            cells = [_cell(rng, p, qt, as_str)
                     for qt in range(n_tokens) for p in range(patch_hi)]
            rng.shuffle(cells)
        else:
            cells = []
            for _ in range(cells_per_map):
                p = (rng.choice(patch_pool) if patch_pool is not None
                     else rng.randrange(patch_hi))
                cells.append(_cell(rng, p, rng.randrange(n_tokens), as_str))
        maps.append({"quantized": {"cells": cells}})
    return inst, q, maps


# All inputs are built once, at import time; the thunks only hand them back.
_BUILT = [
    # dense, typical single-query / few-image workload
    ("typical", _build(3, 8, 1024, seed=0)),
    # many images, fewer query tokens
    ("many-images", _build(6, 5, 1024, seed=1)),
    # processor without image_seq_length -> 1024 fallback branch
    ("fallback-seq-len", _build(4, 8, 1024, image_seq_length=None, seed=2)),
    # image_seq_length=256 -> three quarters of the cells hit the `continue`
    ("skip-heavy", _build(4, 8, 1024, image_seq_length=256, seed=3)),
    # lots of duplicate (patch, querytoken) addresses overwriting each other
    ("duplicates", _build(4, 8, 1024, seed=4, full=False,
                          cells_per_map=3000, patch_pool=list(range(64)))),
    # very many maps, very sparse cells
    ("sparse-many-maps", _build(16, 6, 1024, seed=5, full=False,
                                cells_per_map=40)),
    # different patch grid: n_patch=16, 256 patches
    ("n-patch-16", _build(12, 8, 256, n_patch=16, image_seq_length=256, seed=6)),
    # addresses given as ints instead of strings
    ("int-addresses", _build(3, 8, 1024, seed=7, as_str=False)),
]


def cases():
    return [(label, (lambda args=args: args)) for label, args in _BUILT]


def checks():
    inst = _make_instance(32, 1024)
    q = torch.zeros(1, 128)
    return [
        ("no-maps", lambda: (inst, q, [])),
        ("single-cell", lambda: (inst, q, [{"quantized": {"cells": [
            {"address": {"patch": "0", "querytoken": "0"}, "value": 0.5}]}}])),
        ("odd-patch-type", lambda: (inst, q, [{"quantized": {"cells": [
            {"address": {"patch": "1.5", "querytoken": "0"}, "value": 0.5}]}}])),
    ]
```