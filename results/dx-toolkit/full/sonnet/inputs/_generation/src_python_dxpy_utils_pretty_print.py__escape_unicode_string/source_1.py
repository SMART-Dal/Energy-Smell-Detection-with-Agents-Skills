import random

# Characters that the function escapes.
_SPECIALS = [chr(i) for i in range(0, 32)] + ["\\", chr(127)]
_PRINTABLE = [chr(i) for i in range(32, 127)]


def _plain(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choice(_PRINTABLE) for _ in range(n))


def _with_special(n, special_ratio, seed, specials=None):
    rng = random.Random(seed)
    if specials is None:
        specials = _SPECIALS
    out = []
    for _ in range(n):
        if rng.random() < special_ratio:
            out.append(rng.choice(specials))
        else:
            out.append(rng.choice(_PRINTABLE))
    return "".join(out)


def _all_controls(n, seed):
    rng = random.Random(seed)
    return "".join(chr(rng.randrange(0, 32)) for _ in range(n))


def _unicode(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.15:
            out.append(rng.choice(_SPECIALS))
        elif r < 0.5:
            out.append(chr(rng.randrange(128, 0xD800)))
        else:
            out.append(chr(rng.randrange(0xE000, 0x110000)))
    return "".join(out)


def _del_heavy(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.2:
            out.append(chr(127))
        elif r < 0.4:
            out.append(rng.choice(_SPECIALS))
        else:
            out.append(rng.choice(_PRINTABLE))
    return "".join(out)


# Built once, reused by every thunk call (function does not mutate its input).
_PLAIN_1M = _plain(1_000_000, 0)
_NEWLINES = _with_special(500_000, 0.15, 1, ["\n"])
_CONTROLS = _all_controls(250_000, 2)
_BACKSLASHES = _with_special(300_000, 0.40, 3, ["\\"])
_MIXED = _with_special(400_000, 0.30, 4)
_UNICODE = _unicode(500_000, 5)
_DEL = _del_heavy(300_000, 6)
_TABS_CR = _with_special(500_000, 0.25, 7, ["\t", "\r"])


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-char", lambda: ("a",)),
        ("only-specials", lambda: ("\n\\\x11\x7f",)),
    ]


def cases():
    return [
        ("plain-ascii-1M", lambda: (_PLAIN_1M,)),
        ("newlines-dense", lambda: (_NEWLINES,)),
        ("all-controls", lambda: (_CONTROLS,)),
        ("backslash-heavy", lambda: (_BACKSLASHES,)),
        ("mixed-random", lambda: (_MIXED,)),
        ("unicode-heavy", lambda: (_UNICODE,)),
        ("del-heavy", lambda: (_DEL,)),
        ("tabs-and-cr", lambda: (_TABS_CR,)),
    ]
