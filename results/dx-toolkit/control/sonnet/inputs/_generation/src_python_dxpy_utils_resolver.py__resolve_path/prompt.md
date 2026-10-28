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
Function under test: `resolve_path` in `src/python/dxpy/utils/resolver.py`
Import it as `from dxpy.utils.resolver import resolve_path`.

## The function
```python
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
    '''
    :param path: A path to a data object to attempt to resolve
    :type path: string
    :param expected: one of the following: "folder", "entity", or None
            to indicate whether the expected path is a folder, a data
            object, or either
    :type expected: string or None
    :returns: A tuple of 3 values: container_ID, folderpath, entity_name
    :rtype: string, string, string
    :raises: exc:`ResolutionError` if the project cannot be resolved by
            name or the path is malformed
    :param allow_empty_string: If false, a ResolutionError will be
            raised if *path* is an empty string. Use this when resolving
            the empty string could result in unexpected behavior.
    :type allow_empty_string: boolean

    Attempts to resolve *path* to a project or container ID, a folder
    path, and a data object or folder name.  This method will NOT
    raise an exception if the specified folder or object does not
    exist.  This method is primarily for parsing purposes.

    Returns one of the following:

      (project, folder, maybe_name)
      where
        project is a container ID (non-null)
        folder is a folder path
        maybe_name is a string if the path could represent a folder or an object, or
        maybe_name is None if the path could only represent a folder

    OR

      (maybe_project, None, object_id)
      where
        maybe_project is a container ID or None
        object_id is a dataobject, app, or execution (specified by ID, not name)

    OR

      (job_id, None, output_name)
      where
        job_id and output_name are both non-null

    '''
    # TODO: callers that intend to obtain a data object probably won't be happy
    # with an app or execution ID. Callers should probably have to specify
    # whether they are okay with getting an execution ID or not.

    # TODO: callers that are looking for a place to write data, rather than
    # read it, probably won't be happy with receiving an object ID, or a
    # JBOR. Callers should probably specify whether they are looking for an
    # "LHS" expression or not.

    if '_DX_FUSE' in os.environ:
        from xattr import xattr
        path = xattr(path)['project'] + ":" + xattr(path)['id']

    if path == '' and not allow_empty_string:
        raise ResolutionError('Cannot parse ""; expected the path to be a non-empty string')
    path = _maybe_convert_stringified_dxlink(path)

    # Easy case: ":"
    if path == ':':
        if dxpy.WORKSPACE_ID is None:
            raise ResolutionError("Cannot resolve \":\": expected a project name or ID "
                                  "to the left of the colon, or for a current project to be set")
        return ([dxpy.WORKSPACE_ID] if multi_projects else dxpy.WORKSPACE_ID), '/', None
    # Second easy case: empty string
    if path == '':
        if dxpy.WORKSPACE_ID is None:
            raise ResolutionError('Expected a project name or ID to the left of a colon, '
                                  'or for a current project to be set')
        return ([dxpy.WORKSPACE_ID] if multi_projects else dxpy.WORKSPACE_ID), dxpy.config.get('DX_CLI_WD', '/'), None
    # Third easy case: hash ID
    if is_container_id(path):
        return ([path] if multi_projects else path), '/', None
    elif is_hashid(path):
        return ([dxpy.WORKSPACE_ID] if multi_projects else dxpy.WORKSPACE_ID), None, path

    # using a numerical sentinel value to indicate that it hasn't been
    # set in case dxpy.WORKSPACE_ID is actually None
    project = 0
    folderpath = None
    entity_name = None
    wd = dxpy.config.get('DX_CLI_WD', u'/')

    # Test for multiple colons
    last_colon = get_last_pos_of_char(':', path)
    if last_colon >= 0:
        last_last_colon = get_last_pos_of_char(':', path[:last_colon])
        if last_last_colon >= 0:
            raise ResolutionError('Cannot parse "' + path + '" as a path; at most one unescaped colon can be present')

    substrings = split_unescaped(':', path)

    if len(substrings) == 2:
        # One of the following:
        # 1) job-id:fieldname
        # 2) project-name-or-id:folderpath/to/possible/entity
        if is_job_id(substrings[0]):
            return ([substrings[0]] if multi_projects else substrings[0]), None, substrings[1]

        if multi_projects:
            project_ids = resolve_container_id_or_name(substrings[0], is_error=True, multi=True)
        else:
            project = resolve_container_id_or_name(substrings[0], is_error=True)
        wd = '/'
    elif get_last_pos_of_char(':', path) >= 0:
        # :folderpath/to/possible/entity OR project-name-or-id:
        # Colon is either at the beginning or at the end
        wd = '/'
        if path.startswith(':'):
            if dxpy.WORKSPACE_ID is None:
                raise ResolutionError('Cannot resolve "%s": expected a project name or ID to the left of the '
                                      'colon, or for a current project to be set' % (path,))
            project = dxpy.WORKSPACE_ID
        else:
            # One nonempty string to the left of a colon
            project = resolve_container_id_or_name(substrings[0], is_error=True)
            folderpath = '/'
    else:
        # One nonempty string, no colon present, do NOT interpret as
        # project
        project = dxpy.WORKSPACE_ID
        if project is None:
            raise ResolutionError('Cannot resolve "%s": expected the path to be qualified with a project name or ID, '
                                  'and a colon; or for a current project to be set' % (path,))

    # Determine folderpath and entity_name if necessary
    if folderpath is None:
        folderpath = substrings[-1]
        folderpath, entity_name = clean_folder_path(('' if folderpath.startswith('/') else wd + '/') + folderpath, expected)

    if multi_projects:
        return (project_ids if project == 0 else [project]), folderpath, entity_name
    else:
        return project, folderpath, entity_name
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import
import os, sys, json, re
import dxpy
from .describe import get_ls_l_desc
from ..compat import basestring
from ..cli import try_call, INTERACTIVE_CLI
from ..exceptions import DXCLIError, DXError
```

