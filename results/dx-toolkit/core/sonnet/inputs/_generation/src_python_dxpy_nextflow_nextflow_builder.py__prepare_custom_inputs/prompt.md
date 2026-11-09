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
Function under test: `prepare_custom_inputs` in `src/python/dxpy/nextflow/nextflow_builder.py`
Import it as `from dxpy.nextflow.nextflow_builder import prepare_custom_inputs`.

## The function
```python
def prepare_custom_inputs(schema_file="./nextflow_schema.json"):
    """
    :param schema_file: path to nextflow_schema.json file
    :type schema_file: str or Path
    :returns: list of custom inputs defined with DNAnexus datatype 
    :rtype: list
    Creates custom input list from nextflow_schema.json that
    will be added in dxapp.json inputSpec field
    """

    def get_dx_type(nf_type, nf_format=None):
        types = {
            "string": "string",
            "integer": "int",
            "number": "float",
            "boolean": "boolean",
            "object": "hash"
        }
        str_types = {
            "file-path": "file",
            "directory-path": "string",  # So far we will stick with strings dx://...
            "path": "string"
        }
        # Handle JSON Schema union types e.g. ["string", "null"], ["boolean", "string"]
        if isinstance(nf_type, list):
            non_null = [t for t in nf_type if t != "null"]
            nf_type = non_null[0] if non_null else "string"
        if nf_type == "string" and nf_format in str_types:
            return str_types[nf_format]
        elif nf_type in types:
            return types[nf_type]
        raise Exception("type {} is not supported by DNAnexus".format(nf_type))

    inputs = []
    if not os.path.exists(schema_file):
        return inputs

    with open(schema_file, "r") as fh:
        schema = json.load(fh)
    defs_key = "definitions" if "definitions" in schema else "$defs" if "$defs" in schema else None
    if defs_key is None:
        return inputs
    for d_key, d_schema in schema.get(defs_key, {}).items():
        required_inputs = d_schema.get("required", [])
        for property_key, property in d_schema.get("properties", {}).items():
            dx_input = {}
            dx_input["name"] = property_key
            dx_input["title"] = dx_input['name']
            dx_input["class"] = get_dx_type(property.get("type"), property.get("format"))

            help_parts = [f"(Nextflow pipeline {'required' if property_key in required_inputs else 'optional'})"]
            if "default" in property:
                help_parts.append(f"Default value: {property.get('default', '')}.")
            help_parts.append(property.get('description', None))
            help_parts.append(property.get('help_text', None))
            dx_input["help"] = " ".join(filter(lambda x: x, help_parts)).strip()

            dx_input["hidden"] = property.get('hidden', False)
            dx_input["optional"] = True
            if property_key in required_inputs:
                inputs.insert(0, dx_input)
            else:
                inputs.append(dx_input)

    return inputs
```

## Imports of its module
```python
import os
import sys
import dxpy
import json
import argparse
import logging
from glob import glob
import shutil
import tempfile
from functools import partial
from dxpy.nextflow.nextflow_templates import (get_nextflow_dxapp, get_nextflow_src)
from dxpy.nextflow.nextflow_utils import (get_template_dir, write_exec, write_dxapp, get_importer_name,
                                          create_readme, get_nested, get_allowed_extra_fields_mapping,
                                          resolve_version)
from dxpy.cli.exec_io import parse_obj
from dxpy.cli import try_call
from dxpy.utils.resolver import resolve_existing_path
```

## Everything else its module defines (headers only)
```python
def _npi_supports_version_selection():
def build_pipeline_with_npi(
        repository=None,
        tag=None,
        cache_docker=False,
        docker_secrets=None,
        nextflow_pipeline_params="",
    # ... (truncated)
def prepare_nextflow(
        resources_dir,
        profile,
        region,
        cache_docker=False,
        nextflow_pipeline_params="",
    # ... (truncated)
```

## Signatures of what its module imports from the repository
```python
# from dxpy.nextflow.nextflow_templates import get_nextflow_dxapp
def get_nextflow_dxapp(
        custom_inputs=None,
        resources_dir="",
        region="aws:us-east-1",
        profile="",
        cache_docker=False,
        nextflow_pipeline_params="",
        nextflow_version=None
):
    """:param custom_inputs: Custom inputs that will be used in the created Nextflow pipeline."""
    ...

# from dxpy.nextflow.nextflow_templates import get_nextflow_src
def get_nextflow_src(custom_inputs=None, profile=None, resources_dir=None):
    """:param custom_inputs: Custom inputs (as configured in nextflow_schema.json) that will be used in created runtime configuration and runtime params argu"""
    ...

# from dxpy.nextflow.nextflow_utils import get_template_dir
def get_template_dir():
    ...

# from dxpy.nextflow.nextflow_utils import write_exec
def write_exec(folder, content):
    ...

# from dxpy.nextflow.nextflow_utils import write_dxapp
def write_dxapp(folder, content):
    ...

# from dxpy.nextflow.nextflow_utils import get_importer_name
def get_importer_name():
    ...

# from dxpy.nextflow.nextflow_utils import create_readme
def create_readme(source_dir, destination_dir):
    """:param destination_dir: Directory where readme is going to be created"""
    ...

# from dxpy.nextflow.nextflow_utils import get_nested
def get_nested(args, arg_path):
    """:param args: extra args from command input"""
    ...

# from dxpy.nextflow.nextflow_utils import get_allowed_extra_fields_mapping
def get_allowed_extra_fields_mapping():
    """:returns: tuple (arg_path, target_key)"""
    ...

# from dxpy.nextflow.nextflow_utils import resolve_version
def resolve_version(requested_version=None, warn=True):
    """Resolve Nextflow version. Returns (version_key, version_config)."""
    ...

# from dxpy.cli.exec_io import parse_obj
def parse_obj(string, klass):
    ...

# from dxpy.cli import try_call
def try_call(func, *args, **kwargs):
    ...

# from dxpy.utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_nextflow.py:550
        self.assertTrue("dx-download-all-inputs --parallel --except {} --except {} --except {}".format(
            input1.get("name"), input3.get("name"), input4.get("name")) in src)

    def test_prepare_inputs(self):
        inputs = prepare_custom_inputs(schema_file=THIS_DIR / "nextflow/schema2.json")
        names = [i["name"] for i in inputs]
        self.assertTrue(
            "input" in names and "outdir" in names and "save_merged_fastq" in names)

# src/python/test/test_nextflow.py:557
            "input" in names and "outdir" in names and "save_merged_fastq" in names)
        self.assertEqual(len(names), 3)

    def test_prepare_inputs_single(self):
        inputs = prepare_custom_inputs(schema_file=THIS_DIR / "nextflow/schema3.json")
        self.assertEqual(len(inputs), 1)
        i = inputs[0]
        self.assertEqual(i["name"], "outdir")

# src/python/dxpy/nextflow/nextflow_builder.py:164
        raise dxpy.app_builder.AppBuilderException(
            "Directory %s does not contain Nextflow file (*.nf): not a valid Nextflow directory" % resources_dir)
    dxapp_dir = tempfile.mkdtemp(prefix=".dx.nextflow")

    custom_inputs = prepare_custom_inputs(schema_file=os.path.join(resources_dir, "nextflow_schema.json"))
    dxapp_content = get_nextflow_dxapp(
        custom_inputs=custom_inputs,
        resources_dir=resources_dir,
```

Write `checks()` and `cases()` for `prepare_custom_inputs`. Remember: setup in the thunk or at module level, never timed.