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
Function under test: `has_local_job_refs` in `src/python/dxpy/utils/local_exec_utils.py`
Import it as `from dxpy.utils.local_exec_utils import has_local_job_refs`.

## The function
```python
def has_local_job_refs(io_hash):
    '''
    :param io_hash: input/output hash
    :type io_hash: dict
    :returns: boolean indicating whether any job-based object references are found in *io_hash*
    '''
    q = []

    for field in io_hash:
        if is_job_ref(io_hash[field]):
            if get_job_from_jbor(io_hash[field]).startswith('localjob'):
                return True
        elif isinstance(io_hash[field], list) or isinstance(io_hash[field], dict):
            q.append(io_hash[field])

    while len(q) > 0:
        thing = q.pop()
        if isinstance(thing, list):
            for i in range(len(thing)):
                if is_job_ref(thing[i]):
                    if get_job_from_jbor(thing[i]).startswith('localjob'):
                        return True
                elif isinstance(thing[i], list) or isinstance(thing[i], dict):
                    q.append(thing[i])
        else:
            for field in thing:
                if is_job_ref(thing[field]):
                    if get_job_from_jbor(thing[field]).startswith('localjob'):
                        return True
                elif isinstance(thing[field], list) or isinstance(thing[field], dict):
                    q.append(thing[field])

    return False
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, json, subprocess, shlex
import collections, datetime
import dxpy
from .describe import (get_field_from_jbor, get_job_from_jbor, get_index_from_jbor,
                       is_job_ref, job_output_to_str, JOB_STATES)
from .printing import (GREEN, BLUE, BOLD, ENDC, fill)
from .resolver import is_localjob_id
from ..compat import basestring
from . import file_load_utils
```

## Everything else its module defines (headers only)
```python
def exit_with_error(msg):
def resolve_job_ref(jbor, job_outputs={}, should_resolve=True):
def resolve_job_references(io_hash, job_outputs, should_resolve=True):
def get_nonclosed_data_obj_link(thing):
def get_implicit_depends_on(input_hash, depends_on):
def wait_for_depends_on(depends_on, all_job_outputs):
    # Wait for depends_on and any data objects in the input to close
def ensure_env_vars():
def queue_entry_point(function, input_hash, depends_on=[], name=None):
def run_one_entry_point(job_id, function, input_hash, run_spec, depends_on, name=None):
def run_entry_points(run_spec):
```

## Signatures of what its module imports from the repository
```python
# from .describe import get_job_from_jbor
def get_job_from_jbor(thing):
    """:returns: Job ID from a JBOR"""
    ...

# from .describe import is_job_ref
def is_job_ref(thing, reftype=dict):
    """:param thing: something that might be a job-based object reference hash"""
    ...

# from .describe import get_field_from_jbor
def get_field_from_jbor(thing):
    """:returns: Output field name from a JBOR"""
    ...

# from .describe import get_index_from_jbor
def get_index_from_jbor(thing):
    """:returns: Array index of the JBOR if applicable; None otherwise"""
    ...

# from .describe import job_output_to_str
def job_output_to_str(job_output, prefix='\n', title="Output: ", title_len=None):
    ...

# from .describe import JOB_STATES
def JOB_STATES(state):
    ...

# from .printing import GREEN
def GREEN(message=None):
    ...

# from .printing import BLUE
def BLUE(message=None):
    ...

# from .printing import BOLD
def BOLD(message=None):
    ...

# from .printing import ENDC
def ENDC():
    ...

# from .printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from .resolver import is_localjob_id
def is_localjob_id(thing):
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/utils/local_exec_utils.py:434
        entry_point_to_run = None
        for i, entry_point in enumerate(job_queue):
            runnable = True
            # See if its inputs are ready
            while has_local_job_refs(entry_point['input_hash']):
                try:
                    resolve_job_references(entry_point['input_hash'], all_job_outputs)
                except:
```

Write `checks()` and `cases()` for `has_local_job_refs`. Remember: setup in the thunk or at module level, never timed.