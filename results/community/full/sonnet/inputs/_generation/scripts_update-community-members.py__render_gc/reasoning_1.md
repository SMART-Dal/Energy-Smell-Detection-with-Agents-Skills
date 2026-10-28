Let me analyze. `render_gc` reads module globals `teams`, `people`, `metadata`. It uses `teams.get("governance-committee", [])`, and `people` dict for display_name, company, term_end.

The module is `scripts/update-community-members.py`. Importing it via importlib. But importing the module executes module-level code, which may read files (metadata, people) — let's think. The module has `teams = metadata.get("teams", {})` at module level, so `metadata` is defined earlier. Likely the module loads a YAML config file at import time. That could fail if files don't exist.

Hmm, we need to be careful: importing the module runs its top-level code. If it reads a file that doesn't exist, it will raise. We can't know. But we can set up... Actually the task says "Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk."

We don't know the module's top-level code. But we can guess it reads a YAML file, maybe from a path relative to the script. Risky.

Let me think about what's likely: `metadata` probably = yaml.safe_load of some file. `people` too. The module likely does something like:

```python
DATA = Path(__file__).parent / "community-members.yaml"
with open(DATA) as f:
    metadata = yaml.safe_load(f)
people = metadata.get("people", {})
```

Hmm, but we can't know. However, we can set the module globals after import: `mod.teams = ...`, `mod.people = ...`. But if the import itself fails, we're stuck.

Actually, maybe the module is designed to be imported and reads files that exist in the repo. But we don't have the repo files here. Hmm, but the task says "Everything you can know about the repository is in the task". So maybe the import works fine because the module reads a data file that ships with the repo? We don't know.

Alternative: the top-level code might read a file that doesn't exist in our environment → ImportError. Then we'd get CANNOT RUN. But the task expects us to write inputs.

Hmm. Let me reconsider. Actually the module top-level probably does something like:

```python
script_dir = Path(__file__).parent
metadata = yaml.safe_load((script_dir / "community-members.yaml").read_text())
```

Since we're importing from the repo's scripts directory, the file would be there if the repo is present. The task says the repository is available (we import the module). So the data file likely exists.

But wait — the module might also call subprocess or sys.argv... The imports include subprocess and sys. Possibly there's a `run_in_check_mode` flag from sys.argv. If the module's top-level code uses sys.argv and does something like `sys.exit()`... unlikely.

Actually the module probably has a `main()` guarded by `if __name__ == "__main__":`. So importing is safe.

But the module-level code reading the yaml file — we don't know the filename. Hmm. But if it's relative to `__file__` it'll work.

Let me just write code that imports the module inside a try? No — we must write code that runs. Let's assume import works.

Actually, there's a risk: the module may read a file path from sys.argv or from a constant. Let's just try to import and set the globals.

