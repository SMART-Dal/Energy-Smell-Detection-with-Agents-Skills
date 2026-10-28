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
Function under test: `extract_assay_expression` in `src/python/dxpy/cli/dataset_utilities.py`
Import it as `from dxpy.cli.dataset_utilities import extract_assay_expression`.

## The function
```python
def extract_assay_expression(args):
    """
    `dx extract_assay expression`

    Retrieve the selected data or generate SQL to retrieve the data from an expression assay in a dataset or cohort based on provided rules.
    """

    # Validating input arguments (argparse) combinations
    parser_dict = vars(args)
    input_validator = ArgsValidator(
        parser_dict=parser_dict,
        schema=EXTRACT_ASSAY_EXPRESSION_INPUT_ARGS_SCHEMA,
        error_handler=err_exit,
    )
    input_validator.validate_input_combination()

    if args.json_help:
        print(EXTRACT_ASSAY_EXPRESSION_JSON_HELP)
        sys.exit(0)

    if args.additional_fields_help:
        print(EXTRACT_ASSAY_EXPRESSION_ADDITIONAL_FIELDS_HELP)
        sys.exit(0)

    # Resolving `path` argument
    if args.path:
        # entity_result contains `id` and `describe`
        project, folder_path, entity_result = resolve_existing_path(args.path)
        if entity_result is None:
            err_exit(
                'Unable to resolve "{}" to a data object in {}.'.format(
                    args.path, project
                )
            )
        else:
            entity_describe = entity_result.get("describe")

        # Is object in current project?
        if project != entity_result["describe"]["project"]:
            err_exit(
                'Unable to resolve "{}" to a data object or folder name in {}. Please make sure the object is in the selected project.'.format(
                    args.path, project
                )
            )

        # Is object a cohort or a dataset?
        EXPECTED_TYPES = ["Dataset", "CohortBrowser"]
        _record_types = entity_result["describe"]["types"]
        if entity_result["describe"]["class"] != "record" or all(
            x not in _record_types for x in EXPECTED_TYPES
        ):
            err_exit(
                "{} Invalid path. The path must point to a record type of cohort or dataset and not a {} object.".format(
                    entity_result["id"], _record_types
                )
            )

        # Cohort/Dataset handling
        record = DXRecord(entity_describe["id"])
        dataset, cohort_info = Dataset.resolve_cohort_to_dataset(record)

        if cohort_info:
            if args.assay_name or args.list_assays:
                err_exit(
                    'Currently "--assay-name" and "--list-assays" may not be used with a CohortBrowser record (Cohort Object) as input. To select a specific assay or to list assays, please use a Dataset object as input.'
                )
            if float(cohort_info["details"]["version"]) < 3.0:
                err_exit(
                    "{}: Version of the cohort is too old. Version must be at least 3.0.".format(
                        cohort_info["id"]
                    )
                )
            
            BASE_SQL = cohort_info.get("details").get("baseSql")
            COHORT_FILTERS = cohort_info.get("details").get("filters")
            IS_COHORT = True
        else:
            BASE_SQL = None
            COHORT_FILTERS = None
            IS_COHORT = False
            if float(dataset.version) < 3.0:
                err_exit(
                    "{}: Version of the dataset is too old. Version must be at least 3.0.".format(
                        dataset.id
                    )
                )

    if args.list_assays:
        print(*dataset.assay_names_list("molecular_expression"), sep="\n")
        sys.exit(0)

    # Check whether assay_name is valid
    # If no assay_name is provided, the first molecular_expression assay in the dataset must be selected
    if args.assay_name:
        if not dataset.is_assay_name_valid(args.assay_name, "molecular_expression"):
            err_exit(
                "Assay {} does not exist in {}, or the assay name provided cannot be recognized as a molecular expression assay. For valid assays accepted by the function, `extract_assay expression`, please use the --list-assays flag.".format(
                    args.assay_name, dataset.id
                )
            )
    elif not args.assay_name:
        if dataset.assays_info_dict.get("molecular_expression") is None or len(dataset.assays_info_dict.get("molecular_expression")) == 0:
            err_exit("No molecular expression assays found in the dataset")

    # Load args.filter_json or args.filter_json_file into a dict
    if sys.version_info.major == 2:
        # In Python 2 JSONDecodeError does not exist
        json.JSONDecodeError = ValueError

    if args.filter_json:
        try:
            user_filters_json = json.loads(args.filter_json)
        except json.JSONDecodeError as e:
            json_reading_error = (
                "JSON provided for --retrieve-expression is malformatted."
                + "\n"
                + str(e)
            )
            err_exit(json_reading_error)
        except Exception as e:
            err_exit(str(e))

    elif args.filter_json_file:
        try:
            with open(args.filter_json_file) as f:
                user_filters_json = json.load(f)
        except json.JSONDecodeError as e:
            json_reading_error = (
                "JSON provided for --retrieve-expression is malformatted."
                + "\n"
                + str(e)
            )
            err_exit(json_reading_error)
        except OSError as e:
            if "No such file or directory" in str(e):
                err_exit(
                    "JSON file {} provided to --retrieve-expression does not exist".format(
                        e.filename
                    )
                )
            else:
                err_exit(str(e))
        except Exception as e:
            err_exit(str(e))

    # If --sql flag is provided, filter JSON is optional. If not present, all data must be returned
    if args.sql and not args.filter_json and not args.filter_json_file:
        return_all_data = True
        user_filters_json = {}
    else:
        return_all_data = False

    if not user_filters_json and not return_all_data:
        err_exit(
            "No filter JSON is passed with --retrieve-expression or input JSON for --retrieve-expression does not contain valid filter information."
        )

    if args.expression_matrix:
        if "expression" in user_filters_json:
            err_exit(
                'Expression filters are not compatible with --expression-matrix argument. Please remove "expression" from filters JSON.'
            )

        if args.additional_fields:
            err_exit(
                "--additional-fields cannot be used with --expression-matrix argument."
            )

    # Replace 'str' with 'unicode' when checking types in Python 2
    if sys.version_info.major == 2:
        EXTRACT_ASSAY_EXPRESSION_JSON_SCHEMA["location"]["items"]["properties"][
            "chromosome"
        ]["type"] = unicode
        EXTRACT_ASSAY_EXPRESSION_JSON_SCHEMA["location"]["items"]["properties"][
            "starting_position"
        ]["type"] = unicode
        EXTRACT_ASSAY_EXPRESSION_JSON_SCHEMA["location"]["items"]["properties"][
            "ending_position"
        ]["type"] = unicode

    # In case --sql flag is provided but no input json, function should return all data
    if user_filters_json:
        # Validate filters JSON provided by the user according to a predefined schema
        input_json_validator = JSONValidator(
            schema=EXTRACT_ASSAY_EXPRESSION_JSON_SCHEMA, error_handler=err_exit
        )
        input_json_validator.validate(input_json=user_filters_json)


    if args.assay_name:
        # Assumption: assay names are unique in a dataset descriptor
        # i.e. there are never two assays of the same type with the same name in the same dataset
        for molecular_assay in dataset.assays_info_dict["molecular_expression"]:
            if molecular_assay["name"] == args.assay_name:
                ASSAY_ID = molecular_assay["uuid"]
                break
    else:
        ASSAY_ID = dataset.assays_info_dict["molecular_expression"][0]["uuid"]

    # Getting generalized_assay_model_version to match filter schema
    # ... (truncated)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import, annotations
import sys
import collections
import copy
import json
import os
import re
import csv
import dxpy
import codecs
import subprocess
from functools import reduce
from typing import Optional
from ..utils.printing import fill
from ..bindings import DXRecord
from ..bindings.dxdataobject_functions import is_dxlink, describe
from ..bindings.dxfile import DXFile
from ..utils.resolver import resolve_existing_path, is_hashid, ResolutionError, resolve_path, check_folder_exists
from ..utils.file_handle import as_handle
from ..utils.describe import print_desc
from ..exceptions import (
    err_exit,
    DXError,
    PermissionDenied,
    InvalidInput,
    InvalidState,
    default_expected_exceptions,
)
from ..dx_extract_utils.filter_to_payload import validate_JSON, final_payload
from ..dx_extract_utils.germline_utils import (
    get_genotype_only_types,
    add_germline_base_sql,
    sort_germline_variant,
    harmonize_germline_sql,
    harmonize_germline_results,
    get_germline_ref_payload,
    get_germline_loci_payload,
    update_genotype_only_ref,
    get_genotype_types,
    infer_genotype_type,
    # ... (truncated)
```

