# Inputs for src/python/dxpy/utils/resolver.py::resolve_path, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

import dxpy
import dxpy.utils.resolver as resolver
from dxpy.utils.resolver import resolve_path

# ---------------------------------------------------------------------------
# Module-level state that resolve_path reads.  Everything here is just data
# (no mocks): the current project, the CLI working directory, and the module's
# project-name cache so that name resolution never has to hit the network.
# ---------------------------------------------------------------------------
_PROJ_ID = "project-" + "B" * 16
_JOB_ID = "job-" + "E" * 20

dxpy.WORKSPACE_ID = "project-" + "A" * 16
dxpy.config['DX_CLI_WD'] = '/a'

resolver.cached_project_names['myproj'] = "project-" + "C" * 16
resolver.cached_project_names[_PROJ_ID] = _PROJ_ID
resolver.cached_project_names[_JOB_ID] = "project-" + "A" * 16


# ---------------------------------------------------------------------------
# Input generators (run once, at import / thunk time -- never timed)
# ---------------------------------------------------------------------------
def _tok(rng, lo=3, hi=10):
    return ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz0123456789')
                   for _ in range(rng.randint(lo, hi)))


def _gen_deep(n, seed):
    """A long, deep folder path with many unescaped '/' separators."""
    rng = random.Random(seed)
    return '/'.join(_tok(rng) for _ in range(n))


def _gen_escaped(n, seed):
    """A long path where roughly half the separators are escaped ('\\/')."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append(_tok(rng, 2, 8))
        if i < n - 1:
            out.append('\\/' if rng.random() < 0.5 else '/')
    return ''.join(out)


def _gen_mixed(n, seed):
    """A long path mixing '.' and '..' components with normal names."""
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        r = rng.random()
        if r < 0.08:
            parts.append('..')
        elif r < 0.16:
            parts.append('.')
        else:
            parts.append(_tok(rng))
    return '/'.join(parts)


# Build the big strings once, at module level.
_DEEP0 = _gen_deep(3000, 0)
_DEEP1 = _gen_deep(3000, 1)
_DEEP2 = _gen_deep(3000, 2)
_DEEP3 = _gen_deep(3000, 3)
_ESCAPED = _gen_escaped(2500, 4)
_MIXED = _gen_mixed(3000, 5)


def checks():
    return [
        ("empty-string", lambda: ("",)),
        ("empty-not-allowed", lambda: call("", allow_empty_string=False)),
        ("colon-only", lambda: (":",)),
    ]


def cases():
    return [
        ("deep-no-colon", lambda: (_DEEP0,)),
        ("deep-folder-expected", lambda: call(_DEEP1, expected="folder")),
        ("proj-name-deep", lambda: ("myproj:" + _DEEP2,)),
        ("proj-id-deep", lambda: (_PROJ_ID + ":" + _DEEP3,)),
        ("leading-colon-deep", lambda: (":" + _DEEP0,)),
        ("escaped-slashes", lambda: (_ESCAPED,)),
        ("dotdot-mix", lambda: (_MIXED,)),
        ("hash-id", lambda: ("file-" + "D" * 19,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['leading-colon-deep', 'deep-no-colon', 'proj-id-deep', 'proj-name-deep']
_KEEP_CHECKS = ['empty-string', 'empty-not-allowed', 'colon-only']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
