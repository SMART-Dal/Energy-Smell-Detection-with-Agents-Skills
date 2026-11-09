import random

import torch
from PIL import Image

from backend.colpali import SimMapGenerator

# Build the instance without loading the (network/GPU) model: the method only
# needs the class-level `colormap` and the static `_normalize_sim_map`.
_INSTANCE = object.__new__(SimMapGenerator)

# `img` is accepted but never used by the body; a real PIL image keeps it realistic.
_IMG = Image.new("RGB", (256, 256))


def _sim_map(shape, seed, lo=-1.0, hi=1.0):
    """A float32 similarity-map tensor of the given (h, w) shape."""
    rng = random.Random(seed)
    h, w = shape
    data = [[rng.uniform(lo, hi) for _ in range(w)] for _ in range(h)]
    return torch.tensor(data, dtype=torch.float32)


def checks():
    return [
        ("single-pixel", lambda: (_INSTANCE, _IMG, _sim_map((1, 1), 100), (64, 64))),
        ("empty-map", lambda: (_INSTANCE, _IMG, _sim_map((0, 0), 101), (128, 128))),
        ("none-original-size", lambda: (_INSTANCE, _IMG, _sim_map((4, 4), 102), None)),
    ]


def cases():
    return [
        # smallest resolution (both dims clamp to 32)
        ("tiny-32", lambda: (_INSTANCE, _IMG, _sim_map((32, 32), 0, -1.0, 1.0), (256, 256))),
        # small square, non-negative values
        ("small-64", lambda: (_INSTANCE, _IMG, _sim_map((32, 32), 1, 0.0, 1.0), (512, 512))),
        # mid square, wider value range
        ("mid-128", lambda: (_INSTANCE, _IMG, _sim_map((32, 32), 2, -3.0, 3.0), (1024, 1024))),
        # wide aspect ratio, very large value range
        ("wide-200x100", lambda: (_INSTANCE, _IMG, _sim_map((32, 32), 3, -10.0, 10.0), (1600, 800))),
        # tall aspect ratio, near-constant values
        ("tall-100x200", lambda: (_INSTANCE, _IMG, _sim_map((32, 32), 4, 0.4, 0.6), (800, 1600))),
        # larger patch grid -> heavier bicubic resize
        ("bigmap-256", lambda: (_INSTANCE, _IMG, _sim_map((64, 64), 5, -1.0, 1.0), (2048, 2048))),
        # biggest output resolution
        ("large-300", lambda: (_INSTANCE, _IMG, _sim_map((32, 32), 6, 0.0, 1.0), (2400, 2400))),
        # non-square patch grid, mixed range
        ("nonsquare-150x225", lambda: (_INSTANCE, _IMG, _sim_map((16, 48), 7, -5.0, 5.0), (1200, 1800))),
    ]
