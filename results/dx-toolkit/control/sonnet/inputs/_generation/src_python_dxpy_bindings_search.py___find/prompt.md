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
Function under test: `_find` in `src/python/dxpy/bindings/search.py`
Import it as `from dxpy.bindings.search import _find`.

## The function
```python
def _find(api_method, query, limit, return_handler, first_page_size, **kwargs):
    ''' Takes an API method handler (dxpy.api.find*) and calls it with *query*,
    and then wraps a generator around its output. Used by the methods below.

    Note that this function may only be used for /system/find* methods.
    '''
    num_results = 0

    if "limit" not in query:
        query["limit"] = first_page_size

    while True:
        resp = api_method(query, **kwargs)

        by_parent = resp.get('byParent')
        descriptions = resp.get('describe')
        def format_result(result):
            if return_handler:
                result = dxpy.get_handler(result['id'], project=result.get('project'))
            if by_parent is not None:
                return result, by_parent, descriptions
            else:
                return result

        for i in resp["results"]:
            if num_results == limit:
                return
            num_results += 1
            yield format_result(i)

        # set up next query
        if resp["next"] is not None:
            query["starting"] = resp["next"]
            query["limit"] = min(query["limit"]*2, 1000)
        else:
            return
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import dxpy
from . import DXApplet, DXApp, DXWorkflow, DXProject, DXJob, DXAnalysis
from ..exceptions import DXError, DXSearchError
```

## Everything else its module defines (headers only)
```python
def resolve_data_objects(objects, project=None, folder=None, batchsize=1000):
def find_data_objects(classname=None, state=None, visibility=None,
                      name=None, name_mode='exact', properties=None,
                      typename=None, tag=None, tags=None,
                      link=None, project=None, folder=None, recurse=None,
                      modified_after=None, modified_before=None,
                      created_after=None, created_before=None,
    # ... (truncated)
def find_executions(classname=None, launched_by=None, executable=None, project=None,
                    state=None, origin_job=None, parent_job=None, no_parent_job=False,
                    parent_analysis=None, no_parent_analysis=False, root_execution=None,
                    created_after=None, created_before=None, describe=False,
                    name=None, name_mode="exact", tags=None, properties=None, limit=None,
                    first_page_size=100, return_handler=False, include_subjobs=True,
    # ... (truncated)
def find_jobs(*args, **kwargs):
def find_analyses(*args, **kwargs):
def find_projects(name=None, name_mode='exact', properties=None, tags=None,
                  level=None, describe=False, explicit_perms=None, region=None,
                  public=None, created_after=None, created_before=None, billed_to=None,
                  limit=None, return_handler=False, first_page_size=100, containsPHI=None, externalUploadRestricted=None, **kwargs):
def find_global_executables(method, name=None, name_mode='exact', category=None,
                            all_versions=None, published=None,
                            billed_to=None, created_by=None, developer=None,
                            created_after=None, created_before=None,
                            modified_after=None, modified_before=None,
                            describe=False, limit=None, return_handler=False,
    # ... (truncated)
def find_apps(name=None, name_mode='exact', category=None,
              all_versions=None, published=None,
              billed_to=None, created_by=None, developer=None,
              created_after=None, created_before=None,
              modified_after=None, modified_before=None,
              describe=False, limit=None, return_handler=False, first_page_size=100, **kwargs):
def find_global_workflows(name=None, name_mode='exact', category=None,
                          all_versions=None, published=None,
                          billed_to=None, created_by=None, developer=None,
                          created_after=None, created_before=None,
                          modified_after=None, modified_before=None,
                          describe=False, limit=None, return_handler=False,
    # ... (truncated)
def _find_one(method, zero_ok=False, more_ok=True, **kwargs):
    # users often incorrectly pass strings to zero_ok, fail fast in that case
def find_one_data_object(zero_ok=False, more_ok=True, **kwargs):
def find_one_project(zero_ok=False, more_ok=True, **kwargs):
def find_one_app(zero_ok=False, more_ok=True, **kwargs):
def _org_find(api_method, org_id, query, first_page_size=100):
def org_find_members(org_id=None, level=None, describe=False):
def org_find_projects(org_id=None, name=None, name_mode='exact', ids=None, properties=None, tags=None, describe=False,
                      public=None, created_after=None, created_before=None, region=None, containsPHI=None):
def org_find_apps(org_id,
                  name=None,
                  name_mode='exact',
                  category=None,
                  all_versions=None,
                  published=None,
    # ... (truncated)
def find_orgs(query, first_page_size=10):
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import DXError
class DXError(Exception):

# from ..exceptions import DXSearchError
class DXSearchError(DXError):
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/bindings/search.py:270
        query['archivalState'] = archival_state
    if limit is not None:
        query["limit"] = limit

    return _find(dxpy.api.system_find_data_objects, query, limit, return_handler, first_page_size, **kwargs)


def find_executions(classname=None, launched_by=None, executable=None, project=None,

# src/python/dxpy/bindings/search.py:426
        query["includeRestarted"] = include_restarted
    if limit is not None:
        query["limit"] = limit

    return _find(dxpy.api.system_find_executions, query, limit, return_handler, first_page_size, **kwargs)

def find_jobs(*args, **kwargs):
    """
```

Write `checks()` and `cases()` for `_find`. Remember: setup in the thunk or at module level, never timed.