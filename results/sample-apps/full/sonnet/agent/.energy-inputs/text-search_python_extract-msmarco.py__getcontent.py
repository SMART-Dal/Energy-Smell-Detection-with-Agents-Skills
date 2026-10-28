# Inputs for text-search/python/extract-msmarco.py::getcontent, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import importlib
import random

getcontent = importlib.import_module('extract-msmarco').getcontent

_WORDS = "the quick brown fox jumps over lazy dog and cat run fast in a big red house with small green trees near blue water under bright sun".split()


def _build_file(path, lines):
    offsets = {}
    pos = 0
    with open(path, "w", encoding="utf8", newline="") as f:
        for docid, url, title, body in lines:
            offsets[docid] = pos
            line = f"{docid}\t{url}\t{title}\t{body}\n"
            f.write(line)
            pos += len(line.encode("utf8"))
    return offsets


def _gen_normal(rng, n_words):
    parts = []
    for i in range(n_words):
        parts.append(rng.choice(_WORDS))
        if i % 12 == 11:
            parts.append(".")
        elif i % 8 == 7:
            parts.append(",")
        else:
            parts.append(" ")
    return "".join(parts)


def _gen_camel(rng, n_words):
    return "".join(rng.choice(_WORDS).capitalize() for _ in range(n_words))


def _gen_punct(rng, n_words):
    punct = list(",;:!?()[]{}<>@#$%^&*-+=|~`")
    parts = []
    for _ in range(n_words):
        parts.append(rng.choice(_WORDS))
        parts.append(rng.choice(punct))
    return "".join(parts)


def _gen_plain(rng, n_words):
    return " ".join(rng.choice(_WORDS) for _ in range(n_words))


def _gen_underscore(rng, n_words):
    return "_".join(rng.choice(_WORDS) for _ in range(n_words))


def _gen_unicode(rng, n_words):
    uni = ["café", "naïve", "résumé", "über", "中文", "日本語", "αβγ",
           "δοκιμή", "тест", "prüfung", "mañana", "señor"]
    parts = []
    for _ in range(n_words):
        parts.append(rng.choice(_WORDS))
        parts.append(rng.choice(uni))
    return " ".join(parts)


def _gen_digit_symbol(rng, n_words):
    parts = []
    for _ in range(n_words):
        parts.append(str(rng.randint(0, 10 ** 9)))
        parts.append(rng.choice("+-*/=<>!@#$%^&*()"))
    return "".join(parts)


_CASES = []


def _add_case(label, seed, title_gen, body_gen, n_filler=200):
    rng = random.Random(seed)
    path = WORKDIR / f"docs_{seed}.tsv"
    target_docid = f"doc{seed}_target"
    target_url = f"http://example.com/{seed}/target"
    target_title = title_gen(rng)
    target_body = body_gen(rng)

    lines = []
    for i in range(n_filler):
        docid = f"doc{seed}_{i}"
        url = f"http://example.com/{seed}/{i}"
        title = " ".join(rng.choice(_WORDS) for _ in range(5))
        body = " ".join(rng.choice(_WORDS) for _ in range(20))
        lines.append((docid, url, title, body))
    lines.append((target_docid, target_url, target_title, target_body))

    offsets = _build_file(path, lines)
    f = open(path, "r", encoding="utf8", newline="")
    _CASES.append((label, f, offsets, target_docid))


# 8 measured inputs with diverse content and sizes.
_add_case("typical-web", 0,
          lambda rng: _gen_normal(rng, 30),
          lambda rng: _gen_normal(rng, 20000))

_add_case("huge-punct", 1,
          lambda rng: _gen_normal(rng, 20),
          lambda rng: _gen_punct(rng, 60000))

_add_case("camel-heavy", 2,
          lambda rng: _gen_camel(rng, 50),
          lambda rng: _gen_camel(rng, 60000))

_add_case("plain-spaces", 3,
          lambda rng: _gen_plain(rng, 20),
          lambda rng: _gen_plain(rng, 40000))

_add_case("underscore", 4,
          lambda rng: _gen_underscore(rng, 20),
          lambda rng: _gen_underscore(rng, 40000))

_add_case("unicode", 5,
          lambda rng: _gen_unicode(rng, 20),
          lambda rng: _gen_unicode(rng, 20000))

_add_case("digits-symbols", 6,
          lambda rng: _gen_digit_symbol(rng, 20),
          lambda rng: _gen_digit_symbol(rng, 50000))

_add_case("long-title", 7,
          lambda rng: _gen_normal(rng, 40000),
          lambda rng: _gen_normal(rng, 2000))


def cases():
    return [
        (label, (lambda f=f, offsets=offsets, docid=docid: (docid, f, offsets)))
        for label, f, offsets, docid in _CASES
    ]


_check_counter = 0


def _make_check_file(content):
    global _check_counter
    _check_counter += 1
    p = WORKDIR / f"check_{_check_counter}.tsv"
    with open(p, "w", encoding="utf8", newline="") as f:
        f.write(content)
    return open(p, "r", encoding="utf8", newline="")


def checks():
    f1 = _make_check_file("")
    f2 = _make_check_file("a\turl\ttitle\tbody\n")
    f3 = _make_check_file("a\turl\ttitle\n")

    return [
        ("empty-file", lambda: ("x", f1, {})),
        ("mismatch-docid", lambda: ("b", f2, {"b": 0})),
        ("too-few-fields", lambda: ("a", f3, {"a": 0})),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['camel-heavy', 'huge-punct', 'digits-symbols', 'unicode']
_KEEP_CHECKS = ['empty-file', 'mismatch-docid', 'too-few-fields']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
