You are a performance testing expert. You will write the inputs for an energy measurement of one Python function from a real repository. We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs.

# What to write
Python source defining two functions, `checks()` and `cases()`. Each returns a list of `(label, thunk)` pairs with distinct labels. A thunk takes no arguments and returns a tuple of positional arguments for the function, e.g. `lambda: (rows, 3)`. For keyword arguments the thunk returns `call(...)`, e.g. `lambda: call(rows, sep=",")`; `call` is provided, do not import or define it. A method is called as a plain function: the thunk builds the instance and passes it as the first argument (a classmethod gets its class there, a staticmethod nothing; the task says which).
**The thunk returns the arguments; it never calls the function under test.** We call the function with them, and time only that call.

# Instructions
1. **Setup is never timed**: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed.

2. **`cases()`: exactly 8 measured inputs.** We run them on the original function and keep the 4 that do the most work.
    - Define a real workload: the kind of data this function gets in this repository (see where the repository calls it). Use realistic scale and complexity, and a fixed random seed (`random.Random(0)`) when generating data.
    - Generate stressful inputs: complex, time-consuming, as diverse as possible. Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths.
    - Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes.
    - One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped. Keep the data in memory under about 100 MB, and building all inputs under about 10 s.
    - The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values.
    - Every case must run to completion on the original function without raising.

