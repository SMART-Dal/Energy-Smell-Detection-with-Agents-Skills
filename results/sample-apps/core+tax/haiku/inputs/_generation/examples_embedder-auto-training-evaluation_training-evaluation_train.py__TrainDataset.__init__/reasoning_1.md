We need write inputs. Function reads two JSONL files: documents with doc_id, queries with query_id, builds dicts. Need import train. But train imports sentence_transformers and torch, might not be installed? The task says import repository modules exactly as shown. But sentence_transformers may not be available. Hmm. We need consider. The function under test is TrainDataset.__init__ in train.py. Importing train triggers sentence_transformers import. If not installed, cannot run. But likely environment has dependencies? The instruction says use only stdlib, repo itself and packages repo already imports. sentence_transformers is imported by module. We can't avoid. If not available, CANNOT RUN? But the task expects us to write. Typically these tasks environment includes dependencies. Let's assume available.

We need build files under WORKDIR. Function opens documents and queries. It reads all lines, json.loads, builds dict keyed by doc_id/query_id. Need realistic data. Docs likely have fields doc_id, text, maybe title. Queries query_id, text. We'll generate JSON lines.

Need 8 cases with varying sizes and duplicates. Function work ~ parse JSON + dict insertion. 1ms-200ms. Need large enough. JSON parsing ~ maybe 1M lines too slow. Keep under 100MB and 1M values. Let's target documents 5k-50k lines, queries 1k-20k. Each line maybe 200 bytes. 50k * 200 = 10MB. Parsing 50k lines maybe 50ms. Good.

Need avoid duplicates? Function dict overwrites duplicates, that's a path. Cases with duplicates. Also keys order. Queries_ids list from keys. Output? __init__ returns None, but we compare instance attributes? The runner compares outputs. Since __init__ returns None, but maybe it compares the instance state? It says output compared in full. For __init__ returning None, they might compare instance attributes? The harness likely captures return value only. But we just need cases.

Need checks: 2-3 small edge inputs, may raise. Empty files, missing doc_id? Should run on original without raising? Checks only identical behaviour, may raise. We can include empty files, one document one query, maybe invalid JSON? But "may raise" means okay. But better produce valid.

Need thunks: create new instance? The method is called as TrainDataset.__init__(instance, documents, queries). So thunk must build instance (without calling __init__? We can use object.__new__(TrainDataset) or TrainDataset.__new__(TrainDataset)). Then return (instance, docs_path, queries_path). But note each call mutates instance, setting attributes. Since thunk creates a fresh instance each time, fine. But building instance cheap. However if we use TrainDataset.__new__(TrainDataset), no __init__ called. Good. Alternatively create a dummy instance via object.__new__. Need not call __init__.

Files: create once at module level under WORKDIR. Function only reads, does not write. So same files can be reused. Good.

Need import train. The module path: examples/embedder-auto-training-evaluation/training-evaluation/train.py. We need add that directory to sys.path? The task says import as `from train import TrainDataset`. We can do `import sys; sys.path.insert(0, str(WORKDIR?))`? Actually the repo file location. The harness likely sets up path? We need ensure import works. We can use importlib? But instructions: "Import the repository's modules exactly as shown in the task." They show `from train import TrainDataset`. We can do that. But if directory not on sys.path, we need add. The task says "Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk." The repository's main likely runs from that directory. We can add path at module level. But we don't know absolute path of repo. The harness likely has cwd at repo root? We can compute path relative to this file? Our code is in some file, not necessarily in repo. But WORKDIR is provided. Hmm.

In these tasks, typically the repository is installed or on sys.path. The import `from train import TrainDataset` should work if the harness adds the target directory. They gave import exactly. We'll just do `from train import TrainDataset`. If it fails, can't run. But maybe we can robustly add path? We don't know where repo is. Could search? Not allowed? We can use `os.path`? The task says everything you can know is in task. We can't know repo path. So just import.

But importing train imports sentence_transformers. If not available, error. We'll assume.

Now design 8 cases. Need distinct labels. Workloads:

- "small-docs-large-queries": docs 2000, queries 20000
- "large-docs-small-queries": docs 20000, queries 2000
- "balanced-medium": 10000 docs, 10000 queries
- "many-duplicates-docs": 15000 lines but only 1000 unique doc_ids
- "many-duplicates-queries": 15000 lines but 1000 unique query_ids
- "large-docs": 50000 docs, 5000 queries
- "large-queries": 5000 docs, 50000 queries
- "mixed-fields": docs with extra fields, queries with extra fields, varying text lengths.

