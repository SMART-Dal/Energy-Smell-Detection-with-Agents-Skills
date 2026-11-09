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
Function under test: `DXJob.wait_on_done` in `src/python/dxpy/bindings/dxjob.py`
Import it as `from dxpy.bindings.dxjob import DXJob`; the method is called as `DXJob.wait_on_done(instance, ...)`.

## The function
```python
    def wait_on_done(self, interval=2, timeout=3600*24*7, **kwargs):
        '''
        :param interval: Number of seconds between queries to the job's state
        :type interval: integer
        :param timeout: Maximum amount of time to wait, in seconds, until the job is done running
        :type timeout: integer
        :raises: :exc:`~dxpy.exceptions.DXError` if the timeout is reached before the job has finished running, or :exc:`dxpy.exceptions.DXJobFailureError` if the job fails

        Waits until the job has finished running.
        '''

        elapsed = 0
        while True:
            state = self._get_state(**kwargs)
            if state == "done":
                break
            if state == "failed":
                desc = self.describe(**kwargs)
                err_msg = "Job has failed because of {failureReason}: {failureMessage}".format(**desc)
                if desc.get("failureFrom") != None and desc["failureFrom"]["id"] != desc["id"]:
                    err_msg += " (failure from {id})".format(id=desc['failureFrom']['id'])
                raise DXJobFailureError(err_msg)
            if state == "terminated":
                raise DXJobFailureError("Job was terminated.")

            if elapsed >= timeout or elapsed < 0:
                raise DXJobFailureError("Reached timeout while waiting for the job to finish")

            time.sleep(interval)
            elapsed += interval
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class DXJob(DXObject):
    '''
    Remote job object handler.
    '''
    _class = "job"
    def __init__(self, dxid=None):
        self._test_harness_result = None
        DXObject.__init__(self, dxid=dxid)
        self.set_id(dxid)
    def new(self, fn_input, fn_name, name=None, tags=None, properties=None, details=None, instance_type=None,
            depends_on=None, cluster_spec=None, fpga_driver=None, system_requirements=None,
            system_requirements_by_executable=None, nvidia_driver=None, **kwargs):
        '''
        :param fn_input: Function input
        :type fn_input: dict
        :param fn_name: Name of the function to be called
        :type fn_name: string
        :param name: Name for the new job (default is "<parent job name>:<fn_name>")
        :type name: string
        :param tags: Tags to associate with the job
        :type tags: list of strings
        :param properties: Properties to associate with the job
        :type properties: dict with string values
        :param details: Details to set for the job
        :type details: dict or list
        :param instance_type: Instance type on which the job will be run, or a dict mapping function names to instance type requests
        :type instance_type: string or dict
        :param depends_on: List of data objects or jobs to wait that need to enter the "closed" or "done" states, respectively, before the new job will be run; each element in the list can either be a dxpy handler or a string ID
        :type depends_on: list
        :param cluster_spec: a dict mapping function names to cluster spec requests
        :type cluster_spec: dict
        :param fpga_driver: a dict mapping function names to fpga driver requests
        :type fpga_driver: dict
        :param system_requirements: System requirement single mapping
        :type system_requirements: dict
        :param system_requirements_by_executable: System requirement by executable double mapping
        :type system_requirements_by_executable: dict
        :param nvidia_driver: a dict mapping function names to nvidia driver requests
        :type nvidia_driver: dict

        Creates and enqueues a new job that will execute a particular
        function (from the same app or applet as the one the current job
        is running).

        .. note:: This method is intended for calls made from within
           already-executing jobs or apps. If it is called from outside
           of an Execution Environment, an exception will be thrown. To
           create new jobs from outside the Execution Environment, use
           :func:`dxpy.bindings.dxapplet.DXApplet.run` or
           :func:`dxpy.bindings.dxapp.DXApp.run`.

        '''
        ...
    def set_id(self, dxid):
        '''
        :param dxid: New job ID to be associated with the handler (localjob IDs also accepted for local runs)
        :type dxid: string

        Discards the currently stored ID and associates the handler with *dxid*
        '''
        ...
    def describe(self, fields=None, defaultFields=None, io=None, **kwargs):
        """
        :param fields: dict where the keys are field names that should
            be returned, and values should be set to True (by default,
            all fields are returned)
        :type fields: dict
        :param defaultFields: include default fields when fields is supplied
        :type defaultFields: bool
        :param io: Include input and output fields in description;
            cannot be provided with *fields*; default is True if
            *fields* is not provided (deprecated)
        :type io: bool
        :returns: Description of the job
        :rtype: dict

        Returns a hash with key-value pairs containing information about
        the job, including its state and (optionally) its inputs and
        outputs, as described in the API documentation for the
        `/job-xxxx/describe
        <https://documentation.dnanexus.com/developer/api/running-analyses/applets-and-entry-points#api-method-job-xxxx-describe>`_
        method.

        """
        ...
    def add_tags(self, tags, **kwargs):
        """
        :param tags: Tags to add to the job
        :type tags: list of strings

        Adds each of the specified tags to the job. Takes no
        action for tags that are already listed for the job.

        """
        ...
    def remove_tags(self, tags, **kwargs):
        """
        :param tags: Tags to remove from the job
        :type tags: list of strings

        Removes each of the specified tags from the job. Takes
        no action for tags that the job does not currently have.

        """
        ...
    def update(self, allow_ssh, **kwargs):
        """
        :param allow_ssh: Allowable IP ranges to set for SSH access to the job
        :type allow_ssh: list of strings

        Updates a job's allowSSH field, overwrites existing values

        """
        ...
    def set_properties(self, properties, **kwargs):
        """
        :param properties: Property names and values given as key-value pairs of strings
        :type properties: dict

        Given key-value pairs in *properties* for property names and
        values, the properties are set on the job for the given
        property names. Any property with a value of :const:`None`
        indicates the property will be deleted.

        .. note:: Any existing properties not mentioned in *properties*
           are not modified by this method.

        """
        ...
    def wait_on_done(self, interval=2, timeout=3600*24*7, **kwargs):
        '''
        :param interval: Number of seconds between queries to the job's state
        :type interval: integer
        :param timeout: Maximum amount of time to wait, in seconds, until the job is done running
        :type timeout: integer
        :raises: :exc:`~dxpy.exceptions.DXError` if the timeout is reached before the job has finished running, or :exc:`dxpy.exceptions.DXJobFailureError` if the job fails

        Waits until the job has finished running.
        '''

        elapsed = 0
        while True:
            state = self._get_state(**kwargs)
            if state == "done":
                break
            if state == "failed":
                desc = self.describe(**kwargs)
                err_msg = "Job has failed because of {failureReason}: {failureMessage}".format(**desc)
                if desc.get("failureFrom") != None and desc["failureFrom"]["id"] != desc["id"]:
                    err_msg += " (failure from {id})".format(id=desc['failureFrom']['id'])
                raise DXJobFailureError(err_msg)
            if state == "terminated":
                raise DXJobFailureError("Job was terminated.")

            if elapsed >= timeout or elapsed < 0:
                raise DXJobFailureError("Reached timeout while waiting for the job to finish")

            time.sleep(interval)
            elapsed += interval
    def terminate(self, **kwargs):
        '''
        Terminates the associated job.
        '''
        ...
    def get_output_ref(self, field, index=None, metadata=None):
        '''
        :param field: Output field name of this job
        :type field: string
        :param index: If the referenced field is an array, optionally specify an index (starting from 0) to indicate a particular member of the array
        :type index: int
        :param metadata: If the referenced field is of a data object class, a string indicating the metadata that should be read, e.g. "name", "properties.propkey", "details.refgenome"
        :type metadata: string

        Returns a dict containing a valid job-based object reference
        to refer to an output of this job.  This can be used directly
        in place of a DNAnexus link when used as a job output value.
        For example, after creating a subjob, the following app
        snippet uses a reference to the new job's output as part of
        its own output::

            mysubjob = dxpy.new_dxjob({}, "my_function")
            return { "myfileoutput": mysubjob.get_output_ref("output_field_name"),
                     "myotherfileoutput": mysubjob.get_output_ref("output_array",
                                                                  index=1),
                     "filename": mysubjob.get_output_ref("output_field_name",
                                                         metadata="name") }
        '''
        ...
    def _get_state(self, **kwargs):
        '''
        :returns: State of the remote object
        :rtype: string

        Queries the API server for the job's state.

        Note that this function is shorthand for:

            dxjob.describe(io=False, **kwargs)["state"]

        '''
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, time
import dxpy
from . import DXObject, DXDataObject, DXJobFailureError, verify_string_dxid
from ..exceptions import DXError
from ..system_requirements import SystemRequirementsDict
from ..utils.local_exec_utils import queue_entry_point
from ..compat import basestring
```

## Everything else its module defines (headers only)
```python
def new_dxjob(fn_input, fn_name, name=None, tags=None, properties=None, details=None, instance_type=None,
              depends_on=None, cluster_spec=None, fpga_driver=None, system_requirements=None,
              system_requirements_by_executable=None, nvidia_driver=None, **kwargs):
```

## Signatures of what its module imports from the repository
```python
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

# from . import DXDataObject
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

# from . import verify_string_dxid
def verify_string_dxid(dxid, expected_classes):
    """:param dxid: Value to verify as a DNAnexus ID of class *expected_class*"""
    ...

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

# from ..utils.local_exec_utils import queue_entry_point
def queue_entry_point(function, input_hash, depends_on=[], name=None):
    """:param function: function to run"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/templating/templates/python/basic/test/test.py:55
        Tests the app with a basic input.
        """
        job = dxpy.DXApplet(self.applet_id).run(self.base_input)
        print("Waiting for %s to complete" % (job.get_id(),))
        job.wait_on_done()
        print( json.dumps(job.describe()["output"]) )

if __name__ == '__main__':

# src/python/dxpy/templating/templates/python/parallelized/test/test.py:55
        Tests the app with a basic input.
        """
        job = dxpy.DXApplet(self.applet_id).run(self.base_input)
        print("Waiting for {} to complete".format(job.get_id()))
        job.wait_on_done()
        print(json.dumps(job.describe()["output"]))

