# Inputs for incremental-search/search-suggestions/count_terms.py::write_json_file, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random
from count_terms import write_json_file


def _make_terms(n, min_words, max_words, seed, vocab_size=500,
                double_space=False, count_max=100_000):
    rng = random.Random(seed)
    vocab = [f"w{i}" for i in range(vocab_size)]
    terms = {}
    while len(terms) < n:
        length = rng.randint(min_words, max_words)
        words = [rng.choice(vocab) for _ in range(length)]
        if double_space and len(words) > 1 and rng.random() < 0.25:
            term = "  ".join(words)
        else:
            term = " ".join(words)
        if term in terms:
            continue
        terms[term] = {
            "term": term,
            "count": rng.randint(1, count_max),
            "docs": rng.randint(1, 5000),
        }
    return terms


_TERMS_SINGLE = _make_terms(5000, 1, 1, 0, vocab_size=8000)
_TERMS_TWO = _make_terms(3500, 2, 2, 1, vocab_size=1000)
_TERMS_MIXED = _make_terms(3000, 1, 6, 2, vocab_size=500)
_TERMS_LONG = _make_terms(1200, 8, 15, 3, vocab_size=300)
_TERMS_MANY = _make_terms(6000, 1, 2, 4, vocab_size=8000)
_TERMS_DOUBLE = _make_terms(2000, 2, 8, 5, vocab_size=400, double_space=True)
_TERMS_HIGH_COUNTS = _make_terms(4000, 1, 4, 6, vocab_size=2000, count_max=10**12)
_TERMS_DENSE = _make_terms(1800, 4, 10, 7, vocab_size=500)


def checks():
    return [
        ("empty", lambda: ({}, WORKDIR / "check_empty.json")),
        ("single-term", lambda: (
            {"hello world": {"term": "hello world", "count": 3, "docs": 1}},
            WORKDIR / "check_single.json",
        )),
        ("none", lambda: (None, WORKDIR / "check_none.json")),
    ]


def cases():
    return [
        ("single-word-terms", lambda: (_TERMS_SINGLE, WORKDIR / "out_single.json")),
        ("two-word-phrases", lambda: (_TERMS_TWO, WORKDIR / "out_two.json")),
        ("mixed-lengths", lambda: (_TERMS_MIXED, WORKDIR / "out_mixed.json")),
        ("long-phrases", lambda: (_TERMS_LONG, WORKDIR / "out_long.json")),
        ("many-terms", lambda: (_TERMS_MANY, WORKDIR / "out_many.json")),
        ("double-spaces", lambda: (_TERMS_DOUBLE, WORKDIR / "out_double.json")),
        ("high-counts", lambda: (_TERMS_HIGH_COUNTS, WORKDIR / "out_counts.json")),
        ("dense-phrases", lambda: (_TERMS_DENSE, WORKDIR / "out_dense.json")),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['double-spaces', 'many-terms', 'high-counts', 'single-word-terms']
_KEEP_CHECKS = ['empty', 'single-term', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
