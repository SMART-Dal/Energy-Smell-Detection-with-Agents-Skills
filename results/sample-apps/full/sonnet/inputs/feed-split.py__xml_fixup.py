# Inputs for feed-split.py::xml_fixup, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import importlib
import random

xml_fixup = importlib.import_module('feed-split').xml_fixup


def _xml_content(n, rng):
    parts = []
    total = 0
    while total < n:
        tag = rng.choice(['item', 'entry', 'record', 'data', 'node', 'row', 'field'])
        attr = rng.choice(['id', 'name', 'type', 'value', 'key', 'ref'])
        val = rng.randint(0, 10**6)
        text = rng.choice(['foo & bar', 'a < b', 'x > y', 'plain text', 'a & b & c', '1 < 2 > 0', 'value & more'])
        line = f'<{tag} {attr}="{val}">{text}</{tag}>'
        parts.append(line)
        total += len(line)
    return "\n".join(parts)[:n]


def _xml_content_special(n, rng):
    parts = []
    total = 0
    while total < n:
        tag = rng.choice(['item', 'entry', 'record'])
        attr = rng.choice(['id', 'name'])
        val = rng.randint(0, 10**6)
        text = rng.choice(['a & b & c', 'x < y > z', '&amp; &lt; &gt;', 'a < b & c > d'])
        line = f'<{tag} {attr}="{val}">{text}</{tag}>'
        parts.append(line)
        total += len(line)
    return "\n".join(parts)[:n]


def _make_doc(n_blocks, content_len, filler_len, seed, variants=False, dup=False, special=False):
    rng = random.Random(seed)
    parts = []
    filler = "<p>" + " ".join(f"word{rng.randint(0, 10000)}" for _ in range(max(1, filler_len // 6))) + "</p>"
    dup_content = None
    if dup:
        dup_content = _xml_content_special(content_len, random.Random(123)) if special else _xml_content(content_len, random.Random(123))
    for _ in range(n_blocks):
        if dup:
            content = dup_content
        else:
            content = _xml_content_special(content_len, rng) if special else _xml_content(content_len, rng)
        v = rng.randint(0, 2) if variants else 0
        if v == 0:
            block = "{% highlight xml %}" + content + "{% endhighlight %}"
        elif v == 1:
            block = "{%highlight xml%}" + content + "{%endhighlight%}"
        else:
            block = "{%  highlight  xml  %}" + content + "{%  endhighlight  %}"
        parts.append(block)
        parts.append(filler)
    return "".join(parts)


_DOC_TYPICAL = _make_doc(10, 200, 2000, 0)
_DOC_MANY = _make_doc(300, 80, 500, 1)
_DOC_LARGE = _make_doc(3, 300, 200000, 2)
_DOC_LONG = _make_doc(5, 20000, 1000, 3)
_DOC_SPECIAL = _make_doc(50, 500, 5000, 4, special=True)
_DOC_DUP = _make_doc(100, 300, 1000, 5, dup=True)
_DOC_VARIANTS = _make_doc(50, 400, 2000, 6, variants=True)
_DOC_MIXED = _make_doc(20, 1000, 100, 7)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-blocks", lambda: ("<p>hello world</p>",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("typical", lambda: (_DOC_TYPICAL,)),
        ("many-blocks", lambda: (_DOC_MANY,)),
        ("large-text", lambda: (_DOC_LARGE,)),
        ("long-blocks", lambda: (_DOC_LONG,)),
        ("special-chars", lambda: (_DOC_SPECIAL,)),
        ("duplicates", lambda: (_DOC_DUP,)),
        ("variants", lambda: (_DOC_VARIANTS,)),
        ("mixed", lambda: (_DOC_MIXED,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-blocks', 'special-chars', 'long-blocks', 'duplicates']
_KEEP_CHECKS = ['empty', 'no-blocks', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
