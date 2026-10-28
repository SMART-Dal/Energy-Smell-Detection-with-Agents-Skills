We need to write checks() and cases() for validate_workstreams_semantics(workstreams, people_data).

The function is pure (returns errors list), doesn't modify inputs. So thunks can return the same data.

We need 8 cases with realistic scale and complexity. Let's build workstreams lists and people_data dicts.

Structure of workstreams entries: dict with "id", "kind", "parent", "people" (list of single-key dicts), "tcSponsorship".

people_data: {"teams": {"governance-committee": [...], "technical-committee": [...], "spec-sponsors": [...]}}.

Let's design cases that exercise different paths:
- duplicate ids
- self parent
- missing parent
- cycles
- missing required roles
- gcLiaison/tcSponsor/specSponsor membership checks
- collective tcSponsorship matching / mismatching
- TBD usernames

Let's create a generator function.

Note the function reads REQUIRED_ROLES, MEMBERSHIP_REQUIRED_ROLES, TBD, NONE from module globals — they're already defined in the module, fine.

Let's write a helper to build workstreams.

Key considerations: each call should take ~1ms-200ms. The function is O(n * chain length) for the cycle detection loop — with long chains it's quadratic. Let's use moderate sizes like 500-2000 workstreams.

Actually the cycle detection: for each workstream, walks up the parent chain. If we have a deep chain of length L, that's O(n*L). With n=1000 and chain length 1000, that's 10^6 steps — maybe 1 second in Python? Let's be careful. Actually each step is a dict lookup, ~100ns-200ns, so 10^6 steps ≈ 0.2s. Hmm. Let's keep chains moderate.

Let's design 8 cases:

1. "typical": ~500 workstreams, mostly valid, some with parents forming a shallow tree, people with roles, teams populated. Few errors.
2. "duplicates-and-missing-parents": many duplicate ids and missing parents.
3. "deep-chain": long parent chain (e.g., 800 deep) — exercises cycle detection loop heavily.
4. "cycle": a cycle in parent chain.
5. "role-errors": many workstreams missing required roles, and people assigned roles not in teams.
6. "collective": tcSponsorship="collective" with matching/mismatching tcSponsor lists.
7. "large-mixed": large scale, ~2000 workstreams with a mix of everything.
8. "tbd-and-none": usernames "tbd", parents "none", etc.

Let's write generator code.

Constants:
TBD = "tbd", NONE = "none".

People entry format: single-key dict like {"gcLiaison": "alice"} or {"tcSponsor": {"username": "bob"}}.

Let's write:

```python
import importlib
import random

validate_workstreams_semantics = importlib.import_module('validate-workstreams').validate_workstreams_semantics

TBD = "tbd"
NONE = "none"
```

Wait, we should not redefine TBD/NONE? It's fine to define our own constants for building data; they're just strings. The function reads its own module's globals. Fine.

Helper to build people_data:

```python
def _teams(gc, tc, ss):
    return {"teams": {
        "governance-committee": gc,
        "technical-committee": tc,
        "spec-sponsors": ss,
    }}
```

Helper to build a workstream:

```python
def _ws(wid, kind="sig", parent=None, people=None, tc_sponsorship=None):
    w = {"id": wid, "kind": kind}
    if parent is not None:
        w["parent"] = parent
    if people is not None:
        w["people"] = people
    if tc_sponsorship is not None:
        w["tcSponsorship"] = tc_sponsorship
    return w
```

Now cases.

Case 1: typical valid tree.
```python
def _case_typical(seed=0):
    rng = random.Random(seed)
    gc = [f"gc{i}" for i in range(10)]
    tc = [f"tc{i}" for i in range(15)]
    ss = [f"ss{i}" for i in range(20)]
    teams = _teams(gc, tc, ss)
    people_data = {"teams": teams}
    workstreams = []
    n = 400
    for i in range(n):
        wid = f"ws-{i:04d}"
        parent = None if i < 20 else f"ws-{rng.randrange(i):04d}"
        # ensure parent index < i so no cycles
        ...
```

Hmm, parent = f"ws-{rng.randrange(i)}" ensures parent exists and is acyclic. But parent index may be < i, fine.

people: each workstream needs gcLiaison and tcSponsor to avoid errors. Add some specSponsor too.

```python
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        if rng.random() < 0.5:
            people.append({"specSponsor": rng.choice(ss)})
```

Then workstreams.append(_ws(wid, "sig", parent, people)).