## Everything else its module defines (headers only)
```python
class VizserverError(Exception):
class DXDataset(DXRecord):
    def __init__(self, dxid=None, project=None):
    # methods: get_descriptor, get_dictionary
class DXDatasetDescriptor:
    def __init__(self, dxfile, **kwargs):
    # methods: get_dictionary
class DXDatasetDictionary:
    def __init__(self, descriptor, codings=None):
    # methods: load_data_dictionary, create_entity_dframe, get_join_path_to_entity_field_map, create_edge, load_coding_dictionary, create_coding_name_dframe, load_entity_dictionary, write
def resolve_validate_record_path(path):
def viz_query_api_call(resp, payload, route):
def raw_query_api_call(resp, payload):
def raw_cohort_query_api_call(resp, payload):
def raw_api_call(resp, payload, sql_message=True):
def viz_meta_codings_page(resp: dict, payload: dict) -> dict:
def _hierarchy_from_parents(codes_to_parent: dict, all_codes: list) -> list:
def _finalize_split_codings(codings: dict) -> dict:
def get_codings(resp: dict, project_context: str, limit: Optional[int] = None) -> dict:
def extract_dataset(args):
def get_assay_info(rec_descriptor, assay_type):
def json_validation_function(filter_type, args):
def retrieve_meta_info(resp, project_id, assay_id, assay_name, print_to_stdout, out_file_name):
def assign_output_method(args, record_name, friendly_assay_type):
    #### Decide output method based on --output and --sql ####
def get_assay_name_info(
    list_assays, assay_name, path, friendly_assay_type, rec_descriptor
):
def comment_fill(string, comment_string='#  ', **kwargs):
def retrieve_samples(resp: dict, assay_name: str, assay_id: str) -> list:
def extract_assay_germline(args):
def retrieve_entities(model):
def list_fields(model, main_entity, args):
def csv_from_json(
    out_file_name="",
    print_to_stdout=False,
    sep=",",
    raw_results=[],
    column_names=[],
    # ... (truncated)
def extract_assay_somatic(args):
def resolve_validate_dx_path(path):
def validate_cohort_ids(descriptor, project, resp, ids):
    # Usually the name of the table
def has_access_level(project, access_level):
def validate_project_access(project, access_level="UPLOAD"):
def create_cohort(args):
```

