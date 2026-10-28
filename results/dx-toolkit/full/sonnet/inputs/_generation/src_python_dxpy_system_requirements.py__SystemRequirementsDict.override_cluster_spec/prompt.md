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
Function under test: `SystemRequirementsDict.override_cluster_spec` in `src/python/dxpy/system_requirements.py`
Import it as `from dxpy.system_requirements import SystemRequirementsDict`; the method is called as `SystemRequirementsDict.override_cluster_spec(instance, ...)`.

## The function
```python
    def override_cluster_spec(self, srd):
        """
        Returns SystemRequirementsDict can be passed in a "systemRequirements"
        input or as an entry of the "systemRequirementsByExecutable" mapping
        to app-xxx/run, e.g. {'fn': {'clusterSpec': {initialInstanceCount: 3, version: "2.4.0", ..}}}
        Since full clusterSpec must be passed to the API server, we need to retrieve the cluster
        spec defined in app doc's systemRequirements and overwrite the field initialInstanceCount
        with the value the user passed to dx run for each entrypoint.
        initialInstanceCount is currently the only clusterSpec's field the user is allowed to change
        at runtime.
        A few scenarios when requesting instance count for different entrypoints with dx run 
        and the resulting merged systemRequirements (merged_cluster_spec). The bootstapScript
        field here is only one of many (version, ports, etc) that should be copied from app
        spec to merged_cluster_spec:

        Requested: {"*": 5}
        App doc: {"main": "clusterSpec": {"initialInstanceCount": 7, bootstrapScript: "x.sh"},
                "other": "clusterSpec": {"initialInstanceCount": 9, bootstrapScript: "y.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 5, bootstrapScript: "x.sh"},
                "other": "clusterSpec": {"initialInstanceCount": 5, bootstrapScript: "y.sh"}}
        
        Requested: {"*": 15}
        App doc: {"main": "clusterSpec": {"initialInstanceCount": 7, bootstrapScript: "x.sh"},
                  "other": "clusterSpec": {"initialInstanceCount": 9, bootstrapScript: "y.sh"},
                  "*": "clusterSpec": {"initialInstanceCount": 11, bootstrapScript: "y.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 15, bootstrapScript: "x.sh"},
                 "other": "clusterSpec": {"initialInstanceCount": 15, bootstrapScript: "y.sh"},
                 "*": "clusterSpec": {"initialInstanceCount": 15, bootstrapScript: "y.sh"}}

        Requested: {"main": 12}
        App doc: {"main": "clusterSpec": {"initialInstanceCount": 7, bootstrapScript: "x.sh"},
                  "other": "clusterSpec": {"initialInstanceCount": 9, bootstrapScript: "y.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 12, bootstrapScript: "x.sh"}}

        Requested: {"main": 33}
        App doc: {"*": "clusterSpec": {"initialInstanceCount": 2, bootstrapScript: "z.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 33, bootstrapScript: "z.sh"}}

        Requested: {"main": 22, "*": 11}
        App doc: {"*": "clusterSpec": {"initialInstanceCount": 2, bootstrapScript: "t.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 22, bootstrapScript: "t.sh"},
                 "*": "clusterSpec": {"initialInstanceCount": 11, bootstrapScript: "t.sh"}}
        """

        merged_cluster_spec = copy.deepcopy(self.entrypoints)

        # Remove entrypoints without "clusterSpec"
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if v.get("clusterSpec") is not None])

        # Remove entrypoints not provided in requested instance counts
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if \
            k in srd.entrypoints or "*" in srd.entrypoints])

        # Overwrite values of self.entrypoints.clusterSpec with the ones from srd
        # Named entrypoint takes precedence over the wildcard
        for entry_pt, req in merged_cluster_spec.items():
            merged_cluster_spec[entry_pt]["clusterSpec"].update(
                srd.entrypoints.get(entry_pt, srd.entrypoints.get("*"))["clusterSpec"])

        # Check if all entrypoints in srd are included in merged_cluster_spec
        # (if a named entrypoint was used in srd and such an entrypoint doesn't exist
        #  in app sys req, we need to take the cluster spec from the app's "*", if it exists)
        for entry_pt, req in srd.entrypoints.items():
            if entry_pt not in merged_cluster_spec and "*" in self.entrypoints and "clusterSpec" in self.entrypoints["*"]:
                merged_cluster_spec[entry_pt] = {"clusterSpec": copy.deepcopy(self.entrypoints["*"]["clusterSpec"])}
                merged_cluster_spec[entry_pt]["clusterSpec"].update(req["clusterSpec"])

        return SystemRequirementsDict(merged_cluster_spec)
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class SystemRequirementsDict(object):
    """
    A class representing system requirements that can be passed as
    "systemRequirements" or an entry of the "systemRequirementsByExecutable"
    to the class-xxxx/run or job/new API call (after converting
    it to a dictionary with as_dict()).
    """
    def __init__(self, entrypoints):
        """
        Example of the entrypoints input:
        {"main":
            {"instanceType": "mem2_hdd2_x2"},
         "other_function":
            {"instanceType": "mem2_hdd2_x1",
             "clusterSpec": {"type": "spark",
                             "version": "2.4.0",
                             "initialInstanceCount": 2}}}
        """
        if entrypoints is not None and not isinstance(entrypoints, dict):
            raise DXError("Expected entrypoints to be a dict or None")
        self.entrypoints = copy.deepcopy(entrypoints)
    @classmethod
    def from_instance_count(cls, instance_count_arg, entrypoint="*"):
        """
        Returns a SystemRequirementsDict that can be passed as a
        "systemRequirements" input or an entry of the "systemRequirementsByExecutable" mapping
        to job/new or run/ API calls.
        The instance_count_arg should be either a:
        * string or int eg. "6" or 8
        * dictionary, eg. {"main": 4, "other_function": 2}
        """
        ...
    @classmethod
    def from_instance_type(cls, instance_type_arg, entrypoint="*"):
        """
        Returns SystemRequirementsDict that can be passed as a
        "systemRequirements" input or an entry of the "systemRequirementsByExecutable" mapping
        to job/new or run/ API calls.
        The instance_type_arg should be either a:
        * string, eg. mem1_ssd1_x2
        * dictionary, eg. {"main": "mem2_hdd2_x2", "other_function": "mem2_hdd2_x1"}
        """
        ...
    @classmethod
    def from_sys_requirements(cls, system_requirements, _type='all'):
        """
        Returns SystemRequirementsDict encapsulating system requirements.
        It can extract only entrypoints with specific fields ('clusterSpec',
        'instanceType', 'instanceTypeSelector', etc), depending on the value of _type.
        """
        ...
    def override_cluster_spec(self, srd):
        """
        Returns SystemRequirementsDict can be passed in a "systemRequirements"
        input or as an entry of the "systemRequirementsByExecutable" mapping
        to app-xxx/run, e.g. {'fn': {'clusterSpec': {initialInstanceCount: 3, version: "2.4.0", ..}}}
        Since full clusterSpec must be passed to the API server, we need to retrieve the cluster
        spec defined in app doc's systemRequirements and overwrite the field initialInstanceCount
        with the value the user passed to dx run for each entrypoint.
        initialInstanceCount is currently the only clusterSpec's field the user is allowed to change
        at runtime.
        A few scenarios when requesting instance count for different entrypoints with dx run 
        and the resulting merged systemRequirements (merged_cluster_spec). The bootstapScript
        field here is only one of many (version, ports, etc) that should be copied from app
        spec to merged_cluster_spec:

        Requested: {"*": 5}
        App doc: {"main": "clusterSpec": {"initialInstanceCount": 7, bootstrapScript: "x.sh"},
                "other": "clusterSpec": {"initialInstanceCount": 9, bootstrapScript: "y.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 5, bootstrapScript: "x.sh"},
                "other": "clusterSpec": {"initialInstanceCount": 5, bootstrapScript: "y.sh"}}
        
        Requested: {"*": 15}
        App doc: {"main": "clusterSpec": {"initialInstanceCount": 7, bootstrapScript: "x.sh"},
                  "other": "clusterSpec": {"initialInstanceCount": 9, bootstrapScript: "y.sh"},
                  "*": "clusterSpec": {"initialInstanceCount": 11, bootstrapScript: "y.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 15, bootstrapScript: "x.sh"},
                 "other": "clusterSpec": {"initialInstanceCount": 15, bootstrapScript: "y.sh"},
                 "*": "clusterSpec": {"initialInstanceCount": 15, bootstrapScript: "y.sh"}}

        Requested: {"main": 12}
        App doc: {"main": "clusterSpec": {"initialInstanceCount": 7, bootstrapScript: "x.sh"},
                  "other": "clusterSpec": {"initialInstanceCount": 9, bootstrapScript: "y.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 12, bootstrapScript: "x.sh"}}

        Requested: {"main": 33}
        App doc: {"*": "clusterSpec": {"initialInstanceCount": 2, bootstrapScript: "z.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 33, bootstrapScript: "z.sh"}}

        Requested: {"main": 22, "*": 11}
        App doc: {"*": "clusterSpec": {"initialInstanceCount": 2, bootstrapScript: "t.sh"}}
        Merged: {"main": "clusterSpec": {"initialInstanceCount": 22, bootstrapScript: "t.sh"},
                 "*": "clusterSpec": {"initialInstanceCount": 11, bootstrapScript: "t.sh"}}
        """

        merged_cluster_spec = copy.deepcopy(self.entrypoints)

        # Remove entrypoints without "clusterSpec"
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if v.get("clusterSpec") is not None])

        # Remove entrypoints not provided in requested instance counts
        merged_cluster_spec = dict([(k, v) for k, v in merged_cluster_spec.items() if \
            k in srd.entrypoints or "*" in srd.entrypoints])

        # Overwrite values of self.entrypoints.clusterSpec with the ones from srd
        # Named entrypoint takes precedence over the wildcard
        for entry_pt, req in merged_cluster_spec.items():
            merged_cluster_spec[entry_pt]["clusterSpec"].update(
                srd.entrypoints.get(entry_pt, srd.entrypoints.get("*"))["clusterSpec"])

        # Check if all entrypoints in srd are included in merged_cluster_spec
        # (if a named entrypoint was used in srd and such an entrypoint doesn't exist
        #  in app sys req, we need to take the cluster spec from the app's "*", if it exists)
        for entry_pt, req in srd.entrypoints.items():
            if entry_pt not in merged_cluster_spec and "*" in self.entrypoints and "clusterSpec" in self.entrypoints["*"]:
                merged_cluster_spec[entry_pt] = {"clusterSpec": copy.deepcopy(self.entrypoints["*"]["clusterSpec"])}
                merged_cluster_spec[entry_pt]["clusterSpec"].update(req["clusterSpec"])

        return SystemRequirementsDict(merged_cluster_spec)
    def override_spec(self, requested_spec):
        ...
    def _add_dict_values(self, d1, d2):
        """
        Merges the values of two dictionaries, which are expected to be dictionaries, e.g
        d1 = {'a': {'x': pqr}}
        d2 = {'a': {'y': lmn}, 'b': {'y': rst}}
        will return: {'a': {'x': pqr, 'y': lmn}, 'b': {'y': rst}}.
        Collisions of the keys of the sub-dictionaries are not checked.
        """
        ...
    def __add__(self, other):
        ...
    def as_dict(self):
        ...
```