Plan:
- Import the module via importlib.
- Set `mod.teams = {"governance-committee": [...]}` and `mod.people = {...}`.
- Note: `render_gc` reads `teams` and `people` as module globals at call time (they're referenced inside the function body). Actually `teams` is defined at module level as `metadata.get("teams", {})`. The function references the global `teams`, so setting `mod.teams` works. Similarly `people` — display_name uses `people.get(...)`, so `mod.people` must be set.

Wait, but is `people` a module global? `display_name` uses `people.get(username, {})`. Yes, `people` must be a module-level global. We set `mod.people`.

Now, the function: sorts usernames by display_name, then joins lines. Work is proportional to number of GC members. To make it take ~1ms-200ms, we need many members. With maybe 100k members? Sorting 100k strings with a key... display_name is a dict lookup. That's fast, maybe 50ms. Let's use up to ~200k.

Actually to get 200ms we might need ~500k entries. Let's aim for varied sizes: 10k, 50k, 100k, 200k. Hmm, but the constraint: output under 100,000 values. The returned string is one value; but "keep what it returns ... under about 100 000 values" — the string length? Each line is maybe 100 chars. 200k lines = 20MB string. That's fine-ish but "under 100 000 values" probably means list elements. A string is one value. Hmm, but let's be moderate: keep members under ~100k to be safe. Actually let's keep the largest at 100k. Sorting 100k with key lookups: roughly 100k * log2(100k) ≈ 1.7M comparisons, each comparison calls display_name (dict lookups). Maybe 100-200ms. Good.

Diversity: different people dicts — some usernames missing from people (so display_name returns username, company "", term_end ""), some with full data, some with only name, etc. Also duplicates in the team list? sorted with duplicates. Also members whose display names are similar.

Also note: `teams.get("governance-committee", [])` — cases where the key is missing → empty. That's a check case.

Let's design 8 cases:
1. Large team of 100k, all present in people with name/company/termEnd.
2. Team of 50k, half missing from people.
3. Team of 80k with many duplicate usernames.
4. Team with unusual display names (unicode, empty names).
5. Team of 20k with people entries having only name.
6. Team of 120k? maybe too big. Let's keep ≤ 100k.
7. Team with unsorted random order and mixed presence.
8. Team where people map has extra entries not in team.

Hmm, but the function's output is compared in full after every input, and we keep 4 that do most work. That's fine.

Let me think about realistic scale: a governance committee is normally ~10 people. But we need stress. The task says "Use realistic scale and complexity" but also "Generate stressful inputs". I'll go with larger.

Let me write helper to generate.

```python
import importlib
import random

render_gc = importlib.import_module('update-community-members').render_gc
_mod = importlib.import_module('update-community-members')
```

Careful: importlib.import_module with a name containing dashes works since it's a module name (file name). But we need the module in sys.path. The task says import it as shown, so presumably the scripts dir is on sys.path.

Actually `importlib.import_module('update-community-members')` — Python module names with dashes are fine for import_module? It uses the finder; the name is used as-is. Should work if the file is on the path.

But wait, the module top-level code may fail. Let's consider: it probably reads a yaml file. If it fails, we can't do anything. I'll assume it works.

Hmm, actually there's a concern: the module might be located in scripts/ and read a file relative to cwd. But we can't control. Let's just go.

Now, setting globals: `_mod.teams = {...}`, `_mod.people = {...}`.

But careful: `teams` at module level = `metadata.get("teams", {})`. If we set `_mod.teams`, the function reads the global `teams` from the module namespace → our value. Good.

Now, does the function read `people` global? display_name/company/term_end are defined in the module and reference `people`. Yes.

Now build data.

Helper:

```python
def _build(n, present_ratio, dup_ratio, seed, full=True):
    rng = random.Random(seed)
    usernames = []
    people = {}
    for i in range(n):
        u = f"user{i}"
        usernames.append(u)
        if rng.random() < present_ratio:
            entry = {}
            if rng.random() < 0.9:
                entry["name"] = f"Name {i}"
            if rng.random() < 0.7:
                entry["company"] = f"Company {i % 50}"
            if rng.random() < 0.7:
                entry["termEnd"] = f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"
            people[u] = entry
    # duplicates
    ...
```

Hmm, generating 100k with Python loop is fine (< 1s).

But wait, for the "different data distributions" requirement, let's make each case distinct.

Also, module-level: build all data once, thunks return references. The function doesn't mutate teams/people (sorted creates a new list; get doesn't mutate). So thunks can just return `()`. But since the function reads module globals, we must set the globals per case. Hmm! That's a problem: the function reads `teams` and `people` from the module globals, not from arguments. The thunk returns arguments (empty tuple). But the module globals must be set to the case's data at call time.

So the thunk must set `_mod.teams` and `_mod.people` before returning `()`. That's setup in the thunk — allowed, and it's not timed (well, thunk runs before timing). Yes: "Thunks run before the timing starts; only the call of the function is timed." So setting globals in the thunk is fine.

But careful: each thunk call must set the globals. Since we run the same thunk many times, it just re-assigns the same dicts. Fine.