## Signatures of what its module imports from the repository
```python
# from ..utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...

# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from ..bindings.apollo.dataset import Dataset
class Dataset(DXRecord):
    def __init__(self, dataset_id, detail_describe_dict=None):
        ...
    @staticmethod
    def resolve_cohort_to_dataset(record_obj):
        ...
    @property
    def descriptor_file(self):
        ...
    @property
    def descriptor_file_dict(self):
        ...
    @property
    def visualize_info(self):
        ...
    @property
    def vizserver_url(self):
        ...
    @property
    def project_id(self):
        ...
    @property
    def version(self):
        ...
    @property
    def detail_describe(self):
        ...
    @property
    def assays_info_dict(self):
        ...
    def assay_info_dict(self, assay_uuid):
        ...
    def assay_names_list(self, assay_type):
        ...
    def is_assay_name_valid(self, assay_name, assay_type):
        ...
    def assay_index(self, assay_name):
        ...

# from ..bindings.apollo.cmd_line_options_validator import ArgsValidator
class ArgsValidator:
    def __init__(
        self,
        parser_dict,
        schema,
        error_handler=print,
        warning_handler=print,
    ):
        ...
    def validate_schema_conditions(self):
        # Checking if all conditions exist
        ...
    def interpret_conditions(self):
        ...
    def throw_schema_message(self, check):
        ...
    def throw_exit_error(self, message):
        ...
    def throw_warning(self, message):
        ...
    def get_parser_values(self, params):
        ...
    def get_main_key(self, check):
        ...
    def get_items(self, check):
        ...
    def get_items_values(self, check):
        ...
    def get_exceptions(self, check):
        ...
    def remove_exceptions_from_list(self, check, list):
        ...
    def interpret_exclusive(self, check):
        ...
    def interpret_exclusive_with_exceptions(self, check, exception_present=True):
        ...
    def interpret_with_none_of(self, check):
        ...
    def interpret_required(self, check):
        ...
    # ... (truncated)

# from ..bindings.apollo.json_validation_by_schema import JSONValidator
class JSONValidator(object):
    def __init__(self, schema, error_handler=print):
        ...
    def validate(self, input_json):
        ...
    def validate_types(self, input_dict):
        ...
    def validate_properties(self, properties, input_dict):
        ...
    def validate_list_items(self, item_schema, input_list, key_name):
        ...
    def check_incompatible_subkeys(self, input_json, current_key):
        ...
    def check_incompatible_keys(self, input_json):
        ...
    def check_dependent_key_combinations(
        self, input_json, enforce_one_associated_key=False
    ):
        ...
    def error_on_invalid_keys(self, input_json):
        ...
    def are_list_items_within_range(
        self,
        input_json,
        key,
        start_subkey,
        end_subkey,
        window_width=250000000,
        check_each_separately=False,
    ):
        """This won't run by default when calling .validate() on a JSONValidator object. Run it separately when necessary"""
        ...
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `extract_assay_expression`. Remember: setup in the thunk or at module level, never timed.