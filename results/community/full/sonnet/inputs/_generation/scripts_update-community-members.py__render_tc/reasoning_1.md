Let me analyze the function.

`render_tc()` takes no arguments. It reads module globals `teams` and `people`. `teams = metadata.get("teams", {})` — module-level, derived from metadata. `people` is also a module global presumably.

The function sorts `teams.get("technical-committee", [])` by `display_name`, then joins.

Since the function takes no arguments, all inputs must be set via module globals. We need to set `teams` and `people` on the repository's module.

Wait — but the thunk returns the arguments for the function. `render_tc()` takes no arguments, so thunk returns `()`. But we need each case to make the function do different work — which means changing the module globals `teams` and `people` between cases. Since thunks run before timing, we can set globals in the thunk.

But careful: "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next". render_tc doesn't change globals. Good.

So each thunk sets the module globals and returns `()`.

Let's figure out the module import. The file is `scripts/update-community-members.py`. Import it as `importlib.import_module('update-community-members')`. Hmm, but the module path... The task says import it as `render_tc = importlib.import_module('update-community-members').render_tc`. So we do:

```python
import importlib
_mod = importlib.import_module('update-community-members')
```

But wait, does the module execute code at import time that requires things? Let's think: it defines `teams = metadata.get("teams", {})`. `metadata` must be defined earlier. Let's think about the module top-level code. It imports subprocess, sys, yaml. Probably reads some file. Actually `metadata` — where does it come from? Maybe it does `metadata = yaml.safe_load(...)`. Hmm.

The task says everything we can know about the repository is in the task. We're told the imports and definitions. But there's `metadata` and `people` globals used. We don't see how they're defined. Hmm.

Actually the task says: "Module globals the function reads must be set on the repository's own module". So we set `_mod.teams` and `_mod.people`.

But if importing the module runs code that reads a file or does network... The module has `subprocess` import and does `splice`. Let's think: typical update script reads MARKDOWN_FILE. But that's under `if __name__ == "__main__"` probably? Actually line 67 is inside... The call site shows top-level-ish code. Hmm, but likely guarded by `if __name__ == "__main__":`. We can't know.

Let me think about what's safe. The import may fail if the module executes something requiring files. But we have no choice — we must import it. Actually the task explicitly tells us to import it that way, so presumably it works.

Hmm, but `metadata` and `people` — the module must define them somehow. Possibly:

```python
MARKDOWN_FILE = ...
with open(...) as f:
    ...
metadata = yaml.safe_load(...)
people = metadata.get("people", {})
teams = metadata.get("teams", {})
```

We don't know. But the key point: we set `_mod.teams` and `_mod.people` in thunks.

Wait, but the function `render_tc` references `teams` and `people` as module globals — actually it references `teams` and `people` at call time from the module namespace. So setting `_mod.teams = {...}` and `_mod.people = {...}` works.

Actually wait, `display_name` and `company` also reference `people` from the module globals. So setting `_mod.people` works for them too.

Now the sys.path: to import `update-community-members`, the directory `scripts/` must be on sys.path. The task says "Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk." Hmm. Actually importlib.import_module searches sys.path. We may need to add the scripts dir. But we don't know the repo layout. The task says import it as given, so presumably the harness has set it up. Let's just try `importlib.import_module('update-community-members')`. Hmm, but if it fails...

Actually, maybe safer to add the scripts directory. But we don't know where the repo is. We could search sys.path? Hmm.

Let's keep it simple and trust the task. Actually, I could make it robust: try import, and if it fails, find the file. But we don't know the repo root. Hmm.

Let me just do:

```python
import importlib
import os
import sys

try:
    _mod = importlib.import_module('update-community-members')
except ModuleNotFoundError:
    # add candidate directories
    ...
```

That's risky and might be seen as faking. Let's just do the direct import as instructed.

Now design the cases.

The function: sorts usernames by display_name (which is people[username]['name'] or username), then for each: `- [name](https://github.com/u), company`.

Work: sorting n usernames, each comparison calls display_name which does dict lookups. So n up to large.

Each case sets `_mod.teams = {"technical-committee": [...usernames...]}` and `_mod.people = {...}`.

To make it substantial: n = 50,000 usernames with people entries. Sorting 50k strings by key ~ maybe 30-50 ms. Good.

