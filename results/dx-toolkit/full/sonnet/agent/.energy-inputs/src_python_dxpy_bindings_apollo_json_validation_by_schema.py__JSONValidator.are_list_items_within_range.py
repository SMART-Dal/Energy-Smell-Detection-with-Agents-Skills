# Inputs for src/python/dxpy/bindings/apollo/json_validation_by_schema.py::JSONValidator.are_list_items_within_range, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from dxpy.bindings.apollo.json_validation_by_schema import JSONValidator

_SCHEMA = {"location": {"type": "list"}}


def _noop(msg):
    pass


# A single stateless validator is reused for every call; the method never
# mutates it and the error handler keeps no state.
_VALIDATOR = JSONValidator(_SCHEMA, error_handler=_noop)

_KEY = "location"
_START = "starting_position"
_END = "ending_position"


def _make_items(n, seed, start_lo, start_hi, width_lo, width_hi, as_str=False):
    rng = random.Random(seed)
    items = []
    for _ in range(n):
        s = rng.randint(start_lo, start_hi)
        w = rng.randint(width_lo, width_hi)
        e = s + w
        if as_str:
            items.append({_START: str(s), _END: str(e)})
        else:
            items.append({_START: s, _END: e})
    return items


def _make_reversed(n, seed):
    rng = random.Random(seed)
    items = []
    for _ in range(n):
        s = rng.randint(0, 100_000_000)
        if rng.random() < 0.5:
            e = s - rng.randint(1, 1000)  # end <= start -> per-item error
        else:
            e = s + rng.randint(1, 1000)
        items.append({_START: s, _END: e})
    return items


# ---------------------------------------------------------------------------
# Module level workloads (built once, shared by every repeated call).
# ---------------------------------------------------------------------------

# 1. modest, well-behaved int ranges, global check only
_DATA_1 = {"location": _make_items(40_000, 1, 0, 1_000_000, 1, 1000)}

# 2. large, well-behaved int ranges, global check only
_DATA_2 = {"location": _make_items(100_000, 2, 0, 1_000_000, 1, 1000)}

# 3. per-item check, all widths comfortably inside the window
_DATA_3 = {"location": _make_items(80_000, 3, 0, 1_000_000, 1, 1000)}

# 4. per-item check, every width exceeds the window -> error path each item
_DATA_4 = {"location": _make_items(80_000, 4, 0, 1_000_000, 250_000_001, 500_000_000)}

# 5. numeric values given as strings (int() conversion path)
_DATA_5 = {"location": _make_items(80_000, 5, 0, 1_000_000, 1, 1000, as_str=True)}

# 6. global check violated: starts spread over ~1e9 > 250e6 window
_DATA_6 = {"location": _make_items(100_000, 6, 0, 1_000_000_000, 1, 1000)}

# 7. many reversed ranges (end <= start) -> per-item error path
_DATA_7 = {"location": _make_reversed(60_000, 7)}

# 8. tiny window, global check violated
_DATA_8 = {"location": _make_items(40_000, 8, 0, 100_000, 1, 5000)}


def checks():
    return [
        ("empty-list",
         lambda: (_VALIDATOR, {"location": []}, _KEY, _START, _END)),
        ("single-item",
         lambda: (_VALIDATOR,
                  {"location": [{_START: 5, _END: 10}]},
                  _KEY, _START, _END)),
        ("none-values",
         lambda: (_VALIDATOR,
                  {"location": [{_START: None, _END: None}]},
                  _KEY, _START, _END)),
    ]


def cases():
    return [
        ("typical-40k",
         lambda: (_VALIDATOR, _DATA_1, _KEY, _START, _END, 250000000, False)),
        ("large-100k",
         lambda: (_VALIDATOR, _DATA_2, _KEY, _START, _END, 250000000, False)),
        ("each-separately-80k",
         lambda: (_VALIDATOR, _DATA_3, _KEY, _START, _END, 250000000, True)),
        ("each-separately-over-window",
         lambda: (_VALIDATOR, _DATA_4, _KEY, _START, _END, 250000000, True)),
        ("string-values-80k",
         lambda: (_VALIDATOR, _DATA_5, _KEY, _START, _END, 250000000, False)),
        ("global-window-violation",
         lambda: (_VALIDATOR, _DATA_6, _KEY, _START, _END, 250000000, False)),
        ("reversed-ranges-60k",
         lambda: (_VALIDATOR, _DATA_7, _KEY, _START, _END, 250000000, False)),
        ("tiny-window-40k",
         lambda: (_VALIDATOR, _DATA_8, _KEY, _START, _END, 1000, False)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['each-separately-over-window', 'string-values-80k', 'global-window-violation', 'large-100k']
_KEEP_CHECKS = ['empty-list', 'single-item', 'none-values']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
