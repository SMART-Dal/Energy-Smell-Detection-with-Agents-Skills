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

Repository: dx-toolkit
Function under test: `_harmonize_sql_select_named_expression` in `src/python/dxpy/dx_extract_utils/germline_utils.py`
Import it as `from dxpy.dx_extract_utils.germline_utils import _harmonize_sql_select_named_expression`.

## The function
```python
def _harmonize_sql_select_named_expression(sql, return_columns, **kwargs):
    """
    Harmonizes the SELECT list of a SQL statement to include all columns in return_columns. NULL values are used for
    columns not in the SELECT list.
    """
    select_info = {alias: (table, column) for table, column, alias in _parse_sql_select_named_expression(sql)}

    select_lists = []
    for return_column in return_columns:
        return_column = tuple(return_column)[0]
        if return_column in select_info:
            table, column = select_info[return_column]
            select_lists.append("`{table}`.`{column}` AS `{return_column}`".format(table=table,
                                                                                   column=column,
                                                                                   return_column=return_column))
        elif return_column in kwargs:
            select_lists.append("`{table}`.`{column}` AS `ref`".format(table=kwargs[return_column][0],
                                                                       column=kwargs[return_column][1]))
        else:
            select_lists.append("NULL AS `{return_column}`".format(return_column=return_column))
    select_list = ", ".join(select_lists)

    distinct = re.match(SELECT_LIST_REGEX, sql).group(1)
    return re.sub(
        SELECT_LIST_REGEX,
        "SELECT {distinct}{select_list} FROM".format(distinct=distinct, select_list=select_list),
        sql,
    )
```

## Imports of its module
```python
from __future__ import annotations
import json
import os
import re
from .filter_to_payload import extract_utils_basepath
from .input_validation import GENOTYPE_TYPES
```

## Definitions it uses from the same module
```python
SELECT_LIST_REGEX = r"SELECT\s+(DISTINCT\s+)?(.+?)\s+FROM"

def _parse_sql_select_named_expression(sql):
    """
    Parses the SELECT list of a SQL statement and returns a generator of named expressions table, column, and alias.
    """
    select_list_match = re.match(SELECT_LIST_REGEX, sql).group(2)
    for named_expression in [x.strip() for x in select_list_match.split(",")]:
        named_expression_match = re.match(NAMED_EXPRESSION_REGEX, named_expression).groups()
        yield named_expression_match[1], named_expression_match[2], named_expression_match[4]
```

## Everything else its module defines (headers only)
```python
def get_genotype_types(filter_dict):
def get_genotype_only_types(filter_dict, exclude_refdata, exclude_halfref, exclude_nocall):
def get_types_to_filter_out_when_infering(
    requested_types: list[str],
) -> list:
def add_germline_base_sql(resp, payload):
def sort_germline_variant(d):
def harmonize_germline_sql(sql):
def harmonize_germline_results(results, fields_list):
def get_germline_ref_payload(results, genotype_payload):
def update_genotype_only_ref(results, locus_id_refs):
def get_germline_loci_payload(locations, genotype_payload):
def _produce_loci_dict(loci: list[dict], results_entries: list[dict]) -> dict:
def infer_genotype_type(
    samples: list, loci: list[dict], result_entries: list[dict], type_to_infer: str
) -> list[dict]:
def filter_results(
    results: list[dict], key: str, restricted_values: list
) -> list[dict]:
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/dx_extract_utils/germline_utils.py:135
    allele_table = re.search(join_condition_regex, sql).group(2)
    sql = re.sub(join_condition_regex, "ON `\\1`.`locus_id` = `\\3`.`locus_id` WHERE", sql)

    # Add return columns missing in SQL statement to the SELECT list as NULL values
    sql = _harmonize_sql_select_named_expression(sql, genotype_return_columns, ref=(allele_table, "a_id"))

    return sql

```

Write `checks()` and `cases()` for `_harmonize_sql_select_named_expression`. Remember: setup in the thunk or at module level, never timed.