# Inputs for src/python/dxpy/nextflow/nextflow_builder.py::prepare_custom_inputs, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import json
import random

_WORK = WORKDIR / "nextflow_schemas"
_WORK.mkdir(parents=True, exist_ok=True)


def _make_prop(rng, style):
    p = {}
    if style == "formats":
        p["type"] = "string"
        p["format"] = rng.choice(["file-path", "directory-path", "path"])
    elif style == "union":
        p["type"] = rng.choice(
            [["string", "null"], ["integer", "null"], ["boolean", "string"],
             ["number", "string"], ["object", "null"], ["string", "null"]]
        )
        if p["type"][0] == "string" and rng.random() < 0.5:
            p["format"] = rng.choice(["file-path", "path", "directory-path"])
    else:
        p["type"] = rng.choice(["string", "integer", "number", "boolean", "object"])
        if p["type"] == "string" and rng.random() < 0.5:
            p["format"] = rng.choice(["file-path", "directory-path", "path"])

    if style == "defaults":
        p["default"] = rng.choice(
            ["value_string", 7, 2.5, True, {"nested": "x"}, [1, 2, 3], ""]
        )
    elif rng.random() < 0.4:
        p["default"] = rng.choice(["val", 1, 3.5, False])

    if style == "longtext":
        p["description"] = " ".join("word%d" % rng.randrange(5000) for _ in range(25))
        p["help_text"] = " ".join("note%d" % rng.randrange(5000) for _ in range(20))
    elif rng.random() < 0.7:
        p["description"] = "description for input %d" % rng.randrange(100000)
        if rng.random() < 0.4:
            p["help_text"] = "extra help text %d" % rng.randrange(100000)

    if rng.random() < 0.15:
        p["hidden"] = True
    return p


def _make_schema(n_defs, props_per, seed, style="mixed", defs_key="definitions"):
    rng = random.Random(seed)
    defs = {}
    for d in range(n_defs):
        props = {}
        for j in range(props_per):
            props["p_%d_%d" % (d, j)] = _make_prop(rng, style)
        names = list(props.keys())
        if style == "required":
            req = names
        else:
            req = [n for n in names if rng.random() < 0.3]
        defs["def_%d_%d" % (d, seed)] = {"properties": props, "required": req}
    return {defs_key: defs}


def _write(name, schema):
    path = _WORK / name
    path.write_text(json.dumps(schema))
    return str(path)


_MIXED = _write("mixed.json", _make_schema(400, 20, 0, "mixed", "definitions"))
_DEFS = _write("defs.json", _make_schema(300, 26, 1, "mixed", "$defs"))
_REQUIRED = _write("required.json", _make_schema(200, 40, 2, "required", "definitions"))
_UNION = _write("union.json", _make_schema(250, 32, 3, "union", "definitions"))
_DEFAULTS = _write("defaults.json", _make_schema(200, 40, 4, "defaults", "definitions"))
_LONGTEXT = _write("longtext.json", _make_schema(150, 12, 5, "longtext", "definitions"))
_FORMATS = _write("formats.json", _make_schema(250, 32, 6, "formats", "definitions"))
_MANYDEFS = _write("manydefs.json", _make_schema(2600, 3, 7, "mixed", "definitions"))

# checks-only schemas
_NO_DEFS = _write("nodefs.json", {"properties": {"a": {"type": "string"}}})
_BAD_TYPE = _write("badtype.json", {"definitions": {"d": {"properties": {"x": {"type": "weird"}}}}})
_MISSING = str(_WORK / "does_not_exist.json")


def checks():
    return [
        ("missing-file", lambda: (_MISSING,)),
        ("no-definitions-key", lambda: (_NO_DEFS,)),
        ("unsupported-type", lambda: (_BAD_TYPE,)),
    ]


def cases():
    return [
        ("mixed-definitions", lambda: (_MIXED,)),
        ("dollar-defs", lambda: (_DEFS,)),
        ("all-required", lambda: (_REQUIRED,)),
        ("union-types", lambda: (_UNION,)),
        ("many-defaults", lambda: (_DEFAULTS,)),
        ("long-text", lambda: (_LONGTEXT,)),
        ("path-formats", lambda: (_FORMATS,)),
        ("many-definitions", lambda: (_MANYDEFS,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['all-required', 'union-types', 'many-definitions', 'path-formats']
_KEEP_CHECKS = ['missing-file', 'no-definitions-key', 'unsupported-type']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
