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
Function under test: `_get_pool_manager` in `src/python/dxpy/__init__.py`
Import it as `from dxpy import _get_pool_manager`.

## The function
```python
def _get_pool_manager(verify, cert_file, key_file, ssl_context=None):
    global _pool_manager
    default_pool_args = dict(maxsize=32,
                             cert_reqs=ssl.CERT_REQUIRED,
                             headers=_default_headers,
                             timeout=_default_timeout)
    # Don't use the default CA bundle if the user has set the env variable
    # DX_USE_OS_CA_BUNDLE. Enabling that var will make us attempt to load
    # the default CA certs provided by the OS; see DEVEX-875.
    if 'DX_USE_OS_CA_BUNDLE' not in os.environ:
        default_pool_args.update(ca_certs=_default_certs)

    if cert_file is None and verify is None and 'DX_CA_CERT' not in os.environ:
        with _pool_mutex:
            if _pool_manager is None:
                if _get_env_var_proxy():
                    proxy_params = _get_proxy_info(_get_env_var_proxy(print_proxy=True))
                    default_pool_args.update(proxy_params)
                    _pool_manager = urllib3.ProxyManager(**default_pool_args)
                else:
                    _pool_manager = urllib3.PoolManager(**default_pool_args)
            return _pool_manager
    else:
        # This is the uncommon case, normally, we want to cache the pool
        # manager.
        pool_args = dict(default_pool_args,
                         cert_file=cert_file,
                         key_file=key_file,
                         ssl_context=ssl_context,
                         ca_certs=verify or os.environ.get('DX_CA_CERT') or certifi.where())
        if verify is False or os.environ.get('DX_CA_CERT') == 'NOVERIFY':
            pool_args.update(cert_reqs=ssl.CERT_NONE, ca_certs=None)
            urllib3.disable_warnings()
        if _get_env_var_proxy():
            proxy_params = _get_proxy_info(_get_env_var_proxy(print_proxy=True))
            pool_args.update(proxy_params)
            return urllib3.ProxyManager(**pool_args)
        else:
            return urllib3.PoolManager(**pool_args)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import logging
import os, sys, json, time, platform, ssl, traceback
import errno
import math
import socket
import threading
import certifi
from collections import namedtuple
from http.client import BadStatusLine
from io import StringIO
from reprlib import Repr
from . import exceptions
from .utils.printing import BOLD, BLUE, YELLOW, GREEN, RED, WHITE
from random import randint
import urllib3
from threading import Lock
from urllib.parse import urlsplit
from .toolkit_version import version as TOOLKIT_VERSION
from .utils.config import DXConfig as _DXConfig
from .bindings import *
from .dxlog import DXLogHandler
from .utils.exec_utils import run, entry_point
```

## Definitions it uses from the same module
```python
_default_certs = certifi.where()

_default_headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

_default_timeout = urllib3.util.timeout.Timeout(connect=DEFAULT_TIMEOUT, read=DEFAULT_TIMEOUT)

_pool_mutex = Lock()

_pool_manager = None

def _get_proxy_info(url):
    proxy_info = {}

    url_info = urlsplit(url)
    # If the url contains a username, need to separate the username/password
    # from the url
    if url_info.username:
        # Strip the username/password out of the url
        url = url_info.netloc[url_info.netloc.find('@')+1:]
        # Now get the username and possibly password
        proxy_info['proxy_url'] = '{0}://{1}'.format(url_info.scheme, url)
        if url_info.password:
            proxy_auth = '{0}:{1}'.format(url_info.username, url_info.password)
        else:
            proxy_auth = url_info.username
        proxy_info['proxy_headers'] = urllib3.make_headers(proxy_basic_auth=proxy_auth)
    else:
        # No username was given, so just take the url as is.
        proxy_info['proxy_url'] = url

    return proxy_info

def _get_env_var_proxy(print_proxy=False):
  proxy_tuple = ('http_proxy', 'HTTP_PROXY', 'https_proxy', 'HTTPS_PROXY')
  proxy = None
  for env_proxy in proxy_tuple:
    if env_proxy in os.environ:
      proxy = os.environ[env_proxy]
  if print_proxy:
    print('Using env variable %s=%s as proxy' % (env_proxy,proxy),
          file=sys.stderr)
  return proxy
```

