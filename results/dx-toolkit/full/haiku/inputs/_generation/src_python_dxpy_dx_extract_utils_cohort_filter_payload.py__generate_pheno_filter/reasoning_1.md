Let me analyze the function.

`generate_pheno_filter(values, entity, field, filters, lambda_for_list_conv)`.

It mutates `filters` and returns it. Since it mutates the input, each thunk call must get a fresh copy of `filters`. Also `values` may be modified? `values = sorted(set(values)...)` reassigns local, doesn't mutate. But `primary_filters.append({"condition": "in", "values": values})` — values is the new local. So values isn't mutated. But filters is mutated, so we need a deep copy per call.

lambda_for_list_conv is a function — we can pass a plain lambda defined at module level. That's fine (not a mock of repository code; it's a parameter). The repository's test uses `lambda a, b: a+[str(b)]`.

Paths through the code:
1. No "pheno_filters" key → create compound, then falls through to the loops (empty compound) → appends new entity filter. Returns.
2. "pheno_filters" exists but no "compound" → wrap into compound.
3. "pheno_filters" compound with logic != "and" → raise ValueError. (checks only, since must run to completion... actually raising is allowed in checks only, cases must not raise.)
4. Existing compound filter with "filters" containing entity_field → process primary_filters, conditions exists/in/not-in.
5. Existing compound filter with entity name matching → add filter.
6. Existing compound filter with filters containing other_entity_field with same entity prefix → add filter.
7. No match → append new.

For cases, we want substantial work. The heavy work is in path 4: `values = sorted(set(values).intersection(set(reduce(lambda_for_list_conv, primary_filter["values"], []))))`. With large values and large primary_filter values lists, this is the heavy computation. Also reduce over a list of lists.

Let's design 8 cases with realistic scale.

The lambda_for_list_conv: `lambda a, b: a+[str(b)]` — builds a list. reduce over primary_filter["values"] which is a list of lists presumably. Each element b is a list, converted to str then appended. Hmm, actually in the test, values are lists? Let me think: reduce(lambda_for_list_conv, primary_filter["values"], []) - starts with [], for each b in primary_filter["values"], appends str(b) to a. So primary_filter["values"] is a list of items (maybe lists of values). The result is a list of strings. Then set(...) intersect with values.

