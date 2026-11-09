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
Function under test: `TestDXClientRun.test_dx_describe_job_with_resolved_jbors` in `src/python/test/test_dxclient.py`
Import it as `from test_dxclient import TestDXClientRun`; the method is called as `TestDXClientRun.test_dx_describe_job_with_resolved_jbors(instance, ...)`.

## The function
```python
    @unittest.skipUnless(testutil.TEST_RUN_JOBS,
                         'skipping tests that would run jobs')
    def test_dx_describe_job_with_resolved_jbors(self):
        applet_id = dxpy.api.applet_new({"project": self.project,
                                         "dxapi": "1.0.0",
                                         "inputSpec": [{"name": "array", "class": "array:int"}],
                                         "outputSpec": [{"name": "array", "class": "array:int"}],
                                         "runSpec": {"interpreter": "python3",
                                                     "distribution": "Ubuntu",
                                                     "release": "20.04",
                                                     "version": "0",
                                                     "code": '''#!/usr/bin/env python3

@dxpy.entry_point('main')
def main(array):
    output = {"array": array}
    return output
'''}})['id']
        first_job_handler = dxpy.DXJob(dxpy.api.applet_run(applet_id,
                                                           {"project": self.project,
                                                            "input": {"array": [0, 1, 5]}})['id'])

        # Launch a second job which depends on the first, using two
        # arrays in an array (to be flattened) as input
        second_job_run_input = {"project": self.project,
                                "input": {"array": [first_job_handler.get_output_ref("array"),
                                                    first_job_handler.get_output_ref("array")]}}
        second_job_handler = dxpy.DXJob(dxpy.api.applet_run(applet_id, second_job_run_input)['id'])
        first_job_handler.wait_on_done()
        # Need to wait for second job to become runnable (idle and
        # waiting_on_input are the only states before it becomes
        # runnable)
        while second_job_handler.describe()['state'] in ['idle', 'waiting_on_input']:
            time.sleep(0.1)
        second_job_desc = run("dx describe " + second_job_handler.get_id())
        first_job_res = first_job_handler.get_id() + ":array => [ 0,\n                                   1, 5 ]"
        self.assertIn(first_job_res, second_job_desc)

        # Launch another job which depends on the first done job and
        # the second (not-done) job; the first job can and should be
        # mentioned in the resolved JBORs list, but the second
        # shouldn't.
        third_job_run_input = {"project": self.project,
                               "input": {"array": [first_job_handler.get_output_ref("array"),
                                                   first_job_handler.get_output_ref("array", index=2),
                                                   second_job_handler.get_output_ref("array")]}}
        third_job = dxpy.api.applet_run(applet_id, third_job_run_input)['id']
        third_job_desc = run("dx describe " + third_job)
        self.assertIn(first_job_res, third_job_desc)
        self.assertIn(first_job_handler.get_id() + ":array.2 => 5", third_job_desc)
        self.assertNotIn(second_job_handler.get_id() + ":array =>", third_job_desc)
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class TestDXClientRun(DXTestCase):
    def setUp(self):
        ...
    def tearDown(self):
        ...
    def test_dx_run_disallow_project_and_folder(self):
        ...
    @contextmanager
    def configure_ssh(self, use_alternate_config_dir=False):
        ...
    @pytest.mark.TRACEABILITY_MATRIX
    @testutil.update_traceability_matrix(["DNA_CLI_APP_RUN_APPLET","DNA_API_DATA_OBJ_RUN_APPLET"])
    def test_dx_run_applet_with_input_spec(self):
        ...
    def test_dx_run_applet_without_input_spec(self):
        ...
    def test_dx_resolve(self):
        ...
    def test_dx_resolve_check_resolution_needed(self):
        # If no entity_name is given, no entity_name should be returned
        ...
    def test_dx_run_depends_on_success(self):
        ...
    def test_dx_run_depends_on_failure(self):
        ...
    def test_dx_run_no_hidden_executables(self):
        # hidden applet
        ...
    @unittest.skipUnless(testutil.TEST_RUN_JOBS,
                         'skipping tests that would run jobs')
    def test_dx_run_jbor_array_ref(self):
        ...
    @pytest.mark.TRACEABILITY_MATRIX
    @testutil.update_traceability_matrix(["DNA_CLI_EXE_WATCH_LOGS", "DNA_CLI_EXE_TERMINATE"])
    @unittest.skipUnless(testutil.TEST_RUN_JOBS,
                         'skipping tests that would run jobs')
    def test_dx_run_priority(self):
        ### Helper functions
        ...
    @unittest.skipUnless(testutil.TEST_RUN_JOBS,
                         'skipping tests that would run jobs')
    def test_dx_run_head_job_on_demand(self):
        ...
    def test_dx_run_tags_and_properties(self):
        # success
        ...
    def test_dx_run_extra_args(self):
        # success
        ...
    def test_dx_run_extra_args_instanceTypeSelector_rejected(self):
        # Validate that instanceTypeSelector cannot be specified in runtime extra-args
        ...
    def test_dx_run_sys_reqs(self):
        ...
    def test_dx_run_clone_nvidia_driver(self):
        """
        Run the applet and clone the origin job. Verify nvidiaDriver value.
        """
        ...
    def test_dx_run_clone_with_instance_type_selector(self):
        """
        Test that when cloning a job from an applet that uses instanceTypeSelector:
        1. Cloning without runtime args works - instanceTypeSelector is preserved
        2. Cloning with --instance-type works - runtime instanceType overrides instanceTypeSelector
        3. Cloning with --instance-count fails - clusterSpec and instanceTypeSelector are mutually exclusive
        4. Job description contains instanceTypeSelector in systemRequirements
        """
        ...
    def test_dx_run_clone(self):
        ...
    @unittest.skipUnless(testutil.TEST_RUN_JOBS,
                         'skipping tests that would run jobs')
    def test_dx_describe_job_with_resolved_jbors(self):
        applet_id = dxpy.api.applet_new({"project": self.project,
                                         "dxapi": "1.0.0",
                                         "inputSpec": [{"name": "array", "class": "array:int"}],
                                         "outputSpec": [{"name": "array", "class": "array:int"}],
                                         "runSpec": {"interpreter": "python3",
                                                     "distribution": "Ubuntu",
                                                     "release": "20.04",
                                                     "version": "0",
                                                     "code": '''#!/usr/bin/env python3

@dxpy.entry_point('main')
def main(array):
    output = {"array": array}
    return output
'''}})['id']
        first_job_handler = dxpy.DXJob(dxpy.api.applet_run(applet_id,
                                                           {"project": self.project,
                                                            "input": {"array": [0, 1, 5]}})['id'])

        # Launch a second job which depends on the first, using two
        # arrays in an array (to be flattened) as input
        second_job_run_input = {"project": self.project,
                                "input": {"array": [first_job_handler.get_output_ref("array"),
                                                    first_job_handler.get_output_ref("array")]}}
        second_job_handler = dxpy.DXJob(dxpy.api.applet_run(applet_id, second_job_run_input)['id'])
        first_job_handler.wait_on_done()
        # Need to wait for second job to become runnable (idle and
        # waiting_on_input are the only states before it becomes
        # runnable)
        while second_job_handler.describe()['state'] in ['idle', 'waiting_on_input']:
            time.sleep(0.1)
        second_job_desc = run("dx describe " + second_job_handler.get_id())
        first_job_res = first_job_handler.get_id() + ":array => [ 0,\n                                   1, 5 ]"
        self.assertIn(first_job_res, second_job_desc)

        # Launch another job which depends on the first done job and
        # the second (not-done) job; the first job can and should be
        # mentioned in the resolved JBORs list, but the second
        # shouldn't.
        third_job_run_input = {"project": self.project,
                               "input": {"array": [first_job_handler.get_output_ref("array"),
                                                   first_job_handler.get_output_ref("array", index=2),
                                                   second_job_handler.get_output_ref("array")]}}
        third_job = dxpy.api.applet_run(applet_id, third_job_run_input)['id']
        third_job_desc = run("dx describe " + third_job)
        self.assertIn(first_job_res, third_job_desc)
        self.assertIn(first_job_handler.get_id() + ":array.2 => 5", third_job_desc)
        self.assertNotIn(second_job_handler.get_id() + ":array =>", third_job_desc)
    def test_dx_run_ssh_no_config(self):
        # Create minimal applet.
        ...
    @unittest.skipUnless(testutil.TEST_RUN_JOBS, "skipping test that would run jobs")
    def test_bundledDepends_name_with_whitespaces(self):
        # upload a tar.gz file with spaces in its name
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, unittest, json, tempfile, subprocess, shutil, re, base64, random, time
import filecmp
import shlex
import stat
import hashlib
import collections
import string
from contextlib import contextmanager
import pexpect
import requests
import textwrap
import pytest
import gzip
import tarfile
from mock import patch
import dxpy
import dxpy.executable_builder
import dxpy.workflow_builder
from dxpy.scripts import dx_build_app
from dxpy_testutil import (DXTestCase, DXTestCaseBuildApps, DXTestCaseBuildWorkflows, check_output, temporary_project,
                           select_project, cd, override_environment, generate_unique_username_email,
                           without_project_context, without_auth, as_second_user, chdir, run, DXCalledProcessError)
import dxpy_testutil as testutil
from dxpy.exceptions import DXAPIError, DXSearchError, EXPECTED_ERR_EXIT_STATUS, HTTPError
from dxpy.utils.resolver import ResolutionError, _check_resolution_needed as check_resolution
```

