# Inputs for incremental-search/search-suggestions/accepted_words.py::process_docs, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

_VOCAB = [f"term{i}" for i in range(2000)]
_VOCAB_SMALL = [f"common{i}" for i in range(50)]
_PUNCT = [",", ".", "!", "?", "-", "_", "/", ":", ";", "(", ")", "[", "]",
          "'", '"', "*", "&", "%", "#", "@", "+", "="]


def _text(rng, n_terms, vocab, punct_rate=0.3):
    out = []
    for i in range(n_terms):
        out.append(rng.choice(vocab))
        if i < n_terms - 1:
            if rng.random() < punct_rate:
                out.append(rng.choice(_PUNCT))
            else:
                out.append(" ")
    return "".join(out)


def _docs(n, title_terms, content_terms, vocab, seed, punct_rate=0.3, skip_ratio=0.0):
    rng = random.Random(seed)
    docs = []
    for _ in range(n):
        if skip_ratio and rng.random() < skip_ratio:
            if rng.random() < 0.5:
                docs.append({'fields': {'title': '',
                                        'content': _text(rng, content_terms, vocab, punct_rate)}})
            else:
                docs.append({'fields': {'title': _text(rng, title_terms, vocab, punct_rate),
                                        'content': ''}})
            continue
        docs.append({'fields': {
            'title': _text(rng, title_terms, vocab, punct_rate),
            'content': _text(rng, content_terms, vocab, punct_rate),
        }})
    return docs


def _mixed_docs(n, seed):
    rng = random.Random(seed)
    titles = ["Hello", "World", "Foo123", "BAR", "x9", "Test42", "MiXeD", "a1B2"]
    contents = ["Alpha", "BETA", "gamma7", "Delta9", "OMEGA", "z1", "QwErTy", "n0d3"]
    docs = []
    for _ in range(n):
        title = " ".join(rng.choice(titles) for _ in range(6))
        content = " ".join(rng.choice(contents) for _ in range(80))
        docs.append({'fields': {'title': title, 'content': content}})
    return docs


_D_TYPICAL = _docs(1000, 6, 60, _VOCAB, 0)
_D_LARGE = _docs(3000, 8, 80, _VOCAB, 1)
_D_LONG = _docs(150, 5, 900, _VOCAB, 2)
_D_DUPES = _docs(2000, 10, 120, _VOCAB_SMALL, 3)
_D_PUNCT = _docs(1500, 8, 80, _VOCAB, 4, punct_rate=0.85)
_D_SKIP = _docs(3000, 8, 80, _VOCAB, 5, skip_ratio=0.5)
_D_MIXED = _mixed_docs(2500, 6)
_D_TINY = _docs(8000, 2, 5, _VOCAB, 7)


def checks():
    return [
        ("empty-list", lambda: ([],)),
        ("empty-fields", lambda: ([{'fields': {'title': '', 'content': ''}}],)),
        ("missing-fields", lambda: ([{'title': 'hello'}],)),
    ]


def cases():
    return [
        ("typical", lambda: (_D_TYPICAL,)),
        ("large-corpus", lambda: (_D_LARGE,)),
        ("long-content", lambda: (_D_LONG,)),
        ("duplicates", lambda: (_D_DUPES,)),
        ("punctuation-heavy", lambda: (_D_PUNCT,)),
        ("skipped-docs", lambda: (_D_SKIP,)),
        ("mixed-case-digits", lambda: (_D_MIXED,)),
        ("tiny-docs-many", lambda: (_D_TINY,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['large-corpus', 'duplicates', 'mixed-case-digits', 'skipped-docs']
_KEEP_CHECKS = ['empty-list', 'empty-fields', 'missing-fields']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
