import random

import numpy
import torch

import train_mf
from train_mf import write_embeddings

# The function reads the module-level `data_dir` global; point it at WORKDIR.
train_mf.data_dir = str(WORKDIR)


def _ids(n, seed, prefix, as_int=False):
    rng = random.Random(seed)
    if as_int:
        return rng.sample(range(10 ** 9), n)
    seen = set()
    out = []
    while len(out) < n:
        s = "%s%d" % (prefix, rng.randrange(10 ** 9))
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _build(n, dim, seed, prefix="N", as_int=False, n_rows=None, index_map=None):
    torch.manual_seed(seed)
    rows = n_rows if n_rows is not None else n
    emb = torch.randn(rows, dim)
    ids = _ids(n, seed + 1000, prefix, as_int)
    if index_map is None:
        index_map = list(range(n))
    d = {ids[i]: index_map[i] for i in range(n)}
    return d, emb


# --- module-level data (built once, reused by every thunk call) ---

# typical news / user maps from the repo's save_embeddings call
_NEWS_MAP, _NEWS_EMB = _build(2000, 32, 1, "N")
_USERS_MAP, _USERS_EMB = _build(3000, 16, 2, "U")

# very low embedding dimension
_SMALL_MAP, _SMALL_EMB = _build(4000, 8, 3, "S")

# high embedding dimension, fewer rows
_LARGE_MAP, _LARGE_EMB = _build(400, 200, 4, "L")

# integer ids
_INT_MAP, _INT_EMB = _build(2000, 32, 5, as_int=True)

# index values shuffled (non monotone order)
_shuf_idx = list(range(2000))
random.Random(6).shuffle(_shuf_idx)
_SHUF_MAP, _SHUF_EMB = _build(2000, 32, 7, "H", index_map=_shuf_idx)

# sparse: many embedding rows, only a subset of indices referenced
_sparse_rng = random.Random(8)
_sparse_idx = _sparse_rng.sample(range(8000), 1500)
_SPARSE_MAP, _SPARSE_EMB = _build(1500, 64, 9, "P", n_rows=8000, index_map=_sparse_idx)

# many ids collapsing onto few embedding rows (duplicate indices)
_dup_rng = random.Random(10)
_dup_idx = [_dup_rng.randrange(400) for _ in range(3000)]
_DUP_MAP, _DUP_EMB = _build(3000, 32, 11, "D", n_rows=400, index_map=_dup_idx)


def checks():
    return [
        ("empty", lambda: ({}, torch.zeros(0, 4), "check_empty.tsv")),
        ("single", lambda: ({"N1": 0}, torch.zeros(1, 3), "check_single.tsv")),
        ("numpy-array", lambda: ({"a": 0, "b": 1}, numpy.zeros((2, 3)), "check_numpy.tsv")),
    ]


def cases():
    return [
        ("news-typical", lambda: (_NEWS_MAP, _NEWS_EMB, "news_embeddings.tsv")),
        ("users-large", lambda: (_USERS_MAP, _USERS_EMB, "user_embeddings.tsv")),
        ("small-dim", lambda: (_SMALL_MAP, _SMALL_EMB, "small_dim.tsv")),
        ("large-dim", lambda: (_LARGE_MAP, _LARGE_EMB, "large_dim.tsv")),
        ("int-ids", lambda: (_INT_MAP, _INT_EMB, "int_ids.tsv")),
        ("shuffled-indices", lambda: (_SHUF_MAP, _SHUF_EMB, "shuffled.tsv")),
        ("sparse-indices", lambda: (_SPARSE_MAP, _SPARSE_EMB, "sparse.tsv")),
        ("duplicate-indices", lambda: (_DUP_MAP, _DUP_EMB, "duplicates.tsv")),
    ]
