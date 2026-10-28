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
Function under test: `DXGlobalWorkflow.describe_underlying_workflow` in `src/python/dxpy/bindings/dxglobalworkflow.py`
Import it as `from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow`; the method is called as `DXGlobalWorkflow.describe_underlying_workflow(instance, ...)`.

## The function
```python
    def describe_underlying_workflow(self, region, describe_output=None):
        """
        :param region: region name
        :type region: string
        :param describe_output: description of a global workflow
        :type describe_output: dict
        :returns: object description of a workflow
        :rtype: : dict

        Returns an object description of an underlying workflow from a given region.
        """
        assert(describe_output is None or describe_output.get('class', '') == 'globalworkflow')

        if region is None:
            raise DXError(
                'DXGlobalWorkflow: region must be provided to get an underlying workflow')

        # Perhaps we have cached it already
        if region in self._workflow_desc_by_region:
            return self._workflow_desc_by_region[region]

        if not describe_output:
            describe_output = self.describe()

        if region not in describe_output['regionalOptions'].keys():
            raise DXError('DXGlobalWorkflow: the global workflow {} is not enabled in region {}'.format(
                self.get_id(), region))

        underlying_workflow_id = describe_output['regionalOptions'][region]['workflow']
        dxworkflow = dxpy.DXWorkflow(underlying_workflow_id)
        dxworkflow_desc = dxworkflow.describe()
        self._workflow_desc_by_region = dxworkflow_desc
        return dxworkflow_desc
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class DXGlobalWorkflow(DXObject, DXExecutable):
    '''
    Remote global workflow object handler.
    '''
    _class = "globalworkflow"
    def __init__(self, dxid=None, name=None, alias=None):
        DXObject.__init__(self)
        if dxid is not None or name is not None:
            self.set_id(dxid=dxid, name=name, alias=alias)

        # caches for underlying workflow instances and descriptions per region
        # (they are immutable for a given global workflow)
        self._workflows_by_region = {}
        self._workflow_desc_by_region = {}
    def set_id(self, dxid=None, name=None, alias=None):
        '''
        :param dxid: Global workflow ID
        :type dxid: string
        :param name: Global workflow name
        :type name: string
        :param alias: Global workflow version or tag
        :type alias: string
        :raises: :exc:`~dxpy.exceptions.DXError` if *dxid* and some other input are both given or if neither *dxid* nor *name* are given

        Discards the currently stored ID and associates the handler
        with the requested parameters.  Note that if *dxid* is given,
        the other fields should not be given, and if *name* is given,
        *alias* has default value "default".

        '''
        ...
    def get_id(self):
        '''
        :returns: Object ID of associated global workflow
        :rtype: string

        Returns the object ID of the global workflow that the handler is currently
        associated with.
        '''
        ...
    def new(self, **kwargs):
        '''

        .. note:: It is highly recommended that `dx build --create-global-workflow
           <https://documentation.dnanexus.com/user/helpstrings-of-sdk-command-line-utilities#build>`_
           be used instead for global workflow creation.

        Creates a workflow in the global space with the given parameters by using
        the specified workflow(s) in regionalOptions as a base.

        The workflow is available only to its developers until
        :meth:`publish()` is called, and is not run until :meth:`run()`
        is called.

        '''
        ...
    def describe(self, fields=None, **kwargs):
        '''
        :param fields: Hash where the keys are field names that should be returned, and values should be set to True (default is that all fields are returned)
        :type fields: dict
        :returns: Description of the remote global workflow object
        :rtype: dict

        Returns a dict with a description of the workflow.

        '''
        ...
    def publish(self, **kwargs):
        """
        Publishes the global workflow, so all users can find it and use it on the platform.

        The current user must be a developer of the workflow.
        """
        ...
    def describe_underlying_workflow(self, region, describe_output=None):
        """
        :param region: region name
        :type region: string
        :param describe_output: description of a global workflow
        :type describe_output: dict
        :returns: object description of a workflow
        :rtype: : dict

        Returns an object description of an underlying workflow from a given region.
        """
        assert(describe_output is None or describe_output.get('class', '') == 'globalworkflow')

        if region is None:
            raise DXError(
                'DXGlobalWorkflow: region must be provided to get an underlying workflow')

        # Perhaps we have cached it already
        if region in self._workflow_desc_by_region:
            return self._workflow_desc_by_region[region]

        if not describe_output:
            describe_output = self.describe()

        if region not in describe_output['regionalOptions'].keys():
            raise DXError('DXGlobalWorkflow: the global workflow {} is not enabled in region {}'.format(
                self.get_id(), region))

        underlying_workflow_id = describe_output['regionalOptions'][region]['workflow']
        dxworkflow = dxpy.DXWorkflow(underlying_workflow_id)
        dxworkflow_desc = dxworkflow.describe()
        self._workflow_desc_by_region = dxworkflow_desc
        return dxworkflow_desc
    def get_underlying_workflow(self, region, describe_output=None):
        """
        :param region: region name
        :type region: string
        :param describe_output: description of a global workflow
        :type describe_output: dict
        :returns: object handler of a workflow
        :rtype: :class:`~dxpy.bindings.dxworkflow.DXWorkflow`

        Returns an object handler of an underlying workflow from a given region.
        """
        ...
    def append_underlying_workflow_desc(self, describe_output, region):
        """
        :param region: region name
        :type region: string
        :param describe_output: description of a global workflow
        :type describe_output: dict
        :returns: object description of the global workflow
        :rtype: : dict

        Appends stages, inputs, outputs and other workflow-specific metadata to a global workflow describe output.

        Note: global workflow description does not contain functional metadata (stages, IO), since this data
        is region-specific (due to applets and bound inputs) and so reside only in region-specific underlying
        workflows. We add them to global_workflow_desc so that it can be used for a workflow or a global workflow
        """
        ...
    def _get_input_name(self, input_str, region=None, describe_output=None):
        ...
    def _get_run_input(self, workflow_input, project=None, **kwargs):
        """
        Checks the region in which the global workflow is run
        and returns the input associated with the underlying workflow
        from that region.
        """
        ...
    def _run_impl(self, run_input, **kwargs):
        ...
    def run(self, workflow_input, *args, **kwargs):
        '''
        :param workflow_input: Dictionary of the workflow's input arguments; see below for more details
        :type workflow_input: dict
        :param instance_type: Instance type on which all stages' jobs will be run, or a dict mapping function names to instance types. These may be overridden on a per-stage basis if stage_instance_types is specified.
        :type instance_type: string or dict
        :param stage_instance_types: A dict mapping stage IDs, names, or indices to either a string (representing an instance type to be used for all functions in that stage), or a dict mapping function names to instance types.
        :type stage_instance_types: dict
        :param stage_folders: A dict mapping stage IDs, names, indices, and/or the string "*" to folder values to be used for the stages' output folders (use "*" as the default for all unnamed stages)
        :type stage_folders: dict
        :param rerun_stages: A list of stage IDs, names, indices, and/or the string "*" to indicate which stages should be run even if there are cached executions available
        :type rerun_stages: list of strings
        :returns: Object handler of the newly created analysis
        :rtype: :class:`~dxpy.bindings.dxanalysis.DXAnalysis`

        Run the workflow. See :meth:`dxpy.bindings.dxapplet.DXExecutable.run` for additional args.

        When providing input for the workflow, keys should be of one of the following forms:

        * "N.name" where *N* is the stage number, and *name* is the
          name of the input, e.g. "0.reads" if the first stage takes
          in an input called "reads"

        * "stagename.name" where *stagename* is the stage name, and
          *name* is the name of the input within the stage

        * "stageID.name" where *stageID* is the stage ID, and *name*
          is the name of the input within the stage

        * "name" where *name* is the name of a workflow level input
          (defined in inputs) or the name that has been
          exported for the workflow (this name will appear as a key
          in the "inputSpec" of this workflow's description if it has
          been exported for this purpose)

        '''
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import dxpy
from . import DXObject, DXAnalysis, DXExecutable, verify_string_dxid
from ..exceptions import DXError
from ..compat import basestring
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import DXError
class DXError(Exception):

# from . import DXObject
class DXObject(object):
    def __init__(self, dxid=None, project=None):
        # Initialize _dxid and _proj to None values, and have
        # subclasses actually perform the setting of the values once
        # they have been validated.
        ...
    def describe(self, *args, **kwargs):
        """Avoid infinite recursion in __getattr__ if describe is not defined."""
        ...
    def set_id(self, dxid):
        """:param dxid: New ID to be associated with the handler"""
        ...
    def get_id(self):
        """:returns: ID of the associated object"""
        ...

# from . import verify_string_dxid
def verify_string_dxid(dxid, expected_classes):
    """:param dxid: Value to verify as a DNAnexus ID of class *expected_class*"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/bindings/dxglobalworkflow.py:246
        workflows. We add them to global_workflow_desc so that it can be used for a workflow or a global workflow
        """
        assert(describe_output is None or describe_output.get('class') == 'globalworkflow')

        underlying_workflow_desc = self.describe_underlying_workflow(region,
                                                                     describe_output=describe_output)
        for field in ['inputs', 'outputs', 'inputSpec', 'outputSpec', 'stages']:
            describe_output[field] = underlying_workflow_desc[field]
        return describe_output
```

Write `checks()` and `cases()` for `DXGlobalWorkflow.describe_underlying_workflow`. Remember: setup in the thunk or at module level, never timed.