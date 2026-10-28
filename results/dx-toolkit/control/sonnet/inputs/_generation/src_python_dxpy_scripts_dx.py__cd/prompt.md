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
Function under test: `cd` in `src/python/dxpy/scripts/dx.py`
Import it as `from dxpy.scripts.dx import cd`.

## The function
```python
def cd(args):
    # entity_result should be None because expected='folder'
    project, folderpath = try_call(resolve_existing_path, args.path, 'folder')[:2]

    if project is not None:
        project_name = try_call(dxpy.get_handler(project).describe)['name']

        # It is obvious what the project is
        if project != dxpy.WORKSPACE_ID or 'DX_PROJECT_CONTEXT_NAME' not in os.environ:
            # Cache ID and name if necessary
            set_project(project, not state['interactive'], name=project_name)
            state['currentproj'] = project_name
    else:
        err_exit('Error: No current project was given', 3)

    # TODO: attempt to add caching later if it's an issue
    # if project in cached_project_paths and folderpath in cached_project_paths[project]:
    #     set_wd(folderpath, not interactive)

    try:
        dxproj = dxpy.get_handler(dxpy.WORKSPACE_ID)
        dxproj.list_folder(folder=folderpath, only='folders')
    except:
        err_exit(fill(folderpath + ': No such file or directory found in project ' + dxpy.WORKSPACE_ID), 3)

    set_wd(folderpath, not state['interactive'])
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, datetime, getpass, collections, re, json, argparse, copy, hashlib, io, time, subprocess, glob, logging, functools
import csv
from ..compat import sys_encoding, basestring
import dxpy
from dxpy.scripts import dx_build_app
from dxpy import workflow_builder
from dxpy.exceptions import PermissionDenied, InvalidState, ResourceNotFound, DXCLIError
from ..cli import try_call, prompt_for_yn, INTERACTIVE_CLI
from ..cli import workflow as workflow_cli
from ..cli.cp import cp
from ..cli.dataset_utilities import extract_dataset, extract_assay_germline, extract_assay_somatic, create_cohort, extract_assay_expression
from ..cli.download import (download_one_file, download_one_database_file, download)
from ..cli.parsers import (no_color_arg, delim_arg, env_args, stdout_args, all_arg, json_arg, try_arg, parser_dataobject_args,
                           parser_single_dataobject_output_args, process_properties_args,
                           find_by_properties_and_tags_args, process_find_by_property_args, process_dataobject_args,
                           process_single_dataobject_output_args, find_executions_args, add_find_executions_search_gp,
                           set_env_from_args, extra_args, process_extra_args, DXParserError, exec_input_args,
                           instance_type_arg, process_instance_type_arg, process_instance_type_by_executable_arg, process_instance_count_arg, get_update_project_args,
                           property_args, tag_args, contains_phi, process_phi_param, process_external_upload_restricted_param)
from ..cli.exec_io import (ExecutableInputs, format_choices_or_suggestions)
from ..cli.org import (get_org_invite_args, add_membership, remove_membership, update_membership, new_org, update_org,
                       find_orgs, org_find_members, org_find_projects, org_find_apps)
from ..exceptions import (err_exit, DXError, DXCLIError, DXAPIError, network_exceptions, default_expected_exceptions,
                          format_exception)
from ..utils import warn, group_array_by_field, normalize_timedelta, normalize_time_input, merge
from ..utils.batch_utils import (batch_run, batch_launch_args)
from ..app_categories import APP_CATEGORIES
from ..utils.printing import (CYAN, BLUE, YELLOW, GREEN, RED, WHITE, UNDERLINE, BOLD, ENDC, DNANEXUS_LOGO,
                              DNANEXUS_X, set_colors, set_delimiter, get_delimiter, DELIMITER, fill,
                              tty_rows, tty_cols, pager, format_find_results, nostderr)
from ..utils.pretty_print import format_tree, format_table
from ..utils.resolver import (clean_folder_path, pick, paginate_and_pick, is_hashid, is_data_obj_id, is_container_id, is_job_id,
                              is_analysis_id, get_last_pos_of_char, resolve_container_id_or_name, resolve_path,
                              resolve_existing_path, get_app_from_path, resolve_app, resolve_global_executable, get_exec_handler,
                              split_unescaped, ResolutionError, resolve_to_objects_or_project, is_project_explicit,
                              object_exists_in_project, is_jbor_str, parse_input_keyval)
from ..utils.completer import (path_completer, DXPathCompleter, DXAppCompleter, LocalCompleter,
                               ListCompleter, MultiCompleter)
from ..utils.describe import (print_data_obj_desc, print_desc, print_ls_desc, get_ls_l_desc, print_ls_l_header,
    # ... (truncated)
```