Actually parent=None for roots — but the code treats parent_id None as skip. Good.

Case 2: duplicates and missing parents.
```python
n = 600
workstreams = []
for i in range(n):
    wid = f"dup-{i % 200:04d}"  # duplicates
    parent = f"missing-{rng.randrange(300)}"  # nonexistent
    ...
```
This gives lots of duplicate id errors and missing parent errors.

Case 3: deep chain. Build chain of length 800: ws-0 parent none, ws-i parent ws-(i-1). Then for each workstream, the cycle loop walks up i steps → total ~320k steps. Fine.

Actually to make it heavier, maybe 1500 length → ~1.1M steps. That could be ~0.3-0.5s. Let's use 1000.

Case 4: cycle. Create a cycle among some workstreams, plus normal ones. e.g. ws-0..ws-499, with ws-250 parent ws-251, ws-251 parent ws-250... Actually simpler: make a big cycle of length 300. Then each of those walks 300 steps before detecting cycle. Plus other workstreams.

Case 5: role errors. Many workstreams missing gcLiaison/tcSponsor, and people with roles not in teams.

Case 6: collective tcSponsorship. Some workstreams with tcSponsorship="collective" and tcSponsor lists matching tc_members (no error) and some not matching (error).

Case 7: large mixed — 2000 workstreams with random mix.

Case 8: tbd and none — usernames "tbd" skip checks, parents "none" skip.

Let me now write them concretely, ensuring no exceptions.

Note: `w.get("people", [])` — entries are single-key dicts. `_entry_role_and_username` does `next(iter(entry))`. If entry is empty dict, next(iter({})) raises StopIteration. Avoid empty entries.

For tcSponsor role, val must be dict with "username" key for the collective check: `pr["tcSponsor"]["username"].lower()`. If val is a string, `pr["tcSponsor"]["username"]` would fail (string indexing with "username" → TypeError). So for collective workstreams, ensure tcSponsor entries are dicts with username.

Also the person_roles set: `{next(iter(pr)) for pr in w.get("people", [])}` — fine.

Let's carefully write each case.

Also note: the function's output list of errors is compared in full. Errors could be many (thousands). Keep under 100k. Fine.

Let me write helper `_mk_people`.

Let me write the code.

```python
import importlib
import random

validate_workstreams_semantics = importlib.import_module('validate-workstreams').validate_workstreams_semantics

TBD = "tbd"
NONE = "none"


def _teams(gc, tc, ss):
    return {
        "governance-committee": list(gc),
        "technical-committee": list(tc),
        "spec-sponsors": list(ss),
    }


def _people_data(gc, tc, ss):
    return {"teams": _teams(gc, tc, ss)}


def _ws(wid, kind="sig", parent=None, people=None, tc_sponsorship=None):
    w = {"id": wid, "kind": kind}
    if parent is not None:
        w["parent"] = parent
    if people is not None:
        w["people"] = people
    if tc_sponsorship is not None:
        w["tcSponsorship"] = tc_sponsorship
    return w
```

Case 1 typical:

```python
def _case_typical():
    rng = random.Random(0)
    gc = [f"gc{i}" for i in range(8)]
    tc = [f"tc{i}" for i in range(12)]
    ss = [f"ss{i}" for i in range(15)]
    pd = _people_data(gc, tc, ss)
    n = 500
    ws = []
    for i in range(n):
        wid = f"ws-{i:04d}"
        parent = None if i < 25 else f"ws-{rng.randrange(i):04d}"
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        if rng.random() < 0.4:
            people.append({"specSponsor": rng.choice(ss)})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

Wait — parent index rng.randrange(i) gives parent index < i, so chain depth could be long-ish but on average O(log n)? Actually with random parent it's like a random recursive tree, depth ~ O(log n). Fine.

Case 2 duplicates/missing:

```python
def _case_duplicates():
    rng = random.Random(1)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(600):
        wid = f"dup-{i % 150:04d}"
        parent = f"ghost-{rng.randrange(400):04d}"
        people = [{"gcLiaison": rng.choice(gc)}, {"tcSponsor": {"username": rng.choice(tc)}}]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

Case 3 deep chain:

