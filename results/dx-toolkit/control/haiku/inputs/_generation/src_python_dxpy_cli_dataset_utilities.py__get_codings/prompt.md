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
Function under test: `get_codings` in `src/python/dxpy/cli/dataset_utilities.py`
Import it as `from dxpy.cli.dataset_utilities import get_codings`.

## The function
```python
def get_codings(resp: dict, project_context: str, limit: Optional[int] = None) -> dict:
    """
    Returns all of the dataset's codings as a dict of coding name to coding, following the
    server's pagination cursor and reassembling any coding split across pages.

    Each coding has the same shape as a descriptor's `model["codings"]` entry. On the wire, a
    hierarchical coding the server had to split sends `codes_to_parent` in place of `display`,
    since a tree built from a single page could be wrong; once every fragment is in hand the
    edges are complete, so this rebuilds `display` from them before returning -- callers never
    see `codes_to_parent`.
    """
    codings = collections.OrderedDict()
    payload = {"project_context": project_context}
    if limit is not None:
        payload["limit"] = limit

    for _ in range(MAX_CODINGS_PAGES):
        page = viz_meta_codings_page(resp, payload)
        for name, coding in page["results"].items():
            if name not in codings:
                # Deep-copied so a stored coding never aliases the response, and so every
                # key -- not just the ones this function knows to merge -- is safe to keep.
                codings[name] = copy.deepcopy(coding)
                continue

            # Seen already, so the server split this coding across pages. `existing` aliases
            # the accumulated coding and is merged into in place.
            existing = codings[name]
            existing[CODING_PAGINATED_KEY] = True
            existing["codes_to_meanings"].update(coding.get("codes_to_meanings") or {})
            existing["codes_to_concepts"].update(coding.get("codes_to_concepts") or {})
            if "codes_to_parent" in coding:
                # A tree built from a single page is wrong, since a code's children can fall
                # on the next page; parent edges hold however the pages divide.
                existing.setdefault("codes_to_parent", {}).update(
                    coding["codes_to_parent"] or {}
                )
                existing.pop("display", None)
            elif "display" in coding and "display" in existing:
                existing["display"].extend(coding["display"] or [])

        if not page.get("next"):
            return _finalize_split_codings(codings)
        # Echoed back verbatim as `starting`: when a coding has more codes than `limit`,
        # `next` carries that coding's real `after_code` so the next page resumes mid-coding
        # at the right code, rather than always just advancing to the next coding name.
        payload["starting"] = page["next"]

    raise DXError(
        "Codings pagination did not complete after {} pages".format(MAX_CODINGS_PAGES)
    )
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

## Definitions it uses from the same module
```python
CODING_PAGINATED_KEY = "_dx_paginated"

MAX_CODINGS_PAGES = 10000

def viz_meta_codings_page(resp: dict, payload: dict) -> dict:
    """
    Returns a single page of the dataset's codings. Raises rather than exiting, so the
    caller can fall back to the descriptor.
    """
    resource_val = resp["url"] + "/viz-meta/3.0/" + resp["dataset"] + "/codings"
    page = dxpy.DXHTTPRequest(resource=resource_val, data=payload, prepend_srv=False)
    if "error" in page:
        raise DXError(str(page["error"]))
    return page

def _finalize_split_codings(codings: dict) -> dict:
    """
    Turns any coding still carrying `codes_to_parent` back into the canonical shape, now
    that every fragment of it has been merged: its edges are a complete parent map, so the
    tree hare couldn't safely build from a single page can be built here (see
    _hierarchy_from_parents), and the coding is no longer distinguishable from a whole one.
    """
    for coding in codings.values():
        if "codes_to_parent" not in coding:
            continue
        all_codes = list(coding["codes_to_meanings"])
        coding["display"] = _hierarchy_from_parents(
            coding.pop("codes_to_parent"), all_codes
        )
        coding.pop(CODING_PAGINATED_KEY, None)
    return codings
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
def _hierarchy_from_parents(codes_to_parent: dict, all_codes: list) -> list:
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
def extract_assay_expression(args):
def resolve_validate_dx_path(path):
def validate_cohort_ids(descriptor, project, resp, ids):
    # Usually the name of the table
