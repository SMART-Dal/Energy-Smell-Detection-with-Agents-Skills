Let me analyze this function.

`get_underlying_workflow(self, region, describe_output=None)`:
- Asserts describe_output is None or class == 'globalworkflow'
- If region is None raises DXError
- If region in self._workflows_by_region return cached
- If not describe_output: describe_output = self.describe()  — this calls the API! Network access.
- If region not in describe_output['regionalOptions'] raise
- underlying_workflow_id = describe_output['regionalOptions'][region]['workflow']
- self._workflow_desc_by_region = dxpy.DXWorkflow(underlying_workflow_id)  — creating DXWorkflow handler, no network? DXWorkflow.__init__ calls DXObject.__init__ and set_id... Actually let's check: DXWorkflow(underlying_workflow_id) — the __init__ of DXObject just sets _dxid. Hmm, does DXWorkflow.__init__ do any network? Typically DXObject.__init__ just sets fields. Set_id calls verify_string_dxid locally. So no network.

But the path requires describe_output passed in (to avoid describe() network call) OR the region is cached. If we pass describe_output, no network.

So we can run this function without network by passing describe_output with the proper structure.

But wait — does `self.describe()` go over network? Yes, it calls dxpy.api. We avoid by passing describe_output for all measured cases. But for caching path: region in self._workflows_by_region returns immediately. That's a valid case.

Note: describe_output can be any dict with 'class' == 'globalworkflow'. Actually assertion checks describe_output.get('class') == 'globalworkflow'. If describe_output is falsy... e.g. empty dict {} → `not describe_output` is True → calls describe() → network. So we must pass non-empty dicts with class globalworkflow.

So we can build realistic describe_output dicts.

Also, the region must be in describe_output['regionalOptions'].keys().

Now, what work does this function do? Honestly very little — a dict lookup and constructing DXWorkflow objects. This isn't heavy. But we need 8 cases that do "substantial and different work". Hmm.

The heaviest work here might be:
- `dxpy.DXWorkflow(underlying_workflow_id)` — validates the ID via verify_string_dxid. That's regex matching on a string.
- Actually `dxpy.DXWorkflow(underlying_workflow_id)` with a huge workflow ID? Not huge.

Hmm, the function is cheap. But the task requires 8 cases with 1ms-200ms. Perhaps the real cost can be in `describe()`? No, that's network.

Wait — but maybe the "work" is in the DXWorkflow construction and verify_string_dxid. Let's think about what's actually charged: only the call to get_underlying_workflow. If we pass a describe_output, work is trivial microsecond-level. Hmm.

But `self.describe()` — if we make the instance such that describe() returns a locally computed dict? No, DXObject.describe calls the API.

Hmm. Let's reconsider: maybe we can make describe() not go to network... The class DXGlobalWorkflow.describe calls dxpy.api.global_workflow_describe presumably. That requires network.

Alternatively, the caching path with a pre-populated `_workflows_by_region` returns immediately — trivial.

So the function is intrinsically cheap. The measurement would be dominated by call overhead. Still, we should make inputs that maximize work within the function. Possibly by making describe_output large (a big dict) — dict lookups on large dicts are O(1) though. Making regionalOptions have many regions — `region not in describe_output['regionalOptions'].keys()` is O(1).

Hmm, so it's basically constant. Well, so be it. We can still create varied inputs: different region counts, hit vs miss, cached vs uncached, describe_output provided vs not (but not = describe() → network, so always provided).

Wait, can we avoid network for the `describe()` path? What if `self._workflows_by_region` contains the region → returns before describe. That's the cache path.

For non-cached, we must pass describe_output. So all cases pass describe_output except cache-hit cases.

Actually, could we set `dxpy.api` to something? No, that's mocking — not allowed.

Could describe() hit a real local API? No network allowed.

So measured cases: all pass describe_output.

Now, generating work: the biggest cost might be constructing describe_output? No, that's in the thunk, not timed.

Hmm, we need to be honest. The function is cheap. The instructions say "One call should take roughly 1 ms to 200 ms on the original." We can't force that. But we can still provide inputs. The measured work is tiny; the measurement will be noisy but we should do our best.

Wait — maybe there's a trick: `assert` with a large describe_output? No.

Actually hold on. Perhaps `self.describe()` isn't necessarily network if... no.

Let's think about the underlying workflow id construction: verify_string_dxid uses regex. Not heavy.

OK. Another thought: The function returns a DXWorkflow object; constructing it calls DXWorkflow.__init__ which is DXObject.__init__ ... Actually let me recall dxpy DXWorkflow.__init__ signature: `def __init__(self, dxid=None, project=None, name=None, alias=None)` and it calls set_id. Cheap.

So overall, this is a lightweight function. We'll make do.

Could there be a way to make it heavier: large `describe_output` with many regions... `.keys()` view and `in` is hash-based. A dict with 1M entries: building it is expensive but that's setup. Lookup O(1). Validation of args: hmm, the harness "renders arguments before and after each call" — that's not part of the timed call though? It says arguments are rendered before and after each call to see whether it changed them. That's probably outside timing.

Hmm, but wait: `self._workflow_desc_by_region = dxpy.DXWorkflow(underlying_workflow_id)` sets an attribute. Fine.

