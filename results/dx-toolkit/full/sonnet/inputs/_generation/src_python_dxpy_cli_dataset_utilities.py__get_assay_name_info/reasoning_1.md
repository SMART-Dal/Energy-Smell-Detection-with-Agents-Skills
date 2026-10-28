Let me analyze the function.

`get_assay_name_info(list_assays, assay_name, path, friendly_assay_type, rec_descriptor)`.

It uses `rec_descriptor.assays` via `get_assay_info`. So rec_descriptor just needs an `assays` attribute — a list of dicts.

For `list_assays=True`, it prints names and calls `sys.exit(0)` — that raises SystemExit. Hmm, that would raise. So for cases, we must use list_assays=False (which is what the repository callers do). Actually the test calls use list_assays=False.

For checks, we could include list_assays=True which raises SystemExit — allowed to raise. But it prints a lot. Keep small.

The function needs `friendly_assay_type` in {"germline", "somatic"}. Note: if friendly_assay_type is something else, `assay_type` is undefined -> NameError. So checks could include an odd type.

Now the workload: `get_assay_info` iterates over assay_list and partitions by `generalized_assay_model == assay_type`. So the work scales with number of assays. To make it substantial (1ms-200ms), we need many assays — maybe 100k-500k assays. Building a list of dicts with many keys... Each assay is a dict. 200k dicts might be ~100MB? Let's be careful.

Actually the function does: iterate all assays twice (once for get_assay_info, once more). Then list comprehensions over target_assays. Then for germline, loops over target_assays to find selected assay name, accessing nested fields.

So the heavy part is the number of assays and the size of dicts. Let's make assays with realistic fields: name, uuid, generalized_assay_model, reference_genome (dict with name), entities.genotype.fields.type.mapping.table, exclude_refdata etc.

We need to keep under 1,000,000 values for arguments. Each assay dict with ~6 keys and nested dicts... 100k assays * ~10 values = 1M values. Hmm, "each input's data under about 1 000 000 values" — that's a soft guideline. Let's aim for maybe 50k-100k assays.

But wait — does the function do enough work with 100k assays? Iterating 100k dict comparisons is maybe 10-20 ms. Good.

Let's design cases with different distributions:

1. germline, list_assays=False, assay_name=None, many target assays and other assays.
2. germline with assay_name given, matching a target assay in the middle.
3. somatic, assay_name=None.
4. somatic with assay_name matching.
5. germline with many other assays (few targets).
6. germline with reference_genome None for some.
7. somatic where reference is None (so selected_ref_genome stays "").
8. germline with exclude_* keys present.

Note that `assay_name` not in target names but in other names -> err_exit -> raises SystemExit. Avoid in cases.

Also note: err_exit raises SystemExit (it exits program). So avoid.

Careful: for germline, the loop `for a in target_assays: if a["name"] == selected_assay_name:` accesses `a["reference_genome"]` and `a["entities"]["genotype"]["fields"]["type"]["mapping"]["table"]` only when name matches. So only the selected assay needs those. But to be safe, give all target assays the full structure? Actually the check `if a["name"] == selected_assay_name` guards. So only selected assay needs nested structure. But if reference_genome is None, `if a["reference_genome"]` guards. Good.

For somatic: `if a["name"] == selected_assay_name and a["reference"]:` — needs "reference" key only for selected assay. But if assay_name given and matches, then selected_assay_name = assay_name, and loop over target_assays finds matching name; a["reference"] accessed. So selected assay needs "reference".

Let's build helper to create assay dicts.

For germline, selected assay fields:
- name, uuid, generalized_assay_model="genetic_variant", reference_genome={"name": "GRCh38.92.something"} -> split(".",1)[1] => "something" (needs at least one dot). Use {"name": "GRCh38.92.genome"}.
- entities: {"genotype": {"fields": {"type": {"mapping": {"table": [...]}}}}} — table could be a list of mappings; to add work, make it a decent-sized list? Hmm, that adds values. Keep moderate, e.g. list of 100 entries.

Actually additional_descriptor_info["genotype_type_table"] = that table. Output compared in full — the returned additional_descriptor_info contains the table. Keep under 100k values total. Fine.

Let's keep table as a list of maybe 50 dicts or just a list of strings.

For somatic, selected assay: reference: {"name": "GRCh38", "annotation_source_version": "v92"}.

Now the "other_assays" — assays with generalized_assay_model different, e.g. "expression" or "somatic_variant" etc. They need name and uuid (for other_assay_names). Actually other_assay_names = [oa["name"] for oa in other_assays] — needs "name". uuid not needed for others. But give both.