def has_access_level(project, access_level):
def validate_project_access(project, access_level="UPLOAD"):
def create_cohort(args):
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import DXError
class DXError(Exception):

# from ..utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from ..bindings.dxdataobject_functions import is_dxlink
def is_dxlink(x):
    """:param x: A potential DNAnexus link"""
    ...

# from ..bindings.dxdataobject_functions import describe
def describe(id_or_link, **kwargs):
    """:param id_or_link: String containing an object ID or dict containing a DXLink,"""
    ...

# from ..bindings.dxfile import DXFile
class DXFile(DXDataObject):
    _class = "file"
    _describe = staticmethod(dxpy.api.file_describe)
    _add_types = staticmethod(dxpy.api.file_add_types)
    _remove_types = staticmethod(dxpy.api.file_remove_types)
    _get_details = staticmethod(dxpy.api.file_get_details)
    _set_details = staticmethod(dxpy.api.file_set_details)
    _set_visibility = staticmethod(dxpy.api.file_set_visibility)
    _rename = staticmethod(dxpy.api.file_rename)
    _set_properties = staticmethod(dxpy.api.file_set_properties)
    _add_tags = staticmethod(dxpy.api.file_add_tags)
    _remove_tags = staticmethod(dxpy.api.file_remove_tags)
    _close = staticmethod(dxpy.api.file_close)
    _list_projects = staticmethod(dxpy.api.file_list_projects)
    _http_threadpool_size = DXFILE_HTTP_THREADS
    _http_threadpool = dxpy.utils.get_futures_threadpool(max_workers=_http_threadpool_size)
    NO_PROJECT_HINT = 'NO_PROJECT_HINT'
    @classmethod
    def set_http_threadpool_size(cls, num_threads):
        """.. deprecated:: 0.191.0"""
        ...
    def __init__(self, dxid=None, project=None, mode=None, read_buffer_size=DEFAULT_BUFFER_SIZE,
                 write_buffer_size=DEFAULT_BUFFER_SIZE, expected_file_size=None, file_is_mmapd=False):
        """:param dxid: Object ID"""
        ...
    next = next
    __next__ = next
    def set_ids(self, dxid, project=None):
        """:param dxid: Object ID"""
        ...
    def seek(self, offset, from_what=os.SEEK_SET):
        """:param offset: Position in the file to seek to"""
        ...
    def tell(self):
        """Returns the current position of the file read cursor."""
        ...
    def flush(self, multithread=True, **kwargs):
        """Flushes the internal write buffer."""
        ...
    def write(self, data, multithread=True, **kwargs):
    # ... (truncated)

# from ..utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...

# from ..utils.resolver import is_hashid
def is_hashid(string):
    ...

# from ..utils.resolver import ResolutionError
class ResolutionError(DXError):
    def __init__(self, msg):
        ...

# from ..utils.resolver import resolve_path
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
    """:param path: A path to a data object to attempt to resolve"""
    ...

# from ..utils.resolver import check_folder_exists
def check_folder_exists(project, path, folder_name):
    """:param project: project id"""
    ...

# from ..utils.file_handle import as_handle
@contextlib.contextmanager
def as_handle(path_or_handle, mode=None, is_gzip=False, **kwargs):
    """Open a file path, or pass through an already open file handle."""
    ...

# from ..utils.describe import print_desc
def print_desc(desc, verbose=False):
    """:param desc: The describe hash of a DNAnexus entity"""
    ...

# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from ..exceptions import PermissionDenied
class PermissionDenied(DXAPIError):

# from ..exceptions import InvalidInput
class InvalidInput(DXAPIError):

# from ..exceptions import InvalidState
class InvalidState(DXAPIError):

