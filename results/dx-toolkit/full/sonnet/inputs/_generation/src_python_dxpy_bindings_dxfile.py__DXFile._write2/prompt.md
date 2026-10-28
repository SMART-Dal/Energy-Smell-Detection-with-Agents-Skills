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
Function under test: `DXFile._write2` in `src/python/dxpy/bindings/dxfile.py`
Import it as `from dxpy.bindings.dxfile import DXFile`; the method is called as `DXFile._write2(instance, ...)`.

## The function
```python
    def _write2(self, data, multithread=True, **kwargs):
        '''
        :param data: Data to be written
        :type data: str or mmap object
        :param multithread: If True, sends multiple write requests asynchronously
        :type multithread: boolean

        Writes the data *data* to the file.

        .. note::

            Writing to remote files is append-only. Using :meth:`seek`
            does not affect where the next :meth:`write` will occur.

        '''
        assert(isinstance(data, bytes))

        self._ensure_write_bufsize(**kwargs)

        def write_request(data_for_write_req):
            if multithread:
                self._async_upload_part_request(data_for_write_req, index=self._cur_part, **kwargs)
            else:
                self.upload_part(data_for_write_req, self._cur_part, **kwargs)
            self._cur_part += 1

        if self._write_buf.tell() == 0 and self._write_bufsize == len(data):
            # In the special case of a write that is the same size as
            # our write buffer size, and no unflushed data in the
            # buffer, just directly dispatch the write and bypass the
            # write buffer.
            #
            # This saves a buffer copy, which is especially helpful if
            # 'data' is actually mmap'd from a file.
            #
            # TODO: an additional optimization could be made to allow
            # the last request from an mmap'd upload to take this path
            # too (in general it won't because it's not of length
            # _write_bufsize). This is probably inconsequential though.
            write_request(data)
            return

        remaining_space = self._write_bufsize - self._write_buf.tell()

        if len(data) <= remaining_space:
            self._write_buf.write(data)
        else:
            self._write_buf.write(data[:remaining_space])

            temp_data = self._write_buf.getvalue()
            self._write_buf = BytesIO()
            write_request(temp_data)

            # TODO: check if repeat string splitting is bad for
            # performance when len(data) >> _write_bufsize
            self.write(data[remaining_space:], **kwargs)
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class DXFile(DXDataObject):
    '''Remote file object handler.

    :param dxid: Object ID
    :type dxid: string
    :param project: Project ID
    :type project: string
    :param mode: One of "r", "w", or "a" for read, write, and append modes, respectively.
                 Use "b" for binary mode. For example, "rb" means open a file for reading
                 in binary mode.
    :type mode: string

    .. note:: The attribute values below are current as of the last time
              :meth:`~dxpy.bindings.DXDataObject.describe` was run.
              (Access to any of the below attributes causes
              :meth:`~dxpy.bindings.DXDataObject.describe` to be called
              if it has never been called before.)

    .. py:attribute:: media

       String containing the Internet Media Type (also known as MIME type
       or Content-type) of the file.

    .. automethod:: _new

    '''
    _class = "file"
    _describe = staticmethod(dxpy.api.file_describe)
    _add_types = staticmethod(dxpy.api.file_add_types)
    _remove_types = staticmethod(dxpy.api.file_remove_types)
    _get_details = staticmethod(dxpy.api.file_get_details)
    _set_details = staticmethod(dxpy.api.file_set_details)
    _set_visibility = staticmethod(dxpy.api.file_set_visibility)
    _rename = staticmethod(dxpy.api.file_rename)
    _set_properties = staticmethod(dxpy.api.file_set_properties)
    _add_tags = staticmethod(dxpy.api.file_add_tags)
    _remove_tags = staticmethod(dxpy.api.file_remove_tags)
    _close = staticmethod(dxpy.api.file_close)
    _list_projects = staticmethod(dxpy.api.file_list_projects)
    _http_threadpool_size = DXFILE_HTTP_THREADS
    _http_threadpool = dxpy.utils.get_futures_threadpool(max_workers=_http_threadpool_size)
    NO_PROJECT_HINT = 'NO_PROJECT_HINT'
    @classmethod
    def set_http_threadpool_size(cls, num_threads):
        '''

        .. deprecated:: 0.191.0

        '''
        ...
    def __init__(self, dxid=None, project=None, mode=None, read_buffer_size=DEFAULT_BUFFER_SIZE,
                 write_buffer_size=DEFAULT_BUFFER_SIZE, expected_file_size=None, file_is_mmapd=False):
        """
        :param dxid: Object ID
        :type dxid: string
        :param project: Project ID
        :type project: string
        :param mode: One of "r", "w", or "a" for read, write, and append
            modes, respectively. Add "b" for binary mode.
        :type mode: string
        :param read_buffer_size: size of read buffer in bytes
        :type read_buffer_size: int
        :param write_buffer_size: hint for size of write buffer in
            bytes. A lower or higher value may be used depending on
            region-specific parameters and on the expected file size.
        :type write_buffer_size: int
        :param expected_file_size: size of data that will be written, if
            known
        :type expected_file_size: int
        :param file_is_mmapd: True if input file is mmap'd (if so, the
            write buffer size will be constrained to be a multiple of
            the allocation granularity)
        :type file_is_mmapd: bool
        """
        DXDataObject.__init__(self, dxid=dxid, project=project)

        # By default, a file is created in text mode. This makes a difference
        # in python 3.
        self._binary_mode = False
        if mode is None:
            self._close_on_exit = True
        else:
            if 'b' in mode:
                self._binary_mode = True
                mode = mode.replace("b", "")
            if mode not in ['r', 'w', 'a']:
                raise ValueError("mode must be one of 'r', 'w', or 'a'. Character 'b' may be used in combination (e.g. 'wb').")
            self._close_on_exit = (mode == 'w')
        self._read_buf = BytesIO()
        self._write_buf = BytesIO()

        self._read_bufsize = read_buffer_size

        # Computed lazily later since this depends on the project, and
        # we want to allow the project to be set as late as possible.
        # Call _ensure_write_bufsize to ensure that this is set before
        # trying to read it.
        self._write_bufsize = None

        self._write_buffer_size_hint = write_buffer_size
        self._expected_file_size = expected_file_size
        self._file_is_mmapd = file_is_mmapd

        # These are cached once for all download threads. This saves calls to the apiserver.
        self._download_url, self._download_url_headers, self._download_url_expires = None, None, None

        # This lock protects accesses to the above three variables, ensuring that they would
        # be checked and changed atomically. This protects against thread race conditions.
        self._url_download_mutex = Lock()

        self._request_iterator, self._response_iterator = None, None
        self._http_threadpool_futures = set()

        # Initialize state
        self._pos = 0
        self._file_length = None
        self._cur_part = 1
        self._num_uploaded_parts = 0
        # Cache for object existence in project
        self._exists_in_proj = None  
    def _new(self, dx_hash, media_type=None, **kwargs):
        """
        :param dx_hash: Standard hash populated in :func:`dxpy.bindings.DXDataObject.new()` containing attributes common to all data object classes.
        :type dx_hash: dict
        :param media_type: Internet Media Type
        :type media_type: string

        Creates a new remote file with media type *media_type*, if given.

        """
        ...
    def __enter__(self):
        ...
    def __exit__(self, type, value, traceback):
        ...
    def __del__(self):
        '''
        Exceptions raised here in the destructor are IGNORED by Python! We will try and flush data
        here just as a safety measure, but you should not rely on this to flush your data! We will
        be really grumpy and complain if we detect unflushed data here.

        Use a context manager or flush the object explicitly to avoid this.

        In addition, when this is triggered by interpreter shutdown, the thread pool is not
        available, and we will wait for the request queue forever. In this case, we must revert to
        synchronous, in-thread flushing. We don't know how to detect this condition, so we'll use
        that for all destructor events.

        Neither this nor context managers are compatible with kwargs pass-through (so e.g. no
        custom auth).
        '''
        ...
    def __iter__(self):
        ...
    next = next
    __next__ = next
    def set_ids(self, dxid, project=None):
        '''
        :param dxid: Object ID
        :type dxid: string
        :param project: Project ID
        :type project: string

        Discards the currently stored ID and associates the handler with
        *dxid*. As a side effect, it also flushes the buffer for the
        previous file object if the buffer is nonempty.
        '''
        ...
    def seek(self, offset, from_what=os.SEEK_SET):
        '''
        :param offset: Position in the file to seek to
        :type offset: integer

        Seeks to *offset* bytes from the beginning of the file.  This is a no-op if the file is open for writing.

        The position is computed from adding *offset* to a reference point; the reference point is selected by the
        *from_what* argument. A *from_what* value of 0 measures from the beginning of the file, 1 uses the current file
        position, and 2 uses the end of the file as the reference point. *from_what* can be omitted and defaults to 0,
        using the beginning of the file as the reference point.
        '''
        ...
    def tell(self):
        '''
        Returns the current position of the file read cursor.

        Warning: Because of buffering semantics, this value will **not** be accurate when using the line iterator form
        (`for line in file`).
        '''
        ...
    def flush(self, multithread=True, **kwargs):
        '''
        Flushes the internal write buffer.
        '''
        ...
    def _async_upload_part_request(self, *args, **kwargs):
        ...
    def _ensure_write_bufsize(self, **kwargs):
        ...
    def _write2(self, data, multithread=True, **kwargs):
        '''
        :param data: Data to be written
        :type data: str or mmap object
        :param multithread: If True, sends multiple write requests asynchronously
        :type multithread: boolean

        Writes the data *data* to the file.

        .. note::

            Writing to remote files is append-only. Using :meth:`seek`
            does not affect where the next :meth:`write` will occur.

        '''
        assert(isinstance(data, bytes))

        self._ensure_write_bufsize(**kwargs)

        def write_request(data_for_write_req):
            if multithread:
                self._async_upload_part_request(data_for_write_req, index=self._cur_part, **kwargs)
            else:
                self.upload_part(data_for_write_req, self._cur_part, **kwargs)
            self._cur_part += 1

        if self._write_buf.tell() == 0 and self._write_bufsize == len(data):
            # In the special case of a write that is the same size as
            # our write buffer size, and no unflushed data in the
            # buffer, just directly dispatch the write and bypass the
            # write buffer.
            #
            # This saves a buffer copy, which is especially helpful if
            # 'data' is actually mmap'd from a file.
            #
            # TODO: an additional optimization could be made to allow
            # the last request from an mmap'd upload to take this path
            # too (in general it won't because it's not of length
            # _write_bufsize). This is probably inconsequential though.
            write_request(data)
            return

        remaining_space = self._write_bufsize - self._write_buf.tell()

        if len(data) <= remaining_space:
            self._write_buf.write(data)
        else:
            self._write_buf.write(data[:remaining_space])

            temp_data = self._write_buf.getvalue()
            self._write_buf = BytesIO()
            write_request(temp_data)

            # TODO: check if repeat string splitting is bad for
            # performance when len(data) >> _write_bufsize
            self.write(data[remaining_space:], **kwargs)
    def write(self, data, multithread=True, **kwargs):
        '''
        :param data: Data to be written
        :type data: str or mmap object
        :param multithread: If True, sends multiple write requests asynchronously
        :type multithread: boolean
    # ... (truncated)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, traceback, copy, time
from io import BytesIO
import math
import mmap
from threading import Lock
from multiprocessing import cpu_count
import dxpy
from . import DXDataObject
from ..exceptions import DXFileError, DXIncompleteReadsError
from ..utils import warn
from ..utils.resolver import object_exists_in_project
from ..compat import md5_hasher, basestring
```

