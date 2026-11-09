```python
import json
import random
from train import TrainDataset

_WORDS = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "search", "engine", "document", "query", "relevant", "ranking",
    "neural", "network", "embedding", "vector", "similarity", "index",
    "data", "science", "machine", "learning", "model", "training",
    "evaluation", "test", "validation", "performance", "metric",
]


def _random_text(rng, min_words, max_words):
    n = rng.randint(min_words, max_words)
    return " ".join(rng.choices(_WORDS, k=n))


def _ids(n_lines, n_unique, rng, prefix=None):
    if n_unique == n_lines:
        ids = list(range(n_lines))
        rng.shuffle(ids)
    else:
        ids = [rng.randrange(n_unique) for _ in range(n_lines)]
    if prefix:
        ids = [f"{prefix}{i:08d}" for i in ids]
    return ids


def _write_docs(path, n_lines, n_unique, seed, long_text=False, extra=True, prefix=None):
    rng = random.Random(seed)
    ids = _ids(n_lines, n_unique, rng, prefix)
    with open(path, "w") as f:
        for doc_id in ids:
            if long_text:
                text = _random_text(rng, 50, 200)
            else:
                text = _random_text(rng, 10, 50)
            rec = {"doc_id": doc_id, "text": text}
            if extra:
                rec["title"] = _random_text(rng, 3, 10)
                rec["url"] = f"http://example.com/{rng.randrange(10**6)}"
            f.write(json.dumps(rec) + "\n")


def _write_queries(path, n_lines, n_unique, seed, long_text=False, extra=True, prefix=None):
    rng = random.Random(seed + 1000)
    ids = _ids(n_lines, n_unique, rng, prefix)
    with open(path, "w") as f:
        for query_id in ids:
            if long_text:
                text = _random_text(rng, 30, 100)
            else:
                text = _random_text(rng, 5, 30)
            rec = {"query_id": query_id, "text": text}
            if extra:
                rec["user"] = f"user{rng.randrange(1000)}"
            f.write(json.dumps(rec) + "\n")


_CASE_FILES = {}


def _make_case(name, docs_lines, docs_unique, queries_lines, queries_unique, seed,
               long_text=False, extra=True, prefix=None):
    docs_path = WORKDIR / f"{name}_docs.jsonl"
    queries_path = WORKDIR / f"{name}_queries.jsonl"
    _write_docs(docs_path, docs_lines, docs_unique, seed, long_text, extra, prefix)
    _write_queries(queries_path, queries_lines, queries_unique, seed, long_text, extra, prefix)
    _CASE_FILES[name] = (docs_path, queries_path)


_make_case("balanced", 10000, 10000, 10000, 10000, 0)
_make_case("docs_heavy", 30000, 30000, 5000, 5000, 1)
_make_case("queries_heavy", 5000, 5000, 30000, 30000, 2)
_make_case("dup_docs", 20000, 1000, 5000, 5000, 3)
_make_case("dup_queries", 5000, 5000, 20000, 1000, 4)
_make_case("long_text", 5000, 5000, 5000, 5000, 5, long_text=True)
_make_case("sparse_fields", 15000, 15000, 15000, 15000, 6, extra=False)
_make_case("string_ids", 20000, 20000, 20000, 20000, 7, prefix="doc-")

# Small edge-case files for checks
_EMPTY_DOCS = WORKDIR / "check_empty_docs.jsonl"
_EMPTY_QUERIES = WORKDIR / "check_empty_queries.jsonl"
_EMPTY_DOCS.write_text("")
_EMPTY_QUERIES.write_text("")

_SINGLE_DOCS = WORKDIR / "check_single_docs.jsonl"
_SINGLE_QUERIES = WORKDIR / "check_single_queries.jsonl"
_SINGLE_DOCS.write_text(json.dumps({"doc_id": 1, "text": "hello"}) + "\n")
_SINGLE_QUERIES.write_text(json.dumps({"query_id": 1, "text": "world"}) + "\n")

_MISSING_DOCS = WORKDIR / "check_missing_docs.jsonl"
_MISSING_QUERIES = WORKDIR / "check_missing_queries.jsonl"
_MISSING_DOCS.write_text(json.dumps({"text": "no id"}) + "\n")
_MISSING_QUERIES.write_text("")


def checks():
    return [
        ("empty", lambda: (object.__new__(TrainDataset), _EMPTY_DOCS, _EMPTY_QUERIES)),
        ("single", lambda: (object.__new__(TrainDataset), _SINGLE_DOCS, _SINGLE_QUERIES)),
        ("missing-doc-id", lambda: (object.__new__(TrainDataset), _MISSING_DOCS, _MISSING_QUERIES)),
    ]


def cases():
    return [
        (name, lambda d=docs, q=queries: (object.__new__(TrainDataset), d, q))
        for name, (docs, queries) in _CASE_FILES.items()
    ]
```