## Definitions it uses from the same module
```python
class ResolutionError(DXError):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        ...

def is_hashid(string):
    return hash_pattern.match(string) is not None

def is_container_id(string):
    return is_hashid(string) and (string.startswith('project-') or string.startswith('container-'))

def is_job_id(string):
    return is_hashid(string) and string.startswith('job-')

def get_last_pos_of_char(char, string):
    '''
    :param char: The character to find
    :type char: string
    :param string: The string in which to search for *char*
    :type string: string
    :returns: Index in *string* where *char* last appears (unescaped by a preceding "\\"), -1 if not found
    :rtype: int

    Finds the last occurrence of *char* in *string* in which *char* is
    not present as an escaped character.

    '''
    pos = len(string)
    while pos > 0:
        pos = string[:pos].rfind(char)
        if pos == -1:
            return -1
        num_backslashes = 0
        test_index = pos - 1
        while test_index >= 0 and string[test_index] == '\\':
            num_backslashes += 1
            test_index -= 1
        if num_backslashes % 2 == 0:
            return pos
    return -1

def split_unescaped(char, string, include_empty_strings=False):
    '''
    :param char: The character on which to split the string
    :type char: string
    :param string: The string to split
    :type string: string
    :returns: List of substrings of *string*
    :rtype: list of strings

    Splits *string* whenever *char* appears without an odd number of
    backslashes ('\\') preceding it, discarding any empty string
    elements.

    '''
    words = []
    pos = len(string)
    lastpos = pos
    while pos >= 0:
        pos = get_last_pos_of_char(char, string[:lastpos])
        if pos >= 0:
            if pos + 1 != lastpos or include_empty_strings:
                words.append(string[pos + 1: lastpos])
            lastpos = pos
    if lastpos != 0 or include_empty_strings:
        words.append(string[:lastpos])
    words.reverse()
    return words

def clean_folder_path(path, expected=None):
    '''
    :param path: A folder path to sanitize and parse
    :type path: string
    :param expected: Whether a folder ("folder"), a data object ("entity"), or either (None) is expected
    :type expected: string or None
    :returns: *folderpath*, *name*

    Unescape and parse *path* as a folder path to possibly an entity
    name.  Consecutive unescaped forward slashes "/" are collapsed to
    a single forward slash.  If *expected* is "folder", *name* is
    always returned as None.  Otherwise, the string to the right of
    the last unescaped "/" is considered a possible data object name
    and returned as such.

    '''
    folders = split_unescaped('/', path)

    if len(folders) == 0:
        return '/', None

    if expected == 'folder' or folders[-1] == '.' or folders[-1] == '..' or get_last_pos_of_char('/', path) == len(path) - 1:
        entity_name = None
    else:
        entity_name = unescape_name_str(folders.pop())

    sanitized_folders = []

    for folder in folders:
        if folder == '.':
            pass
        elif folder == '..':
            if len(sanitized_folders) > 0:
                sanitized_folders.pop()
        else:
            sanitized_folders.append(unescape_folder_str(folder))

    return ('/' + '/'.join(sanitized_folders)), entity_name

def resolve_container_id_or_name(raw_string, is_error=False, multi=False):
    '''
    :param raw_string: A potential project or container ID or name
    :type raw_string: string
    :param is_error: Whether to raise an exception if the project or
            container ID cannot be resolved
    :type is_error: boolean
    :returns: Project or container ID if found or else None
    :rtype: string or None
    :raises: :exc:`ResolutionError` if *is_error* is True and the
            project or container could not be resolved

    Unescapes and attempts to resolve *raw_string* to a project or
    container ID.

    '''
    string = unescape_name_str(raw_string)
    if is_container_id(string):
        return ([string] if multi else string)

    if string in cached_project_names:
        return ([cached_project_names[string]] if multi else cached_project_names[string])

    try:
        results = list(dxpy.find_projects(name=string, describe=True, level='VIEW'))
    except Exception as details:
        raise ResolutionError(str(details))

    if len(results) == 1:
        cached_project_names[string] = results[0]['id']
        return ([results[0]['id']] if multi else results[0]['id'])
    elif len(results) == 0:
        if is_error:
            raise ResolutionError('Could not find a project named "' + string + '"')
        return ([] if multi else None)
    elif not multi:
        if INTERACTIVE_CLI:
            print('Found multiple projects with name "' + string + '"')
            choice = pick(['{id} ({level})'.format(id=result['id'], level=result['level'])
                           for result in results])
            return results[choice]['id']
        else:
            raise ResolutionError('Found multiple projects with name "' + string + '"; please use a project ID to specify the desired project')
    else:
        # len(results) > 1 and multi
        return [result['id'] for result in results]

def _maybe_convert_stringified_dxlink(path):
    try:
        possible_hash = json.loads(path)
        if isinstance(possible_hash, dict) and '$dnanexus_link' in possible_hash:
            if isinstance(possible_hash['$dnanexus_link'], basestring):
                return possible_hash['$dnanexus_link']
            elif (isinstance(possible_hash['$dnanexus_link'], dict) and
                  isinstance(possible_hash['$dnanexus_link'].get('project', None), basestring) and
                  isinstance(possible_hash['$dnanexus_link'].get('id', None), basestring)):
                return possible_hash['$dnanexus_link']['project'] + ':' + possible_hash['$dnanexus_link']['id']
    except:
        pass
    return path
```