Now, work: get_assay_info iterates all. Then list comps over target_assays. So having many target assays increases work.

Case design (8 cases):

Let me define a builder:

```python
def _assay(name, uuid, model, kind):
    a = {"name": name, "uuid": uuid, "generalized_assay_model": model}
    if kind == "germline":
        a["reference_genome"] = {"name": "GRCh38.92.genome"}
        a["entities"] = {"genotype": {"fields": {"type": {"mapping": {"table": ["0/0", "0/1", "1/1", "0|1", "./."]}}}}}
        a["exclude_refdata"] = True
        a["exclude_halfref"] = False
        a["exclude_nocall"] = True
    elif kind == "somatic":
        a["reference"] = {"name": "GRCh38", "annotation_source_version": "v92"}
    return a
```

Hmm but the "a["exclude_refdata"]" present adds to additional_descriptor_info. Fine.

Wait: for germline, the loop for exclude_genotype checks `if exclude_genotype in a` for each target assay where name matches selected. Only selected. OK.

Now sizes. Let's do N total assays ~ 60,000 per case. Iterating 60k twice plus list comps... maybe 30-50 ms? Actually Python dict comparisons are fast; 60k * few ops ~ maybe 20ms. Let's aim higher: 150k? Memory: each dict ~ 300 bytes + nested dicts. 150k * ~1KB = 150MB. Too much maybe. Let's keep nested structures only on the selected assay, and make the rest lightweight dicts with 3 keys.

Lightweight assay: {"name":..., "uuid":..., "generalized_assay_model":...} ~ 200 bytes. 150k -> 30MB. Plus strings. OK.

But wait, for germline the loop `for a in target_assays: if a["name"] == selected_assay_name` — only accesses nested for selected. Good.

So make target assays mostly lightweight, with the selected one being rich. But then the function does less work per assay. Still, iterating 150k dicts is work.

Hmm, but the "work" measured is the whole call. Let's make number of assays large: 200k. Memory ~ 200k*200 = 40MB plus name strings. Names: f"assay_{i}" strings, each ~50 bytes. 200k*50 = 10MB. Fine, under 100MB.

Actually, the guideline: "each input's data under about 1 000 000 values". 200k assays * 3 values = 600k values. OK under 1M. Good. But 8 cases each with 200k assays -> building all inputs under 10s? Building 8*200k dicts = 1.6M dicts, maybe 3-5 seconds. Acceptable but let's be careful. Maybe use 100k per case.

Let's calibrate: a single call with 100k assays: two passes over 100k = 200k iterations, plus list comps. In Python maybe 30-60 ms. Good, within 1ms-200ms.

Let's use varying sizes per case to be diverse: 50k, 100k, 150k, 200k etc.

For list_assays=True case: it prints names of all target assays then sys.exit(0). That raises SystemExit, so can't be a measured case (must run to completion without raising). So all cases list_assays=False.

checks():
- empty assays list -> get_assay_info err_exit("No valid assays") -> raises SystemExit. Allowed.
- list_assays=True with one target -> prints and sys.exit -> raises SystemExit. Allowed.
- odd friendly_assay_type "weird" -> NameError (assay_type undefined). Allowed? It raises. Allowed for checks. But careful: if list_assays False and friendly_assay_type not germline/somatic, assay_type undefined -> NameError at get_assay_info call. Yes raises.

Actually wait, for "weird" with list_assays=True: assay_type undefined -> NameError too.

Let's do checks:
1. ("no-assays", lambda: (False, None, "record-xxx", "germline", _Desc([])))  -> err_exit raises SystemExit.
2. ("list-assays", lambda: (True, None, "record-xxx", "germline", _Desc([germline assay]))) -> prints, sys.exit raises SystemExit.
3. ("bad-type", lambda: (False, None, "record-xxx", "weird", _Desc([...]))) -> NameError.

Hmm, but checks are "checked only for identical behaviour" — if they raise, both original and modified must raise identically. Fine.

Now rec_descriptor: needs `.assays`. Use a simple class:

```python
class _Desc:
    def __init__(self, assays):
        self.assays = assays
```

That's fine — it's not a mock of a repository class; it's a plain data holder. The function only accesses `.assays`. Good. Actually "no mocks" — but building an input object with the attribute the function reads is fine ("Setting data ... to build an input is fine"). The real DXDataset.get_descriptor returns a descriptor object with `.assays`. We can't call DXDataset (needs network). So a simple namespace is the reasonable approach. This is a data input, not a mock of a repository class. I think acceptable.

Now, does the function call anything else that needs network? get_assay_info only reads rec_descriptor.assays. err_exit only on error paths. print for list_assays. So no network. Good.

Now module-level building: build the assay lists once.

