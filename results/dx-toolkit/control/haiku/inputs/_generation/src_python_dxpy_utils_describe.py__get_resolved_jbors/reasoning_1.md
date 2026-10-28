The function `get_resolved_jbors` recurses over a structure. When it hits a job ref (JBOR), it calls `job_describe` from `dxpy.api`, which makes a network request. That would fail (no network) but the whole thing is wrapped in try/except that swallows everything. So it will just pass and not add to resolved_jbors.

Hmm — the task says: "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here". But here the network call is inside a try/except that catches everything. So the function runs to completion. The network call will fail (raise an exception) and be caught.

But wait — `job_describe` from dxpy.api — will it try to make a network request? It likely uses dxpy's HTTP layer which requires auth. It might raise quickly (no auth token) or might hang trying to connect. Hmm. Actually dxpy without a token raises DXError immediately I think. Let's think: `job_describe` in dxpy.api calls `dxpy.api` machinery which requires a security context. Without login, it raises an exception immediately ("No security context"). That gets caught by the bare except. So the function completes.

Actually there's a risk it hangs on network. But dxpy typically raises before making the request if not logged in. Let me consider: `dxpy.api.job_describe` -> `api_call` -> `DXHTTPRequest` -> needs auth. Actually it might attempt to read ~/.dnanexus_config or environment variables. If no token, it raises DXError immediately.

Hmm, but there's a risk. However, the recursion over lists/dicts is the main work. The JBOR handling is a minor part. We can design inputs to be mostly non-JBOR structures so the function does substantial recursion work without network calls... but wait, the function is only called recursively on things where `resolved_thing != orig_thing`. If they're equal it returns early. So we need differences.

Actually let's think about the design. The caller does:
```
for k in desc["input"]:
    if k in input_with_jbors and desc["input"][k] != input_with_jbors[k]:
        get_resolved_jbors(desc["input"][k], input_with_jbors[k], resolved_jbors)
```

So resolved_thing = desc["input"][k] (the resolved input), orig_thing = input_with_jbors[k] (the original input with JBORs). They differ where JBORs have been resolved.

So the structure: orig_thing contains JBOR dicts like `{'job': 'job-xxx', 'field': 'foo'}` or `{'$dnanexus_link': {'job':..., 'field':...}}`, and resolved_thing contains the actual resolved values.

The function recurses: for lists, iterate; for dicts (without '$dnanexus_link'), iterate keys.

Now, the network call: for each JBOR, it tries `job_describe`. If that raises, caught. Each JBOR triggers an attempted call. If that hangs, bad.

Hmm. Is there a way to avoid the network call entirely and still exercise the function? The function's main work is the recursion. If we include JBORs, network calls happen. If we don't include JBORs, then the function just recurses over matching structures — but that's the bulk of the work anyway (recursion over lists/dicts).

But to be truly representative, we should include JBORs. The question is whether dxpy will hang or fail fast.

Let me think about what dxpy does. `from dxpy.api import job_describe`. `job_describe(job_id)` calls `api_call("job-xxxx", "describe", ...)`. Actually:

```python
def job_describe(job_id, **kwargs):
    return api_call("job-xxxx", "describe", {"job": job_id}, **kwargs)
```

api_call -> `DXHTTPRequest` -> needs a security context. `dxpy.SECURITY_CONTEXT` is None if not logged in. Actually there's `_get_security_context()` which may try to read config files, but if none, raises `DXError("No security context found...")` before any network request. So it fails fast.

Actually I recall dxpy's `DXHTTPRequest.__init__` calls `_get_security_context()` which checks `dxpy.SECURITY_CONTEXT` and env vars and config file. If nothing, raises. So no network.

But to be safe, maybe set an environment so it fails fast? We can't fake the environment. Hmm, "Do not fake the environment either". Setting DX_SECURITY_CONTEXT env var would be faking. Better not.

Actually, could the request be attempted? If there's a token, it would attempt network. There's no token here, so it raises. Good.

But there's still risk of it trying to resolve a server (api.dnanexus.com) and hanging on DNS/connect. Only if a security context exists. It doesn't. So fine.

Actually, wait: let me reconsider. dxpy's `api_call` might be `dxpy.api` module's `api_call`. Let's just trust it fails fast.

Hmm, but the instructions say a function whose work starts with a request to a server cannot run. Here the request would fail immediately due to no credentials, caught by except. I think it's fine to run. But to be safe, I could design cases that mostly exercise recursion and include a modest number of JBORs.

Actually, let me reconsider: the risk is that job_describe actually attempts a network connection. If dxpy has no security context, `_get_security_context` raises. Let me be more careful — I'll include JBORs but keep the count moderate. If each call fails fast, it's fine.

Actually, there's another consideration: the bare `except:` catches everything including KeyboardInterrupt... but not relevant.

Let me now design the inputs.

The function signature: `get_resolved_jbors(resolved_thing, orig_thing, resolved_jbors)`.

`resolved_jbors` is a dict that accumulates results. Important: it's mutated across calls! The caller creates a fresh `resolved_jbors = {}` each time. But since our thunk returns the arguments and the function mutates `resolved_jbors`, we need a fresh dict each thunk call. Yes — "if the function changes it (adds to a dict)".

So each thunk should return a fresh `{}` for resolved_jbors. Good.

Also `resolved_thing` and `orig_thing` — the function doesn't modify them (only reads). So we can share them.

But wait: the early return `if resolved_thing == orig_thing: return`. So we need them to differ.

Now, "Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1,000,000 values." Rendering a big nested structure each call could be expensive but that's outside timing presumably. Keep under 1M values.

"keep what it returns (and anything it writes) under about 100,000 values" — it returns None but writes to resolved_jbors. So resolved_jbors should have under 100k entries. Since JBOR network calls fail, resolved_jbors stays empty. Good.

Hmm, so actually resolved_jbors will always be empty because job_describe fails. That means the "output" comparison is trivial. But the function still does the recursion work.

Now let's design 8 cases with diverse structures.

Structure types:
1. Deeply nested dicts and lists without JBORs, where resolved differs from orig in leaf values.
2. Lists of JBORs.
3. Dicts with '$dnanexus_link' JBORs.
4. Mixed large arrays.
5. Wide dicts.
6. Deep nesting.
7. JBORs with 'index'.
8. Combinations.

Let me think about what makes the function do work: recursion over the structure. Each node visited. For nodes that are equal, early return (but the parent still recurses into them... wait, no — the parent calls get_resolved_jbors(child_resolved, child_orig, ...) and if equal, returns immediately). So equal subtrees are cheap (one comparison). To maximize work, we want differences spread throughout so recursion goes deep.

Actually the top-level check `resolved_thing == orig_thing` compares the whole structure — that's O(n) itself. For a large structure with any difference, this comparison scans until it finds a difference. Hmm, dict equality compares keys and values.

Let me design the structure so that the top-level is a dict or list with many children, each child differing.

Let me create a helper to build a structure with JBOR leaves.

Design: a "resolved input" is a dict mapping input names to values. E.g., `{'reads': [...], 'reference': ..., 'settings': {...}}`.

Let me think about realistic dxpy runInput. Actually the function is called per-key on desc["input"][k] vs input_with_jbors[k]. So resolved_thing is the resolved value of one input, orig_thing is the original.

Let me just build structures.

Case design:

Case 1: Large flat list of JBORs (orig) vs resolved values (resolved). E.g., orig = [{'job': 'job-1', 'field': 'out'} for ...], resolved = [actual values]. The function iterates the list, each element is a JBOR -> tries job_describe -> fails -> caught. Work: N iterations plus N failed API calls. If API call fails fast, this is fast. But if it's slow... risky.

Hmm, maybe I should limit JBOR-heavy cases. But the function's characteristic behavior involves JBORs.

Let me reconsider whether job_describe fails fast. Let me think about dxpy.api.

```python
def api_call(method, resource, data, ...):
    ...
    return DXHTTPRequest(...)
```

Actually in dxpy, `dxpy.api` functions call `dxpy._dxhttp.DXHTTPRequest`. DXHTTPRequest's `__init__` calls `_get_security_context()`:

```python
def _get_security_context():
    if dxpy.SECURITY_CONTEXT is not None:
        return dxpy.SECURITY_CONTEXT
    ... check env vars, config file ...
    raise DXError('No security context found...')
```

Hmm actually I'm not 100% sure. But I believe it raises before network. Let me just go with it and keep JBOR counts moderate (like a few thousand).

Actually, an alternative safer approach: make the inputs have JBORs but... no, we can't avoid the call if there's a JBOR.

Hmm, but wait. Actually, could we make the API call succeed without network? No.

Let me reconsider: is there a risk the import `from dxpy.api import job_describe` fails? The module imports dxpy at top. dxpy is the repository itself. Should be importable.

OK here's a thought: to be safe about hanging, I could keep the number of JBORs small in each case, so even if each call takes, say, 10ms (unlikely), 100 JBORs = 1s. Hmm. Let's keep JBOR counts modest, like a few hundred max. But then the recursion work is small too.

Actually, the bulk of work in realistic usage: the structure is the run input, which can be large nested dicts/lists. JBORs appear at leaves. So a case could be a big nested structure where most leaves are plain values (differing) and a few are JBORs.

Wait, but if a leaf differs and it's not a JBOR and not a list/dict, the function does nothing (no branch matches). So plain leaf differences are cheap. The recursion only continues into lists and dicts.

So the work is: number of list/dict nodes visited. To make it heavy, we need many nested lists/dicts.

Hmm, so actually the recursion is over containers. Let's build deeply nested containers.

Let me design:

