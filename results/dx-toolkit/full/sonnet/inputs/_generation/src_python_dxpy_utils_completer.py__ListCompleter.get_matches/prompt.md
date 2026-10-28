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
Function under test: `ListCompleter.get_matches` in `src/python/dxpy/utils/completer.py`
Import it as `from dxpy.utils.completer import ListCompleter`; the method is called as `ListCompleter.get_matches(instance, ...)`.

## The function
```python
    def get_matches(self, line, point, prefix, suffix):
        # This implementation is reliant on bash behavior that ':' is
        # treated as a word separator for determining prefix
        if get_last_pos_of_char(' ', line) != point - 1:
            prefix = split_unescaped(' ', line[:point])[-1]
        self._populate_matches(prefix)
        if prefix.rfind(':') != -1:
            for i in range(len(self.matches)):
                self.matches[i] = self.matches[i][self.matches[i].rfind(':') + 1:]

        return self.matches
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class ListCompleter():
    def __init__(self, completions):
        self.completions = completions
        self.matches = []
    def _populate_matches(self, prefix):
        ...
    def get_matches(self, line, point, prefix, suffix):
        # This implementation is reliant on bash behavior that ':' is
        # treated as a word separator for determining prefix
        if get_last_pos_of_char(' ', line) != point - 1:
            prefix = split_unescaped(' ', line[:point])[-1]
        self._populate_matches(prefix)
        if prefix.rfind(':') != -1:
            for i in range(len(self.matches)):
                self.matches[i] = self.matches[i][self.matches[i].rfind(':') + 1:]

        return self.matches
    def complete(self, text, state):
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import sys
from argcomplete import warn
from collections import namedtuple, OrderedDict
import dxpy
from .resolver import (get_first_pos_of_char, get_last_pos_of_char, clean_folder_path, resolve_path,
                       split_unescaped, ResolutionError)
from .printing import fill
```

## Everything else its module defines (headers only)
```python
class DXPathCompleter():
    def __init__(self, expected=None, classes=None, typespec=None, include_current_proj=False,
                 visibility=None):
    # methods: get_matches, complete
class DXAppCompleter():
    def __init__(self, installed=None):
    # methods: get_matches, complete
class LocalCompleter():
    def __init__(self):
    # methods: get_matches, complete
class NoneCompleter():
    # methods: get_matches, complete
class MultiCompleter():
    def __init__(self, completers):
    # methods: get_matches, complete
class InstanceTypesCompleter():
    # methods: complete
def startswith(text):
def escape_name(text):
def escape_colon(text):
def unescape_colon(text):
def join_path(project, path, name):
def split_path(path):
def get_folder_matches(text, delim_pos, dxproj, folderpath):
def get_data_matches(text, delim_pos, dxproj, folderpath, classname=None,
                     typespec=None, visibility=None):
def path_completer(text, expected=None, classes=None, perm_level=None,
                   include_current_proj=False, typespec=None, visibility=None):
```

## Signatures of what its module imports from the repository
```python
# from .resolver import get_last_pos_of_char
def get_last_pos_of_char(char, string):
    """:param char: The character to find"""
    ...

# from .resolver import split_unescaped
def split_unescaped(char, string, include_empty_strings=False):
    """:param char: The character on which to split the string"""
    ...

# from .resolver import get_first_pos_of_char
def get_first_pos_of_char(char, string):
    """:param char: The character to find"""
    ...

# from .resolver import clean_folder_path
def clean_folder_path(path, expected=None):
    """:param path: A folder path to sanitize and parse"""
    ...

# from .resolver import resolve_path
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
    """:param path: A path to a data object to attempt to resolve"""
    ...

# from .resolver import ResolutionError
class ResolutionError(DXError):
    def __init__(self, msg):
        ...

# from .printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/cli/exec_io.py:263
            readline.set_completer(DXPathCompleter(classes=[in_class],
                                                   typespec=typespec).complete)
        elif in_class == 'boolean':
            from dxpy.utils.completer import ListCompleter
            readline.set_completer(ListCompleter(completions=['true', 'false']).complete)
        elif 'suggestions' in param_desc:
            from dxpy.utils.completer import ListCompleter
            readline.set_completer(ListCompleter(completions=map(str, param_desc['suggestions'])).complete)

# src/python/dxpy/cli/exec_io.py:367
            readline.set_completer(DXPathCompleter(classes=[in_class],
                                                   typespec=typespec).complete)
        elif in_class == 'boolean':
            from dxpy.utils.completer import ListCompleter
            readline.set_completer(ListCompleter(completions=['true', 'false']).complete)
        elif 'suggestions' in param_desc:
            from dxpy.utils.completer import ListCompleter
            readline.set_completer(ListCompleter(completions=map(str, param_desc['suggestions'])).complete)

# src/python/dxpy/scripts/dx.py:6089
    parents=[stdout_args, json_arg, delim_arg, env_args],
    prog='dx find apps'
)
parser_find_apps.add_argument('--name', help='Name of the app')
parser_find_apps.add_argument('--category', help='Category of the app').completer = ListCompleter(APP_CATEGORIES)
parser_find_apps.add_argument('--category-help',
                              help='Print a list of common app categories',
                              nargs=0,

# src/python/dxpy/scripts/dx.py:6116
    parents=[stdout_args, json_arg, delim_arg, env_args],
    prog='dx find globalworkflows'
)
parser_find_globalworkflows.add_argument('--name', help='Name of the workflow')
parser_find_globalworkflows.add_argument('--category', help='Category of the workflow').completer = ListCompleter(APP_CATEGORIES)
parser_find_globalworkflows.add_argument('--category-help',
                              help='Print a list of common global workflow categories',
                              nargs=0,

# src/python/dxpy/utils/completer.py:392

    def _populate_matches(self, prefix):
        self.matches = []
        for completer in self.completers:
            self.matches += completer.get_matches('', 0, prefix, '')
        return self.matches

    def get_matches(self, line, point, prefix, suffix):

# src/python/dxpy/utils/completer.py:400
        # This implementation assumes the get_matches will handle any
        # special word separation
        self.matches = []
        for completer in self.completers:
            self.matches += completer.get_matches(line, point, prefix, suffix)
        return self.matches

    def complete(self, text, state):
```

Write `checks()` and `cases()` for `ListCompleter.get_matches`. Remember: setup in the thunk or at module level, never timed.