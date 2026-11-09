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
Function under test: `_download_dxdatabasefile` in `src/python/dxpy/bindings/dxdatabase_functions.py`
Import it as `from dxpy.bindings.dxdatabase_functions import _download_dxdatabasefile`.

## The function
```python
def _download_dxdatabasefile(dxid, filename, src_filename, file_status, part_retry_counter,
                     chunksize=dxfile.DEFAULT_BUFFER_SIZE, append=False, show_progress=False,
                     project=None, describe_output=None, **kwargs):
    '''
    Core of download logic. Download the specified file/folder *src_filename*
    associated with database-id *dxid* and store it in
    a local file *filename*.

    The return value is as follows:
    - True means the download was successfully completed
    - False means the download was stopped because of a retryable error
    - Exception raised for other errors
    '''
    def print_progress(bytes_downloaded, file_size, action="Downloaded"):
        num_ticks = 60

        effective_file_size = file_size or 1
        if bytes_downloaded > effective_file_size:
            effective_file_size = bytes_downloaded

        ticks = int(round((bytes_downloaded / float(effective_file_size)) * num_ticks))
        percent = int(math.floor((bytes_downloaded / float(effective_file_size)) * 100))

        fmt = "[{done}{pending}] {action} {done_bytes:,}{remaining} bytes ({percent}%) {name}"
        # Erase the line and return the cursor to the start of the line.
        # The following VT100 escape sequence will erase the current line.
        sys.stderr.write("\33[2K")
        sys.stderr.write(fmt.format(action=action,
                                    done=("=" * (ticks - 1) + ">") if ticks > 0 else "",
                                    pending=" " * (num_ticks - ticks),
                                    done_bytes=bytes_downloaded,
                                    remaining=" of {size:,}".format(size=file_size) if file_size else "",
                                    percent=percent,
                                    name=filename))
        sys.stderr.flush()
        sys.stderr.write("\r")
        sys.stderr.flush()

    _bytes = 0

    if isinstance(dxid, DXDatabase):
        dxdatabase = dxid
    else:
        dxdatabase = DXDatabase(dxid, project=(project if project != DXFile.NO_PROJECT_HINT else None))

    do_debug("dxdatabase_functions.py _download_dxdatabasefile - dxdatabase: {}".format(dxdatabase)) 

    if describe_output and describe_output.get("parts") is not None:
        dxdatabase_desc = describe_output
    else:
        dxdatabase_desc = dxdatabase.describe(fields={"parts"}, default_fields=True, **kwargs)

    # For database files, the whole parquet file is one 'part'.
    # Consider a multi part download approach in the future.
    parts = {u'1': {u'state': u'complete', u'size': file_status["size"]}}
    parts_to_get = sorted(parts, key=int)
    file_size = file_status["size"]

    offset = 0
    for part_id in parts_to_get:
        parts[part_id]["start"] = offset
        offset += parts[part_id]["size"]

    do_debug("dxdatabase_functions.py _download_dxdatabasefile - parts {}".format(parts))

    # Create proper destination path, including any subdirectories needed within path.
    ensure_local_dir(filename);
    dest_path = os.path.join(filename, src_filename)
    dest_dir_idx = dest_path.rfind("/");
    if dest_dir_idx != -1:
        dest_dir = dest_path[:dest_dir_idx]
        ensure_local_dir(dest_dir)      

    do_debug("dxdatabase_functions.py _download_dxdatabasefile - dest_path {}".format(dest_path)) 

    if append:
        fh = open(dest_path, "ab")
    else:
        try:
            fh = open(dest_path, "rb+")
        except IOError:
            fh = open(dest_path, "wb")

    if show_progress:
        print_progress(0, None)

    def get_chunk(part_id_to_get, start, end):
        do_debug("dxdatabase_functions.py get_chunk - start {}, end {}, part id {}".format(start, end, part_id_to_get))
        url, headers = dxdatabase.get_download_url(src_filename=src_filename, project=project, **kwargs)
        # No sub ranges for database file downloads
        sub_range = False
        data = dxpy._dxhttp_read_range(url, headers, start, end, FILE_REQUEST_TIMEOUT, sub_range)
        return part_id_to_get, data

    def chunk_requests():
        for part_id_to_chunk in parts_to_get:
            part_info = parts[part_id_to_chunk]
            for chunk_start in range(part_info["start"], part_info["start"] + part_info["size"], chunksize):
                chunk_end = min(chunk_start + chunksize, part_info["start"] + part_info["size"]) - 1
                yield get_chunk, [part_id_to_chunk, chunk_start, chunk_end], {}

    def verify_part(_part_id, got_bytes, hasher):
        if got_bytes is not None and got_bytes != parts[_part_id]["size"]:
            msg = "Unexpected part data size in {} part {} (expected {}, got {})"
            msg = msg.format(dxdatabase.get_id(), _part_id, parts[_part_id]["size"], got_bytes)
            raise DXPartLengthMismatchError(msg)
        if hasher is not None and "md5" not in parts[_part_id]:
            warnings.warn("Download of file {} is not being checked for integrity".format(dxdatabase.get_id()))
        elif hasher is not None and hasher.hexdigest() != parts[_part_id]["md5"]:
            msg = "Checksum mismatch in {} part {} (expected {}, got {})"
            msg = msg.format(dxdatabase.get_id(), _part_id, parts[_part_id]["md5"], hasher.hexdigest())
            raise DXChecksumMismatchError(msg)

    with fh:

        try:
            # Main loop. In parallel: download chunks, verify them, and write them to disk.
            get_first_chunk_sequentially = (file_size > 128 * 1024 and dxpy.JOB_ID)
            cur_part, got_bytes, hasher = None, None, None
            for chunk_part, chunk_data in response_iterator(chunk_requests(),
                                                            dxdatabase._http_threadpool,
                                                            do_first_task_sequentially=get_first_chunk_sequentially):
                if chunk_part != cur_part:
                    # TODO: remove permanently if we don't find use for this
                    # verify_part(cur_part, got_bytes, hasher)

                    cur_part, got_bytes, hasher = chunk_part, 0, md5_hasher()
                got_bytes += len(chunk_data)
                hasher.update(chunk_data)
                fh.write(chunk_data)
                if show_progress:
                    _bytes += len(chunk_data)
                    print_progress(_bytes, file_size)
            # TODO: same as above
            # verify_part(cur_part, got_bytes, hasher)
            if show_progress:
                print_progress(_bytes, file_size, action="Completed")
        except DXFileError:
            print(traceback.format_exc(), file=sys.stderr)
            part_retry_counter[cur_part] -= 1
            if part_retry_counter[cur_part] > 0:
                print("Retrying {} ({} tries remain for part {})".format(dxdatabase.get_id(), part_retry_counter[cur_part], cur_part),
                      file=sys.stderr)
                return False
            raise

        if show_progress:
            sys.stderr.write("\n")

        return True
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, math, mmap, stat
import hashlib
import traceback
import warnings
from collections import defaultdict
import multiprocessing
import dxpy
from .. import logger
from . import dxfile, DXFile
from . import dxdatabase, DXDatabase
from .dxfile import FILE_REQUEST_TIMEOUT
from ..compat import md5_hasher
from ..exceptions import DXFileError, DXChecksumMismatchError, DXIncompleteReadsError, err_exit
from ..utils import response_iterator
import subprocess
```