Need diversity: different sizes, different people coverage (some usernames not in people -> fallback), different name distributions, duplicates, etc.

Also "different paths through its code": the fallback branches in display_name and company.

Also note: sorted() with key=display_name — display_name called n times, then comparisons are on the returned strings. So it's O(n log n) string comparisons plus O(n) dict lookups.

Now, the output: a string of n lines. "keep what it returns ... under about 100 000 values" — n up to maybe 100k lines is fine but let's keep under. Actually 100k values — n=50k lines, each line ~ 1 value? Probably fine. Let's cap n at 60k.

Let me design 8 cases:

1. "empty-teams" — no technical-committee key. teams = {}. Output empty string. Hmm that's tiny work; but we need 8 measured, top 4 kept. Small ones are fine as long as they don't dominate. Actually they said each case should do substantial work. But having a couple small is okay? "Define a real workload" and "Each case should make the function do substantial and different work". Let's make most substantial. But we need 8; the harness keeps top 4 by work. Let's make all reasonably big but diverse.

Let me think about realistic: the community repo's technical committee list is small in reality (like 10-20 people). But for stress we scale up.

Let's define generator helpers.

Plan:

```python
import importlib
import random

_mod = importlib.import_module('update-community-members')
render_tc = _mod.render_tc
```

Wait, but the task says import it as `render_tc = importlib.import_module('update-community-members').render_tc`. So we define `render_tc`. But the thunk returns args, and the harness calls the function. Actually the harness calls the function under test which is `render_tc`? The thunk returns positional args for the function. Since render_tc takes no args, thunk returns `()`.

Hmm, but how does the harness know which function? It's given by the task: `render_tc`. We just write checks/cases.

But wait — the harness needs `render_tc` accessible? Probably it imports it itself. We just define checks and cases. The instruction says "Import the repository's modules exactly as shown in the task." So we should import it to set globals.

Now, cases: each thunk sets `_mod.teams` and `_mod.people` then returns `()`.

But careful: since all 8 cases share the module globals, and the thunk sets them right before the timed call, that's fine — each case's thunk runs then the call is timed. Thunks for all cases might be run... Actually the harness probably runs each case: build args (thunk), call function, compare. Repeated many times. So the thunk sets the globals each time. Good.

But there's a subtlety: "We run them on the original function and keep the 4 that do the most work." Fine.

Now, generation must be at module level (build data once) and thunks just assign and return. Assigning dicts is cheap.

Let me write generators:

```python
def _make(n, seed, people_ratio=1.0, name_style="normal", companies=True, dup=False):
    rng = random.Random(seed)
    usernames = []
    people = {}
    for i in range(n):
        u = f"user{i}"
        usernames.append(u)
        if rng.random() < people_ratio:
            entry = {}
            if name_style == "normal":
                entry["name"] = f"{rng.choice(['Alice','Bob','Carol'])} {rng.randrange(10**6)}"
            elif name_style == "prefix":
                entry["name"] = "z" * rng.randint(0, 30) + f"{i}"
            elif name_style == "unicode":
                entry["name"] = "".join(rng.choice("áéíóúñçß漢字") for _ in range(rng.randint(1,10)))
            elif name_style == "none":
                pass  # no name -> fallback to username
            if companies and rng.random() < 0.8:
                entry["company"] = f"Company {rng.randrange(1000)}"
            people[u] = entry
    ...
```

Hmm, this is getting complex. Let me simplify but keep diversity.

Key diversity axes:
- n (size)
- ratio of usernames present in people
- ratio with 'name' key present
- ratio with 'company' key present
- duplicates in the list
- name strings that are long / share prefixes (sorting cost)
- unicode names

Let me write a builder:

```python
def _build(n, seed, present=1.0, named=1.0, with_company=0.7, name_len=8, prefix_len=0, dup=0, unicode_names=False):
    rng = random.Random(seed)
    people = {}
    usernames = []
    for i in range(n):
        u = f"member{i:07d}"
        usernames.append(u)
        if rng.random() < present:
            entry = {}
            if rng.random() < named:
                if unicode_names:
                    entry["name"] = "".join(rng.choice(_UNI) for _ in range(rng.randint(1, 12)))
                else:
                    entry["name"] = "a"*prefix_len + f"{rng.randrange(10**name_len):0{name_len}d}"
            if rng.random() < with_company:
                entry["company"] = f"Corp {rng.randrange(10**5):05d}"
            people[u] = entry
    # duplicates
    if dup:
        extra = [usernames[rng.randrange(n)] for _ in range(dup)]
        usernames.extend(extra)
    return usernames, people
```

