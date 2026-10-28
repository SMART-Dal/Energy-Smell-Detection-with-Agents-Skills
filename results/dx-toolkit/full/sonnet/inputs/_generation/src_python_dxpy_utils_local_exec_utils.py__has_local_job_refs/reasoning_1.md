We need to write inputs for `has_local_job_refs(io_hash)`.

The function walks a nested structure of dicts/lists, checking each value: if `is_job_ref(value)` then check `get_job_from_jbor(value).startswith('localjob')` → return True. Else if list/dict, push to queue.

We need to know what `is_job_ref` and `get_job_from_jbor` consider a job ref. From dxpy describe module:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    ...
```

Let me recall the actual dxpy code. In dxpy/utils/describe.py:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

And get_job_from_jbor:

```python
def get_job_from_jbor(thing):
    """
    :returns: Job ID from a JBOR
    """
    if not is_job_ref(thing):
        return None
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link']
    else:
        return thing['$dnanexus_link']['job']
```

Hmm, but I shouldn't rely on memory too heavily — but the task says build inputs from the classes and functions shown. We know is_job_ref checks for a dict with '$dnanexus_link'. We can just construct dicts with `$dnanexus_link` keys.

Actually let's be careful: is_job_ref may check `'$dnanexus_link' in thing`. Let's construct both forms: string link and dict link with 'job'.

Let me check the actual dxpy source for describe.py to be accurate. I recall:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, actually I think it's:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

And get_job_from_jbor:

```python
def get_job_from_jbor(thing):
    """
    :returns: Job ID from a JBOR
    """
    if not is_job_ref(thing):
        return None
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link']
    else:
        return thing['$dnanexus_link']['job']
```

Hmm, wait — actually I think is_job_ref requires the link to be a dict with 'job'. Let me think again. In dxpy, a JBOR looks like:

```json
{"$dnanexus_link": {"job": "job-xxxx", "field": "output_field", "index": 0}}
```

or

```json
{"$dnanexus_link": "job-xxxx"}
```

I believe both forms are supported. The `get_job_from_jbor` returns the job id.

Since we don't have the exact source, we should construct inputs that work either way. The safest: use dict form `{"$dnanexus_link": {"job": "job-..."}}`. If is_job_ref only accepts dict-with-job, that works. If it accepts string too, dict-with-job also works (since it checks 'job' in the dict).

Actually wait, if is_job_ref checks `isinstance(thing['$dnanexus_link'], dict) and 'job' in ...`, then dict form works. If it checks string form, dict form might fail. But the dict form is the standard JBOR. Let's use it.

Hmm, but to be safe, maybe we can test both forms in different cases. But if the string form isn't recognized as a job ref, then the function would just treat it as a plain dict and recurse into it (it's a dict, so it gets appended to q). That's fine — no error, just different work. But we want cases that exercise the "return True" path.

Actually, the key question: we want cases where `has_local_job_refs` returns True (found localjob ref) and cases where it returns False (no refs).

Let's design:

- `is_localjob_id(thing)` — from resolver. Local job IDs start with 'localjob'. So a job id like `'localjob-xxxx'`.

Let's look at get_job_from_jbor — returns the job id string. `startswith('localjob')`.

So a JBOR for a local job: `{"$dnanexus_link": {"job": "localjob-0000"}}`.

Now design 8 cases with realistic scale. The function is called in a loop `while has_local_job_refs(...)` — so it's called repeatedly. The io_hash is a dict of input/output hashes. Realistic: nested dicts with lists of file links, etc.

Let's design cases:

1. **Deeply nested, no job refs, large** — returns False. Many nested dicts/lists with plain values.
2. **Local job ref at top level** — returns True quickly.
3. **Local job ref deeply nested in a list** — returns True after some traversal.
4. **Non-local job refs (job-xxxx) nested deeply, no local** — returns False, but exercises the `get_job_from_jbor` path.
5. **Mixed: many non-local refs, one local ref at the end** — returns True.
6. **Wide dict with many keys** — returns False.
7. **Large list of dicts** — returns False.
8. **Empty-ish / small** — but we need substantial work.

Wait, we need each case to take roughly 1ms to 200ms. The function is pure Python traversal, so we need a lot of elements. Let's estimate: a simple loop over ~100k elements in Python takes ~10ms. So we want maybe 50k-500k elements per case.

But constraint: "keep each input's data under about 1 000 000 values" and "keep what it returns ... under about 100 000 values". The function returns a boolean, so fine.

Let's build data structures with maybe 100k-300k leaf values.

Careful: the function's traversal. For a dict, it iterates fields; for each field, if is_job_ref → check; elif list/dict → append to q. Then pops from q and processes. So it's a DFS/BFS traversal of the nested structure. Each leaf (non-container) value that's not a job ref is just skipped.

So to make it do work, we need many nested containers and many job-ref-like dicts.

Note: `is_job_ref` is called on every value. So even plain values cause a call. For a dict `{"a": 1}`, is_job_ref(1) → isinstance(1, dict) is False → returns False quickly.

To maximize work, use many small dicts and lists.

Let me design:

Case A: "deep-nesting-no-refs": a deeply nested structure (depth ~50) with lists/dicts, no job refs. Returns False. But deep nesting alone with few nodes is fast. We need many nodes.

Better: build a wide structure with many nested containers.

Let's think about realistic input from the repo: `entry_point['input_hash']` is a dict mapping input names to values, where values can be file links, arrays, nested dicts. So typical: a dict with ~10-100 keys, values are lists of file links or nested dicts.

To make it heavy, we can have a dict with many keys each mapping to a list of many items.

Let's write helper functions.

```python
import random
from dxpy.utils.local_exec_utils import has_local_job_refs

def _jbor(job_id, field=None, index=None):
    link = {"job": job_id}
    if field is not None:
        link["field"] = field
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}
```

Hmm, but we need to be careful: if is_job_ref requires `'$dnanexus_link'` to be a string OR dict with 'job', our dict form works. If it requires the link to be a string, then our dict form is not a job ref and the function would recurse into it as a plain dict. That would still run (no error), but the "return True" cases wouldn't return True. But the task says the function's output is compared — the original and modified version must produce the same output. As long as both produce the same, it's fine. But we want to exercise the `get_job_from_jbor` path.

Let me try to recall the actual dxpy describe.py. I'm fairly confident:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, actually I now recall it might be simpler:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Let me search my memory of the actual file. dxpy/utils/describe.py:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

I'll go with the dict-with-job form as the primary, and maybe also include string form in some cases. Actually, to be safe and exercise both, I can include both forms. If the string form isn't recognized, it's treated as a dict and recursed — no error.

Hmm, but there's a subtlety: if the string form `{"$dnanexus_link": "job-xxx"}` is not recognized as a job ref, then the function will treat it as a dict and push it to q, then iterate its fields: field = "$dnanexus_link", value = "job-xxx". is_job_ref("job-xxx") → False. Then it's not a list/dict. So nothing. Fine.

Let me just use the dict form for job refs. And maybe include some string-form ones as "plain dicts" to add variety.

Actually, I want to be careful about `get_job_from_jbor` returning None for non-job-refs. In the function, `get_job_from_jbor` is only called after `is_job_ref` returns True. So it's fine.

Now, let's design the cases.

We need 8 cases. Let's think about what makes different work:

1. Large flat dict with many keys, no refs → returns False. Work: iterate all keys.
2. Large flat dict with many keys, one local job ref at the end → returns True.
3. Nested structure: dict of lists of dicts, no refs → returns False.
4. Nested structure with a local job ref deep inside → returns True.
5. Many non-local job refs (job-xxxx) → returns False (all checked via get_job_from_jbor, startswith fails).
6. Mixed: many non-local refs and one local ref → returns True.
7. Very deep nesting (depth 100+) with no refs → returns False.
8. Wide list of many items, some dicts, some refs → returns True or False.

Let's make each case substantial: ~50k-200k leaf values.

Let me write a helper to build a nested structure.

```python
def _plain_value(rng):
    return rng.choice([rng.randint(0, 10**6), "s" + str(rng.randint(0, 10**6)), None, True, 3.14])
```

Hmm, but random values might be slow to generate. Let's keep it simple.

Actually, generating 200k random values with random.Random is fast enough (< 1s).

Let me design a builder:

```python
def _make_nested(depth, breadth, rng, job_ref_prob=0.0, local_job_prob=0.0, job_id_prefix="job"):
    ...
```

Maybe simpler to write each case explicitly.

Let me think about the traversal cost. For a dict with N keys where each value is a plain int: the function iterates N fields, calls is_job_ref on each (isinstance check + `in` check). That's maybe ~0.5 µs per key. For 200k keys, ~100ms. Good.

But wait, a single dict with 200k keys — the function's first loop iterates all fields. That's fine.

Actually, `is_job_ref(thing)` where thing is an int: `isinstance(thing, dict)` → False, return False. Fast.

For a dict value that is itself a dict, is_job_ref checks `'$dnanexus_link' in thing` → False, then it's a dict → append to q. Then processed later.

So nested dicts cause more work.

Let me design:

**Case 1: "flat-dict-no-refs"**
```python
d = {f"field_{i}": i for i in range(200_000)}
```
Returns False. Work: 200k is_job_ref calls.

Hmm, but the task says avoid uniformity/patterns that a simple trick could exploit. A flat dict with sequential keys is a pattern. But the function doesn't exploit patterns — it just iterates. Still, let's add some variety: mix of ints, strings, None, floats, lists, dicts.

Actually, the concern about patterns is more about the function under test being able to shortcut. Here the function has no shortcut. But let's still add variety for realism.

Let's make a realistic input_hash: a dict mapping input names to values. Values are typically file links (`{"$dnanexus_link": "file-xxxx"}`), arrays, or plain values.

Let me write:

```python
def _rand_value(rng, depth=0):
    r = rng.random()
    if depth > 3 or r < 0.5:
        return rng.choice([rng.randint(0, 10**9), "str_" + str(rng.randint(0, 10**9)), None, 1.5, True])
    elif r < 0.75:
        return [_rand_value(rng, depth+1) for _ in range(rng.randint(1, 5))]
    else:
        return {f"k{j}": _rand_value(rng, depth+1) for j in range(rng.randint(1, 5))}
```

But this could generate a lot of nodes. Let's control.

Hmm, this is getting complex. Let me think about what's realistic and what makes good cases.

Actually, the key thing: the function is called in a `while has_local_job_refs(...)` loop, meaning it's called repeatedly until no local job refs remain. So the input_hash typically contains local job refs that get resolved. So realistic inputs DO contain local job refs.

But for our measurement, we just need diverse inputs.

Let me design 8 cases with a mix:

1. **no-refs-large**: large nested structure, no job refs at all. Returns False.
2. **local-ref-top**: large structure with a local job ref at the top level (early return True).
3. **local-ref-deep**: large structure with a local job ref deep inside (late return True).
4. **nonlocal-refs-only**: many non-local job refs, no local. Returns False.
5. **mixed-refs**: many non-local refs + one local ref. Returns True.
6. **wide-list**: a big list of items (dicts, refs). 
7. **deep-nesting**: very deep nesting.
8. **many-small-dicts**: many small dicts.

Let me now write the code.

First, I need to know the structure of a job ref. Let me define:

```python
def _jbor(job_id, field="out", index=None):
    link = {"job": job_id, "field": field}
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}
```

And a file link (not a job ref, but a plain dict):
```python
def _file_link(file_id):
    return {"$dnanexus_link": file_id}
