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
Function under test: `upload_resources` in `src/python/dxpy/app_builder.py`
Import it as `from dxpy.app_builder import upload_resources`.

## The function
```python
def upload_resources(src_dir, project=None, folder='/', ensure_upload=False, force_symlinks=False, brief=False, resources_dir=None, worker_resources_subpath=""):
    """
    :param ensure_upload: If True, will bypass checksum of resources directory
                          and upload resources bundle unconditionally;
                          will NOT be able to reuse this bundle in future builds.
                          Else if False, will compute checksum and upload bundle
                          if checksum is different from a previously uploaded
                          bundle's checksum.
    :type ensure_upload: boolean
    :param force_symlinks: If true, will bypass the attempt to dereference any
                           non-local symlinks and will unconditionally include
                           the link as-is.  Note that this will almost certainly
                           result in a broken link within the resource directory
                           unless you really know what you're doing.
    :type force_symlinks: boolean
    :param resources_dir: Directory with resources to be archived and uploaded. If not given, uses `resources/`.
    :type resources_dir: str
    :param worker_resources_subpath: Path that will be prepended to the default directory where files are extracted on the worker.
                                     Default is empty string, therefore files would be extracted directly to the root folder.
                                     Example: If "home/dnanexus" is given, files will be extracted into /home/dnanexus.
    :type worker_resources_subpath: str
    :returns: A list (possibly empty) of references to the generated archive(s)
    :rtype: list

    If resources_dir exists, archives and uploads the contents of the resources_dir
    (usually ``resources/``) subdirectory of *src_dir* to a new remote file
    object, and returns a list describing a single bundled dependency in
    the form expected by the ``bundledDepends`` field of a run
    specification. Returns an empty list, if no archive was created.
    """
    if not resources_dir:
        resources_dir = os.path.join(src_dir, "resources")

    applet_spec = _get_applet_spec(src_dir)

    if project is None:
        dest_project = applet_spec['project']
    else:
        dest_project = project
        applet_spec['project'] = project

    if os.path.exists(resources_dir) and len(os.listdir(resources_dir)) > 0:
        target_folder = applet_spec['folder'] if 'folder' in applet_spec else folder

        # While creating the resource bundle, optimistically look for a
        # resource bundle with the same contents, and reuse it if possible.
        # The resource bundle carries a property 'resource_bundle_checksum'
        # that indicates the checksum; the way in which the checksum is
        # computed is given below.   If the checksum matches  (and
        # ensure_upload is False), then we will use the existing file,
        # otherwise, we will compress and upload the tarball.


        # The input to the SHA1 contains entries of the form (whitespace
        # only included here for readability):
        #
        # / \0 MODE \0 MTIME \0
        # /foo \0 MODE \0 MTIME \0
        # ...
        #
        # where there is one entry for each directory or file (order is
        # specified below), followed by a numeric representation of the
        # mode, and the mtime in milliseconds since the epoch.
        #
        # Note when looking at a link, if the link is to be dereferenced,
        # the mtime and mode used are that of the target (using os.stat())
        # If the link is to be kept as a link, the mtime and mode are those
        # of the link itself (using os.lstat())

        with tempfile.NamedTemporaryFile(suffix=".tar") as tar_tmp_fh:

            output_sha1 = hashlib.sha1()
            tar_fh = tarfile.open(fileobj=tar_tmp_fh, mode='w')

            for dirname, subdirs, files in os.walk(resources_dir):
                if not dirname.startswith(resources_dir):
                    raise AssertionError('Expected %r to start with root directory %r' % (dirname, resources_dir))

                # Add an entry for the directory itself
                relative_dirname = dirname[len(resources_dir):]
                dir_stat = os.lstat(dirname)
                if not relative_dirname.startswith('/'):
                    relative_dirname = '/' + relative_dirname

                fields = [relative_dirname, str(_fix_perms(dir_stat.st_mode)), str(int(dir_stat.st_mtime * 1000))]
                output_sha1.update(b''.join(s.encode('utf-8') + b'\0' for s in fields))

                # add an entry in the tar file for the current directory, but
                # do not recurse!
                tar_fh.add(dirname, arcname=worker_resources_subpath + relative_dirname, recursive=False, filter=_fix_perm_filter)
                # Canonicalize the order of subdirectories; this is the order in
                # which they will be visited by os.walk
                subdirs.sort()

                # check the subdirectories for symlinks.  We should throw an error
                # if there are any links that point outside of the directory (unless
                # --force-symlinks is given).  If a link is pointing internal to
                # the directory (or --force-symlinks is given), we should add it
                # as a file.
                for subdir_name in subdirs:
                    dir_path = os.path.join(dirname, subdir_name)

                    # If we do have a symlink,
                    if os.path.islink(dir_path):
                        # Let's get the pointed-to path to ensure that it is
                        # still in the directory
                        link_target = os.readlink(dir_path)

                        # If this is a local link, add it to the list of files (case 1)
                        # else raise an error
                        if force_symlinks or is_link_local(link_target):
                            files.append(subdir_name)
                        else:
                            raise AppBuilderException("Cannot include symlinks to directories outside of the resource directory.  '%s' points to directory '%s'" % (dir_path, os.path.realpath(dir_path)))


                # Canonicalize the order of files so that we compute the
                # checksum in a consistent order
                for filename in sorted(files):
                    deref_link = False

                    relative_filename = os.path.join(relative_dirname, filename)
                    true_filename = os.path.join(dirname, filename)

                    file_stat = os.lstat(true_filename)
                    # check for a link here, please!
                    if os.path.islink(true_filename):

                        # Get the pointed-to path
                        link_target = os.readlink(true_filename)

                        if not (force_symlinks or is_link_local(link_target)):
                            # if we are pointing outside of the directory, then:
                            # try to get the true stat of the file and make sure
                            # to dereference the link!
                            try:
                                file_stat = os.stat(os.path.join(dirname, link_target))
                                deref_link = True
                            except OSError:
                                # uh-oh! looks like we have a broken link!
                                # since this is guaranteed to cause problems (and
                                # we know we're not forcing symlinks here), we
                                # should throw an error
                                raise AppBuilderException("Broken symlink: Link '%s' points to '%s', which does not exist" % (true_filename, os.path.realpath(true_filename)) )


                    fields = [relative_filename, str(_fix_perms(file_stat.st_mode)), str(int(file_stat.st_mtime * 1000))]
                    output_sha1.update(b''.join(s.encode('utf-8') + b'\0' for s in fields))

                    # If we are to dereference, use the target fn
                    if deref_link:
                        true_filename = os.path.realpath(true_filename)
                    tar_fh.add(true_filename, arcname=worker_resources_subpath + relative_filename, filter=_fix_perm_filter)
                # end for filename in sorted(files)

            # end for dirname, subdirs, files in os.walk(resources_dir):

            # at this point, the tar is complete, so close the tar_fh
            tar_fh.close()

            # Optimistically look for a resource bundle with the same
            # contents, and reuse it if possible. The resource bundle
            # carries a property 'resource_bundle_checksum' that indicates
            # the checksum; the way in which the checksum is computed is
            # given in the documentation of _directory_checksum.

            if ensure_upload:
                properties_dict = {}
                existing_resources = False
            else:
                directory_checksum = output_sha1.hexdigest()
                properties_dict = dict(resource_bundle_checksum=directory_checksum)
                existing_resources = dxpy.find_one_data_object(
                    project=dest_project,
                    folder=target_folder,
                    properties=dict(resource_bundle_checksum=directory_checksum),
                    visibility='either',
                    zero_ok=True,
                    state='closed',
                    return_handler=True
                )

            if existing_resources:
                if not brief:
                    logger.info("Found existing resource bundle that matches local resources directory: " +
                                existing_resources.get_id())

                dx_resource_archive = existing_resources
            else:

                logger.debug("Uploading in " + src_dir)
                # We need to compress the tar that we've created


                targz_fh = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)

                # compress the file by reading the tar file and passing
                # it though a GzipFile object, writing the given
                # block size (by default 8192 bytes) at a time
                targz_gzf = gzip.GzipFile(fileobj=targz_fh, mode='wb')
    # ... (truncated)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, json, subprocess, tempfile, multiprocessing
import datetime
import gzip
import hashlib
import io
import tarfile
import stat
import dxpy
import dxpy.executable_builder
from . import logger
from .utils import merge
from .utils.printing import fill
from .cli import INTERACTIVE_CLI
```

