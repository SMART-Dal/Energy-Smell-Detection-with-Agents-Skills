# Inputs for incremental-search/search-suggestions/count_terms.py::process_docs, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

# ---------------------------------------------------------------------------
# Realistic document corpus for count_terms.process_docs
#
# The repository's main() calls process_docs(read_json_file(path), ...) where
# the JSON file is a list of documents, each shaped like
#   {"_id": ..., "fields": {"title": ..., "content": ...}}
# so we build exactly that structure.
# ---------------------------------------------------------------------------

_COMMON = ["the", "of", "and", "to", "in", "a", "is", "that", "for", "it",
           "as", "with", "on", "be", "at", "by", "this", "are", "or", "from"]


def _vocab(n, tag):
    return _COMMON + [f"t{tag}_{i}" for i in range(n)]


def _text(rng, vocab, n):
    return " ".join(rng.choice(vocab) for _ in range(n))


def _make_docs(n, seed, vocab, title_max, content_max, empty_frac=0.0):
    rng = random.Random(seed)
    docs = []
    for i in range(n):
        title = _text(rng, vocab, rng.randint(1, title_max))
        content = _text(rng, vocab, rng.randint(max(1, content_max // 2), content_max))
        if rng.random() < empty_frac:
            if rng.random() < 0.5:
                title = ""
            else:
                content = ""
        docs.append({
            "_id": f"doc-{seed}-{i}",
            "fields": {"title": title, "content": content},
        })
    return docs


# Different vocabularies per case so the term distributions differ.
_V_TYPICAL = _vocab(2000, 1)
_V_MANY = _vocab(1500, 2)
_V_LONG = _vocab(3000, 3)
_V_BIGRAM = _vocab(1200, 4)
_V_TRIGRAM = _vocab(900, 5)
_V_COMMON = _vocab(800, 6)
_V_EMPTY = _vocab(1000, 7)
_V_DUP = _vocab(60, 8)

_D_TYPICAL = _make_docs(100, 0, _V_TYPICAL, 5, 50)
_D_MANY = _make_docs(400, 1, _V_MANY, 4, 25)
_D_LONG = _make_docs(40, 2, _V_LONG, 8, 300)
_D_BIGRAM = _make_docs(120, 3, _V_BIGRAM, 5, 80)
_D_TRIGRAM = _make_docs(80, 4, _V_TRIGRAM, 6, 100)
_D_COMMON = _make_docs(150, 5, _V_COMMON, 5, 60)
_D_EMPTY = _make_docs(250, 6, _V_EMPTY, 5, 40, empty_frac=0.5)
_D_DUP = _make_docs(300, 7, _V_DUP, 4, 80)

_COMMON_SET = set(_COMMON)


def checks():
    return [
        ("empty-list", lambda: ([],)),
        ("empty-fields", lambda: ([{"fields": {"title": "", "content": ""}}],)),
        ("single-doc", lambda: ([{"fields": {"title": "hello", "content": "world"}}],)),
    ]


def cases():
    return [
        ("typical", lambda: (_D_TYPICAL,)),
        ("many-docs", lambda: (_D_MANY,)),
        ("long-content", lambda: (_D_LONG,)),
        ("bigrams", lambda: (_D_BIGRAM, 2)),
        ("trigrams", lambda: (_D_TRIGRAM, 3)),
        ("common-words", lambda: (_D_COMMON, 1, _COMMON_SET)),
        ("empty-fields", lambda: (_D_EMPTY,)),
        ("high-duplicates", lambda: (_D_DUP,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['trigrams', 'bigrams', 'many-docs', 'high-duplicates']
_KEEP_CHECKS = ['empty-list', 'empty-fields', 'single-doc']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