Let me write:

```python
import random

class _Descriptor:
    def __init__(self, assays):
        self.assays = assays

_TABLE = ["0/0", "0/1", "1/1", "0|1", "1|0", "./.", ".|."]

def _germline_assay(i, rich=False):
    a = {"name": "germline_assay_%d" % i,
         "uuid": "assay-%08d" % i,
         "generalized_assay_model": "genetic_variant"}
    if rich:
        a["reference_genome"] = {"name": "GRCh38.92.genome"}
        a["entities"] = {"genotype": {"fields": {"type": {"mapping": {"table": list(_TABLE)}}}}}
        a["exclude_refdata"] = True
        a["exclude_halfref"] = False
        a["exclude_nocall"] = True
    return a
```

Wait, if rich=False, then in the loop for germline, when a["name"]==selected_assay_name (only the selected one), a["reference_genome"] accessed. So we need the selected assay to be rich. Also for the case where assay_name given and matches, selected_assay_name = assay_name; the loop finds the rich one. Good.

But careful: what if selected_assay_name = target_assay_names[0] and that first target is not rich? Then KeyError. So make the first target rich, or make all target assays rich? Making all rich increases memory a lot. Better: ensure the selected assay is rich. For assay_name=None, selected is target_assays[0], so make index 0 rich. For assay_name given, make that specific one rich.

Alternatively give all assays a "reference_genome": None and "entities" minimal? For germline, `if a["reference_genome"]` — if None, skip. And entities only accessed after that? Let's re-read:

```
for a in target_assays:
    if a["name"] == selected_assay_name:
        if a["reference_genome"]:
            selected_ref_genome = a["reference_genome"]["name"].split(".", 1)[1]
        additional_descriptor_info["genotype_type_table"] = a["entities"]["genotype"]["fields"]["type"]["mapping"]["table"]
        ...
```

So if reference_genome is None (falsy), skip split but still access entities. So entities always needed for the selected assay. So selected must be rich.

Simplest: build target list with the rich assay at a known position.

Let me structure: `_make_germline_case(n_targets, n_others, selected_index, assay_name, seed)`.

Actually to keep it simple, I'll build the list: first the rich selected assay, then the rest. But for diversity, put selected at different positions using random insertion? The function picks target_assays[0] when assay_name is None. So if assay_name is None, the rich one must be at position 0 among targets. If assay_name given, rich one must be the one with that name.

Let me just write a helper that builds a list of assays where a designated index (in the full list) is rich.

Plan:

```python
def _build_germline(n_target, n_other, rich_pos, seed):
    rng = random.Random(seed)
    assays = []
    for i in range(n_target):
        assays.append(_germline_assay(i, rich=(i == rich_pos)))
    for j in range(n_other):
        assays.append({"name": "other_%d" % j, "uuid": "other-%08d" % j,
                       "generalized_assay_model": rng.choice(["somatic_variant", "expression", "unknown"])})
    rng.shuffle(assays)
    return assays
```

But shuffling breaks rich_pos mapping. Instead, build with the rich assay at a chosen position in the *target* ordering. Since get_assay_info preserves order of target assays, target_assays[0] is the first genetic_variant assay in the list order. So if I want rich at target index k, I set rich for the k-th target. Let me just build the list in order: targets first then others, or interleave. Order in the list determines target order. So:

```python
def _build_germline(n_target, n_other, rich_idx, seed):
    rng = random.Random(seed)
    targets = [_germline_assay(i, rich=(i == rich_idx)) for i in range(n_target)]
    others = [{"name": "other_%d" % j, "uuid": "other-%08d" % j,
               "generalized_assay_model": rng.choice(["somatic_variant", "expression", "unknown"])}
              for j in range(n_other)]
    combined = targets + others
    rng.shuffle(combined)   # shuffling doesn't change relative order of targets? 
```

Shuffle does change relative order of targets! So don't shuffle, or shuffle before assigning rich. Simpler: don't shuffle; just interleave deterministically. Actually the order matters only for target order. Let's just not shuffle. But then "avoid uniformity/patterns" — the assays are all similar anyway. The function's work doesn't depend on order except for which is selected. Fine.

Actually, to be diverse, I can put others interspersed. Let me build: for i in range(max(n_target,n_other)): add target i, add other i. That interleaves. Targets keep their relative order. Good.

Let me write a generic builder:

```python
def _build(assay_factory, n_target, n_other, rich_idx, seed, other_models):
    rng = random.Random(seed)
    assays = []
    n = max(n_target, n_other)
    for i in range(n):
        if i < n_target:
            assays.append(assay_factory(i, i == rich_idx))
        if i < n_other:
            assays.append({"name": "other_%d" % i, "uuid": "other-%08d" % i,
                           "generalized_assay_model": rng.choice(other_models)})
    return assays
```

