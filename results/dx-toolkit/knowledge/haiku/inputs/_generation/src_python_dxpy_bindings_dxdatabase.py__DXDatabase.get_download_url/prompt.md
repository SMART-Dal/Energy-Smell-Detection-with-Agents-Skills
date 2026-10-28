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
Function under test: `DXDatabase.get_download_url` in `src/python/dxpy/bindings/dxdatabase.py`
Import it as `from dxpy.bindings.dxdatabase import DXDatabase`; the method is called as `DXDatabase.get_download_url(instance, ...)`.

## The function
```python
    def get_download_url(self, filename=None, src_filename=None, project=None, **kwargs):
        """
        :param filename: desired filename of the local downloaded file
        :type filename: str
        :param project: ID of a project containing the file (the download URL
            will be associated with this project, and this may affect which
            billing account is billed for this download).
            If no project is specified, an attempt will be made to verify if the database is
            in the project from the DXDatabase handler (as specified by the user or
            the current project stored in dxpy.WORKSPACE_ID). Otherwise, no hint is supplied.
            This fall back behavior does not happen inside a job environment.
        :type project: str
        :returns: download URL and dict containing HTTP headers to be supplied
            with the request
        :rtype: tuple (str, dict)
        :raises: :exc:`~dxpy.exceptions.ResourceNotFound` if a project context was
            given and the database was not found in that project context.
        :raises: :exc:`~dxpy.exceptions.ResourceNotFound` if no project context was
            given and the database was not found in any projects.

        Obtains a URL that can be used to directly download files associated
        with the specified database.

        """

        args = {}

        if src_filename is not None:
            args["filename"] = src_filename

        # If project=None, we fall back to the project attached to this handler
        # (if any). If this is supplied, it's treated as a hint: if it's a
        # project in which this file exists, it's passed on to the
        # apiserver. Otherwise, NO hint is supplied. In principle supplying a
        # project in the handler that doesn't contain this file ought to be an
        # error, but it's this way for backwards compatibility. We don't know
        # who might be doing downloads and creating handlers without being
        # careful that the project encoded in the handler contains the file
        # being downloaded. They may now rely on such behavior.
        if project is None and 'DX_JOB_ID' not in os.environ:
            project_from_handler = self.get_proj_id()
            if project_from_handler and object_exists_in_project(self.get_id(), project_from_handler):
                project = project_from_handler

        if project is not None and project is not DXDatabase.NO_PROJECT_HINT:
            args["projectContext"] = project

        # Test hook to write 'project' argument passed to API call to a
        # local file
        if '_DX_DUMP_BILLED_PROJECT' in os.environ:
            with open(os.environ['_DX_DUMP_BILLED_PROJECT'], "w") as fd:
                if project is not None and project != DXDatabase.NO_PROJECT_HINT:
                    fd.write(project)

        with self._url_download_mutex:

            if self._download_url is None or self._download_url_expires < time.time():
                # The idea here is to cache a download URL for the entire file, that will
                # be good for a few minutes. This avoids each thread having to ask the
                # server for a URL, increasing server load.
                #
                # To avoid thread race conditions, this check/update procedure is protected
                # with a lock.

                # logging.debug("Download URL unset or expired, requesting a new one")
                if "timeout" not in kwargs:
                    kwargs["timeout"] = FILE_REQUEST_TIMEOUT
                do_debug("dxdatabase get_download_url - download_file args = {}".format(args))
                resp = dxpy.api.database_download_file(self._dxid, args, **kwargs)
                do_debug("dxdatabase get_download_url - download_file resp = {}".format(resp));
                self._download_url = resp["url"]
                self._download_url_headers = _validate_headers(resp.get("headers", {}))
                self._download_url_expires = 32503680000  # doesn't expire (year 3000)

            # Make a copy, ensuring each thread has its own mutable
            # version of the headers.  Note: python strings are
            # immutable, so we can safely give a reference to the
            # download url.
            retval_download_url = self._download_url
            retval_download_url_headers = copy.copy(self._download_url_headers)

        return retval_download_url, retval_download_url_headers
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class DXDatabase(DXDataObject):
    '''Remote database object handler.

    :param dxid: Object ID
    :type dxid: string
    :param project: Project ID
    :type project: string

    '''
    _class = "database"
    _describe = staticmethod(dxpy.api.file_describe)
    _http_threadpool_size = DXFILE_HTTP_THREADS
    _http_threadpool = dxpy.utils.get_futures_threadpool(max_workers=_http_threadpool_size)
    NO_PROJECT_HINT = 'NO_PROJECT_HINT'
    def __init__(self, dxid=None, project=None, read_buffer_size=DEFAULT_BUFFER_SIZE,
                 expected_file_size=None, file_is_mmapd=False):
        """
        :param dxid: Object ID
        :type dxid: string
        :param project: Project ID
        :type project: string
        :param read_buffer_size: size of read buffer in bytes
        :type read_buffer_size: int
        :param expected_file_size: size of data that will be written, if
            known
        :type expected_file_size: int
        :param file_is_mmapd: True if input file is mmap'd (if so, the
            write buffer size will be constrained to be a multiple of
            the allocation granularity)
        :type file_is_mmapd: bool
        """

        DXDataObject.__init__(self, dxid=dxid, project=project)

        self._read_buf = BytesIO()
        self._read_bufsize = read_buffer_size
        self._expected_file_size = expected_file_size
        self._file_is_mmapd = file_is_mmapd

        # These are cached once for all download threads. This saves calls to the apiserver.
        self._download_url, self._download_url_headers, self._download_url_expires = None, None, None

        # This lock protects accesses to the above three variables, ensuring that they would
        # be checked and changed atomically. This protects against thread race conditions.
        self._url_download_mutex = Lock()

        self._request_iterator, self._response_iterator = None, None
        self._http_threadpool_futures = set()
    def get_download_url(self, filename=None, src_filename=None, project=None, **kwargs):
        """
        :param filename: desired filename of the local downloaded file
        :type filename: str
        :param project: ID of a project containing the file (the download URL
            will be associated with this project, and this may affect which
            billing account is billed for this download).
            If no project is specified, an attempt will be made to verify if the database is
            in the project from the DXDatabase handler (as specified by the user or
            the current project stored in dxpy.WORKSPACE_ID). Otherwise, no hint is supplied.
            This fall back behavior does not happen inside a job environment.
        :type project: str
        :returns: download URL and dict containing HTTP headers to be supplied
            with the request
        :rtype: tuple (str, dict)
        :raises: :exc:`~dxpy.exceptions.ResourceNotFound` if a project context was
            given and the database was not found in that project context.
        :raises: :exc:`~dxpy.exceptions.ResourceNotFound` if no project context was
            given and the database was not found in any projects.

        Obtains a URL that can be used to directly download files associated
        with the specified database.

        """

        args = {}

        if src_filename is not None:
            args["filename"] = src_filename

        # If project=None, we fall back to the project attached to this handler
        # (if any). If this is supplied, it's treated as a hint: if it's a
        # project in which this file exists, it's passed on to the
        # apiserver. Otherwise, NO hint is supplied. In principle supplying a
        # project in the handler that doesn't contain this file ought to be an
        # error, but it's this way for backwards compatibility. We don't know
        # who might be doing downloads and creating handlers without being
        # careful that the project encoded in the handler contains the file
        # being downloaded. They may now rely on such behavior.
        if project is None and 'DX_JOB_ID' not in os.environ:
            project_from_handler = self.get_proj_id()
            if project_from_handler and object_exists_in_project(self.get_id(), project_from_handler):
                project = project_from_handler

        if project is not None and project is not DXDatabase.NO_PROJECT_HINT:
            args["projectContext"] = project

        # Test hook to write 'project' argument passed to API call to a
        # local file
        if '_DX_DUMP_BILLED_PROJECT' in os.environ:
            with open(os.environ['_DX_DUMP_BILLED_PROJECT'], "w") as fd:
                if project is not None and project != DXDatabase.NO_PROJECT_HINT:
                    fd.write(project)

        with self._url_download_mutex:

            if self._download_url is None or self._download_url_expires < time.time():
                # The idea here is to cache a download URL for the entire file, that will
                # be good for a few minutes. This avoids each thread having to ask the
                # server for a URL, increasing server load.
                #
                # To avoid thread race conditions, this check/update procedure is protected
                # with a lock.

                # logging.debug("Download URL unset or expired, requesting a new one")
                if "timeout" not in kwargs:
                    kwargs["timeout"] = FILE_REQUEST_TIMEOUT
                do_debug("dxdatabase get_download_url - download_file args = {}".format(args))
                resp = dxpy.api.database_download_file(self._dxid, args, **kwargs)
                do_debug("dxdatabase get_download_url - download_file resp = {}".format(resp));
                self._download_url = resp["url"]
                self._download_url_headers = _validate_headers(resp.get("headers", {}))
                self._download_url_expires = 32503680000  # doesn't expire (year 3000)

            # Make a copy, ensuring each thread has its own mutable
            # version of the headers.  Note: python strings are
            # immutable, so we can safely give a reference to the
            # download url.
            retval_download_url = self._download_url
            retval_download_url_headers = copy.copy(self._download_url_headers)

        return retval_download_url, retval_download_url_headers
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, copy, time
from io import BytesIO
from threading import Lock
from multiprocessing import cpu_count
import dxpy
from . import DXDataObject
from ..utils.resolver import object_exists_in_project
from .. import logger
from ..compat import basestring
```

