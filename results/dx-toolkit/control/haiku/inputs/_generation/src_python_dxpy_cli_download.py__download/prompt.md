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
Function under test: `download` in `src/python/dxpy/cli/download.py`
Import it as `from dxpy.cli.download import download`.

## The function
```python
def download(args):
    folders_to_get, files_to_get, count = collections.defaultdict(list), collections.defaultdict(list), 0
    foldernames, filenames = [], []
    for path in args.paths:
        # Attempt to resolve name. If --all is given or the path looks like a glob, download all matches.
        # Otherwise, the resolver will display a picker (or error out if there is no tty to display to).
        resolver_kwargs = {'allow_empty_string': False}
        if args.all or _is_glob(path):
            resolver_kwargs.update({'allow_mult': True, 'all_mult': True})

        # include "parts" and a few additional fields in the description so that
        # we don't have to call a separate describe method downstream
        resolver_kwargs.update({"describe": {"parts": True,
                                             "size": True,
                                             "drive": True,
                                             "md5": True,
                                             "checksumType": True
                                             }})

        project, folderpath, matching_files = try_call(resolve_existing_path, path, **resolver_kwargs)

        if matching_files is None:
            matching_files = []
        elif not isinstance(matching_files, list):
            matching_files = [matching_files]

        # TODO: this could also be returned as metadata by resolve_path since
        # resolve_path knows these things in some circumstances
        path_has_explicit_proj = is_project_explicit(path) or is_jbor_str(path)

        if is_jbor_str(path):
            assert len(matching_files) == 1
            project = matching_files[0]["describe"]["project"]
        matching_folders = []
        # project may be none if path is an ID and there is no project context
        if project is not None:
            colon_pos = get_first_pos_of_char(":", path)
            if colon_pos >= 0:
                path = path[colon_pos + 1:]
            abs_path, strip_prefix = _rel2abs(path, project)
            parent_folder = os.path.dirname(abs_path)
            folder_listing = dxpy.list_subfolders(project, parent_folder, recurse=False)
            matching_folders = pathmatch.filter(folder_listing, abs_path)
            if '/' in matching_folders and len(matching_folders) > 1:
                # The list of subfolders is {'/', '/A', '/B'}.
                # Remove '/', otherwise we will download everything twice.
                matching_folders.remove('/')

        if len(matching_files) == 0 and len(matching_folders) == 0:
            err_exit(fill('Error: {path} is neither a file nor a folder name'.format(path=path)))

        # If the user did not explicitly provide the project, don't pass any
        # project parameter to the API call but continue with the download.
        if not path_has_explicit_proj:
            project = dxpy.DXFile.NO_PROJECT_HINT

        # If the user explicitly provided the project and it doesn't contain
        # the files, don't allow the download.

        # For speed's sake, skip this check (i.e. one API call) if the user
        # passed the lightweight argument
        #
        # If length of matching_files is 0 then we're only downloading folders
        # so skip this logic since the files will be verified in the API call.
        if not args.lightweight \
            and len(matching_files) > 0 \
            and path_has_explicit_proj \
            and not any(object_exists_in_project(f['describe']['id'], project) for f in matching_files):
                err_exit(fill('Error: specified project does not contain specified file object'))

        files_to_get[project].extend(matching_files)
        folders_to_get[project].extend(((f, strip_prefix) for f in matching_folders))
        count += len(matching_files) + len(matching_folders)
        filenames.extend(f["describe"]["name"] for f in matching_files)
        foldernames.extend(f[len(strip_prefix):].lstrip('/') for f in matching_folders)

    if len(filenames) > 0 and len(foldernames) > 0:
        name_conflicts = set(filenames) & set(foldernames)
        if len(name_conflicts) > 0:
            msg = "Error: The following paths are both file and folder names, and " \
                  "cannot be downloaded to the same destination: "
            msg += ", ".join(sorted(name_conflicts))
            err_exit(fill(msg))

    if args.output is None:
        destdir, dest_filename = os.getcwd(), None
    elif count > 1:
        if not os.path.exists(args.output):
            err_exit(fill("Error: When downloading multiple objects, --output must be an existing directory"))
        destdir, dest_filename = args.output, None
    elif os.path.isdir(args.output):
        destdir, dest_filename = args.output, None
    elif args.output.endswith('/'):
        err_exit(fill("Error: {path} could not be found".format(path=args.output)))
    else:
        destdir, dest_filename = os.getcwd(), args.output

    _download_folders(folders_to_get, destdir, args)
    _download_files(files_to_get, destdir, args, dest_filename=dest_filename)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import collections
import os
import subprocess
import sys
import logging
import dxpy
from ..utils.resolver import (resolve_existing_path, get_first_pos_of_char, is_project_explicit,
                              object_exists_in_project, is_jbor_str)
from ..exceptions import err_exit
from . import try_call
from dxpy.utils.printing import (fill)
from dxpy.utils import pathmatch
```