```python
def _case_deep_chain():
    rng = random.Random(2)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    n = 1200
    ws = []
    for i in range(n):
        wid = f"chain-{i:05d}"
        parent = None if i == 0 else f"chain-{i-1:05d}"
        people = [{"gcLiaison": rng.choice(gc)}, {"tcSponsor": {"username": rng.choice(tc)}}]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

Total chain steps = sum i = n(n-1)/2 ≈ 720k. Each step: dict.get, .get, set membership. Maybe 0.3s. Hmm, could be near the limit but under 1s. Let's use n=1000 → 500k steps. Probably ~0.2s. OK.

Actually wait, the visited set check: `if current in visited` then `visited.add(current)`. For a chain, each workstream creates a new visited set. Total operations ~ 2 * 500k = 1M. Python ~0.1-0.2 µs each → 0.1-0.2s. Fine.

Case 4 cycle:

```python
def _case_cycle():
    rng = random.Random(3)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    ws = []
    cycle_len = 400
    for i in range(cycle_len):
        wid = f"cyc-{i:04d}"
        parent = f"cyc-{(i+1) % cycle_len:04d}"
        people = [{"gcLiaison": rng.choice(gc)}, {"tcSponsor": {"username": rng.choice(tc)}}]
        ws.append(_ws(wid, "sig", parent, people))
    # plus some normal ones
    for i in range(200):
        wid = f"norm-{i:04d}"
        parent = None if i < 10 else f"norm-{rng.randrange(i):04d}"
        people = [{"gcLiaison": rng.choice(gc)}, {"tcSponsor": {"username": rng.choice(tc)}}]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

For each cycle member, the loop walks 400 steps → 160k steps. Fine.

Case 5 role errors:

