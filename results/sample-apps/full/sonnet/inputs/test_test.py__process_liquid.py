# Inputs for test/test.py::process_liquid, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from test import process_liquid
import test

# ---------------------------------------------------------------------------
# Liquid -> shell transforms, set on the repository's own module so that the
# function under test reads them (it uses the module global `liquid_transforms`).
# ---------------------------------------------------------------------------
_TRANSFORMS = {
    r"""\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\|\s*default:\s*["']([^"']*)["']\s*\}\}""": r"${\1:-\2}",
    r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\|\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}": r"$(\2 \1)",
    r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}": r"${\1}",
    r"\{%\s*if\s+([A-Za-z_][A-Za-z0-9_]*)\s*%\}": r'if [ -n "$\1" ]; then',
    r"\{%\s*endif\s*%\}": "fi",
    r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}": r"for \1 in \2; do",
    r"\{%\s*endfor\s*%\}": "done",
    r"""\{%\s*include\s+["']([^"']+)["']\s*%\}""": r"source \1",
}

test.liquid_transforms = _TRANSFORMS

# ---------------------------------------------------------------------------
# Building blocks for realistic test-script bodies.
# ---------------------------------------------------------------------------
_VARS = ["app_name", "region", "version", "bucket", "artifact", "sha",
         "env", "user", "port", "host", "cluster", "namespace"]

_SIMPLE = ["{{ %s }}" % v for v in _VARS]
_FILTERED = (["{{ %s | upper }}" % v for v in _VARS]
             + ["{{ %s | lower }}" % v for v in _VARS]
             + ["{{ %s | trim }}" % v for v in _VARS])
_DEFAULTED = ["{{ %s | default: 'val%d' }}" % (v, i) for i, v in enumerate(_VARS)]
_IFS = ["{%% if %s %%}" % v for v in _VARS]
_ENDS = ["{% endif %}"]
_FORS = ["{%% for %s in %ss %%}" % (v, v) for v in _VARS]
_ENDF = ["{% endfor %}"]
_INCS = ["{%% include '%s.sh' %%}" % v for v in _VARS]

_WORDS = ["deploy", "build", "test", "run", "check", "clean", "install",
          "package", "upload", "fetch", "verify", "render", "publish", "sync"]


def _make_command(n_lines, seed, pool, max_tags=4):
    rng = random.Random(seed)
    lines = []
    for _ in range(n_lines):
        n_words = rng.randint(3, 10)
        text = " ".join("%s%d" % (rng.choice(_WORDS), rng.randint(0, 99999))
                        for _ in range(n_words))
        n_tags = rng.randint(0, max_tags)
        if n_tags:
            text += " " + " ".join(rng.choice(pool) for _ in range(n_tags))
        lines.append(text)
    return "\n".join(lines)


def _make_dupes(n_lines, tag, per_line):
    return "\n".join("echo " + " ".join([tag] * per_line) for _ in range(n_lines))


def _make_plain(n_lines, seed):
    rng = random.Random(seed)
    lines = []
    for _ in range(n_lines):
        n_words = rng.randint(5, 15)
        lines.append(" ".join("%s%d" % (rng.choice(_WORDS), rng.randint(0, 99999))
                              for _ in range(n_words)))
    return "\n".join(lines)


_C1 = _make_command(5000, 0, _SIMPLE + _FILTERED)
_C2 = _make_command(5000, 1, _IFS + _ENDS + _FORS + _ENDF, max_tags=5)
_C3 = _make_command(5000, 2, _INCS + _DEFAULTED)
_C4 = _make_command(7000, 3,
                    _SIMPLE + _FILTERED + _DEFAULTED + _IFS + _ENDS + _FORS + _ENDF + _INCS,
                    max_tags=6)
_C5 = _make_dupes(2500, "{{ app_name }}", 20)
_C6 = _make_plain(10000, 5)
_C7 = _make_command(6000, 6, _FILTERED + _DEFAULTED, max_tags=5)
_C8 = _make_command(10000, 7, _SIMPLE + _IFS + _ENDS + _INCS, max_tags=6)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-tag", lambda: ("echo {{ app_name }}",)),
        ("regex-specials", lambda: ("a.b*c(d)[e]{f}g\\h {{x}} {% endif %}",)),
    ]


def cases():
    return [
        ("simple-substitutions", lambda: (_C1,)),
        ("block-tags", lambda: (_C2,)),
        ("includes-defaults", lambda: (_C3,)),
        ("mixed-dense", lambda: (_C4,)),
        ("duplicate-tags", lambda: (_C5,)),
        ("no-matches", lambda: (_C6,)),
        ("filters", lambda: (_C7,)),
        ("large-mixed", lambda: (_C8,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['duplicate-tags', 'large-mixed', 'mixed-dense', 'filters']
_KEEP_CHECKS = ['empty', 'single-tag', 'regex-specials']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
