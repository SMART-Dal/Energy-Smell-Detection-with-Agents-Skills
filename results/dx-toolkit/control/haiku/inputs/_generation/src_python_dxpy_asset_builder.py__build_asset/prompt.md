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
Function under test: `build_asset` in `src/python/dxpy/asset_builder.py`
Import it as `from dxpy.asset_builder import build_asset`.

## The function
```python
def build_asset(args):
    if args.src_dir is None:
        args.src_dir = os.getcwd()

    dest_project_name = None
    dest_folder_name = None
    dest_asset_name = None
    make_file = None
    asset_file = None
    conf_file = None

    try:
        asset_conf = parse_asset_spec(args.src_dir)
        validate_conf(asset_conf)
        asset_conf_file = os.path.join(args.src_dir, "dxasset.json")

        dxpy.api.system_whoami()
        dest_project_name, dest_folder_name, dest_asset_name = parse_destination(args.destination)
        if dest_project_name is None:
            raise AssetBuilderException("Can't build an asset without specifying a destination project; \
            please use the -d/--destination flag to explicitly specify a project")
        if dest_asset_name is None:
            dest_asset_name = asset_conf['name']

        # If dx build_asset is launched form a job, set json flag to True to avoid watching the job log
        if dxpy.JOB_ID:
            args.json = True

        if not args.json:
            print("Uploading input files for the AssetBuilder", file=sys.stderr)

        conf_file = dx_upload(asset_conf_file, dest_project_name, dest_folder_name, args.json)
        make_file = get_asset_make(args.src_dir, dest_project_name, dest_folder_name, args.json)
        asset_file = get_asset_tarball(asset_conf['name'], args.src_dir, dest_project_name,
                                       dest_folder_name, args.json)

        input_hash = {"conf_json": dxpy.dxlink(conf_file)}
        if asset_file:
            input_hash["custom_asset"] = dxpy.dxlink(asset_file)
        if make_file:
            input_hash["asset_makefile"] = dxpy.dxlink(make_file)

        builder_run_options = {
            "name": dest_asset_name,
            "input": input_hash
            }

        if args.priority is not None:
            builder_run_options["priority"] = args.priority

        # Add the default destination project to app run options, if it is not run from a job
        if not dxpy.JOB_ID:
            builder_run_options["project"] = dest_project_name
        if 'instanceType' in asset_conf:
            builder_run_options["systemRequirements"] = {"*": {"instanceType": asset_conf["instanceType"]}}
        if dest_folder_name:
            builder_run_options["folder"] = dest_folder_name

        release = asset_conf['release']
        if asset_conf['runSpecVersion'] == '1':
            release += '_v1'
        app_run_result = dxpy.api.app_run(ASSET_BUILDERS[release], input_params=builder_run_options)

        job_id = app_run_result["id"]

        if not args.json:
            print("\nStarted job '" + str(job_id) + "' to build the asset bundle.\n", file=sys.stderr)
            if args.watch:
                try:
                    subprocess.check_call(["dx", "watch", job_id])
                except subprocess.CalledProcessError as e:
                    if e.returncode == 3:
                        # Some kind of failure to build the asset. The reason
                        # for the failure is probably self-evident from the
                        # job log (and if it's not, the CalledProcessError
                        # is not informative anyway), so just propagate the
                        # return code without additional remarks.
                        sys.exit(3)
                    else:
                        raise e

        dxpy.DXJob(job_id).wait_on_done(interval=1)
        asset_id, _ = dxpy.get_dxlink_ids(dxpy.api.job_describe(job_id)['output']['asset_bundle'])

        if args.json:
            print(json.dumps({"id": asset_id}))
        else:
            print("\nAsset bundle '" + asset_id +
                  "' is built and can now be used in your app/applet's dxapp.json\n", file=sys.stderr)
    except Exception as de:
        print(de.__class__.__name__ + ": " + str(de), file=sys.stderr)
        sys.exit(1)
    finally:
        if conf_file:
            try:
                conf_file.remove()
            except:
                pass
        if make_file:
            try:
                make_file.remove()
            except:
                pass
        if asset_file:
            try:
                asset_file.remove()
            except:
                pass
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os
import sys
import subprocess
import tempfile
import shutil
import json
from .exceptions import err_exit
from .utils import json_load_raise_on_duplicates
from .utils.resolver import is_container_id, resolve_path
from .cli import try_call
import dxpy
```

