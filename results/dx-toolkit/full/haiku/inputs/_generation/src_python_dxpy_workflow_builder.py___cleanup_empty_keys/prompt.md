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
Function under test: `_cleanup_empty_keys` in `src/python/dxpy/workflow_builder.py`
Import it as `from dxpy.workflow_builder import _cleanup_empty_keys`.

## The function
```python
def _cleanup_empty_keys(json_spec):
    import re
    clean_json = re.sub('\"\w*\": (null|\{\}|\"\"|\[\])(\,|)\s*','',json.dumps(json_spec)).replace(", }","}")
    return json.loads(clean_json)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os
import sys
import json
import copy
import dxpy
from .cli import INTERACTIVE_CLI
from .cli.parsers import process_extra_args
from .utils.printing import fill
from .utils import json_load_raise_on_duplicates
from .exceptions import err_exit
from . import logger
```

## Everything else its module defines (headers only)
```python
class WorkflowBuilderException(Exception):
def _fetch_spec_from_dxworkflowjson(src_dir, json_file_name, parser):
def _check_dxcompiler_version(json_spec):
def _notify_instance_type_selection(json_spec):
def _notify_dependencies(json_spec):
    # APPS-622: A textual representation of all the dependencies is appended to 
    # the "description" field of every workflow generated by the dxCompiler in markdown format.
def _get_destination_project(json_spec, args, build_project_id=None):
def _get_destination_folder(json_spec, folder_name=None):
def _get_workflow_name(json_spec, workflow_name=None):
def _get_unsupported_keys(keys, supported_keys):
def _set_categories_on_workflow(global_workflow_id, categories_to_set):
def _version_exists(json_spec, name=None, version=None):
def _get_validated_stage(stage, stage_index):
    # required keys
def validate_ignore_reuse(stages, ignore_reuse_stages):
def _get_validated_stages(stages):
def _validate_json_for_regular_workflow(json_spec, args):
def _validate_json_for_global_workflow(json_spec, args):
def _get_validated_json(json_spec, args):
def _get_validated_json_for_build_or_update(json_spec, args):
def _assert_executable_regions_match(workflow_enabled_regions, workflow_spec):
def _build_regular_workflow(json_spec, keep_open=False):
def _get_validated_enabled_regions(json_spec, args):
def _create_temporary_projects(enabled_regions, bill_to):
def _build_underlying_workflows(enabled_regions, json_spec, args):
def _build_global_workflow(json_spec, enabled_regions, args):
def _update_global_workflow(json_spec, args, global_workflow_id):
def _build_or_update_workflow(args, parser):
def _print_output(workflow_id, args):
def build(args, parser):
```

## Signatures of what its module imports from the repository
```python
# from .cli.parsers import process_extra_args
def process_extra_args(args):
    ...

# from .utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from .utils import json_load_raise_on_duplicates
def json_load_raise_on_duplicates(*args, **kwargs):
    """Like json.load(), but raises an error on duplicate keys."""
    ...

# from .exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/workflow_builder.py:672
                if not args.brief:
                    _notify_instance_type_selection(json_spec)
                    _notify_dependencies(json_spec)
            
            json_spec = _cleanup_empty_keys(json_spec)
            # Verify if the global workflow already exists and if the user has developer rights to it
            # If the global workflow name doesn't exist, the user is free to build it
            # If the name does exist two things can be done:
```

Write `checks()` and `cases()` for `_cleanup_empty_keys`. Remember: setup in the thunk or at module level, never timed.