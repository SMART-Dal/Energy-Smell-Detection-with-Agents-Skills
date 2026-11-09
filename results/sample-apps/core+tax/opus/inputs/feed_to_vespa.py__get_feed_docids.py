# Inputs for feed_to_vespa.py::get_feed_docids, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import json
import random


def _dump(name, docs):
    p = WORKDIR / name
    p.write_text(json.dumps(docs), encoding="utf-8")
    return str(p)


def _make_doc_docs(n, seed, ns_count=5, path_count=200000, extra_fields=True):
    rng = random.Random(seed)
    docs = []
    for i in range(n):
        ns = "ns%d" % rng.randrange(ns_count)
        path = "/data/%d/%d" % (rng.randrange(50), rng.randrange(path_count))
        fields = {"namespace": ns, "path": path}
        if extra_fields:
            fields["title"] = "title-%d-%d" % (i, rng.randrange(1000))
            fields["body"] = "body text %d" % rng.randrange(10 ** 6)
        docs.append({"put": "id:%s:doc::d%d" % (ns, i), "fields": fields})
    return docs


def _make_term_docs(n, seed, missing_ratio=0.0, hash_str_ratio=0.0):
    rng = random.Random(seed)
    docs = []
    for i in range(n):
        ns = "ns%d" % rng.randrange(5)
        fields = {}
        if rng.random() >= missing_ratio:
            if rng.random() < hash_str_ratio:
                fields["hash"] = "h%08x" % rng.randrange(16 ** 8)
            else:
                fields["hash"] = rng.randrange(10 ** 9)
        docs.append({"put": "id:%s:term::t%d" % (ns, i), "fields": fields})
    return docs


def _make_para_docs(n, seed):
    rng = random.Random(seed)
    docs = []
    for i in range(n):
        ns = "ns%d" % rng.randrange(5)
        docs.append({
            "put": "id:%s:paragraph::p%d" % (ns, i),
            "fields": {"text": "x" * rng.randrange(1, 60)},
        })
    return docs


_EMPTY = _dump("empty.json", [])
_DOC_SMALL = _dump("doc_small.json", _make_doc_docs(3000, 0, ns_count=3, path_count=500))
_DOC_LARGE = _dump("doc_large.json", _make_doc_docs(30000, 1, ns_count=7, path_count=500000))
_DOC_DUPS = _dump("doc_dups.json", _make_doc_docs(20000, 2, ns_count=3, path_count=50))
_DOC_MIXED = _dump("doc_mixed.json", _make_doc_docs(25000, 3, ns_count=12, path_count=5000))
_TERM_LARGE = _dump("term_large.json", _make_term_docs(30000, 4))
_TERM_MISS = _dump("term_missing.json", _make_term_docs(15000, 5, missing_ratio=0.5, hash_str_ratio=0.5))
_PARA_LARGE = _dump("para_large.json", _make_para_docs(40000, 6))
_PARA_MED = _dump("para_medium.json", _make_para_docs(8000, 7))


def checks():
    return [
        ("empty-doc", lambda: (_EMPTY, "mynamespace", "doc")),
        ("empty-term", lambda: (_EMPTY, "mynamespace", "term")),
        ("unknown-type", lambda: (_DOC_SMALL, "mynamespace", "unknown")),
    ]


def cases():
    return [
        ("doc-small", lambda: (_DOC_SMALL, "mynamespace", "doc")),
        ("doc-large", lambda: (_DOC_LARGE, "mynamespace", "doc")),
        ("doc-dups", lambda: (_DOC_DUPS, "mynamespace", "doc")),
        ("doc-mixed", lambda: (_DOC_MIXED, "mynamespace", "doc")),
        ("term-large", lambda: (_TERM_LARGE, "mynamespace", "term")),
        ("term-missing-hash", lambda: (_TERM_MISS, "mynamespace", "term")),
        ("paragraph-large", lambda: (_PARA_LARGE, "mynamespace", "paragraph")),
        ("paragraph-medium", lambda: (_PARA_MED, "mynamespace", "paragraph")),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['doc-large', 'doc-mixed', 'term-large', 'doc-dups']
_KEEP_CHECKS = ['empty-doc', 'empty-term', 'unknown-type']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
