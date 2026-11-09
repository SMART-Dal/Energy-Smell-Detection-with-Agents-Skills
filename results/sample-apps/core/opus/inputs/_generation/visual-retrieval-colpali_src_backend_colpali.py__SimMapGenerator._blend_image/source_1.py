import random

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

# Build the instance without running __init__ (which would download/load the
# ColPali model).  _blend_image only needs the class-level colormap and the
# static _normalize_sim_map, both reachable through the class.
_INSTANCE = SimMapGenerator.__new__(SimMapGenerator)

# Callers always hand a real PIL image; _blend_image itself does not use it.
_IMG = Image.new("RGB", (512, 512), (120, 140, 160))


def _uniform_map(h, w, seed, low=0.0, high=1.0):
    rng = random.Random(seed)
    data = [[rng.uniform(low, high) for _ in range(w)] for _ in range(h)]
    return torch.tensor(data, dtype=torch.float32)


def _gradient_map(h, w):
    ys = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
    data = (ys * 0.6 + xs * 0.4).astype(np.float32)
    return torch.from_numpy(data)


# Similarity maps as produced by the model (n_patch x n_patch), built once.
_MAP_A = _uniform_map(32, 32, 0)
_MAP_B = _uniform_map(32, 32, 1)
_MAP_C = _uniform_map(32, 32, 2)
_MAP_D = _uniform_map(32, 32, 3)
_MAP_E = _uniform_map(32, 32, 4)
_MAP_F = _uniform_map(32, 32, 5)
_MAP_G = _gradient_map(64, 64)
_MAP_H = _uniform_map(32, 32, 6, -5.0, 5.0)


def checks():
    return [
        ("single-pixel-map", lambda: (_INSTANCE, _IMG, _uniform_map(1, 1, 10), (256, 256))),
        ("zero-size", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 11), (0, 0))),
        ("single-row-map", lambda: (_INSTANCE, _IMG, _uniform_map(1, 32, 12), (1024, 768))),
    ]


def cases():
    return [
        ("square-512", lambda: (_INSTANCE, _IMG, _MAP_A, (512, 512))),
        ("square-1k", lambda: (_INSTANCE, _IMG, _MAP_B, (1024, 1024))),
        ("landscape-4k", lambda: (_INSTANCE, _IMG, _MAP_C, (4000, 3000))),
        ("portrait-4k", lambda: (_INSTANCE, _IMG, _MAP_D, (3000, 4000))),
        ("panorama", lambda: (_INSTANCE, _IMG, _MAP_E, (8000, 1200))),
        ("tall", lambda: (_INSTANCE, _IMG, _MAP_F, (1200, 8000))),
        ("gradient-bigmap", lambda: (_INSTANCE, _IMG, _MAP_G, (4000, 3000))),
        ("wide-range", lambda: (_INSTANCE, _IMG, _MAP_H, (6000, 4000))),
    ]
