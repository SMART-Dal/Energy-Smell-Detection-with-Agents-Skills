Let me understand the function. `override_cluster_spec(self, srd)` where `self` is a `SystemRequirementsDict` (app doc's systemRequirements) and `srd` is another `SystemRequirementsDict` (requested instance counts).

The function deep-copies `self.entrypoints`, filters, merges, returns a new `SystemRequirementsDict`.

The main workload: deep copies and dict operations. To make it substantial, we want large entrypoints dicts with many entrypoints, each having clusterSpec with many fields.

But note: the returned value is compared in full. It returns a SystemRequirementsDict object... hmm, how is it compared? "The function's output is compared in full after every input, so keep what it returns under about 100 000 values." The return is a SystemRequirementsDict. Comparison probably uses repr or equality. Anyway, keep sizes moderate.

Also "its arguments are rendered before and after each call to see whether it changed them". The function deep-copies self.entrypoints so it doesn't mutate self. But `merged_cluster_spec[entry_pt]["clusterSpec"].update(...)` mutates the deep copy, not the original. Good. So args are unchanged. But rendering args means converting to something — probably repr. So the entrypoints dicts should be under 1M values.

Let's design cases:

- self.entrypoints: dict of entrypoint_name -> {"clusterSpec": {...many fields...}} or {"instanceType": ...} (no clusterSpec).
- srd.entrypoints: dict of entrypoint_name -> {"clusterSpec": {"initialInstanceCount": N}}.

Paths:
1. Wildcard "*" requested, many app entrypoints with clusterSpec -> all merged, wildcard used.
2. Named entrypoints requested matching app entrypoints.
3. Mixed named + wildcard.
4. App has "*" clusterSpec, srd has named entrypoints not in app -> they get copied from app's "*".
5. App entrypoints without clusterSpec (filtered out).
6. srd with entrypoints not in app and app has no "*" -> nothing added.
7. Large number of entrypoints to stress deep copy.
8. Large clusterSpec dicts with many fields.

Let me make the field-heavy clusterSpec: each clusterSpec has e.g. 200 keys, and many entrypoints.

Let's be careful: `srd.entrypoints.get(entry_pt, srd.entrypoints.get("*"))["clusterSpec"]` — if srd has entry_pt key or "*" key it must have "clusterSpec". Since we only include entrypoints in merged if k in srd.entrypoints or "*" in srd.entrypoints, the get is safe as long as each srd entrypoint has "clusterSpec". Fine.

Also, in the last loop, for entry_pt in srd.entrypoints, if entry_pt not in merged and "*" in self.entrypoints and "clusterSpec" in self.entrypoints["*"], then req["clusterSpec"] is accessed — req must have "clusterSpec". Fine.

Now to make work substantial: deep copy of large nested structure. Let's target ~1ms-200ms. A deep copy of a dict with, say, 500 entrypoints each with 200 fields = 100k values — deepcopy might take ~50-100ms. Good.

Let's design a helper to build an app entrypoints dict.

```python
import random
import copy
from dxpy.system_requirements import SystemRequirementsDict

def _cluster_spec(n_fields, seed, base=0):
    rng = random.Random(seed)
    d = {"initialInstanceCount": rng.randint(1, 100),
         "type": "spark",
         "version": "2.4.0"}
    for j in range(n_fields):
        d[f"field{j}"] = f"value{rng.randint(0, 10**6)}"
    return d

def _app_entrypoints(names, n_fields, seed, wildcard=False):
    rng = random.Random(seed)
    eps = {}
    for i, name in enumerate(names):
        ep = {}
        if rng.random() < 0.8:
            ep["clusterSpec"] = _cluster_spec(n_fields, seed * 1000 + i)
        # else no clusterSpec -> filtered
        if rng.random() < 0.5:
            ep["instanceType"] = f"mem{rng.randint(1,4)}_ssd1_x{rng.randint(2,8)}"
        eps[name] = ep
    if wildcard:
        eps["*"] = {"clusterSpec": _cluster_spec(n_fields, seed * 9999)}
    return eps

def _srd_entrypoints(mapping):
    return {k: {"clusterSpec": {"initialInstanceCount": v}} for k, v in mapping.items()}
```

Wait, srd.entrypoints values used in the last loop: `req["clusterSpec"]` — that's the dict with initialInstanceCount. Fine.

Now cases. Each thunk builds new SystemRequirementsDict instances (because the function deep copies, so reusing the same instance across calls is fine — it doesn't mutate). Actually since the function doesn't mutate self or srd, we can reuse the same instances across all calls. But the thunk runs before each timing... wait, "Thunks run before the timing starts; only the call of the function is timed." Each measured iteration calls the thunk then times the call. So the thunk should be cheap. Building SystemRequirementsDict deep-copies entrypoints in __init__ — that's a deepcopy of large data, potentially expensive. Better to build the instances at module level once, and have the thunk return them.

But careful: does the function mutate srd? No. Does it mutate self? No, it deep-copies. So reusing instances is safe. Good.

So module-level build instances.

Let me define cases:

1. "wildcard-many": app with 400 entrypoints (80% with clusterSpec), srd = {"*": 5}. All app entrypoints with clusterSpec get merged.

Wait with srd = {"*": 5}: the filter keeps k in srd.entrypoints or "*" in srd.entrypoints -> all kept. Then update each with srd["*"]["clusterSpec"] = {"initialInstanceCount": 5}. Then last loop: "*" not in merged_cluster_spec (unless app has "*"), "*" in self.entrypoints? If app has no "*", skip. So "*" requested but not added unless app has "*". Actually if app has "*" with clusterSpec, then "*" is in merged_cluster_spec already.

2. "named-subset": app with 400 entrypoints, srd with 200 named entrypoints matching a subset.

3. "mixed": srd with 200 named + "*".

4. "fallback-star": app with only "*" clusterSpec and many fields, srd with 300 named entrypoints not in app -> each gets deep copy of app's "*" clusterSpec then update. This stresses the last loop with deepcopy per entry.

5. "no-clusterspec": app with many entrypoints without clusterSpec -> filtered out early; minimal work. Hmm, that's low work. But we need diversity. Maybe combine: app has some without clusterSpec.

6. "field-heavy": few entrypoints but each clusterSpec has 5000 fields, srd wildcard -> deepcopy heavy.

7. "srd-missing-app": srd has entrypoints not in app and app has no "*" -> last loop no-op.

8. "no-wildcard-named-miss": app has named entrypoints, srd has named ones not matching -> merged becomes empty.

Let me ensure each case runs without error.

Case 8: app = {"main": {"clusterSpec": ...}, "other": {...}}, srd = {"unknown1": {...}, "unknown2": {...}}. Filter: k in srd.entrypoints? "main" not in srd -> removed. "*" in srd? no. So merged = {}. Last loop: entry_pt "unknown1" not in merged, "*" in self.entrypoints? no -> skip. Returns empty SRD. Fine.

Case 4: app = {"*": {"clusterSpec": heavy}}. srd = {"fn0": 3, ... "fn299": 3}. Filter keeps app entries if k in srd or "*" in srd: "*" in srd? no. So "*" removed. merged = {}. Then last loop: each fn not in merged, "*" in self.entrypoints and "clusterSpec" in self.entrypoints["*"] -> true, so merged[fn] = {"clusterSpec": deepcopy(app["*"]["clusterSpec"])}, update with req["clusterSpec"]. So 300 deep copies of the heavy clusterSpec. Good heavy workload.

Now sizes: keep under limits. Return value for case 1: 400 entrypoints each with clusterSpec of n_fields. If n_fields=200, that's 80k values — under 100k. Hmm plus. Let's be careful. Actually "under about 100 000 values" for output. Let's keep total returned values moderate.

Let me plan sizes carefully.

Case 1: 400 app entrypoints, ~80% with clusterSpec, n_fields=50. Returned ~320 entrypoints * (50 fields + few) ≈ 16k values. Deepcopy of self.entrypoints: 400 * 50 ≈ 20k values. Fine. Time maybe a few ms. Might be too fast. Let's increase to make it 1ms+.

Deepcopy of 20k small values maybe ~10ms. Ok.

Actually let's think about the "keep the 4 that do the most work" - we just provide 8 diverse ones.

Let me aim for each case ~5-100ms.

Let me build:

- Case A "wildcard-all": app 500 eps, 90% with clusterSpec of 100 fields; srd {"*": 5}. Work: deepcopy 500*100=50k values, filter, update 450 clusterSpecs. Output ~450*100=45k values. Good.

- Case B "named-subset": app 500 eps with clusterSpec 100 fields; srd 250 named matching. Filter to 250. Deepcopy full 500 first (deepcopy of self.entrypoints is full regardless!). Note the deepcopy always copies all of self.entrypoints. So deepcopy dominates. Good.

- Case C "mixed-named-wildcard": app 400 eps incl "*" with clusterSpec; srd 200 named + "*".

- Case D "fallback-star": app {"*": clusterSpec with 500 fields}, srd 400 named not in app. Last loop does 400 deepcopies of 500-field spec = 200k value copies. Output 400*500=200k values — exceeds 100k. Reduce: 100 named, 300 fields -> 30k. Hmm want more work. Actually work here is 100 deepcopies of 300 fields = 30k. Output 30k. Maybe 200 named * 200 fields = 40k output. deepcopy work 40k. Fine, moderate.

Let me instead make app "*" clusterSpec have 1000 fields and srd 100 named -> output 100*1000=100k values. That's at the limit. Let's do 80 named * 1000 fields = 80k output. Deepcopy 80*1000=80k. Good, should be ~50ms+.

- Case E "no-clusterspec-heavy": app 2000 eps mostly without clusterSpec (so deepcopy still copies them all — 2000 eps), srd wildcard. Deepcopy of 2000 entries. Work mostly deepcopy. Output small. Hmm but output small means the 4-most-work selection... it's fine.

Actually deepcopy of 2000 entries each with instanceType only ~ few values each = ~6000 values. Not much.

Let me make clusterSpec missing but entry has many other fields to make deepcopy heavy. E.g. each ep has "instanceTypeSelector" dict with 50 fields. That's realistic-ish (app doc systemRequirements can have instanceTypeSelector). Deepcopy 2000*50 = 100k values. Good.

- Case F "field-heavy": app 10 eps each clusterSpec 5000 fields; srd wildcard. Deepcopy 50k values. Output 10*5000=50k. Good.

- Case G "srd-no-match": app 300 eps clusterSpec 100 fields, srd 300 named not matching, app no "*". Filter removes all, last loop no-op. Work: deepcopy 300*100=30k. Output empty. 

- Case H "large-mixed-fields": app 200 eps each clusterSpec 200 fields with mix; srd 100 named + wildcard.

That's 8. Good.

Now, importantly, SystemRequirementsDict.__init__ deep copies entrypoints. So building instances at module level is fine (setup not timed). The thunk returns the instances.

But wait: does the function mutate srd? No. Does the function's returned SRD get compared? It returns SRD with merged_cluster_spec. Comparison probably compares .entrypoints. Fine.

One concern: The function does `merged_cluster_spec[entry_pt]["clusterSpec"].update(...)`. The deep copy of self.entrypoints means self not mutated. Good. But srd's clusterSpec dict is used as source in update; not mutated. Good.

However, there's a subtlety: `srd.entrypoints.get(entry_pt, srd.entrypoints.get("*"))["clusterSpec"]` — the dict returned is from srd, and .update() reads it. Not mutated.

Now, reusing the same srd instance across many calls: fine since not mutated.

But wait — "Anything the function changes outside its arguments ... carries over". The function doesn't change anything persistent. Good.

Now module-level data generation. Let's ensure total memory < 100MB. 500 eps * 100 fields strings ~ maybe a few MB. Fine.

Let me write the code.

```python
import random
from dxpy.system_requirements import SystemRequirementsDict


def _cluster_spec(n_fields, seed):
    rng = random.Random(seed)
    d = {
        "initialInstanceCount": rng.randint(1, 100),
        "type": rng.choice(["spark", "dnanexus", "generic"]),
        "version": "2.4.0",
        "bootstrapScript": f"bootstrap_{rng.randint(0, 999)}.sh",
    }
    for j in range(n_fields):
        d["p%d" % j] = "v%d_%d" % (rng.randint(0, 10**6), j)
    return d


def _app(names, n_fields, seed, with_cluster_prob=0.9, wildcard=None, filler_fields=0):
    rng = random.Random(seed)
    eps = {}
    for i, name in enumerate(names):
        ep = {}
        if rng.random() < with_cluster_prob:
            ep["clusterSpec"] = _cluster_spec(n_fields, seed * 100003 + i)
        if rng.random() < 0.5:
            ep["instanceType"] = "mem%d_ssd1_x%d" % (rng.randint(1, 4), rng.randint(2, 8))
        if filler_fields:
            ep["instanceTypeSelector"] = {"f%d" % j: "s%d" % rng.randint(0, 10**6)
                                          for j in range(filler_fields)}
        eps[name] = ep
    if wildcard is not None:
        eps["*"] = {"clusterSpec": _cluster_spec(wildcard, seed * 7919 + 3)}
    return eps


def _srd(mapping):
    return {k: {"clusterSpec": {"initialInstanceCount": v}} for k, v in mapping.items()}
```

Wait, `_srd` values: for the last loop `req["clusterSpec"]` is used directly. Good.

Hmm, but note: in the update step, `srd.entrypoints.get(entry_pt, srd.entrypoints.get("*"))["clusterSpec"]` is merged into the app clusterSpec. If srd's clusterSpec only has initialInstanceCount, fine.

Now build module-level instances:

```python
_names_a = ["fn%04d" % i for i in range(500)]
_app_a = SystemRequirementsDict(_app(_names_a, 100, 1))
_srd_a = SystemRequirementsDict(_srd({"*": 5}))

_names_b = ["fn%04d" % i for i in range(500)]
_app_b = SystemRequirementsDict(_app(_names_b, 100, 2))
_srd_b = SystemRequirementsDict(_srd({n: (i % 7) + 1 for i, n in enumerate(_names_b[:250])}))
```

Wait `_srd_b` maps 250 names to values. But `_srd` takes mapping k->int. Good.

Case C mixed:
```python
_names_c = ["ep%04d" % i for i in range(400)]
_app_c = SystemRequirementsDict(_app(_names_c, 80, 3, wildcard=80))
_srd_c = SystemRequirementsDict(_srd(dict(
    [(n, i % 5 + 1) for i, n in enumerate(_names_c[:200])] + [("*", 9)]
)))
```

Careful building dict with duplicate "*"? No.

Case D fallback:
```python
_app_d = SystemRequirementsDict({"*": {"clusterSpec": _cluster_spec(1000, 4)}})
_srd_d = SystemRequirementsDict(_srd({"fn%03d" % i: i % 9 + 1 for i in range(80)}))
```

Case E no clusterSpec heavy filler:
```python
_names_e = ["ep%04d" % i for i in range(2000)]
_app_e = SystemRequirementsDict(_app(_names_e, 0, 5, with_cluster_prob=0.0, filler_fields=50))
_srd_e = SystemRequirementsDict(_srd({"*": 3}))
```
Wait with_cluster_prob=0.0 so no clusterSpec. Then deepcopy copies 2000 eps each with instanceTypeSelector of 50 fields = 100k values. Hmm plus instanceType. Deepcopy of 100k values maybe ~100ms. Output: filter removes all (no clusterSpec) -> empty. But the last loop: srd has "*", app has no "*" -> skip. So output empty.

Hmm, but the deepcopy of self.entrypoints with 100k values — that's the work. Good. But careful: memory. 2000*50 = 100k strings. Fine.

Actually wait, filler dict `{"f%d" % j: "s%d" % rng.randint(...)}` — 50 fields. ok.

Case F field-heavy:
```python
_names_f = ["fn%02d" % i for i in range(10)]
_app_f = SystemRequirementsDict(_app(_names_f, 5000, 6))
_srd_f = SystemRequirementsDict(_srd({"*": 7}))
```
deepcopy 10*5000=50k. Output 10*5000=50k. Good.

Case G no match:
```python
_names_g = ["app%04d" % i for i in range(300)]
_app_g = SystemRequirementsDict(_app(_names_g, 100, 7))
_srd_g = SystemRequirementsDict(_srd({"req%04d" % i: i % 6 + 1 for i in range(300)}))
```
merged empty, output empty. deepcopy 30k.

Case H mixed fields:
```python
_names_h = ["fn%04d" % i for i in range(200)]
_app_h = SystemRequirementsDict(_app(_names_h, 200, 8, with_cluster_prob=0.7, wildcard=200))
_srd_h = SystemRequirementsDict(_srd(dict(
    [(n, i % 4 + 1) for i, n in enumerate(_names_h[:100])] + [("*", 11)]
)))
```

Now cases list with labels. Thunks return (instance, srd) — the method is called as `SystemRequirementsDict.override_cluster_spec(instance, srd)`.

Thunk: `lambda: (_app_a, _srd_a)`.

checks(): 2-3 small edge inputs.

- empty: app empty dict, srd empty.
- one entrypoint.
- app has entrypoint without clusterSpec and srd wildcard.

Let's write checks:
```python
def checks():
    return [
        ("empty", lambda: (SystemRequirementsDict({}), SystemRequirementsDict({}))),
        ("single", lambda: (SystemRequirementsDict({"main": {"clusterSpec": {"initialInstanceCount": 1, "version": "2.4.0"}}}),
                            SystemRequirementsDict({"main": {"clusterSpec": {"initialInstanceCount": 3}}}))),
        ("no-cluster-spec", lambda: (SystemRequirementsDict({"main": {"instanceType": "mem1_ssd1_x2"}}),
                                     SystemRequirementsDict({"*": {"clusterSpec": {"initialInstanceCount": 2}}}))),
    ]
```

Wait empty: app {} -> merged {} -> filter -> {} -> filter -> {} -> loop none -> last loop srd.entrypoints empty -> returns SRD({}). Fine.

Single: app main with clusterSpec, srd main. merged = {main: {...}}, k in srd.entrypoints yes. update. last loop: main in merged -> skip. returns. Fine.

no-cluster-spec: app main without clusterSpec -> filtered. srd {"*"}. filter: "main" has no clusterSpec removed. merged {}. last loop: "*" in srd.entrypoints, entry_pt "*" not in merged, "*" in self.entrypoints? no -> skip. returns empty. Fine.

These are checked only for identical behaviour.

Now one issue: does the function rely on DXError import etc.? The module imports work as long as dxpy is installed. Presumably the test environment has it.

Also `from dxpy.system_requirements import SystemRequirementsDict` — the module path. Task says import exactly as `from dxpy.system_requirements import SystemRequirementsDict`. Good.

Now, potential issue: SystemRequirementsDict constructor deep copies, and constructing at module level is fine.

Let me double check that the function doesn't mutate srd or self across calls in a way that would change behavior on repeated calls. It deep-copies self.entrypoints at the start. It never touches srd.entrypoints except reading. So repeated calls identical. Good.

But hold on — the returned value is a new SRD whose __init__ deep copies merged_cluster_spec. Fine.

Now, one more: the "rendered before and after each call" of arguments — arguments are SRD instances. Rendering probably repr. Fine.

Let me reconsider the total size: case E deepcopy 100k values each call, repeated many times. Fine.

Now let me also double check `_app` with `wildcard` param: for case C, `wildcard=80` adds eps["*"] = {"clusterSpec": _cluster_spec(80,...)}.

In case C, srd has "*" and 200 named. The app has "*" too. So merged includes "*" (has clusterSpec, "*" in srd). Update "*" with srd["*"]. Good.

Case H similar.

Now think about work ordering; all good.

Let me also make sure numbers of output values under 100k:
- A: 500 eps, ~90% with clusterSpec = ~450 * (100+4) ≈ 47k. ok.
- B: 250 kept * 104 ≈ 26k.
- C: app 400 eps, 90% cluster = 360, plus "*". srd named 200 + "*". filter keeps all (since "*" in srd) -> 360+1 entries * 84 ≈ 30k.
- D: 80 * 1004 ≈ 80k. ok.
- E: 0.
- F: 10 * 5004 ≈ 50k.
- G: 0.
- H: 200 eps, 70% cluster = 140 + "*" = 141 * 204 ≈ 29k.

Good.

Now, one thing: in case A, srd only has "*". Last loop iterates srd.entrypoints = {"*": ...}. "*" not in merged_cluster_spec (app has no "*"). "*" in self.entrypoints? no. So skip. Good.

Now write final code. Use `random.Random(seed)` fixed.

Also need to be careful: `_srd` builds dict comprehension; for case C we pass a dict combining list of tuples and [("*", 9)]. Fine.

Let me also add diversity: different distributions of which entrypoints have clusterSpec.

One more consideration: the function's deepcopy of self.entrypoints is the dominant cost. To vary, the number of app entrypoints and field counts differ.

I think it's good. Let me also ensure import doesn't fail — we rely on the repository being importable.

Potential concern: `from .utils import merge` etc. dxpy.system_requirements imports from .utils, .exceptions, .compat. These are standard in repo. Should be fine.

Let me finalize.

Actually, let me reconsider whether reusing the same SystemRequirementsDict instances is safe given "no time-dependent behaviour" etc. Yes.

Also, the thunk returning the same objects each call: "The call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts." So returning module-level objects is fine, and copies are only needed if function mutates them. It doesn't.

Write it out.

For clarity, name cases descriptively.

Final code:

```python
import random

from dxpy.system_requirements import SystemRequirementsDict


def _cluster_spec(n_fields, seed):
    rng = random.Random(seed)
    d = {
        "initialInstanceCount": rng.randint(1, 100),
        "type": rng.choice(["spark", "dnanexus", "generic"]),
        "version": "2.4.0",
        "bootstrapScript": "bootstrap_%d.sh" % rng.randint(0, 999),
    }
    for j in range(n_fields):
        d["p%d" % j] = "v%d_%d" % (rng.randint(0, 10**6), j)
    return d
...
```

I'll write everything now.

Double-check case B srd: `_srd({n: (i % 7) + 1 for i, n in enumerate(_names_b[:250])})`. Names are fn0000..fn0499; first 250 = fn0000..fn0249. Good, matches app.

Case C: app names ep0000..ep0399, srd first 200 + "*".

Case H: app fn0000..fn0199, srd first 100 + "*".

Ok.

One more check on `_app` for case E: with_cluster_prob=0.0 means `rng.random() < 0.0` always False. Good. filler_fields=50 gives instanceTypeSelector dict of 50. Also 50% chance instanceType. So each ep has ~51 values. 2000*51=102k values. Good.

Write final.