Let's just build 8 diverse cases:
1. describe_output provided with one region, no cache → full path.
2. describe_output with many regions (~5000) → lookup among many.
3. describe_output with nested large regionalOptions per region (each with workflow, plus extra fields).
4. cache hit: pre-populate _workflows_by_region with the region.
5. cache miss but many cached regions (large cache dict) → still O(1), but fine.
6. describe_output where the region key is a long string.
7. different class of... hmm.
8. describe_output with 'class': 'globalworkflow' and various extra fields.

Also checks(): region None → raises DXError; describe_output={} → calls describe → network! Careful — checks may raise, but {} would trigger describe() → network. Avoid. Use describe_output with class != 'globalworkflow' → assertion error, that's fine (checks may raise). But assert may be disabled with -O; fine, either way it's just behavior comparison. Actually if assertions are off, it proceeds... then not describe_output? A dict with class 'workflow' is truthy, so it'd go on, region lookup, maybe raise DXError. Either way identical between original and modified presumably. But better to keep checks simple and safe.

checks:
- ("region-none", lambda: (instance, None, desc)) → raises DXError.
- ("class-mismatch", lambda: (instance, "aws:us-east-1", {"class": "workflow", "regionalOptions": {...}})) → AssertionError.
- ("region-not-enabled", lambda: (instance, "aws:eu-west-1", desc with only us-east-1)) → DXError.

But careful: for the region-not-enabled check, the instance gets no caching/mutation issues since it raises before. For class-mismatch, assertion.

Now about instances: each thunk should build a fresh instance (since _workflows_by_region and _workflow_desc_by_region get mutated). Actually the function mutates self only in the cache path? It sets self._workflow_desc_by_region and returns a new DXWorkflow; it does NOT add to self._workflows_by_region! Interesting — the code as shown doesn't populate the cache. So repeated calls with the same instance and same region do the same work. But to be safe, build fresh instance per thunk call (creating DXGlobalWorkflow is cheap) or reuse.

Hmm, but building the instance per thunk call is fine (setup not timed).

But note: DXGlobalWorkflow(dxid=...) requires a valid dxid? set_id calls verify_string_dxid which may raise for invalid IDs. We could pass a name instead? Also validated. Hmm — creating the instance might fail with fake IDs. Let's think: `DXGlobalWorkflow.__init__(dxid=None, name=None, alias=None)`: if dxid or name given → set_id. If neither → no ID set; self._dxid remains None? Then get_id() would raise DXError ("no ID"). In the non-cache path we call self.get_id() only when region not enabled (error message). In success path we don't call get_id. So an instance with no ID works for the success path!

But wait, DXObject.__init__(self) with no args — fine. Then get_underlying_workflow works if describe_output given and region present. get_id() is only called in the error branch.

So we can create `DXGlobalWorkflow()` with no ID — no validation issues.

But is that realistic? The repository creates global workflows with real IDs. However creating with a fake id would raise DXError in set_id (verify_string_dxid raises on invalid format). We could use a syntactically valid dxid like "globalworkflow-xxxx..." — format: `globalworkflow-<24 hex?>`. Actually dxids: class-XXXXXXXXXXXX... 24 chars base36? verify_string_dxid checks prefix and length. To be safe, avoid set_id entirely: DXGlobalWorkflow() with no args. Hmm but then `self._class` etc still fine.

Actually wait, does DXObject.__init__ require anything? `DXObject.__init__(self)` — fine.

Hmm, but maybe realistic: repository's own callers do `DXGlobalWorkflow(dxid=...)`. But since we can't validate a made-up id without network, and the function doesn't need the id, use no-id instance. Actually — could we use a valid-format id? Let's check verify_string_dxid: it likely does regex `^globalworkflow-[0-9a-zA-Z]{24}$`. Actually DNAnexus IDs are like "globalworkflow-xxxx" with 24 chars? Standard: class- + 24 characters base36 (some use 24). e.g. "workflow-000000000000000000000001". Hmm risky. Use no-id.

But careful: get_id() for the error path in the measured cases — if we have a "region not enabled" measured case (which raises), that's not allowed? "Every case must run to completion on the original function without raising." So measured cases must not raise. So no region-not-enabled case in cases().

Also the assert must pass. And region not None.

OK.

Now, is there real variation possible? Let's design describe_outputs with varying sizes.

Actually, one more idea to add work: the `assert` evaluates `describe_output.get('class')`. Fine.

Another thought: `dxpy.DXWorkflow(underlying_workflow_id)` — do we need dxpy imported? The module imports dxpy. Our test module needn't.

Now, does constructing DXWorkflow require the id to be valid? Yes! DXWorkflow.__init__(dxid=underlying_workflow_id) → set_id → verify_string_dxid which validates format. If invalid it raises DXError. So the underlying workflow IDs in our describe_output must be VALID dxids.

Let's check verify_string_dxid implementation. From dxpy/bindings/__init__.py:

```python
def verify_string_dxid(dxid, expected_classes):
    if isinstance(expected_classes, str):
        expected_classes = [expected_classes]
    m = re.match("^(" + "|".join(expected_classes) + ")-([0-9a-zA-Z]{24})$", dxid)
    if m is None:
        raise DXError(...)
    return m.group(2)
```

Something like that. Actually I recall the regex is `^([a-zA-Z0-9_]+)-([0-9a-zA-Z]{24})$` maybe with check on class. Let me be safe: use IDs like "workflow-000000000000000000000001" — 24 chars after the dash. Let me count: "000000000000000000000001" = 24 characters. Yes.

But is the class check enforced? verify_string_dxid(dxid, expected_classes) — for DXWorkflow, expected_classes = "workflow". If we give prefix "workflow" it matches. Good.

