import logging
import random

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

# --------------------------------------------------------------------------
# constants / instance
# --------------------------------------------------------------------------

_N_PATCH = 32
_PATCHES = _N_PATCH * _N_PATCH
_EMB_DIM = 128


def _build_instance():
    # The real __init__ downloads a ColPali model from the hub; build the
    # object without it and just set the plain fields the method reads.
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.model_name = "vidore/colpali-v1.2"
    inst.n_patch = _N_PATCH
    inst.device = "cpu"
    inst.logger = logging.getLogger("simmap-generator-test")
    inst.model = None
    inst.processor = None
    return inst


_INSTANCE = _build_instance()

# --------------------------------------------------------------------------
# images on disk (like main.py, which passes file paths)
# --------------------------------------------------------------------------

_IMG_DIR = WORKDIR / "simmap_images"
_IMG_DIR.mkdir(parents=True, exist_ok=True)


def _write_image(path, size, seed, style):
    w, h = size
    if style == "gradient":
        x = np.linspace(0, 255, w, dtype=np.float32)[None, :]
        y = np.linspace(0, 255, h, dtype=np.float32)[:, None]
        r = np.clip(0.7 * x + 0.3 * y, 0, 255)
        g = np.clip(0.3 * x + 0.7 * y, 0, 255)
        b = np.clip(0.5 * (x + y), 0, 255)
        arr = np.stack([r, g, b], axis=-1).astype(np.uint8)
    else:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        arr = np.empty((h, w, 3), dtype=np.uint8)
        arr[..., 0] = np.clip(127 + 100 * np.sin(xx / 17.0 + seed), 0, 255).astype(np.uint8)
        arr[..., 1] = np.clip(127 + 100 * np.sin(yy / 13.0 + 0.7 * seed), 0, 255).astype(np.uint8)
        arr[..., 2] = np.clip(127 + 100 * np.sin((xx + yy) / 23.0), 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(path)


_IMAGE_SPECS = [
    ("img0.png", (160, 120), 1, "gradient"),
    ("img1.png", (256, 192), 2, "waves"),
    ("img2.png", (320, 240), 3, "gradient"),
    ("img3.png", (384, 288), 4, "waves"),
    ("img4.png", (448, 336), 5, "gradient"),
    ("img5.png", (512, 384), 6, "waves"),
    ("img6.png", (256, 256), 7, "gradient"),
    ("img7.png", (240, 320), 8, "waves"),
]

_IMAGE_PATHS = []
for _name, _size, _seed, _style in _IMAGE_SPECS:
    _p = _IMG_DIR / _name
    _write_image(_p, _size, _seed, _style)
    _IMAGE_PATHS.append(_p)

# --------------------------------------------------------------------------
# query side data
# --------------------------------------------------------------------------

_TOKEN_POOL = [
    "▁the", "▁dog", "▁cat", "2", "0", "3", "▁running", "norwegian",
    "unlisted", "▁hi", "<bos>", "<pad>", ":", "\n", "▁", "?", ")", "%",
    "/)", "Question", "▁a", "▁b", "▁c", "▁d", "▁e", "▁f", "▁g", "▁h",
    "▁i", "▁j", "▁k", "▁l", "▁m", "▁n", "▁o", "▁p", "▁q", "▁r",
]


def _build(n_images, n_tokens, img_indices, seed, query):
    rng = random.Random(seed)
    q_embs = torch.tensor(
        [[[rng.gauss(0.0, 1.0) for _ in range(_EMB_DIM)] for _ in range(n_tokens)]],
        dtype=torch.float32,
    )
    token_idx_map = {
        i: _TOKEN_POOL[rng.randrange(len(_TOKEN_POOL))] for i in range(n_tokens)
    }
    images = [_IMAGE_PATHS[j % len(_IMAGE_PATHS)] for j in img_indices]

    vespa_sim_maps = []
    for k in range(n_images):
        r = random.Random(seed * 131 + k)
        smap = {}
        for i in range(n_tokens):
            if (seed + i + k) % 3 == 0:
                v = np.array([r.random() for _ in range(_PATCHES)], dtype=np.float32)
            else:
                base = np.linspace(0.0, 1.0, _N_PATCH, dtype=np.float32)
                noise = np.array(
                    [r.random() for _ in range(_PATCHES)], dtype=np.float32
                ).reshape(_N_PATCH, _N_PATCH)
                blob = np.outer(base, base) + 0.05 * noise
                v = blob.reshape(-1).astype(np.float32)
            smap[i] = v
        vespa_sim_maps.append(smap)

    return (query, q_embs, token_idx_map, images, vespa_sim_maps)


_CASE_SPECS = {
    "c1": (1, 8, [0], 101, "How many people are seated at the table?"),
    "c2": (2, 10, [1, 2], 202, "What is the total revenue in 2023?"),
    "c3": (4, 8, [2, 3, 6, 7], 303, "List the dates and the amounts."),
    "c4": (3, 12, [3, 6, 7], 404, "Summarize the second paragraph of the document."),
    "c5": (5, 8, [6, 0, 2, 4, 1], 505, "Which city has the highest population?"),
    "c6": (2, 6, [5, 3], 606, "Total amount due including taxes"),
    "c7": (1, 36, [7], 707, "Explain the difference between the two proposals in detail."),
    "c8": (8, 6, [0, 1, 2, 3, 4, 5, 6, 7], 808, "invoice number 42"),
}

_CASE_DATA = {k: _build(*v) for k, v in _CASE_SPECS.items()}


def _replicate(key):
    query, q_embs, token_idx_map, images, vespa = _CASE_DATA[key]
    return (
        _INSTANCE,
        query,
        q_embs.clone(),
        dict(token_idx_map),
        list(images),
        vespa,
    )


# --------------------------------------------------------------------------
# checks (small edge inputs, never measured)
# --------------------------------------------------------------------------

_CHECK_QEMBS = {
    n: torch.zeros((1, n, _EMB_DIM), dtype=torch.float32) for n in (1, 4)
}
_CHECK_MAP = np.linspace(0.0, 1.0, _PATCHES, dtype=np.float32)


def checks():
    return [
        (
            "no-images",
            lambda: (_INSTANCE, "hello", _CHECK_QEMBS[4].clone(),
                     {i: "▁a" for i in range(4)}, [], []),
        ),
        (
            "empty-token-map",
            lambda: (_INSTANCE, "hello", _CHECK_QEMBS[1].clone(), {},
                     [_IMAGE_PATHS[0]], [{}]),
        ),
        (
            "single-token",
            lambda: (_INSTANCE, "hello", _CHECK_QEMBS[1].clone(), {0: "▁dog"},
                     [_IMAGE_PATHS[0]], [{0: _CHECK_MAP}]),
        ),
    ]


# --------------------------------------------------------------------------
# measured cases
# --------------------------------------------------------------------------


def cases():
    return [
        ("one-image-few-tokens", lambda: _replicate("c1")),
        ("two-images", lambda: _replicate("c2")),
        ("four-images", lambda: _replicate("c3")),
        ("three-mid-images-more-tokens", lambda: _replicate("c4")),
        ("five-square-images", lambda: _replicate("c5")),
        ("large-images", lambda: _replicate("c6")),
        ("many-tokens", lambda: _replicate("c7")),
        ("many-images", lambda: _replicate("c8")),
    ]