But also: the function reads globals at call time. Since thunks set them right before the call, good.

However, there's a subtlety: the harness might call the thunk, then call the function, then call the thunk again, etc. Setting globals in thunk works.

So:

```python
def _case(teams_val, people_val):
    def thunk():
        _mod.teams = teams_val
        _mod.people = people_val
        return ()
    return thunk
```

Wait, but `teams` is `metadata.get("teams", {})`. The function does `teams.get("governance-committee", [])`. So we set teams to a dict with key "governance-committee".

Also `metadata` might be used elsewhere but not by render_gc.

Now checks():
- empty team: `{"governance-committee": []}` → returns "".
- missing key: `{}` → returns "".
- one element with no people entry.

These may raise? They don't. Fine.

Now let's think about sizes and timing. Let's target the largest ~100k. Sorting 100k items with a Python key function that does dict lookups: key function called 100k times, then sort comparisons on strings. Probably ~100-200ms. Good enough.

Actually, let me reconsider: to be safe on "one call takes over 1s are dropped", keep max at 100k.

Let me define cases with different sizes and distributions:

1. "full-100k": 100k members, all present with name/company/termEnd.
2. "sparse-60k": 60k members, 30% present, some with empty dicts.
3. "dups-80k": 80k entries from a pool of 5k usernames (many duplicates), all present.
4. "unicode-40k": names with unicode, some empty names, some missing.
5. "mixed-70k": random presence, varying fields.
6. "no-people-50k": all members missing from people (display_name = username).
7. "sorted-input-30k": usernames already sorted (to test best-case sorting, still work).
8. "big-people-90k": people has 200k entries, team has 90k.

Hmm, we need "different paths through its code". The code is simple; paths are limited. Diversity in data distributions is the main lever.

Let's also include a case where termEnd/company are empty strings.

Let me write generation carefully and efficiently.

For duplicates case: generate 80k usernames drawn from a pool of 5000, with people entries for the pool.

Let me write:

```python
def _people_for(usernames, seed, present=1.0, name_ratio=0.9, company_ratio=0.7, term_ratio=0.7):
    rng = random.Random(seed)
    people = {}
    for u in usernames:
        if rng.random() > present:
            continue
        e = {}
        if rng.random() < name_ratio:
            e["name"] = ...
        ...
        people[u] = e
    return people
```

Hmm, generating 100k entries with random calls: ~600k random calls, maybe 0.5s each case. 8 cases → a few seconds. Acceptable ("building all inputs under about 10 s").

Let me be a bit careful and keep it fast.

Let me now write the code.

```python
import importlib
import random

_mod = importlib.import_module('update-community-members')
render_gc = _mod.render_gc


def _team(usernames):
    return {"governance-committee": usernames}


def _people(usernames, seed, present=1.0, name_ratio=0.9, company_ratio=0.7,
            term_ratio=0.7, prefix="Name"):
    rng = random.Random(seed)
    people = {}
    for i, u in enumerate(usernames):
        if rng.random() > present:
            continue
        e = {}
        if rng.random() < name_ratio:
            e["name"] = f"{prefix} {i}"
        if rng.random() < company_ratio:
            e["company"] = f"Company {i % 37}"
        if rng.random() < term_ratio:
            e["termEnd"] = f"20{rng.randint(20, 30)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"
        people[u] = e
    return people
```

Wait, for duplicates, usernames list has dupes; people dict keyed by username; using enumerate index i for name gives different names per occurrence — but dict dedups, last wins. Fine.

Better: for duplicates, build people from the unique pool.

Let me restructure: each case builds (team_list, people_dict) at module level.

Case 1: 100k unique usernames, all present, full fields.
```python
_u1 = [f"user{i}" for i in range(100_000)]
_p1 = _people(_u1, 0, present=1.0)
```

Case 2: 60k, present 0.3, some empty dicts.
```python
_u2 = [f"member{i}" for i in range(60_000)]
_p2 = _people(_u2, 1, present=0.3, name_ratio=0.5, company_ratio=0.3, term_ratio=0.3)
```

