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
Function under test: `DXConfig.get_session_conf_dir` in `src/python/dxpy/utils/config.py`
Import it as `from dxpy.utils.config import DXConfig`; the method is called as `DXConfig.get_session_conf_dir(instance, ...)`.

## The function
```python
    def get_session_conf_dir(self, cleanup=False):
        """
        Tries to find the session configuration directory by looking in ~/.dnanexus_config/sessions/<PID>,
        where <PID> is pid of the parent of this process, then its parent, and so on.
        If none of those exist, the path for the immediate parent is given, even if it doesn't exist.

        If *cleanup* is True, looks up and deletes all session configuration directories that belong to nonexistent
        processes.
        """
        sessions_dir = os.path.join(self._user_conf_dir, "sessions")
        try:
            from psutil import Process, pid_exists

            if cleanup:
                try:
                    session_dirs = os.listdir(sessions_dir)
                except OSError as e:
                    # Silently skip cleanup and continue if we are unable to
                    # enumerate the session directories for any reason
                    # (including, most commonly, because the sessions dir
                    # doesn't exist)
                    session_dirs = []
                for session_dir in session_dirs:
                    try:
                        session_pid = int(session_dir)
                    except ValueError:
                        # If dir name doesn't look like an int, leave it
                        # alone
                        continue
                    if not pid_exists(session_pid):
                        rmtree(os.path.join(sessions_dir, session_dir), ignore_errors=True)

            parent_process = Process(os.getpid()).parent()
            if parent_process is None:
                parent_process = Process(os.getpid())
            default_session_dir = os.path.join(sessions_dir, str(parent_process.pid))
            while parent_process is not None and parent_process.pid != 0:
                session_dir = os.path.join(sessions_dir, str(parent_process.pid))
                if os.path.exists(session_dir):
                    return session_dir
                parent_process = parent_process.parent()
            return default_session_dir
        except (ImportError, IOError, AttributeError) as e:
            # We don't bundle psutil with Windows, so failure to import
            # psutil would be expected.
            if platform.system() != 'Windows':
                warn(fill("Error while retrieving session configuration: " + format_exception(e)))
        except Exception as e:
            warn(fill("Unexpected error while retrieving session configuration: " + format_exception(e)))
        return self._get_ppid_session_conf_dir(sessions_dir)
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class DXConfig(MutableMapping):
    """This class provides the dxpy configuration manager, available as
    ``dxpy.config``. When first accessed, the config manager looks up
    environment variables used to configure dxpy, and if they are not
    found, then attempts to resolve them by looking in the file
    ~/.dnanexus_config/environment, followed by the installed defaults
    in /etc/dnanexus.

    To assign to and access variables managed by the configuration
    manager, use ``dxpy.config["VAR_NAME"]``. When assigning a
    variable, the manager sets it as a process environment variable
    and updates any dxpy variable bound to it
    (e.g. dxpy.SECURITY_CONTEXT when setting
    DX_SECURITY_CONTEXT). When accessing a variable, it is looked up
    from the process environment.

    To save (serialize) the value of a variable to a persistent dxpy
    configuration file, use ``dxpy.config.write(key, value)`` or
    ``dxpy.config.save()`` after assigning variable values. To clear
    the values in persistent dxpy configuration, use
    ``dxpy.config.clear()``.
    """
    CORE_VAR_NAMES = {"DX_APISERVER_HOST", "DX_APISERVER_PORT",
                      "DX_APISERVER_PROTOCOL", "DX_PROJECT_CONTEXT_ID",
                      "DX_WORKSPACE_ID", "DX_SECURITY_CONTEXT", "DX_JOB_ID"}
    STANDALONE_VAR_NAMES = {"DX_CLI_WD", "DX_USERNAME",
                            "DX_PROJECT_CONTEXT_NAME"}
    """
    List of variable names supported by the configuration manager.
    """
    VAR_NAMES = set.union(CORE_VAR_NAMES, STANDALONE_VAR_NAMES)
    defaults = {
        "DX_SECURITY_CONTEXT": json.dumps({"auth_token": "PUBLIC", "auth_token_type": "Bearer"}),
        "DX_APISERVER_PROTOCOL": DEFAULT_APISERVER_PROTOCOL,
        "DX_APISERVER_HOST": DEFAULT_APISERVER_HOST,
        "DX_APISERVER_PORT": DEFAULT_APISERVER_PORT,
        "DX_CLI_WD": "/"
    }
    _global_conf_dir = "/etc/dnanexus"
    def __init__(self, suppress_warning=False):
        """
        :param suppress_warning:
            Whether to suppress the warning message for any mismatch found in the environment variables and the dx
            configuration file
        :type suppress_warning: boolean
        """
        try:
            dxpy._DEBUG = int(os.environ.get("_DX_DEBUG", 0))
        except ValueError as e:
            warn("WARNING: Expected _DX_DEBUG to be an integer, but got", os.environ["_DX_DEBUG"])
            dxpy._DEBUG = 0

        try:
            dxpy._INJECT_ERROR = bool(os.environ.get("_DX_INJECT_ERROR", 0))
        except:
            dxpy._INJECT_ERROR = False

        self._user_conf_dir = os.path.expanduser(os.environ.get("DX_USER_CONF_DIR", "~/.dnanexus_config"))

        dxpy._UPGRADE_NOTIFY = os.path.join(self._user_conf_dir, ".upgrade_notify")
        # If last upgrade notification was less than 24 hours ago, disable it
        if os.path.exists(dxpy._UPGRADE_NOTIFY) and os.path.getmtime(dxpy._UPGRADE_NOTIFY) > time.time() - 86400:
            dxpy._UPGRADE_NOTIFY = False

        env_vars = self._read_conf_dir(self.get_global_conf_dir())
        env_vars.update(self._read_conf_dir(self.get_user_conf_dir()))
        env_vars.update(self._read_conf_dir(self.get_session_conf_dir(cleanup=True)))
        env_overrides = []
        for var in self.VAR_NAMES:
            if var in os.environ:
                if var in env_vars and env_vars.get(var) != os.environ[var]:
                    env_overrides.append(var)
                env_vars[var] = os.environ[var]

        for var in env_vars:
            if env_vars[var] is not None:
                os.environ[var] = env_vars[var]

        if sys.stdout.isatty():
            if not suppress_warning and len(env_overrides) > 0:
                msg = "WARNING: The following environment variables were found to be different than the values " + \
                      "last stored by dx: "
                warn(fill(msg + ", ".join(env_overrides), width=80))
                msg = "To use the values stored by dx, unset the environment variables in your shell by running " + \
                      '"source ~/.dnanexus_config/unsetenv".  To clear the dx-stored values, run "dx clearenv".'
                warn(fill(msg, width=80))

        self._sync_dxpy_state()
    def _sync_dxpy_state(self):
        ...
    def get_global_conf_dir(self):
        ...
    def get_user_conf_dir(self):
        ...
    def get_session_conf_dir(self, cleanup=False):
        """
        Tries to find the session configuration directory by looking in ~/.dnanexus_config/sessions/<PID>,
        where <PID> is pid of the parent of this process, then its parent, and so on.
        If none of those exist, the path for the immediate parent is given, even if it doesn't exist.

        If *cleanup* is True, looks up and deletes all session configuration directories that belong to nonexistent
        processes.
        """
        sessions_dir = os.path.join(self._user_conf_dir, "sessions")
        try:
            from psutil import Process, pid_exists

            if cleanup:
                try:
                    session_dirs = os.listdir(sessions_dir)
                except OSError as e:
                    # Silently skip cleanup and continue if we are unable to
                    # enumerate the session directories for any reason
                    # (including, most commonly, because the sessions dir
                    # doesn't exist)
                    session_dirs = []
                for session_dir in session_dirs:
                    try:
                        session_pid = int(session_dir)
                    except ValueError:
                        # If dir name doesn't look like an int, leave it
                        # alone
                        continue
                    if not pid_exists(session_pid):
                        rmtree(os.path.join(sessions_dir, session_dir), ignore_errors=True)

            parent_process = Process(os.getpid()).parent()
            if parent_process is None:
                parent_process = Process(os.getpid())
            default_session_dir = os.path.join(sessions_dir, str(parent_process.pid))
            while parent_process is not None and parent_process.pid != 0:
                session_dir = os.path.join(sessions_dir, str(parent_process.pid))
                if os.path.exists(session_dir):
                    return session_dir
                parent_process = parent_process.parent()
            return default_session_dir
        except (ImportError, IOError, AttributeError) as e:
            # We don't bundle psutil with Windows, so failure to import
            # psutil would be expected.
            if platform.system() != 'Windows':
                warn(fill("Error while retrieving session configuration: " + format_exception(e)))
        except Exception as e:
            warn(fill("Unexpected error while retrieving session configuration: " + format_exception(e)))
        return self._get_ppid_session_conf_dir(sessions_dir)
    def _get_ppid_session_conf_dir(self, sessions_dir):
        ...
    def _read_conf_dir(self, dirname):
        ...
    def __getitem__(self, item):
        ...
    def __setitem__(self, key, value):
        ...
    def __delitem__(self, key):
        ...
    def __iter__(self):
        ...
    def __len__(self):
        ...
    def __repr__(self):
        ...
    def write(self, item, value):
        ...
    def save(self):
        ...
    def _write_unsetenv(self, conf_dir):
        ...
    def _write_conf_dir(self, conf_dir):
        ...
    def clear(self, reset=False):
        ...
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, json, time
import platform
from shutil import rmtree
from collections.abc import MutableMapping
import dxpy
from . import warn
from .. import DEFAULT_APISERVER_PROTOCOL, DEFAULT_APISERVER_HOST, DEFAULT_APISERVER_PORT
from ..exceptions import format_exception
from .printing import fill
```

