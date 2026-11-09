```python
import random

from backend.colpali import SimMapGenerator

# Alphabets chosen so that every case hits a different branch of the regex.
_LETTERS = "abcdefghijklmnopqrstuvwxyz"
# No '<' (first alternative), no '_' (fourth), no digits, no whitespace,
# no '▁' (U+2581).
_PUNCT = "!\"#$%&'()*+,-./:;=>?@[\\]^`{|}~"
_WS = " \t\n\r\f\v"
_BLOCK = "\u2581"


def _rand_string(alphabet, n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(alphabet, k=n))


def _punct(n, seed):
    return _rand_string(_PUNCT, n, seed)


def _letters(n, seed):
    return _rand_string(_LETTERS, n, seed)


def _whitespace(n, seed):
    return _rand_string(_WS, n, seed)


def _punct_then(n, tail, seed):
    return _punct(n, seed) + tail


def _letters_then(n, tail, seed):
    return _letters(n, seed) + tail


def checks():
    return [
        ("empty",        lambda: ("",)),
        ("single-space", lambda: (" ",)),
        ("question",     lambda: ("Question",)),
    ]


def cases():
    return [
        # long punctuation run -> third alternative matches the whole string
        ("punct-500k",            lambda: (_punct(500_000, 0),)),
        # long whitespace run -> second alternative matches
        ("whitespace-500k",       lambda: (_whitespace(500_000, 1),)),
        # long letters, no digit -> lookahead scans everything, match fails
        ("letters-500k",          lambda: (_letters(500_000, 2),)),
        # '<' prefix -> first alternative matches, '.*' scans everything
        ("bracket-prefix-500k",   lambda: ("<" + _letters(500_000, 3),)),
        # '_' prefix -> fourth alternative matches, '.*' scans everything
        ("underscore-prefix-500k", lambda: ("_" + _letters(500_000, 4),)),
        # '▁' prefix -> (?!▁) fails, lookahead had already scanned everything
        ("blockchar-prefix-500k", lambda: (_BLOCK + _letters(500_000, 5),)),
        # punctuation run ending in a word char -> '[^\w\s]+$' backtracks fully
        ("punct-then-letter-500k", lambda: (_punct_then(499_999, "a", 6),)),
        # letters with a digit at the very end -> '(?!.*\d)' scans fully, fails
        ("letters-then-digit-500k", lambda: (_letters_then(499_999, "7", 7),)),
    ]
```