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
Function under test: `ExecutableInputs.add` in `src/python/dxpy/cli/exec_io.py`
Import it as `from dxpy.cli.exec_io import ExecutableInputs`; the method is called as `ExecutableInputs.add(instance, ...)`.

## The function
```python
    def add(self, input_name, input_value):
        if self.input_name_prefix is not None:
            if input_name.startswith(self.input_name_prefix):
                input_name = input_name[len(self.input_name_prefix):]
            else: # Skip inputs that don't start with prefix
                return

        if ':' in input_name:
            input_class = input_name[input_name.find(':') + 1:]
            input_name = input_name[:input_name.find(':')]
        else:
            input_class = None

        if self.input_spec is not None:
            if input_name not in self.input_spec and self._desc.get('class') != 'workflow':
                raise DXCLIError('Input field called "' + input_name + '" was not found in the input spec')
            elif input_name in self.input_spec:
                input_class = self.input_spec[input_name]['class']

        if input_class is None:
            resolved_input_as_jbor = False
            try:
                # Resolve "job-xxxx:output-name" syntax into a canonical job ref
                job_id, field = split_unescaped(':', input_value)
            except:
                pass
            else:
                if is_job_id(job_id) or is_localjob_id(job_id):
                    input_value = _construct_jbor(job_id, field)
                    resolved_input_as_jbor = True

            if resolved_input_as_jbor:
                if isinstance(self.inputs[input_name], list):
                    self.inputs[input_name].append(input_value)
                else:
                    self.inputs[input_name] = input_value
            else:
                try:
                    parsed_input_value = json.loads(input_value, object_pairs_hook=collections.OrderedDict)
                    immediate_types = {collections.OrderedDict, list, int, float}
                    if type(parsed_input_value) not in immediate_types:
                        raise Exception()
                except:
                    # Not recognized JSON (list or dict), so resolve it as a name
                    # Add to self.requires_resolution, and insert None as a placeholder in self.inputs;
                    # self.requires_resolution will also store the location of the corresponding placeholder
                    if isinstance(self.inputs[input_name], list):
                        self.requires_resolution.append((input_name, input_value, None, len(self.inputs[input_name])))
                        self.inputs[input_name].append(None)
                    else:
                        # If the input is to only have a single value, then the index will be -1
                        self.requires_resolution.append((input_name, input_value, None, -1))
                        self.inputs[input_name] = None
                else:
                    if isinstance(self.inputs[input_name], list):
                        self.inputs[input_name].append(parsed_input_value)
                    else:
                        self.inputs[input_name] = parsed_input_value
        else:
            # Input class is known.  Respect the "array" class.
            val_substrings = split_unescaped(':', input_value)
            try:
                if len(val_substrings) == 2 and (is_job_id(val_substrings[0]) or is_localjob_id(val_substrings[0])):
                    input_value = _construct_jbor(val_substrings[0], val_substrings[1])
                    if input_class.startswith('array:'):
                        self.inputs[input_name].append(input_value)
                    else:
                        self.inputs[input_name] = input_value
                else:
                    # TODO: Consolidate the following checks with exec_io.parse_input_or_jbor
                    # `parse_bool()` can throw DXCLIError, which will be
                    # propagated directly to the caller.
                    if input_class == 'boolean':
                        self.inputs[input_name] = parse_bool(input_value)
                    elif input_class == 'array:boolean':
                        self.inputs[input_name].append(parse_bool(input_value))
                    elif input_class == 'string':
                        self.inputs[input_name] = input_value
                    elif input_class == 'array:string':
                        self.inputs[input_name].append(input_value)
                    elif input_class == 'float':
                        self.inputs[input_name] = float(input_value)
                    elif input_class == 'array:float':
                        self.inputs[input_name].append(float(input_value))
                    elif input_class == 'int':
                        self.inputs[input_name] = int(input_value)
                    elif input_class == 'array:int':
                        self.inputs[input_name].append(int(input_value))
                    elif input_class == 'hash':
                        self.inputs[input_name] = json.loads(input_value)
                    elif input_class == 'array:hash':
                        self.inputs[input_name].append(json.loads(input_value))
                    elif input_class == 'job' or input_class == 'app':
                        self.inputs[input_name] = {'$dnanexus_link': input_value}
                    elif input_class == 'array:job' or input_class == 'array:app':
                        self.inputs[input_name].append({'$dnanexus_link': input_value})
                    else:
                        # Add to self.requires_resolution
                        if input_class.startswith('array:'):
                            # No placeholders needed; just pass in input_index that is not -1 to append a result
                            self.requires_resolution.append((input_name, input_value, input_class[6:], 0))
                        else:
                            # input_name is to only have a single value, set index to -1
                            self.requires_resolution.append((input_name, input_value, input_class, -1))
            except (ValueError, TypeError) as details:
                raise DXCLIError('Value provided for input field "' + input_name + '" could not be parsed as ' +
                                 input_class + ': ' + str(details))
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class ExecutableInputs(object):
    def __init__(self, executable=None, input_name_prefix=None, input_spec=None, active_region=None):
        """
        :param executable: Executable object handler
        :type executable: :class:`~dxpy.bindings.dxapplet.DXApplet`,
                          :class:`~dxpy.bindings.dxapp.DXApp`,
                          :class:`~dxpy.bindings.dxworkflow.DXWorkflow`,
                          :class:`~dxpy.bindings.dxglobalworkflow.DXGlobalWorkflow`
        :param input_name_prefix: A prefix set on an input field name
        :type input_name_prefix: string
        :param input_spec: Input specification
        :type input_spec: dict
        :param active_region: The region in which the executable is run, determined by the destination project context.
        :type active_region: string
        """
        self.executable = executable
        self.region = active_region

        self._desc = self.get_executable_description()

        self.required_inputs, self.optional_inputs, self.array_inputs = [], [], set()
        self.input_name_prefix = input_name_prefix
        self.inputs = OrderedDefaultdict(list)

        # List of tuples (input name, input value, input class, index), where input name and input value are
        # propagated from command-line (input class is propagated from the input spec, and may be None if no input
        # spec is provided). index is the order in which this particular input value is specified on the command-line
        # relative to other input values of the same name (as multiple input values may be specified for the same
        # input name). If input class is truthy, then the index is 0. Otherwise, if input name will have only a
        # single input value instead of a list of input values, then index is -1.
        self.requires_resolution = []

        # update input_spec passed to the constructor and initialize
        # self.input_spec, self.optional_inputs, self.required_inputs, self.array_inputs
        self.input_spec = collections.OrderedDict() if 'inputSpec' in self._desc or input_spec else None

        if input_spec is None:
            input_spec = self._desc.get('inputSpec', [])

        if input_spec is None and self._desc['class'] in ('workflow', 'globalworkflow'):
            # this is only the case if it's a workflow with an
            # inaccessible stage
            inaccessible_stages = [stage['id'] for stage in self._desc['stages'] if stage['accessible'] is False]
            raise DXCLIError('The workflow ' + self._desc['id'] + ' has the following inaccessible stage(s): ' + ', '.join(inaccessible_stages))

        # Workflow-level inputs (defined in "inputs")
        #  i. If the workflow has no "inputs"
        #   * The inputs can be passed to stages directly
        # ii. If the workflow has "inputs" (in a closed or open state)
        #   * Only inputs defined in inputs can be passed to the workflow,
        #     using workflow-level input names
        if self._accept_only_workflow_level_inputs():
            input_spec = self._desc.get('inputs', [])

        for spec_atom in input_spec:
            input_name = spec_atom['name']
            if spec_atom['class'].startswith('array:'):
                self.array_inputs.add(input_name)
            self.input_spec[input_name] = spec_atom
            if self._is_input_optional(spec_atom):
                self.optional_inputs.append(input_name)
            else:
                self.required_inputs.append(input_name)
    def _accept_only_workflow_level_inputs(self):
        ...
    def get_executable_description(self):
        ...
    def update(self, new_inputs, strip_prefix=True):
        """
        Updates the inputs dictionary with the key/value pairs from new_inputs, overwriting existing keys.
        """
        ...
    def _update_requires_resolution_inputs(self):
        """
        Updates self.inputs with resolved input values (the input values that were provided
        as paths to items that require resolutions, eg. folder or job/analyses ids)
        """
        ...
    def add(self, input_name, input_value):
        if self.input_name_prefix is not None:
            if input_name.startswith(self.input_name_prefix):
                input_name = input_name[len(self.input_name_prefix):]
            else: # Skip inputs that don't start with prefix
                return

        if ':' in input_name:
            input_class = input_name[input_name.find(':') + 1:]
            input_name = input_name[:input_name.find(':')]
        else:
            input_class = None

        if self.input_spec is not None:
            if input_name not in self.input_spec and self._desc.get('class') != 'workflow':
                raise DXCLIError('Input field called "' + input_name + '" was not found in the input spec')
            elif input_name in self.input_spec:
                input_class = self.input_spec[input_name]['class']

        if input_class is None:
            resolved_input_as_jbor = False
            try:
                # Resolve "job-xxxx:output-name" syntax into a canonical job ref
                job_id, field = split_unescaped(':', input_value)
            except:
                pass
            else:
                if is_job_id(job_id) or is_localjob_id(job_id):
                    input_value = _construct_jbor(job_id, field)
                    resolved_input_as_jbor = True

            if resolved_input_as_jbor:
                if isinstance(self.inputs[input_name], list):
                    self.inputs[input_name].append(input_value)
                else:
                    self.inputs[input_name] = input_value
            else:
                try:
                    parsed_input_value = json.loads(input_value, object_pairs_hook=collections.OrderedDict)
                    immediate_types = {collections.OrderedDict, list, int, float}
                    if type(parsed_input_value) not in immediate_types:
                        raise Exception()
                except:
                    # Not recognized JSON (list or dict), so resolve it as a name
                    # Add to self.requires_resolution, and insert None as a placeholder in self.inputs;
                    # self.requires_resolution will also store the location of the corresponding placeholder
                    if isinstance(self.inputs[input_name], list):
                        self.requires_resolution.append((input_name, input_value, None, len(self.inputs[input_name])))
                        self.inputs[input_name].append(None)
                    else:
                        # If the input is to only have a single value, then the index will be -1
                        self.requires_resolution.append((input_name, input_value, None, -1))
                        self.inputs[input_name] = None
                else:
                    if isinstance(self.inputs[input_name], list):
                        self.inputs[input_name].append(parsed_input_value)
                    else:
                        self.inputs[input_name] = parsed_input_value
        else:
            # Input class is known.  Respect the "array" class.
            val_substrings = split_unescaped(':', input_value)
            try:
                if len(val_substrings) == 2 and (is_job_id(val_substrings[0]) or is_localjob_id(val_substrings[0])):
                    input_value = _construct_jbor(val_substrings[0], val_substrings[1])
                    if input_class.startswith('array:'):
                        self.inputs[input_name].append(input_value)
                    else:
                        self.inputs[input_name] = input_value
                else:
                    # TODO: Consolidate the following checks with exec_io.parse_input_or_jbor
                    # `parse_bool()` can throw DXCLIError, which will be
                    # propagated directly to the caller.
                    if input_class == 'boolean':
                        self.inputs[input_name] = parse_bool(input_value)
                    elif input_class == 'array:boolean':
                        self.inputs[input_name].append(parse_bool(input_value))
                    elif input_class == 'string':
                        self.inputs[input_name] = input_value
                    elif input_class == 'array:string':
                        self.inputs[input_name].append(input_value)
                    elif input_class == 'float':
                        self.inputs[input_name] = float(input_value)
                    elif input_class == 'array:float':
                        self.inputs[input_name].append(float(input_value))
                    elif input_class == 'int':
                        self.inputs[input_name] = int(input_value)
                    elif input_class == 'array:int':
                        self.inputs[input_name].append(int(input_value))
                    elif input_class == 'hash':
                        self.inputs[input_name] = json.loads(input_value)
                    elif input_class == 'array:hash':
                        self.inputs[input_name].append(json.loads(input_value))
                    elif input_class == 'job' or input_class == 'app':
                        self.inputs[input_name] = {'$dnanexus_link': input_value}
                    elif input_class == 'array:job' or input_class == 'array:app':
                        self.inputs[input_name].append({'$dnanexus_link': input_value})
                    else:
                        # Add to self.requires_resolution
                        if input_class.startswith('array:'):
                            # No placeholders needed; just pass in input_index that is not -1 to append a result
                            self.requires_resolution.append((input_name, input_value, input_class[6:], 0))
                        else:
                            # input_name is to only have a single value, set index to -1
                            self.requires_resolution.append((input_name, input_value, input_class, -1))
            except (ValueError, TypeError) as details:
                raise DXCLIError('Value provided for input field "' + input_name + '" could not be parsed as ' +
                                 input_class + ': ' + str(details))
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
    def _is_input_optional(self, spec_atom):
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, json, collections, shlex
from ..bindings.dxworkflow import DXWorkflow
import dxpy
from . import INTERACTIVE_CLI
from ..exceptions import DXCLIError, DXError
from ..utils.printing import (RED, GREEN, WHITE, BOLD, ENDC, UNDERLINE, fill)
from ..utils.describe import (get_find_executions_string, get_ls_l_desc, get_ls_l_desc_fields, parse_typespec)
from ..utils.resolver import (parse_input_keyval, is_hashid, is_job_id, is_localjob_id, paginate_and_pick, pick,
                              resolve_existing_path, resolve_multiple_existing_paths, split_unescaped, is_analysis_id)
from ..utils import OrderedDefaultdict
from ..compat import basestring
```

