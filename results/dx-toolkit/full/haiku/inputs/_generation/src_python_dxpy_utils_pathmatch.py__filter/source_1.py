import random


def _siblings(n, parent, seed, prefix="", width=6, suffix_pool=None, shuffle=True):
    rng = random.Random(seed)
    names = set()
    max_num = 10 ** width
    base = rng.randrange(max_num - n) if max_num > n else 0
    for i in range(n):
        num = base + i
        s = f"{parent}/{prefix}{num:0{width}d}"
        if suffix_pool:
            s += rng.choice(suffix_pool)
        names.add(s)
    names = list(names)
    if shuffle:
        rng.shuffle(names)
    return names


# Case 1: many siblings, pattern matches everything.
_names1 = _siblings(50_000, "/data/project", 1, prefix="run-", width=6)
_pat1 = "/data/project/run-*"

# Case 2: many siblings, only about 10% match.
_names2 = _siblings(100_000, "/data/project", 2, prefix="run-", width=6)
_pat2 = "/data/project/run-9*"

# Case 3: pattern full of '?' wildcards, all names match.
_names3 = _siblings(80_000, "/data/project", 3, prefix="run-", width=6)
_pat3 = "/data/project/run-??????"

# Case 4: character class selecting about half the names.
_names4 = _siblings(100_000, "/data/project", 4, prefix="run-", width=6)
_pat4 = "/data/project/run-[0-4]?????"

# Case 5: negated character class selecting the other half.
_names5 = _siblings(100_000, "/data/project", 5, prefix="run-", width=6)
_pat5 = "/data/project/run-[!0-4]?????"

# Case 6: deeper paths, so each name is a longer string.
_names6 = _siblings(80_000, "/data/project/subfolder/deeper", 6, prefix="file-", width=6)
_pat6 = "/data/project/subfolder/deeper/file-*"

# Case 7: mixed suffixes; only the .txt entries match.
_names7 = _siblings(
    100_000,
    "/data/project",
    7,
    prefix="",
    width=6,
    suffix_pool=["", ".txt", "_backup", "-old", ".tar.gz"],
)
_pat7 = "/data/project/*.txt"

# Case 8: exact literal pattern; only one name matches.
_names8 = _siblings(120_000, "/data/project", 8, prefix="run-", width=6)
_pat8 = _names8[0]


def checks():
    return [
        ("empty-names", lambda: ([], "/data/project/*")),
        ("single-match", lambda: (["/data/project/run-000001"], "/data/project/run-*")),
        ("none-pattern", lambda: (["/data/project/run-000001"], None)),
    ]


def cases():
    return [
        ("all-match-50k", lambda: (_names1, _pat1)),
        ("low-hit-100k", lambda: (_names2, _pat2)),
        ("question-mark-80k", lambda: (_names3, _pat3)),
        ("char-class-100k", lambda: (_names4, _pat4)),
        ("negated-class-100k", lambda: (_names5, _pat5)),
        ("deep-paths-80k", lambda: (_names6, _pat6)),
        ("suffix-mix-100k", lambda: (_names7, _pat7)),
        ("exact-literal-120k", lambda: (_names8, _pat8)),
    ]
