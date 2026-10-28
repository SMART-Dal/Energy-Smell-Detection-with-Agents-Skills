```python
import importlib
import random

_build_issue_body = importlib.import_module('move-to-emeritus')._build_issue_body

ROLE_LABELS = ["Triager", "Approver", "Maintainer", "Member", "Emeritus"]


def _rand_word(rng, n):
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))


def _changes(n, tmin, tmax, seed, prefix="u", ulen=8, tlen=8):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        user = prefix + _rand_word(rng, ulen)
        label = rng.choice(ROLE_LABELS)
        k = rng.randint(tmin, tmax)
        teams = [f"team-{rng.randrange(10**9)}-{_rand_word(rng, tlen)}" for _ in range(k)]
        out.append((user, label, teams))
    return out


def _dup_changes(n, seed):
    rng = random.Random(seed)
    users = [f"user{i}" for i in range(50)]
    labels = ["Triager", "Approver", "Maintainer"]
    teams = [f"team{i}" for i in range(30)]
    out = []
    for _ in range(n):
        k = rng.randint(1, 5)
        out.append((rng.choice(users), rng.choice(labels),
                    [rng.choice(teams) for _ in range(k)]))
    return out


def _unicode_changes(n, seed):
    rng = random.Random(seed)
    chars = "áéíóúüñç中文日本語한국어αβγδεζ"
    out = []
    for _ in range(n):
        user = "".join(rng.choice(chars) for _ in range(10))
        label = rng.choice(ROLE_LABELS)
        k = rng.randint(1, 4)
        teams = ["".join(rng.choice(chars) for _ in range(8)) for _ in range(k)]
        out.append((user, label, teams))
    return out


_MANY = _changes(20000, 1, 3, 0)
_WIDE = _changes(2000, 20, 40, 1)
_HUGE = _changes(300, 100, 200, 2)
_SORTED = sorted(_changes(15000, 1, 4, 3))
_REVERSED = sorted(_changes(15000, 1, 4, 4), reverse=True)
_DUPS = _dup_changes(15000, 5)
_LONG = _changes(5000, 2, 5, 6, ulen=60, tlen=60)
_UNICODE = _unicode_changes(8000, 7)


def checks():
    return [
        ("empty", lambda: ([],)),
        ("single", lambda: ([("alice", "Triager", ["team-a"])],)),
        ("tuple-teams", lambda: ([("bob", "Approver", ("t1", "t2"))],)),
    ]


def cases():
    return [
        ("many-members", lambda: (_MANY,)),
        ("wide-teams", lambda: (_WIDE,)),
        ("huge-teams", lambda: (_HUGE,)),
        ("sorted-input", lambda: (_SORTED,)),
        ("reverse-sorted", lambda: (_REVERSED,)),
        ("duplicates", lambda: (_DUPS,)),
        ("long-names", lambda: (_LONG,)),
        ("unicode", lambda: (_UNICODE,)),
    ]
```