Case 3: duplicates: pool of 4000, team of 80k.
```python
_pool3 = [f"dup{i}" for i in range(4_000)]
_p3 = _people(_pool3, 2, present=1.0)
_rng = random.Random(3)
_u3 = [_pool3[_rng.randrange(4_000)] for _ in range(80_000)]
```

Case 4: unicode names, 40k, some missing.
```python
_u4 = [f"用户{i}" for i in range(40_000)]
_p4 = _people(_u4, 4, present=0.6, name_ratio=0.8)
```
Plus some empty names? Let's add a few entries with name "" — display_name returns "" (since .get("name", username) returns "" if key present with empty). Actually `people.get(username, {}).get("name", username)` — if "name" is "" then returns "". Good, that's an edge. Let's set some names to "".

Hmm, let me add a parameter. Simpler: after building, mutate some entries.

Case 5: mixed 70k with random presence and varying fields, and people containing extra unrelated entries.
```python
_u5 = [f"dev{i}" for i in range(70_000)]
_p5 = _people(_u5, 5, present=0.7, name_ratio=0.95, company_ratio=0.5, term_ratio=0.9)
# extra entries
for j in range(50_000):
    _p5[f"extra{j}"] = {"name": f"Extra {j}", "company": "X", "termEnd": "2030-01-01"}
```

Case 6: all missing from people, 50k.
```python
_u6 = [f"ghost{i}" for i in range(50_000)]
_p6 = {}
```

Case 7: already sorted usernames, 30k.
```python
_u7 = [f"a{i:06d}" for i in range(30_000)]  # sorted
_p7 = _people(_u7, 7, present=0.8)
```

Case 8: reverse-sorted usernames, 90k, to stress sorting worst case? Sorting reverse-sorted is also easy in Timsort. Hmm. Maybe random order is worse. Let's do a case with people having long names to make comparisons heavier.

Actually let's make case 8: 90k members with people entries whose names are long strings (e.g., 200 chars), making string comparisons more expensive and the output bigger. But output size: 90k lines * ~250 chars = 22MB. Under 100k values (one string). Should be OK but maybe heavy. Let's keep names ~80 chars.

Hmm, "keep what it returns ... under about 100 000 values". A single string — ambiguous. 90k lines is under 100k. Fine.

Let me reconsider sizes for timing. Sorting 100k strings: key extraction 100k dict lookups + 100k string creations? No, key returns existing strings. Then sort comparisons. Python sort of 100k strings ~ 30-50ms. Plus join and f-string formatting 100k times ~ 50ms. So maybe 100ms total. Good.

Let's make sure the largest is 100k.

Now checks():
- empty list: `{"governance-committee": []}` → ""
- missing key: `{}` → ""
- one member not in people.

These set globals too.

Let me write checks with thunks setting globals.

Now, one important thing: the module import. `importlib.import_module('update-community-members')` — will it find it? The task says to import it that way, so presumably yes. But the module's top-level code might read a data file. Let's hope it works.

Actually wait — there's a risk the module's top-level reads a file with a relative path and fails. But the task explicitly gives the import line, implying it works in the harness environment. I'll go with it.

Also note: the module might have `metadata` loaded and `teams` derived. We override `teams` and `people`. But `render_gc` also uses `display_name`, `company`, `term_end` which use `people`. Good.

One more: does `render_gc` use `metadata` directly? No.

Let me also consider: the function might be defined to read `teams` from globals — yes.

Now write final code.

Let me be careful about the `_people` helper using index i for name — for duplicates case, names differ per occurrence but dict keeps last. Fine.

Also for case 4, I want some empty names. Let me add a param `empty_name_ratio`.

Let me simplify and write inline.