## Definitions it uses from the same module
```python
state = {"interactive": False,
         "colors": "auto",
         "delimiter": None,
         "currentproj": None}

def set_project(project, write, name=None):
    if dxpy.JOB_ID is None:
        dxpy.config["DX_PROJECT_CONTEXT_ID"] = project
        dxpy.config["DX_PROJECT_CONTEXT_NAME"] = name
    else:
        dxpy.config["DX_WORKSPACE_ID"] = project
    if write:
        dxpy.config.save()
    dxpy.set_workspace_id(project)

def set_wd(folder, write):
    dxpy.config.update(DX_CLI_WD=folder)
    if write:
        dxpy.config.save()

def describe(args):

    def describe_global_executable(json_output, args, exec_type):
        """
        Describes a global executable, i.e. either app or global workflow
        depending on the provided exec_type. Appends the result to json_output.
        Returns True if any matches were found
        """
        assert(exec_type in ('app', 'globalworkflow'))
        found_match = False

        try:
            if exec_type == 'app':
                desc = dxpy.api.app_describe(args.path)
            else:
                desc = dxpy.api.global_workflow_describe(args.path)
                desc = dxpy.append_underlying_workflow_describe(desc)
            if args.json:
                json_output.append(desc)
            elif args.name:
                print(desc['name'])
            else:
                print(get_result_str())
                print_desc(desc, args.verbose)
            found_match = True
        except dxpy.DXAPIError as e:
            if not isinstance(e, ResourceNotFound):
                raise e

        return found_match

    def find_global_executable(json_output, args):
        """
        Makes a find_apps API call and, if no matches are found, a find_global_workflows call.
        Since these two objects share namespace, either app or a global workflow will be
        found, not both. The results are appended to json_output and printed to STDOUT.
        """

        def append_to_output_json_and_print(result):
            if args.json:
                json_output.append(result['describe'])
            elif args.name:
                print(result['describe']['name'])
            else:
                print(get_result_str())
                print_desc(result['describe'], args.verbose)

        found_match = False
        for result in dxpy.find_apps(name=args.path, describe=True):
            append_to_output_json_and_print(result)
            found_match = True
        if not found_match:
            for result in dxpy.find_global_workflows(name=args.path, describe=True):
                result['describe'] = dxpy.append_underlying_workflow_describe(result['describe'])
                append_to_output_json_and_print(result)
                found_match = True
        return found_match

    try:
        if len(args.path) == 0:
    # ... (truncated)
```

