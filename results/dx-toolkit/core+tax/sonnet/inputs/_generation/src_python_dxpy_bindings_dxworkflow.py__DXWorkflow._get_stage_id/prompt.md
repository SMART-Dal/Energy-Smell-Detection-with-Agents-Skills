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
Function under test: `DXWorkflow._get_stage_id` in `src/python/dxpy/bindings/dxworkflow.py`
Import it as `from dxpy.bindings.dxworkflow import DXWorkflow`; the method is called as `DXWorkflow._get_stage_id(instance, ...)`.

## The function
```python
    def _get_stage_id(self, stage):
        '''
        :param stage: A stage ID, name, or index (stage index is the number n for the nth stage, starting from 0; can be provided as an int or a string)
        :type stage: int or string
        :returns: The stage ID (this is a no-op if it was already a stage ID)
        :raises: :class:`~dxpy.exceptions.DXError` if *stage* could not be parsed, resolved to a stage ID, or it could not be found in the workflow
        '''
        # first, if it is a string, see if it is an integer
        if isinstance(stage, basestring):
            try:
                stage = int(stage)
            except:
                # we'll try parsing it as a string later
                pass

        if not isinstance(stage, basestring):
            # Try to parse as stage index; ensure that if it's not a
            # string that it is an integer at this point.
            try:
                stage_index = int(stage)
            except:
                raise DXError('DXWorkflow: the given stage identifier was neither a string stage ID nor an integer index')
            if stage_index < 0 or stage_index >= len(self.stages):
                raise DXError('DXWorkflow: the workflow contains ' + str(len(self.stages)) + \
                              ' stage(s), and the numerical value of the given stage identifier is out of range')
            return self.stages[stage_index].get("id")

        if re.compile('^([a-zA-Z_]|stage-)[0-9a-zA-Z_]*$').match(stage) is not None:
            # Check if there exists a stage with this stage id
            stage_id_exists = any([stg['id'] for stg in self.stages if stg.get('id') == stage])
            if stage_id_exists:
                return stage

        # A stage with the provided ID can't be found in the workflow, so look for it as a name
        stage_ids_matching_name = [stg['id'] for stg in self.stages if stg.get('name') == stage]
        if len(stage_ids_matching_name) == 0:
            raise DXError('DXWorkflow: the given stage identifier ' + stage + ' could not be found as a stage ID nor as a stage name')
        elif len(stage_ids_matching_name) > 1:
            raise DXError('DXWorkflow: more than one workflow stage was found to have the name "' + stage + '"')
        else:
            return stage_ids_matching_name[0]
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class DXWorkflow(DXDataObject, DXExecutable):
    '''
    Remote workflow object handler.  This class is used for the
    workflow class data objects which produce an analysis when run.
    '''
    _class = "workflow"
    _describe = staticmethod(dxpy.api.workflow_describe)
    _add_types = staticmethod(dxpy.api.workflow_add_types)
    _remove_types = staticmethod(dxpy.api.workflow_remove_types)
    _get_details = staticmethod(dxpy.api.workflow_get_details)
    _set_details = staticmethod(dxpy.api.workflow_set_details)
    _set_visibility = staticmethod(dxpy.api.workflow_set_visibility)
    _rename = staticmethod(dxpy.api.workflow_rename)
    _set_properties = staticmethod(dxpy.api.workflow_set_properties)
    _add_tags = staticmethod(dxpy.api.workflow_add_tags)
    _remove_tags = staticmethod(dxpy.api.workflow_remove_tags)
    _close = staticmethod(dxpy.api.workflow_close)
    _list_projects = staticmethod(dxpy.api.workflow_list_projects)
    def _new(self, dx_hash, **kwargs):
        """
        :param dx_hash: Standard hash populated in :func:`dxpy.bindings.DXDataObject.new()` containing attributes common to all data object classes.
        :type dx_hash: dict
        :param title: Workflow title (optional)
        :type title: string
        :param summary: Workflow summary (optional)
        :type summary: string
        :param description: Workflow description (optional)
        :type description: string
        :param output_folder: Default output folder of the workflow (optional)
        :type output_folder: string
        :param stages: Stages of the workflow (optional)
        :type stages: array of dictionaries
        :param workflow_inputs: Workflow-level input specification (optional)
        :type workflow_inputs: array of dictionaries
        :param workflow_outputs: Workflow-level output specification (optional)
        :type workflow_outputs: array of dictionaries
        :param init_from: Another analysis workflow object handler or and analysis (string or handler) from which to initialize the metadata (optional)
        :type init_from: :class:`~dxpy.bindings.dxworkflow.DXWorkflow`, :class:`~dxpy.bindings.dxanalysis.DXAnalysis`, or string (for analysis IDs only)

        Create a new remote workflow object.
        """
        ...
    def _add_edit_version_to_request(self, request_hash, edit_version=None):
        ...
    def _get_stage_id(self, stage):
        '''
        :param stage: A stage ID, name, or index (stage index is the number n for the nth stage, starting from 0; can be provided as an int or a string)
        :type stage: int or string
        :returns: The stage ID (this is a no-op if it was already a stage ID)
        :raises: :class:`~dxpy.exceptions.DXError` if *stage* could not be parsed, resolved to a stage ID, or it could not be found in the workflow
        '''
        # first, if it is a string, see if it is an integer
        if isinstance(stage, basestring):
            try:
                stage = int(stage)
            except:
                # we'll try parsing it as a string later
                pass

        if not isinstance(stage, basestring):
            # Try to parse as stage index; ensure that if it's not a
            # string that it is an integer at this point.
            try:
                stage_index = int(stage)
            except:
                raise DXError('DXWorkflow: the given stage identifier was neither a string stage ID nor an integer index')
            if stage_index < 0 or stage_index >= len(self.stages):
                raise DXError('DXWorkflow: the workflow contains ' + str(len(self.stages)) + \
                              ' stage(s), and the numerical value of the given stage identifier is out of range')
            return self.stages[stage_index].get("id")

        if re.compile('^([a-zA-Z_]|stage-)[0-9a-zA-Z_]*$').match(stage) is not None:
            # Check if there exists a stage with this stage id
            stage_id_exists = any([stg['id'] for stg in self.stages if stg.get('id') == stage])
            if stage_id_exists:
                return stage

        # A stage with the provided ID can't be found in the workflow, so look for it as a name
        stage_ids_matching_name = [stg['id'] for stg in self.stages if stg.get('name') == stage]
        if len(stage_ids_matching_name) == 0:
            raise DXError('DXWorkflow: the given stage identifier ' + stage + ' could not be found as a stage ID nor as a stage name')
        elif len(stage_ids_matching_name) > 1:
            raise DXError('DXWorkflow: more than one workflow stage was found to have the name "' + stage + '"')
        else:
            return stage_ids_matching_name[0]
    def add_stage(self, executable, stage_id=None, name=None, folder=None, stage_input=None, instance_type=None,
                  edit_version=None, **kwargs):
        '''
        :param executable: string or a handler for an app or applet
        :type executable: string, DXApplet, or DXApp
        :param stage_id: id for the stage (optional)
        :type stage_id: string
        :param name: name for the stage (optional)
        :type name: string
        :param folder: default output folder for the stage; either a relative or absolute path (optional)
        :type folder: string
        :param stage_input: input fields to bind as default inputs for the executable (optional)
        :type stage_input: dict
        :param instance_type: Default instance type on which all jobs will be run for this stage, or a dict mapping function names to instance type requests
        :type instance_type: string or dict
        :param edit_version: if provided, the edit version of the workflow that should be modified; if not provided, the current edit version will be used (optional)
        :type edit_version: int
        :returns: ID of the added stage
        :rtype: string
        :raises: :class:`~dxpy.exceptions.DXError` if *executable* is not an expected type :class:`~dxpy.exceptions.DXAPIError` for errors thrown from the API call

        Adds the specified executable as a new stage in the workflow.
        '''
        ...
    def get_stage(self, stage, **kwargs):
        '''
        :param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID
        :type stage: int or string
        :returns: Hash of stage descriptor in workflow
        '''
        ...
    def remove_stage(self, stage, edit_version=None, **kwargs):
        '''
        :param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID
        :type stage: int or string
        :param edit_version: if provided, the edit version of the workflow that should be modified; if not provided, the current edit version will be used (optional)
        :type edit_version: int
        :returns: Stage ID that was removed
        :rtype: string

        Removes the specified stage from the workflow
        '''
        ...
    def move_stage(self, stage, new_index, edit_version=None, **kwargs):
        '''
        :param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID
        :type stage: int or string
        :param new_index: The new position in the order of stages that the specified stage should have (where 0 indicates the first stage)
        :type new_index: int
        :param edit_version: if provided, the edit version of the workflow that should be modified; if not provided, the current edit version will be used (optional)
        :type edit_version: int

        Removes the specified stage from the workflow
        '''
        ...
    def update(self, title=None, unset_title=False, summary=None, description=None,
               output_folder=None, unset_output_folder=False,
               workflow_inputs=None, unset_workflow_inputs=False,
               workflow_outputs=None, unset_workflow_outputs=False,
               stages=None, edit_version=None, **kwargs):
        '''
        :param title: workflow title to set; cannot be provided with *unset_title* set to True
        :type title: string
        :param unset_title: whether to unset the title; cannot be provided with string value for *title*
        :type unset_title: boolean
        :param summary: workflow summary to set
        :type summary: string
        :param description: workflow description to set
        :type description: string
        :param output_folder: new default output folder for the workflow
        :type output_folder: string
        :param unset_folder: whether to unset the default output folder; cannot be True with string value for *output_folder*
        :type unset_folder: boolean
        :param stages: updates to the stages to make; see API documentation for /workflow-xxxx/update for syntax of this field; use :meth:`update_stage()` to update a single stage
        :type stages: dict
        :param workflow_inputs: updates to the workflow input to make; see API documentation for /workflow-xxxx/update for syntax of this field
        :type workflow_inputs: dict
        :param workflow_outputs: updates to the workflow output to make; see API documentation for /workflow-xxxx/update for syntax of this field
        :type workflow_outputs: dict
        :param edit_version: if provided, the edit version of the workflow that should be modified; if not provided, the current edit version will be used (optional)
        :type edit_version: int

        Make general metadata updates to the workflow
        '''
        ...
    def update_stage(self, stage, executable=None, force=False,
                     name=None, unset_name=False, folder=None, unset_folder=False, stage_input=None,
                     instance_type=None, edit_version=None, **kwargs):
        '''
        :param stage: A number for the stage index (for the nth stage, starting from 0), or a string stage index, name, or ID
        :type stage: int or string
        :param executable: string or a handler for an app or applet
        :type executable: string, DXApplet, or DXApp
        :param force: whether to use *executable* even if it is incompatible with the previous executable's spec
        :type force: boolean
        :param name: new name for the stage; cannot be provided with *unset_name* set to True
        :type name: string
        :param unset_name: whether to unset the stage name; cannot be True with string value for *name*
        :type unset_name: boolean
        :param folder: new default output folder for the stage; either a relative or absolute path (optional)
        :type folder: string
        :param unset_folder: whether to unset the stage folder; cannot be True with string value for *folder*
        :type unset_folder: boolean
        :param stage_input: input fields to bind as default inputs for the executable (optional)
        :type stage_input: dict
        :param instance_type: Default instance type on which all jobs will be run for this stage, or a dict mapping function names to instance type requests
        :type instance_type: string or dict
        :param edit_version: if provided, the edit version of the workflow that should be modified; if not provided, the current edit version will be used (optional)
        :type edit_version: int

        Removes the specified stage from the workflow
        '''
        ...
    def is_locked(self):
        ...
    def _get_input_name(self, input_str, region=None, describe_output=None):
        '''
        :param input_str: A string of one of the forms: "<exported input field name>", "<explicit workflow input field name>", "<stage ID>.<input field name>", "<stage index>.<input field name>", "<stage name>.<input field name>"
        :type input_str: string
        :returns: If the given form was one of those which uses the stage index or stage name, it is translated to the stage ID for use in the API call (stage name takes precedence)
        '''
        ...
    def _get_effective_input(self, workflow_input):
        ...
    def _get_run_input(self, workflow_input, **kwargs):
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
        :param ignore_reuse_stages: Stages of a workflow (IDs, names, or indices) or "*" for which job reuse should be disabled
        :type ignore_reuse_stages: list
        :returns: Object handler of the newly created analysis
        :rtype: :class:`~dxpy.bindings.dxanalysis.DXAnalysis`

        Run the associated workflow. See :meth:`dxpy.bindings.dxapplet.DXExecutable.run` for additional args.

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
import re
import dxpy
from ..system_requirements import SystemRequirementsDict
from ..bindings import DXDataObject, DXExecutable, DXAnalysis
from ..exceptions import DXError
from ..compat import basestring
```

