import json
import random

from dxpy.utils.pretty_print import flatten_json_array


def _dump(obj):
    # Same rendering the repository uses in executable_unbuilder._write_json_file
    return json.dumps(obj, indent=2, separators=(',', ': '))


def _strings(n, seed):
    rng = random.Random(seed)
    return ["item_%d_%d" % (rng.randrange(10 ** 7), i) for i in range(n)]


def _numbers(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        if rng.random() < 0.5:
            out.append(rng.randint(-10 ** 6, 10 ** 6))
        else:
            out.append(round(rng.uniform(-10 ** 4, 10 ** 4), 5))
    return out


def _special(n, seed):
    # strings with escaped quotes, backslashes and non-ascii (json escapes them)
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append("v%d \"q\" \\ %s" % (i, chr(0x4e00 + (i % 300))))
    return out


# ---- module level data (never timed) -------------------------------------

_SMALL = _dump({"a": 1, "arr": ["one", 2, "three", "four", "five", "six", 7.8, 9]})

_S300 = _dump({"name": "app", "patterns": _strings(300, 2)})

_S400 = _dump({"name": "app", "patterns": _strings(400, 3)})

_N350 = _dump({"name": "app", "patterns": _numbers(350, 4)})

_SP250 = _dump({"name": "app", "patterns": _special(250, 5)})

# three arrays sharing the name "patterns", at different nesting depths
_MULTI = _dump({
    "name": "app",
    "patterns": _strings(100, 6),
    "details": {
        "patterns": _numbers(100, 7),
        "nested": {"patterns": _strings(100, 8)},
    },
    "other": _strings(150, 9),
})

_CRLF = _dump({"name": "app", "patterns": _strings(300, 10)}).replace("\n", "\r\n")

# applet-like metadata: many small "patterns" arrays plus one big one
_DEEP = _dump({
    "id": "applet-abc",
    "inputSpec": [
        {"name": "in%d" % i, "class": "file", "patterns": _strings(4, 200 + i)}
        for i in range(25)
    ],
    "patterns": _strings(250, 11),
    "runSpec": {"code": "main", "distribution": "Ubuntu", "execDepends": []},
})


def checks():
    return [
        ("empty-string", lambda: ("", "patterns")),
        ("no-match", lambda: ('{"a": 1}', "patterns")),
        ("single-element", lambda: ('{\n  "patterns": [\n    "only"\n  ]\n}', "patterns")),
    ]


def cases():
    return [
        ("test-like-arr", lambda: (_SMALL, "arr")),
        ("strings-300", lambda: (_S300, "patterns")),
        ("strings-400", lambda: (_S400, "patterns")),
        ("numbers-350", lambda: (_N350, "patterns")),
        ("special-250", lambda: (_SP250, "patterns")),
        ("multi-arrays", lambda: (_MULTI, "patterns")),
        ("crlf-300", lambda: (_CRLF, "patterns")),
        ("deep-inputspec", lambda: (_DEEP, "patterns")),
    ]