```python
import importlib
import random

_mod = importlib.import_module('update-community-members')
render_gc = _mod.render_gc


def _make_people(usernames, seed, present=1.0, name_ratio=0.9, company_ratio=0.7,
                 term_ratio=0.7, empty_name_ratio=0.0, name_len=0):
    rng = random.Random(seed)
    people = {}
    for i, u in enumerate(usernames):
        if rng.random() > present:
            continue
        e = {}
        if rng.random() < name_ratio:
            if rng.random() < empty_name_ratio:
                e["name"] = ""
            else:
                base = f"Name {i}"
                if name_len:
                    base = (base + " " + "x" * name_len)[:name_len]
                e["name"] = base
        if rng.random() < company_ratio:
            e["company"] = f"Company {i % 37}"
        if rng.random() < term_ratio:
            e["termEnd"] = f"20{rng.randint(20, 30)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        people[u] = e
    return people
```

Hmm name_len truncation is weird. Let's just use long names for case 8 with a separate approach.

Let me finalize cases:

1. full-100k
2. sparse-60k
3. dups-80k
4. unicode-40k
5. mixed-70k (+extra people)
6. ghosts-50k (no people)
7. sorted-30k
8. longnames-90k

For case 8, generate names of length ~120: `f"{'n'*100} {i}"`.

Let me write it.

```python
_u8 = [f"long{i}" for i in range(90_000)]
_p8 = {}
_rng8 = random.Random(8)
for i, u in enumerate(_u8):
    _p8[u] = {
        "name": "N" * 100 + f" {i:06d}",
        "company": "C" * 50,
        "termEnd": "2030-01-01",
    }
```
That's 90k dicts — building takes maybe 0.2s. Fine.

Output for case 8: 90k lines each ~ 100+ chars → ~15MB string. OK.

Now thunks:

```python
def _set(team, people):
    def thunk():
        _mod.teams = team
        _mod.people = people
        return ()
    return thunk
```

Wait, but `teams` in module is `metadata.get("teams", {})`. Setting `_mod.teams` replaces it. Good.

But careful: the harness renders arguments before and after each call to see if changed. Arguments here are `()` — nothing. Fine. It also may check module globals? No, only arguments.

Now cases list:

```python
def cases():
    return [
        ("full-100k", _set({"governance-committee": _u1}, _p1)),
        ...
    ]
```

Note: each thunk returns `()` — the function takes no arguments. Good.

One concern: `render_gc` is the function; calling `render_gc()` with no args. The thunk returns `()`. Good.

Now checks:

```python
def checks():
    return [
        ("empty", _set({"governance-committee": []}, {})),
        ("missing-key", _set({}, {})),
        ("one-unknown", _set({"governance-committee": ["nobody"]}, {})),
    ]
```

These should produce "" and a line. Fine.

Wait — checks may raise; these don't. That's fine.

Now, potential issue: setting `_mod.teams` — but is `teams` used at module import time by other code? No, only render_gc and render_tc.

Hmm, but what if the module's top-level code fails to import because it needs a file? Then everything fails. Let's think whether we can guard. The instructions say if the function cannot run here at all, reply CANNOT RUN. But we can't know without trying. I'll assume it imports.

Actually, let me reconsider: maybe the module reads data from a YAML file located next to the script, e.g. `community-members.yaml`. Since we import the module from the repo, that file exists. Good.

But the module might use `Path(__file__).parent` — fine.

Alternatively it might use a hardcoded relative path like `"data/community-members.yaml"` relative to cwd. Then import would fail unless cwd is repo root. Hmm. We can't control cwd. Risky but let's go.

Actually, we could set the module globals after import, but the import itself is the issue. We can't avoid it.

Hmm, one more thought: maybe the module doesn't read files at top level at all; maybe metadata is defined via an import or a constant. Either way.

Let me just write it. If import fails, harness will show error, but we can't do better.

Actually — could we make the import more robust by adding the script's directory to sys.path? The import line is given as `importlib.import_module('update-community-members')`, so the harness presumably has the right path. Don't add.

Let me also double check: `render_gc = importlib.import_module('update-community-members').render_gc` — the task says import it this way. I'll do exactly that but also keep `_mod`.