Need ensure each call ~1-200ms. Parsing 50k lines maybe 50-100ms. Good. Total build under 10s. Generating 8 files maybe total 200k lines, fine.

Need use random.Random(0) for generation. But module-level generation with fixed seed. For each case, generate separate files. We can write a helper to generate.

Fields: doc_id int or string? In repo likely doc_id integer. Query query_id integer. We'll use ints. Documents may have "doc_id", "text", "title". Queries "query_id", "text". The function only uses doc_id/query_id. Extra fields add parse work.

Need avoid uniform patterns. Use random strings, varying lengths, duplicates.

For duplicates: when generating, choose doc_id from small range so duplicates. But need line count. We'll generate.

Important: function reads file.readlines() then iterates. So file size matters. Keep under 100MB. 50k lines * maybe 300 bytes = 15MB. 8 cases total maybe 100MB if all in memory? Files on disk. The instruction says keep data in memory under 100MB. Files on disk can be larger but okay. We'll keep total lines ~ 200k, each ~200 bytes -> 40MB disk. Fine.

Need checks: 2-3 small edge inputs. Could use empty files, one doc one query, maybe file with duplicate ids. They may raise? We'll make valid. Also maybe a file with missing doc_id? That would raise KeyError. But checks may raise. But better to have one that raises? The instruction says "These may raise." It's okay. But to be safe, include valid small and one invalid. However if the original raises, the modified should too. We'll include:
- "empty": empty docs and queries files.
- "single": one doc, one query.
- "missing-key": a document line without doc_id -> KeyError. This tests edge. But if harness expects no raise? It says may raise. So fine.

But creating files for checks: can create at module level too. Need thunk returns instance, paths. For empty files, we can create empty files. For single, write one line each. For missing-key, write line without doc_id.

Need instance creation. `TrainDataset.__new__(TrainDataset)` works? For a subclass of torch Dataset, __new__ is object.__new__? Actually torch Dataset is a simple class, no __new__. So `TrainDataset.__new__(TrainDataset)` returns instance without __init__. Good. But if Dataset has __new__? likely not. Safer: `object.__new__(TrainDataset)`. That works for any normal class. Use `object.__new__(TrainDataset)`.

Thunk: `lambda: (object.__new__(TrainDataset), _DOCS_CASE1, _QUERIES_CASE1)`. But note the method is called as `TrainDataset.__init__(instance, documents, queries)`. The harness will call function with args. So thunk returns (instance, docs, queries). Good.

Need module-level file creation. Use WORKDIR. WORKDIR is a pathlib.Path provided. We can use it. Need not define.

Let's write code.

Potential issue: train.py may have imports that fail. If sentence_transformers not installed, cannot run. But we can't fix. Could we import the class without executing module? No, must import. The task says import exactly. So we'll do.

Let's craft generation.

Helper:

```python
import json, random, itertools
from train import TrainDataset

def _write_jsonl(path, records):
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
```

But generating records in memory could be large. Better stream to file. Use generator functions.

For docs:

```python
def _make_docs(path, n, unique_ids=None, seed=0, extra_fields=True):
    rng = random.Random(seed)
    if unique_ids is None:
        unique_ids = n
    with open(path, "w") as f:
        for i in range(n):
            doc_id = rng.randrange(unique_ids) if unique_ids < n else i
            # but if unique_ids < n, duplicates. If unique_ids == n, use i to ensure all unique? Or rng? Use i for unique.
            rec = {"doc_id": doc_id, "text": _random_text(rng, 20, 200)}
            if extra_fields:
                rec["title"] = _random_text(rng, 5, 50)
                rec["url"] = f"http://example.com/{rng.randrange(10**6)}"
            f.write(json.dumps(rec) + "\n")
```

But for unique_ids < n, doc_id random in range, duplicates. For unique, use i. Need not uniform. We can shuffle? Not needed.

Random text: generate from words to vary length. Use rng.choices? Simpler: `" ".join(rng.choices(_WORDS, k=rng.randint(5, 30)))`. But building large strings for 50k lines * 30 words might be slow but okay. Use a fixed vocabulary of 100 words.

Queries similar.

Need ensure each case different sizes and distributions. Let's define cases:

1. "balanced-10k": docs 10000 unique, queries 10000 unique, seed 0.
2. "docs-heavy-50k": docs 50000 unique, queries 5000 unique, seed 1.
3. "queries-heavy-50k": docs 5000 unique, queries 50000 unique, seed 2.
4. "dup-docs-20k-1k": docs 20000 lines, 1000 unique, queries 5000 unique, seed 3.
5. "dup-queries-20k-1k": docs 5000 unique, queries 20000 lines, 1000 unique, seed 4.
6. "long-text": docs 10000 with long text (100-500 words), queries 10000 with long text, seed 5.
7. "sparse-fields": docs 15000 with only doc_id and text (no extra), queries 15000 with only query_id and text, seed 6.
8. "mixed-ids": docs 20000 with doc_id as strings? But function uses doc_id as key, can be string. Queries query_id as strings. Realistic? Maybe. Use string ids with varying patterns. docs 20000 unique string ids, queries 20000 unique string ids, seed 7.

Need ensure each call ~1-200ms. Parsing 50k lines with long text may be >200ms? Let's estimate: json.loads per line ~ 5-10 microseconds for small, 20-50 for long. 50k * 20us = 1s. Too slow. Need keep under 200ms. So limit total lines. For long text, use fewer lines. Let's target max 30k lines per file. 30k * 20us = 600ms. Hmm. Actually Python json.loads is ~1-2 us for small dict? Let's roughly: 100k json lines ~ 0.1-0.2s. So 50k ~ 0.05-0.1s. With long text maybe 0.2s. We can test mentally. Better keep max 30k lines for long text. The instruction says one call roughly 1 ms to 200 ms. We can aim 10k-30k lines. Let's adjust:

1. balanced: docs 10000, queries 10000 -> total 20k lines. ~20ms.
2. docs-heavy: docs 30000, queries 5000 -> 35k lines. ~35ms.
3. queries-heavy: docs 5000, queries 30000 -> 35k lines.
4. dup-docs: docs 20000, queries 5000 -> 25k.
5. dup-queries: docs 5000, queries 20000 -> 25k.
6. long-text: docs 5000, queries 5000 with long text -> 10k lines but each large. ~50ms.
7. sparse: docs 15000, queries 15000 -> 30k.
8. string-ids: docs 20000, queries 20000 -> 40k.

Total lines ~ 200k. Build time: generating random text for 200k lines maybe few seconds. Under 10s.

Need ensure file sizes under 100MB. Long text: 10k lines * maybe 1KB = 10MB. Others ~ 200 bytes * 200k = 40MB. Fine.

Now checks: small files. Create at module level.

Implementation details:

- `_WORDS` list of maybe 50 words. Use `random.Random(seed)`.
- For long text, use more words per line (e.g., 50-200 words). That's 500-2000 chars. 10k lines -> 5-20MB. Good.

Need avoid patterns that simple trick could exploit. Random text and ids. For unique ids, using sequential i is a pattern but realistic? The repo likely has sequential ids. But instruction says avoid uniformity unless repo passes. The repo likely passes generated data? We don't know. To be safe, use random unique ids by shuffling range. For n unique, generate list(range(n)) and shuffle with rng. That's fine. For large n, shuffling 50k is cheap. Then write in that order. For duplicates, random ids.

Let's write helper:

```python
def _random_text(rng, min_words, max_words):
    n = rng.randint(min_words, max_words)
    return " ".join(rng.choice(_WORDS) for _ in range(n))
```
Using rng.choice in loop is slow for many. Use `rng.choices(_WORDS, k=n)` faster. Available Python 3.6+. Good.

```python
def _make_docs(path, n_lines, n_unique, seed, long_text=False, extra=True, string_ids=False):
    rng = random.Random(seed)
    if n_unique == n_lines:
        ids = list(range(n_lines))
        rng.shuffle(ids)
    else:
        ids = None
    with open(path, "w") as f:
        for i in range(n_lines):
            if ids is not None:
                doc_id = ids[i]
            else:
                doc_id = rng.randrange(n_unique)
            if string_ids:
                doc_id = f"doc-{doc_id:08d}-{rng.randrange(1000):03d}"  # but if unique, this may not be unique? For string unique case, use i.
            # Actually for string ids, we need unique. Let's handle separately.
            ...
```