`orig_thing` = nested structure with JBORs at some leaves.
`resolved_thing` = same structure but with JBORs replaced by resolved values.

For non-JBOR leaves, both are equal, so the parent's recursion... wait, the parent iterates over its children and calls get_resolved_jbors on each. If a child (leaf value) is equal, early return. So we still pay one call per child. To make it heavy, many children.

So a wide dict with many keys, each key's value being a nested structure. Let's do that.

Let me write a builder:

```python
def _make(seed, n_top, depth, width):
    ...
```

Actually, let me think about a realistic dxpy input structure. A typical input might be:
```
{
  "reads": [{"$dnanexus_link": {"job": "job-xxx", "field": "output"}}, ...],
  "reference": {"$dnanexus_link": {"job": "job-yyy", "field": "out"}},
  "settings": {"advanced": {...}, "list": [...]},
  ...
}
```

Let me build several.

Let me define a helper that builds a pair (resolved, orig) given a spec.

I'll write:

```python
import random
from dxpy.utils.describe import get_resolved_jbors

def _jbor(job, field, index=None, wrapped=False):
    if wrapped:
        d = {'$dnanexus_link': {'job': job, 'field': field}}
        if index is not None:
            d['$dnanexus_link']['index'] = index
        return d
    else:
        d = {'job': job, 'field': field}
        return d
```

For a JBOR, resolved value is some scalar.

Now, the function for a JBOR: `jbor_to_str` -> job + ':' + field (+ '.' + index). Then if not in resolved_jbors, try job_describe. Fails -> caught. resolved_jbors unchanged.

Now design cases:

Case A: "wide-dict-many-jbors": orig is a dict with many keys, each value a JBOR (plain form). resolved is dict with same keys, scalar values. Function iterates keys, each is JBOR -> API call. If 500 keys -> 500 API calls. Risky if slow.

Hmm. Let me instead make most keys non-JBOR nested containers.

Actually, let me reconsider the whole thing. Since the API call likely fails fast (raising an exception), the cost is roughly the exception overhead. Python exception handling is fast-ish. 1000 exceptions ~ maybe 1ms. Fine.

But if the API call actually attempts network with a timeout... that would be catastrophic. Let me think harder.

dxpy's `api_call`:
```python
def api_call(method, resource, data, ...):
    ...
    return DXHTTPRequest('/' + resource + '/' + method, data, ...)
```

`DXHTTPRequest.__init__` -> `self._auth = _get_auth_header()` or similar. In dxpy/_dxhttp.py:

```python
def _get_auth_header():
    ...
```

Hmm. Actually, in newer dxpy, `DXHTTPRequest.__init__` does:
```python
self._auth = _get_security_context()  # or dxpy.SECURITY_CONTEXT
```

Let me recall dxpy's actual behavior: Running dxpy without login and calling an API function raises `DXError: No security context found`. I'm fairly confident. Actually I think it might be `dxpy.exceptions.DXError` with message about security context. Yes.

Actually hold on, there's also the possibility it reads `DX_API_HOST` etc. and attempts. But without a token it can't authenticate. I believe it checks token first.

I'll go with it, but to hedge, I'll keep JBOR counts per case moderate (e.g., ≤ 2000) and total work dominated by container recursion.

Hmm, actually, let me reconsider: maybe I should just not worry and include JBORs generously since they're the point of the function.

Let me now think about "the 4 that do the most work" — we run all 8 on the original and keep 4 with most work. So we want at least a few heavy ones.

Let me design 8 cases:

1. Deeply nested lists: a list of lists of lists... with JBORs at the bottom. 
2. Wide dict of JBORs (plain form).
3. Wide dict of JBORs (wrapped form).
4. Mixed nested dict/list with JBORs at some leaves and plain values at others.
5. JBORs with index.
6. Large array input (list of 10000 elements, some JBORs).
7. Deeply nested dicts (depth ~ 20) with JBORs.
8. A structure mirroring a real runInput: dict with keys like 'reads', 'reference', 'settings', 'stages', with nested.

Let me think about work: The recursion visits each container node once, plus for each leaf (non-container) it calls the function once and returns early. Wait — for a dict, the function iterates `for key in orig_thing: get_resolved_jbors(resolved_thing[key], orig_thing[key], resolved_jbors)`. So each value gets a call. For a list, each element gets a call.

So total calls ≈ number of nodes (containers + leaves) in the structure. Each call does an equality check at the start (`resolved_thing == orig_thing`). For containers this is a deep comparison — could be O(subtree size)! That's a problem: the top-level equality check compares the whole structure. For nested structures, the total work could be O(n^2) in the worst case... Actually no: the top-level check compares resolved vs orig fully (O(n) if equal, but they differ so it stops early at first difference). Hmm, dict comparison: `{'a':1} == {'a':2}` -> compares keys then values; stops at first mismatch. But it must check all keys are the same set first? Actually dict equality: checks len equal, then for each key in one, checks other has key and values equal. It iterates in some order. So it may scan many entries before finding a difference.

This is getting complex. Let's just build structures and let it be. The goal is realistic heavy work.

Key point: to avoid the early-return shortcut at the top, resolved_thing != orig_thing must hold.

Let me just build.

Let me write a generic builder that produces a nested structure of given shape, with JBORs at a fraction of leaves.

```python
def _build(rng, depth, breadth, jbor_prob, counter):
    # returns (resolved, orig)
    if depth == 0:
        if rng.random() < jbor_prob:
            job = "job-%d" % next(counter)
            field = "field%d" % rng.randrange(100)
            wrapped = rng.random() < 0.5
            orig = _jbor(job, field, wrapped=wrapped)
            resolved = rng.randrange(1000)
            return resolved, orig
        else:
            v = rng.randrange(1000)
            return v, v
    else:
        # choose list or dict
        ...
```

Hmm, but for non-JBOR leaves, resolved == orig, so the parent's call returns early. That's fine.

But note: for the top-level to differ, at least one leaf must differ (a JBOR leaf or... only JBOR leaves differ). So we need JBOR leaves.

Also, if depth>0 nodes: build children.

Let me make it concrete. I'll write specialized builders per case for clarity.

Actually, let me simplify: build a structure as nested dicts/lists, and convert some leaves to JBORs.

Let me write:

```python
def _make_tree(rng, depth, breadth, jbor_prob, ctr):
    if depth == 0:
        if rng.random() < jbor_prob:
            job = "job-%d" % next(ctr)
            field = "f%d" % rng.randrange(50)
            wrapped = rng.random() < 0.5
            if wrapped:
                orig = {'$dnanexus_link': {'job': job, 'field': field}}
                if rng.random() < 0.3:
                    orig['$dnanexus_link']['index'] = rng.randrange(10)
            else:
                orig = {'job': job, 'field': field}
            resolved = rng.randrange(10**6)
            return resolved, orig
        v = rng.randrange(10**6)
        return v, v
    if rng.random() < 0.5:
        # list
        n = rng.randrange(1, breadth+1)
        res = []
        org = []
        for _ in range(n):
            r, o = _make_tree(rng, depth-1, breadth, jbor_prob, ctr)
            res.append(r); org.append(o)
        return res, org
    else:
        # dict
        n = rng.randrange(1, breadth+1)
        res = {}; org = {}
        for i in range(n):
            k = "k%d" % i
            r, o = _make_tree(rng, depth-1, breadth, jbor_prob, ctr)
            res[k] = r; org[k] = o
        return res, org
```

Wait, but dict keys: the function iterates `for key in orig_thing` and accesses `resolved_thing[key]`. So resolved must have the same keys. Yes.

But careful: a dict that happens to look like a JBOR (has 'job' and 'field' keys, len 2) would be treated as a JBOR! Our generic dict uses keys "k0","k1" so it won't match. Good.

Also `'$dnanexus_link' not in orig_thing` check — our generic dicts don't have that key. Good.

Hmm, but there's subtlety: if a dict has exactly 2 keys and they're 'field' and 'job', is_job_ref returns True. Our dicts have keys k0,k1,... so fine.

Now, the recursion: at each node, the function first checks equality. If a subtree has no JBORs, resolved==orig, so it returns immediately. So the work is only along paths leading to JBORs, plus the top-level comparison.

Hmm, that means with jbor_prob low, most of the tree is skipped quickly. To make it heavy, we want JBORs spread widely.

Actually the top-level equality check: comparing two large nested structures that differ. Python's == on dicts/lists recurses. It will find the first difference. Depending on ordering, it might scan a lot. But it's O(size) at most.

Hmm, so total work might be less than expected. But that's the real function's behavior. Fine.

To maximize work: make the structure such that differences are everywhere so recursion goes to every leaf. E.g., every leaf is a JBOR. Then the function visits every node.

Let me make cases with high jbor_prob (like 0.8-1.0) in some cases, and low in others.

Actually, wait: if every leaf is a JBOR, then for a tree of N leaves, we do N API calls (all failing). If N is large (say 10000), that's 10000 failed API calls. Could be slow if each involves exception creation. Let's measure roughly: creating an exception and catching ~ 1 microsecond. 10000 -> 10ms. Fine.

But the risk of actual network... Let me hedge by keeping N of JBORs per case ≤ ~5000.

Hmm, actually, let me reconsider. Is `job_describe` really raising immediately? Let me think about dxpy more concretely.

In dxpy, `dxpy/api.py`:
```python
def job_describe(job_id, **kwargs):
    return api_call("job-xxxx", "describe", {"job": job_id}, **kwargs)

def api_call(method, resource, data, **kwargs):
    ...
    return DXHTTPRequest('/' + resource + '/' + method, data, **kwargs)
```

Wait, actually I think it's:
```python
def api_call(method, resource, data, ...):
    return DXHTTPRequest('/%s/%s' % (resource, method), data, ...)
```