## Definitions it uses from the same module
```python
def do_debug(msg):
    logger.debug(msg)

def ensure_local_dir(d):
    if not os.path.isdir(d):
        if os.path.exists(d):
            raise DXFileError("Destination location '{}' already exists and is not a directory".format(d))
        logger.debug("Creating destination directory: '%s'", d)
        os.makedirs(d)
```

## Everything else its module defines (headers only)
```python
def download_dxdatabasefile(dxid, dst_filename, src_filename, file_status, chunksize=dxfile.DEFAULT_BUFFER_SIZE, append=False, show_progress=False,
                            project=None, describe_output=None, **kwargs):
def _which(program):
def _verify(filename, md5digest):
```

## Signatures of what its module imports from the repository
```python
# from ..compat import md5_hasher
def md5_hasher():
    ...

# from ..exceptions import DXFileError
class DXFileError(DXError):

# from ..exceptions import DXChecksumMismatchError
class DXChecksumMismatchError(DXFileError):

# from ..utils import response_iterator
def response_iterator(request_iterator, thread_pool, max_active_tasks=None, do_first_task_sequentially=True):
    """:param request_iterator:"""
    ...

# from ..exceptions import DXIncompleteReadsError
class DXIncompleteReadsError(DXError):

# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/bindings/dxdatabase_functions.py:80

    part_retry_counter = defaultdict(lambda: 3)
    success = False
    while not success:
        success = _download_dxdatabasefile(dxid,
                                           dst_filename,
                                           src_filename,
                                           file_status,
                                           part_retry_counter,
                                           chunksize=chunksize,
                                           append=append,
                                           show_progress=show_progress,
                                           project=project,
                                           describe_output=describe_output,
                                           **kwargs)


# Check if a program (wget, curl, etc.) is on the path, and
```

Write `checks()` and `cases()` for `_download_dxdatabasefile`. Remember: setup in the thunk or at module level, never timed.