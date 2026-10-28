```python
import contextlib
import copy
import io
import json

import dxpy
import dxpy.dx_extract_utils.filter_to_payload as ftp
from dxpy.dx_extract_utils.filter_to_payload import validate_JSON


# --------------------------------------------------------------------------
# Schema files that validate_JSON reads from `extract_utils_basepath`.
# --------------------------------------------------------------------------
_TYPES = ("allele", "annotation", "genotype", "variant")


def _schema_obj(n_fields):
    props = {}
    for i in range(n_fields):
        props["field_%d" % i] = {"type": "string", "description": "x" * 24}
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "retrieve schema",
        "type": "object",
        "properties": props,
        "required": [],
    }


def _write_schema_dir(name, n_fields):
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_schema_obj(n_fields))
    for t in _TYPES:
        (d / ("retrieve_%s_schema.json" % t)).write_text(text)
    return d


_PROBE_DIR = _write_schema_dir("probe_schema", 3)
_SCHEMA_DIRS = [
    _write_schema_dir("schema_%02d" % i, n)
    for i, n in enumerate([800, 1600, 3000, 5000, 8000, 12000, 18000, 26000])
]


# --------------------------------------------------------------------------
# Probe the repository's own validator so that every measured input is a
# filter that the original function really accepts.
# --------------------------------------------------------------------------
@contextlib.contextmanager
def _silent():
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


def _valid(cand, ftype):
    old = ftp.extract_utils_basepath
    ftp.extract_utils_basepath = str(_PROBE_DIR)
    try:
        with _silent():
            validate_JSON(cand, ftype)
        return True
    except BaseException:
        return False
    finally:
        ftp.extract_utils_basepath = old


_KEYS = [
    "project", "scope", "chr", "start", "end", "allele", "rsid", "genotype",
    "annotation", "frequency", "quality", "filter", "variant", "gene",
    "transcript", "consequence", "impact", "clinical_significance",
    "population", "af", "dp", "gq", "id", "sample", "cohort", "dataset",
    "table", "fields", "filters", "and", "or", "not", "eq", "ne", "gt",
    "lt", "ge", "le", "in", "contains", "type", "name", "value", "op",
    "field", "list", "range", "min", "max", "values", "phenotype", "sex",
]

_VALUES = [1, "x", [1, 2], {"a": 1}, True, None, 0.5, ["a", "b"], "0/1", "rs123"]


def _find_base(ftype):
    if _valid({}, ftype):
        return {}
    for k in _KEYS:
        for v in _VALUES:
            if _valid({k: v}, ftype):
                return {k: v}
    for i, k1 in enumerate(_KEYS[:25]):
        for k2 in _KEYS[i + 1:25]:
            if _valid({k1: 1, k2: 1}, ftype):
                return {k1: 1, k2: 1}
    return None


def _grow(base, ftype):
    cur = dict(base)
    for k in _KEYS:
        if k in cur:
            continue
        for v in _VALUES:
            trial = dict(cur)
            trial[k] = v
            if _valid(trial, ftype):
                cur = trial
                break
    return cur


_GROWN = {}
for _t in _TYPES:
    _b = _find_base(_t)
    if _b is not None:
        _GROWN[_t] = _grow(_b, _t)


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------
def _make_thunk(filt, ftype, schema_dir):
    def thunk():
        ftp.extract_utils_basepath = str(schema_dir)
        return (copy.deepcopy(filt), ftype)
    return thunk


def checks():
    def mk(filt, ftype):
        def thunk():
            ftp.extract_utils_basepath = str(_PROBE_DIR)
            return (filt, ftype)
        return thunk

    return [
        ("empty-filter", mk({}, "allele")),
        ("single-key", mk({"project": "project-000000000000000000000000"}, "allele")),
        ("none-filter", mk(None, "allele")),
    ]


def cases():
    types = [t for t in _TYPES if t in _GROWN] or ["allele"]
    fracs = [0.15, 0.3, 0.45, 0.6, 0.7, 0.8, 0.9, 1.0]
    out = []
    for i in range(8):
        t = types[i % len(types)]
        grown = _GROWN.get(t, {})
        items = list(grown.items())
        if items:
            n = max(1, int(round(len(items) * fracs[i])))
            filt = dict(items[:n])
            if not _valid(filt, t):
                filt = dict(grown)
        else:
            filt = {}
        out.append(("case-%d-%s" % (i, t), _make_thunk(filt, t, _SCHEMA_DIRS[i])))
    return out
```