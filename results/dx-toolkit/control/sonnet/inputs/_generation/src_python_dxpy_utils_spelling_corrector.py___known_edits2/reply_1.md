```python
import random

from dxpy.utils.spelling_corrector import _known_edits2, _edits1

_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _rand_word(rng, length):
    return "".join(rng.choice(_LETTERS) for _ in range(length))


def _repeated_word(rng, length, distinct):
    letters = rng.sample(_LETTERS, distinct)
    return "".join(rng.choice(letters) for _ in range(length))


def _base_vocab(n, seed):
    rng = random.Random(seed)
    vocab = {}
    while len(vocab) < n:
        vocab[_rand_word(rng, rng.randint(4, 12))] = rng.randint(1, 10 ** 6)
    return vocab


def _nwords_with_edits(base, word, hit_ratio, seed):
    """Add a random subset of the edit-distance-2 neighbourhood of *word*."""
    rng = random.Random(seed)
    nwords = dict(base)
    for e1 in _edits1(word):
        for e2 in _edits1(e1):
            if rng.random() < hit_ratio:
                nwords[e2] = rng.randint(1, 10 ** 6)
    return nwords


# --- module-level input construction (never timed) ---

_W1 = _rand_word(random.Random(1001), 3)
_W2 = _rand_word(random.Random(1002), 4)
_W3 = _rand_word(random.Random(1003), 5)
_W4 = _rand_word(random.Random(1004), 6)
_W5 = _rand_word(random.Random(1005), 7)
_W6 = _rand_word(random.Random(1006), 8)
_W7 = _rand_word(random.Random(1007), 9)
_W8 = _repeated_word(random.Random(1008), 8, 3)

_N1 = _nwords_with_edits(_base_vocab(2_000, 2001), _W1, 0.10, 3001)
_N2 = _nwords_with_edits(_base_vocab(15_000, 2002), _W2, 0.90, 3002)
_N3 = _nwords_with_edits(_base_vocab(30_000, 2003), _W3, 0.30, 3003)
_N4 = _nwords_with_edits(_base_vocab(50_000, 2004), _W4, 0.03, 3004)
_N5 = _nwords_with_edits(_base_vocab(60_000, 2005), _W5, 0.15, 3005)
_N6 = _nwords_with_edits(_base_vocab(80_000, 2006), _W6, 0.02, 3006)
_N7 = _nwords_with_edits(_base_vocab(20_000, 2007), _W7, 0.05, 3007)
_N8 = _nwords_with_edits(_base_vocab(40_000, 2008), _W8, 0.50, 3008)


def checks():
    small = {"the": 5, "then": 3, "them": 2}
    return [
        ("empty-word", lambda: ("", small)),
        ("empty-nwords", lambda: ("hello", {})),
        ("one-char", lambda: ("a", small)),
    ]


def cases():
    return [
        ("len3-low-hit", lambda: (_W1, _N1)),
        ("len4-high-hit", lambda: (_W2, _N2)),
        ("len5-mid-hit", lambda: (_W3, _N3)),
        ("len6-sparse", lambda: (_W4, _N4)),
        ("len7-mid-hit", lambda: (_W5, _N5)),
        ("len8-sparse", lambda: (_W6, _N6)),
        ("len9-sparse", lambda: (_W7, _N7)),
        ("len8-repeats", lambda: (_W8, _N8)),
    ]
```