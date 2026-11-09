import random

from dxpy.utils.describe import get_resolved_jbors


# ---------------------------------------------------------------------------
# Builders for realistic JBOR-bearing run input structures.
# ---------------------------------------------------------------------------

_JOB_CTR = [0]


def _job():
    _JOB_CTR[0] += 1
    return "job-%d" % _JOB_CTR[0]


def _plain_jbor(job, field):
    # {'job': ..., 'field': ...}  -> is_job_ref() True
    return {"job": job, "field": field}


def _wrapped_jbor(job, field, index=None):
    inner = {"job": job, "field": field}
    if index is not None:
        inner["index"] = index
    return {"$dnanexus_link": inner}


def _flat_list(n, wrapped, indexed=False, seed=0):
    """A list whose elements are JBORs (resolved side holds plain values)."""
    rng = random.Random(seed)
    res = []
    org = []
    for i in range(n):
        job = _job()
        field = "field%d" % (i % 25)
        if wrapped:
            idx = rng.randrange(8) if indexed else None
            org.append(_wrapped_jbor(job, field, idx))
            if indexed:
                res.append([rng.randrange(10 ** 6) for _ in range(10)])
            else:
                res.append(rng.randrange(10 ** 6))
        else:
            org.append(_plain_jbor(job, field))
            res.append(rng.randrange(10 ** 6))
    return res, org


def _list_of_dicts(n_dicts, keys_per, wrapped_prob, seed):
    """A list of dicts, each dict's values being JBORs."""
    rng = random.Random(seed)
    res = []
    org = []
    for _ in range(n_dicts):
        rd = {}
        od = {}
        for j in range(keys_per):
            job = _job()
            field = "field%d" % rng.randrange(25)
            if rng.random() < wrapped_prob:
                od["k%d" % j] = _wrapped_jbor(job, field)
            else:
                od["k%d" % j] = _plain_jbor(job, field)
            rd["k%d" % j] = rng.randrange(10 ** 6)
        res.append(rd)
        org.append(od)
    return res, org


def _dict_of_lists(n_keys, per_list, seed):
    """A dict whose values are lists of JBORs."""
    rng = random.Random(seed)
    res = {}
    org = {}
    for i in range(n_keys):
        rl = []
        ol = []
        for _ in range(per_list):
            job = _job()
            field = "field%d" % rng.randrange(25)
            if rng.random() < 0.5:
                ol.append(_wrapped_jbor(job, field))
            else:
                ol.append(_plain_jbor(job, field))
            rl.append(rng.randrange(10 ** 6))
        res["key%d" % i] = rl
        org["key%d" % i] = ol
    return res, org


def _tree(rng, depth, breadth, jbor_prob, wrapped_prob):
    """Random nested structure of lists/dicts with JBOR leaves."""
    if depth <= 0:
        if rng.random() < jbor_prob:
            job = _job()
            field = "field%d" % rng.randrange(25)
            if rng.random() < wrapped_prob:
                orig = _wrapped_jbor(job, field)
            else:
                orig = _plain_jbor(job, field)
            return rng.randrange(10 ** 6), orig
        v = rng.randrange(10 ** 6)
        return v, v

    n = rng.randrange(1, breadth + 1)
    if rng.random() < 0.5:
        res = []
        org = []
        for _ in range(n):
            r, o = _tree(rng, depth - 1, breadth, jbor_prob, wrapped_prob)
            res.append(r)
            org.append(o)
        return res, org
    else:
        res = {}
        org = {}
        for i in range(n):
            k = "k%d" % i
            r, o = _tree(rng, depth - 1, breadth, jbor_prob, wrapped_prob)
            res[k] = r
            org[k] = o
        return res, org


def _build_tree(depth, breadth, jbor_prob, wrapped_prob, seed):
    return _tree(random.Random(seed), depth, breadth, jbor_prob, wrapped_prob)


def _realistic(seed):
    """A run-input-shaped dict, like the one describe.py feeds the function."""
    rng = random.Random(seed)
    res = {}
    org = {}

    reads_res, reads_org = _flat_list(2500, wrapped=True, seed=seed + 1)
    res["reads"] = reads_res
    org["reads"] = reads_org

    res["reference"] = rng.randrange(10 ** 6)
    org["reference"] = _wrapped_jbor(_job(), "output")

    settings_res, settings_org = _tree(random.Random(seed + 2), 3, 6, 0.75, 0.5)
    res["settings"] = settings_res
    org["settings"] = settings_org

    stages_res, stages_org = _list_of_dicts(80, 10, 0.5, seed + 3)
    res["stages"] = stages_res
    org["stages"] = stages_org

    meta_res, meta_org = _dict_of_lists(25, 20, seed + 4)
    res["metadata"] = meta_res
    org["metadata"] = meta_org

    return res, org


# ---------------------------------------------------------------------------
# Module-level data (built once, never timed).
# ---------------------------------------------------------------------------

_C1 = _flat_list(6000, wrapped=False, seed=0)
_C2 = _flat_list(6000, wrapped=True, seed=1)
_C3 = _flat_list(5000, wrapped=True, indexed=True, seed=2)
_C4 = _list_of_dicts(1500, 5, 0.5, seed=3)
_C5 = _build_tree(5, 12, 0.8, 0.5, seed=4)
_C6 = _build_tree(6, 7, 0.9, 0.5, seed=5)
_C7 = _realistic(seed=6)
_C8 = _dict_of_lists(250, 25, seed=7)


def checks():
    return [
        ("equal-nested",   lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {})),
        ("empty-list",     lambda: ([], [], {})),
        ("top-level-jbor", lambda: (7, {"job": "job-check", "field": "out"}, {})),
    ]


def cases():
    return [
        ("flat-plain-jbors",   lambda: (_C1[0], _C1[1], {})),
        ("flat-wrapped-jbors", lambda: (_C2[0], _C2[1], {})),
        ("indexed-jbors",      lambda: (_C3[0], _C3[1], {})),
        ("list-of-dicts",      lambda: (_C4[0], _C4[1], {})),
        ("nested-tree",        lambda: (_C5[0], _C5[1], {})),
        ("deep-tree",          lambda: (_C6[0], _C6[1], {})),
        ("realistic-runinput", lambda: (_C7[0], _C7[1], {})),
        ("dict-of-lists",      lambda: (_C8[0], _C8[1], {})),
    ]
