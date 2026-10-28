Let me analyze `_build_pr_body`. It takes `repo`, `changes`, `cutoff`, `warning=None`. `changes` is iterated with `sorted(changes)` and each element unpacked as `(user, role_label, teams)`. `teams` is joined with ", ".

So `changes` is an iterable of tuples (user, role_label, teams) where teams is a list of strings.

The function is pure string building. Timing depends on the number of changes. To make it ~1ms-200ms, we need many changes. Each change produces a line. Output is a string, not a list of values — output size is a single string. The "under 100000 values" constraint — the returned string is one value. But the body could be huge. Let's keep it reasonable.

Let's build changes with varying sizes and team list lengths.

Note `sorted(changes)` — sorting a list of tuples. If teams are lists, comparing tuples with equal first elements compares role_label then teams lists. Fine as long as elements are comparable. Use strings.

To stress: large number of members, long team names, many teams per member, unicode names, duplicates? sorted handles duplicates.

Let's design 8 cases:
1. typical: 500 members, 1-3 teams each, short names.
2. large: 5000 members.
3. many teams per member: 1000 members with 20 teams each.
4. long team names / long usernames.
5. unicode names.
6. warning present.
7. all same role_label (many maintainers) — sorting stress.
8. duplicates / mixed roles.

Also `cutoff` — a date string presumably. In the repo it comes from `get_cutoff_date()`. Let's just use a string like "2024-01-01" — actually the code formats it with f-string so any object works. Use a string.

Let's compute rough timing: each line ~ 60 chars. 5000 members → 300KB string, probably a few ms. 200ms would need ~ maybe 100k members. Let's keep sizes such that one call is a few ms to tens of ms. The instruction says 1ms-200ms. Let's aim for a few ms to maybe 50ms.

Actually building strings in Python: concatenation with += in a loop is O(n) amortized-ish (CPython optimizes in-place when refcount 1). For 100k members it might be ~50ms. Let's use up to ~50k members.

Let me be careful about memory: 50k members × 20 teams = 1M strings... that's a lot. Keep teams modest.

Let me write:

```python
import importlib
import random

_mod = importlib.import_module('move-to-emeritus')
_build_pr_body = _mod._build_pr_body

ORG = "open-telemetry"

ROLES = ["Maintainer", "Approver", "Triager", "Member"]

def _changes(n, teams_lo, teams_hi, seed, role_choices=None, name_len=8, unicode_names=False):
    rng = random.Random(seed)
    if role_choices is None:
        role_choices = ROLES
    out = []
    for i in range(n):
        if unicode_names:
            user = "".join(chr(0x4e00 + rng.randrange(2000)) for _ in range(name_len))
        else:
            user = "user" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(name_len))
        role = rng.choice(role_choices)
        nt = rng.randint(teams_lo, teams_hi)
        teams = [f"team-{rng.randrange(1000)}-{rng.randrange(1000)}" for _ in range(nt)]
        out.append((user, role, teams))
    return out
```

Wait — duplicates: if user+role equal, sorting compares teams lists. Fine.

Cutoff: use a string "2024-01-01T00:00:00Z".

Cases must be distinct labels and each thunk returns a tuple of args.

Let's make 8:

1. "typical" — 200 members, 1-3 teams.
2. "large" — 20000 members, 1-3 teams.
3. "many-teams" — 2000 members, 10-25 teams.
4. "long-names" — 3000 members with long usernames and long team names.
5. "unicode" — 3000 members unicode names.
6. "with-warning" — 5000 members + warning text.
7. "same-role" — 10000 members all role "Maintainer" (sorting stress on teams).
8. "duplicates" — 5000 members with duplicated user/role combos.

Hmm, but sorting large lists of tuples is the main cost. Good.

Actually to really stress sorting, make many entries share the same user prefix. Fine.

Let me measure roughly: sorting 20000 tuples ~ maybe 20ms. Plus string building. Good.

Let me ensure each case is under 1s. 20000 members with 3 teams → fine.

For the "many-teams" case: 2000 × 25 teams = 50000 team strings. Fine.

Checks: small edge inputs:
- empty changes: `([], "2024-01-01", None)` — wait signature is (repo, changes, cutoff, warning=None). So thunk returns (repo, changes, cutoff).
- one element.
- warning=None vs warning present, maybe empty changes with warning.

