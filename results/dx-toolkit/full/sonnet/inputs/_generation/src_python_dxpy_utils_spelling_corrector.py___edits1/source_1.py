import random

from dxpy.utils.spelling_corrector import _edits1


def _rand_word(n, seed, alphabet="abcdefghijklmnopqrstuvwxyz"):
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(n))


# Build all words once, at module level (setup is never timed).
_W5 = _rand_word(5, 0)
_W12 = _rand_word(12, 1)
_W25 = _rand_word(25, 2)
_W50_SMALL = _rand_word(50, 3, "abc")
_W90 = _rand_word(90, 4)
_W150 = _rand_word(150, 5)
_W260 = _rand_word(260, 6)
_W400_MIXED = _rand_word(
    400, 7,
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-char", lambda: ("a",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("word-5", lambda: (_W5,)),
        ("word-12", lambda: (_W12,)),
        ("word-25", lambda: (_W25,)),
        ("word-50-small-alphabet", lambda: (_W50_SMALL,)),
        ("word-90", lambda: (_W90,)),
        ("word-150", lambda: (_W150,)),
        ("word-260", lambda: (_W260,)),
        ("word-400-mixed", lambda: (_W400_MIXED,)),
    ]