Hmm, duplicates: sorted with duplicates — the key function called for each duplicate too. That's fine.

Actually let me make names that force many comparisons. Strings with common prefix. Sorting cost is dominated by comparisons. Using random numbers as names means comparisons resolve quickly. Long common prefixes make comparisons slower. Let's include that.

Now cases:

1. ("no-tc-key", teams={}) — small, but empty. Actually should we include? It's a valid path (teams.get default). Output "". Small work. Keep as one of 8 but it'll be dropped from top 4 probably. Hmm, but "Each case should make the function do substantial and different work". Let's instead make 8 substantial ones. But we also want edge coverage. checks() handles small ones.

Actually checks() is only 2-3 small inputs checked for identical behaviour, never measured. Good place for empty/None edge cases. But wait — checks may raise. And they're compared between original and modified. Fine.

Let me put in checks:
- teams missing technical-committee: teams={} -> returns "".
- usernames is None? teams = {"technical-committee": None} -> sorted(None) raises TypeError. Good edge case that raises.
- Actually the task says checks may raise. Fine.

Hmm, but if it raises in the original, does the modified also raise? Presumably. Good.

Let's do checks:
```python
def checks():
    return [
        ("no-teams", lambda: (_set_globals({}, {}),)),
        ("empty-list", lambda: (_set_globals({"technical-committee": []}, {}),)),
        ("none-list", lambda: (_set_globals({"technical-committee": None}, {}),)),
    ]
```

Wait, thunks must return tuple of args. `_set_globals(...)` returns None, so `(None,)` would be one positional arg None. That's wrong — render_tc takes no args. So thunk should return `()`.

So: `lambda: (_set_globals(...), )` gives a 1-tuple containing None. Bad.

Better: define a helper that sets globals and returns `()`:

```python
def _case(teams, people):
    _mod.teams = teams
    _mod.people = people
    return ()
```

Then `lambda: _case({}, {})`.

That works. Thunk returns `()`, no args.

But careful: `_case` sets globals and returns empty tuple. Good.

For cases, we pre-build (usernames, people) at module level, then thunk: `lambda: _case({"technical-committee": U}, P)`.

Note the dict construction each call is cheap.

Now, is there a concern that the harness renders arguments before/after each call? Since args are `()`, nothing. Fine.

Now: does render_tc mutate anything? No.

Now the sorting key: `sorted(usernames, key=display_name)`. display_name uses `people`. Good.

Now let's build 8 cases.

Let me define module-level data:

```python
_U = "aàáâäçèéêëìíîïñòóôöùúûüß漢字"
```

Cases:

1. small-ish realistic: n=5000, all present, all named, companies. 
2. large: n=60000, present=0.9.
3. many missing people entries: n=40000, present=0.3 -> many fallback to username.
4. no names: n=30000, named=0.0 -> all fallback names.
5. heavy duplicates: n=20000 with dup=20000.
6. long common prefix names: prefix_len=60, n=30000.
7. unicode names: n=30000.
8. sparse companies: n=40000, with_company=0.05.

That's 8. All substantial except maybe #1.

Actually let's reconsider "different paths": display_name has `.get(username, {}).get("name", username)` — branches: username missing, name missing. company: `.get(username, {}).get("company", "")` — branches.

Good coverage.

Let me make sure each case's output is under 100k values: n up to 60k lines -> 60k strings, fine. Actually the join returns one string. "under about 100 000 values" — fine.

Input data under 1,000,000 values: 60k usernames + people dict ~ 60k entries. Fine.

Memory: 60k * small = a few MB. Fine.

Time: sorting 60k strings with key -> maybe 40 ms. Good, under 1s.

Let me write the code.

