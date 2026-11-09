import importlib
import random

_mod = importlib.import_module('move-to-emeritus')
_check_events = _mod._check_events

# Populate the module's event cache so _get_repo_events never touches the network.
_mod._repo_events_cache = {}

_ALL_TYPES = ["labeled", "unlabeled", "closed", "merged", "referenced", "mentioned", "assigned"]
_TRIAGE_TYPES = ["labeled", "unlabeled", "closed"]


def _actor_pool(n):
    return [f"user{i}" for i in range(n)]


def _gen(n, actors, types, seed, issue_lo=1, issue_hi=5000):
    rng = random.Random(seed)
    na = len(actors)
    nt = len(types)
    out = []
    for _ in range(n):
        out.append((actors[rng.randrange(na)],
                    types[rng.randrange(nt)],
                    rng.randrange(issue_lo, issue_hi)))
    return out


_A5000 = _actor_pool(5000)
_A20000 = _actor_pool(20000)
_A100 = _actor_pool(100)
_A30000 = _actor_pool(30000)

# 1. big mixed workload, moderate remaining set
_ev1 = _gen(100000, _A5000, _ALL_TYPES, 1)
_rem1 = set(_A5000[:2000])
_mod._repo_events_cache["repo_big_mixed"] = _ev1

# 2. mostly misses: very few remaining actors among a large event stream
_ev2 = _gen(100000, _A20000, _ALL_TYPES, 2)
_rem2 = set(_A20000[:50])
_mod._repo_events_cache["repo_mostly_miss"] = _ev2

# 3. exclude_pr present in ~30% of events
_rng3 = random.Random(3)
_ev3 = []
for _ in range(100000):
    _ev3.append((_A5000[_rng3.randrange(5000)],
                 _TRIAGE_TYPES[_rng3.randrange(3)],
                 999 if _rng3.random() < 0.3 else _rng3.randrange(1, 30000)))
_rem3 = set(_A5000[:1000])
_mod._repo_events_cache["repo_exclude"] = _ev3

# 4. heavy duplicates: few actors, many events, all actors remaining
_ev4 = _gen(100000, _A100, _ALL_TYPES, 4)
_rem4 = set(_A100)
_mod._repo_events_cache["repo_duplicates"] = _ev4

# 5. single matching event type among a mixed stream
_ev5 = _gen(100000, _A5000, _ALL_TYPES, 5)
_rem5 = set(_A5000[:3000])
_mod._repo_events_cache["repo_single_type"] = _ev5

# 6. huge remaining set: nearly every actor matches
_ev6 = _gen(100000, _A30000, _ALL_TYPES, 6)
_rem6 = set(_A30000[:28000])
_mod._repo_events_cache["repo_huge_remaining"] = _ev6

# 7. all actors remaining, small pool, triage types only
_ev7 = _gen(100000, _A100, _TRIAGE_TYPES, 7)
_rem7 = set(_A100)
_mod._repo_events_cache["repo_all_remaining"] = _ev7

# 8. exclude_pr filters essentially every event (pure scan, no appends)
_ev8 = _gen(100000, _A5000, _TRIAGE_TYPES, 8, 1, 100)
_ev8 = [(a, t, 777) for (a, t, _) in _ev8]
_rem8 = set(_A5000[:2000])
_mod._repo_events_cache["repo_exclude_all"] = _ev8

# Small caches for the edge-case checks
_mod._repo_events_cache["chk_empty"] = []
_mod._repo_events_cache["chk_one"] = [("alice", "labeled", 1)]
_mod._repo_events_cache["chk_odd"] = [("", None, None), ("bob", "closed", 2)]


def checks():
    return [
        ("empty-events", lambda: (set(), "chk_empty", "2020-01-01", {"labeled"}, None)),
        ("single-match", lambda: ({"alice"}, "chk_one", "2020-01-01", {"labeled"}, None)),
        ("odd-values", lambda: ({"bob"}, "chk_odd", "2020-01-01", {"closed"}, None)),
    ]


def cases():
    return [
        ("big-mixed",
         lambda: (_rem1, "repo_big_mixed", "2020-01-01", {"labeled", "unlabeled", "closed"}, None)),
        ("mostly-misses",
         lambda: (_rem2, "repo_mostly_miss", "2020-01-01", {"labeled", "unlabeled", "closed"}, None)),
        ("exclude-pr",
         lambda: (_rem3, "repo_exclude", "2020-01-01", {"labeled", "unlabeled", "closed"}, 999)),
        ("duplicates",
         lambda: (_rem4, "repo_duplicates", "2020-01-01", set(_ALL_TYPES), None)),
        ("single-type",
         lambda: (_rem5, "repo_single_type", "2020-01-01", {"merged"}, None)),
        ("huge-remaining",
         lambda: (_rem6, "repo_huge_remaining", "2020-01-01", set(_ALL_TYPES), None)),
        ("all-remaining",
         lambda: (_rem7, "repo_all_remaining", "2020-01-01", {"labeled", "unlabeled", "closed"}, None)),
        ("exclude-all",
         lambda: (_rem8, "repo_exclude_all", "2020-01-01", {"labeled", "unlabeled", "closed"}, 777)),
    ]