Now let me also think about whether the function mutates `teams` or `people`: `sorted(teams.get(...), key=display_name)` creates a new list. `people.get` no mutation. So no copies needed.

Final code. Let me write it cleanly.

One more consideration on timing: to ensure the largest cases do the most work and are kept, sizes vary. Good.

Let me write the module-level data generation compactly.

I'll write:

```python
import importlib
import random

_mod = importlib.import_module('update-community-members')
render_gc = _mod.render_gc


def _make_people(usernames, seed, present=1.0, name_ratio=0.9, company_ratio=0.7,
                 term_ratio=0.7, empty_name_ratio=0.0):
    rng = random.Random(seed)
    people = {}
    for i, u in enumerate(usernames):
        if rng.random() > present:
            continue
        e = {}
        if rng.random() < name_ratio:
            if rng.random() < empty_name_ratio:
                e["name"] = ""
            else:
                e["name"] = f"Name {i}"
        if rng.random() < company_ratio:
            e["company"] = f"Company {i % 37}"
        if rng.random() < term_ratio:
            e["termEnd"] = f"20{rng.randint(20, 30)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        people[u] = e
    return people


# case 1: 100k members, everyone present with full profile
_u1 = [f"user{i}" for i in range(100_000)]
_p1 = _make_people(_u1, 0, present=1.0)

# case 2: 60k members, only 30% known
_u2 = [f"member{i}" for i in range(60_000)]
_p2 = _make_people(_u2, 1, present=0.3, name_ratio=0.5, company_ratio=0.3, term_ratio=0.3)

# case 3: 80k entries drawn from a pool of 4k usernames -> heavy duplicates
_pool3 = [f"dup{i}" for i in range(4_000)]
_p3 = _make_people(_pool3, 2, present=1.0)
_rng3 = random.Random(3)
_u3 = [_pool3[_rng3.randrange(len(_pool3))] for _ in range(80_000)]

# case 4: 40k unicode usernames, some empty names
_u4 = [f"\u7528\u6237{i}" for i in range(40_000)]
_p4 = _make_people(_u4, 4, present=0.6, name_ratio=0.9, empty_name_ratio=0.1)

# case 5: 70k members, mixed presence, plus 50k unrelated people entries
_u5 = [f"dev{i}" for i in range(70_000)]
_p5 = _make_people(_u5, 5, present=0.7, name_ratio=0.95, company_ratio=0.5, term_ratio=0.9)
for j in range(50_000):
    _p5[f"extra{j}"] = {"name": f"Extra {j}", "company": "X", "termEnd": "2030-01-01"}

# case 6: 50k members, nobody known -> display_name falls back to the username
_u6 = [f"ghost{i}" for i in range(50_000)]
_p6 = {}

# case 7: 30k members, usernames already sorted
_u7 = [f"a{i:06d}" for i in range(30_000)]
_p7 = _make_people(_u7, 7, present=0.8)

# case 8: 90k members with very long display names
_u8 = [f"long{i}" for i in range(90_000)]
_p8 = {}
for i, u in enumerate(_u8):
    _p8[u] = {"name": "N" * 100 + f" {i:06d}", "company": "C" * 40, "termEnd": "2030-01-01"}
```

Then:

```python
def _run(team, people):
    def thunk():
        _mod.teams = team
        _mod.people = people
        return ()
    return thunk


def checks():
    return [
        ("empty-team", _run({"governance-committee": []}, {})),
        ("no-key", _run({}, {})),
        ("unknown-member", _run({"governance-committee": ["nobody"]}, {})),
    ]


def cases():
    return [
        ("full-100k", _run({"governance-committee": _u1}, _p1)),
        ("sparse-60k", _run({"governance-committee": _u2}, _p2)),
        ("duplicates-80k", _run({"governance-committee": _u3}, _p3)),
        ("unicode-40k", _run({"governance-committee": _u4}, _p4)),
        ("mixed-70k", _run({"governance-committee": _u5}, _p5)),
        ("ghosts-50k", _run({"governance-committee": _u6}, _p6)),
        ("sorted-30k", _run({"governance-committee": _u7}, _p7)),
        ("longnames-90k", _run({"governance-committee": _u8}, _p8)),
    ]
```

