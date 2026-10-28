Let me analyze the function. `get_nextflow_src` reads a template file from `get_template_dir()` and `get_source_file_name()`. We need to understand what those return. Let me look at nextflow_utils.

We don't have the source of nextflow_utils, but we know the function reads a file at `os.path.join(get_template_dir(), get_source_file_name())`. The repository presumably ships template files. Let me check the repo structure.

The templates are likely in `src/python/dxpy/nextflow/resources/` or similar. Actually `get_template_dir()` likely returns something like `os.path.join(get_resources_dir_name(...), "nextflow")`. Hmm.

We can't know exactly. But the test file `test_nextflow.py` calls `get_nextflow_src()` and asserts `"#!/usr/bin/env bash" in src`. So the template exists in the repo. Since we run on the real repo, the template file should be present.

So the thunk can just call `get_nextflow_src(custom_inputs=..., profile=..., resources_dir=...)`. The resources_dir affects `get_resources_subpath(resources_dir)` which just returns a subpath string presumably. The heavy work is the string replacement on a large template file, plus building applet_runtime_params for each custom input.

Let me think about what "work" means. The function reads a template (a bash script), then does `.replace()` on it, and builds a string for each custom input. With many custom inputs (say 1000), building `applet_runtime_params` involves repeated string concatenation — O(n^2) potentially. That could be the heavy part.

So to make it substantial, use many custom inputs. Each with 'name' and maybe 'class'.

Also `resources_dir` — get_resources_subpath(resources_dir) — for a relative path it probably returns something. Let's just pass various strings.

Since the function doesn't mutate its arguments, thunks can return the same shared list. But wait — `custom_inputs` list is read-only (only iterated). So we can build once at module level and return it. Good.

Now, what about `get_template_dir()` — it might read an environment variable or use a package path. Let me think. In dxpy, `get_template_dir` returns `os.path.join(os.path.dirname(__file__), "resources")` maybe. Since we run in the real repo, the file exists. Let's not worry.

Actually wait, there could be a subtlety: `get_template_dir` might depend on `DX_RESOURCES_SUBPATH` or something. Let's not worry — the test calls it and it works.

Hmm, but I should double check: does `get_template_dir` use `get_resources_dir_name`? Let's look at the truncated info. We only have headers. Let's just assume the default works as in tests.

Actually, let me reconsider: the task says "if the function reads files, create them under WORKDIR". But here the function reads the repository's own template file. We can't recreate it — we shouldn't. The repository's file is used. That's fine; the function reads from the repo's resources dir.

But `resources_dir` parameter affects `get_resources_subpath(resources_dir)`. Let's check: for `resources_dir=""` maybe returns "". For a given path, returns something like `"/resources/..."`. Since it's only used in a string replacement, it doesn't read files. Good.

Now, potential issue: `get_nextflow_src` may write nothing. Fine.

Let's design cases:

1. No custom inputs, no profile: minimal work (baseline).
2. Profile only.
3. Many custom inputs with class "file" (which triggers the more expensive branch with jq/xargs string).
4. Many custom inputs with class "string" or no class.
5. Mixed.
6. Large resources_dir path.
7. Huge number of inputs (e.g., 2000).
8. Combination of all.

The heavy work: building applet_runtime_params with n inputs. String concatenation `applet_runtime_params = applet_runtime_params + '''...'''` is O(n^2) in total length. With 2000 inputs, that's maybe 2000 * average length ~ 2000*400 = 800KB copied repeatedly... Actually total sum of lengths is ~ n^2 * len_per = 2000^2*400/2 = 800MB of copying. Hmm that might be > 1s. Let's be moderate: use maybe 500-1500 inputs.

Let me estimate: each block for a file-class input is roughly:
```
        if [ -n "${name}" ]; then
            applet_runtime_inputs+=(--name "dx://${DX_WORKSPACE_ID}:/$(echo ${name} | jq .[$dnanexus_link] -r | xargs -I {} dx describe {} --json | jq -r .name)")
        fi
```
~250 chars. For n=1000, total final length ~250KB, and concatenation cost ~ n*avg_len/2*... Actually total copying = sum_{k=1}^{n} (k*250) = 250*n^2/2 = 125 * 10^6 = 125 MB for n=1000. That's maybe ~50-100ms in Python. Hmm, string concat in CPython is fairly fast.