Let's do:
```python
def checks():
    return [
        ("empty", lambda: ("community", [], "2024-01-01")),
        ("single", lambda: ("community", [("alice", "Maintainer", ["team-a"])], "2024-01-01")),
        ("empty-teams", lambda: ("community", [("bob", "Approver", [])], "2024-01-01", "WARNING: something")),
    ]
```

Wait warning gets stripped in the caller; here we pass raw. Fine.

Note: the function signature has warning as 4th positional. Thunk returns tuple, call with them.

Now the module import: the file is `scripts/move-to-emeritus.py`. `importlib.import_module('move-to-emeritus')` — the task says to import exactly as shown. But does the module import work? The module imports urllib etc. at top level — fine, no side effects at import? It defines functions and ORG. `main()` guarded presumably. Importing should be safe.

But wait: `importlib.import_module('move-to-emeritus')` requires scripts dir on sys.path. The task says use exactly that import. Hmm, the harness presumably sets it up. The instruction: "Import it as `_build_pr_body = importlib.import_module('move-to-emeritus')._build_pr_body`". So I'll do that.

Actually the example instruction says to use that exact line. Let me do:

```python
import importlib
_build_pr_body = importlib.import_module('move-to-emeritus')._build_pr_body
```

That's what they asked.

Now, does `_build_pr_body` reference ORG from module globals — yes, `ORG` is module-level "open-telemetry". Good, no need to set.

Let me finalize the code.

Team names: keep them realistic-ish. Real teams like "maintainers", "approvers", "triagers", "java-maintainers", etc.

Let me write helper for realistic team names.

```python
_TEAM_POOL = [
    "maintainers", "approvers", "triagers", "java-maintainers", "python-approvers",
    "collector-maintainers", "spec-approvers", "docs-maintainers", "sdk-triagers",
    "operator-approvers", "ebpf-maintainers", "profiling-approvers",
]
```

For long names case, generate long team names.

Let me write it all out.

For distinct labels — 8 distinct.

Let's also ensure the thunk returns fresh copies? The function doesn't modify changes (it uses sorted() which creates a new list). It doesn't mutate. So returning the same list each time is fine.

But `sorted(changes)` on a list of tuples with list elements — fine, no mutation.

Now writing.

Sizes: let me pick so that one call ~ a few ms to ~50ms.

- typical: 300 members, 1-3 teams
- large: 30000 members, 1-3 teams
- many-teams: 3000 members, 8-20 teams
- long-names: 5000 members, long user and team names
- unicode: 5000 members
- warning: 10000 members + warning
- same-role: 20000 members all same role, 2-5 teams
- duplicates: 8000 members with repeated users

Total build time: generating ~80k members with random — fast.

Memory: fine.

Let me write the final code.

One concern: `sorted(changes)` where changes has tuples (user, role, teams) — if two tuples have same user and role, compares lists of strings. Fine.

For unicode names, ensure they're distinct enough. Fine.

Let me write.

```python
import importlib
import random

_build_pr_body = importlib.import_module('move-to-emeritus')._build_pr_body

_ROLES = ["Maintainer", "Approver", "Triager", "Member"]
_TEAMS = [
    "maintainers", "approvers", "triagers", "java-maintainers",
    "python-approvers", "collector-maintainers", "spec-approvers",
    "docs-maintainers", "sdk-triagers", "operator-approvers",
    "ebpf-maintainers", "profiling-approvers",
]
_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"

def _gen(n, seed, teams_lo=1, teams_hi=3, roles=None, name_len=9,
         team_len=None, unicode_names=False, dup_users=False):
    rng = random.Random(seed)
    if roles is None:
        roles = _ROLES
    out = []
    for i in range(n):
        if dup_users:
            user = "user%05d" % (rng.randrange(max(1, n // 10)))
        elif unicode_names:
            user = "".join(chr(0x4e00 + rng.randrange(3000)) for _ in range(name_len))
        else:
            user = "".join(rng.choice(_ALNUM) for _ in range(name_len))
        role = rng.choice(roles)
        nt = rng.randint(teams_lo, teams_hi)
        if team_len:
            teams = ["".join(rng.choice(_ALNUM) for _ in range(team_len)) for _ in range(nt)]
        else:
            teams = [rng.choice(_TEAMS) for _ in range(nt)]
        out.append((user, role, teams))
    return out
```

Hmm for team_len long names, better to use realistic long names. Fine.

Cutoff strings: "2024-06-01T00:00:00Z".

Now cases.

I'll wrap in lambdas returning tuples.

Let me finalize.

Actually for the "long-names" case, using team_len=40 gives long team strings. Good.

Warning text: something long-ish.

Let me write final.