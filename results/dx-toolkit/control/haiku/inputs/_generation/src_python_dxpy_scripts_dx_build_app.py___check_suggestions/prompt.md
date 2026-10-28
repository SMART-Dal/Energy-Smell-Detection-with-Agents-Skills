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
Function under test: `_check_suggestions` in `src/python/dxpy/scripts/dx_build_app.py`
Import it as `from dxpy.scripts.dx_build_app import _check_suggestions`.

## The function
```python
def _check_suggestions(app_json, publish=False):
    """
    Examines the specified dxapp.json file and warns about any
    violations of suggestions guidelines.

    :raises: AppBuilderException for data objects that could not be found
    """
    for input_field in app_json.get('inputSpec', []):
        for suggestion in input_field.get('suggestions', []):
            if 'project' in suggestion:
                try:
                    project = dxpy.api.project_describe(suggestion['project'], {"permissions": True})
                    if 'PUBLIC' not in project['permissions'] and publish:
                        logger.warn('Project {name} NOT PUBLIC!'.format(name=project['name']))
                except dxpy.exceptions.DXAPIError as e:
                    if e.code == 404:
                        logger.warn('Suggested project {name} does not exist, or not accessible by user'.format(
                                     name=suggestion['project']))
                if 'path' in suggestion:
                    try:
                        check_folder_exists(suggestion['project'], suggestion['path'], '')
                    except ResolutionError as e:
                        logger.warn('Folder {path} could not be found in project {project}'.format(
                                     path=suggestion['path'], project=suggestion['project']))
            if '$dnanexus_link' in suggestion:
                if suggestion['$dnanexus_link'].startswith(('file-', 'record-')):
                    try:
                        dnanexus_link = dxpy.describe(suggestion['$dnanexus_link'])
                    except dxpy.exceptions.DXAPIError as e:
                        if e.code == 404:
                            raise dxpy.app_builder.AppBuilderException(
                                'Suggested object {name} could not be found'.format(
                                    name=suggestion['$dnanexus_link']))
                    except Exception as e:
                        raise dxpy.app_builder.AppBuilderException(str(e))
            if 'value' in suggestion and isinstance(suggestion["value"], dict):
                if '$dnanexus_link' in suggestion['value']:
                    # Check if we have JSON or string
                    if isinstance(suggestion['value']['$dnanexus_link'], dict):
                        if 'project' in suggestion['value']['$dnanexus_link']:
                            try:
                                dxpy.api.project_describe(suggestion['value']['$dnanexus_link']['project'])
                            except dxpy.exceptions.DXAPIError as e:
                                if e.code == 404:
                                    logger.warn('Suggested project {name} does not exist, or not accessible by user'.format(
                                                 name=suggestion['value']['$dnanexus_link']['project']))
                    elif isinstance(suggestion['value']['$dnanexus_link'], basestring):
                        if suggestion['value']['$dnanexus_link'].startswith(('file-', 'record-')):
                            try:
                                dnanexus_link = dxpy.describe(suggestion['value']['$dnanexus_link'])
                            except dxpy.exceptions.DXAPIError as e:
                                if e.code == 404:
                                    raise dxpy.app_builder.AppBuilderException(
                                        'Suggested object {name} could not be found'.format(
                                            name=suggestion['value']['$dnanexus_link']))
                            except Exception as e:
                                raise dxpy.app_builder.AppBuilderException(str(e))
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import logging
import os, sys, json, subprocess, argparse
import platform
import py_compile
import re
import shutil
import tempfile
import time
from datetime import datetime
import dxpy
import dxpy.app_builder
import dxpy.workflow_builder
import dxpy.executable_builder
from .. import logger
from dxpy.nextflow.nextflow_builder import build_pipeline_with_npi, prepare_nextflow
from dxpy.nextflow.nextflow_utils import get_resources_subpath, is_importer_job
from ..utils import json_load_raise_on_duplicates
from ..utils.resolver import resolve_path, check_folder_exists, ResolutionError, is_container_id
from ..utils.completer import LocalCompleter
from ..app_categories import APP_CATEGORIES
from ..exceptions import err_exit
from ..utils.printing import BOLD
from ..compat import USING_PYTHON2, basestring
from ..cli.parsers import process_extra_args
```

