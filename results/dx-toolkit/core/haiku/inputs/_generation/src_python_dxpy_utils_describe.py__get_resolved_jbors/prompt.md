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
Function under test: `get_resolved_jbors` in `src/python/dxpy/utils/describe.py`
Import it as `from dxpy.utils.describe import get_resolved_jbors`.

## The function
```python
def get_resolved_jbors(resolved_thing, orig_thing, resolved_jbors):
    if resolved_thing == orig_thing:
        return
    if is_job_ref(orig_thing):
        jbor_str = jbor_to_str(orig_thing)
        if jbor_str not in resolved_jbors:
            try:
                from dxpy.api import job_describe
                job_output = job_describe(get_job_from_jbor(orig_thing)).get('output')
                if job_output is not None:
                    field_value = job_output.get(get_field_from_jbor(orig_thing))
                    jbor_index = get_index_from_jbor(orig_thing)
                    if jbor_index is not None:
                        if isinstance(field_value, list):
                            resolved_jbors[jbor_str] = field_value[jbor_index]
                    else:
                        resolved_jbors[jbor_str] = field_value
            except:
                # Just don't report any resolved JBORs if there are
                # any problems
                pass
    elif isinstance(orig_thing, list):
        for i in range(len(orig_thing)):
            get_resolved_jbors(resolved_thing[i], orig_thing[i], resolved_jbors)
    elif isinstance(orig_thing, dict) and '$dnanexus_link' not in orig_thing:
        for key in orig_thing:
            get_resolved_jbors(resolved_thing[key], orig_thing[key], resolved_jbors)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import datetime, time, json, math, sys, copy
import locale
import subprocess
from collections import defaultdict
import dxpy
from .printing import (RED, GREEN, BLUE, YELLOW, WHITE, BOLD, UNDERLINE, ENDC, DELIMITER, get_delimiter, fill)
from .pretty_print import format_timedelta
from ..compat import basestring
```

## Definitions it uses from the same module
```python
def is_job_ref(thing, reftype=dict):
    '''
    :param thing: something that might be a job-based object reference hash
    :param reftype: type that a job-based object reference would be (default is dict)
    '''
    return isinstance(thing, reftype) and \
        ((len(thing) == 2 and \
              isinstance(thing.get('field'), basestring) and \
              isinstance(thing.get('job'), basestring)) or \
             (len(thing) == 1 and \
                  isinstance(thing.get('$dnanexus_link'), reftype) and \
                  isinstance(thing['$dnanexus_link'].get('field'), basestring) and \
                  isinstance(thing['$dnanexus_link'].get('job'), basestring)))

def get_job_from_jbor(thing):
    '''
    :returns: Job ID from a JBOR

    Assumes :func:`is_job_ref` evaluates to True
    '''
    if '$dnanexus_link' in thing:
        return thing['$dnanexus_link']['job']
    else:
        return thing['job']

def get_field_from_jbor(thing):
    '''
    :returns: Output field name from a JBOR

    Assumes :func:`is_job_ref` evaluates to True
    '''
    if '$dnanexus_link' in thing:
        return thing['$dnanexus_link']['field']
    else:
        return thing['field']

def get_index_from_jbor(thing):
    '''
    :returns: Array index of the JBOR if applicable; None otherwise

    Assumes :func:`is_job_ref` evaluates to True
    '''
    if '$dnanexus_link' in thing:
        return thing['$dnanexus_link'].get('index')
    else:
        return None

def jbor_to_str(val):
    ans = get_job_from_jbor(val) + ':' + get_field_from_jbor(val)
    index = get_index_from_jbor(val)
    if index is not None:
        ans += "." + str(index)
    return ans
```

## Everything else its module defines (headers only)
```python
def JOB_STATES(state):
def DATA_STATES(state):
def get_size_str(size):
def parse_typespec(thing):
def get_io_desc(parameter, include_class=True, show_opt=True, app_help_version=False):
    # For interactive help, format array:CLASS inputs as:
    #   -iNAME=CLASS [-iNAME=... [...]]   # If input is required (needs >=1 inputs)
    #   [-iNAME=CLASS [...]]              # If input is optional (needs >=0 inputs
def get_io_spec(spec, skip_fields=None):
def is_metadata_ref(thing, reftype=dict):
def io_val_to_str(val):
def job_output_to_str(job_output, prefix='\n', title="Output: ", title_len=None):
def get_io_field(io_hash, defaults=None, delim='=', highlight_fields=()):
def render_bundleddepends(thing):
def render_execdepends(thing):
def render_stage(title, stage, as_stage_of=None):
def render_short_timestamp(timestamp):
def render_timestamp(timestamp):
def print_field(label, value):
def print_nofill_field(label, value):
def print_list_field(label, values):
def print_json_field(label, json_value):
def print_project_desc(desc, verbose=False):
def get_advanced_inputs(desc, verbose):
def print_app_desc(desc, verbose=False):
def print_globalworkflow_desc(desc, verbose=False):
def get_col_str(col_desc):
def print_data_obj_desc(desc, verbose=False):
def printable_ssh_host_key(ssh_host_key):
def print_execution_desc(desc, verbose=False):
def locale_from_currency_code(dx_code):
def format_currency_from_meta(value, meta):
def format_currency(value, meta, currency_locale=None):
def print_user_desc(desc):
def print_generic_desc(desc):
def print_desc(desc, verbose=False):
def get_ls_desc(desc, print_id=False):
def print_ls_desc(desc, **kwargs):
def get_ls_l_header():
def print_ls_l_header():
def get_ls_l_desc_fields():
def get_ls_l_desc(desc, include_folder=False, include_project=False):
def print_ls_l_desc(desc, **kwargs):
def get_find_executions_string(desc, has_children, single_result=False, show_outputs=True,
                               is_cached_result=False, show_try=False, as_try_group_root=False):
def print_locked_workflow_note():
```

## Signatures of what its module imports from the repository
```python
# from .printing import RED
def RED(message=None):
    ...

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

# from .printing import UNDERLINE
def UNDERLINE(message=None):
    ...

# from .printing import ENDC
def ENDC():
    ...

# from .printing import DELIMITER
def DELIMITER(alt_delim):
    ...

# from .printing import get_delimiter
def get_delimiter(delim=None):
    ...

# from .printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from .pretty_print import format_timedelta
def format_timedelta(timedelta, in_seconds=False, largest_units=None, auto_singulars=False):
    """Formats timedelta (duration) to a human readable form"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/utils/describe.py:893
    resolved_jbors = {}
    input_with_jbors = desc.get('runInput', desc['originalInput'])
    for k in desc["input"]:
        if k in input_with_jbors and desc["input"][k] != input_with_jbors[k]:
            get_resolved_jbors(desc["input"][k], input_with_jbors[k], resolved_jbors)
    if len(resolved_jbors) != 0:
        print_nofill_field("Resolved JBORs", get_io_field(resolved_jbors, delim=(GREEN() + '=>' + ENDC())))
    print_nofill_field("Output", get_io_field(desc["output"]))
```

Write `checks()` and `cases()` for `get_resolved_jbors`. Remember: setup in the thunk or at module level, never timed.