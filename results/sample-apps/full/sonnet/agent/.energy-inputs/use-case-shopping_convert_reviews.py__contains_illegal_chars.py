# Inputs for use-case-shopping/convert_reviews.py::contains_illegal_chars, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from convert_reviews import contains_illegal_chars


_WORDS = [
    "excellent", "wonderful", "disappointing", "recommend", "purchase",
    "quality", "delivery", "customer", "service", "product",
    "experience", "fantastic", "terrible", "average", "satisfied",
    "refund", "shipping", "packaging", "description", "material",
    "comfortable", "beautiful", "expensive", "worthwhile", "unfortunately",
    "absolutely", "completely", "different", "expectation", "recommended",
    "improvement", "considering", "nevertheless", "understanding", "particularly",
]


def _make_text(n_words, seed):
    rng = random.Random(seed)
    return " ".join(rng.choices(_WORDS, k=n_words))


_BASE_8M = _make_text(800_000, 1)
_BASE_6M = _make_text(600_000, 2)
_BASE_4M = _make_text(400_000, 3)
_BASE_2M = _make_text(200_000, 4)
_BASE_1M = _make_text(100_000, 5)

_MID = len(_BASE_8M) // 2
_TEXT_MIDDLE = _BASE_8M[:_MID] + "\u001a" + _BASE_8M[_MID:]
_TEXT_END = _BASE_8M + "\u001a"
_TEXT_START = "\u001a" + _BASE_6M

_F_ILLEGAL_NAME = {
    "reviewer_name": "John\u001aDoe",
    "title": "A review",
    "text": _BASE_2M,
}
_F_ILLEGAL_TITLE = {
    "reviewer_name": "John Doe",
    "title": "Great\u001aproduct",
    "text": _BASE_4M,
}
_F_ILLEGAL_START = {
    "reviewer_name": "John Doe",
    "title": "A review",
    "text": _TEXT_START,
}
_F_ILLEGAL_MIDDLE = {
    "reviewer_name": "John Doe",
    "title": "A review",
    "text": _TEXT_MIDDLE,
}
_F_ILLEGAL_END = {
    "reviewer_name": "John Doe",
    "title": "A review",
    "text": _TEXT_END,
}
_F_CLEAN_LARGE = {
    "reviewer_name": "John Doe",
    "title": "A review",
    "text": _BASE_8M,
}
_F_CLEAN_MEDIUM = {
    "reviewer_name": "John Doe",
    "title": "A review",
    "text": _BASE_4M,
}
_F_CLEAN_SMALL = {
    "reviewer_name": "John Doe",
    "title": "A review",
    "text": _BASE_1M,
}


def checks():
    return [
        ("empty", lambda: ({"reviewer_name": "", "title": "", "text": ""},)),
        ("illegal-name", lambda: ({"reviewer_name": "\u001a", "title": "", "text": ""},)),
        ("missing-key", lambda: ({"reviewer_name": "", "title": ""},)),
    ]


def cases():
    return [
        ("illegal-name", lambda: (_F_ILLEGAL_NAME,)),
        ("illegal-title", lambda: (_F_ILLEGAL_TITLE,)),
        ("illegal-text-start", lambda: (_F_ILLEGAL_START,)),
        ("illegal-text-middle", lambda: (_F_ILLEGAL_MIDDLE,)),
        ("illegal-text-end", lambda: (_F_ILLEGAL_END,)),
        ("clean-large", lambda: (_F_CLEAN_LARGE,)),
        ("clean-medium", lambda: (_F_CLEAN_MEDIUM,)),
        ("clean-small", lambda: (_F_CLEAN_SMALL,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['clean-large', 'illegal-text-end', 'illegal-text-middle', 'clean-medium']
_KEEP_CHECKS = ['empty', 'illegal-name', 'missing-key']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
