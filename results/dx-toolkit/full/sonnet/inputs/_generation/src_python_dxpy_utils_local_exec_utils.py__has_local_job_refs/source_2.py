import random

from dxpy.utils.local_exec_utils import has_local_job_refs


def _jbor(job_id, field="out", index=None):
    """Build a job-based object reference (JBOR) in the standard dict form."""
    link = {"job": job_id, "field": field}
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}


def _file_link(file_id):
    return {"$dnanexus_link": file_id}


def _plain(rng):
    r = rng.random()
    if r < 0.3:
        return rng.randint(0, 10 ** 9)
    elif r < 0.6:
        return "v" + str(rng.randint(0, 10 ** 9))
    elif r < 0.75:
        return None
    elif r < 0.85:
        return 1.5
    elif r < 0.95:
        return True
    else:
        return False


def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                file_link_ratio=0.0, list_ratio=0.1, dict_ratio=0.1):
    """A realistic input_hash: a dict of input names -> values (refs, lists, dicts, plain)."""
    d = {}
    for i in range(n_keys):
        key = "field_%d" % i
        if local_ref_pos is not None and i == local_ref_pos:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        elif file_link_ratio > 0 and rng.random() < file_link_ratio:
            d[key] = _file_link("file-%06d" % i)
        else:
            r = rng.random()
            if r < list_ratio:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < list_ratio + dict_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d


def _build_deep_local_ref(n_outer, n_inner, rng):
    """A local job ref buried in the first list, so it is found last (q.pop() is LIFO)."""
    d = {}
    for i in range(n_outer):
        lst = []
        for j in range(n_inner):
            if i == 0 and j == 0:
                lst.append(_jbor("localjob-deep"))
            else:
                r = rng.random()
                if r < 0.1:
                    lst.append({"x": _plain(rng), "y": _plain(rng)})
                else:
                    lst.append(_plain(rng))
        d["k%d" % i] = lst
    return d


def _build_big_list(n, rng):
    """A single huge list value under one key."""
    lst = []
    for i in range(n):
        r = rng.random()
        if r < 0.6:
            lst.append(_plain(rng))
        elif r < 0.8:
            lst.append(_jbor("job-%06d" % i))
        elif r < 0.9:
            lst.append({"a": _plain(rng), "b": _plain(rng)})
        else:
            lst.append([_plain(rng), _plain(rng)])
    return {"inputs": lst}


def _build_tree(depth, width, rng):
    """A deep, wide nested list tree (all containers, leaves are plain values)."""
    if depth == 0:
        return _plain(rng)
    return [_build_tree(depth - 1, width, rng) for _ in range(width)]


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, file_link_ratio=0.1,
                     list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, file_link_ratio=0.1,
                     list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3,
                     file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(150_000, _rng)
_CASE7 = {"root": _build_tree(8, 5, _rng)}
_CASE8 = _build_hash(40_000, _rng, file_link_ratio=0.05, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("nested-list-local-ref", lambda: ({"a": [_jbor("localjob-0001")]},)),
    ]


def cases():
    return [
        ("large-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("local-ref-deep", lambda: (_CASE3,)),
        ("nonlocal-refs-only", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
