import random

from backend.colpali import SimMapGenerator


_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Punctuation that is neither a word char nor whitespace, and contains no
# '<' or '_' so the random strings hit the punctuation branch of the regex.
_PUNCT = "!\"#$%&'()*+,-./:;=>?@[\\]^`{|}~"
_WS = " \t\n"


def _rand(alphabet, n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(alphabet, k=n))


# All tokens are built once, at module level; the thunks only return them.
_TOK_LT = "<" + _rand(_ALPHA, 300_000, 1)                 # matches ^<.*$
_TOK_WS = _rand(_WS, 300_000, 2)                          # matches ^\s+$
_TOK_PUNCT = _rand(_PUNCT, 300_000, 3)                    # matches the punctuation branch
_TOK_UNDERSCORE = "_" + _rand(_ALPHA, 300_000, 4)         # matches ^_.*$
_TOK_WORD = _rand(_ALPHA, 300_000, 5)                     # matches nothing
_TOK_DIGIT_FRONT = "1" + _rand(_ALPHA, 300_000, 6)        # digit at the very front
_TOK_PUNCT_DIGIT = _rand(_PUNCT, 300_000, 7) + "5"        # punctuation followed by a digit
_TOK_WS_WORD = _rand(_WS, 150_000, 8) + _rand(_ALPHA, 150_000, 9)  # whitespace then word chars


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-char", lambda: ("a",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("lt-prefix", lambda: (_TOK_LT,)),
        ("all-whitespace", lambda: (_TOK_WS,)),
        ("all-punctuation", lambda: (_TOK_PUNCT,)),
        ("underscore-prefix", lambda: (_TOK_UNDERSCORE,)),
        ("all-word-chars", lambda: (_TOK_WORD,)),
        ("digit-at-front", lambda: (_TOK_DIGIT_FRONT,)),
        ("punct-then-digit", lambda: (_TOK_PUNCT_DIGIT,)),
        ("whitespace-then-word", lambda: (_TOK_WS_WORD,)),
    ]