## Everything else its module defines (headers only)
```python
class ResultCounter():
    def __init__(self):
class DXCLICompleter():
    def __init__(self):
    # methods: get_command_matches, get_subcommand_matches, get_matches, complete
class runHelp(argparse.Action):
class runInputHelp(argparse.Action):
class SetStagingEnv(argparse.Action):
class PrintDXVersion(argparse.Action):
class PrintCategoryHelp(argparse.Action):
class DXNewUserOrgArgsAction(argparse.Action):
    def __init__(self, option_strings, dest, required=False, default=None,
                 nargs=None, **kwargs):
class DXArgumentParser(argparse.ArgumentParser):
    # methods: exit, error
class MetricsHelpAction(argparse.Action):
def filter_verbose_fields(description, entity_id):
def eprint(*args, **kwargs):
def get_json_from_stdin():
def set_cli_colors(args=argparse.Namespace()):
def set_delim(args=argparse.Namespace()):
def login(args):
def logout(args):
def set_api(protocol, host, port, write):
def prompt_for_env_var(prompt_str, env_var_str):
def pick_and_set_project(args):
def whoami(args):
def setenv(args):
def clearenv(args):
def env(args):
def get_pwd():
def pwd(args):
def api(args):
def invite(args):
    # If --project is a valid project (ID or name), then appending ":"
    # should not hurt the path resolution.
def uninvite(args):
    # If --project is a valid project (ID or name), then appending ":"
    # should not hurt the path resolution.
def select(args):
def cmp_names(x):
def ls(args):
def mkdir(args):
def rmdir(args):
def rm(args):
def rmproject(args):
def mv(args):
def tree(args):
def _validate_new_user_input(args):
    # TODO: Support interactive specification of `args.username`.
    # TODO: Support interactive specification of `args.email`.
def _get_user_new_args(args):
def new_user(args):
def new_project(args):
def new_record(args):
def set_visibility(args):
def get_details(args):
    # Attempt to resolve name
def set_details(args):
def add_types(args):
def remove_types(args):
def add_tags(args):
def remove_tags(args):
def rename(args):
def set_properties(args):
def unset_properties(args):
def make_download_url(args):
def get_record(entity_result, args):
def get_output_path(obj_name, obj_class, args):
def get_applet(project, entity_result, args):
def get_app(entity_result, args):
def get_workflow(entity_result, args):
def do_debug(msg):
def get_database(entity_result, args):
def get(args):
    # Decide what to do based on entity's class
def cat(args):
def download_or_cat(args):
def head(args):
    # Attempt to resolve name
def upload(args, **kwargs):
def upload_one(args):
def find_executions(args):
def find_data(args):
    # --folder deprecated to --path.
def find_projects(args):
def find_apps_result(args):
def find_global_workflows_result(args):
def print_find_results(results, args):
def find_apps(args):
def find_global_workflows(args):
def update_project(args):
def close(args):
def wait(args):
def build(args):
def process_list_of_usernames(thing):
def add_users(args):
def remove_users(args):
def list_users(args):
def add_developers(args):
def list_developers(args):
def render_timestamp(epochSeconds):
    # This is the format used by 'aws s3 ls'
def list_database_files(args):
def remove_developers(args):
def install(args):
def uninstall(args):
def _get_input_for_run(args, executable, preset_inputs=None, input_name_prefix=None):
def run_one(args, executable, dest_proj, dest_path, input_json, run_kwargs):
    # Print inputs used for the run
def run_batch_all_steps(args, executable, dest_proj, dest_path, input_json, run_kwargs):
def run_body(args, executable, dest_proj, dest_path, preset_inputs=None, input_name_prefix=None):
def print_run_help(executable="", alias=None):
def print_run_input_help():
def run(args):
def terminate(args):
def watch(args):
def get_client_ip():
def ssh_config(args):
def update_pub_key(user_id, pub_key_file):
def verify_ssh_config():
def ssh(args, ssh_config_verified=False):
def generate_batch_inputs(args):

    # Internally restricted maximum batch size for a TSV
def publish(args):
def archive(args):
def print_help(args):
def exit_shell(args):
def register_parser(parser, subparsers_action=None, categories=('other', ), add_help=True):
def positive_integer(value):
def positive_number(value):
def main():
    # Bash argument completer hook
```