```
Wait — if is_job_ref accepts string links, then `{"$dnanexus_link": "file-xxxx"}` would be considered a job ref! And get_job_from_jbor would return "file-xxxx", which doesn't start with 'localjob'. So it's treated as a non-local job ref. That's fine — it exercises the get_job_from_jbor path.

Hmm, but if is_job_ref only accepts dict-with-job, then `{"$dnanexus_link": "file-xxxx"}` is not a job ref, and it's a dict, so it gets pushed to q and its fields iterated. Also fine.

Either way, no error.

Let me be careful about `get_job_from_jbor` returning None if is_job_ref is True but the structure is unexpected. For the string form, get_job_from_jbor returns the string. For the dict form, returns link['job']. So both fine.

Now, let me write the cases.

I'll use a module-level RNG and build data once.

```python
import random
from dxpy.utils.local_exec_utils import has_local_job_refs

def _jbor(job_id, field="out", index=None):
    link = {"job": job_id, "field": field}
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}

def _file_link(file_id):
    return {"$dnanexus_link": file_id}

def _plain(rng):
    return rng.choice([rng.randint(0, 10**9), "v" + str(rng.randint(0, 10**9)), None, 1.5, True, False])
```

Now, case builders.

**Case 1: no-refs-large**
Build a dict with 1000 keys, each mapping to a list of 100 plain values. Total 100k leaves. Plus some nested dicts.

Actually, let's build a more structured realistic input_hash:

```python
def _build_flat_dict(n, rng):
    d = {}
    for i in range(n):
        r = rng.random()
        if r < 0.7:
            d[f"field_{i}"] = _plain(rng)
        elif r < 0.85:
            d[f"field_{i}"] = [_plain(rng) for _ in range(rng.randint(1, 5))]
        else:
            d[f"field_{i}"] = {f"sub_{j}": _plain(rng) for j in range(rng.randint(1, 5))}
    return d
```

With n=100_000, this creates ~100k top-level keys, plus nested. Total values maybe 200k. The function's first loop iterates 100k fields; for the ~15% that are lists/dicts, they get pushed and processed later. So total work ~200k is_job_ref calls. Should be ~50-100ms.

Hmm, but generating 100k random values might take ~0.5s. That's fine (under 10s for all).

**Case 2: local-ref-top**
Same structure but with a local job ref as one of the first keys. Returns True immediately (well, after iterating until it hits that key).

Actually, if the local ref is the first key, the function returns True after 1 iteration. That's too fast — we want substantial work. So put the local ref at the end.

Let's put it at the last key. Then the function iterates all 100k keys, then returns True. Similar work to case 1.

**Case 3: local-ref-deep**
A local ref buried deep in a nested structure. The function traverses the whole structure before finding it.

**Case 4: nonlocal-refs-only**
Many non-local job refs. Each triggers get_job_from_jbor. Returns False.

**Case 5: mixed**
Many non-local refs + one local ref at the end. Returns True.

**Case 6: wide-list**
A big list containing many items. The function's first loop: `for field in io_hash` — if io_hash is a dict, it iterates keys. Wait, the function expects io_hash to be a dict (it does `for field in io_hash: ... io_hash[field]`). If io_hash is a list, `for field in io_hash` iterates elements, and `io_hash[field]` would fail (list indices must be integers). So io_hash must be a dict.

Actually, the function signature says `io_hash: dict`. So all cases must pass a dict.

But the dict can contain lists. So "wide list" means a dict with a key mapping to a big list.

**Case 6: big-list-value**
`{"inputs": [list of 200k items]}`. The function: first loop, field="inputs", value is a list → not a job ref → pushed to q. Then while loop: pop the list, iterate 200k items, each is_job_ref check. Returns False.

**Case 7: deep-nesting**
A deeply nested structure (depth ~200) where each level is a dict with one key. The function pushes each level to q and processes. Depth 200 → 200 iterations. That's fast. To make it slow, we need many nodes. Let's make a structure that's deep AND wide: e.g., a binary tree of depth 15 → 32k leaves. Or a tree where each node has 3 children.

Let's build a tree: each node is a dict with k keys, each value either a leaf or a subtree. Depth d, branching b → b^d leaves. With b=4, d=8 → 65536 leaves. Total nodes ~87k. The function traverses all.

**Case 8: many-small-dicts**
A dict with 50k keys, each mapping to a small dict with 3 keys. Total ~200k values.

OK, let's also think about the `checks()` function: 2-3 small edge inputs.

- empty dict: `{}` → returns False.
- dict with a local job ref: `{"a": {"$dnanexus_link": {"job": "localjob-0001"}}}` → True.
- dict with None value: `{"a": None}` → False.
- Maybe a dict with a nested list containing a local ref.

These are checked for identical behavior, not measured.

Now, let's be careful about the job ref format. Let me try to verify by looking at the actual dxpy code. Since I can't access the internet, I'll rely on the description.

The function uses `is_job_ref(io_hash[field])` and `get_job_from_jbor(io_hash[field])`. From the imports, `is_job_ref` and `get_job_from_jbor` are from `.describe`.

I'm fairly confident about the dict-with-job form. Let me also consider: maybe is_job_ref requires the link to be a dict with 'job' AND the reftype is dict. So `{"$dnanexus_link": {"job": "job-xxx"}}` works.

Let me also consider that `is_job_ref` might have a `reftype` parameter defaulting to dict, and it checks `isinstance(thing, reftype)`. So thing must be a dict.

OK. Let me write the code.

Actually, let me reconsider the string form. In dxpy, a JBOR can be:
- `{"$dnanexus_link": "job-xxxx"}` (simple)
- `{"$dnanexus_link": {"job": "job-xxxx", "field": "output", "index": 0}}` (full)

I believe `is_job_ref` checks for both. Let me include both forms in different cases to exercise both paths.

Hmm, but if the string form is not recognized, it's treated as a plain dict. That's fine.

Wait, actually there's a risk: if `is_job_ref` checks `isinstance(thing['$dnanexus_link'], basestring)` and returns True, then `get_job_from_jbor` returns the string. If the string is "file-xxxx", it doesn't start with 'localjob', so it's a non-local ref. Fine.

Let me now write the code.

```python
import random
from dxpy.utils.local_exec_utils import has_local_job_refs


def _jbor(job_id, field="out", index=None):
    link = {"job": job_id, "field": field}
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}


def _simple_jbor(job_id):
    return {"$dnanexus_link": job_id}


def _file_link(file_id):
    return {"$dnanexus_link": file_id}


def _plain(rng):
    return rng.choice([rng.randint(0, 10**9), "v" + str(rng.randint(0, 10**9)), None, 1.5, True, False])
```

Now builders.

```python
def _build_flat(n, rng, local_ref_at=None, nonlocal_ref_ratio=0.0):
    d = {}
    for i in range(n):
        key = f"field_{i}"
        if local_ref_at is not None and i == local_ref_at:
            d[key] = _jbor("localjob-%04d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%04d" % i)
        else:
            r = rng.random()
            if r < 0.6:
                d[key] = _plain(rng)
            elif r < 0.8:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            else:
                d[key] = {f"sub_{j}": _plain(rng) for j in range(rng.randint(1, 4))}
    return d
```

Hmm, this is a bit ad-hoc. Let me structure it better.

Actually, let me think about the "distinct labels" requirement — each case has a distinct label. Fine.

Let me also think about the total data size. "Keep the data in memory under about 100 MB". 200k values × ~100 bytes each (Python object overhead) = 20 MB. Fine.

Let me now write each case explicitly.

I'll define module-level data:

```python
_rng = random.Random(0)
```

But wait — the task says "a fixed random seed (`random.Random(0)`) when generating data". So use `random.Random(0)`.

Let me build the data at module level so thunks are cheap.

Actually, the thunks return the arguments. If the function doesn't modify the input, we can return the same object each time. Does `has_local_job_refs` modify io_hash? Looking at the code: it only reads. It appends sub-containers to a local queue `q`. It doesn't modify io_hash. So we can return the same object.

But wait — the task says "Its arguments are rendered before and after each call to see whether it changed them". So we need to make sure the function doesn't change them. It doesn't. Good.

So thunks can just return the pre-built dict.

Let me write:

```python
def _build_case1():
    rng = random.Random(1)
    d = {}
    for i in range(80_000):
        r = rng.random()
        if r < 0.6:
            d[f"f{i}"] = _plain(rng)
        elif r < 0.8:
            d[f"f{i}"] = [_plain(rng) for _ in range(rng.randint(1, 4))]
        else:
            d[f"f{i}"] = {f"s{j}": _plain(rng) for j in range(rng.randint(1, 4))}
    return d
```

This creates 80k top-level keys. The function iterates 80k fields, pushes ~20% (16k) to q, then processes those. Total ~80k + 16k*avg(2.5) = ~120k is_job_ref calls. Maybe ~30ms. Good.

Hmm, actually let me reconsider. The `is_job_ref` call for a plain value: `isinstance(thing, dict)` → False. Very fast, maybe 0.1 µs. For 120k calls, ~12ms. Plus the loop overhead. Maybe 20-30ms. That's within 1-200ms.

Let's aim for ~100-200k top-level keys to be safe.

Actually, let me benchmark mentally: a Python for loop with a function call takes ~100ns per iteration minimum. 200k iterations → 20ms. With the is_job_ref call (which does isinstance and `in`), maybe 200ns → 40ms. Plus the dict lookups. So 200k keys → ~50-80ms. Good.

Let me use 150k top-level keys for the big cases.

But generating 150k random values: `rng.random()` and `rng.choice` are fast. ~150k × few µs = maybe 0.5s. Fine.

Let me write the builders.

Actually, let me simplify and write a generic builder that takes parameters.

```python
def _build_hash(n_keys, rng, local_ref_positions=(), nonlocal_ref_ratio=0.0, nested=True):
    d = {}
    local_set = set(local_ref_positions)
    for i in range(n_keys):
        key = "field_%d" % i
        if i in local_set:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        else:
            r = rng.random()
            if nested and r < 0.15:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif nested and r < 0.25:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d
```

Hmm, but for cases where we want a local ref deep inside, we need a different builder.

Let me write specific builders for each case.

**Case 1: "large-no-refs"** — 150k keys, no refs, some nesting. Returns False.

**Case 2: "local-ref-last"** — 150k keys, local ref at the last position. Returns True.

**Case 3: "local-ref-deep"** — a structure where a local ref is buried deep. E.g., a dict with 1000 keys, each mapping to a list of 100 dicts, and the local ref is in the last one. Returns True after traversing everything.

**Case 4: "nonlocal-refs"** — 150k keys, all job refs are non-local (job-xxxx). Returns False. This exercises get_job_from_jbor heavily.

**Case 5: "mixed-refs"** — 150k keys, many non-local refs, one local ref at the end. Returns True.

**Case 6: "big-list"** — `{"inputs": [200k items]}`, items are a mix of plain values and dicts. Returns False.

**Case 7: "deep-tree"** — a tree with branching factor 4 and depth 8 → 65k leaves, ~87k nodes. Returns False.

**Case 8: "many-small-dicts"** — 50k keys, each mapping to a dict with 3-5 keys. Returns False.

Let me also consider: the function returns a boolean. For case 3 and 5, it returns True. For others, False. Good diversity.

Now, let me write the code carefully.

For case 3 (local-ref-deep):

```python
def _build_deep_local_ref():
    rng = random.Random(3)
    d = {}
    for i in range(1000):
        lst = []
        for j in range(100):
            if i == 999 and j == 99:
                lst.append(_jbor("localjob-deep"))
            else:
                lst.append(_plain(rng))
        d["k%d" % i] = lst
    return d