```python
import importlib
import random

_mod = importlib.import_module('update-community-members')

_UNI = "aàáâäçèéêëìíîïñòóôöùúûüß漢字"


def _build(n, seed, present=1.0, named=1.0, with_company=0.7,
           prefix_len=0, digits=7, dup=0, unicode_names=False):
    rng = random.Random(seed)
    people = {}
    usernames = []
    for i in range(n):
        u = f"member{i:07d}"
        usernames.append(u)
        if rng.random() < present:
            entry = {}
            if rng.random() < named:
                if unicode_names:
                    entry["name"] = "".join(rng.choice(_UNI) for _ in range(rng.randint(1, 12)))
                else:
                    entry["name"] = "a" * prefix_len + f"{rng.randrange(10 ** digits):0{digits}d}"
            if rng.random() < with_company:
                entry["company"] = f"Corp {rng.randrange(10 ** 5):05d}"
            people[u] = entry
    if dup:
        for _ in range(dup):
            usernames.append(usernames[rng.randrange(n)])
    return usernames, people


def _case(usernames, people):
    _mod.teams = {"technical-committee": usernames}
    _mod.people = people
    return ()


def _case_teams(teams, people):
    _mod.teams = teams
    _mod.people = people
    return ()
```

Then cases built at module level:

```python
_C1 = _build(5000, 0, ...)
```

Hmm, but building at module level for 8 cases, total maybe 250k iterations — fast, under 10s. Good.

But wait — if we build at module level, then each case thunk just references the data. Good.

Let me write cases():

```python
def cases():
    u1, p1 = _build(5000, 0, present=1.0, named=1.0, with_company=0.9)
    u2, p2 = _build(60000, 1, present=0.95, named=1.0, with_company=0.8)
    u3, p3 = _build(40000, 2, present=0.3, named=0.8, with_company=0.5)
    u4, p4 = _build(30000, 3, present=1.0, named=0.0, with_company=0.7)
    u5, p5 = _build(20000, 4, present=0.9, named=0.9, with_company=0.6, dup=20000)
    u6, p6 = _build(30000, 5, present=1.0, named=1.0, with_company=0.4, prefix_len=60)
    u7, p7 = _build(30000, 6, present=1.0, named=1.0, with_company=0.5, unicode_names=True)
    u8, p8 = _build(40000, 7, present=0.7, named=0.6, with_company=0.05)

    return [
        ("typical", lambda: _case(u1, p1)),
        ("large", lambda: _case(u2, p2)),
        ("many-missing", lambda: _case(u3, p3)),
        ("no-names", lambda: _case(u4, p4)),
        ("duplicates", lambda: _case(u5, p5)),
        ("long-prefixes", lambda: _case(u6, p6)),
        ("unicode-names", lambda: _case(u7, p7)),
        ("sparse-companies", lambda: _case(u8, p8)),
    ]
```

But building in cases() means it's called once — fine, that's setup not timed. Actually cases() is called once by the harness to get the list. The build happens there. But the instruction says "build large data once, in module-level code". Building inside cases() is also fine since cases() is called once. But to be safe, module-level. Hmm, "in module-level code or in the thunk". cases() body is neither exactly... but it's not timed. I'll put builds at module level to be safe.

Actually, careful: the thunks capture u1, p1 etc. If built at module level, fine.

Let me put them at module level.

Now, one issue: the module `update-community-members` — at import time it might do something. Let me think. It imports subprocess, sys, yaml. Probably at the bottom:

```python
if __name__ == "__main__":
    ...
```

Since we import it as a module (name "update-community-members"), `__name__` is "update-community-members", not "__main__", so the main block won't run. Good.

But `metadata`, `people`, `teams` — these must be defined at module level before use. Actually `teams = metadata.get("teams", {})` is at module level. So `metadata` is defined above. Where from? Possibly:

```python
with open('data/community-members.yaml') as f:
    metadata = yaml.safe_load(f)
```

Hmm. If so, importing the module would fail if the file doesn't exist! We might need to create it under WORKDIR... but we don't know the path.

Hmm. The task says "Everything you can know about the repository is in the task". The imports and definitions are given. We're not shown how metadata/people are loaded. So maybe the module does something like:

Actually, maybe the script reads from a URL or from the markdown file. The call site shows:

```python
with open(MARKDOWN_FILE, encoding="utf-8") as f:
    original = f.read()
```

