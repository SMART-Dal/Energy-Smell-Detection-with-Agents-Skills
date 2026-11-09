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
Function under test: `MindData.lookup_news_index` in `news/src/python/mind_data.py`
Import it as `from mind_data import MindData`; the method is called as `MindData.lookup_news_index(instance, ...)`.

## The function
```python
    def lookup_news_index(self, news_id):
        return self.lookup_index(news_id, self.news_map)
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class MindData:
    def __init__(self, train_news_file, train_impressions_file, valid_news_file, valid_impressions_file):
        self.user_map = {}    # Mapping from user_id to index, e.g. "U82271" -> 0, "U84185" -> 1 etc
        self.news_map = {}    # Mapping from news_id to index, e.g. "N27209" -> 0
        self.cat_map = {}     # Mapping from category to index, e.g. "health" -> 0
        self.sub_cat_map = {} # Mapping from subcategory to index, e.g. "medical" -> 0
        self.entity_map = {}  # Mapping from entity id to index, e.g. "Q212" -> 0  (WikidataId for "ukraine")
        self.news_content = {}
        self.train_impressions = []
        self.valid_impressions = []
        self.read_data(train_impressions_file, self.train_impressions)
        self.read_data(valid_impressions_file, self.valid_impressions)
        self.read_news(train_news_file)
        self.read_news(valid_news_file)
    def users(self):
        ...
    def news(self):
        ...
    def categories(self):
        ...
    def subcategories(self):
        ...
    def entities(self):
        ...
    def read_news(self, news_file):
        ...
    def add_entities(self, entity_ids: list, entities: list):
        ...
    def read_data(self, impressions_file, impression_list):
        ...
    def find_labels(self, impressions, history):
        ...
    def lookup_user_index(self, user_id):
        ...
    def lookup_news_index(self, news_id):
        return self.lookup_index(news_id, self.news_map)
    def lookup_category_index(self, category):
        ...
    def lookup_subcategory_index(self, subcategory):
        ...
    def lookup_entity_index(self, entity_id):
        ...
    def lookup_index(self, id, map):
        ...
    def sample_training_data(self, batch_size, num_negatives, prob=1.0):
        ...
    def sample_valid_data(self, prob=1.0, train=False):
        ...
    def add_impressions(self, impression, user_indices, news_indices, category_indices, subcategory_indices, entity_indices, labels, num_negatives):
        ...
    def find_clicked(self, news_ids, labels):
        ...
    def get_news_content_tensors(self):
        ...
```

## Imports of its module
```python
import os
import io
import sys
import json
import random
import datetime
import torch
from torch.utils.data import DataLoader, TensorDataset, RandomSampler
```

## Where the repository calls it or builds its class
```python
# news/src/python/train_cold_start.py:200
def main():
    set_random_seed(1)

    # read data
    data_loader = MindData(train_news_file, train_impressions_file, valid_news_file, valid_impressions_file)
    num_users = len(data_loader.users())
    num_news = len(data_loader.news())
    num_categories = len(data_loader.categories())

# news/src/python/train_mf.py:134
def main():
    set_random_seed(1)

    # read data
    data_loader = MindData(train_news_file, train_impressions_file, valid_news_file, valid_impressions_file)
    num_users = len(data_loader.users())
    num_news = len(data_loader.news())


# news/src/python/mind_data.py:69
                self.add_entities(entity_ids, title_entities)
                self.add_entities(entity_ids, abstract_entities)
                entity_ids.extend([""] * entities_to_keep)

                self.news_content[self.lookup_news_index(doc_id)] = {
                    "news_id": doc_id,
                    "category_index": self.lookup_category_index(category),
                    "subcategory_index": self.lookup_subcategory_index(subcategory),

# news/src/python/mind_data.py:112
        labels = []
        for impression in impressions:
            news_id, label = impression.split("-")
            if news_id not in history:  # don't add news previously clicked (in history)
                news_indices.append(self.lookup_news_index(news_id))
                labels.append(int(label))
        return news_indices, labels

```

Write `checks()` and `cases()` for `MindData.lookup_news_index`. Remember: setup in the thunk or at module level, never timed.