Simplify: create separate helpers for docs and queries, with parameter `unique` and `string_ids`. For string unique, use f"doc-{i:08d}" but shuffle order? We can generate list of strings and shuffle.

Let's design generic:

```python
def _ids(n_lines, n_unique, rng, prefix=None):
    if n_unique == n_lines:
        ids = list(range(n_lines))
        rng.shuffle(ids)
    else:
        ids = [rng.randrange(n_unique) for _ in range(n_lines)]
    if prefix:
        ids = [f"{prefix}{i:08d}" for i in ids]
    return ids
```

But for string unique, if we convert after shuffle, still unique. For duplicates, prefix + number, duplicates preserved. Good.

Then write:

```python
def _write_docs(path, n_lines, n_unique, seed, long_text=False, extra=True, prefix=None):
    rng = random.Random(seed)
    ids = _ids(n_lines, n_unique, rng, prefix)
    with open(path, "w") as f:
        for doc_id in ids:
            rec = {"doc_id": doc_id, "text": _random_text(rng, 10, 50) if not long_text else _random_text(rng, 50, 200)}
            if extra:
                rec["title"] = _random_text(rng, 3, 10)
                rec["url"] = f"http://example.com/{rng.randrange(10**6)}"
            f.write(json.dumps(rec) + "\n")
```

Similarly queries.

Need ensure for long_text, generating 5000 lines with 200 words each: 1M words, rng.choices fast. Fine.

Now module-level create files for each case. We need names unique. Use WORKDIR / "docs_case1.jsonl" etc.

We can create a function to create all case files and return dict of paths. But module-level code runs once. We'll create files at module level.

```python
_CASE_FILES = {}
def _make_case(name, docs_lines, docs_unique, queries_lines, queries_unique, seed, long_text=False, extra=True, prefix=None):
    docs_path = WORKDIR / f"{name}_docs.jsonl"
    queries_path = WORKDIR / f"{name}_queries.jsonl"
    _write_docs(docs_path, ...)
    _write_queries(queries_path, ...)
    _CASE_FILES[name] = (docs_path, queries_path)
```

Then call for 8 cases.

But careful: module-level code runs when imported. It may take a few seconds. That's fine (setup not timed). But total build under 10s. We'll keep it efficient.

Need checks files: create empty, single, missing-key. For missing-key, write a JSON line without doc_id. That will raise KeyError on original. Good.

For checks, we need thunks. For empty, docs and queries empty. For single, one doc with doc_id, one query with query_id. For missing-key, docs file has line `{"text": "no id"}`. Queries empty or valid. It will raise KeyError. That's okay.

Now thunks: For each case, `lambda: (object.__new__(TrainDataset), _CASE_FILES["case1"][0], _CASE_FILES["case1"][1])`. But lambda captures by reference? We can use default args to avoid late binding. `lambda d=_CASE_FILES["case1"][0], q=...: (object.__new__(TrainDataset), d, q)`. Good.

But note: `object.__new__(TrainDataset)` creates instance. The function sets attributes. No issue.

Need import `TrainDataset` from train. The module `train` may have a `main()` but not executed. Good.

Potential issue: `TrainDataset.__init__` is called as unbound method with instance. The harness will call `TrainDataset.__init__(instance, docs, queries)`. Our thunk returns instance, docs, queries. Perfect.

Now, the output format: exactly one python block. We'll write complete source.

Let's double-check for any missing imports. `json`, `random`, `pathlib`? WORKDIR is provided, no need import pathlib. We use `WORKDIR` directly. We use `object.__new__`. We use `TrainDataset` imported. We use `json.dumps`. Good.

We should not import `call` unless needed. Not needed.

Need ensure files are created under WORKDIR. Yes.

Let's write the code.

One more thing: The instruction says "For keyword arguments the thunk returns call(...)". We don't need.

Now, potential issue: `TrainDataset` inherits from `Dataset` which may have `__slots__`? Unlikely. `object.__new__(TrainDataset)` works.