Also, does DXWorkflow.__init__ require project? `DXWorkflow(dxid=underlying_workflow_id)` — with no project, set_id(dxid) which calls verify_string_dxid and sets _dxid. Should be fine. Hmm, DXWorkflow.set_id might check project? Let me recall:

```python
class DXWorkflow(DXObject, DXExecutable):
    _class = "workflow"
    def __init__(self, dxid=None, project=None, name=None, alias=None):
        DXObject.__init__(self)
        if dxid is not None or name is not None:
            self.set_id(dxid, project, name, alias)
    def set_id(self, dxid=None, project=None, name=None, alias=None):
        if dxid is not None:
            verify_string_dxid(dxid, self._class)
            self._dxid = dxid
            ...
```

Something like that. Should be fine without project. Actually I recall in dxpy set_id:

```python
    def set_id(self, dxid, project=None):
        ...
        verify_string_dxid(dxid, self._class)
        self._dxid = dxid
        if project is not None:
            verify_string_dxid(project, "project")
        self._proj = project
```

OK.

Hmm, but also: does DXObject.__init__ do anything weird? No.

Risk: DXWorkflow.__init__ might make API calls. I'm fairly confident it doesn't.

Actually wait — there's a risk that DXWorkflow.__init__ with only dxid might attempt to describe? No, dxpy handlers are lazy.

Let's also double check `dxpy.DXWorkflow` exists in dxpy namespace — yes, imported in dxpy/__init__.py.

Now, the measured work is tiny (microseconds). The harness will keep 4 cases with most work. Fine.