And `DXHTTPRequest.__init__` in `dxpy/_dxhttp.py`:
```python
def __init__(self, resource, data, ...):
    ...
    self._auth = _get_auth_header()
```

Hmm, or maybe it's lazily done in `request()`. Actually, I recall:

```python
class DXHTTPRequest(object):
    def __init__(self, resource, data, ...):
        ...
        self._auth = _get_auth_header()  # may raise
```

Hmm, but I also recall that the security context check happens in `dxpy.api`'s `api_call` via `dxpy.SECURITY_CONTEXT`. Let me just trust it raises fast.

Actually, you know what, there's a real risk here. Let me think about whether the environment has a DX_SECURITY_CONTEXT. Probably not in the test environment. And no ~/.dnanexus_config. So it raises.

OK. But hold on — one more concern: if it does try network, DNS resolution of api.dnanexus.com might take time or hang. That would blow up the timing. Given the instructions explicitly mention that functions needing network "cannot run here", maybe they'd consider this... but the try/except makes it complete. The instruction says "A function whose work starts with a request to a server ... cannot run here, even if the rest of it only processes the answer." Hmm. But here the request is not the start of work; it's conditional and guarded.

Hmm, this is a judgment call. Let me think: the primary work of the function is recursion over the input structure. The API call is incidental and guarded. The function CAN run and complete. I think we should write it.

But to be safe against network attempts, maybe I should ensure that the API call raises before network. Actually, we can't control that.

Alternative: design all cases so that there are NO JBORs at all? Then the function just recurses over differing structures... but wait, if there are no JBORs, then resolved_thing == orig_thing everywhere (since only JBORs create differences)... unless we make non-JBOR leaves differ. But if a leaf differs and it's not a JBOR/list/dict, the function does nothing. So the recursion would still traverse containers.