This is at line 67, presumably in `main()` or in `if __name__ == "__main__"`. Actually the call site says `# scripts/update-community-members.py:67`. That's inside the script's main flow.

Given uncertainty, the safest approach: import the module and hope it works. If it doesn't, we can't run. But the task expects us to write code. Let's assume the module imports cleanly (perhaps metadata is loaded from a file that... hmm).

Actually, maybe the module fetches data via `subprocess` (gh api?) or via network. The imports include `subprocess`. Hmm, that could be a problem: "A function whose work starts with a request to a server ... cannot run here". But `render_tc` itself doesn't make requests. The module import might.

Hmm. But the task says to import it. Let's think about what's likely: community repo (cncf/community?), scripts/update-community-members.py. It probably runs `gh api` to get members. But `render_tc` just renders from `teams` and `people` globals.

If the module-level code does network at import, importing fails. But the task explicitly instructs the import form, so presumably it's importable. Maybe metadata is loaded lazily or from a local file.

Hmm, but actually maybe the module defines `metadata` from a local YAML that exists in the repo... We can't create it without knowing the path.

Alternatively maybe the module is written so that `metadata` is a global set in main. But `teams = metadata.get(...)` at module level would fail if metadata undefined at import.

Wait, maybe the structure is:

```python
metadata = {}
people = {}
teams = metadata.get("teams", {})

def display_name(...):
    ...
```

i.e., metadata initialized empty at module level, and filled in main. That would import cleanly! And `teams` would be {} initially. Then main sets `metadata`, `people`, `teams` from fetched data.

That's plausible and makes the module importable without network. Actually `teams = metadata.get("teams", {})` computed at import time with metadata={} gives teams={}. Then main would reassign `teams`. Hmm, but then `render_tc` uses global `teams` which main reassigns. Plausible.

Actually more likely, the module has a function that fetches and assigns globals. Whatever.

Given the task says to import it as shown, I'll do exactly that. If it needs network, we'd say CANNOT RUN. But the task wouldn't ask us to write code then... Actually the task says "If the function cannot run here at all -- it needs network access..." But render_tc itself doesn't. The import might. Hmm.

I think the intended answer is to set the globals and write cases. Let's go with it.

But to be robust against import-time network, hmm. I can't do much. Let's just import.

Actually, one more consideration: `importlib.import_module('update-community-members')` requires the scripts directory on sys.path. The task shows exactly this import, implying the harness adds scripts/ to sys.path (or runs from there). I'll add the scripts dir to sys.path if needed... but I don't know the path.

Hmm, could I locate it? Maybe via the module `update-community-members` isn't findable. The harness presumably handles it. I'll just do the import as instructed.

Actually, let me add a fallback: search sys.path and also try to find the file relative to cwd. But that might be overengineering. Let me just do the direct import.

Hmm, but wait. There's a subtlety: if the harness imports the module itself for the function under test, then the module is already in sys.modules, and our import returns the same module. Good — setting globals on it affects the function. Yes, `importlib.import_module` returns the cached module. 

Now, one concern: `_mod.teams` — the function `render_tc` reads global `teams` in its module namespace. Setting `_mod.teams` works.

But `display_name` reads `people` global. Setting `_mod.people` works.

Great.

Now checks():

```python
def checks():
    return [
        ("no-teams-key", lambda: _case_teams({}, {})),
        ("empty-tc", lambda: _case_teams({"technical-committee": []}, {})),
        ("tc-none", lambda: _case_teams({"technical-committee": None}, {})),
    ]
```

Hmm, "tc-none" raises TypeError in sorted. Original and modified both raise? Presumably. But if the modified version changes behavior... The harness compares. If original raises and modified doesn't, it's a difference. But we can't know. It's fine as an edge check.

Actually, maybe safer to avoid raising cases that might differ. But the task allows raising. Let's keep it — it tests an odd type.

Actually, hmm, "None" as the tc list: `sorted(None)` raises TypeError. But wait, `teams.get("technical-committee", [])` returns None (key present with None value). Then sorted(None) -> TypeError. Yes.

Let me include it.

Also maybe a check with a people entry having non-dict? Nah.

Now, let me reconsider: the function signature is `render_tc()` — no args. The thunk returns `()`. Good.

Let me also double check: "Its arguments are rendered before and after each call" — args are empty tuple, fine.