## Everything else its module defines (headers only)
```python
class DXSyntaxError(Exception):
    def __init__(self, message):
def _get_timestamp_version_suffix(version):
def _get_version_suffix(src_dir, version):
    # If anything goes wrong, fall back to the date-based suffix.
def parse_destination(dest_str):
def _create_temporary_build_project(name, bill_to=None, region=None):
    # An explicit null drive keeps the build on DNAnexus storage; omitting it
    # would inherit the billTo's default storage, which may be a drive.
def _lint(dxapp_json_filename, mode):
def _check_syntax(code, lang, temp_dir, enforce=True):
def _error_message_to_string(e, message):
def _check_file_syntax(filename, temp_dir, override_lang=None, enforce=True):
def _verify_app_source_dir_impl(src_dir, temp_dir, mode, enforce=True):
def _get_all_cluster_bootstrap_script_names(manifest):
    # runSpec.systemRequirements is deprecated. Enforce use of regionalOptions.
def _verify_app_source_dir(src_dir, mode, enforce=True):
def _parse_app_spec(src_dir):
def _build_app_remote(mode, src_dir, publish=False, destination_override=None,
                      version_override=None, bill_to_override=None,
                      do_version_autonumbering=True, do_try_update=True, do_parallel_build=True,
                      do_check_syntax=True, region=None, watch=True):
def build_app_from(applet_desc, version, publish=False, do_try_update=True, bill_to_override=None,
                   return_object_dump=False, confirm=True, brief=False, **kwargs):
def build_and_upload_locally(src_dir, mode, overwrite=False, archive=False, publish=False, destination_override=None,
                             version_override=None, bill_to_override=None, use_temp_build_project=True,
                             do_parallel_build=True, do_version_autonumbering=True, do_try_update=True,
                             do_check_syntax=True, dry_run=False,
                             return_object_dump=False, confirm=True, ensure_upload=False, force_symlinks=False,
                             region=None, brief=False, resources_dir=None, worker_resources_subpath="", **kwargs):
def get_destination_region(destination):
def get_project_to_check(destination, extra_args):
    # extra args overrides the destination argument
    # so we're checking it first
def verify_nf_license(destination, extra_args):
def _build_app(args, extra_args):
def build(args):
def main(**kwargs):
```

## Signatures of what its module imports from the repository
```python
# from ..utils.resolver import check_folder_exists
def check_folder_exists(project, path, folder_name):
    """:param project: project id"""
    ...

# from ..utils.resolver import ResolutionError
class ResolutionError(DXError):
    def __init__(self, msg):
        ...

# from dxpy.nextflow.nextflow_builder import build_pipeline_with_npi
def build_pipeline_with_npi(
        repository=None,
        tag=None,
        cache_docker=False,
        docker_secrets=None,
        nextflow_pipeline_params="",
        profile="",
        git_creds=None,
        brief=False,
        destination=None,
        extra_args=None,
        nextflow_version=None
):
    """:param repository: URL to a Git repository"""
    ...

# from dxpy.nextflow.nextflow_builder import prepare_nextflow
def prepare_nextflow(
        resources_dir,
        profile,
        region,
        cache_docker=False,
        nextflow_pipeline_params="",
        nextflow_version=None
):
    """:param resources_dir: Directory with all resources needed for the Nextflow pipeline. Usually directory with user's Nextflow files."""
    ...

# from dxpy.nextflow.nextflow_utils import get_resources_subpath
def get_resources_subpath(resources_dir):
    ...

# from dxpy.nextflow.nextflow_utils import is_importer_job
def is_importer_job():
    ...

# from ..utils import json_load_raise_on_duplicates
def json_load_raise_on_duplicates(*args, **kwargs):
    """Like json.load(), but raises an error on duplicate keys."""
    ...

# from ..utils.resolver import resolve_path
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
    """:param path: A path to a data object to attempt to resolve"""
    ...

# from ..utils.resolver import is_container_id
def is_container_id(string):
    ...

# from ..utils.completer import LocalCompleter
class LocalCompleter():
    def __init__(self):
        ...
    def get_matches(self, line, point, prefix, suffix):
        ...
    def complete(self, text, state):
        ...

# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from ..utils.printing import BOLD
def BOLD(message=None):
    ...

# from ..cli.parsers import process_extra_args
def process_extra_args(args):
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/scripts/dx_build_app.py:767
                             region=None, brief=False, resources_dir=None, worker_resources_subpath="", **kwargs):
    dxpy.app_builder.build(src_dir, parallel_build=do_parallel_build)
    app_json = _parse_app_spec(src_dir)

    _check_suggestions(app_json, publish=publish)
    _verify_app_source_dir(src_dir, mode, enforce=do_check_syntax)
    if mode == "app" and not dry_run:
        dxpy.executable_builder.verify_developer_rights('app-' + app_json['name'])

# src/python/dxpy/scripts/dx_build_app.py:1208
                extra_args=extra_args,
                nextflow_version=args.nextflow_version
            )
        app_json = _parse_app_spec(source_dir)
        _check_suggestions(app_json, publish=args.publish)
        _verify_app_source_dir(source_dir, args.mode)
        if args.mode == "app" and not args.dry_run:
            dxpy.executable_builder.verify_developer_rights('app-' + app_json['name'])
```

Write `checks()` and `cases()` for `_check_suggestions`. Remember: setup in the thunk or at module level, never timed.