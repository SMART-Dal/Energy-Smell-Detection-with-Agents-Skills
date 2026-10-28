# Inputs for src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

import pandas as pd

import dxpy.cli.dataset_utilities as _du
from dxpy.cli.dataset_utilities import DXDatasetDictionary, CODING_PAGINATED_KEY

# The method reads the module-global `pd`; the repository's module must have it.
_du.pd = pd

# A real (uninitialised) DXDatasetDictionary instance.  create_coding_name_dframe
# never touches `self`, and building a fully initialised one would need a live
# descriptor / network access, so we allocate the instance directly.
_INSTANCE = DXDatasetDictionary.__new__(DXDatasetDictionary)


def _make_hierarchy(rng, n_codes, max_depth=6, max_children=10):
    """Build a (display, codes) pair for a hierarchical coding.

    `display` is the nested list the descriptor/codings API produces: terminal
    nodes are code strings, internal nodes are {code: [children]}.
    """
    codes = ["code_%d" % i for i in range(n_codes)]
    rng.shuffle(codes)
    idx = [0]

    def build(n, depth):
        nodes = []
        while n > 0:
            if n == 1 or depth >= max_depth or rng.random() < 0.35:
                nodes.append(codes[idx[0]])
                idx[0] += 1
                n -= 1
            else:
                c = codes[idx[0]]
                idx[0] += 1
                child_n = rng.randint(1, min(max_children, n - 1))
                children = build(child_n, depth + 1)
                nodes.append({c: children})
                n -= 1 + child_n
        return nodes

    return build(n_codes, 0), codes


def _meanings(codes, tag):
    return {c: "%s meaning for %s" % (tag, c) for c in codes}


def _concepts(codes, rng, ratio, tag="concept"):
    return {c: "%s_%d" % (tag, i) for i, c in enumerate(codes) if rng.random() < ratio}


_rng = random.Random(0)

# ---------------------------------------------------------------------------
# 1. large hierarchical coding, half the codes have a concept
# ---------------------------------------------------------------------------
_disp1, _codes1 = _make_hierarchy(_rng, 15000, max_depth=6, max_children=10)
_coding1 = {
    "display": _disp1,
    "codes_to_meanings": _meanings(_codes1, "h1"),
    "codes_to_concepts": _concepts(_codes1, _rng, 0.5, "c1"),
}

# ---------------------------------------------------------------------------
# 2. wide hierarchy (few levels, many children per node)
# ---------------------------------------------------------------------------
_disp2, _codes2 = _make_hierarchy(_rng, 15000, max_depth=3, max_children=40)
_coding2 = {
    "display": _disp2,
    "codes_to_meanings": _meanings(_codes2, "h2"),
    "codes_to_concepts": _concepts(_codes2, _rng, 0.8, "c2"),
}

# ---------------------------------------------------------------------------
# 3. deep hierarchy (many levels, few children per node)
# ---------------------------------------------------------------------------
_disp3, _codes3 = _make_hierarchy(_rng, 8000, max_depth=12, max_children=3)
_coding3 = {
    "display": _disp3,
    "codes_to_meanings": _meanings(_codes3, "h3"),
    "codes_to_concepts": _concepts(_codes3, _rng, 0.2, "c3"),
}

# ---------------------------------------------------------------------------
# 4. hierarchical coding split across pages -> display_order must be dropped
# ---------------------------------------------------------------------------
_disp4, _codes4 = _make_hierarchy(_rng, 12000, max_depth=5, max_children=12)
_coding4 = {
    "display": _disp4,
    "codes_to_meanings": _meanings(_codes4, "h4"),
    "codes_to_concepts": _concepts(_codes4, _rng, 0.5, "c4"),
    CODING_PAGINATED_KEY: True,
}

# ---------------------------------------------------------------------------
# 5. hierarchical coding with no concepts at all
# ---------------------------------------------------------------------------
_disp5, _codes5 = _make_hierarchy(_rng, 12000, max_depth=7, max_children=8)
_coding5 = {
    "display": _disp5,
    "codes_to_meanings": _meanings(_codes5, "h5"),
    "codes_to_concepts": {},
}

# ---------------------------------------------------------------------------
# 6. large flat coding with no display list
# ---------------------------------------------------------------------------
_codes6 = ["fcode_%d" % i for i in range(15000)]
_coding6 = {"codes_to_meanings": _meanings(_codes6, "f6")}

# ---------------------------------------------------------------------------
# 7. flat coding with a display list: hits and misses in the display order
# ---------------------------------------------------------------------------
_codes7 = ["dcode_%d" % i for i in range(1000)]
_display7 = list(_codes7)
_rng.shuffle(_display7)
_display7 = _display7[:900]  # 100 codes are absent from display -> None
_coding7 = {
    "codes_to_meanings": _meanings(_codes7, "f7"),
    "display": _display7,
    "codes_to_concepts": _concepts(_codes7, _rng, 0.5, "c7"),
}

# ---------------------------------------------------------------------------
# 8. large flat coding split across pages -> no display, display_order dropped
# ---------------------------------------------------------------------------
_codes8 = ["pcode_%d" % i for i in range(15000)]
_coding8 = {
    "codes_to_meanings": _meanings(_codes8, "f8"),
    CODING_PAGINATED_KEY: True,
}


def checks():
    return [
        ("empty-flat",
         lambda: (_INSTANCE, {"codes_to_meanings": {}}, "empty", False)),
        ("empty-hier",
         lambda: (_INSTANCE, {"display": [], "codes_to_meanings": {}}, "empty_h", True)),
        ("single-flat",
         lambda: (_INSTANCE, {"codes_to_meanings": {"a": "A"}}, "one", False)),
    ]


def cases():
    return [
        ("hier-large",       lambda: (_INSTANCE, _coding1, "coding_one", True)),
        ("hier-wide",        lambda: (_INSTANCE, _coding2, "coding_two", True)),
        ("hier-deep",        lambda: (_INSTANCE, _coding3, "coding_three", True)),
        ("hier-paginated",   lambda: (_INSTANCE, _coding4, "coding_four", True)),
        ("hier-no-concepts", lambda: (_INSTANCE, _coding5, "coding_five", True)),
        ("flat-large",       lambda: (_INSTANCE, _coding6, "coding_six", False)),
        ("flat-with-display", lambda: (_INSTANCE, _coding7, "coding_seven", False)),
        ("flat-paginated",   lambda: (_INSTANCE, _coding8, "coding_eight", False)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['hier-large', 'hier-wide', 'hier-no-concepts', 'hier-paginated']
_KEEP_CHECKS = ['empty-flat', 'empty-hier', 'single-flat']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
