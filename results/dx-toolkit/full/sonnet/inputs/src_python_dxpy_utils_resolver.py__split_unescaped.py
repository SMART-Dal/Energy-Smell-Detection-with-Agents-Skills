# Inputs for src/python/dxpy/utils/resolver.py::split_unescaped, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
import string as _string

from dxpy.utils.resolver import split_unescaped

_AL = _string.ascii_letters + _string.digits


def _tok(rng, lo=4, hi=12):
    return ''.join(rng.choice(_AL) for _ in range(rng.randint(lo, hi)))


def _colon_plain(n, seed):
    rng = random.Random(seed)
    return ':'.join(_tok(rng) for _ in range(n))


def _colon_escaped(n, seed, esc_ratio):
    rng = random.Random(seed)
    fields = []
    for _ in range(n):
        t = _tok(rng)
        if rng.random() < esc_ratio:
            i = rng.randrange(len(t) + 1)
            t = t[:i] + '\\:' + t[i:]
        fields.append(t)
    return ':'.join(fields)


def _kv(n, seed):
    rng = random.Random(seed)
    return '='.join(_tok(rng) for _ in range(2 * n))


def _spaces(n, seed, esc_ratio):
    rng = random.Random(seed)
    words = []
    for _ in range(n):
        t = _tok(rng, 2, 10)
        if rng.random() < esc_ratio:
            i = rng.randrange(len(t) + 1)
            t = t[:i] + '\\ ' + t[i:]
        words.append(t)
    return ' '.join(words)


def _dense(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        parts.append(_tok(rng, 1, 4))
        parts.append(':' * rng.randint(1, 4))
    parts.append(_tok(rng, 1, 4))
    return ''.join(parts)


def _backslash(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        parts.append(_tok(rng, 3, 8))
        parts.append('\\' * rng.randint(1, 60))
        parts.append(':')
    parts.append(_tok(rng, 3, 8))
    return ''.join(parts)


def _mixed(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        r = rng.random()
        if r < 0.3:
            parts.append('project-' + _tok(rng, 8, 12))
        elif r < 0.6:
            parts.append('folder' + str(rng.randint(0, 999)) + '/' + _tok(rng, 3, 8))
        else:
            parts.append(_tok(rng, 2, 6) + '\\:' + _tok(rng, 2, 6))
        parts.append(':')
    parts.append(_tok(rng, 2, 6))
    return ''.join(parts)


_COLON_PLAIN = _colon_plain(6000, 0)
_COLON_ESC = _colon_escaped(6000, 1, 0.4)
_KV = _kv(3000, 2)
_KV2 = _kv(3500, 3)
_SPACES = _spaces(8000, 4, 0.2)
_DENSE = _dense(5000, 5)
_BACKSLASH = _backslash(3000, 6)
_MIXED = _mixed(5000, 7)


def checks():
    return [
        ("empty", lambda: (':', "")),
        ("one-separator", lambda: (':', ":")),
        ("empty-included", lambda: (':', "", True)),
    ]


def cases():
    return [
        ("colon-plain", lambda: (':', _COLON_PLAIN)),
        ("colon-escaped", lambda: (':', _COLON_ESC)),
        ("equals-include-empty", lambda: ('=', _KV, True)),
        ("equals-no-empty", lambda: ('=', _KV2)),
        ("spaces-escaped", lambda: (' ', _SPACES)),
        ("dense-colons", lambda: (':', _DENSE, True)),
        ("backslash-runs", lambda: (':', _BACKSLASH)),
        ("mixed-include-empty", lambda: (':', _MIXED, True)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['spaces-escaped', 'backslash-runs', 'mixed-include-empty', 'colon-escaped']
_KEEP_CHECKS = ['empty', 'one-separator', 'empty-included']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