```python
def _case_role_errors():
    rng = random.Random(4)
    gc = [f"gc{i}" for i in range(6)]
    tc = [f"tc{i}" for i in range(6)]
    ss = [f"ss{i}" for i in range(6)]
    pd = _people_data(gc, tc, ss)
    outsiders = [f"out{i}" for i in range(20)]
    ws = []
    for i in range(400):
        wid = f"role-{i:04d}"
        parent = None if i < 20 else f"role-{rng.randrange(i):04d}"
        people = []
        # sometimes missing gcLiaison, sometimes missing tcSponsor
        if rng.random() < 0.7:
            people.append({"gcLiaison": rng.choice(outsiders + gc)})
        if rng.random() < 0.7:
            people.append({"tcSponsor": {"username": rng.choice(outsiders + tc)}})
        if rng.random() < 0.5:
            people.append({"specSponsor": rng.choice(outsiders + ss)})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

Case 6 collective:

```python
def _case_collective():
    rng = random.Random(5)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(10)]
    ss = [f"ss{i}" for i in range(8)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(300):
        wid = f"coll-{i:04d}"
        parent = None if i < 10 else f"coll-{rng.randrange(i):04d}"
        # build tcSponsor list: matching or not
        if rng.random() < 0.5:
            listed = list(tc)
        else:
            listed = [f"tc{rng.randrange(10)}" for _ in range(rng.randrange(1, 6))]
        people = [{"gcLiaison": rng.choice(gc)}]
        for u in listed:
            people.append({"tcSponsor": {"username": u}})
        ws.append(_ws(wid, "sig", parent, people, tc_sponsorship="collective"))
    return ws, pd
```

Careful: listed may contain duplicates; the set comprehension dedupes. Matching requires set equality with tc_members (lowercased). tc_members = {u.lower() for u in tc} = tc since lowercase. listed set equals tc set → no error. Otherwise error. Good.

Also note the people list has one gcLiaison and multiple tcSponsor entries — each entry is a single-key dict. Fine.

Case 7 large mixed:

```python
def _case_large_mixed():
    rng = random.Random(6)
    gc = [f"gc{i}" for i in range(10)]
    tc = [f"tc{i}" for i in range(15)]
    ss = [f"ss{i}" for i in range(12)]
    pd = _people_data(gc, tc, ss)
    n = 2000
    ws = []
    for i in range(n):
        wid = f"mix-{i:04d}"
        r = rng.random()
        if r < 0.1:
            parent = None
        elif r < 0.2:
            parent = NONE
        elif r < 0.3:
            parent = wid  # self
        elif r < 0.4:
            parent = f"ghost-{i}"
        else:
            parent = f"mix-{rng.randrange(i):04d}" if i > 0 else None
        people = []
        if rng.random() < 0.8:
            people.append({"gcLiaison": rng.choice(gc + [TBD])})
        if rng.random() < 0.8:
            people.append({"tcSponsor": {"username": rng.choice(tc + [TBD])}})
        if rng.random() < 0.3:
            people.append({"specSponsor": rng.choice(ss)})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

Wait: parent = wid (self) — the code checks `if parent_id == wid` and continues, so no infinite loop. Good.

But careful: `f"mix-{rng.randrange(i):04d}"` when i=0 → randrange(0) raises ValueError. Guard with `if i > 0 else None`. I wrote that. Good.

Hmm, but for the self-parent case, parent=wid, then the cycle detection loop: current=wid, parent of wid is wid → visited={wid}, then current=wid again → in visited → cycle error. Fine.

Case 8 tbd/none:

```python
def _case_tbd_none():
    rng = random.Random(7)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(400):
        wid = f"tbd-{i:04d}"
        parent = NONE if i % 3 == 0 else (None if i % 3 == 1 else f"tbd-{rng.randrange(i):04d}" if i > 0 else None)
        people = [
            {"gcLiaison": TBD},
            {"tcSponsor": {"username": TBD}},
            {"specSponsor": TBD},
        ]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd
```

Hmm, the ternary is messy. Let me simplify.

Actually let's simplify case 8: all usernames TBD, parents mixed none/None/existing.

```python
    for i in range(400):
        wid = f"tbd-{i:04d}"
        if i % 3 == 0:
            parent = NONE
        elif i % 3 == 1:
            parent = None
        else:
            parent = f"tbd-{rng.randrange(i):04d}" if i > 0 else None
        people = [
            {"gcLiaison": TBD},
            {"tcSponsor": {"username": TBD}},
        ]
        if i % 2 == 0:
            people.append({"specSponsor": TBD})
        ws.append(_ws(wid, "sig", parent, people))
```

Wait, if parent is NONE string, the code does `if parent_id is None or parent_id == NONE: continue`. Good.

Now checks(): 2-3 small edge inputs.

- empty workstreams and empty people_data: `([], {})`. The function: seen_ids empty, id_to_workstream empty, loops do nothing, teams = {}.get("teams", {}) → {} → gc_members etc empty. Returns []. Fine.
- one workstream with no people: `([{"id": "w1"}], {"teams": {}})`. person_roles empty → two errors for missing gcLiaison and tcSponsor. Fine.
- odd type: workstream with people entry that's an empty dict? That would raise StopIteration in `next(iter(pr))`. That's allowed for checks (may raise). But maybe better to use something that doesn't raise. Hmm, "an odd type" — could use people_data missing "teams" key, or a workstream with no "id". Let's do: `([{"kind": "sig"}], {})` — no id, no people. wid = "(unknown)", person_roles empty → errors. Fine.

Actually let's include a case that raises? The instruction says checks may raise. But safer to include non-raising ones plus maybe one odd. Let's do three:

1. ("empty", lambda: ([], {}))
2. ("single-no-people", lambda: ([{"id": "w1"}], {"teams": {}}))
3. ("missing-id-and-teams", lambda: ([{"kind": "sig", "people": [{"gcLiaison": "alice"}]}], {}))

Third: wid = "(unknown)", person_roles = {"gcLiaison"}, missing tcSponsor → error. teams = {}.get("teams", {}) = {} → empty sets. gcLiaison "alice" not in gc_members → error. Fine, no raise.

Now, cases() must return exactly 8. Let's finalize.

One concern: the thunks return the same list objects each call. The function doesn't modify them (it builds new sets/dicts). Let me verify: `id_to_workstream = {w["id"]: w for w in workstreams if "id" in w}` — reads. `visited = set()` local. `person_roles = {...}` local. No mutation of inputs. Good. So we can reuse the same objects.

But wait — the harness renders arguments before and after each call to see if they changed. Since no mutation, fine.

However, building all inputs at module level or in thunks? The thunks run before timing, so building in the thunk is fine too, but it would be repeated for each call (many times). Better to build once at module level and have thunks return the prebuilt data.

Let's build at module level:

```python
_CASES = [
    ("typical-tree", _case_typical()),
    ...
]
```

Then cases() returns [(label, lambda: (ws, pd)) ...]. But lambdas capturing loop variables — need default args or a factory.

```python
def cases():
    return [
        ("typical-tree", (lambda a=_case_typical(): (a[0], a[1]))),
        ...
    ]
```

Hmm, but that calls _case_typical() at cases() time, which is fine (setup not timed). Actually the thunk is called before timing each time; if the thunk just returns prebuilt data, cheap. Let's prebuild at module level:

```python
_TYPICAL = _case_typical()
...
def cases():
    return [
        ("typical-tree", lambda: _TYPICAL),
        ...
    ]
```

Wait, `_TYPICAL` is a tuple (ws, pd), and the thunk must return a tuple of positional arguments. So `lambda: _TYPICAL` returns (ws, pd) which is the args tuple. 

But careful: if the function mutated the list, subsequent calls would differ. It doesn't. OK.

Actually, hmm: the harness might call the thunk many times and compare... The args are the same objects each time. Fine.

Let me also double check the module import: `importlib.import_module('validate-workstreams')`. The module has top-level code that imports subprocess, sys, pathlib, yaml, jsonschema. Does it execute anything at import time? The file defines constants and functions. `main()` is presumably guarded by `if __name__ == "__main__"`. Let's assume so. The task says import it as given.

But wait — does the module read files at import time? Looking at the headers: load_schema, load_yaml, validate_against_schema, main. Constants PEOPLE_FILE etc. probably defined at module level as Paths. Should be fine.

Now let's make sure the sizes give reasonable timing. Case 7 with 2000 workstreams: the cycle detection loop — for each workstream, walk chain. Chains are shallow (random recursive tree) except self/ghost cases. Should be fast, maybe 10-20ms. Case 3 deep chain ~1000 → ~0.2s. That's within limits.

Hmm, the harness keeps the 4 cases that do the most work. Fine.

Let me reconsider case 3 size. n=1000 chain: total inner iterations = 1000*1001/2 ≈ 500k. Each iteration: `current in visited` (set lookup), `visited.add`, `id_to_workstream.get(current, {}).get("parent")`. Maybe ~0.3µs per iteration → 0.15s. OK.

Maybe make it 1500 to be more substantial? 1500*1501/2 ≈ 1.1M → ~0.35s. Still under 1s. Let's use 1200 as a middle ground.

Actually let's think about the total time budget: "building all inputs under about 10 s". Building 8 cases with a few thousand workstreams each is fast.

Now let me also double-check the "collective" case: the code does

```python
if w.get("tcSponsorship") == "collective":
    listed = {
        pr["tcSponsor"]["username"].lower()
        for pr in w.get("people", [])
        if "tcSponsor" in pr
    }
    if listed != tc_members:
```

So each person entry with key "tcSponsor" must have dict value with "username". In my case 6, all tcSponsor entries are dicts. Good.

But also, in case 6, the people list has a gcLiaison entry and tcSponsor entries. The role check loop: for gcLiaison, checks membership in gc_members. We use rng.choice(gc) so it's a member → no error. For tcSponsor, checks membership in tc_members. We use tc members → no error. Good.

Also note `spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members`.

Now, one more thing: in case 6, `listed` could be empty if rng.randrange(1,6) ... no, at least 1. Fine.

Let's also ensure no duplicate ids in cases other than case 2 and case 7 (where self-parent uses same id but that's the same workstream, not duplicate). In case 7, ids are unique (mix-0000...). Good.