Now let me think about whether `_case` being called in the thunk, which sets globals, could interfere with the harness's rendering. No.

One more: the harness runs each case many times. Each thunk call sets globals. Fine.

Let me finalize the code.

Also should I worry about `people` dict values being shared/mutated? No mutation.

Let me reconsider case diversity for "different paths". In `display_name`: `people.get(username, {}).get("name", username)`. For usernames not in people -> returns username. For usernames in people without "name" -> returns username. For with name -> name.

In `company`: `people.get(username, {}).get("company", "")`.

So the "present" ratio and "named" ratio control branches. Good.

Also duplicates: sorted is stable; duplicates don't change output much but add work.

Let me now also think: does `sorted` with key call the key function once per element (yes, decorate-sort-undecorate). So display_name called n times. The comparison cost depends on name strings. Long prefixes make comparisons slower. Good.

Now writing final code.

```python
import importlib
import random

render_tc = importlib.import_module('update-community-members').render_tc
_mod = importlib.import_module('update-community-members')
```

Better to import once:

```python
_mod = importlib.import_module('update-community-members')
render_tc = _mod.render_tc
```

Now, careful: `_mod.teams` and `_mod.people` are set by our thunks. But at import time they're whatever.

Let me write it.

Actually, wait: should I worry that the module name with a hyphen can't be imported by `import` statement but importlib handles it fine. Yes.

Let me write the final.

One more thought on scale: 60000 elements sorted — Python's sorted with key: maybe 30-50ms. Fine.

Let me double check memory: 60000 usernames strings + people dict with 60000 entries each a small dict -> maybe 30-50 MB? Each dict entry ~ 200 bytes -> 12 MB, plus strings. Should be under 100MB. Let's be a bit conservative: reduce the largest to 50000. Actually fine.

Let me total the data across all 8 cases: 5000+60000+40000+30000+40000(with dup 20000 -> 40000 usernames)+30000+30000+40000 = ~315k usernames, plus people dicts ~ 275k entries. That's maybe 100+ MB total across all cases! Hmm, the limit says "Keep the data in memory under about 100 MB". That's total presumably.

Let me reduce. Total people entries should be smaller. Let's use:

- c1: 4000
- c2: 50000
- c3: 30000
- c4: 25000
- c5: 15000 + 15000 dup
- c6: 25000
- c7: 25000
- c8: 30000

Total people entries ~ 190k. Each entry: dict with 1-2 keys, plus strings. A small dict ~ 184 bytes empty, with 2 items ~ 184+... Let's say ~250 bytes. 190k * 250 = 47 MB. Plus username strings: each ~ 60 bytes * 200k = 12 MB. Plus name strings ~ 50 bytes * 150k = 7 MB. So ~70 MB. Borderline. Hmm.

Actually the 100MB limit is per-input? "Keep the data in memory under about 100 MB" — ambiguous, probably per input or total. Let's aim to keep total modest. Reduce further:

- c2: 40000
- c3: 25000
- c4: 20000
- c5: 12000 + 12000
- c6: 20000
- c7: 20000
- c8: 25000

Total ~ 186k usernames, people entries ~ 165k. ~60 MB. Acceptable.

Hmm, actually dicts in Python: a dict with 2 keys uses ~184 bytes for the dict object plus the keys/values strings. For people entries, keys "name"/"company" are interned? No, they're constants shared (same string object since we use literals — actually "name" literal is the same object across iterations due to interning of string literals? String literals in code are interned; the literal "name" evaluates to the same object each time). Values are new strings.

So each entry dict: 184 bytes (2-key dict... actually a dict with 2 entries: sys.getsizeof ~ 184). Plus value strings ~ 50-60 bytes each. So ~250-300 bytes per entry. 165k * 280 = 46 MB. Plus outer people dict with 165k entries: 165k * ~100 bytes = 16 MB. Plus usernames list 186k * 8 bytes pointers + strings 186k * 60 = 11 MB. Total ~75 MB. Hmm.

Maybe reduce a bit more. Let's cut c2 to 35000, others similar. Or accept ~75MB. The guidance says "under about 100 MB" so 75 is fine. But there are also 8 separate datasets. Let's keep it moderate.

