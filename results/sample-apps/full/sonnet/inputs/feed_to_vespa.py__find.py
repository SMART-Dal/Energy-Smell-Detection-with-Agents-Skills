# Inputs for feed_to_vespa.py::find, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

from feed_to_vespa import find


def _visit_response(n_docs, seed):
    """A Vespa /document/v1 visit response, like vespa_visit returns."""
    rng = random.Random(seed)
    docs = []
    for i in range(n_docs):
        docs.append({
            "id": f"id:msdoc:msdoc::{rng.randrange(10 ** 9)}",
            "relevance": round(rng.random(), 6),
            "fields": {
                "title": f"document {i}",
                "body": "lorem ipsum dolor sit amet " * rng.randrange(1, 15),
                "tags": [f"tag{rng.randrange(100)}" for _ in range(rng.randrange(1, 8))],
                "views": rng.randrange(10 ** 6),
            },
        })
    return {
        "documents": docs,
        "continuation": f"cont-{rng.randrange(10 ** 9)}" if rng.random() < 0.7 else None,
        "totalCount": n_docs,
    }


def _nested(depth, key_len, separator, seed):
    """A chain of nested dicts, plus the dotted path that reaches the innermost one."""
    rng = random.Random(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    root = {}
    cur = root
    parts = []
    for i in range(depth):
        key = f"k{i}-" + "".join(rng.choice(alphabet) for _ in range(key_len))
        parts.append(key)
        nxt = {}
        cur[key] = nxt
        cur = nxt
    cur["leaf"] = "value"
    return root, separator.join(parts)


_VISIT = _visit_response(1500, 0)
_DEEP, _DEEP_PATH = _nested(400, 60, ".", 1)
_DEEP_SLASH, _DEEP_SLASH_PATH = _nested(300, 100, "/", 2)
_LONG, _LONG_PATH = _nested(60, 3000, ".", 3)


def checks():
    return [
        ("empty-path", lambda: ({"a": {"b": 1}}, "")),
        ("empty-dict", lambda: ({}, "a")),
        ("none-json", lambda: (None, "a")),
    ]


def cases():
    return [
        ("visit-documents",    lambda: (_VISIT, "documents")),
        ("visit-continuation", lambda: (_VISIT, "continuation")),
        ("document-id",        lambda: (_VISIT["documents"][0], "id")),
        ("document-nested",    lambda: (_VISIT["documents"][0], "fields.title")),
        ("miss-second-level",  lambda: (_VISIT, "documents.nonexistent")),
        ("trailing-separator", lambda: (_VISIT, "documents.")),
        ("deep-400",           lambda: (_DEEP, _DEEP_PATH)),
        ("deep-slash-300",     lambda: (_DEEP_SLASH, _DEEP_SLASH_PATH, "/")),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['deep-400', 'miss-second-level', 'deep-slash-300', 'document-nested']
_KEEP_CHECKS = ['empty-path', 'empty-dict', 'none-json']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