Now write final code.

Also need `import random` and `import importlib`.

Let me write it all out.

One more check on case 5: `rng.choice(outsiders + gc)` — outsiders + gc is a list. Fine.

Also in case 5, people might be empty list → person_roles empty → errors. Fine.

Let me also consider: in case 2, `wid = f"dup-{i % 150:04d}"` — 600 workstreams, 150 unique ids, each repeated 4 times. seen_ids: first occurrence no error, next 3 → "Duplicate workstream id" errors. Good.

id_to_workstream: dict comprehension with duplicate keys keeps last. Fine.

Now the final code.

Let me write:

```python
import importlib
import random

validate_workstreams_semantics = importlib.import_module('validate-workstreams').validate_workstreams_semantics

TBD = "tbd"
NONE = "none"


def _people_data(gc, tc, ss):
    return {"teams": {
        "governance-committee": list(gc),
        "technical-committee": list(tc),
        "spec-sponsors": list(ss),
    }}


def _ws(wid, kind="sig", parent=None, people=None, tc_sponsorship=None):
    w = {"id": wid, "kind": kind}
    if parent is not None:
        w["parent"] = parent
    if people is not None:
        w["people"] = people
    if tc_sponsorship is not None:
        w["tcSponsorship"] = tc_sponsorship
    return w
```

Then the case builders.

Then:

```python
_TYPICAL = _case_typical()
...
```

