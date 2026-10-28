import random

from dxpy.utils.describe import get_resolved_jbors


# ---------------------------------------------------------------------------
# Builders: resolved / original have identical shape with differing leaves, so
# the function recurses through every node instead of early-returning.
# ---------------------------------------------------------------------------

def _flat_ints(n, seed):
    rng = random.Random(seed)
    res = [rng.randrange(10 ** 9) for _ in range(n)]
    org = [v + 1 for v in res]
    return res, org


def _list_of_lists(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = [[rng.randrange(10 ** 9) for _ in range(n_inner)] for _ in range(n_outer)]
    org = [[v + 1 for v in row] for row in res]
    return res, org


def _dict_of_lists(n_keys, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    for i in range(n_keys):
        k = "k%d" % i
        row = [rng.randrange(10 ** 9) for _ in range(n_inner)]
        res[k] = row
        org[k] = [v + 1 for v in row]
    return res, org


def _list_of_dicts(n, n_fields, seed):
    rng = random.Random(seed)
    res = []
    org = []
    for _ in range(n):
        d = {}
        e = {}
        for j in range(n_fields):
            k = "f%d" % j
            v = rng.randrange(10 ** 9)
            d[k] = v
            e[k] = v + 1
        res.append(d)
        org.append(e)
    return res, org


def _nested_dicts(depth, breadth, seed):
    rng = random.Random(seed)

    def build(d):
        if d == 0:
            v = rng.randrange(10 ** 9)
            return v, v + 1
        res = {}
        org = {}
        for i in range(breadth):
            k = "n%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org

    return build(depth)


def _tree(depth, breadth, seed):
    rng = random.Random(seed)

    def build(d):
        if d == 0:
            v = rng.randrange(10 ** 9)
            return v, v + 1
        if rng.random() < 0.5:
            res = []
            org = []
            for _ in range(breadth):
                r, o = build(d - 1)
                res.append(r)
                org.append(o)
            return res, org
        res = {}
        org = {}
        for i in range(breadth):
            k = "k%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org

    return build(depth)


# ---------------------------------------------------------------------------
# JBOR builders.  Every JBOR string is pre-registered in resolved_jbors, so the
# function never reaches the network call; it still walks the JBOR branch.
# ---------------------------------------------------------------------------

def _flat_jbors(n, seed):
    rng = random.Random(seed)
    res = []
    org = []
    resolved = {}
    for i in range(n):
        job = "job-%d" % i
        field = "out"
        resolved[job + ":" + field] = None
        org.append({"job": job, "field": field})
        res.append(rng.randrange(10 ** 9))
    return res, org, resolved


def _nested_jbors(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    resolved = {}
    for i in range(n_outer):
        k = "key%d" % i
        rl = []
        ol = []
        for j in range(n_inner):
            job = "job-%d-%d" % (i, j)
            field = "field%d" % (j % 7)
            resolved[job + ":" + field] = None
            if j % 2 == 0:
                ol.append({"job": job, "field": field})
            else:
                ol.append({"$dnanexus_link": {"job": job, "field": field}})
            rl.append(rng.randrange(10 ** 9))
        res[k] = rl
        org[k] = ol
    return res, org, resolved


# ---------------------------------------------------------------------------
# Module-level data (built once, never timed).
# ---------------------------------------------------------------------------

_C1 = _flat_ints(200_000, 0)
_C2 = _list_of_lists(1500, 100, 1)
_C3 = _dict_of_lists(300, 300, 2)
_C4 = _list_of_dicts(5000, 10, 3)
_C5 = _nested_dicts(5, 10, 4)
_C6 = _tree(7, 5, 5)
_C7 = _flat_jbors(30_000, 6)
_C8 = _nested_jbors(100, 200, 7)


def checks():
    return [
        ("equal-nested",   lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {})),
        ("empty-list",     lambda: ([], [], {})),
        ("top-jbor-known", lambda: (0, {"job": "j1", "field": "f1"}, {"j1:f1": None})),
    ]


def cases():
    return [
        ("flat-ints",     lambda: (_C1[0], _C1[1], {})),
        ("list-of-lists", lambda: (_C2[0], _C2[1], {})),
        ("dict-of-lists", lambda: (_C3[0], _C3[1], {})),
        ("list-of-dicts", lambda: (_C4[0], _C4[1], {})),
        ("nested-dicts",  lambda: (_C5[0], _C5[1], {})),
        ("mixed-tree",    lambda: (_C6[0], _C6[1], {})),
        ("flat-jbors",    lambda: (_C7[0], _C7[1], dict(_C7[2]))),
        ("nested-jbors",  lambda: (_C8[0], _C8[1], dict(_C8[2]))),
    ]