Now cases:

1. germline, no assay_name, 100k targets, 50k others, rich_idx=0.
2. germline, assay_name = name of target at rich_idx=70000, so it scans. 100k targets, 20k others.
3. germline, no assay_name, 200k targets, 0 others, rich_idx=0.
4. somatic, no assay_name, 120k targets, 30k others, rich_idx=0.
5. somatic, assay_name given matching rich_idx=50000, 80k targets, 40k others.
6. germline, no assay_name, 50k targets, 100k others, rich_idx=0.
7. somatic, no assay_name, 150k targets, 10k others, rich_idx=0.
8. germline, assay_name given matching rich_idx=0 (small scan), 60k targets, 60k others.

Hmm, cases 1 and 3 are similar. Let's diversify more.

Also note: for germline, selected_ref_genome default "GRCh38.92"; if reference_genome present, split. Rich assay has reference_genome -> selected_ref_genome = "genome". Fine.

For somatic, rich has reference -> selected_ref_genome = "GRCh38.v92".

Let me also consider making some rich assays have reference_genome = None to exercise the falsy branch. Case with rich assay having reference_genome None for germline: then selected_ref_genome stays "GRCh38.92", but entities accessed. Let's add a parameter.

Let me define germline factory with options.

Simplify: I'll write two factories with a `rich` flag and a `ref_none` flag.

Actually let's keep it manageable.

```python
def _germline_assay(i, rich, ref_none=False):
    a = {"name": "germline_assay_%d" % i,
         "uuid": "germline-%08d" % i,
         "generalized_assay_model": "genetic_variant"}
    if rich:
        a["reference_genome"] = None if ref_none else {"name": "GRCh38.92.genome"}
        a["entities"] = {"genotype": {"fields": {"type": {"mapping": {"table": list(_TABLE)}}}}}
        a["exclude_refdata"] = True
        a["exclude_halfref"] = False
        a["exclude_nocall"] = True
    return a
```

Hmm, but for non-rich target assays, no "reference_genome" key. That's fine since only selected is accessed.

But wait — what if assay_name given and the matching assay is rich? Yes we set rich_idx to match.

Now, one subtlety: `if a["name"] == selected_assay_name` — for non-rich assays this is False, so no KeyError. Good.

Now the additional_descriptor_info includes genotype_type_table (list of 7 strings) plus excludes. Output small.

Let's now think about whether the function's work is dominated by get_assay_info (iterating all assays). With 150k assays, two passes = 300k iterations, each doing a dict lookup and comparison. ~50ms. Plus list comps. Good.

Building 8 lists of ~150k dicts each = 1.2M dicts. Building time maybe 2-4s. OK.

Memory: 1.2M dicts * ~200 bytes = 240MB. Hmm, that might exceed 100MB. The guideline says "Keep the data in memory under about 100 MB". That's per input presumably. 150k dicts ~ 30MB. Fine. Total across all inputs maybe more but each input is separate. Actually all inputs are built and kept in memory before timing starts ("all built and kept in memory"). So total memory could be large. Hmm.

"all built and kept in memory before the timing starts" — yes all 8 cases' data stays in memory. So total must be reasonable. Let's reduce sizes: use ~50k-100k per case, 8 cases -> ~600k dicts ~ 120MB. Borderline. Let's use smaller: 30k-80k. But then work per call might be < 1ms? Let's estimate: 50k assays, two passes = 100k iterations ~ 15ms. That's fine, above 1ms.

Actually let's estimate more carefully. A simple loop over 100k dicts doing `a["generalized_assay_model"] == assay_type` and append: roughly 0.05 µs? No, Python is ~50-100ns per simple op; a loop iteration with dict lookup and comparison ~150ns. 100k iterations ~ 15ms. Two passes ~30ms. Good.

Hmm, actually let's just target ~100k total assays per case for the big ones, and vary.

Let me set sizes:
1. 80k targets, 20k others (100k total)
2. 70k targets, 30k others
3. 50k targets, 50k others
4. 60k targets, 40k others
5. 40k targets, 60k others
6. 90k targets, 10k others
7. 55k targets, 45k others
8. 30k targets, 70k others

Total ~800k assays. Memory maybe 160MB. Hmm. Each lightweight dict: dict object ~ 64 bytes overhead + 3 entries. In CPython, a dict with 3 items ~ 232 bytes (from sys.getsizeof). Plus keys (interned strings shared? "name", "uuid", "generalized_assay_model" are shared constants) and values: name string ~ 60 bytes, uuid string ~ 60 bytes, model string shared. So ~350 bytes per assay. 800k * 350 = 280MB. Too much.

