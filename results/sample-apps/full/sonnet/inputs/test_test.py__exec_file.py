# Inputs for test/test.py::exec_file, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import os
import random

from test import exec_file

# All files the function writes must live under WORKDIR.  The function builds
# the parent chain of the path it is given, so we clean the whole case tree in
# the thunk before every call to keep each call doing the same work.
_BASE = WORKDIR / "exec_file_cases"
_BASE.mkdir(parents=True, exist_ok=True)


def _rel(p):
    # exec_file breaks on absolute paths ('' component -> makedirs('')), so we
    # hand it a path relative to the current directory that still resolves
    # inside WORKDIR.
    return os.path.relpath(str(p), os.getcwd())


def _text(n, seed, alphabet="abcdefghijklmnopqrstuvwxyz 0123456789\n:-#/"):
    rng = random.Random(seed)
    return "".join(rng.choices(alphabet, k=n))


def _cleanup(base):
    b = str(base)
    if not os.path.isdir(b):
        return
    for root, dirs, files in os.walk(b, topdown=False):
        for f in files:
            try:
                os.remove(os.path.join(root, f))
            except OSError:
                pass
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except OSError:
                pass
    try:
        os.rmdir(b)
    except OSError:
        pass


def _thunk(base, cmd):
    def run():
        _cleanup(base)
        return (cmd, None)
    return run


def _mk(base_name, levels, content):
    base = _BASE / base_name
    full = base.joinpath(*(["a"] * levels), "file.txt")
    return _thunk(base, {"path": _rel(full), "content": content})


def checks():
    e = _BASE / "chk_empty"
    n = _BASE / "chk_none"
    m = _BASE / "chk_missing"
    return [
        ("empty-content", _thunk(e, {"path": _rel(e / "file.txt"), "content": ""})),
        ("none-content", _thunk(n, {"path": _rel(n / "file.txt"), "content": None})),
        ("missing-content", _thunk(m, {"path": _rel(m / "file.txt")})),
    ]


def cases():
    c_small = _text(2_000, 1)
    c_med = _text(90_000, 2)
    raw = _text(80_000, 3)
    c_lines = "\n".join(raw[i:i + 17] for i in range(0, len(raw), 17))
    c_uni = _text(40_000, 5,
                  alphabet="αβγδεζηθικλμνξοπρστυφχψωабвгдежзийклмн 0123456789\n")
    return [
        ("typical", _mk("c0", 2, c_small)),
        ("medium-content", _mk("c1", 3, c_med)),
        ("many-lines", _mk("c2", 4, c_lines)),
        ("unicode-content", _mk("c3", 2, c_uni)),
        ("deep-100", _mk("c4", 100, c_med)),
        ("deep-250", _mk("c5", 250, c_small)),
        ("deep-450", _mk("c6", 450, c_med)),
        ("deep-700", _mk("c7", 700, c_small)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['deep-700', 'deep-450', 'deep-250', 'deep-100']
_KEEP_CHECKS = ['empty-content', 'none-content', 'missing-content']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
