import base64
import logging
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

logger = logging.getLogger("bench")

# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
_IMG_DIR = WORKDIR / "simmap_imgs"
_IMG_DIR.mkdir(parents=True, exist_ok=True)


def _make_img(name, w, h, seed):
    rng = random.Random(seed)
    arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    p = _IMG_DIR / name
    img.save(p)
    return str(p)


_IMG_SPECS = [
    ("a_256.png", 256, 256, 0),
    ("b_512.png", 512, 512, 1),
    ("c_384_512.png", 384, 512, 2),
    ("d_512_384.png", 512, 384, 3),
    ("e_1024.png", 1024, 1024, 4),
    ("f_200_300.png", 200, 300, 5),
    ("g_800_600.png", 800, 600, 6),
    ("h_640_480.png", 640, 480, 7),
]
_IMAGES = [_make_img(*spec) for spec in _IMG_SPECS]


def _to_b64(path_str):
    return "data:image/png;base64," + base64.b64encode(Path(path_str).read_bytes()).decode()


_B64_IMAGES = [_to_b64(p) for p in _IMAGES]

# ---------------------------------------------------------------------------
# Instance (bypass __init__ so the ColPali model is not loaded)
# ---------------------------------------------------------------------------
def _make_instance():
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = 32
    inst.logger = logger
    inst.model_name = "vidore/colpali-v1.2"
    inst.device = "cpu"
    inst.model = None
    inst.processor = None
    return inst


_INSTANCE = _make_instance()

# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
_PASS_TOKENS = [
    '2', '0', '3', '▁2', '▁hi', 'norwegian', 'unlisted',
    '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15',
    '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26',
    '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37',
    '38', '39', '40',
]
_FAIL_TOKENS = [
    '<bos>', 'Question', ':', '<pad>', '\n', '▁', '?', ')', '%', '/)',
    '<eos>', ' ', '!', '@', '#', '$', '^', '&', '*', '(', '_', '-', '+',
    '=', '[', ']', '{', '}', '|', '\\', ';', '"', "'", ',', '.', '<', '>',
    '/', '~', '`',
]

# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------
def _make_data(n_images, n_tokens, n_filtered, seed, image_choices, use_b64=False):
    rng = random.Random(seed)
    tokens = []
    for i in range(n_tokens):
        if i < n_filtered:
            tokens.append(_FAIL_TOKENS[i % len(_FAIL_TOKENS)])
        else:
            tokens.append(_PASS_TOKENS[(i - n_filtered) % len(_PASS_TOKENS)])
    rng.shuffle(tokens)
    token_idx_map = {i: t for i, t in enumerate(tokens)}

    images = []
    for i in range(n_images):
        if use_b64:
            images.append(_B64_IMAGES[image_choices[i % len(image_choices)]])
        else:
            images.append(_IMAGES[image_choices[i % len(image_choices)]])

    query_embs = torch.randn(1, n_tokens, 128, generator=torch.Generator().manual_seed(seed))

    n_patch = 32
    vespa_sim_maps = []
    for i in range(n_images):
        cells = []
        for t in range(n_tokens):
            for p in range(n_patch * n_patch):
                cells.append({
                    "address": {"query_token": str(t), "patch": str(p)},
                    "value": rng.random(),
                })
        vespa_sim_maps.append({"cells": cells})

    return query_embs, token_idx_map, images, vespa_sim_maps


def _make_mixed(n_images, n_tokens, n_filtered, seed):
    rng = random.Random(seed)
    tokens = []
    for i in range(n_tokens):
        if i < n_filtered:
            tokens.append(_FAIL_TOKENS[i % len(_FAIL_TOKENS)])
        else:
            tokens.append(_PASS_TOKENS[(i - n_filtered) % len(_PASS_TOKENS)])
    rng.shuffle(tokens)
    token_idx_map = {i: t for i, t in enumerate(tokens)}

    images = []
    for i in range(n_images):
        if i % 2 == 0:
            images.append(_IMAGES[i % len(_IMAGES)])
        else:
            images.append(_B64_IMAGES[i % len(_B64_IMAGES)])

    query_embs = torch.randn(1, n_tokens, 128, generator=torch.Generator().manual_seed(seed))

    n_patch = 32
    vespa_sim_maps = []
    for i in range(n_images):
        cells = []
        for t in range(n_tokens):
            for p in range(n_patch * n_patch):
                cells.append({
                    "address": {"query_token": str(t), "patch": str(p)},
                    "value": rng.random(),
                })
        vespa_sim_maps.append({"cells": cells})

    return query_embs, token_idx_map, images, vespa_sim_maps


# ---------------------------------------------------------------------------
# Edge cases (not measured)
# ---------------------------------------------------------------------------
def checks():
    empty_data = _make_data(0, 0, 0, 100, [], use_b64=False)
    one_img_empty_tokens = _make_data(1, 0, 0, 101, [0], use_b64=False)
    one_filtered = _make_data(1, 1, 1, 102, [0], use_b64=False)

    return [
        ("empty", lambda: (_INSTANCE, "q", *empty_data)),
        ("empty-tokens", lambda: (_INSTANCE, "q", *one_img_empty_tokens)),
        ("all-filtered-small", lambda: (_INSTANCE, "q", *one_filtered)),
    ]


# ---------------------------------------------------------------------------
# Measured cases
# ---------------------------------------------------------------------------
def cases():
    data1 = _make_data(1, 5, 2, 0, [0], use_b64=False)
    data2 = _make_data(4, 10, 3, 1, [0, 1, 2, 3], use_b64=False)
    data3 = _make_data(8, 5, 1, 2, [0, 1, 2, 3, 4, 5, 6, 7], use_b64=False)
    data4 = _make_data(2, 30, 10, 3, [0, 1], use_b64=False)
    data5 = _make_data(2, 6, 2, 4, [4, 6], use_b64=False)
    data6 = _make_data(5, 6, 2, 5, [0, 1, 2, 3, 4], use_b64=True)
    data7 = _make_mixed(6, 12, 4, 6)
    data8 = _make_data(1, 10, 10, 7, [0], use_b64=False)

    return [
        ("tiny", lambda: (_INSTANCE, "query", *data1)),
        ("medium", lambda: (_INSTANCE, "query", *data2)),
        ("many-images", lambda: (_INSTANCE, "query", *data3)),
        ("many-tokens", lambda: (_INSTANCE, "query", *data4)),
        ("large-images", lambda: (_INSTANCE, "query", *data5)),
        ("base64-images", lambda: (_INSTANCE, "query", *data6)),
        ("mixed", lambda: (_INSTANCE, "query", *data7)),
        ("all-filtered", lambda: (_INSTANCE, "query", *data8)),
    ]
