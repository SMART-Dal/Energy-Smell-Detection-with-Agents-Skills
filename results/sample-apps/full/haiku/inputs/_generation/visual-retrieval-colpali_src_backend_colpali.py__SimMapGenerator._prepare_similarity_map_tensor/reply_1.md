```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


# ---------------------------------------------------------------------------
# Building the object under test without loading the (network/GPU) model.
# Only `n_patch` and `processor.image_seq_length` are read by the function.
# ---------------------------------------------------------------------------
def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_instance_no_seq_len(n_patch):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace()  # no image_seq_length -> fallback path
    return inst


# ---------------------------------------------------------------------------
# Vespa similarity-map builders
# ---------------------------------------------------------------------------
def _cells_random(count, n_patch, num_tokens, seed, patch_hi=None):
    rng = random.Random(seed)
    if patch_hi is None:
        patch_hi = n_patch * n_patch
    cells = []
    for _ in range(count):
        patch = rng.randrange(patch_hi)
        qt = rng.randrange(num_tokens)
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.random(),
        })
    return cells


def _cells_grid(n_patch, num_tokens, seed):
    rng = random.Random(seed)
    cells = []
    for patch in range(n_patch * n_patch):
        for qt in range(num_tokens):
            cells.append({
                "address": {"patch": patch, "querytoken": qt},
                "value": rng.random(),
            })
    return cells


def _cells_duplicates(count, n_patch, num_tokens, seed, n_addresses=64):
    rng = random.Random(seed)
    addrs = [(rng.randrange(n_patch * n_patch), rng.randrange(num_tokens))
             for _ in range(n_addresses)]
    cells = []
    for _ in range(count):
        patch, qt = addrs[rng.randrange(len(addrs))]
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.random(),
        })
    return cells


def _sim_map(cells):
    return {"quantized": {"cells": cells}}


# ---------------------------------------------------------------------------
# Module level data (built once, reused by every thunk call)
# ---------------------------------------------------------------------------
torch.manual_seed(0)

_EMB_16 = torch.randn(16, 128)
_EMB_32 = torch.randn(32, 128)
_EMB_64 = torch.randn(64, 128)

_I32 = _make_instance(32, 1024)
_I32_NOSEQ = _make_instance_no_seq_len(32)
_I16 = _make_instance(16, 256)

_MAP_DENSE = [_sim_map(_cells_grid(32, 16, 0))]                    # full 32x32 patch grid
_MAP_TWO = [
    _sim_map(_cells_random(6000, 32, 32, 1)),
    _sim_map(_cells_random(6000, 32, 32, 2)),
]
_MAP_MANYTOK = [_sim_map(_cells_random(15000, 32, 64, 3))]
_MAP_OOR = [_sim_map(_cells_random(12000, 32, 32, 4, patch_hi=2048))]
_MAP_NOSEQ = [_sim_map(_cells_random(12000, 32, 32, 5))]
_MAP_DUP = [_sim_map(_cells_duplicates(15000, 32, 32, 6))]
_MAP_NP16 = [
    _sim_map(_cells_random(6000, 16, 32, 7)),
    _sim_map(_cells_random(6000, 16, 32, 8)),
]
_MAP_LARGE = [_sim_map(_cells_random(20000, 32, 32, 9))]


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def checks():
    return [
        ("no-images", lambda: (_I32, torch.zeros(4, 128), [])),
        ("empty-cells", lambda: (_I32, torch.zeros(4, 128), [_sim_map([])])),
        ("single-cell", lambda: (
            _I32,
            torch.zeros(4, 128),
            [_sim_map([{"address": {"patch": 0, "querytoken": 0}, "value": 1.0}])],
        )),
    ]


def cases():
    return [
        ("dense-grid", lambda: (_I32, _EMB_16, _MAP_DENSE)),
        ("two-images", lambda: (_I32, _EMB_32, _MAP_TWO)),
        ("many-tokens", lambda: (_I32, _EMB_64, _MAP_MANYTOK)),
        ("out-of-range-patches", lambda: (_I32, _EMB_32, _MAP_OOR)),
        ("no-image-seq-length", lambda: (_I32_NOSEQ, _EMB_32, _MAP_NOSEQ)),
        ("duplicate-addresses", lambda: (_I32, _EMB_32, _MAP_DUP)),
        ("n-patch-16", lambda: (_I16, _EMB_32, _MAP_NP16)),
        ("large", lambda: (_I32, _EMB_32, _MAP_LARGE)),
    ]
```