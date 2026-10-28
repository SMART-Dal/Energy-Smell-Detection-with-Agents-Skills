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
Function under test: `TestDXSearch.test_resolve_data_objects` in `src/python/test/test_dxpy.py`
Import it as `from test_dxpy import TestDXSearch`; the method is called as `TestDXSearch.test_resolve_data_objects(instance, ...)`.

## The function
```python
    def test_resolve_data_objects(self):
        # If the project is provided for an object, then it will be used instead of
        # the top-level project specification
        with testutil.temporary_project(name='test_resolve_data_objects') as p:
            dxrecord0 = dxpy.new_dxrecord(name="myrecord0", project=self.proj_id)
            dxrecord1 = dxpy.new_dxrecord(name="myrecord1", project=p.get_id())
            dxpy.new_dxrecord(name="myrecord2", project=self.proj_id)
            dxpy.new_dxrecord(name="myrecord3", project=p.get_id())
            records = [{"name": "myrecord0", "project": self.proj_id, "folder": "/"},
                       {"name": "myrecord1"},
                       {"name": "myrecord2"},
                       {"name": "myrecord3", "project": self.proj_id, "folder": "/"}]

            objects = list(dxpy.search.resolve_data_objects(records, project=p.get_id()))
            self.assertEqual(len(objects), 4)
            self.assertEqual(objects[0][0]["project"], self.proj_id)
            self.assertEqual(objects[0][0]["id"], dxrecord0.get_id())
            self.assertEqual(objects[1][0]["project"], p.get_id())
            self.assertEqual(objects[1][0]["id"], dxrecord1.get_id())
            self.assertEqual(objects[2], [])
            self.assertEqual(objects[3], [])

        # Test that batching happens correctly
        record_names = []
        record_ids = []
        for i in range(1005):
            record_ids.append(dxpy.new_dxrecord(name=("record" + str(i))).get_id())
            record_names.append({"name": "record" + str(i)})
        objects = list(dxpy.search.resolve_data_objects(record_names, project=self.proj_id))
        self.assertEqual(len(objects), 1005)
        self.assertEqual(objects[200][0]["id"], record_ids[200])
        self.assertEqual(objects[1003][0]["id"], record_ids[1003])
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class TestDXSearch(testutil.DXTestCaseCompat):
    def setUp(self):
        ...
    def tearDown(self):
        ...
    def assertItemsEqual(self, a, b):
        ...
    def test_resolve_data_objects(self):
        # If the project is provided for an object, then it will be used instead of
        # the top-level project specification
        with testutil.temporary_project(name='test_resolve_data_objects') as p:
            dxrecord0 = dxpy.new_dxrecord(name="myrecord0", project=self.proj_id)
            dxrecord1 = dxpy.new_dxrecord(name="myrecord1", project=p.get_id())
            dxpy.new_dxrecord(name="myrecord2", project=self.proj_id)
            dxpy.new_dxrecord(name="myrecord3", project=p.get_id())
            records = [{"name": "myrecord0", "project": self.proj_id, "folder": "/"},
                       {"name": "myrecord1"},
                       {"name": "myrecord2"},
                       {"name": "myrecord3", "project": self.proj_id, "folder": "/"}]

            objects = list(dxpy.search.resolve_data_objects(records, project=p.get_id()))
            self.assertEqual(len(objects), 4)
            self.assertEqual(objects[0][0]["project"], self.proj_id)
            self.assertEqual(objects[0][0]["id"], dxrecord0.get_id())
            self.assertEqual(objects[1][0]["project"], p.get_id())
            self.assertEqual(objects[1][0]["id"], dxrecord1.get_id())
            self.assertEqual(objects[2], [])
            self.assertEqual(objects[3], [])

        # Test that batching happens correctly
        record_names = []
        record_ids = []
        for i in range(1005):
            record_ids.append(dxpy.new_dxrecord(name=("record" + str(i))).get_id())
            record_names.append({"name": "record" + str(i)})
        objects = list(dxpy.search.resolve_data_objects(record_names, project=self.proj_id))
        self.assertEqual(len(objects), 1005)
        self.assertEqual(objects[200][0]["id"], record_ids[200])
        self.assertEqual(objects[1003][0]["id"], record_ids[1003])
    def test_find_data_objs(self):
        ...
    def test_find_data_objs_by_time(self):
        ...
    def test_find_data_objs_in_workspace(self):
        ...
    @pytest.mark.TRACEABILITY_MATRIX
    @testutil.update_traceability_matrix(["DNA_API_PROJ_VIEW_PROJECT_LIST"])
    def test_find_projects(self):
        ...
    @unittest.skipUnless(testutil.TEST_ISOLATED_ENV, 'skipping test that requires presence of test org')
    def test_find_org_projects_created(self):
        ...
    @unittest.skipUnless(testutil.TEST_RUN_JOBS, 'skipping test that would run a job')
    def test_find_executions(self):
        ...
    def test_find_one_fails_if_zero_ok_not_bool(self):
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, unittest, tempfile, filecmp, time, json, sys, random
import shutil
import string
import subprocess
import platform
import pytest
import re
import certifi
from mock import patch
from urllib3.exceptions import SSLError, NewConnectionError
import dxpy
import dxpy_testutil as testutil
from dxpy.exceptions import (DXAPIError, DXFileError, DXError, DXJobFailureError, ResourceNotFound)
from dxpy.scripts import dx_build_app
from dxpy.utils import pretty_print, warn, Nonce
from dxpy.utils.resolver import resolve_path, resolve_existing_path, ResolutionError, is_project_explicit
import dxpy.app_builder as app_builder
import dxpy.executable_builder as executable_builder
import dxpy.workflow_builder as workflow_builder
```

