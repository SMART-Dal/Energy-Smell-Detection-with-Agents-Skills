# Inputs for news/src/python/evaluate.py::predictions, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

from evaluate import predictions


def _build_children(n, seed, rel="int", heavy=False, shuffled=True):
    rng = random.Random(seed)
    order = list(range(n))
    if shuffled:
        rng.shuffle(order)
    children = []
    for idx in order:
        fields = {
            "news_id": "n%d" % idx,
            "title": "title of news %d" % idx,
            "category": "cat%d" % rng.randint(0, 40),
        }
        if rel == "int":
            fields["relevance"] = rng.randint(0, 4)
        else:
            fields["relevance"] = round(rng.uniform(0.0, 1.0), 6)
        if heavy:
            fields["subtopic"] = ["s%d" % rng.randint(0, 30) for _ in range(8)]
            fields["author"] = "author %d" % (idx % 250)
            fields["body"] = "word " * (10 + idx % 30)
        children.append({
            "id": "index:%d" % idx,
            "relevance": fields["relevance"],
            "fields": fields,
        })
    return children


def _hits(children):
    return {"root": {"children": children}}


def _ids_from(children, n, seed):
    rng = random.Random(seed)
    pool = [c["fields"]["news_id"] for c in children]
    return [rng.choice(pool) for _ in range(n)]


def _ids_tail(children, n, seed, tail):
    rng = random.Random(seed)
    pool = [c["fields"]["news_id"] for c in children[-tail:]]
    return [rng.choice(pool) for _ in range(n)]


# case 1: moderate number of children, moderate expected scan
_CH1 = _build_children(1000, 1)
_HITS1 = _hits(_CH1)
_IDS1 = _ids_from(_CH1, 500, 101)

# case 2: many children
_CH2 = _build_children(3000, 2)
_HITS2 = _hits(_CH2)
_IDS2 = _ids_from(_CH2, 600, 102)

# case 3: many queried ids, few children
_CH3 = _build_children(200, 3)
_HITS3 = _hits(_CH3)
_IDS3 = _ids_from(_CH3, 3000, 103)

# case 4: queried ids sit at the tail of the children list -> long scans
_CH4 = _build_children(2000, 4, shuffled=False)
_HITS4 = _hits(_CH4)
_IDS4 = _ids_tail(_CH4, 400, 104, 200)

# case 5: heavy duplication of a few news ids
_CH5 = _build_children(1200, 5)
_HITS5 = _hits(_CH5)
_pool5 = [c["fields"]["news_id"] for c in _CH5[:10]]
_rng5 = random.Random(105)
_IDS5 = [_rng5.choice(_pool5) for _ in range(1500)]

# case 6: float relevances and heavier hit documents
_CH6 = _build_children(1500, 6, rel="float", heavy=True)
_HITS6 = _hits(_CH6)
_IDS6 = _ids_from(_CH6, 500, 106)

# case 7: very many children, few ids
_CH7 = _build_children(4000, 7)
_HITS7 = _hits(_CH7)
_IDS7 = _ids_from(_CH7, 250, 107)

# case 8: dense random mix
_CH8 = _build_children(800, 8)
_HITS8 = _hits(_CH8)
_IDS8 = _ids_from(_CH8, 800, 108)


def checks():
    empty = {"root": {"children": []}}
    one = {
        "root": {
            "children": [
                {"id": "index:0", "relevance": 3, "fields": {"news_id": "a", "relevance": 3}}
            ]
        }
    }
    return [
        ("empty-ids", lambda: (empty, [])),
        ("single-hit", lambda: (one, ["a"])),
        ("missing-id", lambda: (one, ["b"])),
    ]


def cases():
    return [
        ("moderate-random", lambda: (_HITS1, _IDS1)),
        ("wide-children", lambda: (_HITS2, _IDS2)),
        ("many-ids", lambda: (_HITS3, _IDS3)),
        ("tail-matches", lambda: (_HITS4, _IDS4)),
        ("duplicates", lambda: (_HITS5, _IDS5)),
        ("float-relevance", lambda: (_HITS6, _IDS6)),
        ("many-children", lambda: (_HITS7, _IDS7)),
        ("dense-random", lambda: (_HITS8, _IDS8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['wide-children', 'tail-matches', 'many-children', 'float-relevance']
_KEEP_CHECKS = ['empty-ids', 'single-hit', 'missing-id']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