## Definitions it uses from the same module
```python
class AppBuilderException(Exception):
    """
    This exception is raised by the methods in this module when app or applet
    building fails.
    """
    pass

def _get_applet_spec(src_dir):
    applet_spec_file = os.path.join(src_dir, "dxapp.json")
    with open(applet_spec_file) as fh:
        applet_spec = json.load(fh)

    _validate_applet_spec(applet_spec)
    if 'project' not in applet_spec:
        applet_spec['project'] = dxpy.WORKSPACE_ID
    return applet_spec

def is_link_local(link_target):
    """
    :param link_target: The target of a symbolic link, as given by os.readlink()
    :type link_target: string
    :returns: A boolean indicating the link is local to the current directory.
              This is defined to mean that os.path.isabs(link_target) == False
              and the link NEVER references the parent directory, so
              "./foo/../../curdir/foo" would return False.
    :rtype: boolean
    """
    is_local=(not os.path.isabs(link_target))

    if is_local:
        # make sure that the path NEVER extends outside the resources directory!
        d,l = os.path.split(link_target)
        link_parts = []
        while l:
            link_parts.append(l)
            d,l = os.path.split(d)
        curr_path = os.sep

        for p in reversed(link_parts):
            is_local = (is_local and not (curr_path == os.sep and p == os.pardir) )
            curr_path = os.path.abspath(os.path.join(curr_path, p))

    return is_local

def _fix_perms(perm_obj):
    """
    :param perm_obj: A permissions object, as given by os.stat()
    :type perm_obj: integer
    :returns: A permissions object that is the result of "chmod a+rX" on the
              given permission object.  This is defined to be the permission object
              bitwise or-ed with all stat.S_IR*, and if the stat.S_IXUSR bit is
              set, then the permission object should also be returned bitwise or-ed
              with stat.S_IX* (stat.S_IXUSR not included because it would be redundant).
    :rtype: integer
    """
    ret_perm = perm_obj | stat.S_IROTH | stat.S_IRGRP | stat.S_IRUSR
    if ret_perm & stat.S_IXUSR:
        ret_perm = ret_perm | stat.S_IXGRP | stat.S_IXOTH

    return ret_perm

def _fix_perm_filter(tar_obj):
    """
    :param tar_obj: A TarInfo object to be added to a tar file
    :tpye tar_obj: tarfile.TarInfo
    :returns: A TarInfo object with permissions changed (a+rX)
    :rtype: tarfile.TarInfo
    """
    tar_obj.mode = _fix_perms(tar_obj.mode)
    return tar_obj
```

