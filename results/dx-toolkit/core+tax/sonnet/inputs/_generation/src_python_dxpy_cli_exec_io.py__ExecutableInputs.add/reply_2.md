```python
import collections
import json
import random

from dxpy.cli.exec_io import ExecutableInputs
from dxpy.utils import OrderedDefaultdict


# ---------------------------------------------------------------------------
# Input spec (like the one the repository builds from an executable's describe)
# ---------------------------------------------------------------------------
_SPEC_ATOMS = [
    {'name': 'reads', 'class': 'array:file'},
    {'name': 'count', 'class': 'int'},
    {'name': 'flag', 'class': 'boolean'},
    {'name': 'meta', 'class': 'hash'},
    {'name': 'tags', 'class': 'array:string'},
    {'name': 'nums', 'class': 'array:int'},
    {'name': 'ratio', 'class': 'float'},
    {'name': 'job_in', 'class': 'job'},
    {'name': 'app_in', 'class': 'app'},
    {'name': 'arrbool', 'class': 'array:boolean'},
    {'name': 'arrfloat', 'class': 'array:float'},
    {'name': 'arrjob', 'class': 'array:job'},
    {'name': 'arrhash', 'class': 'array:hash'},
    {'name': 'name', 'class': 'string'},
]
_SPEC = collections.OrderedDict((a['name'], a) for a in _SPEC_ATOMS)


def _make(input_spec, prefix=None, desc=None, inputs=None):
    """Build an ExecutableInputs instance without touching the network.

    The real constructor calls get_executable_description(), which needs an
    executable handler (a server round trip).  ``add`` only reads a handful of
    fields, so we build the object and set exactly those fields.
    """
    inst = ExecutableInputs.__new__(ExecutableInputs)
    inst.executable = None
    inst.region = None
    inst.input_name_prefix = prefix
    inst.input_spec = input_spec
    inst._desc = desc if desc is not None else {}
    inst.required_inputs = []
    inst.optional_inputs = []
    inst.array_inputs = set()
    inst.inputs = OrderedDefaultdict(list)
    if inputs:
        for k, v in inputs.items():
            inst.inputs[k] = v
    inst.requires_resolution = []
    return inst


# ---------------------------------------------------------------------------
# Realistic data, built once
# ---------------------------------------------------------------------------
_rng = random.Random(0)

# Big JSON list of ints (parsed with object_pairs_hook -> cheap for lists).
_BIG_LIST = [_rng.randint(0, 10 ** 6) for _ in range(150_000)]
_BIG_LIST_JSON = json.dumps(_BIG_LIST)

# JSON object parsed with object_pairs_hook=OrderedDict (this hook is slow, so
# keep it modest).
_DICT_HOOK = collections.OrderedDict(
    ("k%d" % i, _rng.randint(0, 10 ** 6)) for i in range(5_000)
)
_DICT_HOOK_JSON = json.dumps(_DICT_HOOK)

# JSON object parsed with the default hook (faster, so it can be bigger).
_DICT_PLAIN = collections.OrderedDict(
    ("p%d" % i, _rng.randint(0, 10 ** 6)) for i in range(20_000)
)
_DICT_PLAIN_JSON = json.dumps(_DICT_PLAIN)

# Long plain string; JSON-encoded it parses back to a str (not an immediate type).
_LONG_PLAIN = "".join(_rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(300_000))
_LONG_PLAIN_JSON = json.dumps(_LONG_PLAIN)

# Long value full of escaped colons: makes split_unescaped() do real work.
_LONG_STR = "".join("a\\:b" for _ in range(15_000))
_LONG_STR2 = "".join("x\\:y" for _ in range(8_000))

_JOB_ID = "job-0123456789abcdefghijklmn"


def checks():
    return [
        # prefix does not match -> early return, nothing happens
        ("prefix-skip", lambda: (_make(_SPEC, "zzz.", {}, None), "reads", "x")),
        # name not in spec and not a workflow -> DXCLIError
        ("unknown-input", lambda: (_make(_SPEC, None, {}, None), "nosuch", "1")),
        # empty name -> not in spec -> DXCLIError
        ("empty-name", lambda: (_make(_SPEC, None, {}, None), "", "1")),
    ]


def cases():
    return [
        # No input spec, unknown class: value is a big JSON list -> parsed & appended
        ("json-list-append",
         lambda: (_make(None, None, {}, None), "reads", _BIG_LIST_JSON)),

        # No input spec, unknown class: big JSON object (OrderedDict hook)
        # -> parsed & set (non-list slot)
        ("json-dict-set",
         lambda: (_make(None, None, {}, {"meta": "sentinel"}), "meta", _DICT_HOOK_JSON)),

        # Spec says "hash": big JSON object parsed (default hook) and set
        ("spec-hash-set",
         lambda: (_make(_SPEC, None, {}, None), "meta", _DICT_PLAIN_JSON)),

        # Spec says "array:hash": big JSON object parsed (default hook) and appended
        ("spec-arrayhash-append",
         lambda: (_make(_SPEC, None, {}, None), "arrhash", _DICT_PLAIN_JSON)),

        # No spec, unknown class: JSON string parses to str -> requires_resolution
        ("json-string-resolve",
         lambda: (_make(None, None, {}, None), "name", _LONG_PLAIN_JSON)),

        # Spec says "string": long escaped-colon value, split_unescaped work
        ("spec-string-long",
         lambda: (_make(_SPEC, None, {}, None), "name", _LONG_STR)),

        # No spec, unknown class: "job-xxx:field" -> JBOR construction
        ("job-jbor",
         lambda: (_make(None, None, {}, None), "reads", _JOB_ID + ":output_name")),

        # Class taken from the name ("reads:file"): unknown class -> requires_resolution
        ("name-colon-file-resolve",
         lambda: (_make(None, None, {}, None), "reads:file", _LONG_STR2)),
    ]
```