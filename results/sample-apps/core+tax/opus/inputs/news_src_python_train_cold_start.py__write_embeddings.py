# Inputs for news/src/python/train_cold_start.py::write_embeddings, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

import numpy as np

import train_cold_start
from train_cold_start import write_embeddings

# write_embeddings opens os.path.join(data_dir, file_name); point data_dir at WORKDIR
# so every file the function writes lands under WORKDIR.
train_cold_start.data_dir = str(WORKDIR)


def _make_map(num_entries, seed, prefix="n", width=0):
    """id -> index map, ids shuffled (not sorted) as they are in the real data."""
    rng = random.Random(seed)
    ids = [f"{prefix}{i:0{width}d}" for i in range(num_entries)]
    rng.shuffle(ids)
    return {ids[i]: i for i in range(num_entries)}


def _make_embeddings(num_entries, dim, seed, scale=1.0):
    rng = random.Random(seed)
    return np.array(
        [[rng.uniform(-scale, scale) for _ in range(dim)] for _ in range(num_entries)],
        dtype=np.float64,
    )


def _build(num_entries, dim, seed, prefix="n", width=0, scale=1.0):
    m = _make_map(num_entries, seed, prefix, width)
    e = _make_embeddings(num_entries, dim, seed + 9999, scale)
    return m, e


# Built once, at module level; thunks just hand the same objects back.
_D = {
    "tiny": _build(100, 50, 1),
    "small": _build(500, 50, 2),
    "medium": _build(1000, 50, 3),
    "large": _build(2000, 50, 4),
    "wide": _build(500, 200, 5),
    "narrow": _build(5000, 20, 6),
    "many": _build(10000, 10, 7),
    "longids": _build(1000, 50, 8, prefix="news_article_id_", width=8),
}


def _thunk(key, fname):
    p = WORKDIR / fname
    if p.exists():
        p.unlink()
    m, e = _D[key]
    return (m, e, fname)


def checks():
    return [
        ("empty-map", lambda: ({}, np.zeros((0, 50)), "check_empty.tsv")),
        ("single-entry", lambda: ({"u0": 0}, np.array([[0.5, -1.25, 3.0]]), "check_single.tsv")),
        ("none-map", lambda: (None, np.zeros((1, 3)), "check_none.tsv")),
    ]


def cases():
    return [
        ("tiny", lambda: _thunk("tiny", "tiny.tsv")),
        ("small", lambda: _thunk("small", "small.tsv")),
        ("medium", lambda: _thunk("medium", "medium.tsv")),
        ("large", lambda: _thunk("large", "large.tsv")),
        ("wide", lambda: _thunk("wide", "wide.tsv")),
        ("narrow", lambda: _thunk("narrow", "narrow.tsv")),
        ("many", lambda: _thunk("many", "many.tsv")),
        ("longids", lambda: _thunk("longids", "longids.tsv")),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many', 'narrow', 'large', 'wide']
_KEEP_CHECKS = ['empty-map', 'single-entry', 'none-map']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