Let's write.

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
```

Now create cases. We'll define a function `_make_case` that writes and stores.

```python
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
```

Wait for string_ids, prefix="doc-" for both docs and queries. That's fine, ids are strings. But query prefix should be "query-"? Not important. The function only uses key. But maybe realistic to have different. We can pass prefix for docs and queries separately. Our _make_case uses same prefix for both. That's okay, but maybe better to have separate. Not critical. We can modify _make_case to accept doc_prefix and query_prefix. But simple is fine. Actually if both have same prefix, doc_id and query_id values might overlap but they are in separate dicts. No issue.

However, for string_ids, `_ids` with prefix converts integer to string with 8 digits. For n=20000, unique. Good.

Now checks. Create files:

```python
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
```

Now checks function:

```python
def checks():
    return [
        ("empty", lambda: (object.__new__(TrainDataset), _EMPTY_DOCS, _EMPTY_QUERIES)),
        ("single", lambda: (object.__new__(TrainDataset), _SINGLE_DOCS, _SINGLE_QUERIES)),
        ("missing-doc-id", lambda: (object.__new__(TrainDataset), _MISSING_DOCS, _MISSING_QUERIES)),
    ]
```

Cases function:

```python
def cases():
    result = []
    for name, (docs, queries) in _CASE_FILES.items():
        result.append((name, lambda d=docs, q=queries: (object.__new__(TrainDataset), d, q)))
    return result
```

But dict order in Python 3.7+ is insertion order. We inserted 8. Good. But the instruction says exactly 8 measured inputs. We have 8. Good.

Potential issue: The lambda default arguments capture docs and queries correctly. Good.

Now, one concern: The function `TrainDataset.__init__` calls `open(documents, "r")`. Our paths are pathlib.Path objects. `open` accepts Path. Good.

Another concern: The module `train` may not be importable because it's in a nested directory. The task says import it as `from train import TrainDataset`. We'll trust.

But what if `sentence_transformers` is not installed? Then import fails. Could we avoid importing the whole module by loading just the class? The instruction says import exactly as shown. We cannot mock. If it fails, it's CANNOT RUN. But we are to write code. I'll assume it's available.

Let's also consider if `TrainDataset` has `__init__` that sets attributes. We create instance via `object.__new__`. That's fine.

Now, check if any case might take >1s. Long text 5000 docs + 5000 queries with 200 words each: 5000 * 200 = 1M words, json string maybe 5MB. Parsing 5000 lines of 1KB each ~ 5MB. json.loads 5000 times ~ maybe 50ms. Good.

Total build time: generating 200k lines with random text. `_random_text` uses `rng.choices` which is fast. 200k * 30 words = 6M words. Might take ~2-3 seconds. Under 10s. Good.

Memory: We stream to files, so memory low. The function itself reads all lines into memory via `file.readlines()`. For 30k lines ~ 6MB, fine. For long text 5000 lines ~ 5MB. Fine.

Output: `__init__` returns None. The harness compares outputs. For cases, it will compare None for all. But it also checks arguments unchanged? The instance is mutated, but that's the point. The harness likely captures the instance state? The instruction says "The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them". For `__init__`, the instance is an argument and it changes. That's expected? The harness might compare the instance before and after? It says "rendered before and after each call to see whether it changed them". For a method that mutates self, it will change. But that's the function's purpose. The harness likely handles this by comparing the instance after? Actually the instruction says "Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values." This is a warning that if the function mutates its arguments, the harness will render them. For `__init__`, the instance is an argument and it gets attributes set. That's a change. But that's inherent. The instance initially has no attributes, after has documents, queries, queries_ids. The harness will render both. That's fine as long as the data is under 1M values. Our documents/queries dicts have up to 30k entries. Each entry is a dict with a few fields. Total values maybe 30k * 5 = 150k. Under 1M. Good.

But wait: The harness calls the function many times. Each thunk creates a fresh instance. So no carry-over. Good.

Now, we need ensure that for each case, the function runs to completion without raising. Our files are valid JSON lines with required keys. For dup cases, duplicates cause overwrites but no error. For string_ids, doc_id is string, fine. For sparse_fields, extra=False, still has doc_id and text. Good.

One more thing: The function uses `document["doc_id"]` and `query["query_id"]`. Our keys are correct.

Now, we should ensure that the checks with missing doc_id raises KeyError. That's fine.

Let's produce final code. We'll include comments? Not necessary. But clear.

Check for any syntax errors. `_CASE_FILES` created. `_make_case` uses `WORKDIR` which is provided globally. Good.

One potential issue: `WORKDIR` might not exist? It's provided as a pathlib.Path, likely exists. We can assume.

Another: `rng.choices` is available in Python 3.6+. The environment likely modern.

Now, the output must be exactly one python block. We'll write.

Let's finalize.