import logging

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator


# --------------------------------------------------------------------------
# The real constructor downloads the ColPali weights from the Hub (network),
# which is not available here.  `gen_similarity_maps` itself never touches the
# model: it only uses `self.n_patch`, `self.colormap` and the private helpers,
# so we build the instance the same way the repo's own callers end up using it
# (an object with those fields set) and skip the weight download.
# --------------------------------------------------------------------------
_N_PATCH = 32
_EMB_DIM = 128


def _generator():
    gen = SimMapGenerator.__new__(SimMapGenerator)
    gen.model_name = "vidore/colpali-v1.2"
    gen.n_patch = _N_PATCH
    gen.device = "cpu"
    gen.logger = logging.getLogger("sim-map-generator")
    gen.model = None
    gen.processor = None
    return gen


_GEN = _generator()


# ------------------------------------------------------------------ images --
# Document page renders, written once under WORKDIR (setup is never timed).
_IMAGE_SPECS = {
    "a": (200, 260, 1),
    "b": (200, 260, 2),
    "c": (260, 340, 3),
    "d": (320, 420, 4),
    "e": (400, 520, 5),
    "f": (480, 640, 6),
    "g": (640, 800, 7),
    "h": (300, 900, 8),
    "i": (256, 256, 9),
}

_IMG = {}


def _build_images():
    for name, (w, h, seed) in _IMAGE_SPECS.items():
        path = WORKDIR / f"simmap_img_{name}.png"
        rng = np.random.default_rng(seed)
        arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        Image.fromarray(arr, "RGB").save(path, format="PNG")
        _IMG[name] = path


_build_images()


# ------------------------------------------------------------------ tokens --
_TOKENS = [
    "▁What", "▁is", "▁the", "▁total", "▁revenue", "▁for", "▁Q3", "▁2023",
    "?", "<bos>", "▁", "<pad>", ":", "▁in", "▁Norwegian", "▁kroner",
    "▁million", "▁USD", "▁compared", "▁to", "▁last", "▁year", "▁growth",
    "▁percent", "%", "▁and", "▁profit", "▁margin", "▁was", "▁higher",
    "▁than", "▁expected", "▁by", "▁analysts", "▁according", "▁Reuters",
    "▁data", "▁from", "▁company", "▁report", "▁showed", "▁today", "▁Oslo",
    "▁Norway", "▁shares", "▁rose", "▁2", ".", "3", "▁NOK", "▁1", "5",
    "▁per", "▁share", "▁on", "▁Friday", "▁The", "▁said", "▁it", "▁expects",
    "▁a", "▁around", "▁billion", "▁full", "▁year", "▁end", "▁2024",
    "▁outlook", "▁remains", "▁strong", "▁despite", "▁market", "▁volatility",
    "▁and", "▁currency", "▁headwinds", "▁in", "▁the", "▁region",
]

# A token map where most entries are filtered out by `should_filter_token`.
_TOKENS_FILTER_HEAVY = [
    "<bos>", "▁What", "<pad>", ":", "▁", "?", "▁revenue", "%", "▁", "\n",
    "/)", "▁total", "Question", "_x", "▁2023", "▁", "▁profit", "▁",
]


def _build_case(image_names, tokens, seed, low=0.0, high=1.0):
    """Build (query_embs, token_idx_map, images, vespa_sim_maps) for one call."""
    n_tokens = len(tokens)
    gen = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, _EMB_DIM, generator=gen)
    token_idx_map = {i: t for i, t in enumerate(tokens)}

    rng = np.random.default_rng(seed + 7919)
    vespa_sim_maps = []
    for _ in image_names:
        sim_map = {}
        for i in range(n_tokens):
            sim_map[i] = rng.uniform(low, high, size=(_N_PATCH, _N_PATCH)).tolist()
        vespa_sim_maps.append(sim_map)

    images = [_IMG[name] for name in image_names]
    return query_embs, token_idx_map, images, vespa_sim_maps


_C1 = _build_case(["d"], _TOKENS[0:10], 101)
_C2 = _build_case(["f"], _TOKENS[10:20], 102)
_C3 = _build_case(["a", "b", "c"], _TOKENS[20:28], 103)
_C4 = _build_case(["c"], _TOKENS[0:24], 104, low=-0.5, high=0.5)
_C5 = _build_case(["g"], _TOKENS[30:34], 105, low=0.0, high=1000.0)
_C6 = _build_case(["d", "e"], _TOKENS_FILTER_HEAVY, 106)
_C7 = _build_case(["a", "b", "i", "c"], _TOKENS[36:42], 107, low=-1.0, high=1.0)
_C8 = _build_case(["h"], _TOKENS[42:48], 108)


def checks():
    embs4 = torch.zeros(4, _EMB_DIM)
    tok4 = {i: t for i, t in enumerate(_TOKENS[:4])}
    embs0 = torch.zeros(0, _EMB_DIM)
    return [
        ("no-images", lambda: (_GEN, "revenue", embs4, tok4, [], [])),
        ("no-tokens", lambda: (_GEN, "revenue", embs0, {}, [_IMG["a"]], [{}])),
        ("missing-file",
         lambda: (_GEN, "revenue", embs4, tok4,
                  [WORKDIR / "does_not_exist.png"], [{}])),
    ]


def cases():
    return [
        ("single-320x420-10tok",
         lambda: (_GEN, "What is the total revenue for Q3 2023?", *_C1)),
        ("single-480x640-10tok",
         lambda: (_GEN, "How much did revenue grow compared to last year?", *_C2)),
        ("three-images-8tok",
         lambda: (_GEN, "What was the profit margin in Norwegian kroner?", *_C3)),
        ("many-tokens-260x340",
         lambda: (_GEN, "What is the total revenue for Q3 2023?", *_C4)),
        ("large-image-640x800-4tok",
         lambda: (_GEN, "Was the profit higher than expected by analysts?", *_C5)),
        ("filter-heavy-2img-18tok",
         lambda: (_GEN, "What is the total profit in 2023?", *_C6)),
        ("four-images-6tok",
         lambda: (_GEN, "What data did the company report today?", *_C7)),
        ("tall-image-300x900-6tok",
         lambda: (_GEN, "How much did the shares rise in Oslo?", *_C8)),
    ]