Actually, let me just have cases() build them each time it's called? No — cases() is called once to get the list of thunks. The thunks are called many times. So build at module level to avoid rebuilding. Actually building inside cases() is also fine since cases() is called once. But module-level is cleaner. Let's build inside cases() via closures? The thunk would then need to capture. Simplest: module-level globals.

Let me write:

```python
_C1 = _case_typical()
_C2 = _case_duplicates()
...
```

Then:

```python
def cases():
    return [
        ("typical-tree", lambda: _C1),
        ("duplicates-missing-parents", lambda: _C2),
        ("deep-parent-chain", lambda: _C3),
        ("parent-cycle", lambda: _C4),
        ("role-membership-errors", lambda: _C5),
        ("collective-tcsponsorship", lambda: _C6),
        ("large-mixed", lambda: _C7),
        ("tbd-and-none", lambda: _C8),
    ]
```

Wait — `_C1` is a tuple `(ws, pd)`. `lambda: _C1` returns that tuple, which is the positional args. Good.

Hmm, but the harness says "Each thunk returns a tuple of positional arguments for the function". So returning `_C1` = (ws, pd) is correct.

Now checks():

```python
def checks():
    return [
        ("empty", lambda: ([], {})),
        ("single-no-people", lambda: ([{"id": "w1"}], {"teams": {}})),
        ("missing-id", lambda: ([{"kind": "sig", "people": [{"gcLiaison": "alice"}]}], {})),
    ]
```

Good.

Let me finalize the case builders with careful code.

Double-check case 7's parent assignment: `parent = f"mix-{rng.randrange(i):04d}" if i > 0 else None`. But this branch is under `else` of `r < 0.4`, and if i==0, we want None. Actually for i==0, rng.randrange(0) would fail, so guard. But also for i==0, r<0.1 etc. Let's just guard.

Actually, cleaner:

```python
        if r < 0.1:
            parent = None
        elif r < 0.2:
            parent = NONE
        elif r < 0.3:
            parent = wid
        elif r < 0.4:
            parent = f"ghost-{i}"
        elif i == 0:
            parent = None
        else:
            parent = f"mix-{rng.randrange(i):04d}"
```

Good.

Also note: `_ws` sets parent only if not None. For parent=NONE, it's set. For parent=wid, set.

Now, in case 7, some workstreams have parent pointing to a later workstream? No, rng.randrange(i) < i. Good.

Let me also double check case 4: cycle of length 400. For each cycle member, the while loop: current=wid, visited empty. Iteration 1: current not in visited, add, current = parent. ... After 400 iterations, current = wid again, which is in visited → error "parent chain contains a cycle", break. So 400 iterations per member × 400 members = 160k. Fine.

But wait — the cycle detection loop is for ALL workstreams, including norm ones. Fine.

Now, one subtlety: in case 4, the cycle members have parent = next in cycle. But `id_to_workstream[parent]` exists. Good.

Now let's think about whether the function could be slow due to `person_roles = {next(iter(pr)) for pr in w.get("people", [])}` — fine.

I think we're good.

Let me also reconsider: should I worry that `importlib.import_module('validate-workstreams')` might fail because the module imports yaml/jsonschema which may not be installed? The task says "Use only the standard library, the repository itself and packages the repository already imports." So yaml and jsonschema are available. Fine.

Also, the module might be at `scripts/validate-workstreams.py`. The import path — how does the harness set it up? The task says import it as given, so presumably sys.path includes scripts/. We just follow.

Final code writing.

One more: in `_case_typical`, `parent = None if i < 25 else f"ws-{rng.randrange(i):04d}"`. For i >= 25, randrange(i) gives 0..i-1. Good.

Let me write out everything now.

Actually, let me reconsider the number of errors in case 2. 600 workstreams, 150 unique ids. Duplicate errors: 450. Missing parent errors: each workstream with parent ghost-XXXX → 600 errors (unless parent_id == wid, unlikely). So ~1050 errors. Fine.

Case 5: ~400 workstreams, each missing roles → up to 2 errors each = 800, plus membership errors. Fine.

OK, writing.

Also, I should double check: `_entry_role_and_username` for role "tcSponsor" with val dict: `val.get("username", "")`. If val is dict without username → "". Then username == TBD? No. role in MEMBERSHIP_REQUIRED_ROLES → yes. So checks membership. Fine.

In case 6, all tcSponsor dicts have username. Good.

Now write the final answer.