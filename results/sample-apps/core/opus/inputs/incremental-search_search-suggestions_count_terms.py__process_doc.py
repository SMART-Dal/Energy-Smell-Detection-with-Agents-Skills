# Inputs for incremental-search/search-suggestions/count_terms.py::process_doc, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

_VOCAB = [f"term{i}" for i in range(300)]
_SMALL = [f"r{i}" for i in range(10)]


def _make_text(n, seed, vocab, punct=0.0, upper=0.0):
    rng = random.Random(seed)
    words = []
    for _ in range(n):
        w = vocab[rng.randrange(len(vocab))]
        if rng.random() < upper:
            w = w.capitalize()
        if rng.random() < punct:
            w = w + rng.choice([",", ".", "!", "?", ";", ":"])
        words.append(w)
    return " ".join(words)


# Documents built once, at module level; thunks only hand them over.
_DOC_TYPICAL = {
    "title": _make_text(12, 1, _VOCAB),
    "content": _make_text(300, 2, _VOCAB),
}
_DOC_TL2 = {
    "title": _make_text(25, 3, _VOCAB),
    "content": _make_text(1200, 4, _VOCAB),
}
_DOC_TL3 = {
    "title": _make_text(40, 5, _VOCAB),
    "content": _make_text(4000, 6, _VOCAB),
}
_DOC_TL4 = {
    "title": _make_text(60, 7, _VOCAB),
    "content": _make_text(8000, 8, _VOCAB),
}
_DOC_COMMON = {
    "title": _make_text(30, 9, _VOCAB),
    "content": _make_text(5000, 10, _VOCAB),
}
_DOC_REPET = {
    "title": _make_text(20, 11, _SMALL),
    "content": _make_text(6000, 12, _SMALL),
}
_DOC_PUNCT = {
    "title": _make_text(30, 13, _VOCAB, punct=0.6, upper=0.5),
    "content": _make_text(3000, 14, _VOCAB, punct=0.6, upper=0.5),
}
_DOC_TITLEHEAVY = {
    "title": _make_text(2000, 15, _VOCAB),
    "content": _make_text(200, 16, _VOCAB),
}

_COMMON = set(_VOCAB[:150])


def checks():
    return [
        ("both-empty", lambda: ({"title": "", "content": ""},)),
        ("empty-content", lambda: ({"title": "hello world", "content": ""},)),
        ("punct-only-title", lambda: ({"title": "!!! ???", "content": "abc def"},)),
    ]


def cases():
    return [
        ("typical", lambda: (_DOC_TYPICAL, 1)),
        ("tl2-medium", lambda: (_DOC_TL2, 2)),
        ("tl3-large", lambda: (_DOC_TL3, 3)),
        ("tl4-huge", lambda: (_DOC_TL4, 4)),
        ("common-words", lambda: (_DOC_COMMON, 2, _COMMON)),
        ("repetitive", lambda: (_DOC_REPET, 3)),
        ("punctuation", lambda: (_DOC_PUNCT, 2)),
        ("title-heavy", lambda: (_DOC_TITLEHEAVY, 3)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['tl4-huge', 'repetitive', 'tl3-large', 'common-words']
_KEEP_CHECKS = ['both-empty', 'empty-content', 'punct-only-title']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
