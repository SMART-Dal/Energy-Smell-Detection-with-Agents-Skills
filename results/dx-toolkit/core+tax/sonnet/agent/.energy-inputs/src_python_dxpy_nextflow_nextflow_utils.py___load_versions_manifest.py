# Inputs for src/python/dxpy/nextflow/nextflow_utils.py::_load_versions_manifest, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import json
import random

import dxpy
from dxpy.nextflow.nextflow_utils import _load_versions_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_pkg(name, manifest):
    """Create <WORKDIR>/<name>/nextflow/versions.json and return the package dir."""
    d = WORKDIR / name
    (d / "nextflow").mkdir(parents=True, exist_ok=True)
    (d / "nextflow" / "versions.json").write_text(json.dumps(manifest))
    return d


def _pkg_thunk(pkg_dir):
    """Point dxpy.__file__ at the fake package so the function finds our manifest."""
    def thunk():
        dxpy.__file__ = str(pkg_dir / "__init__.py")
        return ()
    return thunk


def _cfg(rng, digest=None, extra=None):
    cfg = {
        "status": rng.choice(["active", "deprecated", "beta"]),
        "nextflow_assets": {"us-east-1": f"project-{rng.randrange(10**6)}"},
        "nextaur_assets": {"us-east-1": f"project-{rng.randrange(10**6)}"},
        "awscli_assets": {"us-east-1": f"project-{rng.randrange(10**6)}"},
        "cache_digest_type": digest or rng.choice(["config", "manifest"]),
    }
    if extra:
        cfg.update(extra)
    return cfg


# ---------------------------------------------------------------------------
# Manifest generators
# ---------------------------------------------------------------------------

def _tiny():
    rng = random.Random(0)
    versions = {}
    for i in range(4):
        versions[f"24.10.{i}"] = _cfg(rng, extra={
            "nextflow_version": f"24.10.{i}",
            "nextaur_version": "1.0.0",
            "description": "stable release",
        })
    return {"default": "24.10.0", "versions": versions}


def _many_minimal(n):
    versions = {}
    for i in range(n):
        versions[f"v{i}.0"] = {
            "status": "active",
            "nextflow_assets": {"us-east-1": f"p{i}"},
            "nextaur_assets": {"us-east-1": f"p{i}"},
            "awscli_assets": {"us-east-1": f"p{i}"},
            "cache_digest_type": "config",
        }
    return {"default": "v0.0", "versions": versions}


def _many_extras(n):
    rng = random.Random(2)
    versions = {}
    for i in range(n):
        versions[f"rel-{i}"] = _cfg(rng, extra={
            "nextflow_version": f"2{i}.{i % 10}",
            "nextaur_version": f"1.{i % 7}.0",
            "regions": [f"us-east-{j}" for j in range(rng.randint(1, 4))],
            "metadata": {
                "released": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "notes": [f"note-{rng.randrange(1000)}" for _ in range(3)],
            },
        })
    return {"default": "rel-0", "versions": versions}


def _large_strings(n):
    rng = random.Random(3)
    versions = {}
    for i in range(n):
        versions[f"big-{i}"] = _cfg(rng, extra={
            "notes": "".join(rng.choice("abcdefghijklmnopqrstuvwxyz ") for _ in range(3000)),
            "changelog": ["".join(rng.choice("0123456789abc") for _ in range(200))
                          for _ in range(20)],
        })
    return {"default": "big-0", "versions": versions}


def _unicode(n):
    rng = random.Random(4)
    chars = "áéíóúñü日本語中文한국어αβγδε"
    versions = {}
    for i in range(n):
        versions[f"版本-{i}"] = _cfg(rng, extra={
            "description": "".join(rng.choice(chars) for _ in range(40)),
            "标签": "".join(rng.choice(chars) for _ in range(20)),
        })
    return {"default": "版本-0", "versions": versions}


def _wide(n, keys):
    rng = random.Random(5)
    versions = {}
    for i in range(n):
        cfg = _cfg(rng)
        for j in range(keys):
            cfg[f"extra_key_{j}"] = rng.randrange(10**9)
        versions[f"wide-{i}"] = cfg
    return {"default": "wide-0", "versions": versions}


def _varied_digest(n):
    rng = random.Random(6)
    versions = {}
    for i in range(n):
        versions[f"dg-{i}"] = _cfg(rng, digest="config" if i % 2 == 0 else "manifest")
    return {"default": "dg-0", "versions": versions}


def _deep(value, depth):
    if depth <= 0:
        return value
    return {"level": _deep(value, depth - 1), "tag": depth}


def _deep_nested(n, depth):
    rng = random.Random(7)
    versions = {}
    for i in range(n):
        versions[f"deep-{i}"] = _cfg(rng, extra={
            "tree": _deep({"leaf": rng.randrange(10**6)}, depth),
        })
    return {"default": "deep-0", "versions": versions}


# ---------------------------------------------------------------------------
# Build all inputs once, at import time (never timed)
# ---------------------------------------------------------------------------

_CASE_TINY = _write_pkg("case_tiny", _tiny())
_CASE_MANY_MINIMAL = _write_pkg("case_many_minimal", _many_minimal(8000))
_CASE_MANY_EXTRAS = _write_pkg("case_many_extras", _many_extras(2500))
_CASE_LARGE_STRINGS = _write_pkg("case_large_strings", _large_strings(300))
_CASE_UNICODE = _write_pkg("case_unicode", _unicode(2000))
_CASE_WIDE = _write_pkg("case_wide", _wide(800, 40))
_CASE_VARIED = _write_pkg("case_varied", _varied_digest(4000))
_CASE_DEEP = _write_pkg("case_deep", _deep_nested(800, 15))


# ---------------------------------------------------------------------------
# Checks (small edge inputs, never measured)
# ---------------------------------------------------------------------------

def checks():
    missing = WORKDIR / "chk_missing"
    (missing / "nextflow").mkdir(parents=True, exist_ok=True)

    bad = WORKDIR / "chk_bad"
    (bad / "nextflow").mkdir(parents=True, exist_ok=True)
    (bad / "nextflow" / "versions.json").write_text("{not json")

    nokeys = WORKDIR / "chk_nokeys"
    (nokeys / "nextflow").mkdir(parents=True, exist_ok=True)
    (nokeys / "nextflow" / "versions.json").write_text(json.dumps({"foo": "bar"}))

    return [
        ("missing-file", _pkg_thunk(missing)),
        ("bad-json", _pkg_thunk(bad)),
        ("missing-keys", _pkg_thunk(nokeys)),
    ]


# ---------------------------------------------------------------------------
# Measured cases
# ---------------------------------------------------------------------------

def cases():
    return [
        ("tiny-realistic", _pkg_thunk(_CASE_TINY)),
        ("many-minimal", _pkg_thunk(_CASE_MANY_MINIMAL)),
        ("many-with-extras", _pkg_thunk(_CASE_MANY_EXTRAS)),
        ("large-strings", _pkg_thunk(_CASE_LARGE_STRINGS)),
        ("unicode-heavy", _pkg_thunk(_CASE_UNICODE)),
        ("wide-configs", _pkg_thunk(_CASE_WIDE)),
        ("varied-digest", _pkg_thunk(_CASE_VARIED)),
        ("deep-nested", _pkg_thunk(_CASE_DEEP)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-minimal', 'many-with-extras', 'unicode-heavy', 'varied-digest']
_KEEP_CHECKS = ['missing-file', 'bad-json', 'missing-keys']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
