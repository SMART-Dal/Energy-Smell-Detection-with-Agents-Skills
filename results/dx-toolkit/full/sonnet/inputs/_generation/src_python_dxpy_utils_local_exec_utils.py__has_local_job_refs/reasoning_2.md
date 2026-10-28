Let me write the code. I need to be careful about the job ref format. Let me use the dict-with-job form for job refs, and string form for file links.

Let me finalize the sizes:
- Case 1: flat hash, 80k keys, no refs
- Case 2: flat hash, 80k keys, local ref at end
- Case 3: deep local ref, 1000 outer × 80 inner
- Case 4: flat hash, 80k keys, 30% non-local refs
- Case 5: flat hash, 80k keys, 30% non-local refs + local ref at end
- Case 6: big list, 150k items
- Case 7: list-based tree, depth 6, width 8
- Case 8: many small dicts, 40k keys × 3 inner

Let me write the builders.

Actually, for case 7, the tree is built recursively. Depth 6, width 8 → 8^6 = 262144 leaves. The recursion creates 8^6 + 8^5 + ... + 8^0 = (8^7-1)/7 = 299593 nodes. That's ~300k lists. Memory ~24 MB. Building time: 300k list creations, maybe 0.3s. Fine.

Wait, but the top-level must be a dict. So `{"root": tree}`. The function's first loop: field="root", value is a list → pushed. Then while loop processes the tree. Good.

Let me write the code.

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


def _build_tree(depth, width, rng):
    if depth == 0:
        return _plain(rng)
    return [_build_tree(depth - 1, width, rng) for _ in range(width)]


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(150_000, _rng)
_CASE7 = {"root": _build_tree(6, 8, _rng)}
_CASE8 = _build_hash(40_000, _rng, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]