## Everything else its module defines (headers only)
```python
class TestDXProject(unittest.TestCase):
    # methods: setUp, tearDown, test_init_and_set_id, test_dxcontainer_init_and_set_id, test_invite_without_email, test_new, test_update_describe, test_new_list_remove_folders, test_move, test_clone, test_remove_objects
class TestDXFileFunctions(unittest.TestCase):
    # methods: test_readable_part_size, test_get_buffer_size, test_job_detection, test_generate_read_requests
class TestDXFile(testutil.DXTestCaseCompat):
    # methods: setUpClass, tearDownClass, setUp, tearDown, test_init_and_set_ids, test_upload_download_files_dxfile, test_attempt_to_upload_to_closed_file, test_upload_file_with_custom_auth, test_upload_string_dxfile, test_upload_empty_dxfile, test_upload_empty_dxfile_azure, test_write_read_dxfile, ...
class TestFolder(unittest.TestCase):
    # methods: setUp, tearDown, read_entire_file, test_download_folder
class TestDXRecord(testutil.DXTestCaseCompat):
    # methods: setUp, tearDown, test_set_id, test_create_remove_dxrecord, test_init_from, test_describe_dxrecord, test_getattr_dxrecord, test_set_properties_of_dxrecord, test_types_of_dxrecord, test_tags_of_dxrecord, test_visibility_of_dxrecord, test_rename_dxrecord, ...
class TestDXAppletJob(unittest.TestCase):
    # methods: setUp, tearDown, test_dxjob_init_and_set_id, test_run_dxapplet_and_job_metadata
class TestDXWorkflow(testutil.DXTestCaseCompat):
    # methods: setUp, tearDown, test_dxanalysis_init_and_set_id, test_run_workflow_and_analysis_metadata, test_run_locked_workflow, test_run_workflow_with_instance_type, test_run_workflow_with_stage_folders, test_run_workflow_errors, test_new_dxworkflow, test_add_move_remove_stages, test_get_stage, test_update, ...
class TestDXApp(unittest.TestCase):
    # methods: setUp, tearDown, test_init_and_set_id, test_create_app, test_add_and_remove_tags
class TestDXGlobalWorkflow(testutil.DXTestCaseBuildWorkflows):
    # methods: setUp, tearDown, test_init_and_set_id, test_create_globalworkflow, test_dx_find_global_workflows
class TestPrettyPrint(unittest.TestCase):
    # methods: test_string_escaping, test_format_timedelta
class TestWarn(unittest.TestCase):
    # methods: test_warn
class TestHTTPResponses(testutil.DXTestCaseCompat):
    # methods: test_content_type_no_sniff, test_retry_after, test_retry_after_exceeding_max_retries, test_retry_after_without_header_set, test_generic_exception_not_retryable, test_bad_host, test_connection_refused, test_case_insensitive_response_headers, test_ssl_options, test_system_headers_user_agent
class TestDataobjectFunctions(unittest.TestCase):
    # methods: setUp, tearDown, test_dxlink, test_get_handler, test_describe_data_objects
class TestResolver(testutil.DXTestCase):
    # methods: setUp, tearDown, test_resolve_path, test_resolve_existing_path, test_clean_folder_path, test_resolution_batching, test_is_project_explicit
class TestIdempotentRequests(unittest.TestCase):
    # methods: setUp, tearDown, assertItemsEqual, create_applet, do_retry_http_request, get_a_nonce, test_idempotent_record_creation, test_idempotent_applet_and_app_creation, test_idempotent_file_creation, test_idempotent_workflow_creation, test_idempotent_runs, test_idempotent_org_creation
class TestAppBuilderUtils(unittest.TestCase):
    # methods: test_temporary_build_project_clears_drive, test_temporary_build_project_omits_unset_options, test_assert_consistent_regions, test_validate_system_requirements_instance_type_selector, test_validate_system_requirements_in_regional_options
class TestWorkflowBuilderUtils(testutil.DXTestCaseBuildWorkflows):
    # methods: setUp, create_dxworkflow_spec, tearDown, test_clean_json_spec
class TestApiWrappers(unittest.TestCase):
    # methods: test_system_greet
def get_objects_from_listf(listf):
def remove_all(proj_id, folder="/"):
def setUpTempProjects(thing):
def tearDownTempProjects(thing):
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `TestDXSearch.test_resolve_data_objects`. Remember: setup in the thunk or at module level, never timed.