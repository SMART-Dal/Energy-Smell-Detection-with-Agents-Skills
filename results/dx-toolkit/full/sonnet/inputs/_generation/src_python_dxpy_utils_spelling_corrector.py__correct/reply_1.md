```python
import random
from string import ascii_lowercase as LETTERS

from dxpy.utils.spelling_corrector import correct


# ---------------------------------------------------------------------------
# helpers used only to BUILD input data (never timed, never replacing code)
# ---------------------------------------------------------------------------
def _rand_word(rng, length):
    return "".join(rng.choice(LETTERS) for _ in range(length))


def _vocab(seed, n):
    # short words, so that edits of the longer target words can never collide
    rng = random.Random(seed)
    return [_rand_word(rng, rng.randint(2, 6)) for _ in range(n)]


def _del1(word, i):
    # a single deletion is always a member of _edits1(word)
    return word[:i] + word[i + 1:]


def _del2(word, i, j):
    # two deletions (i < j) -> member of _edits2(word) but never of _edits1(word)
    return word[:i] + word[i + 1:j] + word[j + 1:]


def _case_data(seed, n, word, kind):
    vocab = _vocab(seed, n)
    if kind == "self":
        vocab.append(word)
    elif kind == "edit1":
        vocab.append(_del1(word, 3))
    elif kind == "edit2":
        vocab.append(_del2(word, 3, 7))
    return word, vocab


# ---------------------------------------------------------------------------
# module level construction of the shared inputs
# ---------------------------------------------------------------------------
_wr = random.Random(7)

W_SELF = _rand_word(_wr, 10)
W_E1 = _rand_word(_wr, 10)
W_E2A = _rand_word(_wr, 10)
W_E2B = _rand_word(_wr, 12)
W_E2C = _rand_word(_wr, 13)
W_N10 = _rand_word(_wr, 10)
W_N11 = _rand_word(_wr, 11)
W_N13 = _rand_word(_wr, 13)

_CASE_DATA = [
    _case_data(101, 5_000, W_SELF, "self"),    # word is itself a known word
    _case_data(102, 20_000, W_E1, "edit1"),    # one edit-1 neighbour known
    _case_data(103, 20_000, W_E2A, "edit2"),   # only an edit-2 neighbour known
    _case_data(104, 30_000, W_E2B, "edit2"),   # longer word, edit-2 neighbour
    _case_data(105, 50_000, W_E2C, "edit2"),   # longest word, big vocabulary
    _case_data(106, 30_000, W_N10, "none"),    # nothing close -> falls back to word
    _case_data(107, 50_000, W_N11, "none"),
    _case_data(108, 20_000, W_N13, "none"),
]


def checks():
    return [
        ("empty-word-empty-vocab", lambda: ("", [])),
        ("single-char-known", lambda: ("a", ["a", "b", "c"])),
        ("none-word", lambda: (None, ["hello", "world"])),
    ]


def cases():
    return [
        ("self-known", lambda: _CASE_DATA[0]),
        ("edit1-hit", lambda: _CASE_DATA[1]),
        ("edit2-hit-len10", lambda: _CASE_DATA[2]),
        ("edit2-hit-len12", lambda: _CASE_DATA[3]),
        ("edit2-hit-len13", lambda: _CASE_DATA[4]),
        ("no-hit-len10", lambda: _CASE_DATA[5]),
        ("no-hit-len11", lambda: _CASE_DATA[6]),
        ("no-hit-len13", lambda: _CASE_DATA[7]),
    ]
```