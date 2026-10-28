import random

from count_terms import read_common_words

_WORKDIR_FILES = {}


def _write(name, lines):
    path = WORKDIR / name
    path.write_text("\n".join(lines) + "\n")
    _WORKDIR_FILES[name] = path
    return path


def _words(n, vocab, seed, prefix="w"):
    rng = random.Random(seed)
    return [f"{prefix}{rng.randrange(vocab)}" for _ in range(n)]


# 1. small typical word list
_SMALL = _write("common_small.txt", _words(120, 120, 1))

# 2. medium list of mostly distinct words
_MEDIUM = _write("common_medium.txt", _words(5_000, 4_800, 2))

# 3. large list, mostly distinct
_LARGE = _write("common_large.txt", _words(80_000, 45_000, 3))

# 4. heavy duplicates -> small result set
_DUPES = _write("common_dupes.txt", _words(60_000, 150, 4))

# 5. blank lines, surrounding whitespace, tabs
_rng5 = random.Random(5)
_MESSY = _write(
    "common_messy.txt",
    [
        ("   " if i % 7 == 0 else ("\t" + f"word{i % 900}" + "\t" if i % 5 == 0 else f"  word{i % 900}  "))
        if i % 3 else ""
        for i in range(30_000)
    ],
)

# 6. very long lines
_rng6 = random.Random(6)
_LONG = _write(
    "common_long.txt",
    ["".join(_rng6.choice("abcdefghij") for _ in range(12_000)) for _ in range(600)],
)

# 7. unicode / mixed content
_rng7 = random.Random(7)
_alphabet = "áéíóúñüç日本語漢字Ω≈ç√∫˜µ≤≥÷"
_UNICODE = _write(
    "common_unicode.txt",
    ["".join(_rng7.choice(_alphabet) for _ in range(_rng7.randint(1, 40))) for _ in range(15_000)],
)

# 8. numeric / hyphenated / url-like tokens
_rng8 = random.Random(8)
_NUMERIC = _write(
    "common_numeric.txt",
    [
        _rng8.choice(
            [
                str(_rng8.randrange(10**9)),
                f"{_rng8.randrange(10**4)}-{_rng8.randrange(10**4)}",
                f"http://example.com/{_rng8.randrange(10**5)}",
                f"{_rng8.random():.10f}",
                f"user_{_rng8.randrange(10**6)}@host{_rng8.randrange(100)}.net",
            ]
        )
        for _ in range(40_000)
    ],
)

# edge-case files
_EMPTY = _write("common_empty.txt", [])
_ONE = _write("common_one.txt", ["onlyword"])
_ONLY_NEWLINE = WORKDIR / "common_newline.txt"
_ONLY_NEWLINE.write_text("\n")


def checks():
    return [
        ("empty-file", lambda: (_EMPTY,)),
        ("single-line", lambda: (_ONE,)),
        ("none-path", lambda: (None,)),
        ("missing-file", lambda: (WORKDIR / "does_not_exist.txt",)),
    ]


def cases():
    return [
        ("small", lambda: (_SMALL,)),
        ("medium", lambda: (_MEDIUM,)),
        ("large", lambda: (_LARGE,)),
        ("duplicates", lambda: (_DUPES,)),
        ("messy-whitespace", lambda: (_MESSY,)),
        ("long-lines", lambda: (_LONG,)),
        ("unicode", lambda: (_UNICODE,)),
        ("numeric-tokens", lambda: (_NUMERIC,)),
    ]