Let's reduce. Use ~30k-50k per case, total ~300k assays -> ~105MB. Still borderline. Hmm.

Alternatively, share the same list across cases? No, each case needs distinct data ideally, but we could reuse... Actually cases can share the same underlying list if the function doesn't mutate it. The function doesn't mutate rec_descriptor.assays. So we could build a few lists and reuse them across cases with different list_assays/assay_name/friendly_assay_type. That reduces memory.

But the instruction wants diverse inputs. We can have maybe 4 distinct lists reused with different call parameters.

Hmm, but "Generate stressful inputs: ... as diverse as possible." Let's have some distinct lists but keep sizes moderate.

Let me reconsider: is 100MB hard? "Keep the data in memory under about 100 MB" — soft. Let's aim ~50-80MB total.

Let's use sizes around 20k-40k per case. Total ~250k assays -> ~90MB. Hmm.

Actually, let's reduce per-assay size: use tuples? No, function expects dicts (a["name"]). Must be dicts.

Alternative: make the name strings shorter. f"g{i}" and uuid f"u{i}". That reduces string size. With i up to 40000, strings are short (~6 chars -> ~55 bytes each including overhead). Two strings ~110 bytes. Dict 232 + 110 = ~342. Hmm similar.

Could use interned/shared strings? Names must be unique for the assay_name matching. But we could reuse names across cases... not within.

Let's just accept ~250k total assays. ~85MB. Fine, "about 100 MB".

Actually let me reconsider the work per call. 40k assays -> ~10ms. Good enough.

Let me pick:
- case sizes: 40k, 35k, 30k, 45k, 25k, 50k, 30k, 35k -> total 290k. ~100MB. Hmm.

Let's go a bit lower: 30k average. total 240k -> 82MB. OK.

Actually, I realize the rich assay has extra nested structures but only one per list. Negligible.

Let me finalize sizes:
1. germline, no name, 40k targets, 10k others (50k)
2. germline, name, 35k targets, 5k others (40k)
3. somatic, no name, 30k targets, 15k others (45k)
4. somatic, name, 25k targets, 10k others (35k)
5. germline, no name, ref_none rich, 20k targets, 20k others (40k)
6. germline, no name, 45k targets, 5k others (50k)
7. somatic, no name, 30k targets, 5k others (35k)
8. germline, name at idx 0, 25k targets, 25k others (50k)

Total ~345k assays. ~120MB. Hmm, over.

Let me cut: total ~250k. Sizes: 30k, 25k, 25k, 20k, 20k, 35k, 25k, 20k = 200k. ~70MB. Good.

But is 20k assays enough work? ~5ms. Fine (>1ms).

Hmm, but the task says "One call should take roughly 1 ms to 200 ms". 5ms is fine.

Actually, let me reconsider: maybe the dominant cost isn't the loop but... no, it's the loop.

Wait, actually there's a subtlety: `get_assay_info` is called twice (once for list_assays branch, once after). For list_assays=False, only once. Then list comps over target_assays. So cost ~ 1 pass over all assays + 3 passes over targets. Fine.

Let me increase a bit to be safe for the 1ms floor: 30k assays -> ~8ms. Good.

Let me settle on total ~250k assays.

Now about randomness: use random.Random(0) for generating. The instruction says use fixed seed when generating data. I'll use rng for other assay models and maybe for name ordering. Fine.

Let me now write the code.

```python
import random

class _Descriptor(object):
    def __init__(self, assays):
        self.assays = assays

_TABLE = ["0/0", "0/1", "1/1", "0|1", "1|0", "./.", ".|."]
_OTHER_MODELS = ["somatic_variant", "expression", "unknown", "genetic_variant"]  # careful!
```

Wait, "genetic_variant" in other models would make them targets. Don't include. Use ["somatic_variant", "expression", "unknown"].

For germline cases, target model = "genetic_variant" (matches assay_type "genetic_variant"). For somatic cases, target model = "somatic_variant".

Let me write generic builders:

```python
def _germline_assay(i, rich, ref_none=False):
    a = {"name": "germline_assay_%d" % i,
         "uuid": "germline-%08d" % i,
         "generalized_assay_model": "genetic_variant"}
    if rich:
        a["reference_genome"] = None if ref_none else {"name": "GRCh38.92.genome"}
        a["entities"] = {"genotype": {"fields": {"type": {"mapping": {"table": list(_TABLE)}}}}}
        a["exclude_refdata"] = True
        a["exclude_halfref"] = False
        a["exclude_nocall"] = True
    return a

def _somatic_assay(i, rich):
    a = {"name": "somatic_assay_%d" % i,
         "uuid": "somatic-%08d" % i,
         "generalized_assay_model": "somatic_variant"}
    if rich:
        a["reference"] = {"name": "GRCh38", "annotation_source_version": "v92"}
    return a
```

