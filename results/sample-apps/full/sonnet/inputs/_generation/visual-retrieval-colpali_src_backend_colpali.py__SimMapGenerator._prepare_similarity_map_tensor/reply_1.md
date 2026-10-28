```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    """Build a SimMapGenerator without running the (network) model loader."""
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = None
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_cells(rng, n_cells, n_query_tokens, patch_choices):
    cells = []
    for _ in range(n_cells):
        patch = rng.choice(patch_choices)
        qt = rng.randrange(n_query_tokens)
        cells.append(
            {
                "address": {"patch": str(patch), "querytoken": str(qt)},
                "value": rng.random(),
            }
        )
    return cells


def _make_maps(seed, n_maps, n_cells, n_query_tokens, patch_choices):
    rng = random.Random(seed)
    return [
        {"quantized": {"cells": _make_cells(rng, n_cells, n_query_tokens, patch_choices)}}
        for _ in range(n_maps)
    ]


torch.manual_seed(0)

_INST_32_1024 = _make_instance(32, 1024)
_INST_16_256 = _make_instance(16, 256)
_INST_32_FALLBACK = _make_instance(32, None)

_Q8 = torch.randn(8, 128)
_Q16 = torch.randn(16, 128)
_Q64 = torch.randn(64, 128)

# 4 images, 1500 cells each, 16 query tokens, full 32x32 grid -> 65536 output values
_MAPS_TYPICAL = _make_maps(0, 4, 1500, 16, range(1024))
# 6 images -> 98304 output values
_MAPS_MANY_IMGS = _make_maps(1, 6, 1500, 16, range(1024))
# 2 images, very dense cells, only 8 query tokens
_MAPS_DENSE = _make_maps(2, 2, 20000, 8, range(1024))
# n_patch=16, image_seq_length=256 -> 16x16 grid
_MAPS_SMALL_PATCH = _make_maps(3, 4, 4000, 16, range(256))
# every patch is out of range -> all cells hit the `continue`
_MAPS_SKIPPED = _make_maps(4, 4, 20000, 16, range(1024, 4096))
# processor has no image_seq_length -> fallback to 1024
_MAPS_FALLBACK = _make_maps(5, 4, 2500, 16, range(1024))
# a single image but 64 query tokens
_MAPS_LONG_QUERY = _make_maps(6, 1, 3000, 64, range(1024))
# only 64 distinct patches -> heavy overwriting of the same cells
_MAPS_DUPLICATES = _make_maps(7, 4, 4000, 16, range(64))


def checks():
    q = torch.randn(4, 128)
    return [
        ("empty-maps", lambda: (_INST_32_1024, q, [])),
        ("empty-cells", lambda: (_INST_32_1024, q, [{"quantized": {"cells": []}}])),
        (
            "fallback-skip",
            lambda: (
                _INST_32_FALLBACK,
                q,
                [
                    {
                        "quantized": {
                            "cells": [
                                {
                                    "address": {"patch": "2000", "querytoken": "0"},
                                    "value": 0.5,
                                }
                            ]
                        }
                    }
                ],
            ),
        ),
    ]


def cases():
    return [
        ("typical", lambda: (_INST_32_1024, _Q16, _MAPS_TYPICAL)),
        ("many-images", lambda: (_INST_32_1024, _Q16, _MAPS_MANY_IMGS)),
        ("dense-few-tokens", lambda: (_INST_32_1024, _Q8, _MAPS_DENSE)),
        ("small-patch-grid", lambda: (_INST_16_256, _Q16, _MAPS_SMALL_PATCH)),
        ("mostly-skipped", lambda: (_INST_32_1024, _Q16, _MAPS_SKIPPED)),
        ("fallback-seq-len", lambda: (_INST_32_FALLBACK, _Q16, _MAPS_FALLBACK)),
        ("long-query", lambda: (_INST_32_1024, _Q64, _MAPS_LONG_QUERY)),
        ("duplicate-patches", lambda: (_INST_32_1024, _Q16, _MAPS_DUPLICATES)),
    ]
```