## Everything else its module defines (headers only)
```python
def new_dxworkflow(title=None, summary=None, description=None, output_folder=None, init_from=None, **kwargs):
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import DXError
class DXError(Exception):

# from ..system_requirements import SystemRequirementsDict
class SystemRequirementsDict(object):
    def __init__(self, entrypoints):
        """Example of the entrypoints input:"""
        ...
    @classmethod
    def from_instance_count(cls, instance_count_arg, entrypoint="*"):
        """Returns a SystemRequirementsDict that can be passed as a"""
        ...
    @classmethod
    def from_instance_type(cls, instance_type_arg, entrypoint="*"):
        """Returns SystemRequirementsDict that can be passed as a"""
        ...
    @classmethod
    def from_sys_requirements(cls, system_requirements, _type='all'):
        """Returns SystemRequirementsDict encapsulating system requirements."""
        ...
    def override_cluster_spec(self, srd):
        """Returns SystemRequirementsDict can be passed in a "systemRequirements""""
        ...
    def override_spec(self, requested_spec):
        ...
    def as_dict(self):
        ...

# from ..bindings import DXDataObject
class DXDataObject(DXObject):
    def __init__(self, dxid=None, project=None):
        ...
    def new(self, **kwargs):
        """:param project: Project ID in which to create the new remote object"""
        ...
    def set_id(self, dxid):
        """:param dxid: Object ID or a DNAnexus link (a dict with key "$dnanexus_link"); if a project ID is provided in the DNAnexus link, it will also be used t"""
        ...
    def set_ids(self, dxid, project=None):
        """:param dxid: Object ID or a DNAnexus link (a dict with key "$dnanexus_link"); if a project ID is provided in the DNAnexus link, it will be used as *pr"""
        ...
    def get_proj_id(self):
        """:returns: Project ID of associated object"""
        ...
    def describe(self, incl_properties=False, incl_details=False, fields=None, default_fields=None, **kwargs):
        """:param fields: set of fields to include in the output, for"""
        ...
    def add_types(self, types, **kwargs):
        """:param types: Types to add to the object"""
        ...
    def remove_types(self, types, **kwargs):
        """:param types: Types to remove from the object"""
        ...
    def get_details(self, **kwargs):
        """Returns the contents of the details of the object."""
        ...
    def set_details(self, details, **kwargs):
        """:param details: Details to set for the object"""
        ...
    def hide(self, **kwargs):
        """:raises: :class:`~dxpy.exceptions.DXAPIError` if the object is not in the "open" state"""
        ...
    def unhide(self, **kwargs):
        """:raises: :class:`~dxpy.exceptions.DXAPIError` if the object is not in the "open" state"""
        ...
    def rename(self, name, **kwargs):
        """:param name: New name for the object"""
        ...
    def get_properties(self, **kwargs):
    # ... (truncated)
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/bindings/dxworkflow.py:69

        dxworkflow = DXWorkflow()
        dxworkflow.new(**kwargs)
    '''
    dxworkflow = DXWorkflow()
    dxworkflow.new(title=title, summary=summary, description=description, output_folder=output_folder, init_from=init_from, **kwargs)
    return dxworkflow


# src/python/dxpy/bindings/dxworkflow.py:251
        :param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID
        :type stage: int or string
        :returns: Hash of stage descriptor in workflow
        '''
        stage_id = self._get_stage_id(stage)
        result = next((stage for stage in self.stages if stage['id'] == stage_id), None)
        if result is None:
            raise DXError('The stage ID ' + stage_id + ' could not be found')
```

Write `checks()` and `cases()` for `DXWorkflow._get_stage_id`. Remember: setup in the thunk or at module level, never timed.