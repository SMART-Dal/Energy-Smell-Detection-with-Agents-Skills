The issue: every JBOR causes a `job_describe` API call which tries network access and fails (caught by bare except). Actually the try/except catches everything, so it should be fast... but maybe network attempts time out. Each JBOR triggers an API call attempt that may hang/timeout.

Wait — `job_describe` would try to make a network request. That takes time. With thousands of JBORs, that's way too slow. Actually each failing call may take a while.

Hmm, but the function catches exceptions. The problem is the network call itself is slow.

So we need inputs where the number of JBORs is small, so few API calls. But then the work is small. The task says the function cannot run if it needs network... but it catches exceptions. Let me think.

Actually the instructions say: "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here". But this function catches the exception. However the timing is dominated by network timeouts.

We need inputs that don't trigger network calls, or trigger very few. But we need substantial work.

Hmm. The function's work: traversing nested structures, and for each JBOR calling job_describe. If we avoid JBORs entirely, the function just recurses through the structure — that's the "work". But then it does no API calls.

Can we make structures with no JBORs that still do substantial work? Yes — large nested lists/dicts. But the function's only real work for non-JBORs is recursion. That's fast but with big enough data, could reach 1ms-200ms.

But wait — the "resolved_thing != orig_thing" check at top. If they're equal, returns immediately. We need them to differ so it recurses.

Actually, let's reconsider. The real issue is network calls. Can we make job_describe not do network? The function imports `from dxpy.api import job_describe`. We can't mock it. But maybe we can set up dxpy so the API call fails fast? No, that's faking environment.

Hmm, alternatively — could there be a way where `is_job_ref` is True but `job_describe` raises immediately? The bare except catches. If it raises immediately (e.g., invalid job id format), it's fast.

Actually job_describe probably validates and then makes an HTTP request. Without network, it might fail fast with connection refused, or hang with timeout.

Given the feedback says "took over 20s", the network attempts are slow. So we should minimize/eliminate JBORs.

Let me design inputs that are pure nested structures without any JBOR-shaped dicts, so no API calls. The function recurses through lists and dicts (dicts without '$dnanexus_link'). This gives real traversal work.

But is that "realistic"? The repo passes runInput which has JBORs. Hmm. But we need it to run.

Wait, actually maybe we can include a FEW JBORs (like 1-2) so at least some path is exercised, and the rest is plain nested data. But even 1 network call could be slow.

Actually, let's reconsider: maybe the network call fails fast. The "over 20s" was for thousands of JBORs. If we have like 10 JBORs it might be <200ms. Hmm, but risky.

Let me think about what makes it slow. If each job_describe takes ~5ms to fail (connection refused is fast), 6000 calls = 30s. If it's a timeout of e.g. 1s, even 20 calls = 20s.

Safest: zero JBORs. Pure nested structures. Let's make them big enough to take 1-200ms.

The recursion: for each element, checks equality, is_job_ref (isinstance + len checks), isinstance list, isinstance dict. For a deep/large structure this is O(n) with per-node overhead.

To get ~ms-100ms, we need maybe 100k-1M nodes. Let's target ~200k-500k nodes.

But the constraint: "keep each input's data under about 1,000,000 values". So up to ~1M values.

Let me build large nested structures without JBORs.

Actually wait — there's a subtlety. At the top: `if resolved_thing == orig_thing: return`. The comparison of two large structures is itself expensive. And it happens at every recursion level! So for nested structures, each node compares its subtree. That's O(n * depth) potentially. Good — that gives work.

Actually for a list, `resolved_thing == orig_thing` compares element-wise. Then recursion into each element compares again. So total work is O(sum of subtree sizes) = O(n * depth) for balanced.

Hmm, but we want them to differ so it doesn't early-return. Actually if equal at top, it returns immediately — no work. We need them to differ somewhere so it recurses.

Let's make structures where most leaves are equal but some differ, forcing full traversal. Actually if the top-level differs, it recurses; at each child, if child differs, recurse further.

Simplest: make the whole thing differ at leaves but structure identical. E.g., resolved = [[...], ...] and orig = [[...], ...] with different leaf values. Then every level compares unequal and recurses.

Let me design:

1. Deep nested lists (no JBORs): a list of lists of ... with ints, differing.
2. Large flat list of ints, differing.
3. Dict of dicts.
4. Mixed.

But these don't exercise the JBOR path at all. The task wants diversity of paths. Hmm.

Can we exercise the JBOR path cheaply? The JBOR path calls job_describe. If that fails fast... Let's test mentally: dxpy.api.job_describe makes an HTTP request to the DX API server. Without network, requests would fail. The time depends on DNS resolution etc. Could be fast (immediate connection error) or slow (DNS timeout ~5s).

Given the observed >20s, likely each call is slow-ish. With 6000 calls and 20s, that's ~3ms each — actually that's not that slow! 6000 * 3ms = 18s. So maybe each call is ~3ms.

Hmm, 6000 JBORs → 20s means ~3.3ms per call. So if we use ~50 JBORs, that's ~165ms. That's within range!

Wait but the original constraint said one call 1ms-200ms. With 50 JBORs at 3.3ms = 165ms. 

But actually the failing message was "took over 20s" for all. The threshold for dropping is 1s. So we need < 1s, ideally < 200ms.

Hmm, but 3.3ms is a guess. Let me be conservative and use few JBORs.

Actually, let me reconsider. Maybe the network call is not 3ms but the whole thing includes building. The message says "building or running it failed: took over 20s". Could be building too. But building is simple.

Let me be safe: use small numbers of JBORs (like 5-30) and large pure-structure parts.

Actually, hmm, but if job_describe takes a long time (e.g., DNS timeout of 5s), even 5 JBORs = 25s. Risky.

The safest is zero JBORs. But then we don't test the JBOR path and the "work" is just recursion.

Hmm. Let me think about whether there's a way to make job_describe fail instantly. The function does `from dxpy.api import job_describe`. If dxpy isn't configured with a server, job_describe might raise immediately. But we can't control that reliably.

Actually — wait. Let me reconsider the problem. The task says "A function whose work starts with a request to a server cannot run here". But this function catches exceptions and continues. The real issue is the time.

Given the feedback, I think the intended solution is to avoid JBORs (the network path) and focus on the recursion, OR use very few.

But then... the function is basically a tree walk. Is that enough to be a meaningful benchmark? The task says "make the function do substantial and different work: different paths through its code". With no JBORs, it's all one path.

Hmm, let me reconsider: maybe the network calls DO fail fast and the 20s was from having 6000 of them plus the O(n*depth) equality comparisons. Let me estimate: 6000 JBORs in a flat list. Top-level equality compares 6000 elements (each a dict comparison) — fast. Then recursion: for each element, is_job_ref true, jbor_to_str, then job_describe. If job_describe is ~3ms, 6000*3ms = 18s. Yes.

So it's the job_describe calls. To keep under 200ms, we need < ~60 JBORs.

But wait, we also need substantial work. With only 60 JBORs, the work is tiny (60 * 3ms = 180ms). That's actually fine for the 1-200ms range!

Hmm, but 3ms is a guess. If it's 50ms per call, 60 calls = 3s. Too slow.

Let me use a moderate number like 20-30 JBORs, and pad with pure structure to reach the work threshold.

Actually, you know what, let me reconsider whether job_describe even makes a network call when the job id is invalid. dxpy.api.job_describe(job_id) — it constructs a request. It probably just does the HTTP POST. No validation. So it makes a request.

Hmm. Let me think about the actual environment. These tasks run in a sandbox without network. A connection attempt to a non-existent host: DNS lookup fails. If DX_API_HOST is set to something, DNS fails fast (NXDOMAIN) or slow (timeout). Typically in sandboxes, DNS fails fast.

Given 6000 calls → 20s, ~3.3ms each. That's consistent with fast DNS failure + retries. So 30 JBORs → ~100ms. 

Let me go with a design: mostly pure nested structure (large), plus a modest number of JBORs to exercise that path. Actually, to be safe and still get 4 usable inputs, let me make several inputs with ZERO JBORs (pure structure, guaranteed fast) and a few with small JBOR counts.

Wait, but if an input has zero JBORs and the structure is large, the equality comparisons dominate. Let's make sure those are fast enough.

Let me design carefully.

Pure structure input: a large nested list. E.g., 100k ints in a flat list, resolved vs orig differing in one element. Top-level equality: compares 100k ints, ~few ms. Then recursion: for each element, equality check on ints (fast), is_job_ref (isinstance dict → False, fast). So ~100k iterations of cheap work. Maybe 20-50ms. Good.

Nested: list of 1000 lists each of 100 ints. Top equality compares 1000 sublists (100k comparisons). Then recurse into each: equality of 100-int list, then recurse. Total ~200k comparisons. Fine.

Deep nesting: depth 20, each level a list of 2. Small n, but the equality comparison at each level... Actually with depth 20 and branching 2, n = 2^20 = 1M. Too many. Let's do depth 15, branching 2 → 32768 leaves. Each level compares... hmm.

Actually let me just make big flat-ish structures.

Let me reconsider the goal: 8 inputs, need 4 that run. Let me make ALL 8 safe by minimizing JBORs. But the task wants diversity.

Alternative: maybe I should make inputs where JBORs are present but the dicts are NOT recognized as JBORs... no, that defeats the purpose.

Hmm, actually wait. Let me re-read: `is_job_ref(thing)` requires `len(thing)==2 and field/job are basestring` OR `len(thing)==1 and '$dnanexus_link' is dict with field/job`. 