## Everything else its module defines (headers only)
```python
class DXHTTPOAuth2():
    def __init__(self, security_context):
def _get_sequence_number():
def configure_urllib3():
    # Disable verbose urllib3 warnings and log messages
def _process_method_url_headers(method, url, headers):
def _is_retryable_exception(e):
def _extract_msg_from_last_exception():
def _calculate_retry_delay(response, num_attempts):
def _maybe_truncate_request(url, data):
def _raise_error_for_testing(try_index=None, method='GET'):
def _debug_print_request(debug_level, seq_num, time_started, method, url, headers, jsonify_data, data):
def _debug_print_response(debug_level, seq_num, time_started, req_id, response_status, response_was_json, method,
                          url, content):
def DXHTTPRequest(resource, data, method='POST', headers=None, auth=True,
                  timeout=DEFAULT_TIMEOUT,
                  use_compression=None, jsonify_data=True, want_full_response=False,
                  decode_response_body=True, prepend_srv=True, session_handler=None,
                  max_retries=DEFAULT_RETRIES, always_retry=False,
                  **kwargs):
def _dxhttp_read_range(url, headers, start_pos, end_pos, timeout, sub_range=True):
def set_api_server_info(host=None, port=None, protocol=None):
def set_security_context(security_context):
def set_job_id(dxid):
def set_workspace_id(dxid):
def set_project_context(dxid):
def set_watch_port(port=None):
def get_auth_server_name(host_override=None, port_override=None, protocol='https'):
def _set_retry_response(response):
def _get_retry_response():
def append_underlying_workflow_describe(globalworkflow_desc):
```

## Signatures of what its module imports from the repository
```python
# from .utils.printing import BOLD
def BOLD(message=None):
    ...

# from .utils.printing import BLUE
def BLUE(message=None):
    ...

# from .utils.printing import YELLOW
def YELLOW(message=None):
    ...

# from .utils.printing import GREEN
def GREEN(message=None):
    ...

# from .utils.printing import RED
def RED(message=None):
    ...

# from .utils.printing import WHITE
def WHITE(message=None):
    ...

# from .utils.config import DXConfig
class DXConfig(MutableMapping):
    CORE_VAR_NAMES = {"DX_APISERVER_HOST", "DX_APISERVER_PORT",
                      "DX_APISERVER_PROTOCOL", "DX_PROJECT_CONTEXT_ID",
                      "DX_WORKSPACE_ID", "DX_SECURITY_CONTEXT", "DX_JOB_ID"}
    STANDALONE_VAR_NAMES = {"DX_CLI_WD", "DX_USERNAME",
                            "DX_PROJECT_CONTEXT_NAME"}
    VAR_NAMES = set.union(CORE_VAR_NAMES, STANDALONE_VAR_NAMES)
    _global_conf_dir = "/etc/dnanexus"
    def __init__(self, suppress_warning=False):
        """:param suppress_warning:"""
        ...
    def get_global_conf_dir(self):
        ...
    def get_user_conf_dir(self):
        ...
    def get_session_conf_dir(self, cleanup=False):
        """Tries to find the session configuration directory by looking in ~/.dnanexus_config/sessions/<PID>,"""
        ...
    def write(self, item, value):
        ...
    def save(self):
        ...
    def clear(self, reset=False):
        ...

# from .dxlog import DXLogHandler
class DXLogHandler(SysLogHandler):
    def __init__(self, priority_log_address="/opt/dnanexus/log/priority",
                 bulk_log_address="/opt/dnanexus/log/bulk",
                 source="DX_APP"):
        ...
    def close(self):
        ...
    def encodePriority(self, record):
        # See logging.handlers.SysLogHandler for an explanation of this.
        ...
    def truncate_message(self, message):
        ...
    def is_resource_log(self, message):
        ...
    def emit(self, record):
        ...

# from .utils.exec_utils import run
def run(function_name=None, function_input=None):
    """Triggers the execution environment entry point processor."""
    ...

# from .utils.exec_utils import entry_point
def entry_point(entry_point_name):
    """Use this to decorate a DNAnexus execution environment entry point."""
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/dxpy/__init__.py:591
            body = _maybe_truncate_request(_url, serialized_data)

            # throws BadStatusLine if the server returns nothing
            try:
                pool_manager = _get_pool_manager(**pool_args)

                _headers['User-Agent'] = USER_AGENT
                _headers['DNAnexus-API'] = API_VERSION

# src/python/dxpy/__init__.py:727
        except Exception as e:
            # Avoid reusing connections in the pool, since they may be
            # in an inconsistent state (observed as "ResponseNotReady"
            # errors).
            _get_pool_manager(**pool_args).clear()
            success = False
            exception_msg = _extract_msg_from_last_exception()
            if isinstance(e, _expected_exceptions):
```

Write `checks()` and `cases()` for `_get_pool_manager`. Remember: setup in the thunk or at module level, never timed.