```

This creates 1000 keys, each with a list of 100 items → 100k leaves. The function: first loop iterates 1000 keys, pushes 1000 lists to q. Then while loop pops lists and iterates 100 items each. Total 100k is_job_ref calls. The local ref is at the very end (last list, last item). Returns True.

Wait, the order of processing: q is a stack (pop from end). So the last pushed list is processed first. The local ref is in the last list (i=999), which is pushed last, so popped first. So it would be found early! Let me put the local ref in the first list (i=0), which is pushed first and popped last. Then the function processes all other lists before finding it. 

Actually, q.pop() pops from the end. So the last appended is processed first. So to make the local ref found last, put it in the first-appended container. So i=0, j=0.

Let me do that.

Actually, wait. Let me re-read the function:

```python
q = []
for field in io_hash:
    if is_job_ref(io_hash[field]):
        ...
    elif isinstance(io_hash[field], list) or isinstance(io_hash[field], dict):
        q.append(io_hash[field])

while len(q) > 0:
    thing = q.pop()
    ...
```

Yes, q.pop() pops from the end. So the last appended is processed first. So to delay finding the local ref, put it in the first appended container.

OK.

For case 7 (deep tree):

```python
def _build_tree(depth, branching, rng):
    if depth == 0:
        return _plain(rng)
    d = {}
    for i in range(branching):
        d["c%d" % i] = _build_tree(depth - 1, branching, rng)
    return d
```

With depth=8, branching=4 → 4^8 = 65536 leaves, total nodes ~87381. The function: first loop iterates 4 keys of root, pushes 4 dicts. Then processes each. Total ~87k is_job_ref calls. Should be ~20-30ms.

Hmm, maybe increase to depth=9, branching=4 → 262k leaves, ~349k nodes. That might be ~100ms. Let's use depth=8 or 9. Let's use 9 for more work. Actually, 4^9 = 262144 leaves, total nodes = (4^10-1)/3 ≈ 349525. That's 350k is_job_ref calls. Maybe ~100ms. Good.

But building this tree recursively creates 350k dicts. Memory: each dict ~200 bytes → 70 MB. Hmm, that's close to 100 MB. Let's use depth=8: 87381 nodes → ~17 MB. That's safer. Work: ~87k calls → ~25ms. Maybe a bit fast but OK.

Actually, we can make it wider: branching=8, depth=5 → 8^5 = 32768 leaves, total nodes = (8^6-1)/7 ≈ 37449. That's fewer nodes. Hmm.

Let's use branching=4, depth=9 but with a shallower tree... Actually, let's just use branching=3, depth=11: 3^11 = 177147 leaves, total nodes = (3^12-1)/2 = 265720. ~266k nodes. Memory ~50 MB. Work ~266k calls → ~70ms. Good.

Hmm, recursion depth 11 is fine.

Actually, let me reconsider. The function processes each dict by iterating its fields. For a tree node with 3 children, it does 3 is_job_ref calls and pushes up to 3 children. So total work is proportional to the number of edges = number of nodes - 1. So ~266k calls.

Let's use branching=3, depth=11.

Wait, but the tree is built recursively. Python recursion limit is 1000, so depth 11 is fine.

OK.

For case 6 (big list):

```python
def _build_big_list(n, rng):
    lst = []
    for i in range(n):
        r = rng.random()
        if r < 0.7:
            lst.append(_plain(rng))
        elif r < 0.9:
            lst.append(_jbor("job-%06d" % i))
        else:
            lst.append({"a": _plain(rng), "b": _plain(rng)})
    return {"inputs": lst}
```

With n=200k. The function: first loop, field="inputs", value is a list → pushed to q. Then while loop: pop the list, iterate 200k items. Total 200k is_job_ref calls. Good.

For case 8 (many small dicts):

```python
def _build_many_dicts(n, rng):
    d = {}
    for i in range(n):
        d["k%d" % i] = {"a": _plain(rng), "b": _plain(rng), "c": _plain(rng)}
    return d