## Everything else its module defines (headers only)
```python
def _remove_ignore_errors(filename):
def _open_for_writing_with_permissions(filename, perms=0o600):
```

## Signatures of what its module imports from the repository
```python
# from . import warn
def warn(*args, **kwargs):
    ...

# from ..exceptions import format_exception
def format_exception(e):
    """Returns a string containing the type and text of the exception."""
    ...

# from .printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxpy_utils.py:315
class TestDXConfig(unittest.TestCase):
    def test_dxconfig(self):
        environ_backup = os.environ.copy()
        try:
            c = config.DXConfig()
            for var in c.VAR_NAMES:
                value = '{"foo": "bar"}'
                c[var] = value

# src/python/dxpy/__init__.py:1043
    return globalworkflow_desc


from .utils.config import DXConfig as _DXConfig
config = _DXConfig()

from .bindings import *
from .dxlog import DXLogHandler

# src/python/dxpy/utils/config.py:282
        self.save()

    def save(self):
        self._write_conf_dir(self._user_conf_dir)
        self._write_conf_dir(self.get_session_conf_dir())
        self._write_unsetenv(self._user_conf_dir)

    def _write_unsetenv(self, conf_dir):

# src/python/dxpy/utils/config.py:313
                value = self.get(var, self.defaults.get(var, ""))
                fd.write(value)

    def clear(self, reset=False):
        rmtree(self.get_session_conf_dir(), ignore_errors=True)
        _remove_ignore_errors(os.path.join(self._user_conf_dir, "environment"))
        _remove_ignore_errors(os.path.join(self._user_conf_dir, "environment.json"))
        for f in self.STANDALONE_VAR_NAMES:
```

Write `checks()` and `cases()` for `DXConfig.get_session_conf_dir`. Remember: setup in the thunk or at module level, never timed.