Actually CPython has an optimization for `s = s + t` when s has refcount 1 — it can resize in place. That makes it amortized O(n). Hmm, in CPython, `str` concatenation with refcount 1 is optimized in-place. So it might be linear. Then the work is small.

Hmm. So the main work is `src.replace` on the template. The template is a bash script, maybe a few KB. Replacing 5 patterns — trivial. So the whole function might take < 1ms even with many inputs.

Well, the task says "One call should take roughly 1 ms to 200 ms". We should aim for around 1ms+ at least. With many inputs we can get there.

Let me think about what really costs: building the big applet_runtime_params string. Even if amortized linear, generating ~250KB * ... For n=5000 inputs, ~1.25MB string. That's fine, maybe 1-2 ms.

Actually, the real cost might be more subtle. Let's just use large n. But careful: the final src gets `@@APPLET_RUNTIME_PARAMS@@` replaced by the big string — that makes src ~1MB. Then the comparison of outputs — the function returns the src string. "keep what it returns under about 100 000 values" — a string of 1MB is 1 value but huge. Hmm, "values" — a string is a single value but maybe they mean characters? Let's be careful. The output is compared in full. A 1MB string is fine for comparison but might be slow-ish. Let's keep it moderate: n up to ~2000.

Actually, "keep what it returns (and anything it writes) under about 100 000 values" — I'll interpret as a string length. Hmm, risky. Let's keep src under ~500KB.

Hmm, but then the work per call is small. Let's reconsider — maybe the template file is large. Let's check: the nextflow source template is a bash script that includes nextflow.sh. It might be a few KB. Let's not overthink.

Alternatively, we could make the work substantial by using a huge resources_dir string? No, that's just one replacement.

Actually, wait. Let's reconsider `get_resources_subpath`. It might do something with paths. And `get_template_dir()` — might compute based on `resources_dir`? Let's check signature: `get_template_dir()` takes no args. `get_resources_subpath(resources_dir)`.

Hmm, what does get_template_dir return? Possibly:
```python
def get_template_dir():
    return os.path.join(os.path.dirname(__file__), "resources")
```
So the template is in the repo. Good.

Let me look at actual dx-toolkit source. I recall `nextflow_templates.py` in dxpy. The template file `nextflow_applet_template.sh` maybe in `dxpy/nextflow/resources/`. Actually let me recall: `get_template_dir()` returns `os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")`. And `get_source_file_name()` returns "nextflow.sh" maybe.

Hmm, actually I think there might be more: `get_template_dir` could return a path with a subpath determined by `get_resources_dir_name`. Let's not worry.

The key: the test calls `get_nextflow_src()` and works, so the file exists.

Now for realistic scale: the repository calls it from `nextflow_builder.py` with `custom_inputs`, `profile`, `resources_dir`. `custom_inputs` are the pipeline inputs from the nextflow schema — typically a handful to maybe dozens. But for stress, use more.

Let's design 8 cases with varying custom_inputs counts and types:

- case 1: empty custom_inputs, no profile (baseline, minimal)
- case 2: profile only
- case 3: 50 string inputs
- case 4: 50 file inputs
- case 5: 200 mixed inputs
- case 6: 500 file inputs, with profile and resources_dir
- case 7: 1000 mixed with names of varying lengths
- case 8: 2000 file inputs with long names

But we need each to take 1ms-200ms. Let's test mentally... hard. We'll aim for reasonable and let the harness pick the top 4.

Hmm, but the constraint says inputs where one call takes over 1s are dropped; and the "keep under 100000 values" for output. With n=2000 file inputs, the output src could be ~600KB. I think that's acceptable as "1 value"? The instruction is ambiguous but I'll keep n moderate to be safe.

Actually, let me reconsider. The template file — how big? Let me think about what the template contains. It's the applet source template that gets built into the applet's exec. It includes the nextflow.sh content? Actually `@@APPLET_RUNTIME_PARAMS@@`, `@@PROFILE_ARG@@`, `@@EXCLUDE_INPUT_DOWNLOAD@@`, `@@DXPY_BUILD_VERSION@@`, `@@RESOURCES_SUBPATH@@`. These are placeholders in a bash script template. The template is probably ~100-300 lines of bash. So ~5-10KB.

