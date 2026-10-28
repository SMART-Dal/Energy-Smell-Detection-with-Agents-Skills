```python
import random

import main
from main import full_image

# ---------------------------------------------------------------------------
# The function reads its module global IMG_DIR to locate the cached image.
# Point it at a writable directory under WORKDIR and create the files there,
# so that the cache-hit branch (read file + base64 encode) is the one taken.
# ---------------------------------------------------------------------------
IMG_DIR = WORKDIR / "full_images"
IMG_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_dir():
    """Force IMG_DIR on the function's real globals (covers wrappers too)."""
    main.IMG_DIR = IMG_DIR
    g = getattr(full_image, "__globals__", None)
    if g is not None:
        g["IMG_DIR"] = IMG_DIR
    w = getattr(full_image, "__wrapped__", None)
    if w is not None:
        gw = getattr(w, "__globals__", None)
        if gw is not None:
            gw["IMG_DIR"] = IMG_DIR


_ensure_dir()


def _make(doc_id, size, seed):
    rng = random.Random(seed)
    (IMG_DIR / f"{doc_id}.jpg").write_bytes(rng.randbytes(size))
    return doc_id


# Eight measured workloads: same code path (cache hit -> file read + base64
# encode + Img construction) but very different file sizes and byte content,
# so the amount of real work varies substantially.
_SPECS = [
    ("s20k", 20_000, 1),
    ("s100k", 100_000, 2),
    ("s300k", 300_000, 3),
    ("s700k", 700_000, 4),
    ("s1500k", 1_500_000, 5),
    ("s2500k", 2_500_000, 6),
    ("s4000k", 4_000_000, 7),
    ("s5000k", 5_000_000, 8),
]
_IDS = {name: _make(f"doc_{name}", size, seed) for name, size, seed in _SPECS}

# Small edge inputs for checks() only.
_CHECKS = [
    ("one-byte", _make("doc_onebyte", 1, 101)),
    ("empty-file", _make("doc_emptyfile", 0, 102)),
    ("unicode-id", _make("döc_ünicode", 10, 103)),
]


def _thunk(doc_id):
    # Re-assert the global in whatever process the timed call runs in; this
    # is setup only and is never timed.
    _ensure_dir()
    return (doc_id,)


def checks():
    return [
        ("one-byte", lambda: _thunk(_CHECKS[0][1])),
        ("empty-file", lambda: _thunk(_CHECKS[1][1])),
        ("unicode-id", lambda: _thunk(_CHECKS[2][1])),
    ]


def cases():
    return [(name, (lambda d=_IDS[name]: _thunk(d))) for name, _, _ in _SPECS]
```