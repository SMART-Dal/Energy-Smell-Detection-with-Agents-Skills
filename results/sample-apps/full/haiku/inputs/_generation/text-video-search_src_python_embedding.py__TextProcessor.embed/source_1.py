import random

import torch  # noqa: F401  (needed by clip)
import clip
from clip.model import CLIP

from embedding import TextProcessor


# ---------------------------------------------------------------------------
# Setup (never timed): a real CLIP model instance, built locally with random
# weights so that no download / network access is required.  Only the text
# encoder is exercised by `embed`, but CLIP builds both towers.
# ---------------------------------------------------------------------------
def _build_model():
    model = CLIP(
        embed_dim=512,
        # vision tower (unused by embed, kept tiny)
        image_resolution=32,
        vision_layers=1,
        vision_width=64,
        vision_patch_size=32,
        # text tower (this is what embed actually runs)
        context_length=77,
        vocab_size=49408,
        transformer_width=256,
        transformer_heads=4,
        transformer_layers=12,
    )
    model.eval()
    return model


_MODEL = _build_model()

_PROCESSOR = TextProcessor.__new__(TextProcessor)
_PROCESSOR.model = _MODEL
_PROCESSOR.model_name = "ViT-B/32"


# ---------------------------------------------------------------------------
# Text building.  `clip.tokenize` raises when the text needs more than 77
# tokens, so every candidate is grown word by word and kept below that limit.
# ---------------------------------------------------------------------------
def _fit(text):
    out = ""
    for word in text.split():
        candidate = (out + " " + word).strip()
        try:
            clip.tokenize(candidate)
        except RuntimeError:
            break
        out = candidate
    return out


_RNG = random.Random(0)
_VOCAB = [
    "dog", "cat", "running", "park", "video", "clip", "search", "frame",
    "sunset", "beach", "city", "night", "car", "tree", "mountain", "river",
    "person", "walking", "sky", "blue", "red", "green", "fast", "slow",
    "train", "bird", "water", "street", "house", "music", "dance", "food",
]

_TEXT_SHORT = "a dog running in the park"
_TEXT_MEDIUM = _fit(
    "a group of people walking along a busy city street at night with bright "
    "neon signs and a yellow taxi passing by in the rain"
)
_TEXT_LONG = _fit(" ".join(_RNG.choice(_VOCAB) for _ in range(400)))
_TEXT_RANDOM = _fit(" ".join(_RNG.choice(_VOCAB) for _ in range(400)))
_TEXT_UNICODE = _fit(
    "café au lait à Paris señor naïve résumé 日本語のテキスト emoji 🐶 🎬 naïve"
)
_TEXT_PUNCT = _fit(
    "Wait ... what ?! Really ?? Yes -- no ; maybe : 'quotes' (parens) "
    "[brackets] {braces} #hash @at &amp; 100 % + - = / |"
)
_TEXT_SINGLE = "cat"
_TEXT_NUMBERS = _fit("video 2023 12 31 99.5 % $100 #42 3.14e10 0x1F 1,000,000")


def checks():
    return [
        ("empty-string", lambda: (_PROCESSOR, "")),
        ("single-char", lambda: (_PROCESSOR, "a")),
        ("none-text", lambda: (_PROCESSOR, None)),
    ]


def cases():
    return [
        ("short-query", lambda: (_PROCESSOR, _TEXT_SHORT)),
        ("medium-sentence", lambda: (_PROCESSOR, _TEXT_MEDIUM)),
        ("long-caption", lambda: (_PROCESSOR, _TEXT_LONG)),
        ("random-words", lambda: (_PROCESSOR, _TEXT_RANDOM)),
        ("unicode", lambda: (_PROCESSOR, _TEXT_UNICODE)),
        ("punctuation", lambda: (_PROCESSOR, _TEXT_PUNCT)),
        ("single-word", lambda: (_PROCESSOR, _TEXT_SINGLE)),
        ("numbers-symbols", lambda: (_PROCESSOR, _TEXT_NUMBERS)),
    ]
