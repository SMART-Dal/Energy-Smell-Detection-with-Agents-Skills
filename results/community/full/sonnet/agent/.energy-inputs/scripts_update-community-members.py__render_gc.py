# Inputs for scripts/update-community-members.py::render_gc, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import importlib
import random

_mod = importlib.import_module('update-community-members')
render_gc = _mod.render_gc


def _make_people(usernames, seed, present=1.0, name_ratio=0.9, company_ratio=0.7,
                 term_ratio=0.7, empty_name_ratio=0.0):
    """Build a `people` mapping for the given usernames."""
    rng = random.Random(seed)
    people = {}
    for i, u in enumerate(usernames):
        if rng.random() > present:
            continue
        entry = {}
        if rng.random() < name_ratio:
            if rng.random() < empty_name_ratio:
                entry["name"] = ""
            else:
                entry["name"] = f"Name {i}"
        if rng.random() < company_ratio:
            entry["company"] = f"Company {i % 37}"
        if rng.random() < term_ratio:
            entry["termEnd"] = (
                f"20{rng.randint(20, 30)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
            )
        people[u] = entry
    return people


# --- case 1: 40k members, everyone known with a full profile -----------------
_u1 = [f"user{i}" for i in range(40_000)]
_p1 = _make_people(_u1, 0, present=1.0)

# --- case 2: 35k members, only ~30% known (many fall back to the username) ---
_u2 = [f"member{i}" for i in range(35_000)]
_p2 = _make_people(_u2, 1, present=0.3, name_ratio=0.5, company_ratio=0.3, term_ratio=0.3)

# --- case 3: 80k entries drawn from a pool of 4k usernames -> heavy duplicates
_pool3 = [f"dup{i}" for i in range(4_000)]
_p3 = _make_people(_pool3, 2, present=1.0)
_rng3 = random.Random(3)
_u3 = [_pool3[_rng3.randrange(len(_pool3))] for _ in range(80_000)]

# --- case 4: 30k unicode usernames, some people with an empty name -----------
_u4 = [f"\u7528\u6237{i}" for i in range(30_000)]
_p4 = _make_people(_u4, 4, present=0.6, name_ratio=0.9, empty_name_ratio=0.1)

# --- case 5: 40k members, mixed presence, plus 10k unrelated people entries --
_u5 = [f"dev{i}" for i in range(40_000)]
_p5 = _make_people(_u5, 5, present=0.7, name_ratio=0.95, company_ratio=0.5, term_ratio=0.9)
for j in range(10_000):
    _p5[f"extra{j}"] = {"name": f"Extra {j}", "company": "X", "termEnd": "2030-01-01"}

# --- case 6: 40k members, nobody known -> display_name falls back to username
_u6 = [f"ghost{i}" for i in range(40_000)]
_p6 = {}

# --- case 7: 25k members, usernames already sorted ---------------------------
_u7 = [f"a{i:06d}" for i in range(25_000)]
_p7 = _make_people(_u7, 7, present=0.8)

# --- case 8: 35k members with very long display names ------------------------
_u8 = [f"long{i}" for i in range(35_000)]
_p8 = {}
for i, u in enumerate(_u8):
    _p8[u] = {"name": "N" * 100 + f" {i:06d}", "company": "C" * 40, "termEnd": "2030-01-01"}


def _run(team, people):
    """Thunk that installs the module globals render_gc reads, then calls it."""
    def thunk():
        _mod.teams = team
        _mod.people = people
        return ()
    return thunk


def checks():
    return [
        ("empty-team", _run({"governance-committee": []}, {})),
        ("no-key", _run({}, {})),
        ("unknown-member", _run({"governance-committee": ["nobody"]}, {})),
    ]


def cases():
    return [
        ("full-40k", _run({"governance-committee": _u1}, _p1)),
        ("sparse-35k", _run({"governance-committee": _u2}, _p2)),
        ("duplicates-80k", _run({"governance-committee": _u3}, _p3)),
        ("unicode-30k", _run({"governance-committee": _u4}, _p4)),
        ("mixed-40k", _run({"governance-committee": _u5}, _p5)),
        ("ghosts-40k", _run({"governance-committee": _u6}, _p6)),
        ("sorted-25k", _run({"governance-committee": _u7}, _p7)),
        ("longnames-35k", _run({"governance-committee": _u8}, _p8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['duplicates-80k', 'full-40k', 'mixed-40k', 'sparse-35k']
_KEEP_CHECKS = ['empty-team', 'no-key', 'unknown-member']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