## Imports of its module
```python
from collections import defaultdict
import copy
from .utils import merge
from .exceptions import (err_exit, DXError, DXCLIError)
from .compat import basestring
```

## Signatures of what its module imports from the repository
```python
# from .utils import merge
def merge(d, u):
    """Recursively updates a dictionary."""
    ...

# from .exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from .exceptions import DXError
class DXError(Exception):

# from .exceptions import DXCLIError
class DXCLIError(DXError):
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxpy_utils.py:400

    def test_add(self):
        d1 = {'a': {'x': 'pqr'}}
        d2 = {'a': {'y': 'lmn'}, 'b': {'y': 'rst'}}
        srd1 = SystemRequirementsDict(d1)
        srd2 = SystemRequirementsDict(d2)
        added = srd1 + srd2
        expected = SystemRequirementsDict({'a': {'x': 'pqr', 'y': 'lmn'}, 'b': {'y': 'rst'}})

# src/python/test/test_dxpy_utils.py:401
    def test_add(self):
        d1 = {'a': {'x': 'pqr'}}
        d2 = {'a': {'y': 'lmn'}, 'b': {'y': 'rst'}}
        srd1 = SystemRequirementsDict(d1)
        srd2 = SystemRequirementsDict(d2)
        added = srd1 + srd2
        expected = SystemRequirementsDict({'a': {'x': 'pqr', 'y': 'lmn'}, 'b': {'y': 'rst'}})
        self.assertDictEqual(expected.entrypoints, added.entrypoints)

# src/python/dxpy/bindings/dxapplet.py:63
                run_input[arg] = kwargs[arg]

        if any(kwargs.get(key) is not None for key in ['instance_type', 'cluster_spec', 'fpga_driver', 'nvidia_driver']):
            instance_type_srd = SystemRequirementsDict.from_instance_type(kwargs.get('instance_type'))
            cluster_spec_srd = SystemRequirementsDict(kwargs.get('cluster_spec'))
            fpga_driver_srd = SystemRequirementsDict(kwargs.get('fpga_driver'))
            nvidia_driver_srd = SystemRequirementsDict(kwargs.get('nvidia_driver'))
            run_input["systemRequirements"] = (instance_type_srd + cluster_spec_srd + fpga_driver_srd + nvidia_driver_srd).as_dict()

# src/python/dxpy/bindings/dxapplet.py:64

        if any(kwargs.get(key) is not None for key in ['instance_type', 'cluster_spec', 'fpga_driver', 'nvidia_driver']):
            instance_type_srd = SystemRequirementsDict.from_instance_type(kwargs.get('instance_type'))
            cluster_spec_srd = SystemRequirementsDict(kwargs.get('cluster_spec'))
            fpga_driver_srd = SystemRequirementsDict(kwargs.get('fpga_driver'))
            nvidia_driver_srd = SystemRequirementsDict(kwargs.get('nvidia_driver'))
            run_input["systemRequirements"] = (instance_type_srd + cluster_spec_srd + fpga_driver_srd + nvidia_driver_srd).as_dict()


# src/python/dxpy/bindings/dxjob.py:189
            if properties is not None:
                req_input["properties"] = properties
            if any(requirement is not None for requirement in [instance_type, cluster_spec, fpga_driver, nvidia_driver]):
                instance_type_srd = SystemRequirementsDict.from_instance_type(instance_type, fn_name)
                cluster_spec_srd = SystemRequirementsDict(cluster_spec)
                fpga_driver_srd = SystemRequirementsDict(fpga_driver)
                nvidia_driver_srd = SystemRequirementsDict(nvidia_driver)
                req_input["systemRequirements"] = (instance_type_srd + cluster_spec_srd + fpga_driver_srd + nvidia_driver_srd).as_dict()

# src/python/dxpy/bindings/dxjob.py:190
                req_input["properties"] = properties
            if any(requirement is not None for requirement in [instance_type, cluster_spec, fpga_driver, nvidia_driver]):
                instance_type_srd = SystemRequirementsDict.from_instance_type(instance_type, fn_name)
                cluster_spec_srd = SystemRequirementsDict(cluster_spec)
                fpga_driver_srd = SystemRequirementsDict(fpga_driver)
                nvidia_driver_srd = SystemRequirementsDict(nvidia_driver)
                req_input["systemRequirements"] = (instance_type_srd + cluster_spec_srd + fpga_driver_srd + nvidia_driver_srd).as_dict()
            if system_requirements is not None:
```

Write `checks()` and `cases()` for `SystemRequirementsDict.override_cluster_spec`. Remember: setup in the thunk or at module level, never timed.