Note `_u7` sorted: `a000000`, `a000001`, ... yes sorted.

Wait, case 7 sorted usernames but people names are `Name {i}` so display_name keys are "Name 0", "Name 1", ... which sorted by display_name is also sorted. Fine.

Hmm, one concern: `_p7` present=0.8 means 20% fall back to username `a000xxx`, which sorts before "Name ..." (uppercase N is 0x4E, 'a' is 0x61). So mixed. Fine.

Now, about the total build time: `_make_people` for 100k calls with ~4 rng calls each = 400k rng calls, ~0.3s. Case 8 builds 90k dicts ~0.1s. Case 5 extra 50k ~0.05s. Total well under 10s. Good.

Memory: _p1 100k dicts with up to 3 keys → maybe 100k * ~300 bytes = 30MB. _p5 has 120k entries → ~40MB. _p8 90k dicts → ~30MB. Total maybe 100MB+. Hmm, "Keep the data in memory under about 100 MB". Might be close. Let's reduce.

Let me trim: case 5 extra entries to 20k. Case 8 names shorter. Actually the big memory is the dicts. Let's estimate: a dict with 3 string entries ~ 184 bytes + strings. Strings maybe 60 bytes each. So ~350 bytes per person. 100k → 35MB. _p5 120k → 42MB. _p8 90k → 31MB. _p2 60k*0.3=18k → 6MB. _p3 4k → 1.4MB. _p4 24k → 8MB. _p7 24k → 8MB. Plus usernames lists: 100k+60k+80k+40k+70k+50k+30k+90k = 520k strings ~ 30MB (strings ~57 bytes each). Total ~160MB. Too much.

Hmm. Let's reduce sizes. But we need stress for timing. Trade-off: the function is cheap per element, so we need many elements for 1ms+. Actually 1ms is easy: ~10k elements gives maybe 5ms. 200ms needs ~200k. So max 100k is fine.

But memory: let's cut down. Options: reduce number of cases with huge data, and reduce sizes.

Let's reconsider: the constraint is "under about 100 MB". Let's target ~60MB total.

Revised sizes:
1. full-100k → keep? 100k usernames (5.7MB) + 100k people dicts (~35MB) = 40MB. That alone is a lot.

Maybe reduce to 60k for case 1. Hmm, but we want the most-work cases kept. Actually 4 of 8 are kept; the biggest 4 do most work. Fine.

Let me set:
1. full-60k
2. sparse-40k
3. dups-80k (pool 4k, so people small)
4. unicode-30k
5. mixed-50k + 20k extras
6. ghosts-40k (no people dicts → cheap)
7. sorted-25k
8. longnames-50k

Estimate: 
- u1 60k strings 3.4MB; p1 60k dicts ~21MB
- u2 40k 2.3MB; p2 12k dicts 4MB
- u3 80k strings 4.6MB; p3 4k dicts 1.4MB
- u4 30k 1.7MB; p4 18k dicts 6MB
- u5 50k 2.9MB; p5 35k + 20k = 55k dicts ~19MB
- u6 40k 2.3MB; p6 empty
- u7 25k 1.4MB; p7 20k dicts 7MB
- u8 50k 2.9MB; p8 50k dicts ~20MB

Total ~100MB. Still close. Hmm.

Let's reduce further. Actually dict overhead: a dict with 3 items is 184 bytes (empty dict 64, +3*... actually dict grows: 3 items → 8 slots? size 184 bytes). Plus key strings (shared with username list, so counted once? No—the key is the same string object if we use the same object; in `_make_people` we use `u` from `usernames`, so the key is the same object as in the list. Good, no duplication). Value strings: "Name 12345" ~ 60 bytes, "Company 5" ~ 58, "termEnd" ~ 60. So per person ~184 + 180 = 364 bytes. 60k → 22MB. Yes.

