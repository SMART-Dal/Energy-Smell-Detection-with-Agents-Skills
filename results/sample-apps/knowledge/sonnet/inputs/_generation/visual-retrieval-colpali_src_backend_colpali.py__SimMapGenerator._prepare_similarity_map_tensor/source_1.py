import random
import types

import torch

from backend.colpali import SimMapGenerator


def _instance(n_patch, image_seq_length):
    # Build the instance without running __init__ (which loads a model from the hub).
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _query_embs(n_tokens):
    return torch.zeros((n_tokens, 128), dtype=torch.float32)


def _cells(n, n_tokens, image_seq_length, seed, miss_ratio=0.0, dup=False):
    rng = random.Random(seed)
    cells = []
    for _ in range(n):
        if dup:
            patch = rng.randrange(0, 32)
            query_token = rng.randrange(0, min(n_tokens, 4))
        else:
            query_token = rng.randrange(n_tokens)
            if rng.random() < miss_ratio:
                patch = rng.randrange(image_seq_length, image_seq_length + 512)
            else:
                patch = rng.randrange(0, image_seq_length)
        cells.append(
            {
                "address": {"patch": patch, "querytoken": query_token},
                "value": rng.random(),
            }
        )
    return cells


def _sim_maps(n_maps, n_cells, n_tokens, image_seq_length, seed, miss_ratio=0.0, dup=False):
    return [
        {
            "quantized": {
                "cells": _cells(
                    n_cells, n_tokens, image_seq_length, seed + i, miss_ratio, dup
                )
            }
        }
        for i in range(n_maps)
    ]


def _build(n_patch, image_seq_length, n_maps, n_cells, n_tokens, seed,
           miss_ratio=0.0, dup=False):
    inst = _instance(n_patch, image_seq_length)
    embs = _query_embs(n_tokens)
    eff_seq = 1024 if image_seq_length is None else image_seq_length
    maps = _sim_maps(n_maps, n_cells, n_tokens, eff_seq, seed, miss_ratio, dup)
    return (inst, embs, maps)


# ---- module level data (built once, reused by every call) ----
_C_TYPICAL = _build(32, 1024, 2, 4000, 32, 0)
_C_MANY_CELLS = _build(32, 1024, 1, 30000, 32, 1)
_C_MANY_MAPS = _build(32, 1024, 3, 3000, 32, 2)
_C_ALL_MISS = _build(32, 1024, 1, 25000, 32, 3, miss_ratio=1.0)
_C_FEW_TOKENS = _build(32, 1024, 1, 25000, 8, 4)
_C_DUPLICATES = _build(32, 1024, 2, 8000, 32, 5, dup=True)
_C_MIXED = _build(32, 1024, 2, 10000, 32, 6, miss_ratio=0.5)
_C_LARGE_SEQ = _build(32, 4096, 2, 10000, 16, 7, miss_ratio=0.2)


def checks():
    inst = _instance(32, 1024)
    embs = _query_embs(8)
    single = [
        {
            "quantized": {
                "cells": [
                    {"address": {"patch": 5, "querytoken": 1}, "value": 0.5}
                ]
            }
        }
    ]
    inst_no_attr = _instance(32, None)
    return [
        ("empty-maps", lambda: (inst, embs, [])),
        ("single-cell", lambda: (inst, embs, single)),
        ("no-image-seq-length", lambda: (inst_no_attr, embs, single)),
    ]


def cases():
    return [
        ("typical", lambda: _C_TYPICAL),
        ("many-cells", lambda: _C_MANY_CELLS),
        ("many-maps", lambda: _C_MANY_MAPS),
        ("all-miss", lambda: _C_ALL_MISS),
        ("few-tokens", lambda: _C_FEW_TOKENS),
        ("duplicates", lambda: _C_DUPLICATES),
        ("mixed-miss", lambda: _C_MIXED),
        ("large-image-seq", lambda: _C_LARGE_SEQ),
    ]