## Everything else its module defines (headers only)
```python
def pick(choices, default=None, str_choices=None, prompt=None, allow_mult=False, more_choices=False):
def paginate_and_pick(generator, render_fn=str, filter_fn=None, page_len=10, **pick_opts):
def is_data_obj_id(string):
def is_project_id(string):
def is_analysis_id(string):
def is_localjob_id(thing):
def is_nohash_id(string):
def is_glob_pattern(string):
def is_jbor_str(string):
def is_project_explicit(path):
def object_exists_in_project(obj_id, proj_id):
def escaper(match):
def escape_folder_str(string):
def escape_name_str(string):
def unescaper(match):
def unescape_folder_str(string):
def unescape_name_str(string):
def get_first_pos_of_char(char, string):
def resolve_job_ref(job_id, name, describe={}):
def _check_resolution_needed(path, project, folderpath, entity_name, expected_classes=None, describe=True,
                             enclose_in_list=False):
def _resolve_folder(project, parent_folder, folder_name):
def _validate_resolution_output_length(path, entity_name, results, allow_mult=False, all_mult=False,
                                       ask_to_resolve=True):
def _resolve_global_entity(project_or_job_id, folderpath, entity_name, describe=True, visibility="either"):
def _format_resolution_output(path, project, folderpath, entity_name, result):
def resolve_multiple_existing_paths(paths):
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
def check_folder_exists(project, path, folder_name):
def get_app_from_path(path):
def get_global_workflow_from_path(path):
def get_global_exec_from_path(path):
def resolve_app(path):
def resolve_global_workflow(path):
def resolve_global_executable(path, is_version_required=False):
def get_exec_handler(path, alias=None):
def resolve_to_objects_or_project(path, all_matching_results=False):
def parse_input_keyval(keyeqval):
```