Actually, we could reuse... no, each case needs its own.

Let me settle:

- c1 typical: n=4000
- c2 large: n=40000
- c3 many-missing: n=25000
- c4 no-names: n=20000
- c5 duplicates: n=12000, dup=12000
- c6 long-prefixes: n=20000
- c7 unicode: n=20000
- c8 sparse-companies: n=25000

Total people entries ≈ 4000+40000*0.95+25000*0.3+20000*1+12000*0.9+20000+20000+25000*0.7 ≈ 4000+38000+7500+20000+10800+20000+20000+17500 = 137800. ~40 MB. Good.

Time per call: c2 40000 -> ~25ms. Fine.

Alright.

Now name lengths: digits=7 gives names like "a0000000" (with prefix). Fine.

For unicode_names, the names are short random unicode. Sorting cost similar.

Let me finalize.

Also need to make sure `random.Random(0)` fixed seed — yes we use seeds 0..7.

Let me write the final code block.

```python
import importlib
import random

_mod = importlib.import_module('update-community-members')
render_tc = _mod.render_tc

_UNI = "aàáâäçèéêëìíîïñòóôöùúûüß漢字"


def _build(n, seed, present=1.0, named=1.0, with_company=0.7,
           prefix_len=0, digits=7, dup=0, unicode_names=False):
    rng = random.Random(seed)
    people = {}
    usernames = []
    for i in range(n):
        u = f"member{i:07d}"
        usernames.append(u)
        if rng.random() < present:
            entry = {}
            if rng.random() < named:
                if unicode_names:
                    entry["name"] = "".join(rng.choice(_UNI) for _ in range(rng.randint(1, 12)))
                else:
                    entry["name"] = "a" * prefix_len + f"{rng.randrange(10 ** digits):0{digits}d}"
            if rng.random() < with_company:
                entry["company"] = f"Corp {rng.randrange(10 ** 5):05d}"
            people[u] = entry
    if dup:
        for _ in range(dup):
            usernames.append(usernames[rng.randrange(n)])
    return usernames, people


_C1 = _build(4000, 0, present=1.0, named=1.0, with_company=0.9)
_C2 = _build(40000, 1, present=0.95, named=1.0, with_company=0.8)
_C3 = _build(25000, 2, present=0.3, named=0.8, with_company=0.5)
_C4 = _build(20000, 3, present=1.0, named=0.0, with_company=0.7)
_C5 = _build(12000, 4, present=0.9, named=0.9, with_company=0.6, dup=12000)
_C6 = _build(20000, 5, present=1.0, named=1.0, with_company=0.4, prefix_len=60)
_C7 = _build(20000, 6, present=1.0, named=1.0, with_company=0.5, unicode_names=True)
_C8 = _build(25000, 7, present=0.7, named=0.6, with_company=0.05)


def _use(usernames, people):
    _mod.teams = {"technical-committee": usernames}
    _mod.people = people
    return ()


def _use_teams(teams, people):
    _mod.teams = teams
    _mod.people = people
    return ()


def checks():
    return [
        ("no-teams-key", lambda: _use_teams({}, {})),
        ("empty-tc", lambda: _use_teams({"technical-committee": []}, {})),
        ("tc-none", lambda: _use_teams({"technical-committee": None}, {})),
    ]


def cases():
    return [
        ("typical", lambda: _use(_C1[0], _C1[1])),
        ...
    ]
```

Wait, the checks: `_use_teams` sets teams to a dict without "technical-committee" -> render_tc returns "". Good.

But careful: checks run against both original and modified. If they raise, both should raise identically.

Hmm, "tc-none" raises TypeError. Fine.

Now, one concern: after checks run, the module globals are left in some state. Then cases run and set them again. Fine.

Another concern: the harness might run checks and cases interleaved. Each thunk sets globals. Fine.

Let me also consider: the harness may run the function multiple times per case and compare outputs across runs. Our globals are stable within a case (same data). Good.

Now, will `_mod.teams` assignment be visible? Yes.

Edge: `people` might be used by other module code... irrelevant.

Let me write the final.

Actually, one thing: `render_tc` might be defined to reference `teams` global; assigning `_mod.teams` rebinds the module global. Good.

Also note: `display_name` and `company` reference `people`. Good.

Final answer.