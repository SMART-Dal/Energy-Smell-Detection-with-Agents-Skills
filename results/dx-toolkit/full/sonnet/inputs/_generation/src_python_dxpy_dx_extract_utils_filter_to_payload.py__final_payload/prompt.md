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
Function under test: `final_payload` in `src/python/dxpy/dx_extract_utils/filter_to_payload.py`
Import it as `from dxpy.dx_extract_utils.filter_to_payload import final_payload`.

## The function
```python
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
    """
    Assemble the top level payload.  Top level dict contains the project context, fields (return columns),
    and raw filters objects.  This payload is sent in its entirety to the vizserver via an
    HTTPS POST request
    """
    # Generate the assay filter component of the payload
    assay_filter = generate_assay_filter(
        full_input_dict,
        name,
        id,
        project_context,
        genome_reference,
        filter_type,
        exclude_nocall,
        exclude_refdata,
        exclude_halfref
    )

    final_payload = {}
    # Set the project context
    final_payload["project_context"] = project_context

    # Section for defining returned columns for each of the three filter types
    if filter_type == "allele":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_allele.json"), "r"
        ) as infile:
            fields = json.load(infile)
    elif filter_type == "annotation":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_annotation.json"), "r"
        ) as infile:
            fields = json.load(infile)
    elif filter_type == "genotype":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_genotype.json"), "r"
        ) as infile:
            fields = json.load(infile)
    elif filter_type == "genotype_only":
        with open(
            os.path.join(extract_utils_basepath, "return_columns_genotype_only.json"), "r"
        ) as infile:
            fields = json.load(infile)

    if order:
        order_by = [{"allele_id":"asc"}]

        if any("locus_id" in field for field in fields):
            order_by.insert(0, {"locus_id":"asc"})

        # In order for output to be deterministic, we need to do a secondary sort by sample_id
        # if it is present in the fields
        sample_id_present = False
        for field in fields:
            if "sample_id" in field:
                sample_id_present = True
        if sample_id_present:
            order_by.append({"sample_id":"asc"})

        final_payload["order_by"] = order_by

    final_payload["fields"] = fields
    final_payload["adjust_geno_bins"] = False
    final_payload["raw_filters"] = assay_filter
    final_payload["is_cohort"] = True
    final_payload["distinct"] = True

    field_names = []
    for f in fields:
        field_names.append(list(f.keys())[0])

    return final_payload, field_names
```

## Imports of its module
```python
import json
from ..exceptions import err_exit
from .input_validation import validate_filter
import os
import dxpy
from .retrieve_bins import retrieve_bins
```

## Definitions it uses from the same module
```python
extract_utils_basepath = os.path.join(
    os.path.dirname(dxpy.__file__), "dx_extract_utils"
)

def generate_assay_filter(
    full_input_dict,
    name,
    id,
    project_context,
    genome_reference,
    filter_type,
    exclude_nocall=None,
    exclude_refdata=None,
    exclude_halfref=None
):
    """
    Generate the entire assay filters object by reading the filter JSON, making the relevant
    Basic and Location filters, and creating the structure that relates them logically

    There are three possible types of input JSON: a genotype filter, an allele filter,
    and an annotation filter
    """

    filters_dict = {}
    table = filter_type if filter_type != "genotype_only" else "genotype"

    for key in full_input_dict.keys():
        if key == "location":
            location_list = full_input_dict["location"]
            location_aid_filter = location_filter(location_list, table)
            filters_dict.update(location_aid_filter)

        else:
            if not (full_input_dict[key] == "*" or full_input_dict[key] == None):
                filters_dict.update(
                    basic_filter(
                        filter_type,
                        key,
                        full_input_dict[key],
                        project_context,
                        genome_reference,
                    )
                )
    final_filter_dict = {"assay_filters": {"name": name, "id": id}}

    # Additional structure of the payload
    final_filter_dict["assay_filters"].update({"filters": filters_dict})
    # The general filters are related by "and"
    final_filter_dict["assay_filters"]["logic"] = "and"

    if exclude_nocall is not None:
        # no-call genotypes
        final_filter_dict["assay_filters"]["nocall_yn"] = not exclude_nocall
    if exclude_refdata is not None:
        # reference genotypes
        final_filter_dict["assay_filters"]["ref_yn"] = not exclude_refdata
    if exclude_halfref is not None:
        # half-reference genotypes
        final_filter_dict["assay_filters"]["halfref_yn"] = not exclude_halfref

    return final_filter_dict
```

## Everything else its module defines (headers only)
```python
def retrieve_geno_bins(list_of_genes, project, genome_reference):
def basic_filter(
    filter_type, friendly_name, values=[], project_context=None, genome_reference=None
):
def location_filter(location_list, table):
def validate_JSON(filter, type):
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from .input_validation import validate_filter
def validate_filter(filter, filter_type):
    ...

# from .retrieve_bins import retrieve_bins
def retrieve_bins(list_of_genes, project, genome_reference, extract_utils_basepath,
                  stage_file,platform_file,error_message):
    """A function for determining appropriate geno bins to attach to a given filter"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_extract_assay.py:314
            "gnomad_alt_freq",
            "worst_effect",
        ]

        test_payload, test_fields = final_payload(
            full_input_dict,
            name,
            id,
            self.proj_id,
            genome_reference,
            filter_type,
        )

        self.assertEqual(
            test_payload,

# src/python/dxpy/cli/dataset_utilities.py:950
    elif args.retrieve_annotation:
        filter_type = "annotation"

    if filter_type and filter_given:
        payload, fields_list = final_payload(
            full_input_dict=filter_dict,
            name=selected_assay_name,
            id=selected_assay_id,
            project_context=project,
            genome_reference=selected_ref_genome,
            filter_type=filter_type,
        )

        add_germline_base_sql(resp, payload)


# src/python/dxpy/cli/dataset_utilities.py:1007
            genotype_only_types = get_genotype_only_types(filter_dict,
                                                          exclude_refdata, exclude_halfref, exclude_nocall)
            
        # get the payload for the genotype/allele table query for alternate genotype types
        genotype_payload, fields_list = final_payload(
            full_input_dict=filter_dict,
            name=selected_assay_name,
            id=selected_assay_id,
            project_context=project,
            genome_reference=selected_ref_genome,
            filter_type="genotype",
            order=not genotype_only_types,
        )

        add_germline_base_sql(resp, genotype_payload)

```

Write `checks()` and `cases()` for `final_payload`. Remember: setup in the thunk or at module level, never timed.