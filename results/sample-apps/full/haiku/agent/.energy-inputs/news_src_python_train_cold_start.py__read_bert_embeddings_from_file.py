# Inputs for news/src/python/train_cold_start.py::read_bert_embeddings_from_file, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
import numpy as np
from train_cold_start import read_bert_embeddings_from_file


class _DataLoader:
    """Minimal stand-in for MindData providing the .news() mapping used by the function."""
    def __init__(self, news_map):
        self._news = news_map

    def news(self):
        return self._news


_rng = random.Random(0)
_FLOAT_POOL = [repr(_rng.uniform(-1, 1)) for _ in range(10000)]
_SCI_POOL = [f"{_rng.uniform(-1, 1):.6e}" for _ in range(10000)]
_INT_POOL = [str(_rng.randint(-100, 100)) for _ in range(10000)]


def _write_file(path, news_ids, pool, seed):
    rng = random.Random(seed)
    with open(path, "w", encoding="utf-8") as f:
        for nid in news_ids:
            start = rng.randrange(len(pool))
            vals = ",".join(pool[(start + i) % len(pool)] for i in range(512))
            f.write(f"{nid}\t{vals}\n")


# Base file: 1500 unique news ids, standard float strings
_BASE_IDS = [f"N{i}" for i in range(1500)]
_BASE_FILE = WORKDIR / "base_embeddings.txt"
_write_file(_BASE_FILE, _BASE_IDS, _FLOAT_POOL, 1)

# Duplicates file: 1500 lines, 100 unique news ids (many overwrites)
_dup_rng = random.Random(2)
_DUP_IDS = [f"N{_dup_rng.randrange(100)}" for _ in range(1500)]
_DUP_FILE = WORKDIR / "dup_embeddings.txt"
_write_file(_DUP_FILE, _DUP_IDS, _FLOAT_POOL, 3)

# Scientific notation file: 1000 unique news ids
_SCI_IDS = [f"N{i}" for i in range(1000)]
_SCI_FILE = WORKDIR / "sci_embeddings.txt"
_write_file(_SCI_FILE, _SCI_IDS, _SCI_POOL, 4)

# Integer values file: 1000 unique news ids
_INT_IDS = [f"N{i}" for i in range(1000)]
_INT_FILE = WORKDIR / "int_embeddings.txt"
_write_file(_INT_FILE, _INT_IDS, _INT_POOL, 5)

# Check files
_EMPTY_FILE = WORKDIR / "empty_embeddings.txt"
_EMPTY_FILE.write_text("")

_WRONG_LEN_FILE = WORKDIR / "wrong_len_embeddings.txt"
_WRONG_LEN_FILE.write_text("N0\t0.1,0.2,0.3\n")

_MISSING_FILE = WORKDIR / "missing_embeddings.txt"  # deliberately not created


def _news_map(n, start=0):
    return {f"N{i}": i for i in range(start, start + n)}


_DL_ALL = _DataLoader(_news_map(1500))
_DL_HALF = _DataLoader(_news_map(750))
_DL_TEN = _DataLoader(_news_map(150))
_DL_ONE = _DataLoader(_news_map(15))
_DL_NONE = _DataLoader(_news_map(1000, start=5000))
_DL_DUP = _DataLoader(_news_map(100))
_DL_SCI = _DataLoader(_news_map(1000))
_DL_INT = _DataLoader(_news_map(1000))

_EMB_ALL = np.zeros([1500, 512])
_EMB_HALF = np.zeros([750, 512])
_EMB_TEN = np.zeros([150, 512])
_EMB_ONE = np.zeros([15, 512])
_EMB_NONE = np.zeros([1000, 512])
_EMB_DUP = np.zeros([100, 512])
_EMB_SCI = np.zeros([1000, 512])
_EMB_INT = np.zeros([1000, 512])


def checks():
    return [
        ("empty-file", lambda: (_DL_ALL, str(_EMPTY_FILE), np.zeros([1500, 512]))),
        ("missing-file", lambda: (_DL_ALL, str(_MISSING_FILE), np.zeros([1500, 512]))),
        ("wrong-length", lambda: (_DL_ALL, str(_WRONG_LEN_FILE), np.zeros([1500, 512]))),
    ]


def cases():
    return [
        ("all-match", lambda: (_DL_ALL, str(_BASE_FILE), _EMB_ALL.copy())),
        ("half-match", lambda: (_DL_HALF, str(_BASE_FILE), _EMB_HALF.copy())),
        ("ten-percent-match", lambda: (_DL_TEN, str(_BASE_FILE), _EMB_TEN.copy())),
        ("one-percent-match", lambda: (_DL_ONE, str(_BASE_FILE), _EMB_ONE.copy())),
        ("no-match", lambda: (_DL_NONE, str(_BASE_FILE), _EMB_NONE.copy())),
        ("duplicates", lambda: (_DL_DUP, str(_DUP_FILE), _EMB_DUP.copy())),
        ("scientific-notation", lambda: (_DL_SCI, str(_SCI_FILE), _EMB_SCI.copy())),
        ("integer-values", lambda: (_DL_INT, str(_INT_FILE), _EMB_INT.copy())),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['duplicates', 'all-match', 'half-match', 'scientific-notation']
_KEEP_CHECKS = ['empty-file', 'missing-file', 'wrong-length']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
