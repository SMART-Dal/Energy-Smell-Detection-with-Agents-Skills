The function `_build_issue_body(changes)` takes `changes` which is presumably a list of tuples (user, role_label, teams) where teams is a list/iterable of strings. It sorts changes, joins teams.

We need 8 cases with varied data. The function is pure string building, quite fast. Need inputs that take ~1ms to 200ms. Since it's just string formatting, to make it take ~1ms we need many changes. Let's think: each change produces a line. Sorting is O(n log n). To make it take meaningful time, use thousands of entries with long team names.

Let's build changes as list of tuples (user, role_label, teams) where teams is a list of strings.

Varied cases: many entries, few entries with many teams, unicode, long names, duplicates, sorted vs unsorted, etc.

Note sorted(changes) sorts tuples; comparing tuples compares user, then role_label, then teams list. Teams lists compare element-wise. Fine.

Let's write:

```python
import importlib
import random

_build_issue_body = importlib.import_module('move-to-emeritus')._build_issue_body

ROLE_LABELS = ["Triager", "Approver", "Maintainer", "Member"]

def _changes(n, teams_min, teams_max, seed, role=None, prefix="user"):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        user = f"{prefix}{rng.randrange(10**9)}"
        label = role if role else rng.choice(ROLE_LABELS)
        k = rng.randint(teams_min, teams_max)
        teams = [f"team-{rng.randrange(10**6)}-{j}" for j in range(k)]
        out.append((user, label, teams))
    return out
```

Make 8 cases of varying scale. The function is fast; a call with 20,000 entries maybe ~10ms. Let's aim for a range.

Cases:
1. empty-ish? No, checks handles small. Cases should be substantial.
1. "many-members" - 20000 entries, 1-3 teams each.
2. "wide-teams" - 2000 entries, 20-50 teams each.
3. "single-member-many-teams" - 1 entry with 5000 teams.
4. "sorted-input" - already sorted input, 15000 entries.
5. "reverse-sorted" - 15000 entries sorted descending.
6. "duplicates" - many duplicate users/labels, 15000 entries.
7. "long-names" - 5000 entries with very long usernames and team names.
8. "unicode" - 10000 entries with unicode chars.

All should run to completion. Output is a single string; keep under 100000 values? "keep what it returns under about 100 000 values" — a string is one value, but rendering... The body could be large; with 20000 entries each line ~60 chars = 1.2MB string. That's fine memory-wise. But output compared in full — okay, it's a string.

Arguments rendered before/after: changes list of 20000 tuples with teams lists — that's maybe 20000*3 values = 60000 values, under 1M. Wide teams 2000*30 = 60000. Single member 5000 teams = 5000. Fine.

Let's make sure total building under 10s — trivial.

Let's write checks: empty list, one element, maybe None-ish odd type? Function does sorted(changes) — None would raise. checks may raise. Use empty list, single element, and maybe a tuple instead of list (works since sorted accepts iterable). Or teams as a tuple. Let's do:

- ("empty", lambda: ([],))
- ("single", lambda: ([("alice", "Triager", ["team-a"])],))
- ("tuple-teams", lambda: ([("bob", "Approver", ("t1", "t2"))],))  # teams as tuple, join works

Actually teams_str = ", ".join(teams) works for tuple too.

Let's write the code.

For cases, ensure no mutation issues: function only reads and sorts (sorted returns new list). So we can reuse the same data across thunk calls. Each thunk returns the same list object; sorted() doesn't mutate. Fine.

But careful: the arguments are rendered before and after each call to see whether it changed them. sorted() doesn't change. Good.

Let me write with distinct labels.

Scale check: 20000 entries, sorted() each call ~ maybe 5-10ms. Good.

Let's finalize.

For "single-member-many-teams": 1 user with 5000 teams → string join of 5000 team names, line ~ 5000*12 = 60KB. Fine.

Unicode: usernames with non-ascii.

Let me write.

def _changes(n, tmin, tmax, seed, roles=ROLE_LABELS, prefix="u", ulen=8, tlen=8):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        user = prefix + "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(ulen))
        label = rng.choice(roles)
        k = rng.randint(tmin, tmax)
        teams = []
        for j in range(k):
            teams.append("t" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(tlen)))
        out.append((user, label, teams))
    return out

Hmm generating 20000*3 teams with per-char loops might be slowish but fine (20000*3*8 = 480k char choices). Wide teams 2000*35 = 70000 teams * 8 = 560k. Total maybe a few million char ops, under a second or two. Fine.

Better use rng.randrange for speed. Let's use f"t{rng.randrange(10**9)}". Simpler.

Let me just use random strings via rng.randrange.

I'll write helper:

def _rand_word(rng, n):
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))

Fine.

Cases:

1. many-members: _changes(20000, 1, 3, 0)
2. wide-teams: _changes(2000, 20, 40, 1)
3. huge-teams: _changes(300, 100, 200, 2)  → 300*150 = 45000 teams
4. sorted-input: sorted(_changes(15000, 1, 4, 3))
5. reverse-sorted: sorted(_changes(15000, 1, 4, 4), reverse=True)
6. duplicates: build with few distinct users/labels: many duplicates
7. long-names: _changes(5000, 2, 5, 6, ulen=60, tlen=60)
8. unicode: usernames with unicode chars

For duplicates: create 15000 entries from a small pool of users/labels/teams. Let me write a custom builder.

def _dup_changes(n, seed):
    rng = random.Random(seed)
    users = [f"user{i}" for i in range(50)]
    labels = ["Triager", "Approver", "Maintainer"]
    teams = [f"team{i}" for i in range(30)]
    out = []
    for _ in range(n):
        k = rng.randint(1, 5)
        out.append((rng.choice(users), rng.choice(labels), [rng.choice(teams) for _ in range(k)]))
    return out

Good — many duplicate tuples.

Unicode: 
def _unicode_changes(n, seed):
    rng = random.Random(seed)
    chars = "áéíóúüñç中文日本語한국어αβγδ"
    out=[]
    for _ in range(n):
        user = "".join(rng.choice(chars) for _ in range(10))
        label = rng.choice(ROLE_LABELS)
        k = rng.randint(1,4)
        teams = ["".join(rng.choice(chars) for _ in range(8)) for _ in range(k)]
        out.append((user, label, teams))
    return out

n=8000.

OK. Write it.

Total output string sizes: case 3: 300 lines with ~150 teams each * ~12 chars = 540KB. Fine.

All good.