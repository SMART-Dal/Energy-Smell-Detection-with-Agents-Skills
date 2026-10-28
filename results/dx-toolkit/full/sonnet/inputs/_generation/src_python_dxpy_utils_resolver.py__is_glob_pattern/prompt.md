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
Function under test: `is_glob_pattern` in `src/python/dxpy/utils/resolver.py`
Import it as `from dxpy.utils.resolver import is_glob_pattern`.

## The function
```python
def is_glob_pattern(string):
    return (get_last_pos_of_char('*', string) >= 0) or (get_last_pos_of_char('?', string) >= 0)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, json, re
import dxpy
from .describe import get_ls_l_desc
from ..compat import basestring
from ..cli import try_call, INTERACTIVE_CLI
from ..exceptions import DXCLIError, DXError
```

## Definitions it uses from the same module
```python
def get_last_pos_of_char(char, string):
    '''
    :param char: The character to find
    :type char: string
    :param string: The string in which to search for *char*
    :type string: string
    :returns: Index in *string* where *char* last appears (unescaped by a preceding "\\"), -1 if not found
    :rtype: int

    Finds the last occurrence of *char* in *string* in which *char* is
    not present as an escaped character.

    '''
    pos = len(string)
    while pos > 0:
        pos = string[:pos].rfind(char)
        if pos == -1:
            return -1
        num_backslashes = 0
        test_index = pos - 1
        while test_index >= 0 and string[test_index] == '\\':
            num_backslashes += 1
            test_index -= 1
        if num_backslashes % 2 == 0:
            return pos
    return -1
```

## Everything else its module defines (headers only)
```python
class ResolutionError(DXError):
    def __init__(self, msg):
def pick(choices, default=None, str_choices=None, prompt=None, allow_mult=False, more_choices=False):
def paginate_and_pick(generator, render_fn=str, filter_fn=None, page_len=10, **pick_opts):
def is_hashid(string):
def is_data_obj_id(string):
def is_container_id(string):
def is_project_id(string):
def is_analysis_id(string):
def is_job_id(string):
def is_localjob_id(thing):
def is_nohash_id(string):
def is_jbor_str(string):
def is_project_explicit(path):
def object_exists_in_project(obj_id, proj_id):
def escaper(match):
def escape_folder_str(string):
def escape_name_str(string):
def unescaper(match):
def unescape_folder_str(string):
def unescape_name_str(string):
def get_first_pos_of_char(char, string):
def split_unescaped(char, string, include_empty_strings=False):
def clean_folder_path(path, expected=None):
def resolve_container_id_or_name(raw_string, is_error=False, multi=False):
def _maybe_convert_stringified_dxlink(path):
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
def resolve_job_ref(job_id, name, describe={}):
def _check_resolution_needed(path, project, folderpath, entity_name, expected_classes=None, describe=True,
                             enclose_in_list=False):
def _resolve_folder(project, parent_folder, folder_name):
def _validate_resolution_output_length(path, entity_name, results, allow_mult=False, all_mult=False,
                                       ask_to_resolve=True):
def _resolve_global_entity(project_or_job_id, folderpath, entity_name, describe=True, visibility="either"):
def _format_resolution_output(path, project, folderpath, entity_name, result):
def resolve_multiple_existing_paths(paths):
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
def check_folder_exists(project, path, folder_name):
def get_app_from_path(path):
def get_global_workflow_from_path(path):
def get_global_exec_from_path(path):
def resolve_app(path):
def resolve_global_workflow(path):
def resolve_global_executable(path, is_version_required=False):
def get_exec_handler(path, alias=None):
def resolve_to_objects_or_project(path, all_matching_results=False):
def parse_input_keyval(keyeqval):
```

## Signatures of what its module imports from the repository
```python
# from .describe import get_ls_l_desc
def get_ls_l_desc(desc, include_folder=False, include_project=False):
    """desc must have at least all the fields given by get_ls_l_desc_fields."""
    ...

# from ..cli import try_call
def try_call(func, *args, **kwargs):
    ...

# from ..exceptions import DXCLIError
class DXCLIError(DXError):

# from ..exceptions import DXError
class DXError(Exception):
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/utils/resolver.py:994
        except:
            must_resolve = False

        if must_resolve:
            if is_glob_pattern(entity_name):
                # TODO: Must call findDataObjects because resolveDataObjects does not support glob patterns
                try:
                    find_results = _resolve_global_entity(project, folderpath, entity_name)

# src/python/dxpy/utils/resolver.py:815

    if len(results) > 1:
        # The other way the caller can specify it wants all results is by setting
        # allow_mult to be True and allowing all_mult to be True (or if the object name is a glob pattern)
        if allow_mult and (all_mult or is_glob_pattern(entity_name)):
            return results
        if INTERACTIVE_CLI:
            print('The given path "' + path + '" resolves to the following data objects:')
```

Write `checks()` and `cases()` for `is_glob_pattern`. Remember: setup in the thunk or at module level, never timed.