Wait for somatic: `if a["name"] == selected_assay_name and a["reference"]:` — if rich is False, no "reference" key -> KeyError when name matches. But name matches only for the selected one, which is rich. Good. But if assay_name given matches a non-rich? We set rich_idx to that. Good.

Now builder:

```python
def _build(factory, n_target, n_other, rich_idx, seed, ref_none=False):
    rng = random.Random(seed)
    assays = []
    n = max(n_target, n_other)
    for i in range(n):
        if i < n_target:
            if factory is _germline_assay:
                assays.append(factory(i, i == rich_idx, ref_none))
            else:
                assays.append(factory(i, i == rich_idx))
        if i < n_other:
            assays.append({
                "name": "other_%d" % i,
                "uuid": "other-%08d" % i,
                "generalized_assay_model": rng.choice(["somatic_variant", "expression", "unknown"]),
            })
    return assays
```

Hmm, but for germline cases, others with model "somatic_variant" etc. Fine.

But careful: for germline factory, others could have model "genetic_variant"? No, we choose from the other list. Good.

Now the descriptor: `_Descriptor(assays)`.

Cases:

```python
def cases():
    g1 = _build(_germline_assay, 30000, 10000, 0, 0)
    g2 = _build(_germline_assay, 25000, 5000, 12000, 1)
    s1 = _build(_somatic_assay, 25000, 15000, 0, 2)
    s2 = _build(_somatic_assay, 20000, 8000, 7000, 3)
    g3 = _build(_germline_assay, 20000, 20000, 0, 4, ref_none=True)
    g4 = _build(_germline_assay, 35000, 5000, 0, 5)
    s3 = _build(_somatic_assay, 25000, 5000, 0, 6)
    g5 = _build(_germline_assay, 20000, 25000, 0, 7)
    ...
```

Total assays: 40000+30000+40000+28000+40000+40000+30000+45000 = 293k. ~100MB. Hmm. Slightly high. Let me trim to ~200k.

Sizes: 
- g1: 25k targets, 5k others = 30k
- g2: 20k targets, 3k others = 23k
- s1: 20k targets, 10k others = 30k
- s2: 15k targets, 5k others = 20k
- g3: 15k targets, 15k others = 30k (ref_none)
- g4: 30k targets, 2k others = 32k
- s3: 20k targets, 3k others = 23k
- g5: 15k targets, 20k others = 35k

Total = 223k. ~75MB. OK.

Hmm, but wait: for case g2, rich_idx=12000 and assay_name must equal "germline_assay_12000". For s2, rich_idx=7000, assay_name = "somatic_assay_7000".

Let me double check case g2: assay_name given = "germline_assay_12000", which is in target_assay_names (since rich assay at target index 12000 has model genetic_variant). Yes. Then selected_assay_name = assay_name, loop finds it. Good.

For somatic s2: assay_name = "somatic_assay_7000". In target names. selected_ref_genome = "GRCh38.v92".

Now, one issue: in case g2, `assay_name not in list(target_assay_names)` — target_assay_names is already a list, wrapping in list() copies. Fine.

Now checks():

```python
def checks():
    return [
        ("no-assays", lambda: (False, None, "record-xxxx", "germline", _Descriptor([]))),
        ("list-assays", lambda: (True, None, "record-xxxx", "germline", _Descriptor([_germline_assay(0, True)]))),
        ("unknown-type", lambda: (False, None, "record-xxxx", "expression", _Descriptor([_germline_assay(0, True)]))),
    ]
```

Check 1: empty assays -> get_assay_info -> err_exit -> SystemExit (raises). Both original and modified should raise. Fine.

Check 2: list_assays=True -> prints name, sys.exit(0) -> SystemExit. Fine.

Check 3: friendly_assay_type "expression" -> assay_type undefined -> NameError. Fine.

Hmm, but the check "unknown-type" — actually if friendly_assay_type is "expression", neither branch sets assay_type, then get_assay_info(rec_descriptor, assay_type=assay_type) -> NameError. Yes.

Now, is there any concern about err_exit actually calling sys.exit? err_exit in dxpy prints and raises SystemExit. It might try to access sys.exc_info etc. Should be fine.

Now, do we need to worry about the function printing? For list_assays=True it prints. Fine.