Can we add real work legitimately? Hmm — the function's cost is dominated by... nothing. Unless the DXWorkflow construction does something. Let's just maximize: large describe_output dicts (makes `.get` and `in` on huge dicts still O(1), but the harness's argument rendering/serialization might matter — not timed though).

Hmm, wait. Actually maybe I'm wrong about describe_output being passed: for the cache path (`region in self._workflows_by_region`), we pre-populate `_workflows_by_region[region] = some DXWorkflow`. That returns immediately.

OK so what variation to include? Let's think about what a "modified version" of the function might differ on — e.g., reordering checks, caching, etc. Our cases should exercise: cache hit, cache miss with describe_output, region present/absent in regionalOptions (absent raises, excluded), different sizes of regionalOptions, different numbers of cached regions.

But since measured cases must not raise, the "region absent" is out. Hmm, unless... region present required.

Alright, the 8 cases:

1. "single-region" - 1 region, cache empty.
2. "many-regions" - 5000 regions in regionalOptions, cache empty.
3. "cache-hit" - region cached, describe_output large (unused).
4. "cache-hit-many" - region cached among 10000 cached entries.
5. "long-region-name" - region name is a very long string, present.
6. "rich-describe" - regionalOptions region value has many extra fields (workflow + big nested data).
7. "many-regions-and-cache-miss" - 20000 regions.
8. "fresh-instance each" vs reuse? Hmm.

Hmm, but the actual work difference is negligible. That's fine.

Actually, maybe I can make the DXWorkflow construction heavier: the `underlying_workflow_id` string. verify_string_dxid does regex match; a long string would make regex slower (24-char requirement means longer fails → raise, not allowed). So no.

Alternatively make `_workflows_by_region` a huge dict — `in` O(1).

OK, accept.

Wait, actually there might be more: `self.get_id()` is only called in error path.

Let me reconsider whether the harness counts the DXWorkflow object creation. Yes, that's part of the call.

Alright. One more consideration: "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over". The function sets self._workflow_desc_by_region — instance attribute, and we build a fresh instance per thunk call, so no carryover. Actually building fresh instance per thunk call: DXGlobalWorkflow() — cheap and no network. Good, and it avoids any accumulated state.

Hmm, but wait: does creating DXGlobalWorkflow() with no dxid leave self._dxid unset → later get_id() raises AttributeError? Only in error paths which we avoid in measured cases. For checks with region-not-enabled, get_id() is called in the error message. DXObject.__init__ sets self._dxid = None? Let's see: "Initialize _dxid and _proj to None values". So _dxid = None, get_id() returns None fine.

Actually DXObject.get_id() might be `return self._dxid`. Fine.

Let me now write checks:

```python
def checks():
    return [
        ("region-none", lambda: (DXGlobalWorkflow(), None, _DESC)),
        ("class-mismatch", lambda: (DXGlobalWorkflow(), "aws:us-east-1", {"class": "workflow", "regionalOptions": {}})),
        ("region-missing", lambda: (DXGlobalWorkflow(), "aws:eu-west-1", _DESC)),
    ]
```

Where _DESC has regionalOptions with only aws:us-east-1 (or the region we choose). Careful: "region-missing" raises DXError via get_id() format — get_id() returns None, format works.

Hmm, but for "class-mismatch": assert describe_output.get('class') == 'globalworkflow' → AssertionError. If Python runs with -O, asserts are skipped → then it goes on: region "aws:us-east-1" not in regionalOptions {} → raises DXError. Either way both original and modified behave the same, presumably. OK.

Now cases. Let's define a helper to build describe_output.

Realistic content: a global workflow describe output typically:

```python
{
  "id": "globalworkflow-xxxx",
  "class": "globalworkflow",
  "name": "MyWorkflow",
  "version": "1.0.0",
  "regionalOptions": {
     "aws:us-east-1": {"workflow": "workflow-000000000000000000000001"},
     "aws:eu-west-1": {"workflow": "workflow-000000000000000000000002"},
     ...
  }
}
```

The number of regions in real global workflows is like ~3-5. But we can make larger for stress.

Let's write:

```python
import random
from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow

_REGIONS = ["aws:us-east-1", "aws:eu-west-1", "aws:ap-southeast-2", "azure:westus", ...]
```

Let me define a generator for region names: f"{cloud}:{region}".

Helper:

```python
def _wfid(i):
    return "workflow-" + format(i % (36**24), "024d")  # digits only, valid chars
```

Actually base-36 not needed; use digits padded to 24. But format with "024d" gives at most 24 chars if i < 10^24. Fine.

Hmm, but must be unique-ish; doesn't matter.

Build describe:

```python
def _describe(n_regions, seed, extra_per_region=0, target_region_index=0):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        name = "aws:region-%06d" % i
        entry = {"workflow": _wfid(i+1)}
        for j in range(extra_per_region):
            entry["extra_%d" % j] = rng.randrange(10**9)
        regions[name] = entry
    return {"class": "globalworkflow",
            "id": "globalworkflow-000000000000000000000001",
            "name": "gwf",
            "regionalOptions": regions}
```

Hmm but for the extra fields, `describe_output['regionalOptions'][region]['workflow']` is read; extras just bloat.

Building 20000 regions with 20 extra fields = 400k values... "keep each input's data under about 1,000,000 values" — ok. But argument rendering might be slow. Keep moderate: maybe 20000 regions with no extras is fine (each region dict has 1 key). Values count ~ 20k*3 = 60k. Fine.

Actually the rendering of arguments before/after each call — with a huge describe_output, this could be slow per call (not timed but total runtime). The harness presumably renders. Hmm, "Its arguments are rendered before and after each call" — that is outside the timing but repeated many times could be slow. Let's keep describe_outputs moderate in size (a few thousand entries).

Hmm honestly, since the function's work is O(1), the "most work" cases will be noise. Let's not overthink; make reasonable varied cases.

Let me reconsider: is there anything in the function that could scale with input? `if region not in describe_output['regionalOptions'].keys()` — dict. No.

Therefore all cases are essentially equally fast. Fine.

But hold on — could there be a legitimate way to make the function do more work? What about the cached path returning... no.

Another thought: maybe the harness's "work" measure includes the fact that a big describe_output must be... no, not timed.

OK, let's produce 8 cases anyway.

Now, do we pass describe_output or rely on cache? Both.

Important: for the "cache-hit" case, we set instance._workflows_by_region[region] = a DXWorkflow object. That's setting an attribute of an object we construct — allowed (data). The function returns it.

Let's write:

```python
def _instance_with_cache(regions, seed):
    gwf = DXGlobalWorkflow()
    for r in regions:
        gwf._workflows_by_region[r] = _make_wf(...)
    return gwf
```

Hmm — is setting private attributes OK? "Setting data (a module's configuration, an object's fields) to build an input is fine." Yes.

But is it realistic? The repo populates the cache... Actually looking at the shown code, get_underlying_workflow never populates _workflows_by_region! Odd (maybe the real code does elsewhere). Anyway, cache hit is a legitimate path in the function.

Now let's produce the cases:

```python
def cases():
    return [
        ("typical-single-region", lambda: (DXGlobalWorkflow(), "aws:us-east-1", _desc_single(0))),
        ("typical-three-regions", lambda: (DXGlobalWorkflow(), "aws:eu-west-1", _desc_multi(3, 0))),
        ("many-regions-5k", lambda: (DXGlobalWorkflow(), "aws:region-004999", _desc_multi(5000, 1))),
        ("many-regions-20k-target-middle", lambda: (DXGlobalWorkflow(), "aws:region-010000", _desc_multi(20000, 2))),
        ("rich-region-entry", lambda: (DXGlobalWorkflow(), "aws:region-000010", _desc_rich(200, 3))),
        ("cache-hit", lambda: (gwf_cached, "aws:us-east-1", None)),
        ...
    ]
```

Careful: for cache-hit with describe_output=None: assert passes (None). Then region in cache → return. Good.

Hmm, but for cache-hit, if the region is NOT in cache, describe() would be called → network. So must guarantee hit.

Let's also make a case with describe_output being huge but region present (rich).

Also maybe a case where the target region is the last key (order doesn't matter).

Let me finalize data:

- Case 1: single region, target that region.
- Case 2: 3 regions (realistic), target second.
- Case 3: 5000 regions, target last.
- Case 4: 20000 regions, target in middle.
- Case 5: 500 regions but each entry has 20 extra fields (bigger values).
- Case 6: cache hit with empty describe (None) — instance pre-cached with 1 entry.
- Case 7: cache hit with a big cache (10000 entries) and big describe_output passed anyway (unused... wait, cache check is before describe use, so describe_output passed is ignored, but the arg is rendered).
- Case 8: cache miss with a big cache (10000 entries) not containing the region, plus describe_output with many regions.

Hmm, case 8: cache has 10000 entries, region not in it → falls through with describe_output. Fine.

Each thunk builds a fresh instance. For cache cases, build instance and populate cache in the thunk (setup not timed, cheap-ish but 10000 entries per call... repeated many times could be slow for setup). Better: build cache dicts once at module level and copy in thunk: `gwf = DXGlobalWorkflow(); gwf._workflows_by_region = dict(_CACHE_10K)`. Copy of 10k dict is fast.

Even better: since the function doesn't mutate _workflows_by_region, we could reuse a single instance across calls. But to be safe with any state, using a fresh copy is fine. Copy is cheap.

For the cached value: a DXWorkflow instance. We can reuse the same DXWorkflow object for all cache entries; doesn't matter.

Let's write module-level:

```python
import random
from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow

_WORKFLOW_IDS = ...
```

Need to build DXWorkflow objects — requires dxpy.DXWorkflow. Import dxpy? The instructions say import repository modules exactly as shown: `from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow`. We can also `import dxpy`. It's the repository's own package. Should be fine — but "Use only the standard library, the repository itself and packages the repository already imports." dxpy is the repo itself. OK.

Actually simpler: to build the cached DXWorkflow objects we don't even need dxpy.DXWorkflow — any object works as the cache value since the function just returns it. But realism... The harness compares outputs; a DXWorkflow object vs another — comparison is by identity/repr? Hmm! "The function's output is compared in full after every input". If outputs are DXWorkflow objects, they must compare equal between original and modified. Since the harness calls the function with the same args and compares outputs, objects created fresh may not be `==` unless __eq__ defined. Hmm, that's the harness's concern; both original and modified create new objects identically.

Hmm, but "compared in full" — maybe they serialize via repr. DXWorkflow repr would be like `<dxpy.bindings.dxworkflow.DXWorkflow object at 0x...>` — addresses differ! That would make every comparison fail. Risky!

Hmm. Well, the task says outputs are compared in full. If the output is an object without __eq__, equality fails by identity. But the harness presumably handles that—maybe it uses repr or a deep comparison. Actually, many such harnesses compare `repr()` or a pickle. Hmm.

DXObject might define __eq__? I don't think so.

But we have no choice: the function returns a DXWorkflow. Both original and modified return DXWorkflow. The harness designers know the function's return type; they'd have built comparison that works. Actually maybe the modified version returns the same and the harness compares... whatever. Not our problem. Though—hmm, could this make all cases fail? The harness might compare using `==` which for two distinct DXWorkflow instances is False → the case would be considered "output mismatch". That would be bad but it's the nature of the function; every input returns a new object.

Hmm, wait. Actually, would it? Let me consider: maybe DXObject defines __eq__ comparing _dxid. Not sure. Let's not worry.

But we could reduce risk: caching cases return a cached object (same object identity across calls) → identity comparison would succeed between original and modified if both return the same cached object... but each run constructs its own instance? The thunk builds a new instance each call, so the cached object is new each call. Hmm.

Whatever.

Hmm, actually let me reconsider: maybe compare via repr is common. Fine.

Let's just proceed.

Now, about "describe_output" argument when it is None and cache miss → network. Avoid in cases.

Let me now also double check: assert passes for our dicts (class == 'globalworkflow'). Yes.

Region strings: use realistic region names for small cases, and generated ones for big.

Let me write the code.

```python
import random

from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow
import dxpy


def _wfid(n):
    return "workflow-" + ("%024d" % (n % 10**24))


def _mk_entry(rng, extras=0):
    entry = {"workflow": _wfid(rng.randrange(10**9))}
    for j in range(extras):
        entry["field_%d" % j] = {
            "name": "stage-%d" % j,
            "value": rng.randrange(10**12),
            "nested": [[rng.random() for _ in range(3)] for _ in range(2)],
        }
    return entry
```

Hmm, extras generate a lot. Let's keep it simpler.

Let me write clean helper:

```python
def _describe(n_regions, seed, extras=0):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        region = "aws:region-%06d" % i
        entry = {"workflow": _wfid(i + 1)}
        for j in range(extras):
            entry["extra_%d" % j] = rng.getrandbits(32)
        regions[region] = entry
    return {
        "class": "globalworkflow",
        "id": "globalworkflow-000000000000000000000001",
        "name": "global-workflow-%d" % seed,
        "version": "1.0.0",
        "regionalOptions": regions,
        "project": "project-000000000000000000000001",
        "created": 1600000000000,
    }
```

Now cases.

Case list:

1. ("single-region", lambda: (DXGlobalWorkflow(), "aws:us-east-1", _SINGLE))
   where _SINGLE = {"class": "globalworkflow", "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(1)}}}

2. ("three-regions", lambda: (DXGlobalWorkflow(), "aws:eu-west-1", _THREE))  — build at module level.

3. ("many-regions-5k", lambda: (DXGlobalWorkflow(), "aws:region-004999", _BIG5K))

4. ("many-regions-20k", lambda: (DXGlobalWorkflow(), "aws:region-010000", _BIG20K))

5. ("rich-entries-500", lambda: (DXGlobalWorkflow(), "aws:region-000250", _RICH))

6. ("cache-hit-small", lambda: _cache_thunk(1))

7. ("cache-hit-10k-desc-large", lambda: _cache_thunk(10000))

8. ("cache-miss-10k", ...) — instance with 10k cached regions not containing target, plus describe_output with 5k regions containing target.

For 6-8, need helper functions that build instance and set cache.

```python
_CACHE_10K = {("aws:region-%06d" % i): _wfid(i + 5) for i in range(10000)}
```

But the cache values should be DXWorkflow objects? The function returns them directly as output. If output is a string, easier to compare. Hmm, but realism: cache should hold DXWorkflow handlers. For output comparison, a DXWorkflow... Let's use DXWorkflow objects for realism, built once.

```python
_CACHED_HANDLERS = {r: dxpy.DXWorkflow(_wfid(i+5)) for i, r in enumerate(...)}
```

Hmm, building 10k DXWorkflow objects at module load — each does a regex verify. Fine (~fast).

Actually, careful: `dxpy.DXWorkflow(_wfid(i+5))` — positional arg is dxid. Good.

Let me define:

```python
def _cache_entries(n, seed):
    rng = random.Random(seed)
    return {("aws:region-%06d" % i): dxpy.DXWorkflow(_wfid(i + 1000)) for i in range(n)}
```

Wait — but does DXWorkflow.__init__ with an id do any API call? I'm confident not. But risk... Let me think again about dxpy.bindings.dxworkflow.DXWorkflow:

```python
class DXWorkflow(DXObject, DXExecutable):
    _class = "workflow"

    def __init__(self, dxid=None, project=None, name=None, alias=None):
        DXObject.__init__(self)
        if dxid is not None or name is not None:
            self.set_id(dxid, project, name, alias)

    def set_id(self, dxid=None, project=None, name=None, alias=None):
        if dxid is not None:
            self.set_id? 
```

Actually I recall:

```python
    def set_id(self, dxid, project=None):
        if dxid is not None:
            verify_string_dxid(dxid, self._class)
            self._dxid = dxid
        ...
```

Hmm, also `alias` handling. Fine.

No API calls. Good.

Now, one concern: creating 10k DXWorkflow objects at import is fine.

Now the thunks for cache cases:

```python
def _cached_thunk(cache, region, describe_output):
    def thunk():
        gwf = DXGlobalWorkflow()
        gwf._workflows_by_region = cache
        return (gwf, region, describe_output)
    return thunk
```

Since the function doesn't mutate _workflows_by_region, sharing the same dict is fine and cheap. But if a modified version mutated it, we'd... the instruction says build a copy if the function changes it. It doesn't change it here. But to be safe about "same work on every call", sharing a dict that might get mutated by a modified version could cause divergence — but the modified version is what we're testing against; presumably same semantics. I'll use `dict(cache)` copy for safety? Copy of 10k dict is fast (~1ms). Hmm, that's setup, not timed. I'll copy.

Actually simpler: keep it shared but the function never writes. I'll use a shallow copy to be safe.

Now define the case list with lambdas.

Careful about the requirement "distinct labels".

Let me also think about whether to include a case where `_workflows_by_region` is empty but describe_output is None... no (network).

Let me write the final code.

```python
import random

import dxpy
from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow


def _wfid(n):
    return "workflow-" + ("%024d" % (n % 10 ** 24))


def _describe(n_regions, seed, extras=0, target="middle"):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        region = "aws:region-%06d" % i
        entry = {"workflow": _wfid(i + 1)}
        for j in range(extras):
            entry["meta_%d" % j] = rng.randrange(10 ** 9)
        regions[region] = entry
    return {
        "class": "globalworkflow",
        "id": "globalworkflow-000000000000000000000001",
        "name": "global-workflow-%d" % seed,
        "version": "1.0.0",
        "billTo": "org-000000000000000000000001",
        "regionalOptions": regions,
    }
```

Hmm, "billTo" field may not be realistic for globalworkflow; irrelevant.

Module-level data:

```python
_SINGLE = {
    "class": "globalworkflow",
    "id": "globalworkflow-000000000000000000000001",
    "name": "simple-gwf",
    "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(11)}},
}

_THREE = _describe_with_named(3)
```

Let's just use explicit realistic regions for small cases:

```python
_REAL_REGIONS = ["aws:us-east-1", "aws:eu-west-1", "aws:ap-southeast-2", "azure:westus", "azure:westeurope"]
```

_BUILD small describe:
```python
def _describe_regions(names, seed, extras=0):
    rng = random.Random(seed)
    regions = {}
    for i, name in enumerate(names):
        entry = {"workflow": _wfid(seed * 100 + i + 1)}
        for j in range(extras):
            entry["meta_%d" % j] = rng.randrange(10 ** 9)
        regions[name] = entry
    return {"class": "globalworkflow", ...}
```

OK let's just write it.

Now the case thunks. Every thunk: `lambda: (DXGlobalWorkflow(), region, describe_output)`.

For cache thunks: build instance and set cache.

Let me write:

```python
_CACHE_SMALL = {r: dxpy.DXWorkflow(_wfid(i + 500)) for i, r in enumerate(_REAL_REGIONS)}
_CACHE_10K = {("aws:region-%06d" % i): dxpy.DXWorkflow(_wfid(i + 5000)) for i in range(10000)}
```

Hmm, building 10k DXWorkflow objects: each calls verify_string_dxid regex on a 33-char string — fast (~microseconds). 10k → ~50ms. Fine.

Thunk helper:

```python
def _cached_thunk(cache, region, describe_output=None):
    def _t():
        gwf = DXGlobalWorkflow()
        gwf._workflows_by_region = dict(cache)
        return (gwf, region, describe_output)
    return _t
```

Now cases():

```python
def cases():
    return [
        ("single-region", lambda: (DXGlobalWorkflow(), "aws:us-east-1", _SINGLE)),
        ("three-regions", lambda: (DXGlobalWorkflow(), "aws:eu-west-1", _THREE)),
        ("five-thousand-regions", lambda: (DXGlobalWorkflow(), "aws:region-004999", _BIG_5K)),
        ("twenty-thousand-regions", lambda: (DXGlobalWorkflow(), "aws:region-010000", _BIG_20K)),
        ("rich-region-entries", lambda: (DXGlobalWorkflow(), "aws:region-000250", _RICH)),
        ("cache-hit-small", _cached_thunk(_CACHE_SMALL, "aws:ap-southeast-2")),
        ("cache-hit-large", _cached_thunk(_CACHE_10K, "aws:region-005000", _BIG_5K)),
        ("cache-miss-large", _cached_thunk(_CACHE_10K, "aws:not-cached-1", _BIG_5K)),
    ]
```

Wait "cache-miss-large": region "aws:not-cached-1" must be in _BIG_5K's regionalOptions, else raises. _BIG_5K regions are "aws:region-%06d" 0..4999. So use "aws:region-004999" as the target for the miss case (not in the 10k cache which has i+5000 → regions 0..9999 → wait _CACHE_10K covers aws:region-000000..009999). Oops — then "aws:region-004999" IS in the cache. Let me make the cache regions use a different prefix, e.g. "aws:cached-%06d".

Fix: `_CACHE_10K = {("aws:cached-%06d" % i): ...}`. Then target "aws:region-004999" is a miss.

Good.

Now, checks:

```python
def checks():
    return [
        ("region-none", lambda: (DXGlobalWorkflow(), None, _SINGLE)),
        ("class-mismatch", lambda: (DXGlobalWorkflow(), "aws:us-east-1", {"class": "workflow", "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(1)}}})),
        ("region-not-in-options", lambda: (DXGlobalWorkflow(), "aws:sa-east-1", _THREE)),
    ]
```

Check "region-not-in-options": _THREE contains aws:us-east-1, aws:eu-west-1, aws:ap-southeast-2 — sa-east-1 not present → DXError. Good. get_id() returns None → format string works.

Hmm, but if `DXObject.__init__` doesn't set _dxid... it does per docstring "Initialize _dxid and _proj to None values". OK.

Careful with "region-none": assert passes (describe_output _SINGLE class globalworkflow), then region is None → DXError. Good.

"class-mismatch": assert fails → AssertionError (unless -O). Fine either way, deterministic.

Should checks have exactly 2-3 cases. 3 is fine.

Now, one more thought about whether create instance with no id might break in the measured path: the success path returns before get_id(). Yes.

Now think about the harness discarding the 4 least-work cases. Since work is ~equal, whatever.

Let me reconsider the "20k regions" case: describe_output with 20000 entries → 20000 dicts each with 1 key. Argument rendering of 20k dicts before and after each call could be slow if the harness does repr/serialize. Hmm, that could be minutes if repeated many times. Risky. Let's scale down: 5000 and 8000 maybe. Actually the arg rendering is likely a deep-copy or repr check to detect mutation. With 20k small dicts, repr ~1MB — fast enough (ms). Fine.

But total data: keep under 100MB. 20k regions dict: ~20k*200 bytes = 4MB. Fine.

Value count under 1,000,000: 20k regions * (1 key + entry with 2 values) ≈ 60k. Fine.

For the "rich" case: 500 regions × 20 extra fields = 10k values. Fine.

Let me finalize the sizes:
- _SINGLE: 1 region
- _THREE: 3 regions
- _BIG_5K: 5000 regions
- _BIG_20K: 20000 regions → maybe reduce to 15000. Keep 20000, fine.
- _RICH: 800 regions, 12 extras each.

Now, the target region for _RICH: "aws:region-000400".

Let's write `_describe(n, seed, extras, prefix="aws:region")`:

```python
def _gen_describe(n_regions, seed, extras=0):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        region = "aws:region-%06d" % i
        entry = {"workflow": _wfid(seed * 100000 + i + 1)}
        for j in range(extras):
            entry["meta_%d" % j] = rng.getrandbits(40)
        regions[region] = entry
    return {
        "class": "globalworkflow",
        "id": "globalworkflow-%024d" % (seed + 1),
        "name": "global-workflow-%d" % seed,
        "version": "1.0.0",
        "regionalOptions": regions,
    }
```

Careful: "globalworkflow-%024d" % seed gives 24 digits. Good — but wait, does anything verify that id? No, describe_output isn't validated. Fine.

_wfid: "%024d" % n, with n < 10^24. seed*100000+i+1 for seed=5 → 500001. Fine.

Now assemble.

Also need `_REAL_REGIONS` for the cached small case.

Let me write the final code carefully.

```python
import random

import dxpy
from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow


def _wfid(n):
    return "workflow-" + ("%024d" % (n % (10 ** 24)))


def _gen_describe(n_regions, seed, extras=0):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        entry = {"workflow": _wfid(seed * 100000 + i + 1)}
        for j in range(extras):
            entry["meta_%d" % j] = rng.getrandbits(40)
        regions["aws:region-%06d" % i] = entry
    return {
        "class": "globalworkflow",
        "id": "globalworkflow-0000000000000000000000%02d" % (seed % 100,),
        ...
    }
```

Hmm the id format: just use "globalworkflow-000000000000000000000001". Fine, simpler.

Let me just write fixed constant id strings.

Final:

```python
import random

import dxpy
from dxpy.bindings.dxglobalworkflow import DXGlobalWorkflow

_GWF_ID = "globalworkflow-000000000000000000000001"


def _wfid(n):
    return "workflow-" + ("%024d" % (int(n) % (10 ** 24)))


def _gen_describe(n_regions, seed, extras=0):
    rng = random.Random(seed)
    regions = {}
    for i in range(n_regions):
        entry = {"workflow": _wfid(seed * 100000 + i + 1)}
        for j in range(extras):
            entry["meta_%d" % j] = rng.getrandbits(40)
        regions["aws:region-%06d" % i] = entry
    return {
        "class": "globalworkflow",
        "id": _GWF_ID,
        "name": "global-workflow-%d" % seed,
        "version": "1.0.0",
        "regionalOptions": regions,
    }


_SINGLE = {
    "class": "globalworkflow",
    "id": _GWF_ID,
    "name": "simple-global-workflow",
    "version": "1.0.0",
    "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(11)}},
}

_THREE = _gen_describe(3, 1)
_BIG_5K = _gen_describe(5000, 2)
_BIG_20K = _gen_describe(20000, 3)
_RICH = _gen_describe(800, 4, extras=12)

_CACHE_SMALL = {
    "aws:us-east-1": dxpy.DXWorkflow(_wfid(1001)),
    "aws:eu-west-1": dxpy.DXWorkflow(_wfid(1002)),
    "aws:ap-southeast-2": dxpy.DXWorkflow(_wfid(1003)),
}
_CACHE_10K = {
    "aws:cached-%06d" % i: dxpy.DXWorkflow(_wfid(100000 + i))
    for i in range(10000)
}


def _cached_thunk(cache, region, describe_output=None):
    def _thunk():
        gwf = DXGlobalWorkflow()
        gwf._workflows_by_region = dict(cache)
        return (gwf, region, describe_output)
    return _thunk


def _plain_thunk(region, describe_output):
    return lambda: (DXGlobalWorkflow(), region, describe_output)
```

Hmm wait, `_THREE` generated by _gen_describe uses "aws:region-000000" style names, not realistic but fine.

Actually maybe make small cases realistic-looking. Not necessary.

Targets:
- _THREE target: "aws:region-000001"
- _BIG_5K target: "aws:region-004999"
- _BIG_20K target: "aws:region-010000"
- _RICH target: "aws:region-000400"

cases():

```python
def cases():
    return [
        ("single-region", _plain_thunk("aws:us-east-1", _SINGLE)),
        ("three-regions", _plain_thunk("aws:region-000001", _THREE)),
        ("five-thousand-regions", _plain_thunk("aws:region-004999", _BIG_5K)),
        ("twenty-thousand-regions", _plain_thunk("aws:region-010000", _BIG_20K)),
        ("rich-region-entries", _plain_thunk("aws:region-000400", _RICH)),
        ("cache-hit-small", _cached_thunk(_CACHE_SMALL, "aws:ap-southeast-2")),
        ("cache-hit-large-cache", _cached_thunk(_CACHE_10K, "aws:cached-005000", _BIG_5K)),
        ("cache-miss-large-cache", _cached_thunk(_CACHE_10K, "aws:region-004999", _BIG_5K)),
    ]
```

Wait, "cache-hit-large-cache" passes _BIG_5K as describe_output but the cache hit returns before using it; fine (and exercises the early-return path with a big arg).

Note: for "cache-miss-large-cache", region "aws:region-004999" is in _BIG_5K → succeeds and constructs DXWorkflow. Good.

Distinct labels: yes.

checks():

```python
def checks():
    return [
        ("region-none", lambda: (DXGlobalWorkflow(), None, _SINGLE)),
        ("class-mismatch", lambda: (DXGlobalWorkflow(), "aws:us-east-1",
                                    {"class": "workflow",
                                     "regionalOptions": {"aws:us-east-1": {"workflow": _wfid(1)}}})),
        ("region-not-enabled", lambda: (DXGlobalWorkflow(), "aws:sa-east-1", _THREE)),
    ]
```

Good.

One concern: `dxpy.DXWorkflow(_wfid(...))` at module import — if DXWorkflow.__init__ requires project for something... I'm fairly confident. Also verify_string_dxid regex must accept "workflow-" + 24 digits. Yes.

Another concern: does `verify_string_dxid` require exactly 24 chars base36? Digits qualify.

Potential issue: The regex might be `^([a-zA-Z0-9_\-\.]+)-([0-9a-zA-Z]{24})$` or might check the class against allowed list. "workflow" is the right class for DXWorkflow.

Now, is there a risk that DXWorkflow.__init__ actually calls the API to describe? No.

One more: the harness may compare outputs; DXWorkflow instances — if equality fails, all cases fail regardless. But maybe DXObject defines __eq__? Let me think... dxpy DXObject:

```python
class DXObject(object):
    def __init__(self, dxid=None, project=None):
        self._dxid = None
        self._proj = None
        ...
```

I don't recall __eq__. Actually, DXObject might define `__str__` and `__repr__`? Hmm, I recall:

```python
    def __str__(self):
        ...
    def __repr__(self):
        return self.__str__()
```

Not sure. The comparison harness likely uses a robust compare (e.g., comparing reprs or pickles) — many of these benchmark harnesses compare `repr` output. If they compare repr and repr contains id(...), it fails. Not our call.

Given the function inherently returns fresh objects, no input can avoid it. So proceed.

Also note: for the cache cases, the returned object is a DXWorkflow from our cache — the thunk copies the dict but values are the same objects each call. Still new-ish.

Fine. Write it out.

One more: should I use `describe_output.get('class')`... our dicts have class 'globalworkflow'. Good.

Let me also double-check the arg-count: `get_underlying_workflow(self, region, describe_output=None)`. Thunks return (instance, region, describe_output) — positional describe_output. Fine; the docstring examples use keyword but positional is fine.

Write the final answer.