def cases():
    return [
        ("large-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("local-ref-deep", lambda: (_CASE3,)),
        ("nonlocal-refs-only", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
```

Wait, there's an issue with `_CASE7`: the tree is built with `_build_tree(6, 8, _rng)`. The recursion depth is 6, fine. But the tree is a list of 8 elements, each a list of 8, etc. Total nodes = 8^6 + 8^5 + ... + 8^1 = 299592 lists + 262144 leaves. That's ~562k values. Memory: 299k lists × 56 + 262k values × 28 = 16.7 + 7.3 = 24 MB. OK.

But the function's processing: first loop, field="root", value is a list → pushed. Then while loop: pop the list (8 elements), iterate 8 items, each is a list → pushed. Then process each. Total ~300k is_job_ref calls + 262k leaf checks. Actually, the function checks each element: for a list, it iterates `range(len(thing))`, checks `is_job_ref(thing[i])`. For a list element that is itself a list, is_job_ref returns False, then it's a list → pushed. So each edge is one is_job_ref call. Total edges = 299592 (internal nodes) + 262144 (leaves) = 561736. So ~562k is_job_ref calls. That's ~150-200ms. Might be a bit slow. Let's reduce to depth 5, width 8: 8^5 = 32768 leaves, total nodes = (8^6-1)/7 = 37449. Edges = 37449 + 32768 = 70217. ~70k calls → ~20ms. Hmm, fast.

Let's use depth 6, width 6: 6^6 = 46656 leaves, total nodes = (6^7-1)/5 = 55987. Edges = 55987 + 46656 = 102643. ~100k calls → ~30ms. Good. Memory: 56k lists × 56 + 47k × 28 = 3.1 + 1.3 = 4.4 MB. Very small.

Hmm, but I want more work. Let's use depth 7, width 5: 5^7 = 78125 leaves, total nodes = (5^8-1)/4 = 97656. Edges = 97656 + 78125 = 175781. ~176k calls → ~50ms. Memory: 98k × 56 + 78k × 28 = 5.5 + 2.2 = 7.7 MB. Good.

Let's use depth 7, width 5.

Actually, let me reconsider. The tree is built recursively: `_build_tree(depth-1, width, rng)`. At depth 0, it returns `_plain(rng)`. So the leaves are plain values. The internal nodes are lists. So total lists = 5^7 + 5^6 + ... + 5^1 = (5^8-5)/4 = 97655. Leaves = 5^7 = 78125. Total values = 175780. Good.

Let me use depth 7, width 5.

Now, let me double-check the `_build_hash` function. For case 8 with `list_ratio=0.0, dict_ratio=0.9`:
- r < 0.0: never
- r < 0.9: dict
- else: plain

So 90% dicts, 10% plain. Each dict has 1-4 keys with plain values. So 40k keys → 36k dicts × ~2.5 inner values = 90k inner values + 40k top-level = 130k values. The function: first loop iterates 40k keys, pushes 36k dicts. Then while loop processes each dict: ~2.5 is_job_ref calls each → 90k. Total ~130k calls → ~35ms. Good.

Now, let me check the `checks()` cases. The `single-local-ref` case: `{"a": _jbor("localjob-0001")}`. `_jbor` returns `{"$dnanexus_link": {"job": "localjob-0001", "field": "out"}}`. If `is_job_ref` recognizes this, `get_job_from_jbor` returns "localjob-0001", startswith('localjob') → True. Returns True. Good.

If `is_job_ref` doesn't recognize it (unlikely), it's treated as a plain dict, pushed, and its fields iterated. Returns False. Still no error.

Now, let me think about whether the function modifies the input. It doesn't. So returning the same object is fine.

But wait — the task says "Its arguments are rendered before and after each call to see whether it changed them". So the harness renders the arguments. If the arguments are huge (e.g., 80k keys), rendering them might be slow. But that's the harness's problem, not ours. The task says "keep each input's data under about 1 000 000 values". Our largest is case 7 with ~176k values, case 6 with 150k, case 3 with 80k. All under 1M. Good.

Hmm, but rendering 176k values before and after each call, for many repetitions, could be slow. But the task says it's done. Let's not worry.

Actually, wait. The task says "we run the original function and a modified version of it on your inputs, each input many times in a row". So each input is run many times. If rendering is done before and after each call, that's a lot of rendering. But the task explicitly says "keep each input's data under about 1 000 000 values", so our sizes are fine.

Let me also consider: the task says "keep what it returns (and anything it writes) under about 100 000 values". The function returns a boolean. Fine.

Now, let me reconsider the job ref format once more. I want to make sure the local job ref cases actually return True, to exercise the `get_job_from_jbor` path. Let me use the dict form, which is the standard JBOR.

Actually, let me also include a case with the string form for job refs, to exercise both. But I'm not sure if the string form is recognized. Let me include it in case 4 (nonlocal refs) by using some string-form refs.

Hmm, but if the string form is not recognized, it's treated as a plain dict, which adds work but doesn't exercise get_job_from_jbor. That's fine.

Actually, let me not overcomplicate. I'll use the dict form for all job refs. For file links, I'll use the string form (which may or may not be recognized as job refs).

Wait, I didn't include file links in my builders. Let me add them. In `_build_hash`, I can add a `file_link_ratio` parameter. Or just use `_plain` and sometimes return a file link.

Actually, let me add file links to make the data more realistic. In the real repo, input_hash contains file links. Let me modify `_plain` to sometimes return a file link:

```python
def _plain(rng):
    r = rng.random()
    if r < 0.25:
        return rng.randint(0, 10**9)
    elif r < 0.5:
        return "v" + str(rng.randint(0, 10**9))
    elif r < 0.6:
        return None
    elif r < 0.7:
        return 1.5
    elif r < 0.8:
        return True
    elif r < 0.9:
        return False
    else:
        return _file_link("file-%06d" % rng.randint(0, 10**6))
```

Hmm, but `_file_link` returns a dict, which is a container. So the function would push it to q and iterate its fields. That adds work. And if `is_job_ref` recognizes string links as job refs, then it's checked via get_job_from_jbor. Either way, fine.

Actually, wait. If `_plain` returns a dict, then in `_build_hash`, the value is a dict, and the function treats it as a container. That's fine, but it changes the work profile. Let me keep `_plain` returning only non-container values, and add file links separately in the builders.

Let me add a `file_link_ratio` parameter to `_build_hash`:

```python
def _build_hash(n_keys, rng, local_ref_pos=None, nonlocal_ref_ratio=0.0,
                list_ratio=0.1, dict_ratio=0.1, file_link_ratio=0.0):
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
```

Let me use file_link_ratio=0.1 for some cases.

Hmm, but if `is_job_ref` recognizes string links as job refs, then file links are treated as non-local job refs. That's fine.

OK, let me finalize.

Actually, one more thought: the task says "Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit". Our data has varied values. Good.

Let me also make sure the `checks()` cases don't raise. `{}` → False. `{"a": None}` → False. `{"a": _jbor("localjob-0001")}` → True (or False if format not recognized). No raise.

Now, let me write the final code.

Wait, I should double-check the `_build_tree` recursion. With depth=7, width=5, the recursion depth is 7. Python's default recursion limit is 1000. Fine.

Let me also make sure the total build time is under 10s. Let's estimate:
- Case 1: 80k keys × ~1.5 values = 120k values. ~0.2s.
- Case 2: same. ~0.2s.
- Case 3: 1000 × 80 = 80k values. ~0.15s.
- Case 4: 80k keys × ~1.5 = 120k. ~0.2s.
- Case 5: same. ~0.2s.
- Case 6: 150k values. ~0.25s.
- Case 7: 176k values. ~0.3s.
- Case 8: 40k keys × ~3 = 120k. ~0.2s.

Total ~1.7s. Well under 10s. Good.

Memory: let's estimate more carefully.
- Case 1: 80k strings (keys) ~ 4 MB, 80k values ~ 3 MB, dict overhead ~ 4 MB. Total ~11 MB.
- Case 2: ~11 MB.
- Case 3: 1000 keys + 1000 lists + 80k values. ~6 MB.
- Case 4: ~11 MB.
- Case 5: ~11 MB.
- Case 6: 150k values + 1 list. ~6 MB.
- Case 7: 98k lists + 78k values. ~8 MB.
- Case 8: 40k keys + 36k dicts + 90k values. ~10 MB.

Total ~74 MB. Under 100 MB. Good.

Now, let me write the code.

Actually, I realize I should double check: does `has_local_job_refs` handle the case where `io_hash` is a dict with a value that is a dict containing `$dnanexus_link` as a string? Let's trace:

```python
for field in io_hash:
    if is_job_ref(io_hash[field]):
        ...
    elif isinstance(io_hash[field], list) or isinstance(io_hash[field], dict):
        q.append(io_hash[field])
```

If `io_hash[field]` is `{"$dnanexus_link": "file-xxxx"}`, and `is_job_ref` returns False (if it only checks dict-with-job), then it's a dict → pushed to q. Then:

```python
while len(q) > 0:
    thing = q.pop()
    if isinstance(thing, list):
        ...
    else:
        for field in thing:
            if is_job_ref(thing[field]):
                ...
```

`thing` is `{"$dnanexus_link": "file-xxxx"}`. `for field in thing` → field = "$dnanexus_link". `thing[field]` = "file-xxxx". `is_job_ref("file-xxxx")` → False. `isinstance("file-xxxx", list)` → False. `isinstance("file-xxxx", dict)` → False. So nothing. Fine.

No error.

OK, let me write the final code.

One more thing: the task says "For keyword arguments the thunk returns `call(...)`". Our function takes only one positional argument, so no keyword args needed.

Let me write it.

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


def _build_tree(depth, width, rng):
    if depth == 0:
        return _plain(rng)
    return [_build_tree(depth - 1, width, rng) for _ in range(width)]


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(150_000, _rng)
_CASE7 = {"root": _build_tree(7, 5, _rng)}
_CASE8 = _build_hash(40_000, _rng, file_link_ratio=0.05, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]


def cases():
    return [
        ("large-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("local-ref-deep", lambda: (_CASE3,)),
        ("nonlocal-refs-only", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
```

Wait, there's an issue with `_CASE2` and `_CASE5`: the local ref is at position 79,999. But the loop `for field in io_hash` iterates in insertion order. Since we insert keys in order 0..79,999, the local ref is the last key. So the function iterates all 80k keys before finding it. Good.

But wait, in `_build_hash`, the condition `if local_ref_pos is not None and i == local_ref_pos` comes first. So for i=79,999, it's a local ref. Good.

For `_CASE5`, the condition order is: local_ref_pos first, then nonlocal_ref_ratio. So for i=79,999, it's a local ref regardless of the nonlocal ratio. Good.

Now, let me think about whether the function returns True for `_CASE2` and `_CASE5`. The local ref is `_jbor("localjob-079999")` = `{"$dnanexus_link": {"job": "localjob-079999", "field": "out"}}`. If `is_job_ref` recognizes this, then `get_job_from_jbor` returns "localjob-079999", which starts with "localjob". So returns True. Good.

For `_CASE3`, the local ref is `_jbor("localjob-deep")` = `{"$dnanexus_link": {"job": "localjob-deep", "field": "out"}}`. Returns True. Good.

Now, let me reconsider the `_build_tree` function. With depth=7, width=5, the tree is a list of 5 elements, each a list of 5, etc. At depth 0, it returns `_plain(rng)`. So the leaves are plain values (int, str, None, float, bool). The function's while loop processes lists: `for i in range(len(thing)): if is_job_ref(thing[i]) ... elif isinstance(thing[i], list) or isinstance(thing[i], dict): q.append(thing[i])`. So for each element, it checks is_job_ref. For a list element, is_job_ref returns False, then it's a list → pushed. For a plain value, is_job_ref returns False, then it's not a list/dict → nothing. So total is_job_ref calls = number of edges = (5^8-5)/4 + 5^7 = 97655 + 78125 = 175780. Good.

Wait, actually the number of lists is 5^7 + 5^6 + ... + 5^1 = (5^8-5)/4 = 97655. The number of leaves is 5^7 = 78125. The number of edges from lists to their elements: each list at depth d has 5 elements. Total elements across all lists = 5 × 97655 = 488275. Hmm, that's not right.

Let me recompute. A tree of depth 7 (root at depth 7, leaves at depth 0) with branching 5:
- Level 7 (root): 1 list
- Level 6: 5 lists
- Level 5: 25 lists
- ...
- Level 1: 5^6 = 15625 lists
- Level 0: 5^7 = 78125 leaves

Total lists = 1 + 5 + 25 + ... + 5^6 = (5^7-1)/4 = 19531.
Total leaves = 5^7 = 78125.
Total nodes = 19531 + 78125 = 97656.

Each list has 5 elements. Total elements = 5 × 19531 = 97655. These elements are either lists (19530 of them) or leaves (78125). So total is_job_ref calls = 97655. Good.

Wait, I previously said 175780. That was wrong. Let me recompute: total elements = 5 × 19531 = 97655. So ~98k is_job_ref calls. That's ~25ms. Hmm, a bit fast.

Let me increase to depth=8, width=5: total lists = (5^8-1)/4 = 97656. Total leaves = 5^8 = 390625. Total elements = 5 × 97656 = 488280. ~488k is_job_ref calls → ~120ms. Memory: 98k lists × 56 + 390k values × 28 = 5.5 + 10.9 = 16.4 MB. Good.

But building 488k values... let's see. The recursion creates 390k leaves and 98k lists. ~0.5s. Fine.

Let me use depth=8, width=5.

Hmm, but wait: the function processes the tree by pushing lists to q. The root is `{"root": tree}`. First loop: field="root", value is a list → pushed. Then while loop: pop the root list, iterate 5 elements. Each is a list → pushed. Then pop one, iterate 5 elements... So it's a DFS. Total elements processed = 488280. Good.

Actually, let me double-check the memory. 390k leaves: each is an int (28 bytes), str (~50 bytes), None (16 bytes), float (24 bytes), bool (28 bytes). Average maybe 35 bytes. 390k × 35 = 13.6 MB. 98k lists × 56 = 5.5 MB. Total ~19 MB. Plus the dict `{"root": tree}`. Fine.

OK, let me use depth=8, width=5.

Now, let me reconsider case 6 (big list). 150k items. The function: first loop, field="inputs", value is a list → pushed. Then while loop: pop the list, iterate 150k items. For each item: is_job_ref. If it's a job ref (20% = 30k), get_job_from_jbor. If it's a dict (10% = 15k), pushed. If it's a list (10% = 15k), pushed. So total is_job_ref calls = 150k + 15k×2 + 15k×2 = 150k + 30k + 30k = 210k. ~50ms. Good.

Now, let me reconsider case 3. 1000 outer × 80 inner = 80k leaves. The function: first loop iterates 1000 keys, pushes 1000 lists. Then while loop processes each list: 80 items each → 80k is_job_ref calls. Plus the inner dicts (10% = 8k) pushed and processed: 8k × 2 = 16k. Total ~96k calls. ~25ms. Good.

Now, let me reconsider case 8. 40k keys, 90% dicts (36k), 5% file links (2k), 5% plain (2k). The function: first loop iterates 40k keys. For dicts (36k), pushed. For file links (2k), if is_job_ref recognizes string links, checked; else pushed. For plain (2k), checked. Then while loop processes 36k dicts + 2k file links. Each dict has 1-4 keys (avg 2.5) → 90k is_job_ref calls. Each file link has 1 key → 2k calls. Total ~40k + 90k + 2k = 132k calls. ~35ms. Good.

OK, I think the sizes are reasonable. Let me finalize.

Actually, let me reconsider the `_plain` function. It returns `True` or `False` sometimes. In Python, `isinstance(True, dict)` is False. Fine. `isinstance(1.5, dict)` is False. Fine.

Now, let me write the final code.

One more thing: the task says "Import the repository's modules exactly as shown in the task." The task shows `from dxpy.utils.local_exec_utils import has_local_job_refs`. So I should use that import. But do I need to import anything else? No, I just need the function. The builders use only standard library.

Wait, but the function's module imports `dxpy` and other modules. When I import `has_local_job_refs`, the module `local_exec_utils` is loaded, which imports `dxpy`, `.describe`, `.printing`, `.resolver`, `..compat`, `.file_load_utils`. These might have side effects or require network? Let's see: `dxpy` is the main package. Importing it might try to connect to the API? Usually not on import. Let's assume it's fine.

Actually, the task says "Everything you can know about the repository is in the task". So I'll just import as shown.

Let me write the final code.

Actually, I realize I should double-check: does `is_job_ref` require the `$dnanexus_link` value to be a dict with 'job', or does it also accept a string? I've been going back and forth. Let me just use the dict form for job refs, which is the most standard. And for file links, use the string form. If the string form is recognized as a job ref, it's treated as non-local (since "file-xxxx" doesn't start with "localjob"). If not, it's treated as a plain dict. Either way, no error.

Let me finalize.

Hmm, one concern: if `is_job_ref` returns True for `{"$dnanexus_link": "file-xxxx"}`, then `get_job_from_jbor` returns "file-xxxx". `startswith('localjob')` → False. So it's a non-local ref. That's fine.

But if `is_job_ref` returns True for ANY string link, then in case 1 (large-no-refs), the file links would be treated as non-local refs, and the function would call `get_job_from_jbor` on them. That's fine.

OK, writing the code now.

Let me also add a `checks()` case with a nested list containing a local ref, to test the list path.

```python
def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("single-local-ref", lambda: ({"a": _jbor("localjob-0001")},)),
    ]
```

That's 3 cases. Good.

Actually, let me make the third one a nested list: `{"a": [{"$dnanexus_link": {"job": "localjob-0001"}}]}`. That tests the list path. But the task says "small edge inputs". A single-element list is small. Let me use that.

Hmm, but `_jbor` returns a dict. So `{"a": [_jbor("localjob-0001")]}`. The function: first loop, field="a", value is a list → pushed. Then while loop: pop the list, iterate 1 item, is_job_ref → True, get_job_from_jbor → "localjob-0001", startswith → True. Returns True. Good.

Let me use that for the third check.

Actually, let me keep it simple and use the direct dict. Either is fine. Let me use the nested list to test the list path.

Final code:

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


def _build_tree(depth, width, rng):
    if depth == 0:
        return _plain(rng)
    return [_build_tree(depth - 1, width, rng) for _ in range(width)]


_rng = random.Random(0)

_CASE1 = _build_hash(80_000, _rng, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE2 = _build_hash(80_000, _rng, local_ref_pos=79_999, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE3 = _build_deep_local_ref(1000, 80, _rng)
_CASE4 = _build_hash(80_000, _rng, nonlocal_ref_ratio=0.3, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE5 = _build_hash(80_000, _rng, local_ref_pos=79_999, nonlocal_ref_ratio=0.3, file_link_ratio=0.1, list_ratio=0.1, dict_ratio=0.1)
_CASE6 = _build_big_list(150_000, _rng)
_CASE7 = {"root": _build_tree(8, 5, _rng)}
_CASE8 = _build_hash(40_000, _rng, file_link_ratio=0.05, list_ratio=0.0, dict_ratio=0.9)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("none-value", lambda: ({"a": None},)),
        ("nested-list-local-ref", lambda: ({"a": [_jbor("localjob-0001")]},)),
    ]


def cases():
    return [
        ("large-no-refs", lambda: (_CASE1,)),
        ("local-ref-last", lambda: (_CASE2,)),
        ("local-ref-deep", lambda: (_CASE3,)),
        ("nonlocal-refs-only", lambda: (_CASE4,)),
        ("mixed-refs", lambda: (_CASE5,)),
        ("big-list", lambda: (_CASE6,)),
        ("deep-tree", lambda: (_CASE7,)),
        ("many-small-dicts", lambda: (_CASE8,)),
    ]
```

Wait, I need to double-check the `_build_tree` with depth=8, width=5. The recursion depth is 8. The number of lists is (5^8-1)/4 = 97656. The number of leaves is 5^8 = 390625. Total elements = 5 × 97656 = 488280. Memory: 97656 lists × 56 = 5.5 MB, 390625 leaves × ~35 = 13.7 MB. Total ~19 MB. Good.

But building this tree recursively: the recursion creates 390k leaves. Each leaf is a call to `_plain(rng)`, which does a few RNG calls. 390k × ~1 µs = 0.4s. Plus 98k list creations. Total maybe 0.6s. Fine.

Hmm, but the recursion itself: `_build_tree(depth-1, width, rng) for _ in range(width)`. For depth=8, width=5, the number of calls is the number of nodes = 97656 + 390625 = 488281. Each call has overhead. ~0.5s. Fine.

OK, I think this is good. Let me also consider: the task says "One call should take roughly 1 ms to 200 ms on the original." Case 7 with ~488k is_job_ref calls might take ~120ms. Good.

Let me also consider case 1: 80k keys, 10% file links, 10% lists, 10% dicts, 70% plain. So 8k file links, 8k lists, 8k dicts, 56k plain. The function: first loop iterates 80k keys. For file links: if is_job_ref recognizes string links, checked; else pushed. For lists: pushed. For dicts: pushed. For plain: checked. Then while loop processes 8k lists (avg 2.5 items → 20k calls), 8k dicts (avg 2.5 items → 20k calls), 8k file links (1 item each → 8k calls). Total ~80k + 20k + 20k + 8k = 128k calls. ~35ms. Good.

Now, let me make sure the `checks()` cases don't raise. The third one: `{"a": [_jbor("localjob-0001")]}`. The function: first loop, field="a", value is a list → pushed. Then while loop: pop the list, iterate 1 item. `is_job_ref(item)` → True (if dict form recognized). `get_job_from_jbor(item)` → "localjob-0001". `startswith('localjob')` → True. Returns True. No raise.

If dict form not recognized: `is_job_ref(item)` → False. `isinstance(item, list)` → False. `isinstance(item, dict)` → True → pushed. Then process the dict: field="$dnanexus_link", value={"job": "localjob-0001", "field": "out"}. `is_job_ref(value)` → False (no $dnanexus_link). `isinstance(value, dict)` → True → pushed. Then process: field="job", value="localjob-0001". `is_job_ref` → False. `isinstance` → False. field="field", value="out". Same. Returns False. No raise.

OK, good.

Let me finalize. I'll write the code in the required format.

Actually, I want to double-check one thing: the task says "For keyword arguments the thunk returns `call(...)`". Our function takes no keyword arguments, so we just return a tuple with the positional argument. Good.

Also, the task says "A thunk takes no arguments and returns a tuple of positional arguments for the function". So `lambda: (_CASE1,)` is correct.

Let me write the final answer.