## Signatures of what its module imports from the repository
```python
# from ..cli import try_call
def try_call(func, *args, **kwargs):
    ...

# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from ..utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from ..utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...

# from dxpy.exceptions import PermissionDenied
class PermissionDenied(DXAPIError):

# from dxpy.exceptions import InvalidState
class InvalidState(DXAPIError):

# from dxpy.exceptions import ResourceNotFound
class ResourceNotFound(DXAPIError):

# from dxpy.exceptions import DXCLIError
class DXCLIError(DXError):

# from ..cli import prompt_for_yn
def prompt_for_yn(prompt_str, default=None):
    ...

# from ..cli.cp import cp
def cp(args):
    ...

# from ..cli.dataset_utilities import extract_dataset
def extract_dataset(args):
    """Retrieves the data or generates SQL to retrieve the data from a dataset or cohort for a set of entity.fields. Additionally, the dataset's dictionary c"""
    ...

# from ..cli.dataset_utilities import extract_assay_germline
def extract_assay_germline(args):
    """Retrieve the selected data or generate SQL to retrieve the data from an genetic variant assay in a dataset or cohort based on provided rules."""
    ...

# from ..cli.dataset_utilities import extract_assay_somatic
def extract_assay_somatic(args):
    """Retrieve the selected data or generate SQL to retrieve the data from an somatic variant assay in a dataset or cohort based on provided rules."""
    ...

# from ..cli.dataset_utilities import create_cohort
def create_cohort(args):
    """Create a cohort from dataset/cohort and specified list of samples."""
    ...

# from ..cli.dataset_utilities import extract_assay_expression
def extract_assay_expression(args):
    """`dx extract_assay expression`"""
    ...

# from ..cli.download import download_one_file
def download_one_file(project, file_desc, dest_filename, args):
    ...

# from ..cli.download import download_one_database_file
def download_one_database_file(project, database_desc, dest_filename, src_filename, file_status, args):
    ...

# from ..cli.download import download
def download(args):
    ...

# from ..cli.parsers import process_properties_args
def process_properties_args(args):
    # Properties
    ...

# from ..cli.parsers import process_find_by_property_args
def process_find_by_property_args(args):
    ...

# from ..cli.parsers import process_dataobject_args
def process_dataobject_args(args):
    ...

# from ..cli.parsers import process_single_dataobject_output_args
def process_single_dataobject_output_args(args):
    ...

# from ..cli.parsers import add_find_executions_search_gp
def add_find_executions_search_gp(parser):
    ...

# from ..cli.parsers import set_env_from_args
def set_env_from_args(args):
    """Sets the environment variables for this process from arguments (argparse.Namespace)"""
    ...

# from ..cli.parsers import process_extra_args
def process_extra_args(args):
    ...

# from ..cli.parsers import DXParserError
class DXParserError(DXError):
    def __init__(self, msg):
        ...

# from ..cli.parsers import process_instance_type_arg
def process_instance_type_arg(args, for_workflow=False):
    ...

# from ..cli.parsers import process_instance_type_by_executable_arg
def process_instance_type_by_executable_arg(args):
    ...

# from ..cli.parsers import process_instance_count_arg
def process_instance_count_arg(args):
    ...

# from ..cli.parsers import get_update_project_args
def get_update_project_args(args):
    ...

# from ..cli.parsers import process_phi_param
def process_phi_param(args):
    ...

# from ..cli.parsers import process_external_upload_restricted_param
def process_external_upload_restricted_param(args):
    ...

# from ..cli.exec_io import ExecutableInputs
class ExecutableInputs(object):
    def __init__(self, executable=None, input_name_prefix=None, input_spec=None, active_region=None):
        """:param executable: Executable object handler"""
        ...
    def get_executable_description(self):
        ...
    def update(self, new_inputs, strip_prefix=True):
        """Updates the inputs dictionary with the key/value pairs from new_inputs, overwriting existing keys."""
        ...
    def add(self, input_name, input_value):
        ...
    def init_completer(self):
        ...
    def uninit_completer(self):
        ...
    def prompt_for_missing(self, confirm=True):
        # No-op if there is no input spec
        ...
    def prompt_for_input(self, input_name):
        ...
    def prompt_for_optional_inputs(self):
        ...
    def update_from_args(self, args, require_all_inputs=True):
        ...

# from ..cli.exec_io import format_choices_or_suggestions
def format_choices_or_suggestions(header, items, obj_class, initial_indent=' ' * 8, subsequent_indent=' ' * 10):
    ...

# from ..cli.org import get_org_invite_args
def get_org_invite_args(user_id, args):
    """Used by:"""
    ...

# from ..cli.org import add_membership
def add_membership(args):
    ...

# from ..cli.org import remove_membership
def remove_membership(args):
    ...

# from ..cli.org import update_membership
def update_membership(args):
    ...

# from ..cli.org import new_org
def new_org(args):
    ...

# from ..cli.org import update_org
def update_org(args):
    ...

# from ..cli.org import find_orgs
def find_orgs(args):
    ...

# from ..cli.org import org_find_members
def org_find_members(args):
    ...

# from ..cli.org import org_find_projects
def org_find_projects(args):
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/scripts/dx.py:727
        if get_last_pos_of_char(':', args.project) != -1:
            args.path = args.project
        else:
            args.path = args.project + ':'
        cd(args)
        print("Selected project", split_unescaped(":", args.project)[0].replace("\\:", ":"))
    else:
        pick_and_set_project(args)
```

Write `checks()` and `cases()` for `cd`. Remember: setup in the thunk or at module level, never timed.