# Inputs for visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    # Build the object without running __init__ (which would download the
    # ColPali model from the network).  The method under test only reads
    # ``self.n_patch`` and ``self.processor.image_seq_length``.
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_cells(n_cells, n_tokens, patch_max, seed, dup_pool=None):
    rng = random.Random(seed)
    cells = []
    if dup_pool is not None:
        pool = [(rng.randrange(patch_max), rng.randrange(n_tokens))
                for _ in range(dup_pool)]
        n_pool = len(pool)
        for _ in range(n_cells):
            patch, qt = pool[rng.randrange(n_pool)]
            cells.append({
                "address": {"patch": patch, "querytoken": qt},
                "value": rng.random(),
            })
    else:
        for _ in range(n_cells):
            cells.append({
                "address": {
                    "patch": rng.randrange(patch_max),
                    "querytoken": rng.randrange(n_tokens),
                },
                "value": rng.random(),
            })
    return cells


def _make_maps(n_maps, n_cells, n_tokens, patch_max, seed, dup_pool=None):
    return [
        {"quantized": {
            "cells": _make_cells(n_cells, n_tokens, patch_max, seed + 100 * i, dup_pool)
        }}
        for i in range(n_maps)
    ]


def _build(n_maps, n_tokens, n_patch, image_seq_length, n_cells, seed,
           patch_max=None, dup_pool=None, processor_isl=True):
    if patch_max is None:
        patch_max = image_seq_length
    inst = _make_instance(n_patch, image_seq_length if processor_isl else None)
    g = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, 128, generator=g)
    maps = _make_maps(n_maps, n_cells, n_tokens, patch_max, seed, dup_pool)
    return (inst, query_embs, maps)


# ---- prebuilt workloads (setup happens at import time, never timed) ----
_C_TYPICAL = _build(4, 16, 32, 1024, 4000, 0)
_C_MANY_MAPS = _build(8, 8, 32, 1024, 2500, 1)
_C_DENSE = _build(2, 16, 32, 1024, 10000, 2)
_C_NO_ISL = _build(4, 16, 32, 1024, 4000, 3, processor_isl=False)
_C_TRUNCATED = _build(4, 16, 32, 256, 6000, 4, patch_max=1024)
_C_DUPLICATES = _build(4, 16, 32, 1024, 5000, 5, dup_pool=48)
_C_LARGE_GRID = _build(1, 8, 64, 4096, 15000, 6)
_C_SMALL_GRID = _build(1, 64, 16, 256, 10000, 7)


def cases():
    return [
        ("typical-4maps-16tokens", lambda: _C_TYPICAL),
        ("many-maps-8", lambda: _C_MANY_MAPS),
        ("dense-two-maps", lambda: _C_DENSE),
        ("processor-without-image-seq-length", lambda: _C_NO_ISL),
        ("truncated-patches", lambda: _C_TRUNCATED),
        ("duplicate-addresses", lambda: _C_DUPLICATES),
        ("large-patch-grid", lambda: _C_LARGE_GRID),
        ("small-grid-many-tokens", lambda: _C_SMALL_GRID),
    ]


def checks():
    inst = _make_instance(32, 256)
    q = torch.randn(4, 128, generator=torch.Generator().manual_seed(7))
    skipped = [{"quantized": {"cells": [
        {"address": {"patch": 300 + i, "querytoken": i % 4}, "value": 1.0}
        for i in range(5)
    ]}}]
    return [
        ("empty-maps", lambda: (inst, q, [])),
        ("empty-cells", lambda: (inst, q, [{"quantized": {"cells": []}}])),
        ("all-out-of-range", lambda: (inst, q, skipped)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['duplicate-addresses', 'many-maps-8', 'dense-two-maps', 'typical-4maps-16tokens']
_KEEP_CHECKS = ['empty-maps', 'empty-cells', 'all-out-of-range']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
