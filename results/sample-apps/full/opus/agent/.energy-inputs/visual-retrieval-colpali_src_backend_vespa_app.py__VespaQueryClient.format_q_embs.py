# Inputs for visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import torch
from backend.vespa_app import VespaQueryClient

# The method only uses its `q_embs` argument; the client itself is never touched.
# Building a real client would connect to Vespa, so we create the bare instance.
_CLIENT = object.__new__(VespaQueryClient)

torch.manual_seed(0)

# Typical ColPali query embedding: ~32 tokens x 128 dims.
_TYPICAL = torch.randn(32, 128)
# Max query terms (MAX_QUERY_TERMS = 64) x 128 dims.
_MAX_TOKENS = torch.randn(64, 128)
# Many rows, narrower vectors: exercises the per-row Python loop hard.
_MANY_ROWS = torch.randn(900, 100)
# Few rows, very wide vectors: exercises the per-row tolist conversion hard.
_WIDE = torch.randn(90, 1000)
# Non-contiguous tensor (transposed view).
_NON_CONTIG = torch.randn(128, 64).t()
# Different dtypes.
_FLOAT64 = torch.randn(64, 128, dtype=torch.float64)
_FLOAT16 = torch.randn(256, 128, dtype=torch.float16)
# 3D tensor: each slice converts to a nested list.
_THREE_D = torch.randn(16, 4, 32)


def checks():
    return [
        ("empty-rows", lambda: (_CLIENT, torch.zeros(0, 128))),
        ("single-row", lambda: (_CLIENT, torch.randn(1, 4))),
        ("one-dimensional", lambda: (_CLIENT, torch.randn(5))),
    ]


def cases():
    return [
        ("typical-32x128", lambda: (_CLIENT, _TYPICAL)),
        ("max-tokens-64x128", lambda: (_CLIENT, _MAX_TOKENS)),
        ("many-rows-900x100", lambda: (_CLIENT, _MANY_ROWS)),
        ("wide-90x1000", lambda: (_CLIENT, _WIDE)),
        ("non-contiguous", lambda: (_CLIENT, _NON_CONTIG)),
        ("float64-64x128", lambda: (_CLIENT, _FLOAT64)),
        ("float16-256x128", lambda: (_CLIENT, _FLOAT16)),
        ("three-dimensional", lambda: (_CLIENT, _THREE_D)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-rows-900x100', 'wide-90x1000', 'float16-256x128', 'float64-64x128']
_KEEP_CHECKS = ['empty-rows', 'single-row', 'one-dimensional']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
