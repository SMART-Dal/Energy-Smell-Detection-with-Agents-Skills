# Inputs for scripts/gc-elections/create-github-comments.py::sync, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import importlib
import random

sync = importlib.import_module('create-github-comments').sync


def _body(handles):
    lines = ["Voter notification"]
    for h in handles:
        lines.append("* @" + h)
    return "\n".join(lines) + "\n"


def _gen(n_comments, per_comment, stale_ratio, seed, n_file, stale_tag):
    """Build (file_handles, voter_comments) the way the repo's main() would."""
    rng = random.Random(seed)
    file_handles = ["voter%d" % i for i in range(n_file)]
    comments = []
    for c in range(n_comments):
        hs = []
        for _ in range(per_comment):
            if rng.random() < stale_ratio:
                hs.append("%s%d" % (stale_tag, rng.randrange(10 ** 7)))
            else:
                hs.append(rng.choice(file_handles))
        comments.append({'id': 100000 + c, 'body': _body(hs)})
    return file_handles, comments


def checks():
    return [
        ("empty",
         lambda: ("o", "r", "https://example.com/issues/0", [], [], True)),
        ("none-body",
         lambda: ("o", "r", "https://example.com/issues/0",
                  [{'id': 1, 'body': None}], [], True)),
        ("no-mentions",
         lambda: ("o", "r", "https://example.com/issues/0",
                  [{'id': 2, 'body': "just a normal comment"}],
                  ["alice"], True)),
    ]


def cases():
    f1, c1 = _gen(30, 12, 0.5, 1, 300, "stalea")
    f2, c2 = _gen(250, 20, 0.08, 2, 800, "staleb")
    f3, c3 = _gen(150, 15, 1.0, 3, 500, "stalec")
    f4, c4 = _gen(15, 250, 0.5, 4, 400, "staled")
    f5, c5 = _gen(120, 0, 0.0, 5, 200, "stalee")

    rng = random.Random(6)
    f6 = ["voter%d" % i for i in range(400)]
    c6 = []
    for i in range(60):
        hs = ([rng.choice(f6) for _ in range(6)]
              + ["dup%d" % i] * 8
              + ["staledup%d" % rng.randrange(1000) for _ in range(4)])
        c6.append({'id': 200000 + i, 'body': _body(hs)})

    f7, c7 = _gen(300, 12, 0.3, 7, 3000, "stalef")
    f8, c8 = _gen(300, 40, 0.6, 8, 1000, "staleg")

    return [
        ("typical-mixed",
         lambda: ("o", "r", "https://example.com/issues/1", c1, f1, True)),
        ("many-comments-few-stale",
         lambda: ("o", "r", "https://example.com/issues/2", c2, f2, True)),
        ("all-stale",
         lambda: ("o", "r", "https://example.com/issues/3", c3, f3, True)),
        ("large-comments",
         lambda: ("o", "r", "https://example.com/issues/4", c4, f4, True)),
        ("no-mentions",
         lambda: ("o", "r", "https://example.com/issues/5", c5, f5, True)),
        ("duplicates",
         lambda: ("o", "r", "https://example.com/issues/6", c6, f6, True)),
        ("big-file",
         lambda: ("o", "r", "https://example.com/issues/7", c7, f7, True)),
        ("heavy",
         lambda: ("o", "r", "https://example.com/issues/8", c8, f8, True)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['large-comments', 'all-stale', 'big-file', 'many-comments-few-stale']
_KEEP_CHECKS = ['empty', 'none-body', 'no-mentions']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
