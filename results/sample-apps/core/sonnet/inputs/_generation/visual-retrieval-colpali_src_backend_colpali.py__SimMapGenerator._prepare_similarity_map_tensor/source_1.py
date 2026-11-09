import random
import types

import torch

from backend.colpali import SimMapGenerator


_EMB_DIM = 128


def _make_generator(n_patch=32, image_seq_length=1024):
    """Build a SimMapGenerator without running __init__ (which loads a model)."""
    gen = object.__new__(SimMapGenerator)
    gen.n_patch = n_patch
    if image_seq_length is None:
        gen.processor = types.SimpleNamespace()          # no image_seq_length -> fallback 1024
    else:
        gen.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return gen


def _make_sim_map(n_cells, n_tokens, seed, max_patch=1024, value_scale=1.0):
    rng = random.Random(seed)
    cells = []
    for _ in range(n_cells):
        cells.append(
            {
                "address": {
                    "patch": str(rng.randrange(max_patch)),
                    "querytoken": str(rng.randrange(n_tokens)),
                },
                "value": round(rng.uniform(-value_scale, value_scale), 6),
            }
        )
    return {"quantized": {"cells": cells}}


def _make_embs(n_tokens):
    return torch.zeros((n_tokens, _EMB_DIM))


_GEN_DEFAULT = _make_generator(32, 1024)
_GEN_FALLBACK = _make_generator(32, None)
_GEN_SMALL_SEQ = _make_generator(32, 512)
_GEN_P16 = _make_generator(16, 1024)

_EMBS_10 = _make_embs(10)
_EMBS_15 = _make_embs(15)
_EMBS_20 = _make_embs(20)
_EMBS_25 = _make_embs(25)
_EMBS_30 = _make_embs(30)
_EMBS_40 = _make_embs(40)

_MAP_1 = _make_sim_map(3000, 10, 0)
_MAPS_2 = [_make_sim_map(6000, 20, 1 + i) for i in range(4)]
_MAP_3 = _make_sim_map(15000, 25, 10)
_MAP_4 = _make_sim_map(10000, 15, 11, max_patch=2048)
_MAP_5 = _make_sim_map(8000, 20, 12)
_MAP_6 = _make_sim_map(12000, 20, 13, max_patch=1024)
_MAPS_7 = [_make_sim_map(4000, 30, 14 + i) for i in range(2)]
_MAPS_8 = [_make_sim_map(2500, 40, 20 + i) for i in range(2)]


def checks():
    return [
        ("empty-maps", lambda: (_GEN_DEFAULT, _make_embs(5), [])),
        (
            "empty-cells",
            lambda: (_GEN_DEFAULT, _make_embs(5), [{"quantized": {"cells": []}}]),
        ),
        (
            "zero-tokens",
            lambda: (
                _GEN_DEFAULT,
                _make_embs(0),
                [
                    {
                        "quantized": {
                            "cells": [
                                {
                                    "address": {"patch": "0", "querytoken": "0"},
                                    "value": 1.0,
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
        ("single-map-small", lambda: (_GEN_DEFAULT, _EMBS_10, [_MAP_1])),
        ("four-maps", lambda: (_GEN_DEFAULT, _EMBS_20, _MAPS_2)),
        ("dense-single-map", lambda: (_GEN_DEFAULT, _EMBS_25, [_MAP_3])),
        ("oversized-patches", lambda: (_GEN_DEFAULT, _EMBS_15, [_MAP_4])),
        ("no-image-seq-length", lambda: (_GEN_FALLBACK, _EMBS_20, [_MAP_5])),
        ("small-image-seq-length", lambda: (_GEN_SMALL_SEQ, _EMBS_20, [_MAP_6])),
        ("n-patch-16", lambda: (_GEN_P16, _EMBS_30, _MAPS_7)),
        ("many-tokens", lambda: (_GEN_DEFAULT, _EMBS_40, _MAPS_8)),
    ]