## Everything else its module defines (headers only)
```python
class TestDXTestUtils(DXTestCase):
    # methods: test_temporary_project, test_select_project, test_without_project_context, test_as_second_user
class TestDXRemove(DXTestCase):
    # methods: test_remove_objects, test_remove_nonexistent_object, test_remove_folders
class TestApiDebugOutput(DXTestCase):
    # methods: test_dx_debug_shows_request_id, test_dx_debug_shows_timestamp, test_dx_debug_shows_request_response, test_upload_binary_data
class TestDXClient(DXTestCase):
    # methods: test_dx_version, test_dx, test_head, test_path_resolution_doesnt_crash, test_windows_pager, test_get_unicode_url, test_dx_env, test_dx_api, test_dx_invite, test_dx_uninvite, test_dx_add_missing_arguments, test_dx_add_rm_types, ...
class TestDXNewRecord(DXTestCase):
    # methods: test_new_record_basic, test_dx_new_record_with_close, test_new_record_without_context
class TestDXWhoami(DXTestCase):
    # methods: test_dx_whoami_name, test_dx_whoami_id
class TestDXRmdir(DXTestCase):
    # methods: test_dx_rmdir
class TestDXMv(DXTestCase):
    # methods: test_dx_mv, test_dx_mv_folder
class TestDXRename(DXTestCase):
    # methods: test_rename
class TestDXClientUploadDownload(DXTestCase):
    # methods: test_dx_download_recursive_overwrite, test_dx_upload_download, test_dx_upload_with_upload_perm, test_dx_download_no_env, test_dx_upload_no_env, test_dx_make_download_url, test_dx_download_when_current_project_inaccessible, test_dx_upload_mult_paths, test_dx_upload_mult_paths_with_dest, test_dx_upload_mult_hidden, test_dx_upload_empty_file, test_dx_upload_empty_file_azure, ...
class TestDXClientDownloadDataEgressBilling(DXTestCase):
    # methods: gen_file, get_billed_project, prologue, setUp, tearDown, test_dx_cat_project_context, test_dx_download_project_context, test_dx_download_project_explicit, test_dx_download_multiple_projects_with_same_name
class TestDXClientFind(DXTestCase):
    # methods: assert_cmd_gives_ids, test_dx_find_apps_and_globalworkflows_category, test_dx_find_apps, test_dx_find_globalworkflows, test_dx_find_data_formatted, test_dx_find_data_by_name, test_dx_find_data_by_class, test_dx_find_data_by_tag, test_dx_find_data_by_property, test_dx_find_data_by_scope, test_dx_find_data_by_region, test_dx_find_projects, ...
class TestDXClientOrg(DXTestCase):
    # methods: get_unique_org_handle, setUp, test_create_new_org_negative, test_create_new_org, test_create_new_org_prompt, test_org_update_negative, test_org_update, test_org_update_format
class TestDXClientNewProject(DXTestCase):
    # methods: test_dx_new_project_with_region, test_dx_create_new_project_with_bill_to, test_dx_create_new_project_with_phi
class TestDXClientNewUser(DXTestCase):
    # methods: setUp, tearDown, test_create_user_account_and_set_bill_to_negative, test_create_user_on_behalf_of, test_create_user_on_behalf_of_negative, test_self_signup_negative, test_create_user_account_only, test_create_user_account_and_invite_to_org, test_create_user_account_and_set_bill_to, test_create_user_account_and_set_token_duration_negative, test_create_user_account_and_set_token_duration
class TestDXClientMembership(DXTestCase):
    # methods: setUp, tearDown, test_add_membership_default, test_add_membership_with_options, test_add_membership_negative, test_remove_membership_default, test_remove_membership_interactive_conf, test_remove_membership_interactive_conf_format, test_remove_membership_negative, test_update_membership_positive, test_update_membership_to_member_without_membership_flags, test_update_membership_negative, ...
class TestDXClientUpdateProject(DXTestCase):
    # methods: setUp, tearDown, project_describe, test_update_strings, test_update_multiple_items, test_update_project_by_name, test_update_booleans, test_bill_non_existent_user
class TestHTTPProxySupport(DXTestCase):
    # methods: setUp, test_proxy, tearDown
class TestDXScripts(DXTestCase):
    # methods: test_minimal_invocation
class TestDXCp(DXTestCase):
    # methods: setUpClass, tearDownClass, gen_uniq_fname, verify_folders_are_equal, verify_file_ids_are_equal, test_file_with_same_name, test_cp_rename, test_multiple_args, test_cp_dir, test_copy_empty_folder_on_existing_folder, test_copy_folder_on_existing_folder, test_copy_overwrite, ...
class TestDXLs(DXTestCase):
    # methods: test_regular_output, test_long_output
class TestDXTree(DXTestCase):
    # methods: test_regular_output, test_tree
class TestDXGenerateBatchInputs(DXTestCase):
    # methods: test_example_matches
class TestDXRun(DXTestCase):
    # methods: test_dx_run_app, test_dx_run_specific_project, test_applet_prefix_resolve_does_not_send_app_describe_request, test_workflow_prefix_resolve_does_not_send_app_describe_request
class TestDXArchive(DXTestCase):
    # methods: setUpClass, tearDownClass, gen_uniq_fname, test_archive_files, test_archive_files_allmatch, test_archive_folder, test_archive_equivalent_paths, test_archive_invalid_paths, test_archive_allcopies, test_unarchive_dryrun
class TestDXPYImport(unittest.TestCase):
    # methods: test_dxpy_import_stdin_none
class TestDXClientDescribe(DXTestCaseBuildWorkflows):
    # methods: test_projects, test_bad_current_project, test_user_describe_self_shows_bill_to, test_describe_deleted_app, test_describe_applet_with_bundled_objects, test_describe_global_workflow, test_describe_analysis_verbose, test_describe_job_verbose
class TestDXClientWorkflow(DXTestCaseBuildWorkflows):
    # methods: test_dx_run_workflow, test_dx_run_clone_analysis, test_dx_run_workflow_prints_cached_executions, test_dx_run_workflow_with_inst_type_requests, test_dx_run_workflow_with_stage_folders, test_inaccessible_stage, test_dx_new_workflow_without_context, test_dx_new_workflow, test_dx_workflow_resolution, test_dx_describe_workflow, test_dx_add_remove_list_stages, test_dx_update_workflow, ...
class TestDXClientGlobalWorkflow(DXTestCaseBuildWorkflows):
    # methods: test_dx_run_global_workflow, test_dx_update_global_workflow, test_build_multi_region_workflow_with_applet, test_build_workflow_with_regional_resources, test_build_workflow_with_regional_resources_from_extra_args, test_build_workflow_in_invalid_multi_regions, test_build_multi_region_workflow_with_apps
class TestDXClientFindInOrg(DXTestCaseBuildApps):
    # methods: setUpClass, tearDownClass, test_dx_find_org_members_negative, test_dx_find_org_members, test_dx_find_org_members_format, test_dx_find_org_projects_invalid, test_dx_find_org_projects, test_dx_find_org_projects_public, test_dx_find_org_projects_created, test_dx_find_org_projects_format, test_dx_find_org_projects_phi, test_dx_find_org_apps
class TestDXBuildWorkflow(DXTestCaseBuildWorkflows):
    # methods: test_build_single_region_workflow, test_build_workflow_warnings, test_build_workflow_invalid_project_context, test_build_workflow_with_tree_tat_threshold, test_build_workflow_with_bill_to, test_build_workflow_without_bill_to_rights, test_build_workflow_with_invalid_bill_to, test_build_globalworkflow_from_nonexist_workflow, test_build_globalworkflow_without_version_override, test_build_globalworkflow_with_workflow_path, test_build_globalworkflow_from_old_WDL_workflow, test_dx_add_list_remove_users_of_global_workflows, ...
class TestSparkClusterApps(DXTestCaseBuildApps):
    # methods: test_build_and_get_cluster_app_bootstrap_script_inlined
class TestDXBuildApp(DXTestCaseBuildApps):
    # methods: run_and_assert_stderr_matches, test_help_without_security_context, test_accepts_semver, test_version_suffixes, test_build_applet, test_build_applet_with_extra_args, test_dx_build_applet_dxapp_json_created_with_makefile, test_dx_build_applet_no_app_linting, test_build_applet_dry_run, test_build_applet_and_run_immediately, test_build_applet_tree_tat_threshold_and_run, test_remote_build_applet_and_run_immediately, ...
class TestDXGetWorkflows(DXTestCaseBuildWorkflows):
    # methods: test_get_workflow, test_get_global_workflow, test_dx_cross_get_and_build_workflows
class TestDXGetAppsAndApplets(DXTestCaseBuildApps):
    # methods: test_get_applet, test_get_applet_omit_resources, test_get_applet_field_cleanup, test_get_applet_on_windows, make_app, assert_app_get_initialized, test_get_app, test_dx_cross_get_and_build_app_and_applet, test_get_app_by_name, test_get_app_omit_resources, test_uninstall_app, test_get_preserves_system_requirements, ...
class TestTcshEnvironment(unittest.TestCase):
    # methods: test_tcsh_dash_c, test_tcsh_source_environment
class TestDXUpdateApp(DXTestCaseBuildApps):
    # methods: test_update_app
def create_file_in_project(fname, trg_proj_id, folder=None):
def create_project():
def rm_project(proj_id):
def create_folder_in_project(proj_id, path):
def list_folder(proj_id, path):
def run_and_parse_json(cmd):
```