## Signatures of what its module imports from the repository
```python
# from .describe import get_ls_l_desc
def get_ls_l_desc(desc, include_folder=False, include_project=False):
    """desc must have at least all the fields given by get_ls_l_desc_fields."""
    ...

# from ..cli import try_call
def try_call(func, *args, **kwargs):
    ...

# from ..exceptions import DXCLIError
class DXCLIError(DXError):

# from ..exceptions import DXError
class DXError(Exception):
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_dxpy.py:2759
        temp_proj_name = 'resolve_path_' + str(time.time())
        not_a_project_name = 'doesnt_exist_' + str(time.time())
        dxpy.config['DX_CLI_WD'] = '/a'
        with testutil.temporary_project(name=temp_proj_name) as p:
            self.assertEqual(resolve_path(""),
                             (self.project, "/a", None))
            with self.assertRaisesRegex(ResolutionError, "expected the path to be a non-empty string"):
                resolve_path("", allow_empty_string=False)

# src/python/test/test_dxpy.py:2762
        with testutil.temporary_project(name=temp_proj_name) as p:
            self.assertEqual(resolve_path(""),
                             (self.project, "/a", None))
            with self.assertRaisesRegex(ResolutionError, "expected the path to be a non-empty string"):
                resolve_path("", allow_empty_string=False)
            self.assertEqual(resolve_path(":"),
                             (self.project, "/", None))


# src/python/dxpy/cli/dataset_utilities.py:1718
def resolve_validate_dx_path(path):
    """
    Resolves dx path into project, folder and name. Fails if non existing folder is provided.
    """
    project, folder, name = resolve_path(path)
    err_msg, folder_exists = None, None
    if folder != "/":
        folder_name = os.path.basename(folder)

# src/python/dxpy/cli/workflow.py:54
        project, folder, name = try_call(dxpy.utils.resolver.resolve_path, args.output)
    if args.output_folder is not None:
        try:
            # Try to resolve to a path in the project
            _ignore, args.output_folder, _ignore = resolve_path(args.output_folder, expected='folder')
        except:
            # But if not, just use the value directly
            pass

# src/python/dxpy/cli/workflow.py:108
    # get folder path
    folderpath = None
    if args.output_folder is not None:
        try:
            _ignore, folderpath, _none = resolve_path(args.output_folder, expected='folder')
        except:
            folderpath = args.output_folder
    elif args.relative_output_folder is not None:

# src/python/dxpy/scripts/dx.py:845
    had_error = False
    for path in args.paths:
        # Resolve the path and add it to the list
        try:
            project, folderpath, _none = resolve_path(path, expected='folder')
        except ResolutionError as details:
            print(fill('Could not resolve "' + path + '": ' + str(details)))
            had_error = True
```

Write `checks()` and `cases()` for `resolve_path`. Remember: setup in the thunk or at module level, never timed.