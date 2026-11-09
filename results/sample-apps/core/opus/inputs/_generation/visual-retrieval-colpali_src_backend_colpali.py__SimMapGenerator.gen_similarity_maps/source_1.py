import logging
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

N_PATCH = 32
EMB_DIM = 128

_LOGGER = logging.getLogger("simmap-inputs")

# Tokens that pass `should_filter_token` (words / things with digits / '▁'-prefixed).
_KEPT_TOKENS = [
    "norwegian", "unlisted", "hi", "hello", "world", "▁hi", "▁norwegian",
    "▁2", "2", "0", "3", "test123", "colpali", "▁world", "▁hello",
    "image", "▁image", "query", "▁query", "similarity", "▁similarity",
]

# Tokens that `should_filter_token` rejects: '<...>', whitespace, punctuation,
# 'Question', bare '▁', and '_'-prefixed tokens.
_FILTERED_TOKENS = [
    "<bos>", "<pad>", "Question", ":", "?", ")", "%", "/)", "\n", "▁", "   ", "_x",
]


def _make_generator():
    """Build a real SimMapGenerator instance without loading the ColPali model.

    The repository's own startup handler calls ``SimMapGenerator(logger=...)``
    which downloads the model from the Hub; that is unavailable here.  We build
    the object directly and set the fields the tested method reads (``n_patch``),
    which is plain data assignment on a real instance of the real class.
    """
    gen = object.__new__(SimMapGenerator)
    gen.model_name = "vidore/colpali-v1.2"
    gen.n_patch = N_PATCH
    gen.device = "cpu"
    gen.logger = _LOGGER
    gen.model = None
    gen.processor = None
    return gen


def _write_image(path, w, h, seed):
    rng = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    r = (xx * 255 // max(w - 1, 1)).astype(np.uint8)
    g = (yy * 255 // max(h - 1, 1)).astype(np.uint8)
    b = (((np.sin(xx / 37.0) * np.cos(yy / 53.0)) + 1.0) * 127.5).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)
    for _ in range(6):
        x0 = int(rng.randint(0, max(w - 20, 1)))
        y0 = int(rng.randint(0, max(h - 20, 1)))
        rw = int(rng.randint(10, 60))
        rh = int(rng.randint(10, 60))
        arr[y0:y0 + rh, x0:x0 + rw] = rng.randint(0, 256, size=3, dtype=np.uint8)
    Image.fromarray(arr, "RGB").save(path)


_IMG_SMALL = WORKDIR / "simmap_img_small.png"
_IMG_SMALL2 = WORKDIR / "simmap_img_small2.png"
_IMG_MED = WORKDIR / "simmap_img_med.png"
_IMG_MED2 = WORKDIR / "simmap_img_med2.png"
_IMG_MED3 = WORKDIR / "simmap_img_med3.png"
_IMG_LARGE = WORKDIR / "simmap_img_large.png"
_IMG_LARGE2 = WORKDIR / "simmap_img_large2.png"
_IMG_WIDE = WORKDIR / "simmap_img_wide.png"

_write_image(_IMG_SMALL, 400, 500, 1)
_write_image(_IMG_SMALL2, 420, 480, 2)
_write_image(_IMG_MED, 512, 640, 3)
_write_image(_IMG_MED2, 640, 512, 4)
_write_image(_IMG_MED3, 560, 600, 5)
_write_image(_IMG_LARGE, 800, 1000, 6)
_write_image(_IMG_LARGE2, 900, 700, 7)
_write_image(_IMG_WIDE, 1024, 512, 8)


def _token_map(n_tokens, kept_ratio, seed):
    rng = random.Random(seed)
    m = {}
    for i in range(n_tokens):
        if rng.random() < kept_ratio:
            m[i] = rng.choice(_KEPT_TOKENS)
        else:
            m[i] = rng.choice(_FILTERED_TOKENS)
    return m


def _sim_maps(n_images, n_tokens, seed):
    """One Vespa-style similarity map per image: patch index -> per-token scores."""
    rng = random.Random(seed)
    maps = []
    for _ in range(n_images):
        d = {}
        for p in range(N_PATCH * N_PATCH):
            d[str(p)] = [rng.random() for _ in range(n_tokens)]
        maps.append(d)
    return maps


def _make_case(n_tokens, kept_ratio, image_paths, seed):
    token_map = _token_map(n_tokens, kept_ratio, seed)
    rng = np.random.RandomState(seed + 1000)
    embs = torch.tensor(rng.randn(1, n_tokens, EMB_DIM).astype(np.float32))
    sim_maps = _sim_maps(len(image_paths), n_tokens, seed + 2000)
    return token_map, embs, sim_maps, list(image_paths)


_GEN = _make_generator()

_CASES = {
    "all-filtered": _make_case(20, 0.0, [_IMG_MED, _IMG_MED2], 11),
    "all-kept": _make_case(6, 1.0, [_IMG_SMALL], 12),
    "two-medium": _make_case(10, 0.8, [_IMG_MED, _IMG_MED2], 13),
    "three-medium": _make_case(8, 0.75, [_IMG_MED, _IMG_MED2, _IMG_MED3], 14),
    "one-large": _make_case(12, 0.85, [_IMG_LARGE], 15),
    "two-large": _make_case(8, 0.75, [_IMG_LARGE, _IMG_LARGE2], 16),
    "four-small": _make_case(6, 0.85, [_IMG_SMALL, _IMG_SMALL2, _IMG_SMALL, _IMG_SMALL2], 17),
    "many-tokens": _make_case(30, 0.8, [_IMG_MED], 18),
}

_QUERY = "norwegian unlisted companies"


def _thunk(name):
    token_map, embs, sim_maps, images = _CASES[name]
    return lambda: (_GEN, _QUERY, embs, token_map, images, sim_maps)


def checks():
    def _embs(n):
        return torch.tensor(np.zeros((1, n, EMB_DIM), dtype=np.float32))

    return [
        ("empty-token-map",
         lambda: (_GEN, "q", _embs(2), {}, [_IMG_SMALL], [{"0": [0.1, 0.2]}])),
        ("single-token",
         lambda: (_GEN, "q", _embs(1), {0: "hello"}, [_IMG_SMALL], [{"0": [0.5]}])),
        ("all-filtered-tokens",
         lambda: (_GEN, "q", _embs(3), {0: "<bos>", 1: "▁", 2: "?"}, [_IMG_SMALL],
                  [{"0": [0.1, 0.2, 0.3]}])),
    ]


def cases():
    return [
        ("all-filtered", _thunk("all-filtered")),
        ("all-kept", _thunk("all-kept")),
        ("two-medium", _thunk("two-medium")),
        ("three-medium", _thunk("three-medium")),
        ("one-large", _thunk("one-large")),
        ("two-large", _thunk("two-large")),
        ("four-small", _thunk("four-small")),
        ("many-tokens", _thunk("many-tokens")),
    ]