3. **`checks()`: 2 or 3 small edge inputs** (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise.

4. **Build real inputs; never replace code.** No mocks, no monkeypatching, no `unittest.mock`, no assigning functions or lambdas to attributes, and no subclass that overrides a method of a repository or library class -- a subclass whose `get` returns canned data instead of making the request is a mock too. Setting data (a module's configuration, an object's fields) to build an input is fine. No network access, no subprocesses. Do not fake the environment either: no stand-in programs on `PATH`, no fake system files.
    - Module globals the function reads must be set on the repository's own module (`import pricing; pricing.args = ...`, `hyperlink.slugs.update(...)`); a variable of the same name in your source is a different variable and the function never sees it.
    - Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk.

5. **Files**: if the function reads files, create them under `WORKDIR` (a provided `pathlib.Path`; do not define it), in module-level code or in the thunk. Anything the function writes must go under `WORKDIR` too.

6. **Same work on every call**: the call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts. So keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy (`list(data)`, `dict(data)`) if the function changes it (adds to a dict, sorts or fills a list in place). Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys (e.g. with `itertools.count()`), so every call takes the same path. If it creates files, have the thunk remove them first. No time-dependent or unseeded random behaviour.

7. Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports. Everything you can know about the repository is in the task: do not try to recall its code from memory, and build the inputs from the classes and functions shown there.

8. **If the function cannot run here at all** -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`. A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer.

Decide on the inputs and write the code: simple inputs that run are better than clever ones that do not.

# Output format
Exactly one ```python block holding the complete source. An example for a function `summarize(rows, top=10)`:
```python
import random

def _rows(n, columns, seed):
    rng = random.Random(seed)
    return [{f"c{j}": rng.randint(0, 10**6) for j in range(columns)} for _ in range(n)]

def checks():
    return [
        ("empty",      lambda: ([],)),                            # summarize([])
        ("none-value", lambda: ([{"c0": None}],)),
    ]

def cases():
    return [
        ("typical",    lambda: (_rows(2_000, 4, 0),)),            # summarize(rows)
        ("top-100",    lambda: call(_rows(5_000, 4, 1), top=100)), # summarize(rows, top=100)
        # ... 8 in total
    ]
```
A second example, for a method `Index.lookup(self, words)` of `search/index.py`. The instance is built in the thunk and passed first; the vocabulary file it reads is created under `WORKDIR`; a module setting it reads is set on the repository's own module; and because it records the words it has seen in `self.seen`, every thunk call gets words of its own, so that every call takes the same path:
```python
import itertools
import random
import search.index
from search.index import Index

search.index.CASE_SENSITIVE = False                  # a setting the method reads: data, set on its module
_VOCAB = WORKDIR / "vocab.txt"                       # a file it reads
_VOCAB.write_text("\n".join(f"w{i}" for i in range(50_000)))
_batch = itertools.count()

def _words(n, hit_ratio, seed):
    rng = random.Random(seed)
    b = next(_batch)                                 # fresh misses for every thunk call
    return [f"w{rng.randrange(50_000)}" if rng.random() < hit_ratio else f"x{b}_{i}"
            for i in range(n)]

def checks():
    return [("no-words", lambda: (Index(_VOCAB), []))]

def cases():
    return [
        ("mostly-hits",   lambda: (Index(_VOCAB), _words(20_000, 0.9, 0))),
        ("mostly-misses", lambda: (Index(_VOCAB), _words(20_000, 0.1, 1))),
        # ... 8 in total
    ]
```


=== USER ===

Repository: sample-apps
Function under test: `inference` in `examples/in-context-learning/categorize_group.py`
Import it as `from categorize_group import inference`.

## The function
```python
def inference(text):
    """
    Fetch results from Vespa with different rank profiles.
    For simplicity, all queries here parse a result from a grouping expression,
    but queries can group on the label or not:

        To run without grouping the result on label (i.e. no result diversity), use
            all(group(1) max(1) each(max(10) each(output(summary()))))
        This means, all in _one_ group, with 10 hits total.

        To run _with_ grouping on the label, use
            all(group(label) max(10) each(max(2) each(output(summary()))))
        Here, two examples per label.

    {targetHits:10} for the NN operator should be large enough for the expected set of examples returned.

    Set the correct rank-profile in the ranking query parameter.
    The rank-profiles are configured in train.sd.

    timeout is set unusually high here, for laptop experiments.

    Note that the hybrid rank-profiles need
        userQuery() OR ({targetHits:10}nearestNeighbor ...)
    to generate rank scores from both operators.

    When experimenting with different embedders, make sure to set the name in _both_ the ranking profile and
    the query ranking feature like
        'input.query(query_embedding)': 'embed(arctic, @query)'
    Here, the "arctic" embedder model is used, also see services.xml configuration for configuring this.

    See start of file for how to configure the LLM client, opanAI/local / which local model to use.
    Remember to start ollama with correct model, too.

    :param text:    User query
    :return:        Array of examples in (text, relevance, label) tuples
    """

    query_request_bm25_group_20 = {
        'yql': 'select * from sources * where userQuery() limit 0 | all(group(label) max(10) each(max(2) each(output(summary()))))',
        'query': text,
        'timeout': '30s',
        'ranking': 'bm25'
    }
    query_request_bm25_no_group_10 = {
        'yql': 'select * from sources * where userQuery() limit 0 | all(group(1) max(1) each(max(10) each(output(summary()))))',
        'query': text,
        'timeout': '30s',
        'ranking': 'bm25'
    }
    query_request_hybrid_e5_no_group_10_normalized_bm25 = {
        'yql': 'select * from sources * where (userQuery() OR ({targetHits:10}nearestNeighbor(doc_embedding_e5, query_embedding) )) limit 0 | all(group(1) max(1) each(max(10) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'hybrid_e5_normalized_bm25'
    }
    query_request_sim_e5_no_group_10 = {
        'yql': 'select * from sources * where ({targetHits:10}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(1) max(1) each(max(10) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_arctic_no_group_10 = {
        'yql': 'select * from sources * where ({targetHits:10}nearestNeighbor(doc_embedding_arctic, query_embedding)) limit 0 | all(group(1) max(1) each(max(10) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(arctic, @query)',
        'timeout': '30s',
        'ranking': 'sim_arctic'
    }
    query_request_sim_e5_no_group_5 = {
        'yql': 'select * from sources * where ({targetHits:5}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(1) max(1) each(max(5) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_e5_no_group_2 = {
        'yql': 'select * from sources * where ({targetHits:2}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(1) max(1) each(max(2) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_e5_no_group_15 = {
        'yql': 'select * from sources * where ({targetHits:15}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(1) max(1) each(max(15) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_e5_no_group_20 = {
        'yql': 'select * from sources * where ({targetHits:20}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(1) max(1) each(max(20) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_e5_group_10 = {
        'yql': 'select * from sources * where ({targetHits:100}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(label) max(10) each(max(1) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_e5_group_20 = {
        'yql': 'select * from sources * where ({targetHits:100}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(label) max(10) each(max(2) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request_sim_e5_group_30 = {
        'yql': 'select * from sources * where ({targetHits:100}nearestNeighbor(doc_embedding_e5, query_embedding)) limit 0 | all(group(label) max(10) each(max(3) each(output(summary()))))',
        'query': text,
        'input.query(query_embedding)': 'embed(e5, @query)',
        'timeout': '30s',
        'ranking': 'sim_e5'
    }
    query_request = query_request_bm25_no_group_10
    response = requests.post(f"http://localhost:8080/search/", json=query_request)
    if response.ok:
        return parse_vespa_group_response(response.json())
    else:
        print("Search request failed with response " + str(response.json()))
        return []
```

## Imports of its module
```python
from datasets import load_dataset
import requests
from openai import OpenAI
import time
```

## Definitions it uses from the same module
```python
def parse_vespa_group_response(response):
    """
    Parse a Vespa Query into an array of (text, relevance, label) tuples
    :param response:    A JSON Query response in https://docs.vespa.ai/en/reference/default-result-format.html
    :return:            Array of examples in (text, relevance, label) tuples
    """
    result = []
    groups = response['root'].get('children', []).pop().get('children', []).pop().get('children', [])
    for group in groups:
        hits = group.get('children', [])
        for hit in hits.pop().get('children', []):
            label = hit['fields']['label']
            text = hit['fields']['text']
            relevance = hit['relevance']
            result.append((text, relevance, label))
    return result
```

## Everything else its module defines (headers only)
```python
def timer_decorator(func):
def get_label(text, examples):
def get_label_from_retrieval(candidates):
```

## Where the repository calls it or builds its class
```python
# examples/in-context-learning/categorize_group.py:247
for row in ds:
    text = row['text'].replace('\n', '')
    label = int(row['label'])
    label_text = labels[label]
    examples = inference(text)
    retrieved_label, relevance = get_label_from_retrieval(examples)
    predicted_label = get_label(text, examples)

```

Write `checks()` and `cases()` for `inference`. Remember: setup in the thunk or at module level, never timed.