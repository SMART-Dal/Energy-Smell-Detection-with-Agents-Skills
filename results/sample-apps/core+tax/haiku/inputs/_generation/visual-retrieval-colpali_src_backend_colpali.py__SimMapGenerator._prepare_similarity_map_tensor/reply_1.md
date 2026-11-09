```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


# ---------------------------------------------------------------------------
# Helpers (all setup happens at import time or inside the thunks, never timed)
# ---------------------------------------------------------------------------

def _make_instance(n_patch=32, processor_seq_length=1024):
    """Build a SimMapGenerator without running __init__ (which loads a model)."""
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if processor_seq_length is None:
        # exercises the `hasattr(self.processor, "image_seq_length")` fallback
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=processor_seq_length)
    return inst


def _make_query_embs(n_tokens, dim=128, seed=0):
    rng = random.Random(seed)
    data = [[rng.uniform(-1.0, 1.0) for _ in range(dim)] for _ in range(n_tokens)]
    return torch.tensor(data, dtype=torch.float32)


def _make_sim_map(n_cells, n_query_tokens, patch_range, rng,
                  skip_ratio=0.0, address_pool=None):
    cells = []
    for _ in range(n_cells):
        if address_pool is not None:
            patch, qt = address_pool[rng.randrange(len(address_pool))]
        else:
            if skip_ratio > 0.0 and rng.random() < skip_ratio:
                # patch >= image_seq_length -> skipped by the function
                patch = rng.randrange(patch_range, patch_range + 1000)
            else:
                patch = rng.randrange(patch_range)
            qt = rng.randrange(n_query_tokens)
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.uniform(-1.0, 1.0),
        })
    return {"quantized": {"cells": cells}}


def _build(n_maps, n_query_tokens, n_cells, n_patch=32, patch_range=1024,
           processor_seq_length=1024, skip_ratio=0.0, dup_pool=None, seed=0):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, processor_seq_length)
    query_embs = _make_query_embs(n_query_tokens, seed=seed)
    pool = None
    if dup_pool is not None:
        pool = [(rng.randrange(patch_range), rng.randrange(n_query_tokens))
                for _ in range(dup_pool)]
    maps = [
        _make_sim_map(n_cells, n_query_tokens, patch_range, rng, skip_ratio, pool)
        for _ in range(n_maps)
    ]
    return inst, query_embs, maps


# ---------------------------------------------------------------------------
# Measured inputs -- built once here, reused by the thunks.
# The function never mutates its arguments, so the same objects can be reused.
# ---------------------------------------------------------------------------

# 1) small, typical request: a few pages, moderate cell count
_C1 = _build(3, 16, 500, seed=1)

# 2) few maps but very dense cell lists
_C2 = _build(2, 16, 4000, seed=2)

# 3) many maps (many pages), few query tokens
_C3 = _build(6, 8, 800, seed=3)

# 4) half of the cells have patch >= image_seq_length (skip path)
_C4 = _build(4, 16, 3000, skip_ratio=0.5, seed=4)

# 5) duplicate addresses -> lots of overwrites in the tensor
_C5 = _build(3, 16, 3000, dup_pool=150, seed=5)

# 6) processor without image_seq_length -> fallback to 1024
_C6 = _build(3, 16, 2000, processor_seq_length=None, seed=6)

# 7) different n_patch / image_seq_length geometry
_C7 = _build(4, 16, 2000, n_patch=16, patch_range=256,
             processor_seq_length=256, seed=7)

# 8) largest workload: many maps, many query tokens, dense cells
_C8 = _build(4, 24, 5000, seed=8)


def checks():
    inst = _make_instance(32, 1024)
    q8 = _make_query_embs(8, seed=100)
    q0 = _make_query_embs(0, seed=101)
    return [
        ("empty-maps", lambda: (inst, q8, [])),
        ("empty-cells", lambda: (inst, q8, [{"quantized": {"cells": []}}])),
        ("zero-tokens", lambda: (inst, q0, [{"quantized": {"cells": []}}])),
    ]


def cases():
    return [
        ("small-typical", lambda: _C1),
        ("dense-cells", lambda: _C2),
        ("many-maps", lambda: _C3),
        ("skip-heavy", lambda: _C4),
        ("duplicate-addresses", lambda: _C5),
        ("no-image-seq-length", lambda: _C6),
        ("n-patch-16", lambda: _C7),
        ("large", lambda: _C8),
    ]
```