if __name__ == '__main__':

# src/python/dxpy/templating/templates/python/scatter-process-gather/test/test.py:55
        Tests the app with a basic input.
        """
        job = dxpy.DXApplet(self.applet_id).run(self.base_input)
        print("Waiting for %s to complete" % (job.get_id(),))
        job.wait_on_done()
        print(json.dumps(job.describe()["output"]))

if __name__ == '__main__':

# src/python/test/test_dx_bash_helpers.py:253
            cmd_args = ["dx", "run", "--yes", "--brief", applet_id]
            cmd_args.extend(applet_args)
            job_id = run(cmd_args, env=env).strip()

            dxpy.DXJob(job_id).wait_on_done()

            # Assertions -- making sure the script worked
            # Assertions to make about the job's output after it is done running:

# src/python/test/test_dx_bash_helpers.py:432
            applet_args = ["-icreate_seq3=true"]
            cmd_args = ["dx", "run", "--yes", "--brief", applet_id]
            cmd_args.extend(applet_args)
            job_id = run(cmd_args, env=env).strip()
            dxpy.DXJob(job_id).wait_on_done()

            # Run the applet --- this will not create the seq3 output file.
            # This should cause an exception from the job manager.

# src/python/test/test_dxasset.py:249
        app_dir = self.write_app_directory("asset_depends", json.dumps(app_spec))
        asset_applet_id = json.loads(run("dx build --json {app_dir}".format(app_dir=app_dir)))["id"]
        asset_applet = dxpy.DXApplet(asset_applet_id)
        applet_job = asset_applet.run({})
        applet_job.wait_on_done()
        self.assertEqual(applet_job.describe()['state'], 'done')

    @unittest.skipUnless(testutil.TEST_RUN_JOBS, 'skipping test that would run jobs')
```

Write `checks()` and `cases()` for `DXJob.wait_on_done`. Remember: setup in the thunk or at module level, never timed.