Now, module-level code builds the data. But note: the thunks return `(list_assays, assay_name, path, friendly_assay_type, rec_descriptor)` positionally. The function signature is positional. Good.

Let me double check the function's parameter order: `get_assay_name_info(list_assays, assay_name, path, friendly_assay_type, rec_descriptor)`. Yes.

Now, the thunk returns a tuple of positional args. So `lambda: (False, None, "record-xxxx", "germline", _g1_desc)`.

Where _g1_desc = _Descriptor(g1).

I'll build descriptors at module level.

Let me now also double check: does the function mutate rec_descriptor.assays? No. Does it mutate the assay dicts? No. So reusing the same list across many calls is fine. Good — "same work on every call".

Now about the `path` argument: it's used only in error messages. Use a string like "record-xxxx" or a path. Fine.

Let me write final code.

One more consideration: the `_Descriptor` class — is it a "mock"? The rule says no subclass overriding a method of a repository class. _Descriptor is a plain object with an `assays` attribute. The function only reads `.assays`. This is building input data. The real descriptor is a DXDatasetDescriptor object. We can't construct it without network. I think it's acceptable — it's a data holder, akin to passing a dict. But to be safer, could we use a real object? `DXDatasetDescriptor.__init__(self, dxfile, **kwargs)` requires a dxfile. Not feasible. So plain object it is.

Hmm, actually, could we use a simple types.SimpleNamespace? Same thing. I'll use a small class.

Now write the code with careful formatting.

Let me also make sure the "other" assays have distinct names from targets, so assay_name lookup doesn't accidentally match an other assay (which would trigger err_exit). Names: "other_%d" vs "germline_assay_%d" — distinct. Good.

Also, the assay_name in g2 = "germline_assay_12000" — must not be in other names. Good.

Let me write it.

```python
import random


class _Descriptor(object):
    """Minimal stand-in for the object returned by DXDataset.get_descriptor()."""
    def __init__(self, assays):
        self.assays = assays


_TABLE = ["0/0", "0/1", "1/1", "0|1", "1|0", "./.", ".|.", "0/1", "1/1"]
_OTHER_MODELS = ["somatic_variant", "expression", "unknown"]


def _germline_assay(i, rich, ref_none=False):
    a = {
        "name": "germline_assay_%d" % i,
        "uuid": "germline-%08d" % i,
        "generalized_assay_model": "genetic_variant",
    }
    if rich:
        a["reference_genome"] = None if ref_none else {"name": "GRCh38.92.genome"}
        a["entities"] = {
            "genotype": {
                "fields": {"type": {"mapping": {"table": list(_TABLE)}}}
            }
        }
        a["exclude_refdata"] = True
        a["exclude_halfref"] = False
        a["exclude_nocall"] = True
    return a


def _somatic_assay(i, rich):
    a = {
        "name": "somatic_assay_%d" % i,
        "uuid": "somatic-%08d" % i,
        "generalized_assay_model": "somatic_variant",
    }
    if rich:
        a["reference"] = {"name": "GRCh38", "annotation_source_version": "v92"}
    return a


def _build(factory, n_target, n_other, rich_idx, seed, ref_none=False):
    rng = random.Random(seed)
    assays = []
    for i in range(max(n_target, n_other)):
        if i < n_target:
            if factory is _germline_assay:
                assays.append(factory(i, i == rich_idx, ref_none))
            else:
                assays.append(factory(i, i == rich_idx))
        if i < n_other:
            assays.append({
                "name": "other_%d" % i,
                "uuid": "other-%08d" % i,
                "generalized_assay_model": rng.choice(_OTHER_MODELS),
            })
    return assays


_G1 = _Descriptor(_build(_germline_assay, 25000, 5000, 0, 0))
_G2 = _Descriptor(_build(_germline_assay, 20000, 3000, 12000, 1))
_S1 = _Descriptor(_build(_somatic_assay, 20000, 10000, 0, 2))
_S2 = _Descriptor(_build(_somatic_assay, 15000, 5000, 7000, 3))
_G3 = _Descriptor(_build(_germline_assay, 15000, 15000, 0, 4, ref_none=True))
_G4 = _Descriptor(_build(_germline_assay, 30000, 2000, 0, 5))
_S3 = _Descriptor(_build(_somatic_assay, 20000, 3000, 0, 6))
_G5 = _Descriptor(_build(_germline_assay, 15000, 20000, 0, 7))
```

Wait, _G2 rich_idx=12000 but n_target=20000, so index 12000 exists. Good. _S2 rich_idx=7000, n_target=15000. Good.

Total assays: 30000+23000+30000+20000+30000+32000+23000+35000 = 223000. ~75MB. OK.

Now checks:

