# Inputs for text-search/python/sample-queries-and-documents.py::select_documents, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import importlib
import random

_mod = importlib.import_module('sample-queries-and-documents')
select_documents = _mod.select_documents


# ---------------------------------------------------------------------------
# shared workload data (built once, never mutated by the function)
# ---------------------------------------------------------------------------

def _offsets(n):
    return {i: i * 8 for i in range(n)}


_OFF_60K = _offsets(60_000)
_OFF_120K = _offsets(120_000)
_OFF_200K = _offsets(200_000)


def _queries_random(n_qids, per_qid, pool, seed):
    rng = random.Random(seed)
    return {q: {"docs": [rng.randrange(pool) for _ in range(per_qid)]}
            for q in range(n_qids)}


def _queries_sequential(n_qids, per_qid):
    queries = {}
    start = 0
    for q in range(n_qids):
        queries[q] = {"docs": list(range(start, start + per_qid))}
        start += per_qid
    return queries


# 200 queries x 2000 docs drawn from a pool of 60k -> ~400k inner iterations
_Q_DUP = _queries_random(200, 2000, 60_000, 1)
_SEL_DUP = list(range(200))

# one query with 1000 docs, used as a small starting set for a big fill
_Q_SMALL = {0: {"docs": list(range(1000))}}
_SEL_SMALL = [0]

# 10k queries x 8 docs -> many dict lookups, all unique
_Q_MANY = _queries_sequential(10_000, 8)
_SEL_MANY = list(range(10_000))

# 50 queries x 100 docs -> small selected set, huge offsets table
_Q_BLOCK = {i: {"docs": list(range(i * 100, i * 100 + 100))} for i in range(50)}
_SEL_BLOCK = list(range(50))

# 50 queries x 1000 docs drawn from a pool of 20k -> moderate set + fill
_Q_MIX = _queries_random(50, 1000, 20_000, 2)
_SEL_MIX = list(range(50))

# 20k queries x 1 doc -> 20k starting docs, then a near-full fill
_Q_NEAR = _queries_sequential(20_000, 1)
_SEL_NEAR = list(range(20_000))

# 75 queries x 1000 docs -> set already large enough, loop skipped
_Q_COMPLETE = _queries_sequential(75, 1000)
_SEL_COMPLETE = list(range(75))


def _mk(sel, queries, offsets, target):
    """Thunk factory: sets the module global the function reads, returns args."""
    def thunk():
        _mod.documents_to_generate = target
        return (sel, queries, offsets)
    return thunk


# ---------------------------------------------------------------------------
# edge cases (not measured)
# ---------------------------------------------------------------------------

def checks():
    return [
        ("empty", lambda: ([], {}, {})),
        ("single-doc", lambda: ([0], {0: {"docs": [7]}}, {7: 0})),
        ("missing-qid", lambda: ([99], {0: {"docs": [1]}}, {1: 0})),
    ]


# ---------------------------------------------------------------------------
# measured cases
# ---------------------------------------------------------------------------

def cases():
    return [
        # 400k query->doc iterations, selected set already at the target
        ("query-duplicates", _mk(_SEL_DUP, _Q_DUP, _OFF_60K, 60_000)),

        # small starting set, fill up to 80k out of 200k offsets
        ("fill-80k", _mk(_SEL_SMALL, _Q_SMALL, _OFF_200K, 80_000)),

        # no selected queries at all, coupon-collector fill to 55k of 60k
        ("coupon-55k", _mk([], {}, _OFF_60K, 55_000)),

        # 10k queries, 80k unique docs, loop skipped
        ("many-qids", _mk(_SEL_MANY, _Q_MANY, _OFF_120K, 80_000)),

        # 20k starting docs, near-full fill to 58k of 60k
        ("near-full-58k", _mk(_SEL_NEAR, _Q_NEAR, _OFF_60K, 58_000)),

        # 200k offsets keys -> the docids list build dominates
        ("large-offsets", _mk(_SEL_BLOCK, _Q_BLOCK, _OFF_200K, 5_000)),

        # duplicated query docs plus a moderate fill
        ("mixed", _mk(_SEL_MIX, _Q_MIX, _OFF_120K, 60_000)),

        # 75k unique selected docs, loop skipped
        ("already-complete", _mk(_SEL_COMPLETE, _Q_COMPLETE, _OFF_120K, 75_000)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['query-duplicates', 'many-qids', 'large-offsets', 'already-complete']
_KEEP_CHECKS = ['empty', 'single-doc', 'missing-qid']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
