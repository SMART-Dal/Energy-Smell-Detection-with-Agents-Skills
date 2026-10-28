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
Function under test: `escape_unicode_string` in `src/python/dxpy/utils/pretty_print.py`
Import it as `from dxpy.utils.pretty_print import escape_unicode_string`.

## The function
```python
def escape_unicode_string(u):
    """
    Escapes the nonprintable chars 0-31 and 127, and backslash;
    preferably with a friendly equivalent such as '\n' if available, but
    otherwise with a Python-style backslashed hex escape.
    """
    def replacer(matchobj):
        if ord(matchobj.group(1)) == 127:
            return "\\x7f"
        if ord(matchobj.group(1)) == 92: # backslash
            return "\\\\"
        return REPLACEMENT_TABLE[ord(matchobj.group(1))]
    return re.sub("([\\000-\\037\\134\\177])", replacer, u)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import re
from collections.abc import Mapping
from .printing import (GREEN, BLUE, YELLOW, WHITE, BOLD, ENDC)
```

## Definitions it uses from the same module
```python
REPLACEMENT_TABLE = (
    '\\x00',    #  0x00 -> NULL
    '\\x01',    #  0x01 -> START OF HEADING
    '\\x02',    #  0x02 -> START OF TEXT
    '\\x03',    #  0x03 -> END OF TEXT
    '\\x04',    #  0x04 -> END OF TRANSMISSION
    '\\x05',    #  0x05 -> ENQUIRY
    '\\x06',    #  0x06 -> ACKNOWLEDGE
    '\\x07',    #  0x07 -> BELL
    '\\x08',    #  0x08 -> BACKSPACE
    '\\t',      #  0x09 -> HORIZONTAL TABULATION
    '\\n',      #  0x0A -> LINE FEED
    '\\x0b',    #  0x0B -> VERTICAL TABULATION
    '\\x0c',    #  0x0C -> FORM FEED
    '\\r',      #  0x0D -> CARRIAGE RETURN
    '\\x0e',    #  0x0E -> SHIFT OUT
    '\\x0f',    #  0x0F -> SHIFT IN
    '\\x10',    #  0x10 -> DATA LINK ESCAPE
    '\\x11',    #  0x11 -> DEVICE CONTROL ONE
    '\\x12',    #  0x12 -> DEVICE CONTROL TWO
    '\\x13',    #  0x13 -> DEVICE CONTROL THREE
    '\\x14',    #  0x14 -> DEVICE CONTROL FOUR
    '\\x15',    #  0x15 -> NEGATIVE ACKNOWLEDGE
    '\\x16',    #  0x16 -> SYNCHRONOUS IDLE
    '\\x17',    #  0x17 -> END OF TRANSMISSION BLOCK
    '\\x18',    #  0x18 -> CANCEL
    '\\x19',    #  0x19 -> END OF MEDIUM
    '\\x1a',    #  0x1A -> SUBSTITUTE
    '\\x1b',    #  0x1B -> ESCAPE
    '\\x1c',    #  0x1C -> FILE SEPARATOR
    '\\x1d',    #  0x1D -> GROUP SEPARATOR
    '\\x1e',    #  0x1E -> RECORD SEPARATOR
    '\\x1f'     #  0x1F -> UNIT SEPARATOR
    )
```

## Everything else its module defines (headers only)
```python
def format_tree(tree, root=None):
def format_table(table, column_names=None, column_specs=None, max_col_width=32,
                 report_dimensions=False):
def flatten_json_array(json_string, array_name):
def format_timedelta(timedelta, in_seconds=False, largest_units=None, auto_singulars=False):
```

## Signatures of what its module imports from the repository
```python
# from .printing import GREEN
def GREEN(message=None):
    ...

# from .printing import BLUE
def BLUE(message=None):
    ...

# from .printing import YELLOW
def YELLOW(message=None):
    ...

# from .printing import WHITE
def WHITE(message=None):
    ...

# from .printing import BOLD
def BOLD(message=None):
    ...

# from .printing import ENDC
def ENDC():
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxpy.py:2477


class TestPrettyPrint(unittest.TestCase):
    def test_string_escaping(self):
        self.assertEqual(pretty_print.escape_unicode_string("a"), "a")
        self.assertEqual(pretty_print.escape_unicode_string("foo\nbar"), "foo\\nbar")
        self.assertEqual(pretty_print.escape_unicode_string("foo\x11bar"), "foo\\x11bar")
        self.assertEqual(pretty_print.escape_unicode_string("foo\n\t\rbar"), "foo\\n\\t\\rbar")

# src/python/test/test_dxpy.py:2478

class TestPrettyPrint(unittest.TestCase):
    def test_string_escaping(self):
        self.assertEqual(pretty_print.escape_unicode_string("a"), "a")
        self.assertEqual(pretty_print.escape_unicode_string("foo\nbar"), "foo\\nbar")
        self.assertEqual(pretty_print.escape_unicode_string("foo\x11bar"), "foo\\x11bar")
        self.assertEqual(pretty_print.escape_unicode_string("foo\n\t\rbar"), "foo\\n\\t\\rbar")
        self.assertEqual(pretty_print.escape_unicode_string("\n\\"), "\\n\\\\")

# src/python/dxpy/utils/pretty_print.py:153
    my_table = []
    for row in table:
        my_row = []
        for i in range(len(row)):
            my_item = escape_unicode_string(str(row[i]))
            if len(my_item) > max_col_width:
                my_item = my_item[:max_col_width-1] + '…'
            my_row.append(my_item)
```

Write `checks()` and `cases()` for `escape_unicode_string`. Remember: setup in the thunk or at module level, never timed.