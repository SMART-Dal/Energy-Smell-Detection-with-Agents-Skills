# Inputs for visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import logging
import random

import numpy as np

from backend.vespa_app import VespaQueryClient

# ---------------------------------------------------------------------------
# Build a VespaQueryClient instance without running __init__ (which would open
# a network connection to Vespa).  We only need `logger`; MAX_QUERY_TERMS is a
# class attribute.  Setting fields on the object is just building an input.
# ---------------------------------------------------------------------------
_logger = logging.getLogger("vespa_query_client_perf")
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_CLIENT = object.__new__(VespaQueryClient)
_CLIENT.logger = _logger


# ---------------------------------------------------------------------------
# Input builders.  `float_query_embedding` maps a term index to a float vector
# (ColPali query embeddings are 128-dim; we also use wider vectors to stress
# the numpy path).
# ---------------------------------------------------------------------------
def _vector(dim, seed, kind="mixed"):
    rng = random.Random(seed)
    if kind == "positive":
        return [rng.uniform(0.001, 1.0) for _ in range(dim)]
    if kind == "negative":
        return [rng.uniform(-1.0, -0.001) for _ in range(dim)]
    if kind == "zeros":
        return [
            0.0 if rng.random() < 0.3 else rng.uniform(-1.0, 1.0)
            for _ in range(dim)
        ]
    return [rng.uniform(-1.0, 1.0) for _ in range(dim)]


def _embedding(n_terms, dim, seed, kind="mixed"):
    rng = random.Random(seed)
    return {
        i: _vector(dim, rng.randrange(10**9), kind) for i in range(n_terms)
    }


# Built once at module level; the function only reads these dicts.
_E1 = _embedding(1, 128, 0, "mixed")          # single term, realistic dim
_E2 = _embedding(8, 128, 1, "mixed")          # small query
_E3 = _embedding(64, 128, 2, "mixed")         # exactly MAX_QUERY_TERMS
_E4 = _embedding(100, 128, 3, "mixed")        # truncation path + warning
_E5 = _embedding(64, 1024, 4, "positive")     # all positive -> all ones
_E6 = _embedding(64, 1024, 5, "negative")     # all negative -> all zeros
_E7 = _embedding(64, 2048, 6, "zeros")        # many exact zeros
_E8 = _embedding(64, 8192, 7, "mixed")        # wide vectors, heavy numpy work


def checks():
    return [
        ("empty-dict", lambda: (_CLIENT, {})),
        ("empty-vector", lambda: (_CLIENT, {0: []})),
        ("none-vector", lambda: (_CLIENT, {0: None})),
    ]


def cases():
    return [
        ("single-term-128", lambda: (_CLIENT, _E1)),
        ("eight-terms-128", lambda: (_CLIENT, _E2)),
        ("full-64-terms-128", lambda: (_CLIENT, _E3)),
        ("truncate-100-terms", lambda: (_CLIENT, _E4)),
        ("all-positive-1024", lambda: (_CLIENT, _E5)),
        ("all-negative-1024", lambda: (_CLIENT, _E6)),
        ("zeros-mixed-2048", lambda: (_CLIENT, _E7)),
        ("wide-8192", lambda: (_CLIENT, _E8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['wide-8192', 'zeros-mixed-2048', 'all-negative-1024', 'all-positive-1024']
_KEEP_CHECKS = ['empty-dict', 'empty-vector', 'none-vector']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