What if I make dicts that look like JBORs but fail the check? Then they're treated as regular dicts (recursed into), no API call. That gives "dict" path without network. But that's not really the JBOR path.

OK here's my plan: 
- Make several inputs with pure nested structures (lists, dicts) — no JBORs. These exercise the list/dict recursion paths. Guaranteed fast.
- Make a couple inputs with a small number of JBORs (like 10-20) to exercise the JBOR path.

Let me estimate sizes to hit 1-200ms.

Let me just be generous with structure sizes but keep total values < 1M.

Let me write:

Helper to build nested list/dict structures with given number of leaves.

Case A: flat list of 200,000 ints, resolved and orig differ at some positions.
Case B: list of 2,000 lists, each 50 ints (100k leaves).
Case C: nested dicts: dict with 500 keys, each value a list of 100 ints (50k leaves).
Case D: mixed tree.
Case E: list of dicts.
Case F: deep-ish nesting.
Case G: with JBORs (small, ~15).
Case H: with JBORs (small, ~15), different shape.

Hmm, but if G and H are the only JBOR ones and they're slow, we still have A-F.

Actually, let me reconsider: do I even need JBORs? The task says "different paths through its code". Without JBORs, only list/dict paths. But the JBOR path is the "interesting" one. However, it requires network.

Given the constraint that the function "cannot run here" if it needs network... but it catches exceptions. The grader ran it and it took >20s, so it does run but slowly.

I think the pragmatic answer: use very few JBORs. Let me use like 5-10 per input. 10 * 3.3ms = 33ms. Safe.

But if per-call is 100ms, 10 calls = 1s. Borderline.

Hmm. Let me be even more conservative: 3-5 JBORs. 5 * 100ms = 500ms, still under 1s but over 200ms.

Ugh, uncertain. Let me think about what's most likely. The sandbox has no network. A TCP connection to a resolved-but-unreachable IP would take ~1s+ (SYN timeout). A DNS failure is fast.

If DX_API_HOST is "api.dnanexus.com", DNS might resolve (if there's a DNS server) to a real IP, then connection times out. Or DNS fails.

6000 calls in 20s = 3.3ms. If it were TCP timeout (~1-2s), 6000 calls would be hours. So it must be fast failure (~3ms). Good — DNS/connection fails fast.

So 3.3ms per JBOR call. To stay under 200ms, use < 60 JBORs.

I'll use ~30-50 JBORs per JBOR-input, padded with pure structure.

Wait, but actually — hmm, does job_describe retry? dxpy might retry on failure. If it retries 3 times with backoff, 3.3ms could be per full attempt. Anyway.

Let me go with a design where JBOR inputs have ~20 JBORs, and the rest is pure structure. Actually, let me reconsider — maybe the safest is to make the JBOR inputs have exactly a handful, and rely on pure-structure inputs for the "work".

Hmm, actually, let me reconsider once more. What if I make ALL inputs pure structure (no JBORs)? Then all 8 run fast and 4+ are usable. The downside is not testing the JBOR path, but the grader only checks that inputs run and produce outputs. The task says to exercise different paths, but "simple inputs that run are better than clever ones that do not."

But a pure-structure input where resolved == orig returns immediately with no work — need them to differ.

Also, I worry: with pure structure and no JBORs, is the work "substantial"? The equality comparison + recursion is real work. Let's make it big.

Let me design 8 diverse pure-structure inputs plus maybe 1-2 with a few JBORs.

Actually, let me include JBORs in a controlled way: I'll make inputs where the JBOR dicts are present but I limit their count. Let me do a mix:

1. flat-list-ints: 300k ints, differ at ~1000 positions. Pure.
2. list-of-lists: 3000 x 100 ints. Pure.
3. dict-of-lists: 300 keys x 200 ints. Pure.
4. nested-dicts: depth 4, 10^4 leaves. Pure.
5. list-of-dicts: 5000 dicts of 10 int fields. Pure.
6. mixed-tree: random. Pure.
7. few-jbors-flat: 20 JBORs + 100k ints. 
8. few-jbors-nested: 20 JBORs in nested dicts + structure.

Hmm, but 7 and 8 might still be slow if JBOR call is slow. But 20 * 3.3ms = 66ms, fine.

Actually, let me reduce JBOR count to be extra safe: 10 each.

Hmm, but if even 10 is slow... Let me just make 6 pure and 2 with JBORs. Then at least 6 usable.

Actually the requirement is 4 usable out of 8. Let me make 6 pure-structure (guaranteed) + 2 JBOR (risky). That gives 6 usable minimum.

Wait, but "keep the 4 that do the most work" — the grader keeps 4. So we need at least 4 that run. 6 pure ones run. Good.

Let me now also reconsider: is there any chance a pure-structure input fails? The function recursion on lists/dicts. For dicts without '$dnanexus_link'. Should be fine. No exceptions.

But careful: `resolved_thing[i]` requires resolved_thing to have same shape as orig_thing. If resolved is a list and orig is a list of same length, fine. If shapes mismatch, IndexError. But the function is called with resolved and orig of same shape in the repo. Let me ensure same shapes.

Also at top: `if resolved_thing == orig_thing: return`. If they're equal, returns. We need them to differ so recursion happens. But for nested structures, if a subtree is equal, that subtree returns immediately — less work. To maximize work, make them differ everywhere. But then... hmm, actually if they differ at a leaf, the parent's equality is False, so it recurses into all children, and each child's equality is checked. If a child is equal, it returns. To force full traversal, make every node differ.

Simplest: make orig = resolved but with leaves transformed (e.g., resolved leaf = v, orig leaf = v+1... but then is_job_ref on int is False). Actually for pure structure, leaves are ints. If resolved leaf != orig leaf, the parent lists differ.

But wait — for the recursion to go deep, we need each level to differ. If all leaves differ, then all internal nodes differ (since they contain differing leaves). Good.

Let me construct: orig = deep copy of resolved with each int leaf incremented. But then resolved_thing[i] indexing works.

Hmm, but if I just do `orig = resolved` with leaves changed, the structure is identical. Good.

Let me write a helper that builds a structure and a "differing" version.

Actually simpler: build structure S (nested lists/dicts of ints). Then build S' = same structure but leaves +1. Then call get_resolved_jbors(S', S, {})? Wait, signature is (resolved_thing, orig_thing, resolved_jbors). resolved_thing should be the resolved values, orig_thing the original (with JBORs). For pure structure, resolved = orig structure but leaves differ.

Let me just make two independent structures with same shape but different leaf values.

OK let me code it.

```python
import random

def _leaves_diff(resolved, orig):
    ...
```

Let me write a recursive builder:

```python
def _build(rng, depth, spec, seed):
    # returns (resolved, orig)
```

Hmm, let me make it concrete.

I'll write functions that produce (resolved, orig) pairs with identical shape, differing leaves.

```python
def _flat(n, seed, diff_every=1):
    rng = random.Random(seed)
    res = [rng.randrange(10**9) for _ in range(n)]
    org = list(res)
    for i in range(0, n, diff_every):
        org[i] += 1
    return res, org
```

Wait, if diff_every=1, every leaf differs. Good.

But actually, if only some differ, the equality check at top is False (since at least one differs), and recursion happens. For subtrees that are equal, they return early. To maximize work, all differ.

```python
def _list_of_lists(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = [[rng.randrange(10**9) for _ in range(n_inner)] for _ in range(n_outer)]
    org = [[v + 1 for v in row] for row in res]
    return res, org
```

Structure: list of lists. Top differs. Each row differs. Good.

```python
def _dict_of_lists(n_keys, n_inner, seed):
    rng = random.Random(seed)
    res = {"k%d" % i: [rng.randrange(10**9) for _ in range(n_inner)] for i in range(n_keys)}
    org = {k: [v + 1 for v in vs] for k, vs in res.items()}
    return res, org
```

```python
def _list_of_dicts(n, n_fields, seed):
    rng = random.Random(seed)
    res = [{"f%d" % j: rng.randrange(10**9) for j in range(n_fields)} for _ in range(n)]
    org = [{k: v + 1 for k, v in d.items()} for d in res]
    return res, org
```

Nested dicts:
```python
def _nested_dicts(depth, breadth, seed):
    # build recursively
```

Mixed tree with random structure:
```python
def _tree(rng, depth, breadth):
    if depth == 0:
        v = rng.randrange(10**9)
        return v, v + 1
    n = rng.randrange(1, breadth+1)
    if rng.random() < 0.5:
        res = []; org = []
        for _ in range(n):
            r, o = _tree(rng, depth-1, breadth)
            res.append(r); org.append(o)
        return res, org
    else:
        res = {}; org = {}
        for i in range(n):
            r, o = _tree(rng, depth-1, breadth)
            res["k%d" % i] = r; org["k%d" % i] = o
        return res, org
```

This gives identical shapes with differing leaves. 

Now sizes. Let me count "values" (elements). Constraint < 1M values per input.

1. flat 300k ints → 600k values (res+org). Hmm, "each input's data under about 1,000,000 values". 300k*2 = 600k. OK.

Actually is each input counted as res+org? Probably total. Let me keep total under 1M. So flat 300k → 600k total. Fine.

2. list of lists: 2000 x 100 = 200k leaves, x2 = 400k. Fine.

3. dict of lists: 200 x 300 = 60k, x2 = 120k. Maybe bump to 300x300=90k.

4. list of dicts: 5000 x 10 = 50k.