## Definitions it uses from the same module
```python
ASSET_BUILDERS = {
    '12.04': ASSET_BUILDER_PRECISE,
    '14.04': ASSET_BUILDER_TRUSTY,
    '16.04': ASSET_BUILDER_XENIAL,
    '16.04_v1': ASSET_BUILDER_XENIAL_V1,
    '20.04': ASSET_BUILDER_FOCAL,
    '24.04': ASSET_BUILDER_NOBLE,
}

class AssetBuilderException(Exception):
    """
    This exception is raised by the methods in this module
    when asset building fails.
    """
    pass

def parse_asset_spec(src_dir):
    if not os.path.isdir(src_dir):
        err_exit(src_dir + " is not a valid directory.")
    if not os.path.exists(os.path.join(src_dir, "dxasset.json")):
        raise AssetBuilderException("'" + src_dir + "' is not a valid DNAnexus asset source directory." +
                                    " It does not contain a 'dxasset.json' file.")
    with open(os.path.join(src_dir, "dxasset.json")) as asset_desc:
        try:
            return json_load_raise_on_duplicates(asset_desc)
        except Exception as e:
            raise AssetBuilderException("Could not parse dxasset.json file as JSON: " + str(e.args))

def validate_conf(asset_conf):
    """
    Validates the contents of the conf file and makes sure that the required information
    is provided.
        {
            "name": "asset_library_name",
            "title": "A human readable name",
            "description": " A detailed description abput the asset",
            "version": "0.0.1",
            "runSpecVersion": "1",
            "release": "16.04",
            "distribution": "Ubuntu"
            "execDepends":
                        [
                            {"name": "samtools", "package_manager": "apt"},
                            {"name": "bamtools"},
                            {"name": "bio", "package_manager": "gem", "version": "1.4.3"},
                            {"name": "pysam","package_manager": "pip", "version": "0.7.4"},
                            {"name": "Bio::SeqIO", "package_manager": "cpan", "version": "1.006924"}
                        ]
        }
    """
    if 'name' not in asset_conf:
        raise AssetBuilderException('The asset configuration does not contain the required field "name".')

    # Validate runSpec
    if 'release' not in asset_conf or asset_conf['release'] not in ["24.04", "20.04", "16.04", "14.04", "12.04"]:
        raise AssetBuilderException('The "release" field value should be either "24.04", "20.04", "16.04" (DEPRECATED), "14.04" (DEPRECATED), or "12.04" (DEPRECATED)')
    if 'runSpecVersion' in asset_conf:
        if asset_conf['runSpecVersion'] not in ["0", "1"]:
            raise AssetBuilderException('The "runSpecVersion" field should be either "0", or "1"')
        if (asset_conf['runSpecVersion'] == "1" and asset_conf['release'] != "16.04"):
            raise AssetBuilderException('The "runSpecVersion" field can only be "1" if "release" is "16.04"')
    else:
        asset_conf['runSpecVersion'] = "0"
    if 'distribution' in asset_conf:
        if asset_conf['distribution'] != "Ubuntu":
            raise AssetBuilderException('The distribution may only take the value "Ubuntu".')
    else:
        asset_conf['distribution'] = "Ubuntu"

    if 'version' not in asset_conf:
        raise AssetBuilderException('The asset configuration does not contain the required field "version". ')
    if 'title' not in asset_conf:
        raise AssetBuilderException('The asset configuration does not contain the required field "title". ')
    if 'description' not in asset_conf:
        raise AssetBuilderException('The asset configuration does not contain the required field "description".')

def dx_upload(file_name, dest_project, target_folder, json_out):
    try:
        maybe_progress_kwargs = {} if json_out else dict(show_progress=True)
        remote_file = dxpy.upload_local_file(file_name,
                                             project=dest_project,
                                             folder=target_folder,
                                             wait_on_close=True,
                                             **maybe_progress_kwargs)
        return remote_file
    except:
        print("Failed to upload the file " + file_name, file=sys.stderr)
        raise

def get_asset_make(src_dir, dest_folder, target_folder, json_out):
    if os.path.exists(os.path.join(src_dir, "Makefile")):
        return dx_upload(os.path.join(src_dir, "Makefile"), dest_folder, target_folder, json_out)
    elif os.path.exists(os.path.join(src_dir, "makefile")):
        return dx_upload(os.path.join(src_dir, "makefile"), dest_folder, target_folder, json_out)

def parse_destination(dest_str):
    """
    Parses dest_str, which is (roughly) of the form
    PROJECT:/FOLDER/NAME, and returns a tuple (project, folder, name)
    """
    # Interpret strings of form "project-XXXX" (no colon) as project. If
    # we pass these through to resolve_path they would get interpreted
    # as folder names...
    if is_container_id(dest_str):
        return (dest_str, None, None)

    # ...otherwise, defer to resolver.resolve_path. This handles the
    # following forms:
    #
    # /FOLDER/
    # /ENTITYNAME
    # /FOLDER/ENTITYNAME
    # [PROJECT]:
    # [PROJECT]:/FOLDER/
    # [PROJECT]:/ENTITYNAME
    # [PROJECT]:/FOLDER/ENTITYNAME
    return try_call(resolve_path, dest_str)

def get_asset_tarball(asset_name, src_dir, dest_project, dest_folder, json_out):
    """
    If the src_dir contains a "resources" directory its contents are archived and
    the archived file is uploaded to the platform
    """
    if os.path.isdir(os.path.join(src_dir, "resources")):
        temp_dir = tempfile.mkdtemp()
        try:
            resource_file = os.path.join(temp_dir, asset_name + "_resources.tar.gz")
            cmd = ["tar", "-czf", resource_file, "-C", os.path.join(src_dir, "resources"), "."]
            subprocess.check_call(cmd)
            file_id = dx_upload(resource_file, dest_project, dest_folder, json_out)
            return file_id
        finally:
            shutil.rmtree(temp_dir)
```

## Signatures of what its module imports from the repository
```python
# from .exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from .utils import json_load_raise_on_duplicates
def json_load_raise_on_duplicates(*args, **kwargs):
    """Like json.load(), but raises an error on duplicate keys."""
    ...

# from .utils.resolver import is_container_id
def is_container_id(string):
    ...

# from .utils.resolver import resolve_path
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
    """:param path: A path to a data object to attempt to resolve"""
    ...

# from .cli import try_call
def try_call(func, *args, **kwargs):
    ...
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `build_asset`. Remember: setup in the thunk or at module level, never timed.