## Definitions it uses from the same module
```python
def _is_glob(path):
    return get_first_pos_of_char('*', path) > -1 or get_first_pos_of_char('?', path) > -1

def _rel2abs(path, project):
    if path.startswith('/') or dxpy.WORKSPACE_ID != project:
        abs_path, strip_prefix = path, os.path.dirname(path.rstrip('/'))
    else:
        wd = dxpy.config.get('DX_CLI_WD', u'/')
        abs_path, strip_prefix = os.path.join(wd, path), os.path.dirname(os.path.join(wd, path).rstrip('/'))
    if len(abs_path) > 1:
        abs_path = abs_path.rstrip('/')
    return abs_path, strip_prefix

def _download_files(files, destdir, args, dest_filename=None):
    for project in files:
        for f in files[project]:
            file_desc = f['describe']
            dest = dest_filename or os.path.join(destdir, file_desc['name'].replace('/', '%2F'))
            download_one_file(project, file_desc, dest, args)

def _download_folders(folders, destdir, args):
    try:
        show_progress = args.show_progress
    except AttributeError:
        show_progress = False
    for project in folders:
        for folder, strip_prefix in folders[project]:
            if not args.recursive:
                err_exit('Error: "' + folder + '" is a folder but the -r/--recursive option was not given')
            assert(folder.startswith(strip_prefix))
            folder_destdir = os.path.join(destdir, folder[len(strip_prefix):].lstrip('/'))
            try:
                dxpy.download_folder(project, folder_destdir, folder=folder, overwrite=args.overwrite,
                                     show_progress=show_progress)
            except:
                err_exit()
```

## Everything else its module defines (headers only)
```python
def _which(program):
def _verify(filename, md5digest):
def download_one_file(project, file_desc, dest_filename, args):
def do_debug(msg):
def download_one_database_file(project, database_desc, dest_filename, src_filename, file_status, args):
def _ensure_local_dir(d):
```

## Signatures of what its module imports from the repository
```python
# from ..utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...

# from ..utils.resolver import get_first_pos_of_char
def get_first_pos_of_char(char, string):
    """:param char: The character to find"""
    ...

# from ..utils.resolver import is_project_explicit
def is_project_explicit(path):
    """Returns True if the specified path explicitly specifies a project."""
    ...

# from ..utils.resolver import object_exists_in_project
def object_exists_in_project(obj_id, proj_id):
    """:param obj_id: object ID"""
    ...

# from ..utils.resolver import is_jbor_str
def is_jbor_str(string):
    ...

# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from . import try_call
def try_call(func, *args, **kwargs):
    ...

# from dxpy.utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/scripts/dx.py:2078
        cat_args = parser.parse_args(['cat'] + args.paths)
        cat_args.unicode_text = args.unicode_text
        cat(cat_args)
        return
    download(args)


def head(args):
```

Write `checks()` and `cases()` for `download`. Remember: setup in the thunk or at module level, never timed.