5. nested dicts: depth 4, breadth 5 → 5^4 = 625 leaves. Too few. Let me do breadth 10, depth 4 → 10^4 = 10k. Or depth 5, breadth 6 → 7776. Hmm.

Actually for nested dicts, let me just make a specific structure: dict of dicts of lists.

6. tree: depth 6, breadth 4 → up to 4^6 = 4096 leaves. Small. Let me do depth 7, breadth 4 → 16384. Or depth 6, breadth 6 → 46656. Random.

Let me just aim for ~100k leaves each, total ~200k values.

Now, will 100k leaves give 1-200ms? The work per node: equality comparison (for the subtree), isinstance checks, recursion. 

Hmm, the equality comparison is the expensive part. For a flat list of 300k ints, comparing 300k ints is ~10-30ms in CPython. Then recursion: 300k iterations, each doing `resolved_thing == orig_thing` (int comparison, cheap), is_job_ref (isinstance dict → False), isinstance list → False, isinstance dict → False. So ~300k * small. Maybe 30-50ms total. Good.

For nested: top equality compares the whole thing (deep comparison) — that's O(n). Then recurse into each child, each does its own equality O(subtree). Total O(n * depth). For depth 2 (list of lists), O(n*2). Fine.

Let me just make them reasonably large and test mentally.

Actually, I realize I should be careful about the equality comparison cost. For deeply nested structures, `resolved_thing == orig_thing` at the top does a full recursive comparison. Then at each level. So total is O(sum over nodes of subtree size) = O(n * avg_depth). For a tree of depth d with n leaves, that's O(n*d). If d is large, could blow up.

For depth 6, n=100k, that's 600k comparisons. Fine.

But for the "deep tree" case with depth 15, n small... let's avoid extreme depth.

Let me finalize 8 cases:

1. "flat-ints" — flat list of 300k ints, all differ.
2. "list-of-lists" — 2000 x 100.
3. "dict-of-lists" — 300 keys x 300 ints.
4. "list-of-dicts" — 4000 dicts x 12 fields.
5. "nested-dicts" — dict of dicts of lists, ~50k leaves.
6. "mixed-tree" — random tree, ~50k leaves, depth up to 6.
7. "jbors-flat" — 15 JBORs + 100k ints.
8. "jbors-nested" — 15 JBORs embedded in nested dicts + structure.

Hmm, for 7 and 8, I'm worried about the JBOR network calls. Let me make them very few: 8 each. 8 * 3.3ms = 26ms. Safe.

Actually, you know, let me reconsider whether to include JBORs at all. The grader said all 8 failed with >20s. If I include even 8 JBORs and each takes 2.5s (not 3.3ms), that's 20s. The 3.3ms estimate assumed 6000 calls. But maybe the 20s was dominated by something else... 

Let me compute: 6000 JBORs. If each job_describe takes T, total = 6000*T. For total=20s, T=3.3ms. This assumes the rest is negligible. Plausible.

But also the equality comparisons: flat list of 6000 dicts, comparing is fast. So yes, T≈3.3ms.

Hmm, but wait — actually in my original code, case 1 was 6000 plain JBORs in a flat list. Top equality: compares 6000 dicts → fast. Then for each, job_describe. So 6000 * T = 20s → T = 3.3ms. OK.

But actually there might be retries. Let's say T=3.3ms effective.

With 8 JBORs: 26ms. Safe.

But to be really safe, let me do 5 JBORs each. 5*3.3 = 16ms.

Hmm, but is 5 JBORs enough "work"? Combined with 100k ints, yes.

Actually, let me reconsider: maybe I should make ALL inputs have a few JBORs to exercise that path, but keep counts low (5-10). Then even if T=50ms, 10*50=500ms < 1s. And if T=3.3ms, 33ms.

But if T is large (say 500ms), 10 JBORs = 5s. Fail.

Risk tradeoff. Let me do: 6 pure-structure inputs (no JBORs, zero risk) + 2 inputs with 5 JBORs each. Then minimum 6 usable.

Wait, but the pure-structure inputs don't exercise the JBOR path at all. Is that acceptable? The task says exercise different paths. But we have list and dict paths. The JBOR path is exercised (weakly) in 2 inputs.

Hmm, actually, let me reconsider: maybe I can exercise the JBOR path without network by making the JBOR dict trigger an immediate exception before the network call. Looking at the code:

```python
if is_job_ref(orig_thing):
    jbor_str = jbor_to_str(orig_thing)
    if jbor_str not in resolved_jbors:
        try:
            from dxpy.api import job_describe
            job_output = job_describe(get_job_from_jbor(orig_thing)).get('output')
            ...
```

`jbor_to_str` calls get_job_from_jbor, get_field_from_jbor, get_index_from_jbor. These could raise if... no, they just access keys.

Hmm, what if get_index_from_jbor returns something and then... no.

Actually, `jbor_str = get_job_from_jbor(val) + ':' + get_field_from_jbor(val)`. If job is a str and field is a str, fine. If field is not a str... is_job_ref requires basestring. So fine.

What if we make jbor_str already in resolved_jbors? Then no API call! 

`if jbor_str not in resolved_jbors:` — if we pre-populate resolved_jbors with the jbor_str, the API call is skipped!

But resolved_jbors is passed as the third argument. We can pre-populate it! Then the function will skip the API call for those JBORs.

Wait, but the repo passes `resolved_jbors = {}` initially. But for our test, we control the argument. Hmm, but is that "realistic"? The function's purpose is to fill resolved_jbors. If we pre-fill it, we're testing a different scenario. But it IS a valid input — the function handles it (`if jbor_str not in resolved_jbors`).

Hmm, but then no work is done for those JBORs (just the string construction and dict lookup). That exercises the JBOR path without network! 

But wait — the timing: the function is called many times with the same arguments. If resolved_jbors is pre-populated, every call skips the API. Good, deterministic.

But actually, there's a subtlety: the function mutates resolved_jbors when it does resolve. If we pre-populate, it doesn't mutate. Fine.

But is pre-populating "cheating"? It's a legitimate input. The function checks membership. Hmm. But it changes the semantics — normally resolved_jbors starts empty and gets filled.

Alternatively, we could let the function do the API calls but... no.

Hmm, actually, the cleaner approach: pre-populate resolved_jbors with all the jbor_strs so no API calls happen. This exercises: is_job_ref, jbor_to_str, dict membership check. That's the JBOR path minus the API. 

But hold on — is that really testing the function's work? The API call is the "real work". Without it, it's just string ops. Hmm.

But given network constraints, it's the best we can do. And it does exercise the JBOR branch.

Actually wait, I realize there might be an even better approach. What if the JBOR dicts are such that `is_job_ref` is True but `jbor_to_str` raises? No, it won't.

Hmm, what about making the JBOR dict have a job/field that's a str, so jbor_to_str works, and pre-populating resolved_jbors. Yes.

OK so plan: for JBOR inputs, pre-populate resolved_jbors with the jbor_strs. Then no network calls. 

But wait — the thunk returns the arguments, and the function is called with them. If resolved_jbors is a dict that we pre-populate, and the function doesn't mutate it (because all keys present), then repeated calls are fine.

But careful: the function might mutate resolved_jbors if some jbor_str is NOT in it. So we must ensure ALL jbor_strs are pre-populated. Then no mutation.

Hmm, but actually — the function is called as `get_resolved_jbors(resolved_thing, orig_thing, resolved_jbors)`. We pass the same dict object each time (from the thunk). If the function doesn't mutate it, fine. If it does, it accumulates. So pre-populate fully.

Great, this solves the network problem while exercising the JBOR path!

Actually, let me reconsider. Is it realistic that resolved_jbors is pre-populated? In the repo, it starts empty. But the function is designed to handle pre-existing entries. Our input is a valid call. I think it's acceptable.

Hmm, but the task says "Prepare the way the repository's own callers do". The caller passes `{}`. Hmm. But we need to avoid network.

Alternatively... let me think again. Is there any way to make job_describe fast? 

What if we set dxpy's API server to a local address that refuses connections fast? That would be "faking the environment". Not allowed.

Hmm. What about setting `dxpy.api` module attributes? The function does `from dxpy.api import job_describe` inside the try. So it imports the actual function. We can't replace it (no monkeypatching).

OK, pre-populating resolved_jbors is the way.

But wait — actually, let me reconsider. If resolved_jbors is pre-populated, the function does almost nothing for JBORs. The "work" is then just the traversal + string construction. That's fine for a benchmark.

Hmm, but actually — I realize the grader keeps "the 4 that do the most work" and compares energy. If all inputs are similar, fine.

Let me now design with pre-populated resolved_jbors.