Hmm, so we could have structures where resolved and orig differ in leaf scalar values (not JBORs). Then no API calls. The function recurses over all containers (because at each container level, resolved != orig, so it proceeds; then for each child it calls... and for scalar children that differ, it returns early after the equality check fails — actually it doesn't return early, it just falls through all branches and does nothing).

Wait: `if resolved_thing == orig_thing: return`. If a scalar child differs, it's not equal, so it proceeds to the branches: is_job_ref? no. isinstance list? no. isinstance dict? no. So nothing. Fine.

So we can build structures with scalar differences and no JBORs, exercising pure recursion. But that's not representative — the function's purpose is JBOR resolution. And the "most work" cases would be pure recursion.

Hmm, but the task says "Define a real workload: the kind of data this function gets in this repository". The data has JBORs.

I think including JBORs is correct and realistic. Let me include them but also hedge: I'll include JBORs in most cases. If network is an issue, the whole thing fails, but I'll take the risk since the function is designed to swallow errors.

Hmm, wait. Actually, let me reconsider. Let me reconsider the risk more carefully. If job_describe attempts a network connection with a long timeout, each call could take seconds. With even 10 JBORs, that's 10+ seconds per call, and the harness runs each input many times -> catastrophic. The harness would probably time out.

Given the explicit warning in the instructions, maybe the safe choice is to avoid JBORs entirely? But then the function does almost nothing meaningful...

Hmm, but actually, no: the recursion over containers IS the meaningful work when there are no JBORs? No — without JBORs, resolved==orig at leaves only if leaves are equal. If we make leaves differ (scalars), the recursion proceeds.

Hmm, but actually, is it realistic for resolved_thing and orig_thing to differ in scalar non-JBOR values? Not really.

Let me think about the actual dxpy behavior once more. I'm now fairly confident: dxpy raises `DXError` immediately when there's no security context, because `_get_security_context` is called and it checks config/env. Let me recall the code:

```python
def _get_security_context():
    if dxpy.SECURITY_CONTEXT is not None:
        return dxpy.SECURITY_CONTEXT

    env_var = os.environ.get('DX_SECURITY_CONTEXT')
    if env_var is not None:
        ...
    # look in config file
    ...
    raise DXError('No security context found; ...')
```

Hmm, but actually I think `_get_security_context` might be in `dxpy/security_context.py` and `DXHTTPRequest` uses `dxpy.SECURITY_CONTEXT` directly, raising if None.

Actually here's the thing — I recall that dxpy's `DXHTTPRequest.__init__` does:
```python
self._auth = _get_auth_header()
```
where
```python
def _get_auth_header():
    if dxpy.SECURITY_CONTEXT is None:
        raise DXError(...)
    return dxpy.SECURITY_CONTEXT.get_auth_header()
```

Something like that. Either way it raises.

Hmm, actually, I now recall that dxpy's api_call does something like:

```python
def api_call(method, resource, data, ...):
    ...
    if dxpy.SECURITY_CONTEXT is None:
        raise DXError('No security context found')
```

I'm fairly confident it fails fast. Let me go with including JBORs.

Actually, let me hedge differently: I'll make the JBOR counts per case moderate (hundreds to a couple thousand) so even if each call takes 1ms (very pessimistic for an immediate raise... well, 1ms would be 2s for 2000), hmm.

Let me just go with reasonable counts. Actually, let's think: if the API call raises immediately, cost per call ~ few microseconds. 2000 calls = ~10ms. Good. If it does network with 1s timeout, 2000 calls = 2000s. Bad. But I'll bet on immediate raise.

Let me limit to ~1000-3000 JBORs per case to keep it sane.

Hmm, actually, maybe safer: keep JBOR counts lower, like ≤ 500, and make the bulk of the work be container recursion (which is guaranteed no network). Let's do that: structures with many containers and a moderate number of JBORs.

But wait — container recursion only happens along paths to JBORs (since subtrees without JBORs are equal and return early). Hmm, no: the recursion visits a child node and calls the function on it. If that child is a container that is equal to its resolved counterpart, it returns early — one call, one equality check. So we do visit all children of any container that itself is "active" (i.e., differs). But a container differs iff some descendant differs (a JBOR). So active containers are exactly those containing a JBOR.

So if JBORs are sparse, few containers are active. To make lots of containers active, we need JBORs spread throughout.

OK so the work is: (number of containers on paths to JBORs) + (number of JBORs). To maximize, put JBORs everywhere.

So the trade-off is real. Let me just do it: many JBORs.

Actually, let's reconsider: maybe the equality check at the top of each call is the dominant cost for containers. For a container with a JBOR deep inside, `resolved_thing == orig_thing` compares the whole subtree until finding a difference. If the difference is at the end, that's O(subtree). So total could be O(n * depth) roughly. That's the real cost.

OK, let me just build and not over-think. Let me write the code.

Let me define module-level builders and generate the data once.

I need to be careful about total data size < 100MB and < 1M values per input.

Let me create cases:

```python
_RNG_SEED = 0

def _jbor_plain(job, field):
    return {'job': job, 'field': field}

def _jbor_wrapped(job, field, index=None):
    d = {'$dnanexus_link': {'job': job, 'field': field}}
    if index is not None:
        d['$dnanexus_link']['index'] = index
    return d
```

Case builders:

1. `_flat_list(n, wrapped)`: orig = list of n JBORs, resolved = list of n ints.
   Function: for i in range(n): call on element. Each is JBOR -> API call. Also top-level equality: lists differ at index 0 (int vs dict) -> fast.
   Work: n API calls.

2. `_nested_lists(depth, breadth)`: each level a list.

3. `_wide_dict(n)`: dict with n keys, each a JBOR.

4. `_deep_dict(depth)`: nested dicts.

5. `_mixed`: dict of lists of dicts...

6. `_index_jbors`: JBORs with index.

7. `_realistic_runinput`: dict with 'reads' (list of JBORs), 'reference' (JBOR), 'settings' (nested dict with JBORs), 'stages' (list of dicts).

8. `_large_array_of_jbors`: list of many JBORs.

Let me write a generic recursive builder with parameters, then instantiate.

I'll write:

```python
def _gen(rng, depth, breadth, jbor_prob, ctr, wrapped_prob=0.5):
    """Return (resolved, orig) pair."""
    if depth <= 0 or (depth > 0 and rng.random() < 0.0):
        pass
```

Hmm let me structure: at each node, decide leaf or container.

```python
def _gen(rng, depth, breadth, jbor_prob, ctr, wrapped_prob):
    if depth == 0:
        # leaf
        if rng.random() < jbor_prob:
            job = 'job-%d' % next(ctr)
            field = 'field%d' % rng.randrange(20)
            if rng.random() < wrapped_prob:
                idx = rng.randrange(5) if rng.random() < 0.3 else None
                orig = _jbor_wrapped(job, field, idx)
            else:
                orig = _jbor_plain(job, field)
            resolved = rng.randrange(10**6)
            return resolved, orig
        v = rng.randrange(10**6)
        return v, v
    # container
    if rng.random() < 0.5:
        n = rng.randrange(1, breadth + 1)
        res, org = [], []
        for _ in range(n):
            r, o = _gen(rng, depth - 1, breadth, jbor_prob, ctr, wrapped_prob)
            res.append(r); org.append(o)
        return res, org
    else:
        n = rng.randrange(1, breadth + 1)
        res, org = {}, {}
        for i in range(n):
            k = 'k%d' % i
            r, o = _gen(rng, depth - 1, breadth, jbor_prob, ctr, wrapped_prob)
            res[k] = r; org[k] = o
        return res, org
```

Wait, but there's an issue: dict with keys 'k0','k1' — if n==2, keys are k0,k1 -> not a JBOR. Good. But what if the dict has exactly keys 'job' and 'field'? Never, since we use 'k%d'. Good.

But another issue: a dict with a single key whose value is a dict with 'job'/'field'? That's len 1, key not '$dnanexus_link', so is_job_ref checks `len(thing)==1 and isinstance(thing.get('$dnanexus_link'), reftype)` -> get returns None -> False. Good.

Now, careful: `_jbor_plain` returns a dict with exactly keys 'job' and 'field'. is_job_ref: len==2, thing.get('field') is str, thing.get('job') is str -> True. Good.

`_jbor_wrapped` returns {'$dnanexus_link': {...}}. len==1, thing.get('$dnanexus_link') is dict, and its 'field' and 'job' are str -> True. Good.

Now, for the wrapped JBOR with index: the function's `get_index_from_jbor` returns the index. Then `jbor_to_str` includes '.index'. Then job_describe fails -> caught. Fine.

Now, the equality check: resolved is an int, orig is a dict -> differ. Good.

Now, the top-level: resolved_thing is the whole tree, orig_thing the whole tree. They differ (some leaf). Good.

Now let's think about the recursion cost. For each container node, the function does `resolved_thing == orig_thing`. For a container deep in the tree containing a JBOR, this comparison scans... Let's see, for a dict, `==` first checks len, then iterates keys of one dict, checking membership and value equality in the other. It stops at first unequal value. The order of dict iteration is insertion order. So if the JBOR is at the last key, it scans all. Hmm.

Anyway, this is the real behavior.

Now, potential issue: `resolved_thing == orig_thing` where resolved_thing is an int and orig_thing is a dict — fine.

But at the top level, if resolved and orig are huge and differ only at the last leaf, the comparison is O(n). Then the function recurses into children, each doing their own comparison. Total could be O(n^2) for a deeply nested single-child chain. That could be slow. Let's avoid super-deep chains.

Let me now pick sizes.

Let me define a helper to count and keep sizes reasonable.

Let me now write the cases.

Case 1: "flat-list-jbors": n=3000 JBORs in a flat list. resolved = list of ints.
   Work: 3000 API calls + 3000 element calls. If API fails fast, ~ fast. Hmm, 3000 API calls might be the dominant.

Hmm, I worry. Let me reduce to 1000.

Actually, let me reconsider the whole approach given the network concern. 

Alternative safe approach: make ALL cases have JBORs but few (like 50-200), and rely on container recursion for the bulk. But container recursion requires active containers...

Hmm, OK. Actually, you know, let me reconsider: is the API call really going to be attempted? Let me look at the imports of the module: `import dxpy`. And `from dxpy.api import job_describe` inside the function. So dxpy is imported at module load. dxpy's `__init__` might set up things but no network.

When `job_describe` is called, dxpy.api.api_call is invoked. In dxpy, `api_call` is defined in `dxpy/api.py`:

```python
def api_call(method, resource, data, ...):
    ...
    return DXHTTPRequest('/' + resource + '/' + method, data, ...)
```

Hmm, actually I recall dxpy.api has:
```python
def api_call(method, resource, data, timeout=None, ...):
    ...
```

And DXHTTPRequest is in dxpy._dxhttp. Its __init__:

```python
class DXHTTPRequest(object):
    def __init__(self, resource, data, headers=None, ...):
        ...
        self._auth = _get_auth_header()
        ...
```

and `_get_auth_header`:
```python
def _get_auth_header():
    if dxpy.SECURITY_CONTEXT is None:
        raise DXError("No security context found; ...")
```

Hmm, I'm not 100% sure it's in __init__ vs request(). If it's in request(), it still raises before network.

Actually, in dxpy, I believe there's `dxpy.api.api_call` which does:
```python
def api_call(method, resource, data, ...):
    ...
    return DXHTTPRequest('/' + resource + '/' + method, data, ...)
```

and DXHTTPRequest.__init__ starts with:
```python
        if dxpy.SECURITY_CONTEXT is None:
            raise DXError('No security context found; ...')
```

Hmm, actually I think there's a helper `_get_security_context()` that also reads config files. Let me not worry.

I'll go with it. If the environment has a security context (unlikely), it would attempt network — but then the harness environment presumably has no network, and it'd fail with a connection error, caught by except. Either way, caught. The only risk is a long timeout.

Hmm, that's the real risk: connection timeout. If no security context, no network attempt, no timeout. If security context present but no network, connection attempts fail fast usually (DNS failure) or hang.

Given the test environment likely has no DX credentials, I'll proceed.

Actually, hmm, let me reconsider one more time. The instructions say: "If the function cannot run here at all -- it needs network access, a remote service, credentials, ... and no input could avoid that, do not write code". Here, inputs CAN avoid it: inputs without JBORs avoid the network entirely. So the function CAN run here with appropriate inputs. So we should write code.

But then, should we avoid JBORs? The function's work without JBORs is pure recursion. Is that "the kind of data this function gets in this repository"? Partially — the input structure is realistic, but the JBORs are what trigger the resolution.

Hmm. I think the intended answer is to include JBORs (they're guarded by try/except, so the function completes). The task explicitly says "Every case must run to completion on the original function without raising." — with JBORs, it completes (exceptions caught).

I'll include JBORs. Let me balance: include a moderate number.

Let me now decide: I'll make cases with a few hundred to ~2000 JBORs, plus substantial container structure.

Hmm, actually, let me reconsider: what dominates? Let's just include a good mix and let the harness pick the top 4.

Let me write it.

Plan for 8 cases:

1. `flat-list-jbors`: orig = [JBOR]*2000 (plain), resolved = [int]*2000. 
2. `wrapped-list-jbors`: orig = [wrapped JBOR]*2000, resolved = [int]*2000.
3. `indexed-jbors`: orig = [wrapped JBOR with index]*1000, resolved = [list of ints]*1000. (resolved value a list, index picks element)
4. `wide-dict`: dict with 1500 keys, each value a JBOR (mixed plain/wrapped).
5. `nested-mixed`: depth-4 tree, breadth 3-5, jbor_prob 0.4 -> maybe ~1000 JBORs.
6. `deep-chain`: depth-30 nested dicts each with 2 keys, JBORs at leaves.
7. `realistic-runinput`: dict with 'reads' (list of 500 JBORs), 'reference' (JBOR), 'settings' (nested dict), 'stages' (list of dicts with JBORs).
8. `large-nested-lists`: lists of lists of dicts, many JBORs.

Let me estimate node counts.

For case 5: depth 4, breadth up to 5. Number of leaves ~ up to 5^4=625. jbor_prob 0.4 -> ~250 JBORs. Hmm small. Let me increase breadth.

Let me just make breadth larger, like 4-8, depth 3-4.

Hmm, let me think about total nodes for a tree of depth d and breadth b: b^d leaves. For b=6, d=4: 1296 leaves. Plus internal nodes ~260. Total ~1556 nodes. With jbor_prob=0.5, ~650 JBORs. OK.

For case 7 realistic: reads list of 500 JBORs + settings with 200 JBORs + stages 50 dicts each with 10 JBORs = 500. Total ~1200 JBORs.

Let me just write and not obsess.

Actually, I realize I should double check: does the function handle the case where resolved_thing is a list but orig_thing is a dict or vice versa? The function checks `isinstance(orig_thing, list)` and iterates `range(len(orig_thing))` accessing `resolved_thing[i]`. If resolved_thing isn't a list, that would error. But our structures keep them parallel. Good.

Also for dict: `isinstance(orig_thing, dict) and '$dnanexus_link' not in orig_thing` -> iterate keys of orig, access resolved[key]. Parallel. Good.

Now, one more: the top-level `resolved_thing == orig_thing` — if equal, return. We ensure differ.

Let me now also handle `checks()`: 2-3 small edge inputs.

Edge cases:
- Equal things: `get_resolved_jbors(5, 5, {})` -> returns immediately.
- Empty structures: `get_resolved_jbors([], [], {})` -> equal, returns. Or `get_resolved_jbors([1], [{'job':'j','field':'f'}], {})` -> JBOR path.
- None: `get_resolved_jbors(None, None, {})` -> equal -> return.
- A JBOR at top level: `get_resolved_jbors(1, {'job':'job-x','field':'f'}, {})` -> tries job_describe (fails, caught).

These may raise — but they won't.

Hmm, "checked only for identical behaviour, never measured. These may raise." OK.

Let me include:
- ("equal-scalars", lambda: (5, 5, {}))
- ("empty-list", lambda: ([], [], {}))
- ("top-level-jbor", lambda: (1, {'job': 'job-x', 'field': 'f'}, {}))

Wait, but for `top-level-jbor`, it calls job_describe. Same network concern. It's a check, not measured, so it runs once. Fine.

Hmm, actually maybe avoid JBOR in checks to be safe? But it's fine — it's just one call.

Actually, let me make the checks not involve network to be safe: use equal things and a non-JBOR difference.

- ("equal-scalars", lambda: (5, 5, {}))
- ("equal-nested", lambda: ({'a': [1,2]}, {'a': [1,2]}, {}))
- ("empty-dicts", lambda: ({}, {}, {}))

Hmm, but "odd type" edge cases are good. Let me do:
- ("equal-scalars", lambda: (5, 5, {}))
- ("empty-list", lambda: ([], [], {}))
- ("scalar-diff", lambda: (1, 2, {}))  -> not equal, not jbor, not list, not dict -> nothing.

Wait, "scalar-diff": resolved_thing=1, orig_thing=2. Not equal -> is_job_ref(2)? no. isinstance(2, list)? no. isinstance(2, dict)? no. Returns. Fine.

OK, but actually these checks don't test much. Let me include one JBOR check too. I'll include it — it's only run once for behavior comparison.

Hmm, but if it hangs... it's one call. If network timeout is 30s, that's 30s for the check. Acceptable-ish. But if the harness has a per-call timeout... Let me avoid JBOR in checks to be safe. Actually no — the checks are compared for identical behavior between original and modified. If the modified version changes behavior around JBORs, we'd want to catch it. But safety first.

Hmm. Let me include a JBOR check but... ugh. Let me think about what's more likely correct. The task wants edge inputs. I'll include a JBOR at top-level since that's a key edge case, and trust the fail-fast.

Actually, let me reconsider — if job_describe raises immediately, then all JBOR cases are cheap and the "work" is dominated by container recursion. Then cases with more containers win. That's fine.

Let me just write it.

Let me now also think: the thunk must return a fresh `{}` each time for resolved_jbors, and the same resolved_thing/orig_thing (function doesn't mutate them).

Let me write:

```python
def cases():
    return [
        ("flat-list-jbors", lambda: (_C1_RES, _C1_ORG, {})),
        ...
    ]
```

where _C1_RES etc. are module-level.

Now let me write the builders and generate.

Let me write the code carefully.

```python
import random

from dxpy.utils.describe import get_resolved_jbors


def _jbor_plain(job, field):
    return {'job': job, 'field': field}


def _jbor_wrapped(job, field, index=None):
    inner = {'job': job, 'field': field}
    if index is not None:
        inner['index'] = index
    return {'$dnanexus_link': inner}


_CTR = [0]

def _next_job():
    _CTR[0] += 1
    return 'job-%d' % _CTR[0]


def _leaf(rng, jbor_prob, wrapped_prob, index_prob):
    if rng.random() < jbor_prob:
        job = _next_job()
        field = 'field%d' % rng.randrange(30)
        if rng.random() < wrapped_prob:
            idx = rng.randrange(5) if rng.random() < index_prob else None
            orig = _jbor_wrapped(job, field, idx)
        else:
            orig = _jbor_plain(job, field)
        if index_prob and isinstance(orig, dict) and '$dnanexus_link' in orig and 'index' in orig['$dnanexus_link']:
            resolved = [rng.randrange(10**6) for _ in range(6)]
        else:
            resolved = rng.randrange(10**6)
        return resolved, orig
    v = rng.randrange(10**6)
    return v, v
```

Hmm, the index case: if the JBOR has an index, the resolved value should be a list (so that `field_value[jbor_index]` works — but that's in the API path which fails). Doesn't matter since API fails. Keep it simple: resolved is a scalar regardless.

Actually for realism, if index is present, resolved should be a list. But it doesn't matter functionally. I'll make it a list when index present.

Hmm, but the equality check: list vs dict -> differ. Fine.

Now the tree builder:

```python
def _tree(rng, depth, breadth, jbor_prob, wrapped_prob, index_prob):
    if depth <= 0:
        return _leaf(rng, jbor_prob, wrapped_prob, index_prob)
    if rng.random() < 0.5:
        n = rng.randrange(1, breadth + 1)
        res = []
        org = []
        for _ in range(n):
            r, o = _tree(rng, depth - 1, breadth, jbor_prob, wrapped_prob, index_prob)
            res.append(r)
            org.append(o)
        return res, org
    else:
        n = rng.randrange(1, breadth + 1)
        res = {}
        org = {}
        for i in range(n):
            k = 'k%d' % i
            r, o = _tree(rng, depth - 1, breadth, jbor_prob, wrapped_prob, index_prob)
            res[k] = r
            org[k] = o
        return res, org
```

Now specific builders.

Case 1: flat list of plain JBORs.
```python
def _flat_jbor_list(n, wrapped):
    rng = random.Random(0)
    res = []
    org = []
    for i in range(n):
        job = 'job-%d' % i
        field = 'field%d' % (i % 20)
        if wrapped:
            o = _jbor_wrapped(job, field)
        else:
            o = _jbor_plain(job, field)
        org.append(o)
        res.append(rng.randrange(10**6))
    return res, org
```

Hmm, but the function iterates `for i in range(len(orig_thing))` and calls on (res[i], org[i]). Each is a JBOR. So n API calls.

Case 2: same but wrapped.

Case 3: indexed JBORs: orig elements are wrapped JBORs with index; resolved elements are lists.

Case 4: wide dict.

Case 5: nested tree.

Case 6: deep chain.

Case 7: realistic.

Case 8: large nested.

Let me write them.

Actually, let me simplify: use `_tree` for several cases with different parameters.

Let me define:

```python
def _build_tree(seed, depth, breadth, jbor_prob, wrapped_prob=0.5, index_prob=0.2):
    rng = random.Random(seed)
    return _tree(rng, depth, breadth, jbor_prob, wrapped_prob, index_prob)
```

Cases:
- C1: flat list, 1500 plain JBORs.
- C2: flat list, 1500 wrapped JBORs.
- C3: flat list, 1000 wrapped JBORs with index.
- C4: wide dict, 1200 keys, mixed JBORs.
- C5: tree depth 4, breadth 5, jbor_prob 0.6 -> many.
- C6: tree depth 6, breadth 2, jbor_prob 0.8 (deep chain-ish).
- C7: realistic runinput.
- C8: tree depth 3, breadth 8, jbor_prob 0.5.

Let me estimate C5: depth 4, breadth 1-5 avg 3. Leaves ~ 3^4=81? That's small. Hmm, breadth random 1..5, expected 3. So 81 leaves. Too small. Let me use breadth 1..8 (avg 4.5) and depth 4 -> 4.5^4 ≈ 410 leaves. Still smallish.

Let me use depth 5, breadth 1..5 -> 3^5=243. Hmm.

Actually the number of nodes matters. Let me just make breadth larger: breadth = 1..10 (avg 5.5), depth 4 -> 5.5^4 ≈ 915 leaves, plus internal ~200. Total ~1100 nodes. With jbor_prob 0.6, ~550 JBORs. OK.

But the "work" also includes the equality comparisons which are O(subtree). For a balanced tree, the top-level comparison finds a difference quickly (first child differs). So comparisons are cheap. Total work ~ O(nodes).

Hmm, honestly the total work may be small (a few thousand operations) — maybe under 1ms. The task wants 1ms-200ms. Hmm.

Let's scale up. For 1ms, we need maybe ~10k-100k operations. Let me make bigger structures.

Let's do:
- C1: 5000 JBORs flat list -> 5000 API calls + 5000 node visits.
- C5: tree with ~5000 nodes.
- etc.

But the 1M value limit and 100MB limit. 5000 nodes is tiny. We could go to 100k nodes.

Hmm, but each node is a dict/list. 100k dicts ~ 100k * ~200 bytes = 20MB. OK.

But JBOR API calls: if 50k JBORs, and each call is a Python function call + exception, ~ 5 microsec each -> 0.25s. Too slow if it exceeds 1s. Hmm, and if the API call is slower...

Let me be moderate: aim for ~20k-50k total nodes per case, with JBORs maybe 5k-20k.

Hmm, risky. Let me think about the cost of a failed job_describe call. `from dxpy.api import job_describe` — this import happens inside the try each time! `from dxpy.api import job_describe` is executed on every JBOR. After the first, it's a cached module lookup — still some overhead (~1 microsecond). Then the call, then exception. Maybe 2-5 microseconds total. 10k JBORs -> 20-50ms. OK that's in range.

Actually the import statement inside the function: `from dxpy.api import job_describe`. Python caches, so it's a sys.modules lookup + getattr. ~0.5us.

The exception creation (DXError) might be slower — DXError construction with a message. Maybe 1-2us.

So ~5us per JBOR. 10k -> 50ms. Good.

Let me target ~5000-15000 JBORs per case for the heavy ones.

Hmm, but if the API call actually does network... Let me just go with moderate numbers and hope.

Hmm, actually, let me reconsider once more. I keep going back and forth. Let me look at the risk-reward:

- If job_describe fails fast: all good, cases run in ms.
- If job_describe does network with timeout: cases take forever, harness fails.

Given the instruction's emphasis, maybe the safest is to have NO JBORs at all. But then the function does only recursion over structures with no differences... wait, no differences means immediate return at top. So we'd need differences in non-JBOR leaves. Then the function recurses over containers but does nothing at leaves.

Is that a valid "workload"? It exercises the recursion logic (list/dict traversal), which is the bulk of the code. And the outputs (resolved_jbors stays empty) are compared. It's safe.

Hmm, but is it "the kind of data this function gets in this repository"? The structure is similar but the values aren't JBORs.

Hmm. The task says to build realistic inputs. I think including JBORs is more faithful. But safety...

Let me compromise: include JBORs in the measured cases (they're the point), but keep counts moderate (~2000-5000 per case). If job_describe fails fast, great. If it does network... well.

Hmm, actually, let me reconsider the dxpy code once more. I'm now recalling more specifically:

In `dxpy/api.py`:
```python
def api_call(method, resource, data, ...):
    ...
    return DXHTTPRequest('/' + resource + '/' + method, data, ...)
```

Wait no. Let me recall `dxpy._dxhttp.DXHTTPRequest`:

```python
class DXHTTPRequest(object):
    def __init__(self, resource, data, headers=None, auth=True, ...):
        ...
        if auth:
            self._auth = _get_auth_header()
        ...
```

and

```python
def _get_auth_header():
    if dxpy.SECURITY_CONTEXT is None:
        raise DXError("No security context found; ...")
    ...
```

Hmm, but actually I recall `dxpy.SECURITY_CONTEXT` is set by `dxpy.set_security_context()` or by reading env. And there's `dxpy.security_context` module.

Actually, I now strongly recall: dxpy has in `dxpy/__init__.py`:
```python
SECURITY_CONTEXT = None
```
and functions to set it. And `_get_auth_header` in `dxpy/_dxhttp.py`:
```python
def _get_auth_header():
    if dxpy.SECURITY_CONTEXT is None:
        raise DXError('No security context found; ...')
```

Hmm, but actually I think the check might be `dxpy.AUTH_HELPER`... 

Regardless, without login, it raises. I'm confident enough.

Actually, hold on. There's another possibility: dxpy might use `dxpy.api.api_call` which checks `dxpy.SECURITY_CONTEXT` and raises `DXError`. Either way.

OK let me just go with JBORs. Decision made.

Hmm, but actually, wait. Let me reconsider the number. What if the exception path is actually slower, like 20us? Then 5000 JBORs = 100ms. Still fine. 20000 = 400ms. Borderline.

Let me keep JBOR counts ≤ ~8000 per case.

Now let's also make sure the total work is at least ~1ms. Container traversal: each node visit is a function call (~1us). 20000 nodes -> 20ms. Good.

Let me design cases with ~10k-40k nodes total.

Data size: 40k dicts/lists -> ~10MB. Fine. Values count: each leaf is a value; 40k values < 1M. Fine.

Hmm, but "Its arguments are rendered before and after each call" — rendering a 40k-node structure could be slow (repr). 40k nodes repr ~ maybe 1MB string. That's done before and after each call. Might be slow but that's the harness's problem. Let's keep it moderate.

Actually, "keep each input's data under about 1,000,000 values" — so 1M values is the limit. Let's stay well under.

Let me settle on structures with ~10k-30k nodes.

Let me now write concrete builders.

C1: flat list of N plain JBORs. N=6000.
   orig = [{'job': 'job-i', 'field': 'field-i%20'} for i], res = [int].
   Nodes: 6000 JBORs + 6000 list elements = 12000 calls.

C2: flat list of N wrapped JBORs. N=6000.

C3: flat list of N wrapped JBORs with index. N=5000. res = list of ints (so element is a list).

C4: wide dict: N=6000 keys, each value a JBOR (alternating plain/wrapped). res = dict with same keys, int values.

C5: tree depth 4, breadth 1..8, jbor_prob 0.7. Nodes ~ sum of 4.5^k for k=0..4 ≈ 1+4.5+20+91+410 = 526. Too small. Let me use depth 5: +1845 = 2371. Still smallish. depth 6: +8300 = 10671. OK use depth 6, breadth 1..5 (avg 3): 1+3+9+27+81+243+729 = 1093. Hmm.

Let me use explicit large breadth. Let me do a "bushy" tree: depth 3, breadth 1..20 (avg 10.5): 1+10.5+110+1157 = 1279. Hmm.

To get 10k nodes with a tree, use depth 4, breadth 1..15 (avg 8): 1+8+64+512+4096 = 4681. depth 5: +32768 = 37449. Too many maybe.

Let me use depth 4, breadth 1..12 (avg 6.5): 1+6.5+42+274+1785 = 2109. Hmm.

OK let me just use a mix and not be too precise. I'll create a "wide-and-deep" tree with a target node count by controlling breadth.

Alternatively, build a structure that's a list of many dicts, each dict having several keys with JBORs. Like a list of 2000 dicts, each with 5 JBOR values. Nodes: 2000 dicts + 10000 JBORs + list = 12001. 

Let me do that for a couple of cases.

Let me define:

C5: list of 3000 dicts, each dict has 4 keys with JBOR values (mixed plain/wrapped). res = list of dicts with int values.
   Nodes: 1 (list) + 3000 (dicts) + 12000 (leaves) = 15001.

C6: nested tree depth 5, breadth 1..4, jbor_prob 0.8. Nodes ~ 1+3+9+27+81+243=364 containers, leaves 729 -> total ~1093. Too small. Let me use breadth 1..7 (avg 4): 1+4+16+64+256+1024=1365, leaves 4096 -> total 5461. OK.

Hmm, I'll just go with rough numbers.

C7: realistic runinput: dict with:
   - 'reads': list of 3000 JBORs
   - 'reference': 1 JBOR
   - 'settings': nested dict with 500 JBORs
   - 'stages': list of 100 dicts, each with 20 JBORs = 2000
   - 'metadata': dict of 500 JBORs
   Total JBORs ~6000, nodes ~ 12000.

C8: large array of JBORs with index: 8000.

OK, let me just write it.

Actually, let me reconsider the "most work" selection: the harness runs all 8 and keeps 4 with most work. So we want variety, and at least 4 heavy.

Let me write the code now.

One more consideration: `_next_job` uses a global counter — fine, module-level.

Let me also double check `is_job_ref` for our plain JBOR: `{'job': 'job-1', 'field': 'field0'}` — len 2, get('field') is str, get('job') is str -> True. Good. But note: `basestring` is from `..compat`. In Python 3 it's `str`. Our strings are str. Good.

Wrapped: `{'$dnanexus_link': {'job': ..., 'field': ...}}` — len 1, get('$dnanexus_link') is dict, and inner.get('field') str, inner.get('job') str -> True. Good.

With index: inner has 'index' too. len(thing)==1 still. get('$dnanexus_link') is dict. inner.get('field') str, inner.get('job') str -> True. Good.

Now `jbor_to_str`: job + ':' + field + ('.' + str(index)). Fine.

Now, one concern: the dict `{'$dnanexus_link': {...}}` — when the function encounters it as orig_thing, `is_job_ref` returns True first (checked before the dict branch). Good, so it won't recurse into it as a dict.

But what about resolved_thing for a wrapped JBOR? It's an int (or list). Fine.

Now, careful with the top-level structure: if the top-level orig is a dict that happens to have exactly 1 key '$dnanexus_link'... no, our top-level is a list or a dict with many keys.

Now let's write.

Also: the function signature is `get_resolved_jbors(resolved_thing, orig_thing, resolved_jbors)`. Thunks return `(resolved, orig, {})`.

Let me write the final code.

```python
import random

from dxpy.utils.describe import get_resolved_jbors


_JOB_CTR = [0]


def _job():
    _JOB_CTR[0] += 1
    return "job-%d" % _JOB_CTR[0]


def _plain_jbor(job, field):
    return {"job": job, "field": field}


def _wrapped_jbor(job, field, index=None):
    inner = {"job": job, "field": field}
    if index is not None:
        inner["index"] = index
    return {"$dnanexus_link": inner}


def _flat_list(n, wrapped, indexed=False, seed=0):
    rng = random.Random(seed)
    res = []
    org = []
    for i in range(n):
        job = _job()
        field = "field%d" % (i % 25)
        if wrapped:
            idx = rng.randrange(8) if indexed else None
            org.append(_wrapped_jbor(job, field, idx))
            if indexed:
                res.append([rng.randrange(10**6) for _ in range(10)])
            else:
                res.append(rng.randrange(10**6))
        else:
            org.append(_plain_jbor(job, field))
            res.append(rng.randrange(10**6))
    return res, org
```

Hmm, `_job()` uses a global counter shared across all builders. That's fine — jobs are unique. But the counter grows; fine.

Wait, but there's a subtlety: `jbor_to_str` produces job+':'+field. If two JBORs have the same string, the second is skipped (`if jbor_str not in resolved_jbors`). But since job_describe fails, nothing is ever added to resolved_jbors. So all JBORs attempt the call. Fine. Unique jobs anyway.

Now the dict-list builder:

```python
def _list_of_dicts(n_dicts, keys_per, wrapped_prob, seed):
    rng = random.Random(seed)
    res = []
    org = []
    for i in range(n_dicts):
        rd = {}
        od = {}
        for j in range(keys_per):
            job = _job()
            field = "field%d" % rng.randrange(25)
            if rng.random() < wrapped_prob:
                od["k%d" % j] = _wrapped_jbor(job, field)
            else:
                od["k%d" % j] = _plain_jbor(job, field)
            rd["k%d" % j] = rng.randrange(10**6)
        res.append(rd)
        org.append(od)
    return res, org
```

Tree builder:

```python
def _tree(rng, depth, breadth, jbor_prob, wrapped_prob):
    if depth <= 0:
        if rng.random() < jbor_prob:
            job = _job()
            field = "field%d" % rng.randrange(25)
            if rng.random() < wrapped_prob:
                orig = _wrapped_jbor(job, field)
            else:
                orig = _plain_jbor(job, field)
            return rng.randrange(10**6), orig
        v = rng.randrange(10**6)
        return v, v
    if rng.random() < 0.5:
        n = rng.randrange(1, breadth + 1)
        res = []
        org = []
        for _ in range(n):
            r, o = _tree(rng, depth - 1, breadth, jbor_prob, wrapped_prob)
            res.append(r)
            org.append(o)
        return res, org
    else:
        n = rng.randrange(1, breadth + 1)
        res = {}
        org = {}
        for i in range(n):
            k = "k%d" % i
            r, o = _tree(rng, depth - 1, breadth, jbor_prob, wrapped_prob)
            res[k] = r
            org[k] = o
        return res, org
```

Now build the module-level data.

Let me pick sizes:

C1: flat plain list, n=6000.
C2: flat wrapped list, n=6000.
C3: flat wrapped indexed list, n=5000.
C4: list of dicts: n_dicts=2500, keys_per=5 -> 12500 JBORs. Hmm that's a lot of API calls. Let me reduce: n_dicts=1500, keys_per=4 -> 6000 JBORs.
C5: tree depth 4, breadth 1..8, jbor_prob 0.7. Let me compute approximate nodes... I'll just run it mentally: not needed, it'll be whatever.
C6: tree depth 6, breadth 1..3, jbor_prob 0.9 (deep).
C7: realistic.
C8: flat plain list with n=3000 but with resolved values that are lists? Hmm.

Let me make C8 a "mixed large" case: a dict with many keys, each a list of JBORs.

Let me write:

```python
def _dict_of_lists(n_keys, per_list, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    for i in range(n_keys):
        rl = []
        ol = []
        for j in range(per_list):
            job = _job()
            field = "field%d" % rng.randrange(25)
            if rng.random() < 0.5:
                ol.append(_wrapped_jbor(job, field))
            else:
                ol.append(_plain_jbor(job, field))
            rl.append(rng.randrange(10**6))
        res["key%d" % i] = rl
        org["key%d" % i] = ol
    return res, org
```

C8: n_keys=200, per_list=30 -> 6000 JBORs.

C7 realistic:

```python
def _realistic(seed):
    rng = random.Random(seed)
    # reads: list of JBORs
    reads_res, reads_org = _flat_list(2500, wrapped=True, seed=seed)
    # stages
    ...
```

Hmm, let me just build a dict.

```python
def _realistic(seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    # reads
    rl, ol = _flat_list(2500, wrapped=True, seed=seed + 1)
    res["reads"] = rl
    org["reads"] = ol
    # reference
    res["reference"] = rng.randrange(10**6)
    org["reference"] = _wrapped_jbor(_job(), "output")
    # settings: nested dict
    sr, so = _tree(rng, 3, 4, 0.7, 0.5)
    res["settings"] = sr
    org["settings"] = so
    # stages: list of dicts
    st_res, st_org = _list_of_dicts(60, 10, 0.5, seed + 2)
    res["stages"] = st_res
    org["stages"] = st_org
    # metadata
    m_res, m_org = _dict_of_lists(20, 20, seed + 3)
    res["metadata"] = m_res
    org["metadata"] = m_org
    return res, org
```

Hmm, this uses `_tree` with a rng — fine.

Total JBORs: 2500 + 1 + (tree ~ some) + 600 + 400 = ~3500+.

OK.

Now, careful: `_flat_list(2500, wrapped=True, seed=seed+1)` — but `_flat_list` signature is `(n, wrapped, indexed=False, seed=0)`. OK.

Let me now assemble.

Also need to double-check: for the top-level dict in C7, `is_job_ref(dict)`? len is 5 keys -> no. Good. Then `isinstance(orig, dict) and '$dnanexus_link' not in orig` -> iterate keys. Good.

Now write the thunks.

```python
def cases():
    return [
        ("flat-plain-jbors", lambda: (_C1[0], _C1[1], {})),
        ("flat-wrapped-jbors", lambda: (_C2[0], _C2[1], {})),
        ("indexed-jbors", lambda: (_C3[0], _C3[1], {})),
        ("list-of-dicts", lambda: (_C4[0], _C4[1], {})),
        ("nested-tree", lambda: (_C5[0], _C5[1], {})),
        ("deep-tree", lambda: (_C6[0], _C6[1], {})),
        ("realistic-runinput", lambda: (_C7[0], _C7[1], {})),
        ("dict-of-lists", lambda: (_C8[0], _C8[1], {})),
    ]
```

Now, module-level generation:

```python
_C1 = _flat_list(6000, wrapped=False, seed=0)
_C2 = _flat_list(6000, wrapped=True, seed=1)
_C3 = _flat_list(5000, wrapped=True, indexed=True, seed=2)
_C4 = _list_of_dicts(1500, 4, 0.5, seed=3)
_C5 = _build_tree(4, 8, 0.7, 0.5, seed=4)
_C6 = _build_tree(6, 3, 0.9, 0.5, seed=5)
_C7 = _realistic(seed=6)
_C8 = _dict_of_lists(200, 30, seed=7)
```

where `_build_tree(depth, breadth, jbor_prob, wrapped_prob, seed)` returns (res, org).

```python
def _build_tree(depth, breadth, jbor_prob, wrapped_prob, seed):
    rng = random.Random(seed)
    return _tree(rng, depth, breadth, jbor_prob, wrapped_prob)
```

Now let's sanity check that each case's resolved != orig at top level. Yes, since there's at least one JBOR.

Hmm, C6: depth 6, breadth 1..3, jbor_prob 0.9. Might be a deep chain of single-child dicts. The top-level equality comparison would be O(n) each level -> O(n^2). With n ~ a few thousand, that's millions of ops -> could be slow. Let me reduce depth to 5 and breadth 1..4.

Actually, a deep chain: if each level has 1 child, then comparing at level 0 scans the whole chain (O(depth)), level 1 scans depth-1, etc. -> O(depth^2). With depth 6, that's 36. Negligible. But breadth 1..3 means the tree could have up to 3^6=729 leaves. Fine.

Hmm, actually the equality comparison for nested structures: `resolved == orig` where both are dicts. It compares key sets then values. For nested, it recurses. So comparing two identical-except-deep structures is O(size of subtree). For a balanced tree of size n, the top comparison is O(n) worst case (if difference is at the end). Then each child comparison O(subtree). Total O(n * depth). For n=10000, depth=6 -> 60000. Fine.

OK.

Now, let me reconsider the total node counts to ensure ≥1ms work. Each node visit = 1 Python function call (~0.5-1us). Plus equality checks. For 20000 nodes -> ~20ms. Good.

C1: 6000 JBORs + list iteration 6000 -> 12000 calls. Plus 6000 API attempts.
C2: same.
C3: same.
C4: 1500 dicts + 6000 JBORs + 1500 dict iterations -> ~9000 calls.
C5: tree ~ let's see, depth 4 breadth 1..8 avg 4.5: containers ~ 1+4.5+20+91 = 116, leaves ~410. Total ~526. Small. Let me increase breadth to 1..15 (avg 8): containers 1+8+64+512=585, leaves 4096 -> total 4681. Better. Let me use breadth 14.
C6: depth 6 breadth 1..3: containers ~ 1+2+4+8+16+32=63, leaves 64 -> total 127. Too small! Let me use breadth 1..5 (avg 3): depth 6 -> leaves 729, containers 364 -> total 1093. Still small. Use depth 7 breadth 1..5: leaves 2187, total ~3280. Hmm. Use breadth 1..6 (avg 3.5): depth 6 -> leaves 1838, total ~2570.

Hmm, trees are small. Let me just use bigger breadth.

Actually, let me reconsider: maybe use breadth fixed at some value rather than random. Let me make the tree builder take a fixed breadth and vary.

Let me redefine `_tree` to use breadth as a fixed number of children (with some randomness): n = rng.randrange(max(1, breadth-1), breadth+1). Eh, let me just use n = breadth always for containers, alternating list/dict. That gives predictable sizes.

Actually, variety is good. Let me use n = rng.randint(1, breadth).

Hmm. Let me just pick parameters that give big trees:
- C5: depth 4, breadth 1..12 (avg 6.5): leaves 6.5^4 ≈ 1785, total ≈ 2100. Meh.
- Use depth 5, breadth 1..8 (avg 4.5): leaves 4.5^5 ≈ 1845, total ≈ 2300.

Trees just aren't dense. Let me instead use the "list of dicts" pattern for the big cases and use trees for variety with moderate size.

Final plan:
- C1: flat plain list, 6000.
- C2: flat wrapped list, 6000.
- C3: flat indexed list, 5000.
- C4: list of dicts, 2000 dicts * 5 keys = 10000 JBORs.
- C5: tree depth 5, breadth 1..8, jbor_prob 0.8.
- C6: deep tree depth 7, breadth 1..4, jbor_prob 0.9.
- C7: realistic (~4000 JBORs).
- C8: dict of lists, 250 keys * 25 = 6250 JBORs.

Hmm, C4 with 10000 JBORs -> 10000 API attempts. If each is 5us, 50ms. OK.

Let me reduce a bit to be safe: C4 = 1500 dicts * 5 = 7500.

OK, enough. Let me write the final code.

Wait, one thing: the equality check at the top for C4 (list of dicts): resolved is a list of dicts of ints, orig is a list of dicts of JBOR dicts. Comparing: lists differ at element 0 (dict vs dict). Dict comparison: keys same ('k0'..'k4'), values differ (int vs dict). So it compares 'k0' values: int vs dict -> differ. Fast. Good.

For each element: call get_resolved_jbors(rd, od, {}). Not equal. od is dict, no '$dnanexus_link'. Iterate keys, call on each value (int vs JBOR dict). Each is a JBOR -> API call.

Good.

Now, `resolved_jbors` is fresh {} per thunk call. Good.

Let me also make sure the thunk is cheap: it just returns references and a new dict. Good.

Now `checks()`:

```python
def checks():
    return [
        ("equal-scalars", lambda: (5, 5, {})),
        ("empty-list", lambda: ([], [], {})),
        ("scalar-vs-scalar", lambda: (1, 2, {})),
    ]
```

Hmm, the third: resolved=1, orig=2, not equal, no branch -> nothing. Fine.

Maybe add a JBOR top-level check. Let me add it as a 4th? No, "2 or 3". So max 3.

Let me do:
- ("equal-nested", lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {}))
- ("empty-list", lambda: ([], [], {}))
- ("top-level-jbor", lambda: (7, {"job": "job-check", "field": "out"}, {}))

The top-level JBOR triggers job_describe once. Risk: one network attempt. Hmm. It's a check (not measured), run once. If it hangs 30s, the harness might time out. 

Hmm, let me avoid it. Use instead:
- ("scalar-vs-scalar", lambda: (1, 2, {}))

Actually, an "odd type" edge: None. `get_resolved_jbors(None, None, {})` -> equal -> return. Let me use:
- ("none-values", lambda: (None, None, {}))
- ("empty-list", lambda: ([], [], {}))
- ("equal-nested", lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {}))

These are safe. But they don't test the JBOR path. Hmm.

Actually, let me include a JBOR check but with a plain JBOR at top level. The behavior: tries job_describe, fails, caught, resolved_jbors stays {}. The modified version might differ. It's a meaningful check. I'll include it and accept the small risk.

Hmm. Decision: I'll include it. Actually... let me think about the risk/benefit. The benefit: catches behavioral differences in the JBOR path. The risk: a hang.

Given the whole measured set already includes thousands of JBOR calls, if the JBOR path hangs, everything fails anyway. So including one more in checks adds no additional risk. So include it.

OK final:

```python
def checks():
    return [
        ("equal-nested", lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {})),
        ("empty-list", lambda: ([], [], {})),
        ("top-level-jbor", lambda: (7, {"job": "job-check", "field": "out"}, {})),
    ]
```

Now let me finalize the code.

Let me re-examine `_flat_list` with indexed: `res.append([rng.randrange(10**6) for _ in range(10)])`. So resolved element is a list of 10 ints. The function: element is a JBOR (wrapped with index) -> jbor_to_str, job_describe fails -> caught. Fine.

Hmm wait, but there's a subtlety: for the indexed case, `resolved_thing[i]` is a list, `orig_thing[i]` is a wrapped JBOR dict. The function calls get_resolved_jbors(list, dict, {}). Not equal. Then `is_job_ref(dict)` -> True (it's a JBOR). So it doesn't recurse into the list. Good.

Now, `_list_of_dicts`: each dict has keys 'k0'..'k(n-1)'. If keys_per=2, the dict has 2 keys 'k0','k1' -> not a JBOR. Good. keys_per=5 -> fine.

Now writing final.

Let me also double check `_tree` produces dicts with keys 'k0'..'k(n-1)' — n could be 1 -> {'k0': ...}. is_job_ref? len 1, get('$dnanexus_link') is None -> False. Good. n=2 -> {'k0','k1'} -> not 'job'/'field'. Good.

But wait: what if a tree dict has n=2 and by chance keys are... no, always 'k%d'. Good.

Edge: what if a tree node is a dict with a single key '$dnanexus_link'? Never generated. Good.

Now, one more: in `_tree`, the leaf with jbor_prob returns (int, jbor_dict). The non-jbor leaf returns (v, v). Good.

Now the realistic builder. Let me write it carefully so resolved and orig are parallel.

```python
def _realistic(seed):
    rng = random.Random(seed)
    res = {}
    org = {}

    reads_res, reads_org = _flat_list(2500, wrapped=True, seed=seed + 1)
    res["reads"] = reads_res
    org["reads"] = reads_org

    res["reference"] = rng.randrange(10**6)
    org["reference"] = _wrapped_jbor(_job(), "output")

    settings_res, settings_org = _tree(random.Random(seed + 2), 3, 6, 0.75, 0.5)
    res["settings"] = settings_res
    org["settings"] = settings_org

    stages_res, stages_org = _list_of_dicts(80, 10, 0.5, seed + 3)
    res["stages"] = stages_res
    org["stages"] = stages_org

    meta_res, meta_org = _dict_of_lists(25, 20, seed + 4)
    res["metadata"] = meta_res
    org["metadata"] = meta_org

    return res, org
```

Wait, `_tree` signature is `_tree(rng, depth, breadth, jbor_prob, wrapped_prob)`. Good.

Hmm, `_list_of_dicts(n_dicts, keys_per, wrapped_prob, seed)` — I defined it as `(n_dicts, keys_per, wrapped_prob, seed)`. Let me keep consistent.

And `_dict_of_lists(n_keys, per_list, seed)`.

Total for C7: 2500 + 1 + tree(~) + 800 + 500 = ~3800+ JBORs.

Now let me write it all out.

Actually, I realize there might be an issue with `_flat_list` seed parameter ordering: `_flat_list(n, wrapped, indexed=False, seed=0)`. Calls: `_flat_list(6000, wrapped=False, seed=0)`. Good.

Let me write the final code.

Also need `import random` at top.

Let me also consider: should I worry that `get_resolved_jbors` might not be importable due to module-level side effects? The module imports dxpy, .printing, .pretty_print, ..compat. Should be fine.

Final code:

```python
import random

from dxpy.utils.describe import get_resolved_jbors


_JOB_CTR = [0]


def _job():
    _JOB_CTR[0] += 1
    return "job-%d" % _JOB_CTR[0]


def _plain_jbor(job, field):
    return {"job": job, "field": field}


def _wrapped_jbor(job, field, index=None):
    inner = {"job": job, "field": field}
    if index is not None:
        inner["index"] = index
    return {"$dnanexus_link": inner}


def _flat_list(n, wrapped, indexed=False, seed=0):
    rng = random.Random(seed)
    res = []
    org = []
    for i in range(n):
        job = _job()
        field = "field%d" % (i % 25)
        if wrapped:
            idx = rng.randrange(8) if indexed else None
            org.append(_wrapped_jbor(job, field, idx))
            if indexed:
                res.append([rng.randrange(10 ** 6) for _ in range(10)])
            else:
                res.append(rng.randrange(10 ** 6))
        else:
            org.append(_plain_jbor(job, field))
            res.append(rng.randrange(10 ** 6))
    return res, org
```

etc.

Let me finalize.

One concern: `_flat_list` for C1 with n=6000 and wrapped=False: `field = "field%d" % (i % 25)`. So fields repeat across jobs but jobs are unique, so jbor strings unique. Good.

Alright, writing the complete code.

Let me double-check the `_tree` recursion termination: depth decreases each call. Good.

Let me now write out everything.

Final answer below.

Actually, let me reconsider the sizes once more for safety. The biggest concern is total runtime of one call. Let's estimate C4: 1500 dicts, 7500 JBORs. Calls: 1 (top) + 1500 (dict elements) + 7500 (jbor leaves) = ~9000 calls, 7500 API attempts. If API attempt ~5us -> 37ms. Plus equality checks. ~40ms. Good, in range.

C1: 6000 JBORs -> 6000 API attempts -> ~30ms. Good.

C8: 250 keys * 25 = 6250 JBORs + 250 lists + 250*25 element calls = ~12500 calls. ~30ms.

C5: tree depth 5 breadth 1..8. Let's estimate: E[children] = 4.5 for containers. Number of containers at depth d: 4.5^d. Total containers = sum_{d=0}^{4} 4.5^d ≈ 1+4.5+20+91+410 = 526. Leaves = 4.5^5 ≈ 1845. Total nodes ≈ 2371. JBORs ≈ 0.8*1845 ≈ 1476. Work: ~2400 calls + 1476 API. ~10ms. A bit small but OK.

C6: depth 7 breadth 1..4 (avg 2.5): containers sum_{0}^{6} 2.5^d ≈ 1+2.5+6.25+15.6+39+97.7+244 = 406. Leaves 2.5^7 ≈ 610. Total ~1016. Small. Let me increase breadth to 1..6 (avg 3.5): containers sum 3.5^0..3.5^6 ≈ 1+3.5+12.25+42.9+150+525+1838 = 2572. Leaves 3.5^7 ≈ 6434. Total ~9000. JBORs ~0.9*6434 ≈ 5790. Better.

Hmm, but depth 7 with breadth 3.5 -> could be deep chains causing O(n*depth) comparisons. Fine.

Let me set C6: depth 6, breadth 1..6, jbor_prob 0.9. containers sum 3.5^0..3.5^5 ≈ 1+3.5+12.25+42.9+150+525 = 735. Leaves 3.5^6 ≈ 1838. Total ~2573. JBORs ~1654. OK.

Eh, fine. Let me use depth 6 breadth 1..7 (avg 4): containers sum 4^0..4^5 = 1+4+16+64+256+1024 = 1365. Leaves 4^6=4096. Total 5461. JBORs ~3686. Good.

OK: C5 = depth 5, breadth 1..8, jbor_prob 0.8. C6 = depth 6, breadth 1..7, jbor_prob 0.9.

Alright. Writing now.

Hmm, C5 with breadth 1..8: containers sum 4.5^0..4.5^4 = 1+4.5+20.25+91+410 = 527. Leaves 4.5^5 = 1845. Total 2372. Fine.

Let me bump C5 to breadth 1..12 (avg 6.5): containers sum 6.5^0..6.5^4 = 1+6.5+42+274+1785 = 2109. Leaves 6.5^5 = 11603. Total 13712. JBORs ~9290. Good, that's heavy.

OK C5 = depth 5, breadth 1..12, jbor_prob 0.8.

Alright, final.

Let me write the code.

def _build_tree(depth, breadth, jbor_prob, wrapped_prob, seed):
    return _tree(random.Random(seed), depth, breadth, jbor_prob, wrapped_prob)

Now module-level:

_C1 = _flat_list(6000, wrapped=False, seed=0)
_C2 = _flat_list(6000, wrapped=True, seed=1)
_C3 = _flat_list(5000, wrapped=True, indexed=True, seed=2)
_C4 = _list_of_dicts(1500, 5, 0.5, seed=3)
_C5 = _build_tree(5, 12, 0.8, 0.5, seed=4)
_C6 = _build_tree(6, 7, 0.9, 0.5, seed=5)
_C7 = _realistic(seed=6)
_C8 = _dict_of_lists(250, 25, seed=7)

Good.

Now let me make sure `_list_of_dicts` signature matches: `_list_of_dicts(n_dicts, keys_per, wrapped_prob, seed)`.

And `_dict_of_lists(n_keys, per_list, seed)`.

Writing final answer.