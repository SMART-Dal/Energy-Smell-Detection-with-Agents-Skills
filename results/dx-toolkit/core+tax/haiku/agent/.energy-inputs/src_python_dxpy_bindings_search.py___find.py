# Inputs for src/python/dxpy/bindings/search.py::_find, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from dxpy.bindings.search import _find


class _OfflineFindAPI(object):
    """Deterministic offline stand-in for a dxpy.api.system_find_* method.

    The repository always passes one of those functions as the *api_method*
    argument of _find.  This object has the same calling convention: it takes
    the query dict and returns a page dict with 'results', 'next' and
    optionally 'byParent'/'describe'.
    """

    def __init__(self, total, by_parent=None, describe=None, seed=0):
        rng = random.Random(seed)
        self._results = [
            {
                "id": "obj-%d-%d" % (rng.randrange(10 ** 6), i),
                "project": "project-%d" % rng.randrange(50),
            }
            for i in range(total)
        ]
        self._total = total
        self._by_parent = by_parent
        self._describe = describe

    def __call__(self, query, **kwargs):
        start = query.get("starting", 0)
        limit = query["limit"]
        page = self._results[start:start + limit]
        nxt = start + limit
        if nxt >= self._total:
            nxt = None
        resp = {"results": page, "next": nxt}
        if self._by_parent is not None:
            resp["byParent"] = self._by_parent
        if self._describe is not None:
            resp["describe"] = self._describe
        return resp


# Built once at import time; every thunk just hands back a reference.
_API_SMALL = _OfflineFindAPI(2000, seed=0)
_API_MEDIUM = _OfflineFindAPI(5000, seed=1)
_API_LARGE = _OfflineFindAPI(20000, seed=2)
_API_CAPPED = _OfflineFindAPI(30000, seed=3)
_API_TINY_LIMIT = _OfflineFindAPI(10000, seed=4)
_API_PARENT = _OfflineFindAPI(4000,
                              by_parent={"parent-0": ["child-a", "child-b"]},
                              describe=["name", "id", "project"],
                              seed=5)
_API_KWARGS = _OfflineFindAPI(8000, seed=6)
_API_BIG = _OfflineFindAPI(30000, seed=7)


def checks():
    return [
        ("empty-results",
         lambda: (_OfflineFindAPI(0, seed=0), {"name": "x"}, None, False, 100)),
        ("single-result",
         lambda: (_OfflineFindAPI(1, seed=0), {"name": "x"}, None, False, 100)),
        ("zero-limit",
         lambda: (_API_PARENT, {"name": "x"}, 0, False, 10)),
    ]


def cases():
    return [
        ("small-pages",
         lambda: (_API_SMALL, {"name": "x"}, None, False, 1)),
        ("medium-pages",
         lambda: (_API_MEDIUM, {"name": "x"}, None, False, 10)),
        ("large-pages",
         lambda: (_API_LARGE, {"name": "x"}, None, False, 100)),
        ("capped-limit",
         lambda: (_API_CAPPED, {"name": "x"}, 15000, False, 100)),
        ("limit-below-first-page",
         lambda: (_API_TINY_LIMIT, {"name": "x"}, 50, False, 100)),
        ("by-parent-describe",
         lambda: (_API_PARENT, {"name": "x"}, None, False, 50)),
        ("kwarg-project",
         lambda: call(_API_KWARGS, {"name": "x"}, None, False, 100,
                      project="proj-123")),
        ("big-pages",
         lambda: (_API_BIG, {"name": "x"}, None, False, 1000)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['big-pages', 'large-pages', 'capped-limit', 'kwarg-project']
_KEEP_CHECKS = ['empty-results', 'single-result', 'zero-limit']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