Actually, hmm, wait. There's a risk: if I pre-populate resolved_jbors but the thunk returns a NEW dict each time vs the same dict. The task says "the call is repeated many times, and every call gets the arguments of its own thunk call". So each call gets the args from calling the thunk. If the thunk returns the same dict object, and the function doesn't mutate it, fine. If the thunk returns a copy, also fine (but copying a large dict is expensive... well, it's in the thunk, not timed).

Let me have the thunk return a fresh copy of the pre-populated dict? No — if the function doesn't mutate, same object is fine and cheaper. But to be safe against mutation, return `dict(prepop)`.

Hmm, but if the function mutates resolved_jbors (adds keys), then returning the same dict accumulates. With full pre-population, no mutation. So same object is fine. But let me return a copy to be safe? The copy is in the thunk (untimed). But for a dict with many keys, copying is cheap-ish.

Actually, the resolved_jbors dict only needs keys for the JBORs. If we have few JBORs, few keys. Copy is cheap.

OK. Let me also double check: the function checks `if jbor_str not in resolved_jbors`. jbor_str = job + ':' + field (+ '.' + index). We pre-populate with exactly those strings.

For indexed JBORs (wrapped with index), jbor_str includes the index. Let me handle.

Let me now write the code.

Actually, let me reconsider the whole approach once more. The simplest safe approach: all 8 inputs use pre-populated resolved_jbors so no network. Then all 8 run. 

But do I want all 8 to have JBORs? Let me mix: some with JBORs (pre-populated), some pure structure.

Let me design 8:

1. "flat-ints": 300k ints, no JBORs. Pure traversal.
2. "list-of-lists": 2000 x 150 ints.
3. "dict-of-lists": 300 keys x 300 ints.
4. "list-of-dicts": 4000 dicts x 12 fields.
5. "nested-dicts": dict of dicts of lists.
6. "mixed-tree": random tree depth 6.
7. "jbors-flat": 3000 JBORs (pre-populated), flat list.
8. "jbors-nested": 2000 JBORs embedded, pre-populated.

Wait, for 7 and 8, with pre-population, no network. The work is: for each JBOR, is_job_ref (True), jbor_to_str (string concat), dict lookup. Plus traversal. 3000 JBORs → fast, maybe 5-10ms. Hmm, maybe not enough "work". But combined with large structure, fine.

Hmm, but actually, if pre-populated, the JBOR path is cheap. Let me make 7 and 8 have many JBORs (like 20k) to make the string work substantial. 20k * (is_job_ref + jbor_to_str + lookup) ≈ 20k * 2µs = 40ms. Good.

But wait — is_job_ref is called on every node. For a flat list of 20k JBOR dicts, each element: is_job_ref (len==2, .get('field') str, .get('job') str) → True. Then jbor_to_str. Then lookup. Then done.

Also the top equality: comparing 20k dicts. Fast.

OK, 20k JBORs is fine.

Hmm, but hold on. If resolved_jbors is pre-populated with 20k keys, and we return a copy each thunk call... copying 20k-key dict is ~1ms. Untimed. Fine.

Actually, simpler: return the same dict object (no mutation happens). But to be safe, let me return a copy. Actually, if the function doesn't mutate, same object is fine. Let me just return the same object (module-level dict). It's not mutated because all keys present.

Wait, is that guaranteed? Let me re-check the code path for a JBOR:
```python
if is_job_ref(orig_thing):
    jbor_str = jbor_to_str(orig_thing)
    if jbor_str not in resolved_jbors:
        ... # would add
```
If jbor_str IS in resolved_jbors, nothing happens. So no mutation. 

But there's a subtlety: what if two different JBORs produce the same jbor_str? Then only the first would be added (if not pre-populated). With pre-population, both skip. Fine.

OK so module-level resolved_jbors dict, pre-populated, reused. Safe.

Hmm, but actually — wait. What if the grader checks that arguments are unchanged? "Its arguments are rendered before and after each call to see whether it changed them". If resolved_jbors is unchanged, good. So pre-population ensures no change. 

Now let me also make sure resolved_thing and orig_thing are not mutated. The function only reads them. Good.

Now, let me write the builders.

Let me handle the "values" count. For a flat list of 300k ints, resolved+orig = 600k values. Plus if JBORs, the dicts count as values too. Let me keep under 1M.

Let me write:

```python
import random

from dxpy.utils.describe import get_resolved_jbors


def _flat_ints(n, seed):
    rng = random.Random(seed)
    res = [rng.randrange(10**9) for _ in range(n)]
    org = [v + 1 for v in res]
    return res, org


def _list_of_lists(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = [[rng.randrange(10**9) for _ in range(n_inner)] for _ in range(n_outer)]
    org = [[v + 1 for v in row] for row in res]
    return res, org


def _dict_of_lists(n_keys, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    for i in range(n_keys):
        k = "k%d" % i
        row = [rng.randrange(10**9) for _ in range(n_inner)]
        res[k] = row
        org[k] = [v + 1 for v in row]
    return res, org


def _list_of_dicts(n, n_fields, seed):
    rng = random.Random(seed)
    res = []
    org = []
    for _ in range(n):
        d = {}
        e = {}
        for j in range(n_fields):
            k = "f%d" % j
            v = rng.randrange(10**9)
            d[k] = v
            e[k] = v + 1
        res.append(d)
        org.append(e)
    return res, org


def _nested_dicts(depth, breadth, seed):
    rng = random.Random(seed)
    def build(d):
        if d == 0:
            v = rng.randrange(10**9)
            return v, v + 1
        res = {}
        org = {}
        for i in range(breadth):
            k = "n%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org
    return build(depth)
```

Hmm, nested_dicts with depth 4, breadth 8 → 8^4 = 4096 leaves. Too few. depth 4, breadth 12 → 20736. depth 5, breadth 8 → 32768. Let me do depth 5, breadth 8 → 32768 leaves, each level has dicts. Total nodes ≈ 32768 * (1 + 1/8 + ...) ≈ 37k. Values ~74k. Fine.

But the equality comparison: at top, compares whole tree O(n). Then recurse. Total O(n*depth) = 32768*5 = 164k. Fine.

Hmm, but the recursion in the function: for a dict, `for key in orig_thing: get_resolved_jbors(resolved_thing[key], orig_thing[key], ...)`. So it recurses into each key. Good.

Mixed tree:
```python
def _tree(depth, breadth, seed):
    rng = random.Random(seed)
    def build(d):
        if d == 0:
            v = rng.randrange(10**9)
            return v, v + 1
        n = rng.randrange(1, breadth + 1)
        if rng.random() < 0.5:
            res = []
            org = []
            for _ in range(n):
                r, o = build(d - 1)
                res.append(r)
                org.append(o)
            return res, org
        else:
            res = {}
            org = {}
            for i in range(n):
                r, o = build(d - 1)
                k = "k%d" % i
                res[k] = r
                org[k] = o
            return res, org
    return build(depth)
```

With depth 7, breadth 4, expected leaves ~ (avg 2.5)^7 ≈ 610... hmm random. Let me use breadth 5, depth 7 → up to 5^7=78125, avg 3^7=2187. Hmm random branching makes it variable. Let me just use fixed breadth for predictability, or seed it.

Actually, let me make the tree deterministic in size by using fixed branching but random type (list vs dict). Let me do:

```python
def _tree(depth, breadth, seed):
    rng = random.Random(seed)
    def build(d):
        if d == 0:
            v = rng.randrange(10**9)
            return v, v + 1
        if rng.random() < 0.5:
            res = []; org = []
            for _ in range(breadth):
                r, o = build(d-1)
                res.append(r); org.append(o)
            return res, org
        else:
            res = {}; org = {}
            for i in range(breadth):
                r, o = build(d-1)
                k = "k%d" % i
                res[k] = r; org[k] = o
            return res, org
    return build(depth)
```

breadth 5, depth 7 → 5^7 = 78125 leaves. Values ~156k. Fine.

Hmm, but the equality comparison for a tree of depth 7: O(n*depth) = 78125*7 ≈ 550k. Fine.

Now JBOR builders:

```python
def _jbor(job, field, index=None):
    if index is None:
        return {"job": job, "field": field}
    return {"$dnanexus_link": {"job": job, "field": field, "index": index}}
```

And jbor_str:
```python
def _jbor_str(job, field, index=None):
    s = job + ":" + field
    if index is not None:
        s += "." + str(index)
    return s
```

For a flat list of JBORs:
```python
def _flat_jbors(n, seed):
    rng = random.Random(seed)
    res = []
    org = []
    resolved = {}
    for i in range(n):
        job = "job-%d" % i
        field = "out"
        org.append({"job": job, "field": field})
        res.append(rng.randrange(10**9))
        resolved[job + ":" + field] = None
    return res, org, resolved
```

Wait, but resolved_thing[i] is accessed for each i. If orig[i] is a JBOR, is_job_ref True, so it doesn't access resolved_thing[i]. Good. So res[i] value doesn't matter much (but it's used at the top equality check). Actually the top check `resolved_thing == orig_thing` compares the whole lists. If they differ, recurse. res[i] is an int, org[i] is a dict → differ. Good.

Hmm, but actually, when orig[i] is a JBOR, the function doesn't look at resolved_thing[i] at all. So res[i] can be anything. But for the equality check to be False (so it recurses), res[i] should differ from org[i]. An int vs dict → differ. Good.

Now, pre-populating resolved with jbor_str → None. Then `if jbor_str not in resolved_jbors` is False → skip API. 

But wait — the function is called with resolved_jbors = the pre-populated dict. If ALL jbor_strs are in it, no API calls. Good.

Now for nested JBORs:
```python
def _nested_jbors(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    resolved = {}
    for i in range(n_outer):
        k = "key%d" % i
        rl = []
        ol = []
        for j in range(n_inner):
            job = "job-%d-%d" % (i, j)
            field = "field%d" % (j % 5)
            ol.append({"job": job, "field": field})
            rl.append(rng.randrange(10**9))
            resolved[job + ":" + field] = None
        res[k] = rl
        org[k] = ol
    return res, org, resolved
```

Hmm, but if field repeats within a job... jbor_str = job + ':' + field, jobs are unique, so jbor_strs unique. Good.

Wait, but the function recurses into the dict `org` (which has no '$dnanexus_link'). For each key, it recurses into the list. For each list element (JBOR), is_job_ref True, jbor_str, lookup. Good.

But note: the dict `org` itself — is_job_ref? len(org) = n_outer, not 1 or 2 (unless n_outer is 1 or 2). If n_outer is 1 or 2, hmm. Let me use n_outer large. Actually if n_outer==2 and both values are lists (not str), then is_job_ref checks len==2 and .get('field') is str → None is not str → False. And len==1 branch needs '$dnanexus_link'. So False. Good, safe.

Actually careful: if n_outer==2, `len(thing)==2` is True, then checks `isinstance(thing.get('field'), basestring)`. thing.get('field') → None (no 'field' key) → False. So the whole `and` is False. Then second branch: len==1? No. So is_job_ref False. Good.

OK. Now let me also think about the resolved_thing for nested JBORs: res[k] is a list of ints. org[k] is a list of JBORs. Top equality: res != org. Recurse into each key: res[k] (list) vs org[k] (list). Differ. Recurse into elements: res[k][j] (int) vs org[k][j] (JBOR dict). is_job_ref(org[k][j]) True. Good.

Now let me pick sizes.

Case 1: flat-ints, n=250k. Values = 500k. 
Case 2: list-of-lists, 2000 x 120 = 240k leaves. Values ~480k.
Case 3: dict-of-lists, 400 x 400 = 160k. Values ~320k.
Case 4: list-of-dicts, 5000 x 10 = 50k dicts... values: each dict has 10 entries, so 50k*10 = 500k per side, 1M total. Hmm, too much. Let me do 3000 x 10 = 30k dicts, 300k values per side, 600k total. OK.
Case 5: nested-dicts, depth 5, breadth 8 = 32768 leaves. Values ~65k per side. Hmm small. Let me do depth 5, breadth 10 = 100k leaves. Values 200k per side... wait 100k leaves * 2 = 200k total. OK. Actually depth 5 breadth 10 → 10^5 = 100k leaves. Internal nodes: 10^0+...+10^4 = 11111. So ~111k nodes per side, 222k total. Fine.
Case 6: tree, depth 7, breadth 5 = 78125 leaves. ~156k total values.
Case 7: flat-jbors, n=15000. Values: 15000 JBOR dicts (each 2 entries) = 30000 values per side + resolved dict 15000. Total ~75k. Hmm small. Let me do n=30000 → 60k values per side, 120k total + resolved 30k. Fine.
Case 8: nested-jbors, 100 x 200 = 20000 JBORs. Plus lists. Fine.

Hmm, these might be too small to reach 1ms? Let's estimate. 250k ints traversal: each iteration ~0.1-0.2µs → 25-50ms. Good.

Actually, let me reconsider case 1: flat list of 250k ints. Top equality: `[250k ints] == [250k ints]` → compares element-wise, ~250k comparisons, maybe 5-10ms. Then loop: for i in range(250k): call get_resolved_jbors(res[i], org[i], resolved_jbors). Each call: equality (int==int, differs → False), is_job_ref (isinstance dict → False, short-circuit), isinstance list → False, isinstance dict → False. Returns. So ~250k function calls, each cheap but function call overhead ~0.1µs... actually Python function call ~0.1-0.5µs. 250k * 0.3µs = 75ms. Plus the equality. So ~80ms. Good, within range.

Hmm, that's good. Let me keep n=200k to be safe (~60ms).

Actually the range is 1ms-200ms, and we want "the 4 that do the most work" to be kept. So bigger is better up to 200ms. Let me aim ~50-150ms.

Let me now also double-check the "checks()" inputs.

checks():
- ("equal", lambda: ({"a": 1}, {"a": 1}, {}))  → returns immediately.
- ("empty", lambda: ([], [], {})) → equal, returns.
- ("top-jbor", lambda: (5, {"job": "j", "field": "f"}, {})) → is_job_ref True, tries API! Bad.

Hmm, for checks, the function is only checked for identical behavior, not measured. But it still runs. If it tries network, it might be slow. But checks aren't timed... but they still need to complete. Let me avoid JBOR in checks, or pre-populate.

Actually checks "may raise". But better to not hang. Let me use:
- ("equal-nested", lambda: ({"a": [1,2]}, {"a": [1,2]}, {}))
- ("empty-list", lambda: ([], [], {}))
- ("one-elem", lambda: ([1], [2], {}))  → recurses into element: 1 vs 2, not jbor, not list, not dict. Returns.

These are safe. Good.

Hmm, but a JBOR check would be nice for edge cases. Let me do one with pre-populated resolved:
- ("jbor-known", lambda: (0, {"job": "j1", "field": "f1"}, {"j1:f1": None})) → skips API. Safe.

Let me include that.

Now, let me reconsider: is pre-populating resolved_jbors acceptable per the rules? "Setting data (a module's configuration, an object's fields) to build an input is fine." The third argument is just data. We're setting it. Fine.

But hmm, "Prepare the way the repository's own callers do". The caller passes {}. We pass a non-empty dict. Is that "faking"? I don't think so — it's a valid input to the function. The function explicitly handles non-empty resolved_jbors.

However, I'm slightly worried the grader might consider it odd. But the alternative (network) fails. Let me go with it.

Actually, wait. Let me reconsider. Maybe I should just NOT include JBORs at all in the measured cases, to be 100% safe. The function's main work in the repo involves JBORs, but the traversal work is also real.

Hmm, but then all 8 cases are pure traversal. Is that "diverse"? Yes — different structures (flat, nested, dicts, lists, mixed). Different sizes.

But the JBOR branch is never exercised. The task says "different paths through its code". Hmm.

Let me include JBORs with pre-population — it's safe (no network) and exercises the branch. I'll do 2-3 cases with JBORs.

Actually, let me do more: 4 with JBORs (pre-populated) and 4 pure. That gives diversity.

Hmm, but wait — with pre-population, the JBOR branch does: is_job_ref, jbor_to_str, dict lookup. That's the branch. Good.

Let me finalize.

Actually, one more consideration: the `resolved_jbors` dict is shared across calls (module-level). Since the function doesn't mutate it (all keys present), fine. But what if the grader runs the function and it DOES mutate? Let me double check: for each JBOR, `if jbor_str not in resolved_jbors:` — all present → skip. No mutation. 

But what about non-JBOR branches? They recurse, no mutation of resolved_jbors. Good.

OK, but to be extra safe, let me have the thunk return `dict(RESOLVED)` (a copy). Then even if mutated, each call starts fresh. The copy cost is in the thunk (untimed). For a 30k-key dict, copy ~1ms. Fine.

Hmm, but actually if I return a copy, and the function mutates it, the mutation is discarded each call — so every call takes the same path. Good. Let me do that.

Wait, but if I return a copy and the function adds keys, that's fine. But the copy is made each thunk call. For 30k keys, ~1-2ms per thunk call. Since thunks run before timing, and there are many repetitions... hmm, actually the thunk runs once per call (to build args). If there are 1000 repetitions, that's 1000 copies. But that's untimed overhead. Should be OK, but let me minimize by returning the same object (safe since no mutation).

Hmm, the instructions say thunks run before timing starts? "Thunks run before the timing starts; only the call of the function is timed." And "every call gets the arguments of its own thunk call". So the thunk is called for each repetition, but only the function call is timed. So thunk cost isn't timed but does add wall time. For a 30k-key copy at 1ms, times maybe 100 reps = 100ms. Negligible.

Actually, let me just return the same dict object (no copy) since it's not mutated. Simpler and faster.

Hmm, but risk: if somehow mutated, subsequent calls differ. Let me return a copy to be safe. Actually, let me think — the function definitely doesn't mutate when all keys present. I'm confident. But copying is cheap insurance. Let me return a copy.

Hmm, wait, actually there's a subtle issue: if I return a copy each time, and the function doesn't mutate, then all calls are identical. Good. If I return the same object and it's not mutated, also identical. Both fine. Copy is safer. Let me copy.

Actually, copying a dict of 30k keys each thunk call... let me just use the same object. I'll verify no mutation by reasoning. OK, same object.

Hmm, let me reconsider — actually, you know what, let me just make the resolved_jbors small by having few JBORs? No, I want many JBORs for work.

Ugh, let me just do the copy. It's fine.

Hmm, actually, wait. Let me reconsider the whole thing. Let me re-read the feedback: "Only 0 of the 8 measured inputs can be used". So all failed. The reason: "took over 20s".

Given my analysis, the JBOR API calls are the culprit. Pre-populating avoids them.

Let me now write the final code.

One more thing: `from dxpy.utils.describe import get_resolved_jbors` — importing this module imports dxpy and the printing module etc. Should be fine.

Let me write it.

```python
import random

from dxpy.utils.describe import get_resolved_jbors


# ---------------------------------------------------------------------------
# Builders: identical shapes, differing leaves, so the function recurses.
# ---------------------------------------------------------------------------

def _flat_ints(n, seed):
    rng = random.Random(seed)
    res = [rng.randrange(10 ** 9) for _ in range(n)]
    org = [v + 1 for v in res]
    return res, org


def _list_of_lists(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = [[rng.randrange(10 ** 9) for _ in range(n_inner)] for _ in range(n_outer)]
    org = [[v + 1 for v in row] for row in res]
    return res, org


def _dict_of_lists(n_keys, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    for i in range(n_keys):
        k = "k%d" % i
        row = [rng.randrange(10 ** 9) for _ in range(n_inner)]
        res[k] = row
        org[k] = [v + 1 for v in row]
    return res, org


def _list_of_dicts(n, n_fields, seed):
    rng = random.Random(seed)
    res = []
    org = []
    for _ in range(n):
        d = {}
        e = {}
        for j in range(n_fields):
            k = "f%d" % j
            v = rng.randrange(10 ** 9)
            d[k] = v
            e[k] = v + 1
        res.append(d)
        org.append(e)
    return res, org


def _nested_dicts(depth, breadth, seed):
    rng = random.Random(seed)

    def build(d):
        if d == 0:
            v = rng.randrange(10 ** 9)
            return v, v + 1
        res = {}
        org = {}
        for i in range(breadth):
            k = "n%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org

    return build(depth)


def _tree(depth, breadth, seed):
    rng = random.Random(seed)

    def build(d):
        if d == 0:
            v = rng.randrange(10 ** 9)
            return v, v + 1
        if rng.random() < 0.5:
            res = []
            org = []
            for _ in range(breadth):
                r, o = build(d - 1)
                res.append(r)
                org.append(o)
            return res, org
        res = {}
        org = {}
        for i in range(breadth):
            k = "k%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org

    return build(depth)


# ---------------------------------------------------------------------------
# JBOR builders.  Every JBOR string is pre-registered in resolved_jbors so the
# function never reaches the network call; it still walks the JBOR branch.
# ---------------------------------------------------------------------------

def _flat_jbors(n, seed):
    rng = random.Random(seed)
    res = []
    org = []
    resolved = {}
    for i in range(n):
        job = "job-%d" % i
        field = "out"
        s = job + ":" + field
        resolved[s] = None
        org.append({"job": job, "field": field})
        res.append(rng.randrange(10 ** 9))
    return res, org, resolved


def _nested_jbors(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    resolved = {}
    for i in range(n_outer):
        k = "key%d" % i
        rl = []
        ol = []
        for j in range(n_inner):
            job = "job-%d-%d" % (i, j)
            field = "field%d" % (j % 7)
            s = job + ":" + field
            resolved[s] = None
            ol.append({"job": job, "field": field})
            rl.append(rng.randrange(10 ** 9))
        res[k] = rl
        org[k] = ol
    return res, org, resolved
```

Hmm wait, for _nested_jbors, if n_outer is 2 and... no, n_outer will be large. Fine.

But careful: the dict `org` has n_outer keys. If n_outer==2, is_job_ref checks len==2 and .get('field') — 'field' not a key → None → not str → False. Safe.

Now module-level:

```python
_C1 = _flat_ints(200_000, 0)
_C2 = _list_of_lists(2000, 120, 1)
_C3 = _dict_of_lists(400, 400, 2)
_C4 = _list_of_dicts(3000, 10, 3)
_C5 = _nested_dicts(5, 10, 4)
_C6 = _tree(7, 5, 5)
_C7 = _flat_jbors(30_000, 6)
_C8 = _nested_jbors(100, 200, 7)
```

Wait, _nested_dicts(5, 10) → 10^5 = 100k leaves. Each leaf is an int pair. Plus internal dicts. Total nodes per side ≈ 111k. Values ~222k. OK.

_tree(7, 5) → 5^7 = 78125 leaves. OK.

_C4: 3000 dicts x 10 fields = 30k dicts, 300k values per side, 600k total. OK.

_C7: 30k JBORs → 30k dicts x 2 = 60k values per side, 120k total + resolved 30k keys. OK.

_C8: 100 x 200 = 20k JBORs. OK.

Now cases:

```python
def cases():
    return [
        ("flat-ints", lambda: (_C1[0], _C1[1], {})),
        ("list-of-lists", lambda: (_C2[0], _C2[1], {})),
        ("dict-of-lists", lambda: (_C3[0], _C3[1], {})),
        ("list-of-dicts", lambda: (_C4[0], _C4[1], {})),
        ("nested-dicts", lambda: (_C5[0], _C5[1], {})),
        ("mixed-tree", lambda: (_C6[0], _C6[1], {})),
        ("flat-jbors", lambda: (_C7[0], _C7[1], dict(_C7[2]))),
        ("nested-jbors", lambda: (_C8[0], _C8[1], dict(_C8[2]))),
    ]
```

Hmm, for flat-ints etc., resolved_jbors is {} each time. The function doesn't mutate it (no JBORs). Actually it could mutate if there were JBORs, but there aren't. So {} is fine. But returning the same {} object each call... it's a fresh {} literal each thunk call. Fine.

For JBOR cases, I return dict(_C7[2]) — a copy. Since the function doesn't mutate (all keys present), the copy is unnecessary but safe. Actually, copying a 30k-key dict each thunk call adds ~1ms untimed. Fine.

Hmm, actually, let me reconsider: does the function mutate resolved_jbors when all keys present? No. So I could return _C7[2] directly. But copy is safe. Let me keep the copy.

Wait, actually there's a subtlety with copying: if the function DID add a key (it won't), the copy would prevent accumulation. Good.

Now, let me reconsider sizes for timing. Let me estimate each:

_C1: 200k ints flat. Top equality ~200k comparisons. Then 200k recursive calls. ~50-80ms.

_C2: 2000 lists x 120 ints. Top equality: compares 2000 sublists (each 120) → 240k comparisons. Then recurse into 2000 sublists: each does equality (120) + recurse into 120 elements. So 2000*(120 + 120) = 480k. ~80-120ms.

Hmm, might be over 200ms? Let me reduce. 2000 x 100 = 200k. Let me use 1500 x 100 = 150k.

Actually, let me just be moderate and test conceptually. I'll use:
- _C2 = _list_of_lists(1500, 100, 1) → 150k leaves.

_C3: 400 keys x 400 ints = 160k. Top equality compares 400 lists of 400 → 160k. Recurse: 400 sublists, each equality 400 + recurse 400 elements. ~320k. Hmm. Let me use 300 x 300 = 90k.

Actually, these are all fine-ish. Let me just pick reasonable numbers and not overthink. The grader keeps the 4 with most work, so even if some are 20ms and others 100ms, fine.

Let me finalize with moderate sizes:

_C1 = _flat_ints(200_000, 0)
_C2 = _list_of_lists(1500, 100, 1)
_C3 = _dict_of_lists(300, 300, 2)
_C4 = _list_of_dicts(3000, 10, 3)
_C5 = _nested_dicts(5, 10, 4)
_C6 = _tree(7, 5, 5)
_C7 = _flat_jbors(30_000, 6)
_C8 = _nested_jbors(100, 200, 7)

Hmm, _C5 with depth 5, breadth 10: 100k leaves. The equality at top is O(n) = 111k comparisons. Then recursion: each internal dict compared... total O(n*depth) = 555k. ~100ms. OK.

Hmm, but wait — is the equality comparison at each level really happening? Let me re-read:

```python
def get_resolved_jbors(resolved_thing, orig_thing, resolved_jbors):
    if resolved_thing == orig_thing:
        return
    if is_job_ref(orig_thing):
        ...
    elif isinstance(orig_thing, list):
        for i in range(len(orig_thing)):
            get_resolved_jbors(resolved_thing[i], orig_thing[i], resolved_jbors)
    elif isinstance(orig_thing, dict) and '$dnanexus_link' not in orig_thing:
        for key in orig_thing:
            get_resolved_jbors(resolved_thing[key], orig_thing[key], resolved_jbors)
```

Yes, at each recursion, `resolved_thing == orig_thing` is evaluated. For a dict, comparing two dicts compares keys and values recursively. So O(subtree). Total O(n*depth). Yes.

OK.

Now, one concern: for _C5 (nested dicts), the top-level is a dict with breadth=10 keys. is_job_ref? len==10, not 1 or 2 → False. Then isinstance dict and '$dnanexus_link' not in it → True. Recurse. Good.

But wait — at depth 1, the dicts have breadth=10 keys too. Fine. At the leaf level (depth 0), values are ints. Good.

Hmm, but actually — for _C5, the structure is: dict{n0: dict{n0: ...}}, depth 5. So 5 levels of dicts, then ints. Good.

Now, there's a potential issue: the function checks `'$dnanexus_link' not in orig_thing` for dicts. Our dicts don't have that key. Good.

Let me also double check _C4 (list of dicts): each dict has 10 keys "f0".."f9". len==10 → is_job_ref False. isinstance dict, no '$dnanexus_link' → recurse. Good.

OK.

Now checks():

```python
def checks():
    return [
        ("equal-nested", lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {})),
        ("empty-list", lambda: ([], [], {})),
        ("top-jbor-known", lambda: (0, {"job": "j1", "field": "f1"}, {"j1:f1": None})),
    ]
```

top-jbor-known: orig is a JBOR, resolved_jbors has the key → skips API. Good.

Hmm, but actually `resolved_thing` is 0 (int), `orig_thing` is the JBOR dict. 0 == dict → False. is_job_ref(dict) → len==2, 'field' str, 'job' str → True. jbor_str = "j1:f1". In resolved_jbors → skip. Returns. Good.

Now let me reconsider whether pre-populating is truly safe. The function does `from dxpy.api import job_describe` inside the try. But only if jbor_str not in resolved_jbors. Since it is, we never import/execute. Good.

Let me also make sure the import of describe module works. `from dxpy.utils.describe import get_resolved_jbors`. This module imports `dxpy`, `.printing`, `.pretty_print`, `..compat`. Should be importable.

Alright, let me also reconsider: the task says "keep each input's data under about 1,000,000 values". Let me count:

_C1: 200k ints * 2 = 400k. OK.
_C2: 150k leaves * 2 = 300k, plus 1500 sublists * 2 = 3k. OK.
_C3: 90k * 2 = 180k. OK.
_C4: 30k dicts * 10 = 300k per side, 600k total. OK.
_C5: ~111k nodes * 2 = 222k. OK.
_C6: ~78k leaves + internal ~20k = ~98k per side, ~196k total. OK.
_C7: 30k JBOR dicts * 2 entries = 60k per side, 120k total + resolved 30k. OK.
_C8: 20k JBORs * 2 = 40k per side, 80k + lists. OK.

All under 1M. Good.

Building time: all fast (< 1s). Good.

Now let me reconsider the timing risk for _C7 and _C8: no network (pre-populated). Work: 30k JBORs, each is_job_ref + jbor_to_str + dict lookup. Plus top equality comparing 30k dicts. ~30-50ms. Good.

Hmm, but actually — wait. For _C7, the top equality `resolved_thing == orig_thing`: res is a list of 30k ints, org is a list of 30k dicts. Comparing: element-wise, int vs dict → not equal, but Python still checks each pair? Actually list comparison: compares element by element, stops at first difference. So it stops at index 0 (int vs dict differ). Fast!

Oh interesting. So the top equality is fast when the first element differs. Hmm.

Wait, for _C1 (flat ints), res[0] = v, org[0] = v+1. They differ at index 0. So top equality stops immediately! Then recursion: for each i, get_resolved_jbors(res[i], org[i], ...). Each call: res[i] == org[i]? v vs v+1 → False, fast. So no expensive subtree comparison.

Hmm! So my analysis of O(n*depth) is wrong — the equality checks short-circuit at the first difference.

So for flat structures where leaves differ, equality is O(1) per call. Total work = O(n) calls, each cheap. So ~200k calls, ~50ms. Still fine.

For nested structures: at the top, res vs org differ at first element. Then recurse into element 0: differ at its first element. Etc. So each equality is O(1). Total O(n).

Hmm OK. So the work is just O(n) function calls. For 200k nodes, ~50-100ms. Fine.

But wait, for _C5 nested dicts: top dict comparison. Python dict comparison: compares keys, then values. For each key, compares values. If the first key's value differs, does it stop? Actually dict `==` compares all keys and values, but short-circuits on first mismatch? Let me think. CPython's dict comparison iterates and returns False on first mismatch. So yes, short-circuits.

So for nested dicts, at each level, comparing the first key's value: if it's a dict, recurse into comparison... Actually the comparison is done by CPython's C code, which recursively compares. It short-circuits.

Hmm, so `resolved_thing == orig_thing` at the top: for nested dicts, it compares n0's value (a dict), which compares n0's value (a dict), ... down to a leaf where they differ. So O(depth) for the comparison. Then the function recurses into key n0 (since dict iteration order), and does the same. So O(depth) per internal node. Total O(n*depth)? Hmm, no.

Wait. Let me think again. Top-level: `res == org` → compares dicts. CPython compares: for key n0, compare res[n0] (dict) vs org[n0] (dict) → recurse. ... down to leaf, differs → returns False. So the top comparison is O(depth). Then the function iterates over keys: for key n0, recurse get_resolved_jbors(res[n0], org[n0], ...). That call: `res[n0] == org[n0]` → O(depth-1). Then iterate keys... 

So total: at level L (0-indexed from top), there are breadth^L nodes, each doing a comparison of O(depth-L). Total = sum_L breadth^L * (depth-L). Dominated by deepest level: breadth^(depth-1) * 1. Actually the number of nodes at level L is breadth^L, and each comparison is O(depth-L). Sum = sum_{L=0}^{depth} breadth^L * (depth-L).

For breadth=10, depth=5: L=0: 1*5, L=1: 10*4=40, L=2: 100*3=300, L=3: 1000*2=2000, L=4: 10000*1=10000, L=5: 100000*0=0 (leaves, comparison is O(1) int compare). Hmm, at L=5 (leaves), comparison is int vs int, O(1). So total ~12345 comparisons plus 100k leaf calls. So ~100k+ calls. Fine, ~50ms.

Hmm, actually wait, I need to recount. The function is called on each node. Number of nodes = sum breadth^L for L=0..depth = (10^6-1)/9 ≈ 111k. Each call does a comparison. The comparison cost varies. Total comparison work ≈ 12345 (as computed) + 100k leaf comparisons. So ~112k comparisons + 111k function calls. ~50-80ms. OK.

Fine.

Now, the concern: is 50-80ms enough? Range is 1-200ms. Yes.

But the grader keeps the 4 with most work. If some are 5ms and some 80ms, fine.

Let me make sure none exceeds 200ms. _C2: 1500 lists x 100 ints = 150k leaves + 1500 sublists = 151.5k nodes. Each call: comparison (O(1) for leaves, O(100) for sublists... wait). Top: res vs org, first element is a list of 100. Compare lists: first element differs → O(1). So top comparison O(1). Then recurse into 1500 sublists: each `res[i] == org[i]` → compares lists, first element differs → O(1). Then recurse into 100 elements each. So total ~151.5k calls, each cheap. ~50ms. Good.

Hmm, all my structures short-circuit. So work is ~O(nodes). Good, predictable.

Let me bump sizes a bit to get more work, staying under 200ms. Let me target ~150k-300k nodes.

Actually, let me reconsider: 200k function calls in Python ≈ 200k * 0.3µs = 60ms. Plus overhead. So 200k nodes ≈ 60-100ms. Good.

Let me set:
_C1 = _flat_ints(250_000, 0) → 250k nodes.
_C2 = _list_of_lists(2000, 100, 1) → 202k nodes.
_C3 = _dict_of_lists(300, 300, 2) → 90k + 300 = 90.3k nodes. Hmm, maybe bump to 400x400=160k.
_C4 = _list_of_dicts(4000, 10, 3) → 4000 dicts + 40k values = 44k nodes. Hmm, the values are leaves (ints). So 44k nodes. Small. Let me bump to 8000x10 = 88k.
_C5 = _nested_dicts(5, 10, 4) → 111k nodes.
_C6 = _tree(7, 5, 5) → ~97k nodes.
_C7 = _flat_jbors(40_000, 6) → 40k nodes.
_C8 = _nested_jbors(100, 300, 7) → 30k JBORs + lists/dicts → ~30k nodes.

Hmm, these are all roughly 40k-250k nodes. Good.

Let me double check value counts:
_C4 = 8000 dicts x 10 = 80k values per side, 160k total. OK.
_C7 = 40k JBOR dicts x 2 = 80k values per side, 160k + resolved 40k. OK.
_C8 = 30k JBORs x 2 = 60k per side + lists. OK.

All good.

Hmm, actually let me reconsider _C4: 8000 dicts, each with 10 keys. Total nodes = 8000 + 80000 = 88k. Each dict call: comparison O(1) (first key differs), then recurse into 10 keys. Each key: int comparison O(1). So ~88k calls. Fine.

OK let me also reconsider: for _C4, the top-level is a list of 8000 dicts. Top comparison: res[0] is a dict, org[0] is a dict. Compare dicts: first key "f0", res value int vs org value int, differ → O(1). So top comparison O(1). Then recurse into 8000 dicts. Each: `res[i] == org[i]` → dict comparison, first key differs → O(1). Then is_job_ref(dict) → len==10, not 1 or 2 → False. isinstance dict, no '$dnanexus_link' → recurse into 10 keys. Each key: int comparison. So total ~88k calls. Good.

Alright. Let me also reconsider whether the JBOR branch with pre-population is truly exercised. For _C7: orig[i] is a JBOR dict. is_job_ref → len==2, 'field' str, 'job' str → True. jbor_str = job + ':' + field. Check in resolved_jbors → present → skip. So yes, is_job_ref and jbor_to_str are exercised. Good.

Now, let me write the final code cleanly.

One more thought: should I worry that the grader might time the thunk too? No — "only the call of the function is timed".

Also, "anything the function changes outside its arguments carries over". The function doesn't change globals. Good.

Let me also double-check: the function might be called with the same resolved_jbors dict across iterations for _C7. Since no mutation, fine.

Let me write it.

Actually, hold on. Let me reconsider the risk that even with pre-population, something goes wrong. What if `is_job_ref` returns True but `jbor_to_str` produces a string NOT in resolved_jbors due to some subtlety? Let me verify:

`jbor_to_str(val)`: `ans = get_job_from_jbor(val) + ':' + get_field_from_jbor(val)`. For {"job": job, "field": field}: get_job_from_jbor → '$dnanexus_link' in thing? No → return thing['job'] = job. get_field_from_jbor → thing['field'] = field. So ans = job + ':' + field. Then index: get_index_from_jbor → '$dnanexus_link' in thing? No → None. So ans = job + ':' + field. Matches what I pre-populated. 

For wrapped JBORs I'm not using any in the measured cases. Fine.

OK, writing final.

Actually, let me reconsider using wrapped JBORs too for diversity. Let me make _C8 use wrapped JBORs.

Wrapped: {"$dnanexus_link": {"job": job, "field": field}}. is_job_ref: len==1, '$dnanexus_link' is dict, .get('field') str, .get('job') str → True. jbor_str = job + ':' + field (index None). Good.

Let me use wrapped in _C8 for diversity. Actually, let me mix: half plain, half wrapped.

Hmm, but then resolved keys are the same format. Fine.

Let me write _nested_jbors to mix.

Actually, simpler: keep _C8 with wrapped JBORs.

```python
def _nested_jbors(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    resolved = {}
    for i in range(n_outer):
        k = "key%d" % i
        rl = []
        ol = []
        for j in range(n_inner):
            job = "job-%d-%d" % (i, j)
            field = "field%d" % (j % 7)
            s = job + ":" + field
            resolved[s] = None
            if j % 2 == 0:
                ol.append({"job": job, "field": field})
            else:
                ol.append({"$dnanexus_link": {"job": job, "field": field}})
            rl.append(rng.randrange(10 ** 9))
        res[k] = rl
        org[k] = ol
    return res, org, resolved
```

Good, mixes plain and wrapped.

Now, one concern: for the wrapped JBOR, `is_job_ref` requires len==1. Our dict has exactly 1 key. Good.

Alright, final code.

Let me also add a case with indexed JBORs? Indexed requires the field value to be a list and index into it. But since we pre-populate, the index only affects jbor_str. Let me add index to some wrapped JBORs in _C8.

jbor_str for indexed: job + ':' + field + '.' + str(index). Let me handle.

```python
if j % 3 == 0:
    idx = j % 5
    ol.append({"$dnanexus_link": {"job": job, "field": field, "index": idx}})
    resolved[job + ":" + field + "." + str(idx)] = None
```

Hmm, getting complex. Let me keep it simple with plain and wrapped only. Diversity comes from structure.

Actually, let me add a third JBOR case with indexed... no, 8 cases total. Let me keep 8:

1. flat-ints
2. list-of-lists
3. dict-of-lists
4. list-of-dicts
5. nested-dicts
6. mixed-tree
7. flat-jbors (plain)
8. nested-jbors (mixed plain/wrapped)

Good.

Hmm, let me reconsider case 5 (nested-dicts) — it's all dicts, no lists. Case 6 (mixed-tree) has both. Case 2/3 have lists. Good diversity.

Let me finalize.

Actually, let me reconsider the sizes once more for safety on the upper bound (200ms). Let me be a bit conservative:

_C1 = _flat_ints(200_000, 0)
_C2 = _list_of_lists(1500, 100, 1)
_C3 = _dict_of_lists(300, 300, 2)
_C4 = _list_of_dicts(5000, 10, 3)
_C5 = _nested_dicts(5, 10, 4)
_C6 = _tree(7, 5, 5)
_C7 = _flat_jbors(30_000, 6)
_C8 = _nested_jbors(100, 200, 7)

These should each be 20-100ms. Good.

Let me write the final answer.

Wait, one more check on `_tree(7, 5, 5)`: with random list/dict choice at each internal node, the number of leaves is exactly 5^7 = 78125 (since breadth is fixed at 5 and depth fixed at 7). Good, deterministic.

And `_nested_dicts(5, 10, 4)`: 10^5 = 100000 leaves. Good.

OK. Also need to make sure building these doesn't take >10s. 100k nodes building is fast (<0.5s each). Total <3s. Good.

Final code:

```python
import random

from dxpy.utils.describe import get_resolved_jbors


def _flat_ints(n, seed):
    rng = random.Random(seed)
    res = [rng.randrange(10 ** 9) for _ in range(n)]
    org = [v + 1 for v in res]
    return res, org


def _list_of_lists(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = [[rng.randrange(10 ** 9) for _ in range(n_inner)] for _ in range(n_outer)]
    org = [[v + 1 for v in row] for row in res]
    return res, org


def _dict_of_lists(n_keys, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    for i in range(n_keys):
        k = "k%d" % i
        row = [rng.randrange(10 ** 9) for _ in range(n_inner)]
        res[k] = row
        org[k] = [v + 1 for v in row]
    return res, org


def _list_of_dicts(n, n_fields, seed):
    rng = random.Random(seed)
    res = []
    org = []
    for _ in range(n):
        d = {}
        e = {}
        for j in range(n_fields):
            k = "f%d" % j
            v = rng.randrange(10 ** 9)
            d[k] = v
            e[k] = v + 1
        res.append(d)
        org.append(e)
    return res, org


def _nested_dicts(depth, breadth, seed):
    rng = random.Random(seed)

    def build(d):
        if d == 0:
            v = rng.randrange(10 ** 9)
            return v, v + 1
        res = {}
        org = {}
        for i in range(breadth):
            k = "n%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org

    return build(depth)


def _tree(depth, breadth, seed):
    rng = random.Random(seed)

    def build(d):
        if d == 0:
            v = rng.randrange(10 ** 9)
            return v, v + 1
        if rng.random() < 0.5:
            res = []
            org = []
            for _ in range(breadth):
                r, o = build(d - 1)
                res.append(r)
                org.append(o)
            return res, org
        res = {}
        org = {}
        for i in range(breadth):
            k = "k%d" % i
            r, o = build(d - 1)
            res[k] = r
            org[k] = o
        return res, org

    return build(depth)


def _flat_jbors(n, seed):
    rng = random.Random(seed)
    res = []
    org = []
    resolved = {}
    for i in range(n):
        job = "job-%d" % i
        field = "out"
        resolved[job + ":" + field] = None
        org.append({"job": job, "field": field})
        res.append(rng.randrange(10 ** 9))
    return res, org, resolved


def _nested_jbors(n_outer, n_inner, seed):
    rng = random.Random(seed)
    res = {}
    org = {}
    resolved = {}
    for i in range(n_outer):
        k = "key%d" % i
        rl = []
        ol = []
        for j in range(n_inner):
            job = "job-%d-%d" % (i, j)
            field = "field%d" % (j % 7)
            resolved[job + ":" + field] = None
            if j % 2 == 0:
                ol.append({"job": job, "field": field})
            else:
                ol.append({"$dnanexus_link": {"job": job, "field": field}})
            rl.append(rng.randrange(10 ** 9))
        res[k] = rl
        org[k] = ol
    return res, org, resolved


_C1 = _flat_ints(200_000, 0)
_C2 = _list_of_lists(1500, 100, 1)
_C3 = _dict_of_lists(300, 300, 2)
_C4 = _list_of_dicts(5000, 10, 3)
_C5 = _nested_dicts(5, 10, 4)
_C6 = _tree(7, 5, 5)
_C7 = _flat_jbors(30_000, 6)
_C8 = _nested_jbors(100, 200, 7)


def checks():
    return [
        ("equal-nested", lambda: ({"a": [1, 2]}, {"a": [1, 2]}, {})),
        ("empty-list", lambda: ([], [], {})),
        ("top-jbor-known", lambda: (0, {"job": "j1", "field": "f1"}, {"j1:f1": None})),
    ]


def cases():
    return [
        ("flat-ints", lambda: (_C1[0], _C1[1], {})),
        ("list-of-lists", lambda: (_C2[0], _C2[1], {})),
        ("dict-of-lists", lambda: (_C3[0], _C3[1], {})),
        ("list-of-dicts", lambda: (_C4[0], _C4[1], {})),
        ("nested-dicts", lambda: (_C5[0], _C5[1], {})),
        ("mixed-tree", lambda: (_C6[0], _C6[1], {})),
        ("flat-jbors", lambda: (_C7[0], _C7[1], dict(_C7[2]))),
        ("nested-jbors", lambda: (_C8[0], _C8[1], dict(_C8[2]))),
    ]
```

Wait, there's an issue with `_C1` etc. being tuples `(res, org)` and I index `_C1[0]`, `_C1[1]`. Good.

Hmm, but for the JBOR cases, `_C7 = (res, org, resolved)`, so `_C7[0]`, `_C7[1]`, `_C7[2]`. Good.

Let me double check `_C5 = _nested_dicts(5, 10, 4)` returns `build(5)` which returns `(res, org)`. Good.

Now, one concern about `_nested_dicts` with breadth=10 and depth=5: building 111k dicts. Fine.

Another concern: recursion depth in the function for _C5 is 5 (dicts) + 1 (leaf). Fine. For _C6 depth 7. Fine.

OK. Let me also reconsider: is there any chance the function raises for these inputs? 

For lists: `resolved_thing[i]` requires resolved_thing to be indexable and same length. Our res and org have identical shapes. Good.

For dicts: `resolved_thing[key]` for each key in orig_thing. Our res and org dicts have identical keys. Good.

For JBORs: is_job_ref True, jbor_str in resolved → skip. Good.

No exceptions.

Alright, I'm fairly confident. Let me also double-check the `checks` case "top-jbor-known": resolved_thing=0, orig_thing={"job": "j1", "field": "f1"}. 0 == dict → False. is_job_ref → True. jbor_str = "j1:f1". In resolved_jbors {"j1:f1": None} → skip. Returns None. No exception. Good.

Final answer.

Hmm, actually, let me reconsider whether I should reduce the risk further by making ALL cases pure-structure. The concern is that pre-population might be seen as not exercising the real path. But it does exercise the JBOR branch (minus network). I think it's fine and gives diversity.

But what if the grader's "work" measurement finds the JBOR cases do less work? Doesn't matter — it keeps the top 4.

OK, final.

Actually, let me reconsider the case where `resolved_jbors` is `{}` for the pure cases. The function might... no, no JBORs, no mutation. Fine.

Let me also make sure I'm not accidentally creating a JBOR-shaped dict in the pure cases. E.g., _C4 dicts have 10 keys → not JBOR. _C5 dicts have 10 keys → not JBOR. _C6 dicts have 5 keys → not JBOR. Good. _C3 dict has 300 keys → not JBOR. Good.

Wait, _C6 uses breadth=5, so dicts have 5 keys. Not 1 or 2 → not JBOR. Good.

_C5 breadth=10 → 10 keys. Good.

_C2 lists of 100 ints. Good.

All clear.

One last thing: the label "flat-jbors" and "nested-jbors" — distinct labels. Good.

Writing final.