To get under 100MB total, let's cut case 1 to 40k and case 8 to 40k.

Actually, let's just be more conservative overall and accept that the function is fast. The requirement is 1ms-200ms per call. Let's check: 40k elements → key extraction 40k + sort + join 40k f-strings. Probably ~40-60ms. Good, well within range.

Let me set:
1. full-50k
2. sparse-40k
3. dups-80k
4. unicode-30k
5. mixed-40k + 15k extras
6. ghosts-40k
7. sorted-25k
8. longnames-40k

Estimate memory:
- p1: 50k*364 = 18MB; u1 2.9MB
- p2: 12k*364=4.4MB; u2 2.3MB
- p3: 4k → 1.5MB; u3 4.6MB
- p4: 18k → 6.5MB; u4 1.7MB
- p5: (28k+15k)=43k → 15.6MB; u5 2.9MB
- p6: 0; u6 2.3MB
- p7: 20k → 7.3MB; u7 1.4MB
- p8: 40k → 14.6MB; u8 2.3MB

Total ~88MB. Hmm still near. Let's cut p8 to 30k and p5 extras to 10k.

Actually, maybe I'm overestimating dict size. A 3-key dict in CPython 3.11: sys.getsizeof({1:1,2:2,3:3}) = 184. Yes. And strings: "Name 12345" = 49+10 = 59? sys.getsizeof("Name 12345") = 49 + 10 = 59. "Company 5" = 49+9=58. "2025-01-01" = 49+10=59. So ~176 bytes of strings. Total 360. OK.

Let's just cut sizes to be safe: max 50k, and reduce extras.

Final sizes:
1. 50k
2. 40k
3. 80k (pool 4k)
4. 30k
5. 40k + 10k extras
6. 40k
7. 25k
8. 40k

Total people dicts: 50k+12k+4k+18k+38k+0+20k+40k = 182k dicts * 360 = 65MB. Plus username strings 335k * 57 = 19MB. Total ~84MB. Hmm.

Maybe drop case 8's people to 30k and case 1 to 40k. Let's do:
1. 40k
2. 35k
3. 80k
4. 30k
5. 40k+10k
6. 40k
7. 25k
8. 35k

People dicts: 40k + 10.5k + 4k + 18k + 38k + 0 + 20k + 35k = 165k → 60MB. Strings: 40+35+80+30+40+40+25+35 = 325k → 18MB. Total ~78MB. OK-ish.

Hmm, "about 100 MB" — 78MB is fine.

Actually, wait. The timing: is 40k enough for 1ms? Let's estimate: sorting 40k items with key lookup (dict get twice per key call: display_name does people.get(username, {}).get("name", username) — two dict ops). 40k key calls ~ 5ms. Sort ~ 15ms. Join with f-string formatting 40k ~ 20ms. Total ~40ms. Good.

But the harness keeps the 4 that do most work. Fine.

Let me finalize. Actually maybe I should make case 1 the biggest at 60k to be safely above 1ms... 40k gives ~40ms, plenty.

Hmm, but I worry the function might be faster than I estimate. Even 10k gives ~10ms. Fine.

Let me finalize with these sizes and write clean code.

Actually, let me reconsider the "long names" case: names of 100 chars make string comparisons and output bigger. 35k * (100+ chars) output ~ 5MB string. Fine.

Let me write the final code.

One more detail: `_make_people` uses `f"Name {i}"` where i is the index in the usernames list. For case 3 with duplicates, pool is 4000 unique, fine.

Also for case 5, extras: 10k.

Let me write it.

Also, should I worry that `_mod.teams` assignment might conflict if `teams` is used by `render_tc`? Not called.

Final answer.

Let me also double-check the thunk signature: returns `()` → function called as `render_gc()`. Good.

Write it out.