```

With n=50k → 50k keys, each a dict with 3 keys. The function: first loop iterates 50k keys, pushes 50k dicts. Then while loop processes each dict: 3 is_job_ref calls each. Total 50k + 150k = 200k calls. Good.

Now, let me also think about `checks()`.

```python
def checks():
    return [
        ("empty", lambda: ({},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
        ("none-value", lambda: ({"a": None},)),
    ]
```

These are small. The function should run without error. `{}` returns False. `{"a": _jbor(...)}` returns True. `{"a": None}` returns False.

Wait, the task says "These may raise." So it's fine if they raise. But they shouldn't.

Now, let me double-check the `_jbor` format. If `is_job_ref` expects `{"$dnanexus_link": {"job": "..."}}`, then `_jbor("localjob-0001")` returns `{"$dnanexus_link": {"job": "localjob-0001", "field": "out"}}`. `is_job_ref` → True. `get_job_from_jbor` → "localjob-0001". startswith('localjob') → True. Returns True. Good.

If `is_job_ref` expects `{"$dnanexus_link": "..."}`, then our dict form is not recognized. Then the function treats it as a plain dict, pushes it to q, and iterates its fields: "$dnanexus_link" → value is a dict → is_job_ref? No. Then it's a dict → pushed. Then processes it: "job" → "localjob-0001" → is_job_ref? No (it's a string, not a dict). "field" → "out" → no. So returns False. Hmm, that would mean our "local-ref" cases return False instead of True. But that's still a valid run — the original and modified versions would both return False. The comparison is between original and modified, not against an expected value. So it's fine.

But we want to exercise the `get_job_from_jbor` path. If the format is wrong, we won't. To be safe, let's include both formats in different cases. Actually, we can include both in the same case: some refs as dict-with-job, some as string.

Hmm, but if the string form is not recognized, it's treated as a plain dict and recursed. That adds work but doesn't exercise get_job_from_jbor.

Let me think about which format is correct. I'm now fairly sure the dxpy format is:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Wait, actually I recall that in dxpy, `is_job_ref` is:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, I keep repeating. Let me just go with it.

Actually, I found in my memory: dxpy/utils/describe.py has:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

OK, I'll trust this. Both forms are job refs.

And `get_job_from_jbor`:

```python
def get_job_from_jbor(thing):
    """
    :returns: Job ID from a JBOR
    """
    if not is_job_ref(thing):
        return None
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link']
    else:
        return thing['$dnanexus_link']['job']
```

Wait, if the string form is `{"$dnanexus_link": "job-xxxx"}`, then `get_job_from_jbor` returns "job-xxxx". If it's `{"$dnanexus_link": "file-xxxx"}`, it returns "file-xxxx". Hmm, but is_job_ref returns True for any string link? That would mean file links are considered job refs. That seems wrong.

Actually, I think `is_job_ref` checks if the string starts with "job-". Let me reconsider.

Maybe:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link'].startswith('job-')
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, I'm not sure. Let me think about the actual dxpy code. I recall:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Actually, I think the string form is always a job ID (since data object links are always dicts with 'id' or similar). Hmm.

Wait, in dxpy, a data object link is `{"$dnanexus_link": "file-xxxx"}`. And a job-based object reference is `{"$dnanexus_link": {"job": "job-xxxx", "field": "output"}}`. So the string form is a data object link, not a job ref!

Let me reconsider. If `is_job_ref` returns True for string links, then file links would be treated as job refs, which is wrong.

So `is_job_ref` probably only returns True for the dict form with 'job':

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, but then what about the string form? Maybe it's:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link'].startswith('job-')
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

I'm not sure. Let me look at the actual dxpy source from memory... 

I recall that in dxpy, `is_job_ref` is:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, if this is the case, then `{"$dnanexus_link": "file-xxxx"}` is considered a job ref. And `get_job_from_jbor` returns "file-xxxx". Then `startswith('localjob')` is False. So it's treated as a non-local job ref. That's... actually plausible? Because in the context of `has_local_job_refs`, any `$dnanexus_link` string might be a job ID? No, file IDs start with "file-", not "job-".

Wait, maybe the string form is only used for job IDs. Let me think about how dxpy represents things.

Actually, I think I'm overcomplicating. Let me just use the dict-with-job form, which is unambiguously a job ref in either interpretation. And for "non-local job refs", use `{"$dnanexus_link": {"job": "job-xxxx"}}`.

For data object links (which are not job refs), use `{"$dnanexus_link": "file-xxxx"}`. If is_job_ref treats string links as job refs, then these become non-local job refs (since "file-xxxx" doesn't start with "localjob"). Either way, no error.

Actually, to be safe, let me use the dict-with-job form for all job refs, and avoid string links entirely, or use them sparingly.

Hmm, but the function's purpose is to find local job refs. In the real repo, input_hash contains file links (string form) and job refs (dict form). So including both is realistic.

Let me include both, but ensure the local job refs use the dict form (which is definitely recognized).

Actually, wait. What if `is_job_ref` only recognizes the string form? Then our dict form wouldn't be recognized, and we'd never exercise the local job path. But that's unlikely, because the dict form is the standard JBOR.

Let me hedge: use the dict form for local job refs, and also include some string-form job refs (e.g., `{"$dnanexus_link": "job-xxxx"}`) in some cases. If the string form is recognized, great; if not, it's treated as a plain dict.

Actually, you know what, let me just check the dxpy source. I'll try to recall harder.

From dxpy/utils/describe.py (I've seen this code):

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, I really think it's this. Because in dxpy, a "job-based object reference" is any `$dnanexus_link` that could refer to a job's output. The string form `{"$dnanexus_link": "job-xxxx"}` is a reference to a job. But `{"$dnanexus_link": "file-xxxx"}` is a reference to a file, not a job. So why would is_job_ref return True for it?

Maybe the string form is only used for jobs, and data objects use a different structure. Let me think... In dxpy, a data object link is `{"$dnanexus_link": "file-xxxx"}`. And a job link is `{"$dnanexus_link": "job-xxxx"}`. Both are strings. So `is_job_ref` would need to distinguish by prefix.

Hmm, maybe:

```python
def is_job_ref(thing, reftype=dict):
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link'].startswith('job-')
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

I'm not sure. Let me just avoid the string form for job refs and use the dict form. For file links, use the string form. If is_job_ref treats string links as job refs, then file links become non-local job refs, which is fine.

Actually, let me reconsider. The function `has_local_job_refs` checks `get_job_from_jbor(io_hash[field]).startswith('localjob')`. If `is_job_ref` returns True for a file link, then `get_job_from_jbor` returns "file-xxxx", and `startswith('localjob')` is False. So it's treated as a non-local job ref. No error.

So including file links as string form is safe.

Let me now write the code.

One more consideration: the task says "Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes." Our data has varied values. Good.

Also, "Every case must run to completion on the original function without raising." We need to make sure the function doesn't raise. The function does `for field in io_hash: ... io_hash[field]`. If io_hash is a dict, this works. If a value is a list, it's pushed. If a value is a dict, it's pushed. If a value is a job ref, it's checked. No errors expected.

One potential issue: if a value is a dict that is a job ref, `is_job_ref` returns True, and `get_job_from_jbor` is called. If the dict form is `{"$dnanexus_link": {"job": "..."}}`, it returns the job string. Fine.

If a value is a dict with `$dnanexus_link` as a string, and `is_job_ref` returns True (string form), then `get_job_from_jbor` returns the string. Fine.

If `is_job_ref` returns False for the string form, then it's a dict, pushed to q, and its fields iterated. Fine.

No errors.

Now, let me also consider the `checks()` inputs. They should be small. Let's use:

1. `{}` — empty dict.
2. `{"a": None}` — None value.
3. `{"a": {"$dnanexus_link": {"job": "localjob-0001"}}}` — local job ref.

These are checked for identical behavior. They may raise, but they shouldn't.

Actually, the task says "2 or 3 small edge inputs". Let's do 3.

Now, let me write the full code.

```python
import random

from dxpy.utils.local_exec_utils import has_local_job_refs


def _jbor(job_id, field="out", index=None):
    link = {"job": job_id, "field": field}
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}


def _file_link(file_id):
    return {"$dnanexus_link": file_id}


def _plain(rng):
    return rng.choice([
        rng.randint(0, 10**9),
        "v" + str(rng.randint(0, 10**9)),
        None,
        1.5,
        True,
        False,
    ])
```

Wait, `rng.choice` with a list of values — but the values are evaluated eagerly. That's fine, but it generates 6 random values each time. Let's optimize:

```python
def _plain(rng):
    r = rng.random()
    if r < 0.3:
        return rng.randint(0, 10**9)
    elif r < 0.6:
        return "v" + str(rng.randint(0, 10**9))
    elif r < 0.75:
        return None
    elif r < 0.85:
        return 1.5
    elif r < 0.95:
        return True
    else:
        return False
```

This is faster.

Now, the builders.

```python
def _build_flat_hash(n, rng, local_ref_at=None, nonlocal_ref_ratio=0.0, nested_ratio=0.2):
    d = {}
    for i in range(n):
        key = "field_%d" % i
        if local_ref_at is not None and i == local_ref_at:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        else:
            r = rng.random()
            if r < nested_ratio * 0.6:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < nested_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d
```

Hmm, let me simplify. I'll write specific builders.

Actually, let me write a single flexible builder and use it for cases 1, 2, 4, 5, 8.

Let me write:

```python
def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                list_ratio=0.1, dict_ratio=0.1):
    d = {}
    for i in range(n_keys):
        key = "field_%d" % i
        if local_ref_pos is not None and i == local_ref_pos:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        else:
            r = rng.random()
            if r < list_ratio:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < list_ratio + dict_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d
```

For case 1: `_build_hash(150_000, rng, list_ratio=0.1, dict_ratio=0.1)` → no refs. Returns False.

For case 2: `_build_hash(150_000, rng, local_ref_pos=149_999)` → local ref at the end. Returns True.

For case 4: `_build_hash(150_000, rng, nonlocal_ref_ratio=0.3)` → 30% non-local refs. Returns False.

For case 5: `_build_hash(150_000, rng, local_ref_pos=149_999, nonlocal_ref_ratio=0.3)` → mixed. Returns True.

For case 8: `_build_hash(50_000, rng, list_ratio=0.0, dict_ratio=0.9)` → many small dicts.

Hmm, for case 8, dict_ratio=0.9 means 90% of values are dicts with 1-4 keys. That's 50k dicts, each with ~2.5 keys → 125k inner values. Plus 50k top-level. Total ~175k is_job_ref calls. Good.

Wait, but `_build_hash` with `list_ratio=0.0, dict_ratio=0.9`: r < 0.0 is never true, so no lists. r < 0.9 → dict. else → plain. So 90% dicts, 10% plain. Good.

For case 3 (deep local ref), I'll write a separate builder.

For case 6 (big list), separate builder.

For case 7 (deep tree), separate builder.

Let me write case 3:

```python
def _build_deep_local_ref(n_outer, n_inner, rng):
    d = {}
    for i in range(n_outer):
        lst = []
        for j in range(n_inner):
            if i == 0 and j == 0:
                lst.append(_jbor("localjob-deep"))
            else:
                r = rng.random()
                if r < 0.1:
                    lst.append({"x": _plain(rng), "y": _plain(rng)})
                else:
                    lst.append(_plain(rng))
        d["k%d" % i] = lst
    return d
```

With n_outer=1000, n_inner=100 → 100k leaves. The local ref is in the first list (i=0, j=0). Since q.pop() processes the last appended first, the first list is processed last. So the function traverses all other lists before finding the local ref. Returns True.

Wait, but the first loop iterates d's keys in insertion order: k0, k1, ..., k999. It pushes the lists in that order. So q = [list0, list1, ..., list999]. q.pop() pops list999 first, then list998, ..., list0 last. So list0 is processed last. The local ref is in list0. So it's found last. Good.

For case 6:

```python
def _build_big_list(n, rng):
    lst = []
    for i in range(n):
        r = rng.random()
        if r < 0.6:
            lst.append(_plain(rng))
        elif r < 0.8:
            lst.append(_jbor("job-%06d" % i))
        elif r < 0.9:
            lst.append({"a": _plain(rng), "b": _plain(rng)})
        else:
            lst.append([_plain(rng), _plain(rng)])
    return {"inputs": lst}
```

With n=200k. The function: first loop, field="inputs", value is a list → pushed. Then while loop: pop the list, iterate 200k items. For each item: is_job_ref. If it's a job ref, get_job_from_jbor. If it's a list/dict, push. So total ~200k is_job_ref calls, plus processing of nested items. Good.

For case 7:

```python
def _build_tree(depth, branching, rng):
    if depth == 0:
        return _plain(rng)
    d = {}
    for i in range(branching):
        d["c%d" % i] = _build_tree(depth - 1, branching, rng)
    return d
```

With depth=11, branching=3 → 3^11 = 177147 leaves, total nodes = (3^12-1)/2 = 265720. The function traverses all. Returns False.

Wait, but the tree is built recursively. The root is a dict with 3 keys, each mapping to a subtree. The function: first loop iterates 3 keys, pushes 3 dicts. Then processes each. Total ~265k is_job_ref calls. Good.

But memory: 265k dicts × ~200 bytes = 53 MB. Plus the plain values. Should be under 100 MB. Let's use depth=10, branching=3 → 3^10 = 59049 leaves, total nodes = (3^11-1)/2 = 88573. ~88k nodes → ~18 MB. Work ~88k calls → ~25ms. Maybe a bit fast.

Let's use depth=11, branching=3 → 265k nodes. ~53 MB. Work ~265k calls → ~70ms. Good.

Hmm, but building 265k dicts recursively might take a while. Let's estimate: each dict creation is ~1 µs. 265k × 1 µs = 0.265s. Fine.

Actually, the recursion creates the tree bottom-up. At depth 0, we create 177k plain values. At depth 1, 59k dicts. Etc. Total ~265k dicts. Should be ~0.5s. Fine.

Now, let me also think about the `checks()` cases.

```python
def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]
```

Wait, `_jbor` is defined at module level. The thunk `lambda: ({"a": _jbor("localjob-0001")},)` calls `_jbor` each time. That's fine — it's cheap. But the task says "Setup is never timed: everything that builds data, objects or files goes in the thunk or in module-level code." So calling `_jbor` in the thunk is fine.

Actually, for checks, it's not timed anyway. But for consistency, let's build the dict at module level or in the thunk. It's fine either way.

Hmm, but for the cases, the thunks should return the pre-built data. Let me build the data at module level and have the thunks return it.

Wait, but the thunks are called many times. If they return the same object, and the function doesn't modify it, that's fine. The function doesn't modify io_hash. So we can return the same object.

Let me structure:

```python
_rng = random.Random(0)

_CASE1_DATA = _build_hash(150_000, _rng, list_ratio=0.1, dict_ratio=0.1)
_CASE2_DATA = _build_hash(150_000, _rng, local_ref_pos=149_999, list_ratio=0.1, dict_ratio=0.1)
...
```

But wait, using the same `_rng` for all cases means the data is generated sequentially. That's fine, but it's better to use separate seeds for reproducibility. The task says "a fixed random seed (`random.Random(0)`)". So maybe use `random.Random(0)` for each case? Or one RNG for all?

The task says "use a fixed random seed (`random.Random(0)`) when generating data". I think using one RNG seeded with 0 for all data is fine. Or separate RNGs per case. Let me use separate RNGs with different seeds for clarity, but the task specifically says `random.Random(0)`. Hmm.

I'll use `random.Random(0)` for the first case, and maybe different seeds for others. Actually, the task says "a fixed random seed (`random.Random(0)`)" — I think it just means use a fixed seed, and the example uses 0. Let me use `random.Random(0)` for all, or separate seeds. To be safe, I'll use `random.Random(0)` as the base and derive.

Actually, let me just use a single `random.Random(0)` at module level and build all data with it. That's simplest.

But the order of building matters. If I build case 1 first, then case 2, etc., the data is deterministic. That's fine.

Let me write:

```python
_rng = random.Random(0)

_CASE1 = _build_hash(150_000, _rng, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(150_000, _rng, local_ref_pos=149_999, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 100, _rng)
_CASE4 = _build_hash(150_000, _rng, nonlocal_ref_ratio=0.3, list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(150_000, _rng, local_ref_pos=149_999, nonlocal_ref_ratio=0.3, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(200_000, _rng)
_CASE7 = _build_tree(11, 3, _rng)
_CASE8 = _build_hash(50_000, _rng, list_ratio=0.0, dict_ratio=0.9)
```

Hmm, but building all this at module level takes time. The task says "building all inputs under about 10 s". Let's estimate: 150k × 5 cases = 750k values, plus 100k, 200k, 265k, 50k. Total ~1.4M values. Each value generation involves a few RNG calls. Maybe ~2-3s total. Fine.

Memory: 1.4M values × ~100 bytes = 140 MB. Hmm, that's over 100 MB. Let's reduce.

Actually, the constraint says "Keep the data in memory under about 100 MB". So we need to be careful.

Let's reduce the sizes. 150k keys per case is a lot. Let's use 80k keys for the flat cases.

80k keys × 5 cases = 400k top-level values, plus nested. Maybe ~600k total values. ~60 MB. Plus case 3 (100k), case 6 (200k), case 7 (265k), case 8 (50k + 125k). Total ~1.3M values. Still ~130 MB.

Hmm. Let's reduce further. 

Actually, a Python dict with 80k keys: each key is a string (~50 bytes), each value is an object (~28 bytes for int, more for str). The dict itself has overhead. 80k entries × ~100 bytes = 8 MB per case. 5 cases = 40 MB. Case 3: 100k values → 10 MB. Case 6: 200k → 20 MB. Case 7: 265k nodes → 53 MB. Case 8: 50k dicts + 125k values → 50k × 200 + 125k × 50 = 10 + 6 = 16 MB. Total ~140 MB. Still over.

Let's reduce case 7. Use depth=10, branching=3 → 88k nodes → 18 MB. Work ~88k calls → ~25ms. Maybe a bit fast but acceptable.

And reduce flat cases to 60k keys. 60k × 5 = 300k → 30 MB.

Case 6: 150k → 15 MB.
Case 3: 80k → 8 MB.
Case 8: 30k keys × 3 inner = 90k → 12 MB.

Total ~83 MB. Under 100 MB. Good.

But wait, the work per case: 60k keys → ~60k-100k is_job_ref calls → ~15-25ms. That's within 1-200ms. Good.

Actually, let me reconsider. The task says "One call should take roughly 1 ms to 200 ms on the original." So 15-25ms is fine.

Let me also consider that the function might be slower than I estimate. Let's aim for ~50-100ms per call. That means ~200k-400k is_job_ref calls. Hmm.

Let me benchmark mentally: `is_job_ref` does `isinstance(thing, dict)` and `'$dnanexus_link' not in thing`. For a non-dict, it's just `isinstance` → False. That's maybe 50ns. Plus the function call overhead ~50ns. So ~100ns per non-dict value. For 200k values, ~20ms. Plus dict iteration overhead. Maybe ~30-40ms.

So 200k values → ~30-40ms. That's good.

Let's aim for ~200k values per case.

For the flat cases: 100k keys with ~2 values each (some nested) → ~200k values. 100k keys × 100 bytes = 10 MB per case. 5 cases = 50 MB. Plus others. Total maybe 100 MB. Hmm.

Let's use 80k keys per flat case → ~160k values → ~10 MB per case. 5 cases = 50 MB.

Case 3: 1000 outer × 80 inner = 80k values → 8 MB.
Case 6: 150k values → 15 MB.
Case 7: depth 10, branching 3 → 88k nodes → 18 MB.
Case 8: 40k keys × 3 inner = 120k values → 15 MB.

Total ~106 MB. Slightly over. Let's reduce case 7 to depth 9, branching 3 → 3^9 = 19683 leaves, total nodes = (3^10-1)/2 = 29524 → ~6 MB. Work ~30k calls → ~10ms. Hmm, fast.

Alternatively, use branching 4, depth 7: 4^7 = 16384 leaves, total nodes = (4^8-1)/3 = 21845 → ~4 MB. Work ~22k calls. Fast.

Hmm, the tree is memory-inefficient because each node is a dict. Let's use a different structure for deep nesting that uses fewer dicts.

Actually, let's just use a list-based deep structure. E.g., a list of lists of lists... But the function expects io_hash to be a dict. The top-level must be a dict. But nested values can be lists.

Let's build a deeply nested list: `[[[[...]]]]`. Each level is a list with one element (the next level). At the bottom, a local ref or plain value. But that's only ~depth nodes. Not much work.

To make it wide, we can have a list of many nested lists. E.g., a dict with one key mapping to a list of 100k items, each item is a list of 2 items. That's 100k + 200k = 300k values. Memory: 100k lists × 56 bytes + 200k values × 28 bytes = 5.6 + 5.6 = 11 MB. Work: 300k is_job_ref calls → ~40ms.

That's more memory-efficient than the tree. Let's use that for case 7.

Actually, let's rethink. The tree case is meant to exercise deep nesting. Let's build a structure that's both deep and wide, but memory-efficient.

Idea: a dict with 1000 keys, each mapping to a list of 100 items, each item is a dict with 3 keys. Total: 1000 + 100k + 100k dicts + 300k values. Hmm, that's a lot.

Let's simplify. The tree case can be replaced with a "deep list nesting" case:

```python
def _build_deep_nesting(depth, width, rng):
    # Build a structure that is `depth` levels deep and `width` wide at each level
    # Each level is a list of `width` items, each item is the next level
    if depth == 0:
        return _plain(rng)
    return [_build_deep_nesting(depth - 1, width, rng) for _ in range(width)]
```

With depth=4, width=20 → 20^4 = 160k leaves, total nodes = (20^5-1)/19 ≈ 168k. Memory: 168k lists × 56 bytes + 160k values × 28 bytes = 9.4 + 4.5 = 14 MB. Work: ~168k is_job_ref calls → ~25ms.

Hmm, but the top-level must be a dict. So wrap it: `{"root": _build_deep_nesting(4, 20, rng)}`.

Actually, let's just use a dict-based tree with lower branching and higher depth, or a list-based tree.

Let me use a list-based tree with depth=5, width=10: 10^5 = 100k leaves, total nodes = (10^6-1)/9 = 111k. Memory: 111k lists × 56 + 100k values × 28 = 6.2 + 2.8 = 9 MB. Work: ~111k calls → ~20ms.

Hmm, still fast. Let's use depth=6, width=8: 8^6 = 262k leaves, total nodes = (8^7-1)/7 = 299k. Memory: 299k lists × 56 + 262k × 28 = 16.7 + 7.3 = 24 MB. Work: ~300k calls → ~50ms. Good.

But building 300k lists recursively... Python recursion depth 6 is fine. Time: ~0.3s. Fine.

Actually, let's just use the dict-based tree with depth=10, branching=3. 88k nodes → 18 MB. Work ~88k calls → ~20ms. It's fine.

Hmm, I'm overthinking. Let me just pick sizes that give ~50-100ms per call and keep memory under 100 MB.

Let me finalize:

- Case 1: 80k keys, ~160k values. ~10 MB. Work ~160k calls → ~30ms.
- Case 2: 80k keys, ~160k values. ~10 MB. Work ~160k calls → ~30ms.
- Case 3: 1000 × 80 = 80k values. ~8 MB. Work ~80k calls → ~15ms.
- Case 4: 80k keys, 30% refs, ~160k values. ~10 MB. Work ~160k calls → ~30ms.
- Case 5: 80k keys, 30% refs + 1 local, ~160k values. ~10 MB. Work ~160k calls → ~30ms.
- Case 6: 150k list items. ~15 MB. Work ~150k calls → ~30ms.
- Case 7: tree depth 10, branching 3 → 88k nodes. ~18 MB. Work ~88k calls → ~20ms.
- Case 8: 40k keys × ~3 inner = 120k values. ~12 MB. Work ~120k calls → ~25ms.

Total memory ~93 MB. Under 100 MB. Good.

Total work: ~1.1M is_job_ref calls across all cases. Building time: maybe ~3s. Fine.

Wait, but the task says "We run them on the original function and keep the 4 that do the most work." So only 4 cases are kept. The others are just for diversity. So we don't need all 8 to be heavy. But it's good to have variety.

Actually, re-reading: "cases(): exactly 8 measured inputs. We run them on the original function and keep the 4 that do the most work." So the 8 cases are run once on the original to measure work, and the top 4 are kept for the actual energy measurement. So we need 8 diverse cases, and the top 4 should be substantial.

OK, our cases are fine.

Now, let me write the final code.

One more thing: the task says "Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports." So we import `from dxpy.utils.local_exec_utils import has_local_job_refs`. We don't need to import anything else from dxpy.

But wait — do we need to import `dxpy` itself? The module imports `dxpy`. When we import `dxpy.utils.local_exec_utils`, it will import `dxpy` and its dependencies. That should work as long as the environment has dxpy installed.

Let me write the code.

```python
import random

from dxpy.utils.local_exec_utils import has_local_job_refs


def _jbor(job_id, field="out", index=None):
    link = {"job": job_id, "field": field}
    if index is not None:
        link["index"] = index
    return {"$dnanexus_link": link}


def _plain(rng):
    r = rng.random()
    if r < 0.3:
        return rng.randint(0, 10**9)
    elif r < 0.6:
        return "v" + str(rng.randint(0, 10**9))
    elif r < 0.75:
        return None
    elif r < 0.85:
        return 1.5
    elif r < 0.95:
        return True
    else:
        return False


def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                list_ratio=0.1, dict_ratio=0.1):
    d = {}
    for i in range(n_keys):
        key = "field_%d" % i
        if local_ref_pos is not None and i == local_ref_pos:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        else:
            r = rng.random()
            if r < list_ratio:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < list_ratio + dict_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d


def _build_deep_local_ref(n_outer, n_inner, rng):
    d = {}
    for i in range(n_outer):
        lst = []
        for j in range(n_inner):
            if i == 0 and j == 0:
                lst.append(_jbor("localjob-deep"))
            else:
                r = rng.random()
                if r < 0.1:
                    lst.append({"x": _plain(rng), "y": _plain(rng)})
                else:
                    lst.append(_plain(rng))
        d["k%d" % i] = lst
    return d


def _build_big_list(n, rng):
    lst = []
    for i in range(n):
        r = rng.random()
        if r < 0.6:
            lst.append(_plain(rng))
        elif r < 0.8:
            lst.append(_jbor("job-%06d" % i))
        elif r < 0.9:
            lst.append({"a": _plain(rng), "b": _plain(rng)})
        else:
            lst.append([_plain(rng), _plain(rng)])
    return {"inputs": lst}


def _build_tree(depth, branching, rng):
    if depth == 0:
        return _plain(rng)
    d = {}
    for i in range(branching):
        d["c%d" % i] = _build_tree(depth - 1, branching, rng)
    return d


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3,
                     list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(150_000, _rng)
_CASE7 = _build_tree(10, 3, _rng)
_CASE8 = _build_hash(40_000, _rng, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]


def cases():
    return [
        ("flat-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("deep-local-ref", lambda: (_CASE3,)),
        ("nonlocal-refs", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
```

Wait, there's an issue with `_CASE7`: `_build_tree(10, 3, _rng)` returns a dict with 3 keys, each mapping to a subtree. The top-level is a dict. Good.

But wait, the function's first loop does `for field in io_hash: if is_job_ref(io_hash[field]): ...`. For the tree, the root is a dict with 3 keys, each value is a dict. So it pushes 3 dicts. Then processes them. Good.

Now, let me double-check the `_build_hash` function. For `_CASE8`, `list_ratio=0.0, dict_ratio=0.9`: `r < 0.0` is never true. `r < 0.0 + 0.9` → 90% chance. So 90% dicts, 10% plain. Good.

For `_CASE1`, `list_ratio=0.1, dict_ratio=0.1`: 10% lists, 10% dicts, 80% plain. Good.

Now, let me think about whether the function might raise on any of these.

For `_CASE3`, the structure is a dict of lists. The function's first loop iterates the dict's keys, pushes each list. Then while loop pops lists and iterates items. Items are either plain values, dicts, or the local ref. For dicts, it pushes them. Then processes them. No errors.

For `_CASE6`, the structure is `{"inputs": [...]}`. The list contains plain values, job refs, dicts, and lists. The function pushes the list, then iterates items. For job refs, it calls `get_job_from_jbor`. For dicts and lists, it pushes them. No errors.

For `_CASE7`, the tree is a dict of dicts. No errors.

Now, let me think about the job ref format again. `_jbor("localjob-%06d" % i)` returns `{"$dnanexus_link": {"job": "localjob-000001", "field": "out"}}`. If `is_job_ref` recognizes this, then `get_job_from_jbor` returns "localjob-000001", and `startswith('localjob')` is True. So the function returns True. Good.

If `is_job_ref` doesn't recognize this (unlikely), then it's treated as a plain dict, pushed to q, and its fields iterated. The value of "$dnanexus_link" is a dict, so it's pushed. Then its fields: "job" → "localjob-000001" (string, not a job ref), "field" → "out". So no local ref found. The function returns False. But that's still a valid run.

Hmm, but if `is_job_ref` doesn't recognize the dict form, then our "local-ref" cases won't return True, and we won't exercise the `get_job_from_jbor` path. But the task says "build the inputs from the classes and functions shown". We know `is_job_ref` checks for job refs. The standard dxpy job ref is the dict form. I'm confident.

Actually, let me hedge by also including a string-form job ref in some cases. For example, in `_CASE2`, instead of `_jbor("localjob-%06d" % i)`, use `{"$dnanexus_link": "localjob-%06d" % i}`. If `is_job_ref` recognizes string form, then `get_job_from_jbor` returns the string, and `startswith('localjob')` is True. If not, it's treated as a plain dict.

Hmm, but if `is_job_ref` recognizes string form, then file links (`{"$dnanexus_link": "file-xxxx"}`) would also be recognized as job refs. And `get_job_from_jbor` would return "file-xxxx", which doesn't start with "localjob". So they'd be treated as non-local job refs. That's fine.

But I'm not sure if `is_job_ref` recognizes string form. Let me just use the dict form for local job refs, and maybe include some string-form refs as "non-local" in some cases.

Actually, let me think about what's most realistic. In the repo, `entry_point['input_hash']` contains file links and job refs. File links are `{"$dnanexus_link": "file-xxxx"}`. Job refs are `{"$dnanexus_link": {"job": "job-xxxx", "field": "output"}}`. So the dict form is the job ref. The string form is the file link.

So `is_job_ref` must distinguish: dict form with 'job' → job ref; string form → not a job ref (it's a file link). Unless the string starts with "job-".

Hmm, let me look at the actual dxpy code once more. I'll try to recall the exact implementation.

From dxpy/utils/describe.py:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

I'm now fairly sure this is the actual code. Because I remember that in dxpy, `is_job_ref` returns True for any `$dnanexus_link` string. Wait, that would mean file links are job refs. That seems wrong.

Let me think about `get_job_from_jbor`:

```python
def get_job_from_jbor(thing):
    """
    :returns: Job ID from a JBOR
    """
    if not is_job_ref(thing):
        return None
    if isinstance(thing['$dnanexus_link'], basestring):
        return thing['$dnanexus_link']
    else:
        return thing['$dnanexus_link']['job']
```

If `is_job_ref` returns True for a file link, then `get_job_from_jbor` returns the file ID. Then in `has_local_job_refs`, `get_job_from_jbor(...).startswith('localjob')` would be False for a file ID. So it's treated as a non-local job ref. That's... actually fine for this function? But it means the function would check every file link as a potential job ref. That's inefficient but correct.

Hmm, but wait. In dxpy, a data object link is `{"$dnanexus_link": "file-xxxx"}`. And a job-based object reference is `{"$dnanexus_link": {"job": "job-xxxx", "field": "output"}}`. So `is_job_ref` should return False for the string form (file link) and True for the dict form (job ref).

But then why would `get_job_from_jbor` handle the string form? Maybe for backwards compatibility, or for the case where the link is `{"$dnanexus_link": "job-xxxx"}`.

Actually, I think I recall now: in dxpy, `is_job_ref` is:

```python
def is_job_ref(thing, reftype=dict):
    """
    :param thing: something that might be a job-based object reference hash
    :type thing: dict
    :returns: True if thing is a job-based object reference hash
    """
    if not isinstance(thing, reftype):
        return False
    if '$dnanexus_link' not in thing:
        return False
    if isinstance(thing['$dnanexus_link'], basestring):
        return True
    if isinstance(thing['$dnanexus_link'], dict) and 'job' in thing['$dnanexus_link']:
        return True
    return False
```

Hmm, I keep coming back to this. Let me just accept it. If it's wrong, our cases still run without error.

Actually, let me look at the dxpy source from a different angle. The function `has_local_job_refs` is in `local_exec_utils.py`. It checks `get_job_from_jbor(io_hash[field]).startswith('localjob')`. The local job IDs start with "localjob". So a local job ref would be `{"$dnanexus_link": {"job": "localjob-xxxx", "field": "output"}}` or `{"$dnanexus_link": "localjob-xxxx"}`.

I'll use the dict form for local job refs, and also include some string-form local job refs in some cases to hedge.

Let me modify `_jbor` to sometimes use the string form:

Actually, let me just define two functions:

```python
def _jbor_dict(job_id):
    return {"$dnanexus_link": {"job": job_id, "field": "out"}}

def _jbor_str(job_id):
    return {"$dnanexus_link": job_id}
```

And use `_jbor_dict` for local job refs (since it's the standard form), and `_jbor_str` for non-local refs in some cases.

Hmm, but if `is_job_ref` recognizes the string form, then `_jbor_str("job-xxxx")` is a non-local job ref. If not, it's a plain dict. Either way, no error.

Let me include both forms in the "nonlocal-refs" case to exercise both paths.

Actually, let me keep it simple. Use the dict form everywhere. It's the standard form and definitely recognized.

Wait, but what if `is_job_ref` only recognizes the string form? Then our dict form is not recognized. But that's very unlikely, because the dict form is the standard JBOR in dxpy.

Let me just go with the dict form.

Hmm, actually, let me reconsider. I'll include both forms in the nonlocal-refs case, and use the dict form for local refs. This way, if the string form is recognized, we exercise it; if not, it's just a plain dict.

Let me update `_build_hash`:

```python
def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                list_ratio=0.1, dict_ratio=0.1):
    d = {}
    for i in range(n_keys):
        key = "field_%d" % i
        if local_ref_pos is not None and i == local_ref_pos:
            d[key] = {"$dnanexus_link": {"job": "localjob-%06d" % i, "field": "out"}}
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            if rng.random() < 0.5:
                d[key] = {"$dnanexus_link": {"job": "job-%06d" % i, "field": "out"}}
            else:
                d[key] = {"$dnanexus_link": "job-%06d" % i}
        else:
            r = rng.random()
            if r < list_ratio:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < list_ratio + dict_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d
```

This includes both forms for non-local refs.

Now, for the local ref, I use the dict form. If `is_job_ref` doesn't recognize it, the function won't return True. But it will still run.

Hmm, let me also include a string-form local ref in one of the cases. Let's make case 3 use a string-form local ref:

```python
def _build_deep_local_ref(n_outer, n_inner, rng):
    d = {}
    for i in range(n_outer):
        lst = []
        for j in range(n_inner):
            if i == 0 and j == 0:
                lst.append({"$dnanexus_link": "localjob-deep"})
            else:
                ...
```

Wait, but if the string form is not recognized as a job ref, then it's a plain dict, and the function won't return True. But it will still run. And if the string form IS recognized, it returns True.

Actually, let me use the dict form for case 3 as well, to be safe. I'll just use the dict form for all local refs.

Hmm, but then if `is_job_ref` only recognizes the string form, we never return True. Let me include both forms in different cases. Let's make case 2 use the dict form, and case 3 use the string form. That way, at least one of them will return True if either form is recognized.

Wait, but if `is_job_ref` recognizes the string form, then `{"$dnanexus_link": "localjob-deep"}` is a local job ref. And `get_job_from_jbor` returns "localjob-deep". startswith('localjob') → True. Good.

If `is_job_ref` only recognizes the dict form, then case 2 returns True, and case 3 returns False. Still fine.

Let me do that.

Actually, let me just use the dict form for all local refs. I'm confident it's the right form. The string form is for file links.

OK, final decision: use the dict form for all job refs (local and non-local). Use the string form for file links (which may or may not be recognized as job refs).

Let me update:

```python
def _file_link(file_id):
    return {"$dnanexus_link": file_id}
```

And in `_build_hash`, for non-local refs, use `_jbor("job-%06d" % i)` (dict form). For file links, use `_file_link("file-%06d" % i)`.

Hmm, but if `is_job_ref` recognizes string form, then file links are treated as job refs, and `get_job_from_jbor` returns "file-xxxx", which doesn't start with "localjob". So they're non-local refs. That's fine.

Let me include file links in the data to add variety.

OK, let me write the final code.

Actually, let me reconsider the whole thing. The task is to write inputs for energy measurement. The function is `has_local_job_refs`. We need 8 cases and 2-3 checks. The cases should be diverse and substantial.

Let me finalize the code.

```python
import random

from dxpy.utils.local_exec_utils import has_local_job_refs


def _jbor(job_id, field="out"):
    return {"$dnanexus_link": {"job": job_id, "field": field}}


def _file_link(file_id):
    return {"$dnanexus_link": file_id}


def _plain(rng):
    r = rng.random()
    if r < 0.3:
        return rng.randint(0, 10**9)
    elif r < 0.6:
        return "v" + str(rng.randint(0, 10**9))
    elif r < 0.75:
        return None
    elif r < 0.85:
        return 1.5
    elif r < 0.95:
        return True
    else:
        return False


def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                file_link_ratio=0.0, list_ratio=0.1, dict_ratio=0.1):
    d = {}
    for i in range(n_keys):
        key = "field_%d" % i
        if local_ref_pos is not None and i == local_ref_pos:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        elif file_link_ratio > 0 and rng.random() < file_link_ratio:
            d[key] = _file_link("file-%06d" % i)
        else:
            r = rng.random()
            if r < list_ratio:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < list_ratio + dict_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d


def _build_deep_local_ref(n_outer, n_inner, rng):
    d = {}
    for i in range(n_outer):
        lst = []
        for j in range(n_inner):
            if i == 0 and j == 0:
                lst.append(_jbor("localjob-deep"))
            else:
                r = rng.random()
                if r < 0.1:
                    lst.append({"x": _plain(rng), "y": _plain(rng)})
                elif r < 0.2:
                    lst.append(_file_link("file-%d-%d" % (i, j)))
                else:
                    lst.append(_plain(rng))
        d["k%d" % i] = lst
    return d


def _build_big_list(n, rng):
    lst = []
    for i in range(n):
        r = rng.random()
        if r < 0.5:
            lst.append(_plain(rng))
        elif r < 0.7:
            lst.append(_jbor("job-%06d" % i))
        elif r < 0.8:
            lst.append(_file_link("file-%06d" % i))
        elif r < 0.9:
            lst.append({"a": _plain(rng), "b": _plain(rng)})
        else:
            lst.append([_plain(rng), _plain(rng)])
    return {"inputs": lst}


def _build_tree(depth, branching, rng):
    if depth == 0:
        return _plain(rng)
    d = {}
    for i in range(branching):
        d["c%d" % i] = _build_tree(depth - 1, branching, rng)
    return d


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, file_link_ratio=0.2,
                     list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3,
                     file_link_ratio=0.2, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(150_000, _rng)
_CASE7 = _build_tree(10, 3, _rng)
_CASE8 = _build_hash(40_000, _rng, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]


def cases():
    return [
        ("flat-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("deep-local-ref", lambda: (_CASE3,)),
        ("nonlocal-refs", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
```

Wait, there's a potential issue with `_build_tree(10, 3, _rng)`. The tree is built recursively. At depth 10, we have 3^10 = 59049 leaves. Total nodes = (3^11-1)/2 = 88573. That's fine.

But wait, the tree is built with `_plain(rng)` at the leaves. `_plain` uses `rng`. So the tree generation consumes RNG state. That's fine.

Now, let me double-check the memory. 

Case 1: 80k keys. Each key is a string "field_0" to "field_79999" (~10 chars). Each value is either a plain value, a list of 1-4 plain values, or a dict of 1-4 plain values. Average maybe 1.5 values per key. So ~120k values. Memory: 80k strings × 60 bytes = 4.8 MB. 120k values × 30 bytes = 3.6 MB. Dict overhead: 80k × 100 bytes = 8 MB. Total ~16 MB.

Case 2: similar, ~16 MB.

Case 3: 1000 keys × 80 items = 80k values. 1000 lists × 80 items. Memory: 1000 × 60 + 80k × 30 + 1000 × 56 = 0.06 + 2.4 + 0.056 = ~2.5 MB.

Case 4: similar to case 1, ~16 MB.

Case 5: ~16 MB.

Case 6: 150k items. Memory: 150k × 30 + list overhead 150k × 8 = 4.5 + 1.2 = ~6 MB. Plus dict.

Case 7: 88k nodes. Memory: 88k dicts × 200 bytes = 17.6 MB. Plus leaves.

Case 8: 40k keys, 90% dicts with 1-4 keys. 40k × 0.9 = 36k dicts. Each dict has ~2.5 values. So 36k dicts × 200 + 90k values × 30 = 7.2 + 2.7 = ~10 MB.

Total: 16+16+2.5+16+16+6+17.6+10 = ~100 MB. Hmm, right at the limit. Let's reduce case 7 to depth 9, branching 3: 3^9 = 19683 leaves, total nodes = (3^10-1)/2 = 29524. Memory: 29.5k × 200 = 5.9 MB. Work: ~30k calls → ~10ms. A bit fast, but OK.

Or reduce the flat cases to 60k keys. 60k × 5 = 300k keys. Memory: 300k × 100 = 30 MB. Plus values. Maybe 45 MB for the 5 flat cases. Total: 45 + 2.5 + 6 + 17.6 + 10 = 81 MB. Good.

Let's use 60k keys for the flat cases.

Work per flat case: 60k keys × ~1.5 values = 90k values. ~90k is_job_ref calls → ~15-20ms. Hmm, maybe a bit fast. But the task says 1-200ms. 15ms is fine.

Actually, let me increase to 70k keys. 70k × 5 = 350k keys. Memory ~35 MB. Total ~90 MB. Work ~105k calls → ~20ms.

Let me just use 70k.

Hmm, but the task says "We run them on the original function and keep the 4 that do the most work." So the top 4 will be the ones with the most work. If all cases are ~20ms, that's fine.

Actually, let me make the cases more substantial to ensure they're in the 1-200ms range. Let's aim for ~50-100ms per call.

For a flat dict with 70k keys and ~1.5 values each, the function does:
- First loop: 70k iterations. For each, `is_job_ref(value)`. If value is a list/dict, push. 
- While loop: process pushed containers. ~20k containers, each with ~2.5 items. So ~50k more is_job_ref calls.

Total ~120k is_job_ref calls. At ~100ns each, ~12ms. Plus loop overhead. Maybe ~20ms.

To get to 50ms, we need ~300k is_job_ref calls. So 150k keys.

Let's use 120k keys for the flat cases. 120k × 5 = 600k keys. Memory: 600k × 100 = 60 MB. Plus values. Maybe 80 MB. Total with others: 80 + 2.5 + 6 + 17.6 + 10 = 116 MB. Over.

Hmm. Let's reduce the number of flat cases. We have 5 flat cases (1, 2, 4, 5, 8). We could make some of them smaller.

Actually, the task says "exactly 8 measured inputs". We can have different sizes. Let's make the "heavy" cases larger and the "light" cases smaller.

Let's use:
- Case 1: 120k keys (heavy, no refs)
- Case 2: 120k keys (heavy, local ref at end)
- Case 3: 1000 × 80 = 80k values (medium)
- Case 4: 100k keys (heavy, non-local refs)
- Case 5: 100k keys (heavy, mixed)
- Case 6: 150k list items (heavy)
- Case 7: depth 9, branching 3 → 29.5k nodes (light)
- Case 8: 40k keys × 3 inner (medium)

Memory: 
- Case 1: 120k × 100 = 12 MB + values ~6 MB = 18 MB
- Case 2: 18 MB
- Case 3: 2.5 MB
- Case 4: 100k × 100 = 10 MB + values ~5 MB = 15 MB
- Case 5: 15 MB
- Case 6: 6 MB
- Case 7: 6 MB
- Case 8: 10 MB
Total: ~90 MB. Good.

Work:
- Case 1: 120k keys × 1.5 = 180k values → ~180k calls → ~25ms
- Case 2: same → ~25ms
- Case 3: 80k values → ~80k calls → ~12ms
- Case 4: 100k keys × 1.5 = 150k values → ~150k calls → ~20ms
- Case 5: same → ~20ms
- Case 6: 150k items → ~150k calls → ~20ms
- Case 7: 29.5k nodes → ~30k calls → ~5ms
- Case 8: 40k keys + 90k inner = 130k calls → ~18ms

Hmm, these are all ~5-25ms. The task says 1-200ms. So they're within range. But maybe we want the top 4 to be more substantial.

Let me increase the heavy cases to 150k keys. Memory: 150k × 100 = 15 MB + values 7.5 MB = 22.5 MB per case. 4 heavy cases = 90 MB. Plus others = 110 MB. Over.

Hmm. Let's reduce the number of heavy cases. Actually, the task says "keep the 4 that do the most work". So we can have 4 heavy cases and 4 light cases. The light cases are just for diversity.

Let's make cases 1, 2, 4, 5 heavy (150k keys), and cases 3, 6, 7, 8 lighter.

Memory:
- Case 1: 150k × 100 = 15 MB + 7.5 MB = 22.5 MB
- Case 2: 22.5 MB
- Case 4: 22.5 MB
- Case 5: 22.5 MB
- Case 3: 2.5 MB
- Case 6: 6 MB
- Case 7: 6 MB
- Case 8: 10 MB
Total: ~114 MB. Over.

Let's use 120k keys for the heavy cases. 120k × 100 = 12 MB + 6 MB = 18 MB. 4 × 18 = 72 MB. Plus 24.5 = 96.5 MB. Good.

Work per heavy case: 120k × 1.5 = 180k values → ~180k calls → ~25ms. Hmm, still 25ms.

To get 50ms, we need ~350k calls. So 200k keys. Memory: 200k × 100 = 20 MB + 10 MB = 30 MB per case. 4 cases = 120 MB. Over.

Hmm. The memory limit is the constraint. Let's think about how to get more work per byte.

The function's work is proportional to the number of values (is_job_ref calls). Each value takes ~30-100 bytes. So 100 MB / 50 bytes = 2M values. 2M calls × 100ns = 200ms. So we could theoretically get 200ms with 100 MB.

But we have 8 cases, and only 4 are kept. So the total memory is for all 8 cases. If we want the top 4 to be ~100ms each, we need ~400k calls each. 400k values × 50 bytes = 20 MB each. 4 × 20 = 80 MB. Plus the other 4 cases. Total maybe 100 MB.

So let's aim for ~400k values in the heavy cases. That means ~250k keys with 1.5 values each. Memory: 250k × 100 = 25 MB + 12.5 MB = 37.5 MB per case. 4 cases = 150 MB. Over.

Hmm. The dict overhead is the issue. Each key-value pair in a dict takes ~100 bytes. So 250k keys = 25 MB just for the dict.

Alternative: use lists instead of dicts for the heavy cases. A list of 400k values takes 400k × 8 bytes (pointers) + 400k × 30 bytes (values) = 3.2 + 12 = 15 MB. Much more efficient.

But the top-level must be a dict. So we can have `{"inputs": [400k items]}`. That's case 6. Memory: 400k × 8 + 400k × 30 = 3.2 + 12 = 15 MB. Work: 400k is_job_ref calls → ~50ms. 

So let's make the heavy cases list-based.

But we need diversity. We can have:
- Case 1: large flat dict (no refs) — dict-based, 100k keys.
- Case 2: large flat dict with local ref at end — dict-based, 100k keys.
- Case 3: deep local ref — list-based.
- Case 4: non-local refs — list-based, 400k items.
- Case 5: mixed refs — list-based, 400k items.
- Case 6: big list — list-based, 400k items.
- Case 7: deep tree — tree-based.
- Case 8: many small dicts — dict-based, 50k keys.

Hmm, but then cases 4, 5, 6 are all list-based. That's not very diverse.

Let me think differently. The function's work is proportional to the number of values it examines. The most memory-efficient way to have many values is a flat list. But the top-level must be a dict. So `{"inputs": [...]}`.

But the function also processes nested containers. A list of lists of values is also efficient.

Let me design 8 cases with different structures:

1. **flat-dict-no-refs**: dict with 100k keys, values are plain. Work: 100k calls.
2. **flat-dict-local-ref-last**: dict with 100k keys, local ref at last. Work: 100k calls.
3. **deep-local-ref**: dict with 1000 keys, each a list of 100 items, local ref in the first list. Work: 100k calls.
4. **nonlocal-refs**: dict with 100k keys, 50% non-local refs. Work: 100k calls.
5. **mixed-refs**: dict with 100k keys, 50% non-local refs + local ref at end. Work: 100k calls.
6. **big-list**: `{"inputs": [300k items]}`. Work: 300k calls.
7. **deep-tree**: tree with depth 8, branching 4 → 65k leaves, 87k nodes. Work: 87k calls.
8. **many-small-dicts**: dict with 50k keys, each a dict with 4 keys. Work: 50k + 200k = 250k calls.

Memory:
1. 100k × 100 = 10 MB + values 3 MB = 13 MB
2. 13 MB
3. 1000 × 60 + 100k × 30 + 1000 × 56 = 0.06 + 3 + 0.056 = 3 MB
4. 13 MB
5. 13 MB
6. 300k × 8 + 300k × 30 = 2.4 + 9 = 11.4 MB
7. 87k × 200 = 17.4 MB
8. 50k × 100 + 50k × 200 + 200k × 30 = 5 + 10 + 6 = 21 MB

Total: 13+13+3+13+13+11.4+17.4+21 = 104.8 MB. Slightly over. Let's reduce case 8 to 40k keys: 40k × 100 + 40k × 200 + 160k × 30 = 4 + 8 + 4.8 = 16.8 MB. Total ~100 MB. Good.

Work:
1. 100k calls → ~15ms
2. 100k calls → ~15ms
3. 100k calls → ~15ms
4. 100k calls → ~15ms
5. 100k calls → ~15ms
6. 300k calls → ~40ms
7. 87k calls → ~12ms
8. 200k calls → ~25ms

The top 4 by work: case 6 (300k), case 8 (200k), and then cases 1-5 (100k each). That's fine.

Hmm, but the task says "keep the 4 that do the most work". So the top 4 will be measured. We want those to be substantial. Case 6 is 300k, case 8 is 200k, and then 100k each. That's fine.

Actually, let me make the flat dict cases heavier by using more keys. 150k keys → 150k calls. Memory: 150k × 100 = 15 MB + 4.5 MB = 19.5 MB per case. 5 cases = 97.5 MB. Plus others = 130 MB. Over.

Hmm. Let's keep 100k keys.

Actually, wait. The task says "Keep the data in memory under about 100 MB". So we should be under 100 MB. Let's aim for 80 MB.

Let me reduce the sizes a bit:
1. 80k keys → 80k calls. Memory: 80k × 100 = 8 MB + 2.4 MB = 10.4 MB
2. 80k keys → 10.4 MB
3. 1000 × 80 = 80k calls. Memory: 2.5 MB
4. 80k keys → 10.4 MB
5. 80k keys → 10.4 MB
6. 300k list items → 300k calls. Memory: 11.4 MB
7. 87k tree nodes → 87k calls. Memory: 17.4 MB
8. 40k keys × 4 = 200k calls. Memory: 16.8 MB

Total: 10.4+10.4+2.5+10.4+10.4+11.4+17.4+16.8 = 89.7 MB. Good.

Work: 80k, 80k, 80k, 80k, 80k, 300k, 87k, 200k. Top 4: case 6 (300k), case 8 (200k), case 7 (87k), and one of the 80k cases. That's fine.

Hmm, but the top 4 are all quite different in work. That's OK.

Actually, let me make case 7 (tree) heavier. Depth 9, branching 4: 4^9 = 262k leaves, total nodes = (4^10-1)/3 = 349k. Memory: 349k × 200 = 70 MB. Too much.

Depth 8, branching 4: 4^8 = 65k leaves, total nodes = (4^9-1)/3 = 87k. Memory: 17.4 MB. Work: 87k calls.

Let's keep it.

Actually, the tree is memory-inefficient. Let's replace it with a list-based deep structure.

Idea: a dict with one key mapping to a list of 100k items, each item is a list of 3 items. Total values: 100k + 300k = 400k. Memory: 100k × 56 + 300k × 30 + 100k × 8 = 5.6 + 9 + 0.8 = 15.4 MB. Work: 400k calls → ~50ms.

But that's similar to case 6. Let's make it different: a dict with 1000 keys, each mapping to a list of 100 items, each item is a dict with 3 keys. Total: 1000 + 100k + 100k dicts + 300k values = 500k values. Memory: 1000 × 60 + 100k × 8 + 100k × 200 + 300k × 30 = 0.06 + 0.8 + 20 + 9 = 30 MB. Work: 500k calls → ~60ms.

Hmm, that's heavy. Let's use it for case 7.

Actually, let me just keep the tree. It's diverse.

Let me finalize the code with the sizes above.

Wait, I should also consider that the function might be called with the same data multiple times, and the function doesn't modify it. So the thunks can return the same object.

Let me write the final code.

One more thing: the `checks()` function. The task says "2 or 3 small edge inputs (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise."

Let's include:
1. `{}` — empty dict.
2. `{"a": None}` — None value.
3. `{"a": {"$dnanexus_link": {"job": "localjob-0001"}}}` — local job ref.

These are small and should run without error.

Actually, the task says "an odd type". Maybe include a dict with an int value, or a list value. Let's include `{"a": 1}`.

Hmm, "empty, one element, None, an odd type". Let's do:
1. `{}` — empty.
2. `{"a": None}` — None.
3. `{"a": 1}` — odd type (int).

But we also want to test the local job ref path. Let's do:
1. `{}`
2. `{"a": None}`
3. `{"a": {"$dnanexus_link": {"job": "localjob-0001"}}}`

These are fine.

Now, let me write the code.

Actually, I realize I should double-check the import. The task says "Import it as `from dxpy.utils.local_exec_utils import has_local_job_refs`." So we do that. We don't need to import anything else.

But wait — the module `local_exec_utils` imports `dxpy`, `subprocess`, etc. When we import it, it will execute the module-level code. That should be fine.

Let me write the final code.

```python
import random

from dxpy.utils.local_exec_utils import has_local_job_refs


def _jbor(job_id, field="out"):
    return {"$dnanexus_link": {"job": job_id, "field": field}}


def _file_link(file_id):
    return {"$dnanexus_link": file_id}


def _plain(rng):
    r = rng.random()
    if r < 0.3:
        return rng.randint(0, 10**9)
    elif r < 0.6:
        return "v" + str(rng.randint(0, 10**9))
    elif r < 0.75:
        return None
    elif r < 0.85:
        return 1.5
    elif r < 0.95:
        return True
    else:
        return False


def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                file_link_ratio=0.0, list_ratio=0.1, dict_ratio=0.1):
    d = {}
    for i in range(n_keys):
        key = "field_%d" % i
        if local_ref_pos is not None and i == local_ref_pos:
            d[key] = _jbor("localjob-%06d" % i)
        elif nonlocal_ref_ratio > 0 and rng.random() < nonlocal_ref_ratio:
            d[key] = _jbor("job-%06d" % i)
        elif file_link_ratio > 0 and rng.random() < file_link_ratio:
            d[key] = _file_link("file-%06d" % i)
        else:
            r = rng.random()
            if r < list_ratio:
                d[key] = [_plain(rng) for _ in range(rng.randint(1, 4))]
            elif r < list_ratio + dict_ratio:
                d[key] = {"sub_%d" % j: _plain(rng) for j in range(rng.randint(1, 4))}
            else:
                d[key] = _plain(rng)
    return d


def _build_deep_local_ref(n_outer, n_inner, rng):
    d = {}
    for i in range(n_outer):
        lst = []
        for j in range(n_inner):
            if i == 0 and j == 0:
                lst.append(_jbor("localjob-deep"))
            else:
                r = rng.random()
                if r < 0.1:
                    lst.append({"x": _plain(rng), "y": _plain(rng)})
                elif r < 0.2:
                    lst.append(_file_link("file-%d-%d" % (i, j)))
                else:
                    lst.append(_plain(rng))
        d["k%d" % i] = lst
    return d


def _build_big_list(n, rng):
    lst = []
    for i in range(n):
        r = rng.random()
        if r < 0.5:
            lst.append(_plain(rng))
        elif r < 0.7:
            lst.append(_jbor("job-%06d" % i))
        elif r < 0.8:
            lst.append(_file_link("file-%06d" % i))
        elif r < 0.9:
            lst.append({"a": _plain(rng), "b": _plain(rng)})
        else:
            lst.append([_plain(rng), _plain(rng)])
    return {"inputs": lst}


def _build_tree(depth, branching, rng):
    if depth == 0:
        return _plain(rng)
    d = {}
    for i in range(branching):
        d["c%d" % i] = _build_tree(depth - 1, branching, rng)
    return d


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, file_link_ratio=0.2,
                     list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3,
                     file_link_ratio=0.2, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(300_000, _rng)
_CASE7 = _build_tree(8, 4, _rng)
_CASE8 = _build_hash(40_000, _rng, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]


def cases():
    return [
        ("flat-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("deep-local-ref", lambda: (_CASE3,)),
        ("nonlocal-refs", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
```

Wait, `_build_tree(8, 4, _rng)`: depth 8, branching 4 → 4^8 = 65536 leaves, total nodes = (4^9-1)/3 = 87381. Memory: 87k × 200 = 17.4 MB. Work: 87k calls. Good.

Now, let me double-check the total memory:
- Case 1: 80k keys. Each key ~10 chars (60 bytes). Value: 80% plain (~30 bytes), 10% list of 1-4 (avg 2.5) → 80k × 0.1 × 2.5 = 20k values, 10% dict of 1-4 → 20k values. Total values: 80k + 20k + 20k = 120k. Memory: 80k × 60 + 120k × 30 + dict overhead 80k × 100 = 4.8 + 3.6 + 8 = 16.4 MB.
- Case 2: same, 16.4 MB.
- Case 3: 1000 keys, 80k values. Memory: 1000 × 60 + 80k × 30 + 1000 × 56 = 0.06 + 2.4 + 0.056 = 2.5 MB.
- Case 4: same as case 1, 16.4 MB.
- Case 5: 16.4 MB.
- Case 6: 300k items. Memory: 300k × 30 + list overhead 300k × 8 = 9 + 2.4 = 11.4 MB.
- Case 7: 87k nodes. Memory: 87k × 200 = 17.4 MB.
- Case 8: 40k keys, 90% dicts. 36k dicts × 200 + 40k × 60 + 90k × 30 = 7.2 + 2.4 + 2.7 = 12.3 MB.

Total: 16.4 + 16.4 + 2.5 + 16.4 + 16.4 + 11.4 + 17.4 + 12.3 = 109.2 MB. Slightly over 100 MB.

Let's reduce case 1, 2, 4, 5 to 70k keys. Memory: 70k × 60 + 105k × 30 + 70k × 100 = 4.2 + 3.15 + 7 = 14.35 MB each. 4 × 14.35 = 57.4 MB. Total: 57.4 + 2.5 + 11.4 + 17.4 + 12.3 = 101 MB. Still slightly over.

Let's reduce case 7 to depth 7, branching 4: 4^7 = 16384 leaves, total nodes = (4^8-1)/3 = 21845. Memory: 21.8k × 200 = 4.4 MB. Total: 57.4 + 2.5 + 11.4 + 4.4 + 12.3 = 88 MB. Good.

But case 7 work drops to ~22k calls → ~3ms. That's a bit fast but within 1-200ms.

Alternatively, keep case 7 at depth 8 and reduce case 8. Case 8: 30k keys. Memory: 27k dicts × 200 + 30k × 60 + 67.5k × 30 = 5.4 + 1.8 + 2 = 9.2 MB. Total: 57.4 + 2.5 + 11.4 + 17.4 + 9.2 = 97.9 MB. Good.

Let's do that: case 8 with 30k keys.

Work:
- Case 1: 70k keys × 1.5 = 105k values → ~15ms
- Case 2: 105k → ~15ms
- Case 3: 80k → ~12ms
- Case 4: 105k → ~15ms
- Case 5: 105k → ~15ms
- Case 6: 300k → ~40ms
- Case 7: 87k → ~12ms
- Case 8: 30k + 67.5k = 97.5k → ~14ms

Top 4: case 6 (300k), case 1/2/4/5 (105k), case 8 (97.5k). That's fine.

Hmm, the top 4 are all around 100k-300k. The task says "keep the 4 that do the most work". So the top 4 will be measured. They should be substantial. 100k-300k calls is ~15-40ms. That's within 1-200ms.

Actually, let me make case 6 even heavier to ensure it's the top. 400k items. Memory: 400k × 30 + 400k × 8 = 12 + 3.2 = 15.2 MB. Work: 400k calls → ~55ms. Total memory: 57.4 + 2.5 + 15.2 + 17.4 + 9.2 = 101.7 MB. Slightly over.

Let's keep case 6 at 300k.

OK, let me finalize.

Actually, let me reconsider the memory estimate. Python objects have overhead. An int is 28 bytes. A string "v123456789" is ~50 bytes. A dict entry is ~100 bytes. A list of 2.5 items is ~56 + 2.5 × 8 = 76 bytes. So my estimates are roughly right.

Let me just go with the sizes and hope it's under 100 MB. The task says "under about 100 MB", so 100-110 MB might be acceptable. But let's try to stay under.

Let me reduce the flat cases to 60k keys. Memory: 60k × 60 + 90k × 30 + 60k × 100 = 3.6 + 2.7 + 6 = 12.3 MB each. 4 × 12.3 = 49.2 MB. Total: 49.2 + 2.5 + 15.2 + 17.4 + 9.2 = 93.5 MB. Good.

Work per flat case: 60k × 1.5 = 90k values → ~13ms.

OK, let's use 60k keys.

Final sizes:
- Case 1: 60k keys
- Case 2: 60k keys
- Case 3: 1000 × 80
- Case 4: 60k keys
- Case 5: 60k keys
- Case 6: 300k list items
- Case 7: tree depth 8, branching 4 (87k nodes)
- Case 8: 30k keys × 4 inner

Total memory ~93 MB. Work: 90k, 90k, 80k, 90k, 90k, 300k, 87k, 97.5k.

Top 4: case 6 (300k), case 8 (97.5k), and then cases 1-5 (90k each). That's fine.

Let me write the final code.

Wait, one more thing. The task says "Every case must run to completion on the original function without raising." Let's make sure there are no issues.

For case 3, the local ref is at i=0, j=0. The function's first loop iterates the dict keys: k0, k1, ..., k999. It pushes the lists. Then the while loop pops from the end: k999's list first, ..., k0's list last. So k0's list is processed last. The local ref is at j=0 of k0's list. So it's found at the very end. Returns True.

For case 7, the tree is a dict of dicts. The function traverses all. Returns False.

For case 8, the dict has 30k keys