The `.replace` on a 10KB string is trivial. So the only scalable work is building applet_runtime_params.

Let's estimate more carefully the string building. Each input adds:
```
\n        if [ -n "${NAME}" ]; then\n            applet_runtime_inputs+=(--NAME "VALUE")\n        fi\n        
```
For non-file: VALUE = "${NAME}". Block length ~ 90 + 2*len(NAME).
For file: VALUE is long ~150 chars. Block length ~ 250 + len(NAME).

With n=2000 file inputs and names ~10 chars, final string ~ 520KB. Building it: if in-place optimization applies, cost ~ O(total length) ~ 520K char copies, ~0.5ms. If not optimized, ~ n * avg_len = 2000*260K = 520M char copies, ~0.5s. Hmm, that's a big difference.

CPython's in-place concat optimization: in `ceval.c`, `unicode_concatenate` checks if the left operand has refcount 1 and is not interned/shared, then resizes in place. `applet_runtime_params = applet_runtime_params + '''...'''` — the left operand is the local variable, refcount... during evaluation of `+`, the reference from the stack and the local both point to it? Actually when evaluating `applet_runtime_params + X`, the compiler loads `applet_runtime_params` (incref, so refcount 2), then loads X, then BINARY_ADD. Hmm, refcount would be 2. Then optimization doesn't apply? Actually the optimization checks `Py_REFCNT(left) == 1`? Hmm.

Actually CPython has `unicode_concatenate` which does in-place resize if `PyUnicode_CheckExact(left) && Py_REFCNT(left) == 1 && PyUnicode_CheckExact(right) && PyUnicode_CheckExact(v)`. During BINARY_ADD, the two stack references... the left is on the stack (refcount includes stack ref) plus... hmm. Actually when you do `a = a + b`, at the time of BINARY_ADD, `a` is referenced by the local var and by the stack. So refcount is 2. So the optimization wouldn't fire? But in practice CPython does optimize `a += b` and also `a = a + b`? Let me recall: The optimization for `str +=` is real. For `a = a + b`, I believe the same optimization applies because the local is loaded onto the stack (the local slot's ref is stolen? No...).

Hmm, in CPython 3.10+, `a = a + b` is optimized into `a += b` by the compiler (BINARY_ADD specialization). Actually there's a peephole optimization? Not sure.

Let's not rely on it. Even if it's O(n^2) with n=1000, that's 125M char copies ~ 0.1-0.3s. Could exceed... no, under 1s.

Hmm, this is getting too speculative. Let's just pick a range of sizes and let the harness pick top 4. Include sizes like 20, 100, 300, 800, 1500, 3000.

Actually, wait. The output constraint: "keep what it returns under about 100 000 values". If they literally count characters, 3000 inputs → ~800KB output → violates. If they count "values" as elements... a string is one value. I'll interpret conservatively and keep the returned string under ~100K chars. That means n up to ~300 file inputs (~78KB) or ~800 string inputs (~80KB).

Hmm, but then the work is tiny. Let's think: is there a way to make each call do more work while keeping output small? The output is `src` which contains applet_runtime_params. So output size scales with n. To keep output < 100K, n < ~350.

With n=350 file inputs, output ~90KB. Building cost: if O(n^2), 350^2*130 = 16M char copies, ~10ms. If O(n), ~1ms. Either way, within 1-200ms.

Hmm, but then all cases are similar in time. The harness picks top 4 by work. Fine.

Actually, I wonder if the instruction "under about 100 000 values" is really about characters. Let me re-read: "The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values." I think "values" means like list elements / dict entries. For a string... ambiguous. I'll be somewhat conservative but not paranoid. Let's cap returned src at ~200KB. Actually let's just keep it reasonable — a few hundred KB is fine for string comparison.

Hmm, I'll go with max ~500 file inputs → ~130KB output. Reasonable.

Actually, you know what, let's reconsider the whole thing. Maybe I'm wrong about the template size. Let me try to recall the actual file. In dx-toolkit, `src/python/dxpy/nextflow/resources/` contains `nextflow.sh`, `nextflow_applet_template.sh`? Hmm.

Actually `get_source_file_name()` — the name of the source file. In test: `src = get_nextflow_src()` asserts `"#!/usr/bin/env bash" in src`. The applet source is a bash script.

I recall the file `nextflow_templates.py` has:
```python
def get_template_dir():
    return os.path.join(get_resources_dir_name(), "nextflow")
```
Hmm no.

Actually let me think about `get_resources_subpath(resources_dir)` — returns subpath. And `get_resources_dir_name(resources_dir)` returns dir name. These deal with the applet resources dir.

OK. I'll just trust it works.

Now: important — `get_template_dir()` might depend on the current working directory or environment. If it uses `os.path.dirname(__file__)`, fine. If it uses a relative path from cwd... The tests run from the repo root probably. Let's assume it's robust since tests call it.

Hmm, but actually there's a risk: `get_template_dir` might read `DX_RESOURCES_SUBPATH` env or use `get_resources_dir_name`. Let's look at the real code.

Let me recall dx-toolkit `nextflow_utils.py`:

```python
def get_resources_dir_name(resources_dir=None):
    if resources_dir:
        return os.path.basename(resources_dir)
    return "resources"

def get_resources_subpath(resources_dir=None):
    if resources_dir:
        return os.path.join("resources", os.path.basename(resources_dir))
    return ""

def get_template_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
```

Something like that. And `get_source_file_name()` returns "nextflow.sh"? Hmm, but then it would read a file named nextflow.sh.

Hmm, actually I think there might be a template file `nextflow_applet_template.sh`. Let's not worry — whatever it is, it exists.

Wait, actually, I should be careful: does `get_source_file_name` maybe return something that depends on... no, no args.

OK let's just write it.

Now, one more concern: the function reads the template from the repo. But `get_template_dir()` might be affected by our `resources_dir` parameter? No, it takes no args.

Now `get_resources_subpath(resources_dir)`: if resources_dir is a relative path like "my_resources", it returns "resources/my_resources" or similar. Doesn't read files. Good.

Let me now write the code.

```python
import os
import random
from dxpy.nextflow.nextflow_templates import get_nextflow_src

_CLASSES = [None, "string", "int", "float", "file", "boolean"]

def _make_inputs(n, seed, file_ratio=0.5, name_len=12):
    rng = random.Random(seed)
    inputs = []
    for i in range(n):
        name = "input_%d_%s" % (i, "x" * rng.randint(0, name_len))
        inp = {"name": name}
        if rng.random() < file_ratio:
            inp["class"] = "file"
        else:
            inp["class"] = rng.choice(["string", "int", "float", "boolean"])
        inputs.append(inp)
    return inputs
```

Wait, but for the file branch, `i.get("class") == "file"`. For others, value = "${name}". Good.

Also, real nextflow schema inputs might have more keys (description, default, etc.) but the function only reads 'name' and 'class'. Fine.

Now cases:

```python
_CASES_DATA = ...
def cases():
    return [
        ("empty", lambda: ()),
        ("profile-only", lambda: (None, "test_profile")),
        ("few-strings", lambda: (_make_inputs(5, 0, 0.0),)),
        ...
    ]
```

Wait, careful: the function signature is `get_nextflow_src(custom_inputs=None, profile=None, resources_dir=None)`. Thunk returns positional args tuple. `lambda: ()` calls with no args → custom_inputs=None → [].

For profile: `lambda: (None, "test_profile")`.

For resources_dir: `lambda: (inputs, None, "/some/dir")`.

Let's define module-level input lists once and reuse (function doesn't mutate them).

Build:

- `_empty = []`
- `_small_mixed = _make_inputs(10, 1)`
- `_med_files = _make_inputs(100, 2, file_ratio=1.0)`
- `_med_mixed = _make_inputs(150, 3, file_ratio=0.5)`
- `_big_files = _make_inputs(300, 4, file_ratio=1.0, name_len=30)`
- `_big_mixed = _make_inputs(400, 5, file_ratio=0.5, name_len=25)`
- `_huge_strings = _make_inputs(600, 6, file_ratio=0.0, name_len=40)`
- `_huge_files = _make_inputs(500, 7, file_ratio=1.0, name_len=50)`

Hmm, but output size. For 600 string inputs with names ~40 chars: each block ~ 90+2*40=170 chars, total ~102KB. Plus template ~10KB. Slightly over 100K. Let's reduce.

Actually let me reconsider the output constraint more. "keep what it returns ... under about 100 000 values". A string is 1 value. I think comparing two 100KB strings is fine. The concern about "values" is probably for lists/dicts. I'll allow up to a few hundred KB. But to be safe, let's cap around 300KB.

Hmm, let me just go moderate. Total n across cases up to ~400.

Actually, let's think about whether we can get more work with smaller output. The `.replace` calls operate on the template. The template is small. Hmm.

Alternatively — `resources_dir` could be a very long string, making `get_resources_subpath` do work? No.

OK, sizes: I'll use up to ~400 inputs.

Let me reconsider: maybe the template file is actually big! Let me think... The applet source template might include the entire nextflow.sh script inline. Could be 10-50KB. Whatever.

Let me write it with diverse cases:

1. `empty`: no inputs, no profile, no resources_dir. (minimal)
2. `profile`: no inputs, profile="test_profile".
3. `few-file`: 10 file inputs, no profile.
4. `mixed-100`: 100 mixed inputs, profile="docker", resources_dir="my_resources".
5. `files-200`: 200 file inputs with long names.
6. `strings-300`: 300 non-file inputs.
7. `mixed-400-profile-resources`: 400 mixed, profile, resources_dir absolute path.
8. `files-400-longnames`: 400 file inputs, name_len 60.

That gives variety.

Now checks (2-3 small edge inputs, may raise):
- empty: `lambda: ()` → custom_inputs=None.
- empty list: `lambda: ([],)`.
- input missing 'name'? That would raise KeyError. Is that OK? "These may raise." Yes. But better to use something that behaves. Let's use `lambda: ([{"name": "x"}],)` (no class → string branch) and `lambda: ([{"class": "file"}],)` which raises KeyError (missing 'name'). Hmm, "checked only for identical behaviour" — both original and modified run, compare. Raising is fine if both raise identically. But if the modification changes behavior... Let's include one that raises? The instructions say "empty, one element, None, an odd type". So:
  - ("none", lambda: (None,))
  - ("empty-list", lambda: ([],))
  - ("single-file", lambda: ([{"name": "f", "class": "file"}],))

Actually a single element with class file is a good edge. And maybe one with no class.

Let me use 3 checks.

Now, potential issue: `get_nextflow_src` might have side effects? No.

Another concern: does the template file exist? If `get_template_dir()` returns a path relative to cwd, and our harness runs from a different cwd, it could fail. But tests in the repo call it, so presumably it's absolute based on `__file__`. Let's trust.

Hmm, wait. Actually I want to double-check by recalling the real code. Let me search memory: dx-toolkit `src/python/dxpy/nextflow/nextflow_utils.py`:

```python
def get_template_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
```

Hmm, actually I have a vague memory that there's a `get_resources_dir_name` used for applet resources. And templates are under `dxpy/nextflow/resources/`.

I'm fairly confident.

Actually hold on, there's another possibility: `get_template_dir()` might use `get_resources_dir_name(resources_dir)` but takes no args, so returns the default "resources". Fine.

Let me also consider: could `get_template_dir` read an environment variable like `DX_NEXTFLOW_TEMPLATE_DIR`? Possibly not.

OK, writing the final code.

One more: the function's `resources_dir` affects only `get_resources_subpath`. Let's pass realistic values: "", "my_applet_resources", "/abs/path/to/resources".

Let me finalize.

```python
import os
import random

from dxpy.nextflow.nextflow_templates import get_nextflow_src


def _make_inputs(n, seed, file_ratio=0.5, name_len=12):
    rng = random.Random(seed)
    classes = ["string", "int", "float", "boolean", "map"]
    inputs = []
    for i in range(n):
        name = "input_{}_{}".format(i, "x" * rng.randint(0, name_len))
        inp = {"name": name}
        if rng.random() < file_ratio:
            inp["class"] = "file"
        else:
            inp["class"] = rng.choice(classes)
        inputs.append(inp)
    return inputs


_EMPTY = []
_FEW_FILE = _make_inputs(10, 1, file_ratio=1.0, name_len=8)
_MIXED_100 = _make_inputs(100, 2, file_ratio=0.5, name_len=15)
_FILES_200 = _make_inputs(200, 3, file_ratio=1.0, name_len=25)
_STRINGS_300 = _make_inputs(300, 4, file_ratio=0.0, name_len=30)
_MIXED_400 = _make_inputs(400, 5, file_ratio=0.5, name_len=20)
_FILES_400 = _make_inputs(400, 6, file_ratio=1.0, name_len=40)
_MIXED_150 = _make_inputs(150, 7, file_ratio=0.7, name_len=12)
```

Hmm, that's 7 lists + empty. Cases need exactly 8.

Cases:
1. empty: `lambda: (_EMPTY,)`
2. profile-only: `lambda: (_EMPTY, "test_profile")`
3. few-file: `lambda: (_FEW_FILE,)`
4. mixed-100: `lambda: (_MIXED_100, "docker", "my_resources")`
5. files-200: `lambda: (_FILES_200,)`
6. strings-300: `lambda: (_STRINGS_300, "test_profile", "/abs/path/resources")`
7. mixed-400: `lambda: (_MIXED_400, "docker")`
8. files-400: `lambda: (_FILES_400, "test_profile", "my_resources")`

Good, 8 distinct.

Wait — case 2 uses `_EMPTY` shared with case 1. Fine, no mutation.

Now checks:
```python
def checks():
    return [
        ("none-args", lambda: (None,)),
        ("empty-list", lambda: (list(_EMPTY),)),
        ("single-file", lambda: ([{"name": "reads", "class": "file"}],)),
    ]
```

Hmm, `lambda: (None,)` — passes custom_inputs=None. Good. Actually let's also include profile="" maybe. Keep it 3.

Wait, the function signature: passing `(None,)` means custom_inputs=None, others default. Good.

Now, about the "one element" and "None" and "odd type" — maybe include an odd type like a tuple instead of list? `custom_inputs=()` would iterate fine. Or a dict? That would iterate keys (strings) and then `i['name']` would fail on str → TypeError. Both original and modified would raise TypeError. Could be fine but risky. Let's stick to safe ones.

Let me double check the `_make_inputs` with `file_ratio=0.0` gives class in ["string","int","float","boolean","map"], all non-file → value = "${name}". Good.

For class "file", the branch uses `i['name']` and builds the long value. Good.

Now, do I need to worry about the template file? Let's just go.

Actually, one thing: `get_resources_subpath(resources_dir)` — with resources_dir="my_resources" (relative) — might do `os.path.join` — fine.

Let me also make sure importing works: `from dxpy.nextflow.nextflow_templates import get_nextflow_src`. The task says import exactly as shown. Good.

Potential issue: importing `dxpy.nextflow.nextflow_templates` might require `dxpy` package to be importable (setup). The test imports it. Should be fine.

Final code below.

Actually, let me reconsider whether the returned string could be large. For `_FILES_400` with name_len up to 40: each block for file class is roughly:

```
\n        if [ -n "${NAME}" ]; then\n            applet_runtime_inputs+=(--NAME "dx://${DX_WORKSPACE_ID}:/$(echo ${NAME} | jq .[$dnanexus_link] -r | xargs -I {} dx describe {} --json | jq -r .name)")\n        fi\n        
```

Let me count: The value string: `"dx://${DX_WORKSPACE_ID}:/$(echo ${NAME} | jq .[$dnanexus_link] -r | xargs -I {} dx describe {} --json | jq -r .name)"`. That's about 120 chars + 2*len(NAME). Plus surrounding: `\n        if [ -n "${NAME}" ]; then\n            applet_runtime_inputs+=(--NAME "VALUE")\n        fi\n        ` ~ 80 + 2*len(NAME).

Total per file input ~ 200 + 4*len(NAME). With name ~20 avg, ~280 chars. 400 inputs → 112KB. Plus template. ~120KB output. That's a bit over 100K but I think acceptable.

For `_MIXED_400`: half file → ~200*280 + 200*(90+2*20) = 56K + 26K = 82KB. OK.

Alright. Total maybe fine.

Hmm, let me reduce files-400 name_len to 30 to be safer. Actually it's fine.

Let me write it.

Also note: `_make_inputs` uses rng.choice on a list — fine, seeded.

One more consideration: the thunk must be cheap. Returning a module-level list is cheap. Good.

Write final answer.