# from ..dx_extract_utils.filter_to_payload import validate_JSON
def validate_JSON(filter, type):
    """Check user-provdied JSON filter for validity"""
    ...

# from ..dx_extract_utils.filter_to_payload import final_payload
def final_payload(
    full_input_dict,
    name,
    id,
    project_context,
    genome_reference,
    filter_type,
    order=True,
    exclude_nocall=None,
    exclude_refdata=None,
    exclude_halfref=None
):
    """Assemble the top level payload.  Top level dict contains the project context, fields (return columns),"""
    ...

# from ..dx_extract_utils.germline_utils import get_genotype_only_types
def get_genotype_only_types(filter_dict, exclude_refdata, exclude_halfref, exclude_nocall):
    """Returns a list of genotype types for the filter that are use in genotype table only queries."""
    ...

# from ..dx_extract_utils.germline_utils import add_germline_base_sql
def add_germline_base_sql(resp, payload):
    ...

# from ..dx_extract_utils.germline_utils import sort_germline_variant
def sort_germline_variant(d):
    ...

# from ..dx_extract_utils.germline_utils import harmonize_germline_sql
def harmonize_germline_sql(sql):
    """Harmonize the SQL statement for genotype table only queries to include columns to UNION with genotype and allele"""
    ...

# from ..dx_extract_utils.germline_utils import harmonize_germline_results
def harmonize_germline_results(results, fields_list):
    """Harmonizes raw query results to include all columns in fields_list. Columns not in fields_list have value None."""
    ...

# from ..dx_extract_utils.germline_utils import get_germline_ref_payload
def get_germline_ref_payload(results, genotype_payload):
    """Create a payload to query locus_id/ref pairs from the allele table for genotypes missing ref column values."""
    ...

# from ..dx_extract_utils.germline_utils import get_germline_loci_payload
def get_germline_loci_payload(locations, genotype_payload):
    """Create a payload to query locus ids from the allele table with a location filter"""
    ...

# from ..dx_extract_utils.germline_utils import update_genotype_only_ref
def update_genotype_only_ref(results, locus_id_refs):
    """Update genotype results with ref column values from locus_id/ref query result"""
    ...

# from ..dx_extract_utils.germline_utils import get_genotype_types
def get_genotype_types(filter_dict):
    """Returns a list of genotype types for the filter that are use in genotype and allele table queries."""
    ...

# from ..dx_extract_utils.germline_utils import infer_genotype_type
def infer_genotype_type(
    samples: list, loci: list[dict], result_entries: list[dict], type_to_infer: str
) -> list[dict]:
    """If the result_entries does not contain entry with sample_id of specifific starting_position the the genotype type is either no-call or ref."""
    ...

# from ..dx_extract_utils.germline_utils import get_types_to_filter_out_when_infering
def get_types_to_filter_out_when_infering(
    requested_types: list[str],
) -> list:
    """Infer option require all genotypes types to be queried."""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_extract_dataset_codings.py:125

        with patch.object(
            dataset_utilities.dxpy, "DXHTTPRequest", side_effect=send
        ):
            codings = get_codings(VISUALIZE_RESP, "project-xxxx", **kwargs)
        return codings, calls

    def test_single_page(self):

# src/python/test/test_extract_dataset_codings.py:463
            },
        ]
        with patch.object(dataset_utilities.dxpy, "DXHTTPRequest") as request:
            request.side_effect = pages
            codings = get_codings(VISUALIZE_RESP, "project-xxxx")

        dictionary = self.build(descriptor, codings)


# src/python/dxpy/cli/dataset_utilities.py:548
        # Codings live in the database's dx_codings table; a descriptor written before that
        # change still carries them, and the server merges both sources.
        codings = None
        try:
            codings = get_codings(resp, project_context=project)
        except Exception:
            pass
        rec_dict = rec_descriptor.get_dictionary(codings=codings)
```

Write `checks()` and `cases()` for `get_codings`. Remember: setup in the thunk or at module level, never timed.