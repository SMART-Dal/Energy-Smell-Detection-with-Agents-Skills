# Inputs for text-video-search/src/python/embedding.py::sample_images, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

import numpy as np

from embedding import sample_images


def _rng(seed):
    # deterministic, seeded from random.Random as requested
    return np.random.default_rng(random.Random(seed).getrandbits(32))


def _frames(n, shape, seed, dtype="uint8"):
    rng = _rng(seed)
    if dtype == "uint8":
        return [rng.integers(0, 256, size=shape, dtype=np.uint8) for _ in range(n)]
    if dtype == "float32":
        return [rng.random(size=shape, dtype=np.float32) for _ in range(n)]
    raise ValueError(dtype)


# --- module level data (built once, never timed) -----------------------------

# 80 frames of 64x64 RGB  -> 983_040 values
_FRAMES_80_64x64x3 = _frames(80, (64, 64, 3), 0)

# 8 frames of 64x64 RGB   -> 98_304 values
_FRAMES_8_64x64x3 = _frames(8, (64, 64, 3), 1)

# 320 frames of 32x32 RGB -> 983_040 values
_FRAMES_320_32x32x3 = _frames(320, (32, 32, 3), 2)

# 20 frames of 128x128 RGB -> 983_040 values
_FRAMES_20_128x128x3 = _frames(20, (128, 128, 3), 3)

# 200 grayscale frames of 64x64 -> 819_200 values
_FRAMES_200_64x64_GRAY = _frames(200, (64, 64), 4)

# 60 frames of 64x64 RGBA -> 983_040 values
_FRAMES_60_64x64x4 = _frames(60, (64, 64, 4), 5)

# 80 frames of 64x64 RGB float32 -> 983_040 values (bigger byte copy)
_FRAMES_80_64x64x3_F32 = _frames(80, (64, 64, 3), 6, dtype="float32")


def checks():
    return [
        ("empty-images", lambda: ([], 5)),
        ("single-frame", lambda: ([np.zeros((4, 4, 3), dtype=np.uint8)], 3)),
        ("none-images", lambda: (None, 3)),
    ]


def cases():
    return [
        # sampling path, 8 of 80 equal-spaced frames
        ("sample-8-of-80-uint8", lambda: (_FRAMES_80_64x64x3, 8)),
        # sampling path, single frame out of many
        ("sample-1-of-80", lambda: (_FRAMES_80_64x64x3, 1)),
        # no-sampling path (number_to_sample >= len(images))
        ("no-sampling-8-frames", lambda: (_FRAMES_8_64x64x3, 100)),
        # many small frames, moderate sample count
        ("sample-30-of-320-mid", lambda: (_FRAMES_320_32x32x3, 30)),
        # few large frames, tiny sample
        ("sample-2-of-20-large", lambda: (_FRAMES_20_128x128x3, 2)),
        # grayscale frames
        ("sample-20-of-200-gray", lambda: (_FRAMES_200_64x64_GRAY, 20)),
        # RGBA frames
        ("sample-6-of-60-rgba", lambda: (_FRAMES_60_64x64x4, 6)),
        # float32 frames (heavier copy)
        ("sample-8-of-80-float32", lambda: (_FRAMES_80_64x64x3_F32, 8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['sample-8-of-80-float32', 'sample-30-of-320-mid', 'sample-20-of-200-gray', 'sample-8-of-80-uint8']
_KEEP_CHECKS = ['empty-images', 'single-frame', 'none-images']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
