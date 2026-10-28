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
Function under test: `_populate_cached_file_ids` in `src/python/dxpy/nextflow/collect_images.py`
Import it as `from dxpy.nextflow.collect_images import _populate_cached_file_ids`.

## The function
```python
def _populate_cached_file_ids(image_refs):
    """Look up previously cached Docker images in the current project.

    Searches ``/.cached_docker_images/<image_name>/`` for files matching
    ``<image_name>_<tag>``.  When found, verifies the image digest stored
    in the file's ``properties`` and populates ``file_id`` so that
    ``DockerImageRef._package_bundle()`` skips the pull/save/upload cycle
    and reuses the existing platform file.

    This benefits:
    - Repeat builds of the same pipeline (faster rebuilds)
    - Colleagues in the same project building other pipelines that share
      images (e.g. samtools, fastqc are used across many nf-core pipelines)
    """
    project_id = config.get("DX_PROJECT_CONTEXT_ID")
    if not project_id:
        return

    # Skip cache lookup when digest is unknown (e.g. _resolve_digest
    # failed).  Without a digest we cannot guarantee correctness of
    # the cache hit.  Also skip refs that already have a file_id (dx:// URIs).
    cacheable = [ref for ref in image_refs if ref.digest and not ref.file_id]
    if not cacheable:
        return

    _progress(f"Checking project cache for {len(cacheable)} docker image(s)...")
    cache_hits = 0
    for ref in cacheable:
        display = ref.image_name + (":" + ref.tag if ref.tag else "")
        cache_file_name = "_".join(filter(lambda x: x, [ref.image_name, ref.tag]))
        cache_folder = f"/.cached_docker_images/{ref.image_name}/"

        try:
            results = list(find_data_objects(
                classname="file",
                state="closed",
                project=project_id,
                folder=cache_folder,
                name=cache_file_name,
                properties={"image_digest": ref.digest},
                describe={"fields": {"name": True, "folder": True, "project": True}},
                limit=1,
            ))
        except Exception as e:
            log.warning(f"Docker image cache: failed to search for {display}: {e}")
            _progress(f"  {display}: SKIP (lookup error)")
            continue

        if results:
            ref.file_id = results[0]["id"]
            cache_hits += 1
            desc = results[0]["describe"]
            _progress(f"  {display}: CACHED ({desc['project']}:{desc['folder']}/{desc['name']} ({results[0]['id']}))")
        else:
            _progress(f"  {display}: MISS (will pull and upload)")

    cache_misses = len(cacheable) - cache_hits
    _progress(f"Docker image cache: {cache_hits} cached, {cache_misses} to upload")
```

## Imports of its module
```python
import dataclasses
import json
import logging
import shlex
import subprocess
import sys
import time
from typing import Optional
from dxpy import config, find_data_objects
from dxpy.nextflow.ImageRefFactory import ImageRefFactory, ImageRefFactoryError
```

## Definitions it uses from the same module
```python
log = logging.getLogger(__name__)

def _progress(msg):
    """Write user-facing progress to stderr (stdout is reserved for --json output)."""
    print(msg, file=sys.stderr, flush=True)
```

## Everything else its module defines (headers only)
```python
class _ImageRef:
def bundle_docker_images(image_refs):
def _parse_docker_ref(ref):
def _parse_dx_uri(uri):
def _docker_manifest_inspect(ref):
def _resolve_digest(full_ref, use_manifest_digest=False):
def _get_config_digest(image_ref, platform_digest):
def collect_docker_images(resources_dir, profile, nextflow_pipeline_params, use_manifest_digest=False):
```

## Signatures of what its module imports from the repository
```python
# from dxpy.nextflow.ImageRefFactory import ImageRefFactory
class ImageRefFactory(object):
    def __init__(
            self,
            image_ref
    ):
        """A class to instantiate subclasses of ImageRef based on the container engine. Ususally instantiated after using the"""
        ...
    def get_image(self):
        ...

# from dxpy.nextflow.ImageRefFactory import ImageRefFactoryError
class ImageRefFactoryError(Exception):
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_nextflow_collect_images.py:314
        mock_config.get.return_value = "project-123"
        mock_find.return_value = iter([{"id": "file-AAAA", "describe": {"name": "test-name", "project": "project-123", "folder": "/dir"}}])
        refs = [_ImageRef(process="", repository="quay.io/bio/", image_name="fastqc",
                          tag="0.12.1", digest="sha256:abc123", file_id=None, engine="docker")]
        _populate_cached_file_ids(refs)
        self.assertEqual(refs[0].file_id, "file-AAAA")
        call_kwargs = mock_find.call_args[1]
        self.assertEqual(call_kwargs["properties"], {"image_digest": "sha256:abc123"})

# src/python/test/test_nextflow_collect_images.py:333
                      tag="0.12", digest="sha256:xyz", file_id=None, engine="docker"),
            _ImageRef(process="PROC_B", repository="quay.io/bio/", image_name="fastqc",
                      tag="0.12", digest="sha256:xyz", file_id=None, engine="docker"),
        ]
        _populate_cached_file_ids(refs)
        self.assertEqual(refs[0].file_id, "file-BBBB")
        self.assertEqual(refs[1].file_id, "file-BBBB")
        self.assertEqual(mock_find.call_count, 2)

# src/python/dxpy/nextflow/collect_images.py:370
            engine="docker",
            digest_is_original=digest_is_original,
        ))

    _populate_cached_file_ids(image_refs)
    return [dataclasses.asdict(ref) for ref in image_refs]


```

Write `checks()` and `cases()` for `_populate_cached_file_ids`. Remember: setup in the thunk or at module level, never timed.