## Everything else its module defines (headers only)
```python
def _validate_system_requirements(system_requirements):
def _validate_applet_spec(applet_spec):
def _validate_app_spec(app_spec):
    # Validate systemRequirements for instanceTypeSelector constraints in runSpec
def _get_app_spec(src_dir):
def build(src_dir, parallel_build=True):
def get_destination_project(src_dir, project=None):
def upload_applet(src_dir, uploaded_resources, check_name_collisions=True, overwrite=False, archive=False,
                  project=None, override_folder=None, override_name=None,
                  dry_run=False, brief=False, **kwargs):
def _create_or_update_version(app_name, version, app_spec, try_update=True):
def _update_version(app_name, version, app_spec, try_update=True):
def create_app_multi_region(regional_options, app_name, src_dir, publish=False, set_default=False, billTo=None,
                            try_versions=None, try_update=True, confirm=True, inherited_metadata={}, brief=False):
def create_app(applet_id, applet_name, src_dir, publish=False, set_default=False, billTo=None, try_versions=None,
               try_update=True, confirm=True, regional_options=None):
def _create_app(applet_or_regional_options, app_name, src_dir, publish=False, set_default=False, billTo=None,
                try_versions=None, try_update=True, confirm=True, inherited_metadata={}, brief=False):
def get_enabled_regions(app_spec, from_command_line):
```

## Signatures of what its module imports from the repository
```python
# from .utils import merge
def merge(d, u):
    """Recursively updates a dictionary."""
    ...

# from .utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `upload_resources`. Remember: setup in the thunk or at module level, never timed.