Actually the real usage: values are probably lists of value-lists. Let's just make primary_filter["values"] a list of lists of strings, so str() of each gives a string repr. Hmm, but then intersection with values (strings) may not match well. For "in" condition, we want intersection to produce results. Let's make values a list of strings, and primary_filter["values"] a list of strings too (each element str()'d = itself). Then reduce gives list of those strings. Good — that's realistic: values is a list of strings.

Actually let me look more carefully. In cohort_filter_payload, values come from user input. The test at line 437 — let me guess values = ['patient_1', 'patient_2']. And filters with primary_filter values maybe [['patient_1','patient_2']]? Then reduce(lambda a,b: a+[str(b)], [['patient_1','patient_2']], []) = ["['patient_1', 'patient_2']"]. Hmm that wouldn't intersect.

Hard to know. Let's just design plausible data: primary_filter["values"] is a list of strings, so str(b) == b. That gives meaningful intersection.

For the heavy case, make values large (e.g. 200k? no, under 1M values total and output under 100k). Actually the output is `filters` dict which contains values lists. Keep output under 100k values.

Let's think about scale: one call 1ms-200ms. The heavy op is set intersection and sorting. With values of 100k and primary values 100k, that's fast (~50ms maybe). Sorting 100k strings ~ 50ms.

Let's do:

Case A: path 4 "in" with large values (100k) and large primary_filter values (100k) → intersection.
Case B: path 4 "not-in" with large values → difference.
Case C: path 4 with multiple primary_filters including "exists" (pass, values unchanged).
Case D: path 4 with multiple compound filters where the first doesn't match, second matches.
Case E: path 6 (entity in field prefix, different field) → add.
Case F: path 5 (entity name match) → add.
Case G: path 1 (no pheno_filters) with large values → create new.
Case H: path 2 (no compound) with large values → wrap.

Also path 7 (append new). Hmm, we have 8 cases. Let's pick diverse.

Actually the "work" measure: the original function's work. For paths that just add dicts, work is O(size of filters). The heavy computation is only in path 4.

Let's make several path-4 variants with different sizes and conditions, plus a couple of others.

Now important: the function mutates filters. Each thunk must return a fresh deep copy. Build base filters at module level, and thunk returns copy.deepcopy(base). But deepcopy of large data is setup, not timed — fine, but thunk runs before timing. Actually the thunk runs before each call, and it's not timed. Good. But deepcopy of 100k values per call — that's setup cost, acceptable.

Hmm, but "keep a thunk cheap next to one call". deepcopy of 100k strings ~ few ms. Fine relative to 50ms call.

Alternatively build filters fresh in the thunk using a function. Let's just do a builder function.

Also note: `values` is passed and not mutated, so we can share it. But careful: in path 4, `values = sorted(...)` reassigns local; original values list untouched. Good.

Wait — in the "in"/"not-in" branch, values gets reassigned. In other branches, values is used directly in the filter dict. The filter dict is part of the returned filters. If we share the values list across calls, and the function stores it in the dict, then it's the same list object. But we don't mutate it. However if the same list object is stored in the returned filters, and we do deepcopy of filters but not values... the returned filters contains a reference to our shared values list. Comparison of output is fine. But could the function mutate values later? No.

Actually careful: in path 1/2/5/6/7, `values` list is placed directly. If two calls share the same values list, no problem.

But there's a subtlety: the harness renders arguments before and after each call to see whether they changed. Our filters deepcopy is fresh each call, so it's fine. values not changed.

Let's write a builder that returns (values, entity, field, filters, lambda_for_list_conv).

Note lambda_for_list_conv must be a function; define at module level:

def _conv(a, b):
    return a + [str(b)]

Cases must not raise. Path 3 raises — put that in checks.

checks: 
- empty values, minimal filters → no pheno_filters. values=[].
- filters with pheno_filters compound logic "or" → raises ValueError. That's a check (may raise).
- filters with pheno_filters not compound (a dict without "compound") → wraps. Or a None? Let's do one that raises and one edge.

Actually checks are "small edge inputs (empty, one element, None, an odd type)". Let's do 3:
1. empty values, empty filters dict → creates.
2. filters with pheno_filters = {"compound": [], "logic": "or"} → raises ValueError.
3. filters with pheno_filters = {"condition":"in","values":["a"]} (not compound) → wraps into compound, then appends new filter.

Wait for #3: after wrapping, filters["pheno_filters"] = {"compound": [old], "logic":"and"}. Then entity_field search: old has no "filters" key → continue. entity search: old has no "entity" → continue. other_entity_field: old has no "filters" → continue. Append new. Returns. Good.

Now cases. Let me design 8.

Common: entity = "participant", field = "gender" or similar. Actually in dx-toolkit cohorts, entity like "patient", field like "patient_id". Let's use entity="patient", field="patient_id", entity_field = "patient$patient_id".

Case 1: existing compound filter with entity_field filter, condition "in", values 60k, primary values 60k (list of strings). Intersection.
Case 2: same but condition "not-in", values 60k, primary values 40k.
Case 3: multiple primary_filters: one "exists", one "in" with 30k.
Case 4: multiple compound filters, first several don't match (no entity_field), later one matches with "in".
Case 5: path 6 — compound filter with filters {"patient$other_field": [...]}, entity "patient" → adds.
Case 6: path 5 — compound filter with entity {"name":"patient"} → adds.
Case 7: path 1 — no pheno_filters, large values 80k.
Case 8: path 2 — pheno_filters without compound, large values 80k.

Hmm, but work for cases 5-8 is small (just dict ops) - maybe <1ms. The instruction says one call roughly 1ms-200ms. Small cases might be <1ms but that's fine-ish; they'll be dropped in favor of the heavy ones (we keep 4 that do most work). But we should still have 8 valid.

Let's make the heavy ones heavier: values 200k? Output limit: returned filters contains values list of up to 200k → under 100k values? "keep what it returns (and anything it writes) under about 100 000 values". So returned values should be < 100k. Let's cap at ~80k.

Hmm, but the returned filters contains the values list (in path 4, the new values after intersection, which is smaller). In path 1, returned filters contains values directly (80k). That's under 100k. OK.

Also arguments under 1M values: filters with primary values list of 80k, plus values 80k → 160k. Fine.

Let's aim for ~50-100ms calls. Sorting 80k strings: ~30ms. Set intersection of 80k: ~10ms. reduce with list append: 80k appends ~10ms. Total maybe 50ms.

Let's make case 1 values=80000, primary values=80000 with overlap ~50%.

Actually let's be careful about the output size for "in": sorted intersection could be up to 80k. Fine.

Let me now write the generator.

```python
import copy
import random

from dxpy.dx_extract_utils.cohort_filter_payload import generate_pheno_filter


def _conv(a, b):
    return a + [str(b)]


def _vals(n, seed, prefix="v"):
    rng = random.Random(seed)
    return [f"{prefix}{rng.randrange(10**9)}" for _ in range(n)]
```

Hmm, but for intersection to be non-trivial we need overlap. Generate primary values from the same pool.

Let me make a helper that generates a pool and picks subsets.

```python
def _pool(n, seed):
    rng = random.Random(seed)
    return [f"id{rng.randrange(10**9):09d}" for _ in range(n)]
```
Duplicates possible but rare.

Actually to have controlled overlap: generate values as list of strings, and primary values as a sublist of values plus some extras.

Let's write:

```python
def _make_in_case(n_values, n_primary, seed, condition="in"):
    rng = random.Random(seed)
    pool = [f"id{i}" for i in range(n_values + n_primary)]
    rng.shuffle(pool)
    values = pool[:n_values]
    primary = pool[n_values//2 : n_values//2 + n_primary]
    ...
```

Simpler: values = [f"id{i}" for i in range(n_values)]; primary = [f"id{i}" for i in range(offset, offset+n_primary)] where offset creates overlap.

Let me just do that — strings "id0".."idN". Overlap = n_values - offset.

Careful: "avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit". Sorted sequential ids is a pattern. Hmm. But sorting is done anyway. Let's shuffle with a fixed seed to make it non-sequential. Use random.Random(seed).shuffle.

OK.

Let me write a generic builder for filters.

```python
def _filters_with_entity_field(primary_filters, entity_field, extra_compound=None):
    compound = extra_compound or []
    compound.append({"name": "phenotype", "logic": "and", "filters": {entity_field: primary_filters}})
    return {"pheno_filters": {"compound": compound, "logic": "and"}}
```

Now cases.

Case 1 "in-large":
values: 80000 ids, primary: 80000 ids with 50% overlap → intersection ~40000.
Actually to make it work: values = ids[0..80000), primary = ids[40000..120000). Intersection = 40000. Result sorted 40000 strings. reduce over 80000 elements building list of 80000 then set. Good.

Case 2 "not-in-large":
condition "not-in", values 80000, primary 30000 → difference 50000+.

Case 3 "exists-plus-in":
primary_filters = [{"condition":"exists"}, {"condition":"in","values": primary40k}]. values 60000.

Wait order matters: loop over primary_filters, for "exists" pass (values unchanged), then "in" intersects. Then append {"condition":"in","values":values}. Good.

Case 4 "multi-compound":
compound with several non-matching filters first, then matching one. Each non-matching has "filters" key with other entity_field or no filters key.

Case 5 "entity-name-match": compound = [{"entity":{"name":"patient"},"filters":{}}]... wait the code: for compound_filter in compound: if "entity" not in ... continue; if name != entity continue; then compound_filter["filters"][entity_field] = [...]. So the compound_filter must have "filters" key. Let's include {"entity": {"name":"patient"}, "filters": {"other": []}}.

Case 6 "other-field-same-entity": compound = [{"filters": {"patient$other_field": [{"condition":"in","values":["x"]}]}}]. entity_field.split("$")[0] == "patient" → match.

Case 7 "no-pheno-filters": filters = {} with large values 80000. Returns filters with new compound containing values (80000). Output value count 80000 < 100k. OK.

Case 8 "non-compound-wrap": filters = {"pheno_filters": {"condition": "in", "values": ["a","b"]}} with values 80000.

Hmm, case 8 output: filters["pheno_filters"] = {"compound":[old, new], "logic":"and"}. Contains 80000 values. Fine.

Now, the thunks need fresh copies. For cases 1-6, base filters contain primary values lists (large). deepcopy per call. That's setup cost. For case 1, deepcopy of 80k-element list ~ maybe 20ms. Acceptable? The call is ~50ms. Hmm, "keep a thunk cheap next to one call". 20ms vs 50ms is okay-ish but let's reduce. Alternative: build filters fresh each thunk call by constructing dicts referencing shared lists. The function doesn't mutate the primary_filter["values"] lists (reduce just reads). It does mutate compound_filter["filters"][entity_field] = primary_filters (replaces the list reference in the dict). And appends to primary_filters (which is the list we passed as compound_filter["filters"][entity_field]).

Wait: `primary_filters = []` then iterates over compound_filter["filters"][entity_field], appending to primary_filters. Then `compound_filter["filters"][entity_field] = primary_filters`. So the original list object is replaced in the dict, not mutated. Good. But the original list is referenced by our base... if we share base dict across calls, the dict gets mutated. So we need a fresh dict each call, but can we share the large inner lists?

The mutation: filters["pheno_filters"]["compound"] — for path 4 we return early after setting compound_filter["filters"][entity_field]. The compound_filter dict is mutated (key set). If we build fresh dicts per call but share the inner lists (primary_filter dicts and values lists), that's fine because inner dicts aren't mutated... Actually primary_filter dicts are only read. compound_filter["filters"] dict gets a key set — so that dict must be fresh.

So the thunk can build the structure with fresh dicts but shared big lists. That's cheap.

Let's write builder functions that construct fresh dicts each call, referencing shared large lists.

For case 1:
```python
_VALS_1 = [...]
_PRIMARY_1 = [...]
def _case1():
    entity_field = "patient$patient_id"
    cf = {"name":"phenotype","logic":"and","filters":{entity_field: [{"condition":"in","values":_PRIMARY_1}]}}
    filters = {"pheno_filters": {"compound":[cf], "logic":"and"}}
    return (_VALS_1, "patient", "patient_id", filters, _conv)
```
Wait but `_VALS_1` is shared and placed into output. Not mutated. Fine.

But careful: the harness renders arguments before and after to check changes. Rendering a big dict... it says keep each input's data under about 1,000,000 values. Our filters has 80k primary values. Fine.

Hmm, but the check "arguments are rendered before and after each call to see whether it changed them" — with 80k values the render is expensive but that's their problem.

Actually wait, there's a subtlety: the returned filters (output) contains a reference to _VALS_1 (in path 4 the new values list, not _VALS_1). In path 1, output contains _VALS_1. If the harness compares outputs across calls, fine.

But another subtlety: if the function mutates the shared primary_filter dicts... it doesn't.

OK. But careful with case 1: after the call, the compound_filter dict we created fresh is mutated; next call creates a new one. Good.

Now, one more: the `filters` dict passed is the one returned. The harness compares outputs between original and modified versions. Fine.

Let me now write it all.

Let me define a helper to build shuffled id lists:

```python
def _ids(n, seed, start=0):
    rng = random.Random(seed)
    vals = [f"id{start + i}" for i in range(n)]
    rng.shuffle(vals)
    return vals
```

Actually simpler: generate random numeric ids.

```python
def _rand_ids(n, seed):
    rng = random.Random(seed)
    return [f"id{rng.randrange(10**12):012d}" for _ in range(n)]
```
Then overlap control: take a base pool and slice.

Let me do:

```python
def _overlap_pair(n_values, n_primary, overlap, seed):
    rng = random.Random(seed)
    total = n_values + n_primary - overlap
    pool = [f"id{rng.randrange(10**12):012d}" for _ in range(total)]
    # ensure uniqueness? not needed
    values = pool[:n_values]
    primary = pool[n_values - overlap : n_values - overlap + n_primary]
    return values, primary
```

Good. For "in": intersection = overlap elements (roughly). For "not-in": difference = n_values - overlap.

Now sizes:
- Case 1: n_values=80000, n_primary=80000, overlap=40000. Intersection 40000 sorted.
- Case 2: not-in, n_values=80000, n_primary=30000, overlap=25000 → difference 55000.
- Case 3: exists + in, n_values=60000, n_primary=40000, overlap=20000.
- Case 4: multi-compound, matching one with in, n_values=50000, n_primary=50000, overlap=25000.
- Case 5: entity name match, values 50000, small primary.
- Case 6: other-field same entity, values 50000.
- Case 7: no pheno_filters, values 80000.
- Case 8: non-compound wrap, values 80000.

Hmm cases 5-8 have values 50-80k but the function does little with them (just stores the list). Work is O(1) basically. So they'll be slow? No, fast. That's fine; they'll be among the dropped 4.

But wait — cases 5,6,7,8 with 80k values: the function just stores them. Very fast (<1ms). The instruction wants roughly 1ms-200ms. Hmm. But it says "One call should take roughly 1 ms to 200 ms on the original." Maybe make them do more? We can't easily. Alternatively, make these cases have large filters structures to copy? No copying happens.

Actually, maybe the harness's rendering of arguments dominates? No, only the call is timed.

I think it's acceptable to have some fast cases; the 4 heaviest are kept. But to be safe, let's make the non-heavy paths also somewhat heavy by having many compound filters (e.g. 2000 compound filters that don't match) so the loop iterates. That adds work.

For case 5: put 500 non-matching compound filters before the matching one, each with a "filters" dict with a few keys. The loop over compound filters: for path 5 (entity name), each iteration checks "entity" in cf. Cheap. 

For case 6: the third loop iterates over all compound filters and their "filters" keys. With many filters and many keys, work grows. E.g. 1000 compound filters each with 20 keys → 20000 iterations. Still fast.

Hmm. Let's make case 6 have many keys: e.g. 2000 compound filters × 50 keys = 100k iterations of split("$") — split is a bit expensive. Maybe ~50ms. Good.

Actually the third loop: for each compound_filter with "filters", for each other_entity_field: split and compare. If entity matches, it returns immediately. So to make it work, the matching one should be last. Put 2000 non-matching compound filters each with 50 keys of different entities, then the matching one. That's 100k split operations + string compares. Probably ~100ms. 

Let's do that. But building that structure per thunk call: 2000 dicts × 50 keys = 100k dict entries per call. That's heavy setup. Hmm, but setup isn't timed. Still, it must be built per call (since dicts get mutated? In case 6, the matching compound_filter["filters"] gets a new key — so that dict must be fresh; the non-matching ones aren't mutated... but they're nested inside filters, and we return filters. Actually the function mutates only the matching compound_filter's filters dict. So we could share the non-matching ones. But building filters structure each call requires creating the top-level dict and compound list.

Simpler: build the base structure once at module level, and in the thunk do a shallow-ish copy: new top dict, new compound list, and for the matching filter a new dict. But that's fiddly.

Alternative: just deepcopy the whole thing. deepcopy of 100k small dicts is slow (~100ms+). Hmm.

Let me reconsider: maybe keep case 6 modest: 200 compound filters × 20 keys = 4000 iterations. Fast but fine.

Honestly, the harness keeps the 4 heaviest. We just need 8 valid cases. Let's not over-engineer. I'll make cases reasonably heavy but ensure correctness.

Let me settle:

Case 1: in, 80k/80k, overlap 40k. (heavy)
Case 2: not-in, 80k/30k, overlap 25k. (heavy)
Case 3: exists+in, 60k/40k, overlap 20k. (heavy)
Case 4: multi-compound, matching in 50k/50k overlap 25k, with 3 preceding non-matching compound filters. (heavy)
Case 5: entity-name match, values 40k, with 100 preceding compound filters without entity. (light)
Case 6: other-field same entity, values 40k, with 200 preceding compound filters with different entities, each with 10 keys. (medium)
Case 7: no pheno_filters, values 80k. (light)
Case 8: non-compound wrap, values 80k. (light)

Now, for case 4: the first loop iterates over compound filters; for each, checks "filters" in cf and entity_field in cf["filters"]. Non-matching ones have filters with other keys.

Let me write builders.

For shared big lists, define at module level.

Now the thunks: build fresh dicts referencing shared lists.

Let me write:

```python
_EF = "patient$patient_id"
_ENTITY = "patient"
_FIELD = "patient_id"
```

Case 1:
```python
_V1, _P1 = _overlap_pair(80000, 80000, 40000, 0)

def _case1():
    filters = {"pheno_filters": {"compound": [
        {"name": "phenotype", "logic": "and",
         "filters": {_EF: [{"condition": "in", "values": _P1}]}}
    ], "logic": "and"}}
    return (_V1, _ENTITY, _FIELD, filters, _conv)
```

Case 2 similar with not-in.

Case 3:
```python
_V3, _P3 = _overlap_pair(60000, 40000, 20000, 2)
def _case3():
    filters = {"pheno_filters": {"compound": [
        {"name":"phenotype","logic":"and","filters":{_EF:[
            {"condition":"exists"},
            {"condition":"in","values":_P3},
        ]}}
    ], "logic":"and"}}
    return (_V3, _ENTITY, _FIELD, filters, _conv)
```

Case 4:
```python
_V4, _P4 = _overlap_pair(50000, 50000, 25000, 3)
def _case4():
    compound = [
        {"name":"phenotype","logic":"and","filters":{"patient$other": [{"condition":"in","values":["a"]}]}},
        {"name":"phenotype","logic":"and","filters":{"sample$id": [{"condition":"in","values":["b"]}]}},
        {"name":"phenotype","logic":"and"},
        {"name":"phenotype","logic":"and","filters":{_EF:[{"condition":"in","values":_P4}]}},
    ]
    filters = {"pheno_filters": {"compound": compound, "logic":"and"}}
    return (_V4, _ENTITY, _FIELD, filters, _conv)
```

Wait, the first loop: for cf in compound: if "filters" not in cf or entity_field not in cf["filters"]: continue. cf1 has filters but not entity_field → continue. cf2 same. cf3 no filters → continue. cf4 matches. Good.

Case 5:
```python
_V5 = _rand_ids(40000, 5)
def _case5():
    compound = [{"name":"phenotype","logic":"and","filters":{"sample$id":[{"condition":"in","values":["x"]}]}} for _ in range(100)]
    compound.append({"name":"phenotype","logic":"and","entity":{"name":"patient"},"filters":{"sample$id":[{"condition":"in","values":["x"]}]}})
    filters = {"pheno_filters":{"compound":compound,"logic":"and"}}
    return (_V5, _ENTITY, _FIELD, filters, _conv)
```
Wait: first loop checks entity_field in cf["filters"] — none have it. Second loop: checks "entity" in cf and "name" in cf["entity"]; only the last matches. Good. But careful, cf with entity has "filters" key. Yes.

Hmm but the second loop: `compound_filter["filters"][entity_field] = [entity_field_filter]`. The last cf's filters dict is fresh per call. Good.

Case 6:
```python
_V6 = _rand_ids(40000, 6)
def _case6():
    compound = []
    for i in range(200):
        compound.append({"name":"phenotype","logic":"and","filters":{f"sample${j}": [{"condition":"in","values":["x"]}] for j in range(10)}})
    compound.append({"name":"phenotype","logic":"and","filters":{"patient$other_field":[{"condition":"in","values":["x"]}]}})
    ...
```
Wait, the third loop: for cf with "filters", for other_entity_field in cf["filters"]: if other_entity_field.split("$")[0] != entity: continue. The non-matching ones have "sample$..." → continue. The last has "patient$other_field" → matches → sets entity_field. Good.

But building 200×10 dicts per call = 2000 dict entries, cheap.

Case 7:
```python
_V7 = _rand_ids(80000, 7)
def _case7():
    return (_V7, _ENTITY, _FIELD, {}, _conv)
```

Case 8:
```python
_V8 = _rand_ids(80000, 8)
def _case8():
    return (_V8, _ENTITY, _FIELD, {"pheno_filters": {"condition":"in","values":["a","b"]}}, _conv)
```

Wait case 8: filters has pheno_filters which is not compound. So it wraps: filters["pheno_filters"] = {"compound":[{"condition":"in","values":["a","b"]}], "logic":"and"}. Then first loop: cf = {"condition":"in","values":[...]}, no "filters" → continue. Second: no "entity" → continue. Third: no "filters" → continue. Append new. Good.

Now checks:
```python
def checks():
    return [
        ("empty-values-empty-filters", lambda: ([], "patient", "patient_id", {}, _conv)),
        ("bad-logic-raises", lambda: (["a"], "patient", "patient_id",
            {"pheno_filters": {"compound": [], "logic": "or"}}, _conv)),
        ("non-compound-pheno", lambda: (["a","b"], "patient", "patient_id",
            {"pheno_filters": {"condition":"in","values":["a"]}}, _conv)),
    ]
```
Wait check 2: pheno_filters has "compound" so first branch skipped. Then `elif "logic" in filters["pheno_filters"] and ... != "and"` → raises ValueError. Good.

Check 1: filters={} → creates pheno_filters, then loops over empty compound, appends new. Returns.

Check 3: as described.

Hmm, but check 2 raises — is that ok? "These may raise." Yes.

Now, `_rand_ids` — need distinct ids for realistic. Use rng.

Let me write `_rand_ids`:
```python
def _rand_ids(n, seed):
    rng = random.Random(seed)
    return [f"id{rng.randrange(10**12):012d}" for _ in range(n)]
```

And `_overlap_pair`:
```python
def _overlap_pair(n_values, n_primary, overlap, seed):
    rng = random.Random(seed)
    total = n_values + n_primary - overlap
    pool = [f"id{rng.randrange(10**12):012d}" for _ in range(total)]
    values = pool[:n_values]
    primary = pool[n_values - overlap:n_values - overlap + n_primary]
    return values, primary
```

Check sizes: case1 total = 80000+80000-40000 = 120000. Fine.

Now, one concern: the function returns filters, and the output includes the values list. For case 1, the new values list has ~40000 elements. Under 100k. Good.

For case 7, output filters contains _V7 (80000). Under 100k. Good.

For case 8, output contains _V8 (80000). Good.

Case 5: output contains _V5 (40000). Good.

Now the total memory: all these lists ~ 80k+80k+60k+40k+50k+50k+40k+80k+80k strings. Each string ~60 bytes → ~3.5M chars... roughly 350k strings * ~70 bytes = 25MB. Fine.

Wait _P1 is 80000, _V1 80000, _P3 40000, _V3 60000, _P4 50000, _V4 50000, _V5 40000, _V6 40000, _V7 80000, _V8 80000. Total ~560k strings. ~40MB. Under 100MB. OK.

Hmm, "Keep the data in memory under about 100 MB". OK.

Building all inputs: generating 560k random strings — fast, maybe 1-2s. Fine.

Now, one issue: `_conv` is a module-level function. The task says "no assigning functions or lambdas to attributes" — that's about mocks. Passing a plain function as a parameter is fine; the repository's own test does exactly that.

Now, one more consideration: the thunk builds filters fresh each call. Good.

But wait: in case 4, I create compound list with dicts each call. Fine.

Also case 5: list comprehension of 100 dicts each call. Fine.

Let me double check the "in" branch: `values = sorted(set(values).intersection(set(reduce(lambda_for_list_conv, primary_filter["values"], []))))`.

`reduce(_conv, _P1, [])` → starts with [], for each b in _P1 appends str(b) → list of 80000 strings. Then set() of that. Then intersection with set(values). Then sorted. Good, that's the heavy part.

Note that `_conv` does `a + [str(b)]` which is O(n) per step → O(n²)! Wait: `a + [str(b)]` creates a new list of length len(a)+1 each time. That's O(n²) overall! For n=80000, that's 3.2 billion operations — way too slow!

Hmm. That's the test's lambda. `lambda a, b: a+[str(b)]`. With reduce over a list, this is quadratic. In the test, primary_filter["values"] is probably small (like one element).

So I must not use huge primary_filter["values"] lists with this lambda. Because reduce with list-concat is O(n²).

Let me reconsider. Realistic: primary_filter["values"] is a list of value-lists, e.g. [["patient_1","patient_2"]] — one element. Then reduce gives ["['patient_1', 'patient_2']"]. Hmm.

Actually the lambda is `lambda_for_list_conv` — "lambda for list conversion". It converts a list of lists into a flat list? `a+[str(b)]` where b is a list → str(list). Hmm, that gives string repr.

Let me look at the test context more. expected_sql: `WHERE patient_1."patient_id" IN ('patient_1', 'patient_2')`. And filters probably:

```python
filters = {
    "pheno_filters": {
        "compound": [
            {
                "name": "phenotype",
                "logic": "and",
                "filters": {
                    "patient$patient_id": [
                        {"condition": "in", "values": [["patient_1", "patient_2"]]}
                    ]
                }
            }
        ],
        "logic": "and"
    }
}
```

Hmm, then reduce gives ["['patient_1', 'patient_2']"] and values would be like ["['patient_1', 'patient_2']"]? That seems odd.

Alternatively primary_filter["values"] = ["patient_1", "patient_2"] and reduce gives ["patient_1","patient_2"]. That makes sense! The lambda converts each element to str and concatenates. So primary_filter["values"] is a flat list of values (possibly of various types). And the result is a list of strings.

Yes, that's consistent: `lambda a, b: a + [str(b)]` flattens/converts a list of values to strings.

But the O(n²) issue remains: with n elements, reduce is quadratic.

Hmm, but in real usage the lists might be small. The test uses 2.

So for our heavy cases, we can't use large primary_filter["values"] with this lambda. Unless we use a different lambda_for_list_conv that's linear. But the task says use realistic lambda... The lambda is a parameter passed by the caller. The repository's caller (cohort_filter_payload) receives it from the user. In the test it's `lambda a, b: a+[str(b)]`.

Hmm, but we could pass a different lambda, e.g. `lambda a, b: a + [str(b)]` is what's used. Alternatively use a lambda that's linear like `lambda a, b: a + [str(b)]`... no.

Wait, actually maybe we can use a linear lambda that represents the same semantics: `lambda a, b: a + [str(b)]` vs... The function under test just calls reduce with it. If we pass a linear version like:

```python
def _conv(a, b):
    a.append(str(b))
    return a
```
That mutates and is O(n). But is that realistic? The repo's lambda is the non-mutating version. Hmm.

The task says "Prepare the way the repository's own callers do". The caller passes lambda_for_list_conv. In the test it's `lambda a, b: a+[str(b)]`. But other callers might pass different. Since it's a parameter, and we're testing the function's work, using a linear lambda would change the work profile... but it's legitimate: the function's work with a given lambda.

Hmm, but the point of the benchmark is to measure the function's energy. If the lambda dominates (quadratic), we're measuring the lambda, not the function. That's bad. So we should use a lambda that doesn't dominate: linear.

But then is that "realistic"? The parameter exists to be provided. I think using a linear equivalent is reasonable and avoids measuring the lambda. Actually, let's think: with the repo's lambda and n=80000, the reduce is 3.2e9 list-element copies → seconds to minutes. That would exceed 1s per call → dropped. So we must use smaller n or a linear lambda.

Option: keep the repo's lambda but use small primary values (like 100 elements) → quadratic 10^4, negligible. Then the heavy work is the set intersection and sort of large `values` (80000). That's fine! The primary values list doesn't need to be large.

Yes! That's the cleanest: primary_filter["values"] small (say 50-500 elements), `values` large. Then reduce is cheap, set intersection/sort of 80000 is the work.

But then "in" intersection: set(values) ∩ set(small primary) → small result. Work: building set(values) 80000, intersect, sort small. ~10ms. Fine.

For "not-in": set(values) - set(primary) → 80000 elements sorted → ~30ms. Good.

Hmm, but is it realistic that values is 80000 and primary is small? Realistically both are user-provided lists of entity ids. Could be thousands. With the repo's quadratic lambda, thousands would be 10^6-10^7 ops — 1M elements list concat: for n=5000, 12.5M element copies ~ 50ms. Borderline.

Let me use primary sizes up to ~2000 and values up to 80000. reduce with n=2000: 2M operations ~ 10ms. Acceptable, and it's genuinely the repo's lambda.

Hmm, but then the quadratic behavior is part of the measured work. It's the same for original and modified, so it's fine — it's just part of the function's cost.

Actually, wait. Let me reconsider: is the quadratic really that bad? `a + [str(b)]` for list of length k creates a new list of k+1. Total element copies = sum_{k=1}^{n} k = n²/2. For n=2000: 2M copies. Python list copy is fast (~10ns/elem?) → 20ms. Hmm, plus str() calls. OK.

For n=5000: 12.5M → ~125ms. Too much maybe.

Let's use primary sizes 500-2000.

Actually, let's reconsider whether to use the repo's exact lambda. I think yes, use `lambda a, b: a + [str(b)]` — it's what the repo does. Keep primary lists moderate.

Revised design:

Case 1 "in": values 80000 (large), primary 1000. Intersection small. Work: set(values) 80000 + reduce 1000 (quadratic 500k) + sort small. ~15ms.

Hmm, that's dominated by set(values). Fine.

Case 2 "not-in": values 80000, primary 1000. Difference ~79000, sorted. ~40ms.

Case 3 "exists+in": values 60000, primary 2000, plus exists.

Case 4 "multi-compound matching in": values 60000, primary 1500.

Hmm, these are all similar. Let's diversify: some with large primary (but then quadratic dominates...). Let's cap primary at 2000.

Actually, to get more work diversity, vary values sizes: 100k? Output limit 100k. For not-in, output = values size ~ 100k → right at limit. Keep values ≤ 80000.

Let's also add a case where values has many duplicates (set dedup work) and where primary has duplicates.

OK let me finalize.

Actually, hold on. Let me reconsider the "in" case more: `set(values).intersection(set(reduce(...)))`. If primary has 1000 elements and values 80000, result ≤1000. Fine.

Let me also consider: maybe use a larger primary for "in" so intersection is meaningful, e.g. primary 2000 drawn from values pool → intersection 2000. Good.

Let me now write final code.

```python
import random

from dxpy.dx_extract_utils.cohort_filter_payload import generate_pheno_filter


def _conv(a, b):
    return a + [str(b)]


_ENTITY = "patient"
_FIELD = "patient_id"
_EF = "patient$patient_id"


def _rand_ids(n, seed):
    rng = random.Random(seed)
    return [f"id{rng.randrange(10**12):012d}" for _ in range(n)]


def _values_and_primary(n_values, n_primary, overlap, seed):
    rng = random.Random(seed)
    pool = [f"id{rng.randrange(10**12):012d}" for _ in range(n_values + n_primary - overlap)]
    values = pool[:n_values]
    primary = pool[n_values - overlap:n_values - overlap + n_primary]
    return values, primary
```

Hmm, overlap for "in": primary drawn from values region. Let me ensure overlap elements: primary = pool[n_values-overlap : n_values-overlap+n_primary]. The first `overlap` elements of primary are pool[n_values-overlap:n_values], which are the last `overlap` elements of values. So intersection = overlap. Good.

Case definitions:

```python
_V1, _P1 = _values_and_primary(80000, 2000, 1500, 1)

def _case1():
    filters = {"pheno_filters": {"compound": [
        {"name": "phenotype", "logic": "and",
         "filters": {_EF: [{"condition": "in", "values": _P1}]}}
    ], "logic": "and"}}
    return (_V1, _ENTITY, _FIELD, filters, _conv)
```

Case 2 not-in: values 80000, primary 2000, overlap 1500 → difference 78500.

```python
_V2, _P2 = _values_and_primary(80000, 2000, 1500, 2)
```

Case 3: exists + in with values 60000, primary 3000, overlap 2000.
_V3, _P3 = _values_and_primary(60000, 3000, 2000, 3)

Case 4: multi-compound, values 50000, primary 2500, overlap 2000.

Case 5: entity-name match, values 50000.
Case 6: other-field same entity, values 50000, with preceding compound filters.
Case 7: no pheno_filters, values 80000.
Case 8: non-compound wrap, values 80000.

Now the quadratic: primary 3000 → 4.5M copies → ~30-50ms. Plus str() 3000 times. Acceptable.

Hmm, actually let me reconsider: is `a + [str(b)]` really quadratic in CPython? Yes, list concatenation copies. 4.5M element copies of pointers = 36MB memcpy total, fast (~few ms). Plus allocation overhead. Probably ~20ms. Fine.

Let me just be a bit conservative: primary ≤ 3000.

Now let's double-check case 3 order: primary_filters = [{"condition":"exists"}, {"condition":"in","values":_P3}]. Loop: first "exists" → pass (values unchanged). Second "in" → values = sorted(intersection). Then append {"condition":"in","values":values}. Good.

Case 4: I want the first loop to skip several compound filters. Let's include compound filters with "filters" containing other entity_fields and one without "filters".

Now writing everything.

One more check: in case 5, the second loop requires compound_filter["entity"]["name"] == entity. Our matching cf: {"entity":{"name":"patient"}, "filters": {...}}. Good. But note the first loop also checks these cf: they have "filters" but not entity_field → continue. Good.

Also note: cf with "entity" must have "filters" key for the assignment. Yes.

Case 6: third loop. Compound filters with "filters" containing keys "sample$j" → split("$")[0] = "sample" != "patient" → continue. Last one "patient$other_field" → matches. Good.

Now, let me also ensure the entity_field is not present in any of the earlier cf's filters for cases 5,6 (otherwise path 4 triggers). In case 5, earlier cf filters have "sample$id". Good. Case 6 earlier have "sample$j". Good.

Now checks.

Let me write the final code.

Also need to make sure `generate_pheno_filter` import works. The task says import as given.

Potential issue: `dxpy.dx_extract_utils.cohort_filter_payload` module imports — it only imports copy and functools. Fine.

Let me write.

Actually one more thought on the `_conv` function: the repo uses a lambda. Using a def with the same behavior is fine.

Let me write the final answer.

For case 6, building 200 compound filters each with 10 keys per thunk call: 2000 dict entries, cheap.

Let me write:

```python
def _case6():
    compound = []
    for i in range(200):
        compound.append({
            "name": "phenotype",
            "logic": "and",
            "filters": {f"sample$field{j}": [{"condition": "in", "values": ["x"]}] for j in range(10)},
        })
    compound.append({
        "name": "phenotype",
        "logic": "and",
        "filters": {"patient$other_field": [{"condition": "in", "values": ["x"]}]},
    })
    filters = {"pheno_filters": {"compound": compound, "logic": "and"}}
    return (_V6, _ENTITY, _FIELD, filters, _conv)
```

Good.

Now case 5:
```python
def _case5():
    compound = [{"name": "phenotype", "logic": "and",
                 "filters": {"sample$id": [{"condition": "in", "values": ["x"]}]}}
                for _ in range(100)]
    compound.append({"name": "phenotype", "logic": "and",
                     "entity": {"name": "patient"},
                     "filters": {"sample$id": [{"condition": "in", "values": ["x"]}]}})
    filters = {"pheno_filters": {"compound": compound, "logic": "and"}}
    return (_V5, _ENTITY, _FIELD, filters, _conv)
```

Good.

Final: write it out.

Also, should I worry that `_V1` etc. are shared and placed into the returned filters (paths 5,6,7,8)? Not mutated. Fine.

But wait — the harness "renders arguments before and after each call to see whether it changed them". For case 7, filters={} is created fresh each call, so before/after within one call: the function mutates it. That's expected — the function mutates its argument. Would the harness flag that as "changed arguments"? Hmm. The function is designed to mutate filters. The harness checks whether arguments changed... If it flags mutation, that's inherent to the function. But comparing original vs modified, both mutate identically. I think it's fine — the note about copies is to ensure each call gets the same input.

Actually re-reading: "Its arguments are rendered before and after each call to see whether it changed them" — this is to detect if the function mutates inputs, presumably to ensure we handle it. Since the function always mutates filters, we provide a fresh copy each call. Fine.

OK, writing final.

Let me double check `_values_and_primary` when overlap > n_primary? overlap=1500 ≤ 2000. Fine. And n_values - overlap ≥ 0. Fine.

Also ensure primary slice indices valid: n_values - overlap + n_primary ≤ total = n_values + n_primary - overlap. Yes, equal. Good.

Write it.