## Definitions it uses from the same module
```python
def parse_bool(string):
    if len(string) > 0:
        if 'true'.startswith(string.lower()) or string == '1':
            return True
        elif 'false'.startswith(string.lower()) or string == '0':
            return False
    raise DXCLIError('Could not resolve \"' + string +  '\" to a boolean')

def _construct_jbor(job_id, field_name_and_maybe_index):
    '''
    :param job_id: Job ID
    :type job_id: string
    :param field_name_and_maybe_index: Field name, plus possibly ".N" where N is an array index
    :type field_name_and_maybe_index: string
    :returns: dict of JBOR
    '''
    link = {"$dnanexus_link": {"job": job_id}}
    if '.' in field_name_and_maybe_index:
        split_by_dot = field_name_and_maybe_index.rsplit('.', 1)
        link["$dnanexus_link"]["field"] = split_by_dot[0]
        link["$dnanexus_link"]["index"] = int(split_by_dot[1])
    else:
        link["$dnanexus_link"]["field"] = field_name_and_maybe_index
    return link
```

## Everything else its module defines (headers only)
```python
def parse_obj(string, klass):
def parse_input_or_jbor(in_class, value):
def print_param_help(param_desc):
def interactive_help(in_class, param_desc, prompt):
def get_input_array(param_desc):
def format_choices_or_suggestions(header, items, obj_class, initial_indent=' ' * 8, subsequent_indent=' ' * 10):
def get_input_single(param_desc):
def get_optional_input_str(param_desc):
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import DXCLIError
class DXCLIError(DXError):

# from ..utils.resolver import is_job_id
def is_job_id(string):
    ...

# from ..utils.resolver import is_localjob_id
def is_localjob_id(thing):
    ...

# from ..utils.resolver import split_unescaped
def split_unescaped(char, string, include_empty_strings=False):
    """:param char: The character on which to split the string"""
    ...

# from ..bindings.dxworkflow import DXWorkflow
class DXWorkflow(DXDataObject, DXExecutable):
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
    def add_stage(self, executable, stage_id=None, name=None, folder=None, stage_input=None, instance_type=None,
                  edit_version=None, **kwargs):
        """:param executable: string or a handler for an app or applet"""
        ...
    def get_stage(self, stage, **kwargs):
        """:param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID"""
        ...
    def remove_stage(self, stage, edit_version=None, **kwargs):
        """:param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID"""
        ...
    def move_stage(self, stage, new_index, edit_version=None, **kwargs):
        """:param stage: A number for the stage index (for the nth stage, starting from 0), or a string of the stage index, name, or ID"""
        ...
    def update(self, title=None, unset_title=False, summary=None, description=None,
               output_folder=None, unset_output_folder=False,
               workflow_inputs=None, unset_workflow_inputs=False,
               workflow_outputs=None, unset_workflow_outputs=False,
               stages=None, edit_version=None, **kwargs):
        """:param title: workflow title to set; cannot be provided with *unset_title* set to True"""
        ...
    def update_stage(self, stage, executable=None, force=False,
                     name=None, unset_name=False, folder=None, unset_folder=False, stage_input=None,
                     instance_type=None, edit_version=None, **kwargs):
        """:param stage: A number for the stage index (for the nth stage, starting from 0), or a string stage index, name, or ID"""
        ...
    def is_locked(self):
    # ... (truncated)

# from ..exceptions import DXError
class DXError(Exception):

# from ..utils.printing import RED
def RED(message=None):
    ...

# from ..utils.printing import GREEN
def GREEN(message=None):
    ...

# from ..utils.printing import WHITE
def WHITE(message=None):
    ...

# from ..utils.printing import BOLD
def BOLD(message=None):
    ...

# from ..utils.printing import ENDC
def ENDC():
    ...

# from ..utils.printing import UNDERLINE
def UNDERLINE(message=None):
    ...

# from ..utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from ..utils.describe import get_find_executions_string
def get_find_executions_string(desc, has_children, single_result=False, show_outputs=True,
                               is_cached_result=False, show_try=False, as_try_group_root=False):
    """:param desc: hash of execution's describe output"""
    ...

# from ..utils.describe import get_ls_l_desc
def get_ls_l_desc(desc, include_folder=False, include_project=False):
    """desc must have at least all the fields given by get_ls_l_desc_fields."""
    ...

# from ..utils.describe import get_ls_l_desc_fields
def get_ls_l_desc_fields():
    ...

# from ..utils.describe import parse_typespec
def parse_typespec(thing):
    ...

# from ..utils.resolver import parse_input_keyval
def parse_input_keyval(keyeqval):
    ...

# from ..utils.resolver import is_hashid
def is_hashid(string):
    ...

# from ..utils.resolver import paginate_and_pick
def paginate_and_pick(generator, render_fn=str, filter_fn=None, page_len=10, **pick_opts):
    ...

# from ..utils.resolver import pick
def pick(choices, default=None, str_choices=None, prompt=None, allow_mult=False, more_choices=False):
    """:param choices: Strings between which the user will make a choice"""
    ...

# from ..utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...

# from ..utils.resolver import resolve_multiple_existing_paths
def resolve_multiple_existing_paths(paths):
    """:param paths: A list of paths to items that need to be resolved"""
    ...

# from ..utils.resolver import is_analysis_id
def is_analysis_id(string):
    ...

# from ..utils import OrderedDefaultdict
class OrderedDefaultdict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxclient.py:11059
            with open(fname, 'w') as f:
                f.write("foo")

            with tarfile.open(tarballname, 'w:gz') as f:
                f.add(fname)

            dxfile = dxpy.upload_local_file(tarballname, name=tarballname, project=proj_id,
                                            media_type="application/gzip", wait_on_close=True)

# src/python/test/test_dxclient.py:1878
            with open(fname, 'w') as f:
                f.write(data)

            with tarfile.open(tarballname, 'w:gz') as f:
                f.add(fname)

            dxfile = dxpy.upload_local_file(tarballname, name=tarballname, project=proj_id,
                                            media_type="application/gzip", wait_on_close=True)

# src/python/test/test_dxpy_utils.py:89
        pending_tasks = set()
        complete_tasks = set()

        def task(i):
            pending_tasks.add(i)
            if i >= 1:
                self.assertNotIn(0, pending_tasks, "Task 0 was pending during task %d" % i)
            time.sleep(1)

# src/python/test/test_dxpy_utils.py:93
            pending_tasks.add(i)
            if i >= 1:
                self.assertNotIn(0, pending_tasks, "Task 0 was pending during task %d" % i)
            time.sleep(1)
            complete_tasks.add(i)
            pending_tasks.remove(i)

        def tasks():

# src/python/dxpy/app_builder.py:336
                output_sha1.update(b''.join(s.encode('utf-8') + b'\0' for s in fields))

                # add an entry in the tar file for the current directory, but
                # do not recurse!
                tar_fh.add(dirname, arcname=worker_resources_subpath + relative_dirname, recursive=False, filter=_fix_perm_filter)
                # Canonicalize the order of subdirectories; this is the order in
                # which they will be visited by os.walk
                subdirs.sort()

# src/python/dxpy/app_builder.py:399

                    # If we are to dereference, use the target fn
                    if deref_link:
                        true_filename = os.path.realpath(true_filename)
                    tar_fh.add(true_filename, arcname=worker_resources_subpath + relative_filename, filter=_fix_perm_filter)
                # end for filename in sorted(files)

            # end for dirname, subdirs, files in os.walk(resources_dir):
```

Write `checks()` and `cases()` for `ExecutableInputs.add`. Remember: setup in the thunk or at module level, never timed.