## Everything else its module defines (headers only)
```python
def _validate_headers(headers):
def _readable_part_size(num_bytes):
def _get_write_buf_size(buffer_size_hint, file_upload_params, expected_file_size, file_is_mmapd=False):
```

## Signatures of what its module imports from the repository
```python
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

# from ..exceptions import DXFileError
class DXFileError(DXError):

# from ..exceptions import DXIncompleteReadsError
class DXIncompleteReadsError(DXError):

# from ..utils import warn
def warn(*args, **kwargs):
    ...

# from ..utils.resolver import object_exists_in_project
def object_exists_in_project(obj_id, proj_id):
    """:param obj_id: object ID"""
    ...

# from ..compat import md5_hasher
def md5_hasher():
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxfile_download.py:43

    def _make_dxfile(self):
        # Pass dxid=None to skip ID format validation in __init__,
        # then set _dxid directly to the test file ID.
        dxfile = DXFile()
        dxfile._dxid = self.FILE_ID
        return dxfile


# src/python/test/test_dxfile_download.py:105
    DRIVE = 'drive-xxxx'
    CHUNK = b'hello world'

    def _make_dxfile(self):
        dxfile = DXFile()
        dxfile._dxid = self.FILE_ID
        return dxfile


# src/python/dxpy/cli/dataset_utilities.py:1952
        self.describe(default_fields=True, fields={"properties", "details"})
        assert self._record_type in self.types
        assert "descriptor" in self.details
        if is_dxlink(self.details["descriptor"]):
            self.descriptor_dxfile = DXFile(self.details["descriptor"], mode="rb", project=project)
        else:
            err_exit("%s : Invalid cohort or dataset" % self.details["descriptor"])
        self.descriptor = None

# src/python/dxpy/bindings/dxfile.py:570
            bt = bytes(data)
        else:
            raise DXFileError("Invalid type {} for write data argument".format(type(data)))
        assert(isinstance(bt, bytes))
        self._write2(bt, multithread=multithread, **kwargs)

    def closed(self, **kwargs):
        '''
```

Write `checks()` and `cases()` for `DXFile._write2`. Remember: setup in the thunk or at module level, never timed.