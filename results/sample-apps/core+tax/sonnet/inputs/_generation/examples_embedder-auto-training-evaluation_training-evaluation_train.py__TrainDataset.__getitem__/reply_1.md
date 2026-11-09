```python
import json
import random

from train import TrainDataset


_WORDS = [
    "retrieval", "embedding", "sentence", "vector", "search", "model",
    "training", "evaluation", "document", "passage", "question", "answer",
    "neural", "network", "transformer", "encoder", "corpus", "index",
    "similarity", "distance", "query", "context", "token", "attention",
    "language", "learning", "semantic", "ranking", "relevant", "candidate",
]


def _text(rng, n_words):
    return " ".join(rng.choice(_WORDS) for _ in range(n_words))


def _build_dataset(name, n_docs, n_queries, pos_len, neg_len, seed,
                   doc_words=30, query_words=10):
    """Write the documents/queries jsonl files the way the repo's caller does
    and build a TrainDataset from them."""
    folder = WORKDIR / name
    folder.mkdir(parents=True, exist_ok=True)
    docs_path = folder / "documents.jsonl"
    queries_path = folder / "queries.jsonl"

    rng = random.Random(seed)
    with open(docs_path, "w") as fh:
        for i in range(n_docs):
            fh.write(json.dumps({"doc_id": f"doc-{i}",
                                 "text": _text(rng, doc_words)}) + "\n")

    with open(queries_path, "w") as fh:
        for i in range(n_queries):
            query = {
                "query_id": f"query-{i}",
                "query": _text(rng, query_words),
                "positives": [f"doc-{rng.randrange(n_docs)}" for _ in range(pos_len)],
                "negatives": [f"doc-{rng.randrange(n_docs)}" for _ in range(neg_len)],
            }
            fh.write(json.dumps(query) + "\n")

    return TrainDataset(str(docs_path), str(queries_path))


def _thunk_for(dataset, item):
    """__getitem__ rotates the accessed query's positives/negatives lists, so the
    thunk restores the canonical order before every call to keep each call
    identical."""
    query = dataset.queries[dataset.queries_ids[item]]
    original_positives = list(query["positives"])
    original_negatives = list(query["negatives"])

    def thunk():
        query["positives"][:] = original_positives
        query["negatives"][:] = original_negatives
        return (dataset, item)

    return thunk


def checks():
    empty = _build_dataset("check-empty", 3, 0, 0, 0, 10)
    single = _build_dataset("check-single", 4, 1, 1, 1, 11)
    multi = _build_dataset("check-multi", 6, 3, 2, 3, 12)

    return [
        ("empty-queries", lambda: (empty, 0)),        # no queries -> IndexError
        ("single-item", _thunk_for(single, 0)),       # one query, one pos/neg
        ("negative-index", _thunk_for(multi, -1)),    # last query via negative index
    ]


def cases():
    typical = _build_dataset("case-typical", 6000, 6000, 1, 1, 0)
    first = _build_dataset("case-first", 5000, 5000, 1, 1, 1)
    last = _build_dataset("case-last", 5000, 5000, 1, 1, 2)
    many_neg = _build_dataset("case-many-neg", 800, 200, 1, 500, 3)
    many_pos = _build_dataset("case-many-pos", 800, 200, 500, 1, 4)
    balanced = _build_dataset("case-balanced", 1500, 400, 120, 120, 5)
    large = _build_dataset("case-large", 15000, 15000, 1, 1, 6)
    dup = _build_dataset("case-dup-neg", 3000, 2000, 1, 40, 7)

    return [
        ("typical-mid", _thunk_for(typical, 3000)),
        ("first-index", _thunk_for(first, 0)),
        ("last-index", _thunk_for(last, len(last.queries_ids) - 1)),
        ("long-negatives", _thunk_for(many_neg, 100)),
        ("long-positives", _thunk_for(many_pos, 100)),
        ("balanced-long", _thunk_for(balanced, 200)),
        ("large-corpus", _thunk_for(large, 7500)),
        ("duplicate-negatives", _thunk_for(dup, 1000)),
    ]
```