```python
def checks():
    return [
        ("no-assays", lambda: (False, None, "record-xxxx", "germline", _Descriptor([]))),
        ("list-assays", lambda: (True, None, "record-xxxx", "germline", _Descriptor([_germline_assay(0, True)]))),
        ("unknown-friendly-type", lambda: (False, None, "record-xxxx", "expression", _Descriptor([_germline_assay(0, True)]))),
    ]
```

Wait, for "no-assays" with empty list: get_assay_info -> `if not assay_list: err_exit(...)`. err_exit raises SystemExit. Good.

Hmm, actually err_exit signature: `err_exit(message='', code=None, ...)`. It calls sys.exit. Should raise SystemExit. But it might also try to print traceback info. Fine.

Now cases:

```python
def cases():
    return [
        ("germline-default", lambda: (False, None, "record-xxxx", "germline", _G1)),
        ("germline-named", lambda: (False, "germline_assay_12000", "record-xxxx", "germline", _G2)),
        ("somatic-default", lambda: (False, None, "record-xxxx", "somatic", _S1)),
        ("somatic-named", lambda: (False, "somatic_assay_7000", "record-xxxx", "somatic", _S2)),
        ("germline-no-ref-genome", lambda: (False, None, "record-xxxx", "germline", _G3)),
        ("germline-many-targets", lambda: (False, None, "record-xxxx", "germline", _G4)),
        ("somatic-many-others", lambda: (False, None, "record-xxxx", "somatic", _S3)),
        ("germline-many-others", lambda: (False, None, "record-xxxx", "germline", _G5)),
    ]
```

Hmm, "somatic-many-others" S3 has 20k targets, 3k others — not many others. Let me rename or adjust. Actually let me make S3 have more others. But I already have S1 with 10k others. Let me rename S3 to "somatic-named-first"? No.

Let me restructure to have diverse cases:

1. germline-default (G1): 25k targets, 5k others.
2. germline-named-mid (G2): 20k targets, 3k others, name matches index 12000.
3. somatic-default (S1): 20k targets, 10k others.
4. somatic-named-mid (S2): 15k targets, 5k others, name matches 7000.
5. germline-no-ref-genome (G3): 15k targets, 15k others, rich ref None.
6. germline-many-targets (G4): 30k targets, 2k others.
7. somatic-many-targets (S3): 20k targets, 3k others.
8. germline-many-others (G5): 15k targets, 20k others.

Good enough, 8 distinct.

Now, one concern: case 2's assay_name "germline_assay_12000" — need rich at target index 12000. Since we build targets in order and interleave others, the target order is by i. So target index 12000 corresponds to assay named "germline_assay_12000". Good.

But wait — in `_build`, we interleave: for i in range(max(n_target, n_other)): if i<n_target: append target i; if i<n_other: append other i. So the target assays appear in order 0,1,2,... Yes, target_assays preserved order. Good.

Now, the rich assay for G2 is at i=12000. Good.

Let me double check the somatic named case: assay_name="somatic_assay_7000", rich_idx=7000. In the loop `for ga in target_assays: if ga["name"] == assay_name: selected_assay_id = ga["uuid"]`. Good. Then later `for a in target_assays: if a["name"] == selected_assay_name and a["reference"]:` — finds rich. selected_ref_genome = "GRCh38" + "." + "v92" = "GRCh38.v92". Good.

Now, potential issue: in `_build`, `factory is _germline_assay` check. Fine.

Let me also verify the function's `get_assay_info` uses `rec_descriptor.assays`. Our _Descriptor has `.assays`. Good.

Now, about `sys.exit(0)` in list_assays branch — for checks only.

I think we're good. Let me also consider whether `err_exit` might raise something other than SystemExit that would be caught... no.

One more: the task says checks may raise. Good.

Let me also verify the function doesn't read module globals that need setting. It uses `err_exit`, `get_assay_info`, `sys`. No globals. Good.

Final code. Let me write it cleanly.

Actually, one thought on memory: 223k assays, each a dict with 3 entries plus 2 strings. Let me estimate more carefully with sys.getsizeof: dict with 3 items ~ 232 bytes. Strings: "germline_assay_25000" ~ 20 chars -> 69 bytes; "germline-00025000" ~ 17 chars -> 66 bytes. So ~370 bytes/assay. 223k * 370 = 82MB. Plus the others similar. OK ~85MB. Acceptable.

Could reduce by using shorter names but fine.

Actually wait, string interning: the model strings "genetic_variant" etc. are shared (same object referenced). Good.

Let me finalize.

I should double-check: does `random.Random(seed).choice` matter? It's deterministic. Good.

Write the final answer.