## Signatures of what its module imports from the repository
```python
# from dxpy_testutil import run
def run(command, **kwargs):
    ...

# from dxpy_testutil import DXTestCase
class DXTestCase(DXTestCaseCompat):
    def setUp(self):
        ...
    def tearDown(self):
        ...
    @contextmanager
    def assertSubprocessFailure(self, output_regexp=None, output_text=None, stderr_regexp=None, stderr_text=None, exit_code=3):
        """Asserts that the block being wrapped exits with CalledProcessError."""
        ...
    def assertFileContentsEqualsString(self, path, s):
        ...
    def assertDictSubsetOf(self, subset_dict, containing_dict):
        ...
    def write_app_directory_in_dir(self, temp_file_path, app_name, dxapp_str, code_filename, code_content):
        # Note: if called twice with the same app_name, will overwrite
        # the dxapp.json and code file (if specified) but will not
        # remove any other files that happened to be present
        ...

# from dxpy_testutil import DXTestCaseBuildApps
class DXTestCaseBuildApps(DXTestCase):
    base_app_spec = dict(base_applet_spec, version="1.0.0")
    def setUp(self):
        ...
    def tearDown(self):
        ...
    def make_apps(self, num_apps, name_prefix, bill_to=None):
        ...
    def write_app_directory(self, app_name, dxapp_str, code_filename=None, code_content="\n"):
        # Note: if called twice with the same app_name, will overwrite
        # the dxapp.json and code file (if specified) but will not
        # remove any other files that happened to be present
        ...

# from dxpy_testutil import DXTestCaseBuildWorkflows
class DXTestCaseBuildWorkflows(DXTestCase):
    def setUp(self):
        ...
    def tearDown(self):
        ...
    def write_workflow_directory(self, workflow_name, dxworkflow_str,
                                 readme_content="Workflow doc", build_basic=False):
        # Note: if called twice with the same workflow_name, will overwrite
        # the dxworkflow.json and code file (if specified) but will not
        # remove any other files that happened to be present
        ...
    def create_applet_spec(self, project_id):
        ...
    def create_applet(self, project_id):
        ...
    def create_workflow_spec(self, project_id):
        ...
    def create_workflow(self, project_id, workflow_spec=None):
        ...
    def create_global_workflow_spec(self, project_id, name, version, workflow_spec=None):
        ...
    def create_global_workflow(self, project_id, name, version, workflow_spec=None):
        ...
    def create_dxworkflow_spec(self):
        ...
    def write_app_directory(self, app_name, dxapp_str, code_filename=None, code_content="\n"):
        ...

# from dxpy_testutil import check_output
def check_output(*popenargs, **kwargs):
    """Adapted version of the builtin subprocess.check_output which sets a"""
    ...

# from dxpy_testutil import temporary_project
@contextmanager
def temporary_project(name='dx client tests temporary project', cleanup=True, reclaim_permissions=False, select=False,
                      region=None, **kwargs):
    """Creates a temporary project scoped to the context manager, and"""
    ...

# from dxpy_testutil import select_project
@contextmanager
def select_project(project_or_project_id):
    """Selects a project by setting the DX_PROJECT_CONTEXT_ID in"""
    ...

# from dxpy_testutil import cd
def cd(directory):
    ...

# from dxpy_testutil import override_environment
def override_environment(**kwargs):
    """Returns a copy of the current environment, with variables overridden"""
    ...

# from dxpy_testutil import generate_unique_username_email
def generate_unique_username_email():
    ...

# from dxpy_testutil import without_project_context
@contextmanager
def without_project_context():
    """Within the scope of the block, the project context and workspace"""
    ...

# from dxpy_testutil import without_auth
@contextmanager
def without_auth():
    """Within the scope of the block, the auth configuration variable (and"""
    ...

# from dxpy_testutil import as_second_user
def as_second_user():
    ...

# from dxpy_testutil import chdir
@contextmanager
def chdir(dirname=None):
    ...

# from dxpy_testutil import DXCalledProcessError
class DXCalledProcessError(subprocess.CalledProcessError):
    def __init__(self, returncode, cmd, output=None, stderr=None):
        ...
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `TestDXClientRun.test_dx_describe_job_with_resolved_jbors`. Remember: setup in the thunk or at module level, never timed.