## Definitions it uses from the same module
```python
FILE_REQUEST_TIMEOUT = 60

def _validate_headers(headers):
    for key, value in headers.items():
        if not isinstance(key, basestring):
            raise ValueError("Expected key %r of headers to be a string" % (key,))
        if not isinstance(value, basestring):
            raise ValueError("Expected value %r of headers (associated with key %r) to be a string"
                             % (value, key))
    return headers

def do_debug(msg):
    logger.debug(msg)
```

## Everything else its module defines (headers only)
```python
def _readable_part_size(num_bytes):
```

## Signatures of what its module imports from the repository
```python
# from ..utils.resolver import object_exists_in_project
def object_exists_in_project(obj_id, proj_id):
    """:param obj_id: object ID"""
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
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxfile_download.py:58
        dxfile = self._make_dxfile()
        with patch('dxpy.api.file_download', return_value=self._base_resp()) as mock_dl, \
                patch('dxpy.bindings.dxfile.warn') as mock_warn, \
                patch('dxpy.bindings.dxfile.object_exists_in_project', return_value=False):
            dxfile.get_download_url()
            mock_warn.assert_not_called()

    def test_flagged_malicious_emits_warning(self):

# src/python/test/test_dxfile_download.py:67
        dxfile = self._make_dxfile()
        with patch('dxpy.api.file_download', return_value=self._base_resp(security_status='FLAGGED_MALICIOUS')) as mock_dl, \
                patch('dxpy.bindings.dxfile.warn') as mock_warn, \
                patch('dxpy.bindings.dxfile.object_exists_in_project', return_value=False):
            dxfile.get_download_url()
            mock_warn.assert_called_once()
            warned_message = mock_warn.call_args[0][0]
            self.assertEqual(self.WARNING_MESSAGE, warned_message)

# src/python/test/test_dxpy.py:772
        dxfile = dxpy.upload_string(self.foo_str, wait_on_close=True)
        opts = {"preauthenticated": True, "filename": "foo"}
        # File download token/URL is cached
        dxfile = dxpy.open_dxfile(dxfile.get_id())
        url1 = dxfile.get_download_url(**opts)
        url2 = dxfile.get_download_url(**opts)
        self.assertEqual(url1, url2)
        # Cache is invalidated when the client knows the token has expired

# src/python/test/test_dxpy.py:773
        opts = {"preauthenticated": True, "filename": "foo"}
        # File download token/URL is cached
        dxfile = dxpy.open_dxfile(dxfile.get_id())
        url1 = dxfile.get_download_url(**opts)
        url2 = dxfile.get_download_url(**opts)
        self.assertEqual(url1, url2)
        # Cache is invalidated when the client knows the token has expired
        # (subject to clock skew allowance of 30s)

# src/python/dxpy/bindings/dxdatabase_functions.py:220
        print_progress(0, None)

    def get_chunk(part_id_to_get, start, end):
        do_debug("dxdatabase_functions.py get_chunk - start {}, end {}, part id {}".format(start, end, part_id_to_get))
        url, headers = dxdatabase.get_download_url(src_filename=src_filename, project=project, **kwargs)
        # No sub ranges for database file downloads
        sub_range = False
        data = dxpy._dxhttp_read_range(url, headers, start, end, FILE_REQUEST_TIMEOUT, sub_range)

# src/python/dxpy/bindings/dxfile.py:835
                    cur_chunk_size = min(cur_chunk_size * ramp, limit_chunk_size)
                i += 1

        for chunk_start_pos, chunk_end_pos in chunk_ranges(start_pos, end_pos):
            url, headers = self.get_download_url(project=project, **kwargs)
            # It is possible for chunk_end_pos to be outside of the range of the file
            yield dxpy._dxhttp_read_range, [url, headers, chunk_start_pos, min(chunk_end_pos, self._file_length - 1),
                                            FILE_REQUEST_TIMEOUT], {}
```

Write `checks()` and `cases()` for `DXDatabase.get_download_url`. Remember: setup in the thunk or at module level, never timed.