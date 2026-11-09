```python
import json
import random
from train import TrainDataset


def _random_text(rng, length):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    return "".join(rng.choices(chars, k=length))


def _make_dataset(name, n_docs, n_queries, doc_text_len, query_text_len, seed):
    rng = random.Random(seed)
    doc_ids = [f"doc_{i}" for i in range(n_docs)]
    docs = []
    for did in doc_ids:
        docs.append({"doc_id": did, "text": _random_text(rng, doc_text_len)})

    queries = []
    for i in range(n_queries):
        qid = f"query_{i}"
        pos = rng.choice(doc_ids)
        neg = rng.choice(doc_ids)
        while neg == pos:
            neg = rng.choice(doc_ids)
        queries.append({
            "query_id": qid,
            "query": _random_text(rng, query_text_len),
            "positives": [pos],
            "negatives": [neg],
        })

    doc_path = WORKDIR / f"{name}_docs.jsonl"
    query_path = WORKDIR / f"{name}_queries.jsonl"

    with open(doc_path, "w") as f:
        for d in docs:
            f.write(json.dumps(d) + "\n")
    with open(query_path, "w") as f:
        for q in queries:
            f.write(json.dumps(q) + "\n")

    return TrainDataset(str(doc_path), str(query_path))


_CASES_SPEC = [
    ("small-short", 100, 100, 10, 10, 0, 0),
    ("medium", 1000, 1000, 100, 50, 1, 500),
    ("large-docs", 10000, 1000, 100, 50, 2, 0),
    ("large-queries", 1000, 10000, 50, 20, 3, 7500),
    ("long-text", 1000, 1000, 5000, 1000, 4, 999),
    ("many-queries", 5000, 5000, 200, 100, 5, 2500),
    ("huge", 20000, 20000, 50, 30, 6, 0),
    ("mixed", 5000, 5000, 1000, 200, 7, 4999),
]

_DATASETS = {}
for name, n_docs, n_queries, doc_len, query_len, seed, item in _CASES_SPEC:
    _DATASETS[name] = _make_dataset(name, n_docs, n_queries, doc_len, query_len, seed)


def checks():
    def _empty_ds():
        doc_path = WORKDIR / "check_empty_docs.jsonl"
        query_path = WORKDIR / "check_empty_queries.jsonl"
        doc_path.write_text("")
        query_path.write_text("")
        return TrainDataset(str(doc_path), str(query_path))

    def _empty_pos_ds():
        doc_path = WORKDIR / "check_empty_pos_docs.jsonl"
        query_path = WORKDIR / "check_empty_pos_queries.jsonl"
        doc_path.write_text(json.dumps({"doc_id": "d0", "text": "hello"}) + "\n")
        query_path.write_text(json.dumps({
            "query_id": "q0",
            "query": "hi",
            "positives": [],
            "negatives": ["d0"],
        }) + "\n")
        return TrainDataset(str(doc_path), str(query_path))

    return [
        ("empty-dataset", lambda: (_empty_ds(), 0)),
        ("empty-positives", lambda: (_empty_pos_ds(), 0)),
        ("index-out-of-range", lambda: (_empty_ds(), 10)),
    ]


def cases():
    result = []
    for name, n_docs, n_queries, doc_len, query_len, seed, item in _CASES_SPEC:
        ds = _DATASETS[name]
        result.append((name, lambda ds=ds, item=item: (ds, item)))
    return result
```