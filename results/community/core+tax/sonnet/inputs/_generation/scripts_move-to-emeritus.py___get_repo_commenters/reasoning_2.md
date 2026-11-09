Let me finalize the approach: file:// URLs with query in the filename, unique repo per thunk call to defeat the cache, plus clearing the cache.

Wait, actually — careful with unique repo + hardlink: the file name must match exactly what url2pathname produces. Let's write both variants anyway.

Hmm, but with hardlinks I'd need both variants as templates. Let's just write the content twice (write_bytes twice) — simpler, and it's module-level setup done once per case... no wait, per thunk call we hardlink, not write. For each case we pre-write a template file for both name variants, then hardlink per call.

Hmm, actually simpler: since the filename (including query) is the same for all calls within a case (repo changes, cutoff fixed → query same), the filename is the same but the directory differs (repo). So per thunk call: mkdir the repo dir, hardlink template → dir/fname (both variants).

Let me now write it.

Also: for a case, the repo prefix must be unique across the whole run — use a counter with a case-specific prefix.

Also careful: repo names go into html_url and issue_url inside the JSON content, but content is shared across calls, so it references the template's repo name, not the actual one. Does that matter? The function computes `number` from issue_url (parsed) and `is_pr` from html_url — neither depends on the repo name matching. The result dict is keyed by user. So fine.

Let me now write the JSON content generation.

```python
def _mk_comment(rng, user, created, number, is_pr, repo):
    seg = "pull" if is_pr else "issues"
    return {
        "created_at": created,
        "user": ({"login": user} if user is not None else None),
        "html_url": f"https://github.com/{ORG}/{repo}/{seg}/{number}#issuecomment-{...}",
        "issue_url": f"https://api.github.com/repos/{ORG}/{repo}/issues/{number}",
    }
```

Now the 8 cases. Let me write a generator function per case that returns a list of comment dicts.

I'll create a helper:

```python
def _build(n, n_users, pr_ratio, issue_span, dup_ratio, seed, users_override=None, ...):
```

Too many knobs. Let me write each case explicitly with a seed. Keep it readable.

Common: cutoff = "2024-01-01"; created dates in 2024-02..2024-06.

Let me define a `_case_comments(name, n, users, ...)`. Simpler: write a function `_gen(...)` with parameters:

```python
def _gen(n, users, seed, pr_ratio=0.5, span=5000, dup=0.0, bad_user=False, no_issue_url=False, cutoff=None):
```

Hmm. Let me just write straightforward code.

Design of each case:

Case A "typical-mixed": n=20000, 1000 users, 5000 issue numbers, pr_ratio 0.5, dup 0.2.
Case B "many-prs-one-user": n=4000, 3 users? Let's do 1 user with 2000 distinct PR numbers and 2000 duplicates... Actually for the quadratic: 1 user, 3000 distinct PR numbers + repeat pattern.

Hmm, let me carefully craft the quadratic one: one user "power_user", 4000 comments, each comment a distinct PR number (1..4000). The pr list grows to 4000 → membership checks: sum_{k=1}^{4000} k = 8M comparisons. With ints, `x in list` — CPython's list contains uses PyObject_RichCompare with Py_EQ, which for ints uses the identity shortcut first (only for small ints up to 256 cached... actually the identity check happens in `PyObject_RichCompareBool`: if v is w, return equal). Numbers 1..4000 are not all cached (only ≤256). So real comparisons ~ 8M * ~20ns = 0.16s. Hmm, too slow maybe. Let's use 2000 → 2M comparisons → ~40ms. Plus JSON parsing. OK.

Hmm, actually, `number not in commenters[user][kind]` — also each append. Let's use 2000 distinct numbers for one user, ~2000 comments. Then add another 2000 comments from the same user alternating pr/issue... Let's keep it simpler: n=3000, 1 user, 3000 distinct PR numbers.

Hmm, I want each case to have meaningful work. Let's think about the biggest cost: JSON parse dominates for large n. With n=20000, parse ~40ms, loop ~30ms. Fine.

Case list (8):

1. "mixed-typical": 20,000 comments, 800 users, 4000 distinct numbers, pr_ratio 0.5, 15% exact duplicates.
2. "one-user-many-prs": 3,000 comments, 1 user, 2,500 distinct PR numbers, ~500 dups → quadratic.
3. "issues-only": 15,000 comments, 500 users, all issues, 3,000 numbers.
4. "prs-only": 15,000 comments, 500 users, all PRs.
5. "many-users": 25,000 comments, 20,000 distinct users, each 1 comment (thin entries) — tests setdefault with many keys.
6. "no-user-skip": 12,000 comments, 60% with null user or missing login → `continue` path; rest with users.
7. "no-issue-url": 12,000 comments, half with empty issue_url (number=0 → no append), half normal.
8. "early-cutoff": 8,000 comments sorted desc, first 1,500 in range then one older than cutoff → early return (partial). Actually make the cutoff such that many are older... e.g. the first comment processed is older than cutoff → immediate return with {} (tiny work). Better: 5,000 in-range then 3,000 older → the early return happens at comment 5001. Work = parse 8,000 comments + process 5,000.

Hmm, but the early-return also returns with cache set. Good.

Wait — careful with case 8: the function returns at the first comment with created < cutoff. Since we sort descending, the older ones come last. Fine.

Also all cases must run to completion without raising.

Let's also add diversity in the duplicate dedup and the "kind" mixing.

Now sizes: keep JSON under ~10 MB. 25,000 comments * ~230 bytes = 6 MB. OK.

One call time: parse 6 MB JSON ≈ 50 ms, loop 25k ≈ 40 ms → ~100 ms. Under 1s. Good.

Now let me write the comment generation.

```python
_USERS = [f"user{i:05d}" for i in range(20000)]
```

I'll generate users on the fly with f-strings.

Let me write a helper:

```python
def _make(n, seed, user_fn, number_fn, pr_fn, created_fn, bad_user_fn=None, empty_issue_fn=None):
```
Too abstract. Let me just write each case with a loop using an rng.

```python
def _comment(user, created, number, is_pr, repo, idx):
    seg = "pull" if is_pr else "issues"
    return {
        "created_at": created,
        "user": None if user is None else {"login": user},
        "html_url": f"https://github.com/{ORG}/{repo}/{seg}/{number}#issuecomment-{idx}",
        "issue_url": (f"https://api.github.com/repos/{ORG}/{repo}/issues/{number}" if number else ""),
    }
```

Now cases:

Case 1:
```python
def _case1():
    rng = random.Random(1)
    repo = "otel-mixed"
    nums = list(range(1000, 1000 + 4000))
    out = []
    prev = []
    for i in range(20000):
        if prev and rng.random() < 0.15:
            user, num, is_pr = prev[rng.randrange(len(prev))]
        else:
            user = f"user{rng.randrange(800):04d}"
            num = nums[rng.randrange(len(nums))]
            is_pr = rng.random() < 0.5
            prev.append((user, num, is_pr))
        created = f"2024-{rng.randint(2,6):02d}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z"
        out.append(_comment(user, created, num, is_pr, repo, i))
    return repo, "2024-01-01", out
```

Hmm, sorted desc isn't required except for case 8.

OK. Let me be careful about total build time: generating 25k dicts + json.dumps is fast (<0.2s).

Now, hardlink/write both filename variants.

Let me write:

```python
def _register(repo, cutoff, comments):
    data = json.dumps(comments).encode()
    qs = urllib.parse.urlencode(_params(cutoff))
    base = _BASE / "repos" / ORG / repo / "issues"
    base.mkdir(parents=True, exist_ok=True)
    names = {"comments?" + qs, "comments?" + urllib.parse.unquote(qs)}
    paths = []
    for nm in names:
        p = base / nm
        p.write_bytes(data)
        paths.append(p)
    return paths
```

Hmm wait, this creates a file per (name variant) per repo. Then for the per-thunk-call hardlinks with a unique repo... I'd rather pre-create the template file for one repo and hardlink.

Plan: 
- `_register(repo_template, cutoff, comments)` writes the content to `_BASE/repos/ORG/{repo_template}/issues/comments?...` (both variants). This repo name itself could be used as the actual repo! So no hardlink needed at all if we just use a unique repo per case and clear the cache.

Hmm, I keep flip-flopping. Decision: use **unique repo per thunk call with hardlinks**, AND clear the cache. Let me justify: robustness against cache renaming; and clearing keeps memory low.

Hmm, but hardlinks: the target file path for call k is `_BASE/repos/ORG/{repo_k}/issues/comments?...`. The template is at `_BASE/repos/ORG/{template}/issues/...`. Hardlink works across the same filesystem. 

But then, the template dir also has 2 files; for each call we create 2 hardlinks. Fine.

Actually, hmm — is it simpler to just write the file content fresh in the thunk? 6 MB write per call, untimed but slow (could add seconds per case). Hardlink is better.

OK let me write:

```python
_seq = itertools.count()

def _thunk_for(template, cutoff, prefix):
    def thunk():
        _module._repo_comments_cache.clear()
        repo = f"{prefix}-{next(_seq)}"
        d = _BASE / "repos" / ORG / repo / "issues"
        d.mkdir(parents=True, exist_ok=True)
        for tname, cname in template:
            os.link(tname, d / cname)
        return (repo, cutoff)
    return thunk
```

where template is a list of (template_path, case_filename).

Hmm, the template file name is the same string as cname (the filename depends only on cutoff/query). So `template` = list of (path, filename). Let me store `_templates[case] = [(path, name), ...]`.

Simplify: 

```python
def _thunk(template_dir, cutoff, prefix):
    names = sorted(p.name for p in template_dir.iterdir())
    def thunk():
        _module._repo_comments_cache.clear()
        repo = f"{prefix}-{next(_seq)}"
        d = _BASE / "repos" / ORG / repo / "issues"
        d.mkdir(parents=True, exist_ok=True)
        for nm in names:
            os.link(template_dir / nm, d / nm)
        return (repo, cutoff)
    return thunk
```
Careful: `template_dir` must not be inside another repo's dir... it's `_BASE/repos/ORG/{template_repo}/issues`. Fine.

Wait, but there's a potential issue: the thunk hardlinks into a new repo dir for EVERY call, including calls made during... hmm, "before the timing starts" — the thunk is called, then the function is timed. Unlink/cleanup not needed.

Hmm, number of dirs created = number of calls. If 1000 calls, 1000 dirs each with 2 files. Fine.

Hmm, but is `os.link` a "file creation" that persists and could confuse the harness (e.g., "anything the function writes must go under WORKDIR")? It's under WORKDIR. Fine.

Hmm, actually, hmm: do I even need unique repos? With `.clear()` in the thunk, the repo can be constant. The only reason for unique repos is defense against a modified version that renames the cache. Let me weigh: renaming a module-level cache in a performance-modified version is quite unlikely. And unique repos add complexity + risk (e.g., if the harness limits the number of files, or if hardlinks aren't supported on the filesystem).

Hmm. But there's another consideration: the cache dict holds results; with a constant repo and clear(), it's fine.

I'll go with the simpler: constant repo per case + clear the cache in the thunk. Actually no — wait. Let me think about one more scenario: what if the harness measures by calling the function N times and the thunk only once? Then with a constant repo, calls 2..N are cache hits → the original does almost nothing; and the modified version too (if it keeps the cache) → the measurement would be meaningless but not wrong. With unique repos, calls 2..N would fail?? No — the file for repo_k exists only if the thunk created it. If the thunk is called once, only repo_1's file exists → calls 2..N would raise URLError → the harness reports failure. That's BAD. Whereas with a constant repo, the cache hit is safe.

Hmm! That's a strong argument for constant repo + cache clear... but even the cache clear only happens once, so calls 2..N would hit the cache. Both are "safe" (no exception) with constant repo. With unique repos, reusing the thunk's args without re-calling the thunk → exception.

Hmm, but even with the constant repo, the cache clear in the thunk is only effective once. If the thunk is called per measurement, everything is fine.

Given the described protocol (per-call thunk), the constant-repo approach is safe under both interpretations. Unique repo is only safe under the per-call interpretation. So: **constant repo per case + clear cache in thunk**. 

Hmm, but wait: what if the thunk IS called per call, and the modified version renamed the cache? Then the modified version would return the first computed result instantly for calls 2..N, while the original does full work. Energy comparison invalid. Hmm. That's the scenario I worried about.

Could I get both? What about: constant repo + clear cache in the thunk + ALSO delete-and-recreate the file each call? No, that doesn't help the cache issue.

Alternative that's safe under both interpretations AND cache-rename: use a repo name that depends on a counter, but pre-create files for many counter values at module level (say 2000 files)... but the calls could exceed that. Hmm, and if the thunk is called once, only one repo is used anyway.

Hmm, actually here's a cleaner idea: make the repo name unique per thunk call, but ALSO make the file resolution robust by creating a *directory* structure that... no.

Hmm, what about this trick: instead of the repo appearing in the path, what if... no, it's in the path.

OK here's another thought: is the "modified version" likely to change the cache? Let me think about what an energy-optimization of this function looks like: replacing the `number not in list` with a set-based dedup, or hoisting `setdefault`, or using `str.rsplit` instead of `rstrip().split()`. Renaming the module global `_repo_comments_cache` would be unusual. I'll accept the small risk.

Hmm, hmm. But actually — there's a hybrid: keep the constant repo, and in the thunk, clear the cache. If the modified version renamed the cache, we could also clear other likely names... no.

Actually, alternative hybrid that's safe: constant repo, and in the thunk, *remove the repo's entry* from the cache dict AND... same thing.

Fine. Decision made: constant repo per case, clear `_module._repo_comments_cache` in the thunk.

Hmm, wait. One more idea to be even safer: what if I make the thunk take a fresh repo name from a counter AND the function's file lookup still works because I create the file for every possible counter value... unbounded. No.

OK moving on. Actually, hold on, one more consideration about clearing the cache: the instruction says the thunk should be cheap. `.clear()` is cheap.

Also: does clearing the cache affect the output comparison? No.

Now, the `checks()` — 2-3 small edge inputs, not measured, may raise. These should be small edge cases. But they still need to run?! "checked only for identical behaviour, never measured. These may raise." So the checks may raise. But if they'd raise due to missing files (URLError), the original and modified versions would raise the same way — that's still "identical behaviour"? Presumably the harness compares exceptions too. Hmm, but if it raises the same exception type/message, fine.

Let's make checks simple: e.g., a repo that doesn't exist (no file) → URLError. And an empty JSON file (empty comment list) → returns {} immediately. And a file with one comment.

Hmm, for the empty list case, the function returns {} and caches it.

Let's write checks:
1. "no-file": repo that has no file → raises URLError. Hmm, is that desirable? It might be fine ("these may raise"). But maybe safer to have checks that don't raise? The instructions say edge inputs may raise. But if raising is due to our file setup being fake, that's a bit ugly. Let me include:
   - "empty-page": a file containing `[]` → returns {}.
   - "single-comment": one comment.
   - "old-comment": one comment with created < cutoff → early return, {} .
   
   All with tiny files. That's safer than a raising check. But "may raise" is allowed... Let's do the three non-raising ones, plus maybe not.

Hmm, actually the checks also need the cache not to interfere. For checks, we don't time them; we just need them to run. Since the same repo names might be used... use distinct repos for checks and clear the cache in the thunk anyway.

OK, let's write the final code.

One more detail: the module import. The task says import it as `importlib.import_module('move-to-emeritus')._get_repo_commenters`. I'll do:

```python
import importlib
_module = importlib.import_module('move-to-emeritus')
_get_repo_commenters = _module._get_repo_commenters
```

But do I need `_get_repo_commenters` at all? The harness calls the function itself presumably... The example code doesn't reference the function. I'll define it anyway for clarity (not required). Actually, hmm — the harness might look for the function by name? It's given in the task, so the harness knows. I'll define the alias anyway, harmless.

Also: does importing the module execute `main()`? Let's check: the module has `def main():` and presumably `if __name__ == "__main__": main()`. Importing with the name 'move-to-emeritus' means `__name__` is 'move-to-emeritus', not '__main__', so main() won't run. Good.

Also at import time, does the module do anything requiring env vars or network? It defines HEADERS probably via os.environ. Let's hope not. The task says "Import the repository's modules exactly as shown in the task", implying it works.

Hmm, actually HEADERS isn't in the "everything else it defines" header list. Interesting — it's used in request_with_retry but not listed. So HEADERS might be a module-level constant defined somewhere (maybe `HEADERS = {"Authorization": f"token {TOKEN}", ...}`). It exists.

Now, `ORG = "open-telemetry"` is defined in the module per the task. I'll use `_module.ORG`.

Wait — careful, if I use "open-telemetry" as the directory segment, the URL path uses ORG which is the module's actual ORG. Use `_module.ORG`.

Now write the code.

```python
import importlib
import itertools
import json
import os
import random
import urllib.parse

_module = importlib.import_module('move-to-emeritus')
_get_repo_commenters = _module._get_repo_commenters

ORG = _module.ORG
_BASE = WORKDIR.resolve()
_module.REST_API = "file://" + str(_BASE)

CUTOFF_MAIN = "2024-01-01"
```

Hmm: `_module.REST_API = "file://" + str(_BASE)`. If `_BASE` = "/tmp/abc", REST_API = "file:///tmp/abc". Then the url = "file:///tmp/abc/repos/...". Good.

Now the params/query:

```python
def _query(cutoff):
    return urllib.parse.urlencode({
        "since": f"{cutoff}T00:00:00Z",
        "per_page": 100,
        "sort": "created",
        "direction": "desc",
    })
```

And the directory:

```python
def _issue_dir(repo):
    return _BASE / "repos" / ORG / repo / "issues"
```

And writing:

```python
def _publish(repo, cutoff, comments):
    d = _issue_dir(repo)
    d.mkdir(parents=True, exist_ok=True)
    data = json.dumps(comments).encode("utf-8")
    qs = _query(cutoff)
    names = ("comments?" + qs, "comments?" + urllib.parse.unquote(qs))
    for nm in dict.fromkeys(names):
        (d / nm).write_bytes(data)
```

Wait — the urlencode of the params: `urlencode` uses quote_plus by default which encodes ":" as "%3A" and space as "+". Our values have no spaces. Good.

But hold on — `quote_plus` also encodes... the query in the URL: yes "since=2024-01-01T00%3A00%3A00Z". Right.

Now, unquote of `since=2024-01-01T00%3A00%3A00Z` gives `since=2024-01-01T00:00:00Z`. File name segment: "comments?since=2024-01-01T00:00:00Z&per_page=100&sort=created&direction=desc".

Both files written. 

Now, the cache-clearing thunk:

```python
def _mk_thunk(repo, cutoff):
    def thunk():
        _module._repo_comments_cache.clear()
        return (repo, cutoff)
    return thunk
```

Hmm — one concern: `_module._repo_comments_cache` might not exist if the module is different... it's defined per the task.

Now the comment builder:

```python
def _comment(repo, idx, user, created, number, is_pr):
    seg = "pull" if is_pr else "issues"
    issue_url = f"https://api.github.com/repos/{ORG}/{repo}/issues/{number}" if number else ""
    return {
        "created_at": created,
        "user": None if user is None else {"login": user},
        "html_url": f"https://github.com/{ORG}/{repo}/{seg}/{number or 1}#issuecomment-{idx}",
        "issue_url": issue_url,
    }
```

Careful: `"/pull/" in html_url` — for issues: "https://github.com/open-telemetry/otel-x/issues/123#issuecomment-1" → contains "/issues/" → no "/pull/". Good. But web_url for PRs: ".../pull/123#issuecomment-1" → contains "/pull/". Good.

Now generate cases.

```python
def _dates(rng, n):
```
Let's generate created timestamps in 2024-02-01 .. 2024-06-30, as "YYYY-MM-DDTHH:MM:SSZ".

```python
def _ts(rng):
    return (f"2024-{rng.randint(2, 6):02d}-{rng.randint(1, 28):02d}"
            f"T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}Z")
```

Case builders:

Case 1 — mixed typical:
```python
def _case_mixed():
    repo = "otel-mixed-comments"
    cutoff = CUTOFF_MAIN
    rng = random.Random(1)
    nums = [1000 + i for i in range(4000)]
    seen = []
    out = []
    for i in range(20_000):
        if seen and rng.random() < 0.15:
            user, num, is_pr = seen[rng.randrange(len(seen))]
        else:
            user = f"user{rng.randrange(800):04d}"
            num = nums[rng.randrange(len(nums))]
            is_pr = rng.random() < 0.5
            seen.append((user, num, is_pr))
        out.append(_comment(repo, i, user, _ts(rng), num, is_pr))
    return repo, cutoff, out
```

Note: `seen` grows to ~17k tuples; memory fine.

Case 2 — one power user, quadratic dedup:
```python
def _case_power_user():
    repo = "otel-power-user"
    rng = random.Random(2)
    out = []
    for i in range(3000):
        num = 2000 + i            # distinct PR numbers
        out.append(_comment(repo, i, "power-user", _ts(rng), num, True))
    # plus repeated comments on an already-seen PR (dedup hits)
    ...
```
Hmm, 3000 distinct PRs for one user → the pr list grows to 3000, membership checks sum to ~4.5M. Let's reduce to 2500 to be safe → 3.1M comparisons ≈ 60-100 ms? Hmm. Actually, `in` on a list of ints: for each comparison, `PyObject_RichCompareBool` with identity check then `int.__eq__` fast path. That's maybe 15-25 ns. 3.1M * 20ns = 62 ms. OK.

Actually hold on, is it really that fast? Let me think: `x in list` → `list_contains` → for each item, `PyObject_RichCompareBool(item, x, Py_EQ)` → `do_richcompare` → `PyNumber_RichCompare`? With both ints and equal types, it calls `int.__eq__` via the type's tp_richcompare (int_richcompare) which is fast. Plus loop overhead. I'd estimate 30-50 ns each. 3.1M * 40ns = 124 ms. Hmm, that's on the edge but under 1s. Let me use 2000 distinct → 2M comparisons → ~80ms. Then add 1000 duplicate comments for a total n=3000.

Hmm, but actually more work is fine as long as < 1s. Let's use 2500 distinct.

I'll do: for i in range(n): if i < 2500 → new number; else repeat a random earlier number. n = 3500.

Case 3 — issues only, many users:
```python
n=15000, 600 users, numbers 1..3000, is_pr=False, some dups.
```

Case 4 — PRs only, high duplicate ratio (many hits):
n=15000, 400 users, numbers from 500 distinct PRs (lots of duplicates → membership hits fast).

Case 5 — many distinct users, one comment each: n=20000, user = f"u{i}", number = 10000 + i, alternating pr/issue. Result has 20000 users.

Case 6 — bad users: n=12000, 50% user=None or missing login. Hmm, "user": None → `.get("user") or {}` → {} → login "" → continue. Also user dict without "login": {"login"?}. Let's do: rng < 0.5 → user None; else a real user. And also some with `{"login": ""}`? `or {}` — if user = {"login": ""}, it's truthy (non-empty dict) → login "" → continue. Both paths.

To vary, use `user=None` for half, and for another 20% use `{"login": ""}`. Hmm, my `_comment` builder sets `None if user is None else {"login": user}`. I'd need a variant. Let me add a parameter... simpler: build the dicts manually in that case.

Case 7 — missing issue_url: n=12000, half with number=0 (empty issue_url → number=0 → no append, but setdefault still happens). Good.

Case 8 — early cutoff: n=8000, sorted descending by created_at, first 5000 in mid-2024, then comments from 2023 (older than cutoff) → early return after 5000.

For that: created values: i<5000 → "2024-06-XX", i>=5000 → "2023-12-XX" (descending order maintained loosely). The function returns at the first comment with created < cutoff.

Hmm, but the created_at strings must be descending for realism; string comparison only matters vs cutoff.

Good. Note the returned commenters only includes the first 5000.

Now checks:

```python
def checks():
    return [
        ("empty-page", lambda: (_empty_repo, CUTOFF_MAIN)),
        ("single-comment", lambda: (_single_repo, CUTOFF_MAIN)),
        ("all-old", lambda: (_old_repo, CUTOFF_MAIN)),
    ]
```
with tiny files built at module level. Hmm — but a check with an empty list: the function returns {} and caches it. Would the harness call it twice? Doesn't matter.

Hmm, but I want to clear the cache for checks too. Use `_mk_thunk`.

Wait, but for checks, the thunk returns `(repo, cutoff)`. Using `_mk_thunk` clears the cache each call. Fine.

Let me write these small files: empty repo → `[]`; single repo → one comment; old repo → one comment dated 2023.

Now let's also double check the `number` parse: issue_url = "https://api.github.com/repos/open-telemetry/otel-x/issues/1000" → rstrip("/") → same → split("/")[-1] → "1000" → int → 1000. Good. For number=0 → issue_url = "" → number = 0 → `if number and ...` False → no append, but setdefault already created the entry. Right.

Edge: if number were 0 in issue_url (e.g. ".../issues/0"), then int→0, and `if number` is False. Fine.

Now, memory: the result for case 5 has 20,000 users each with {"pr": [num], "issue": []} or similar → that's 20,000 * ~4 values = 80,000 values. Hmm, "keep what it returns under about 100 000 values". Each user entry dict counts as values? Let's count: 20,000 dicts + 20,000 lists (two per user: pr and issue) + 20,000 ints ≈ 60k-80k. Borderline. Let me reduce case 5 to 12,000 users to be safe. Hmm, but then it's less heavy. 15,000. OK, let's use 12,000 distinct users with 12,000 comments. Actually the result also includes numbers. Let's say ~50k values. Fine.

Similarly for other cases: case 1: 800 users * (2 lists + nums) ≈ 800 + 1600 + ~15,000 numbers ≈ 17k. Fine.

Hmm, case 5 with 12k users: the JSON file has 12k comments. Parse ~25ms. Fine.

Let me reconsider max result size: case 3 (issues only, 15,000 comments, 600 users): numbers appended ~13,000 → 600 dicts + 1200 lists + 13,000 ints ≈ 15k values. Fine.

Case 2: 2500 numbers for 1 user → small.

All good.

Now the JSON file sizes: 20,000 comments * ~250 bytes ≈ 5 MB. Fine.

Let's now consider the total time to build all inputs at module level: 8 cases * ~20k dicts = ~120k dicts, each with 4 keys. json.dumps for each → maybe 0.5s total. Plus writing ~30 MB to disk. Should be under 10s. OK.

Hmm, one risk: creating files with "?" and "&" in the name — if WORKDIR is on a filesystem that rejects them (unlikely on Linux). Accept.

Another risk: `_BASE = WORKDIR.resolve()`. If WORKDIR is a Path, fine.

Let me now double check the file-open path once more, considering `_splithost` regex `//([^/#?]*)(.*)`.

URL = "file:///tmp/wd/repos/open-telemetry/repo/issues/comments?since=..."

_splittype → type="file", rest="///tmp/wd/repos/.../comments?since=...".
_splithost(rest) → regex needs "//" at the start. rest starts with "///" → matches "//" then `[^/#?]*` matches "" (next char is "/"), then `(.*)` matches "/tmp/wd/...comments?since=...". host_port="" , path="/tmp/...". Then `if path and path[0] != '/'` → no change. Returns ("", "/tmp/...comments?since=...").

Request._parse sets self.host = "" (falsy, so no unquote), self.selector = "/tmp/wd/repos/.../comments?since=...".

Hmm wait, actually there's something else in Request.__init__: 
```python
if self.host: self.host = unquote(self.host)
```
Fine.

Then FileHandler.file_open(req): url = req.selector = "/tmp/wd/...comments?since=...". `url[:2]` = "/t" ≠ "//" → else branch → open_local_file(req).

open_local_file: host = req.host = "" (falsy), filename = req.selector, localfile = url2pathname(filename) = unquote(filename).

unquote("/tmp/wd/repos/open-telemetry/repo/issues/comments?since=2024-01-01T00%3A00%3A00Z&per_page=100&sort=created&direction=desc") = "/tmp/wd/.../comments?since=2024-01-01T00:00:00Z&per_page=100&sort=created&direction=desc".

Hmm! unquote also affects the directory part if it has %XX. Our dirs have none. Good.

So the disk filename = "comments?since=2024-01-01T00:00:00Z&per_page=100&sort=created&direction=desc". This matches `"comments?" + urllib.parse.unquote(qs)`. 

But hold on — is `unquote` applied to the query by the *server-side*? No. OK.

Now, wait. I should double check one thing: does `Request` strip a fragment or modify the URL? No fragment here.

And `urllib.request.urlopen(req, body, timeout=30)` with body=None → for file handler, `FileHandler.file_open(self, req)` doesn't take data. Fine. Actually, the chain: `OpenerDirector.open(fullurl, data, timeout)` → `_call_chain(self.handle_open, protocol, protocol + '_open', req)` where protocol = req.type = "file" → FileHandler.file_open. It ignores data. Good.

Hmm, one thing: `AbstractHTTPHandler` etc. aren't invoked. Good.

Also: `resp.headers.get("x-ratelimit-remaining")` — headers is an email Message with Content-type, Content-length, Last-modified → returns None. Good. `int(None)` skipped.

`resp.headers.get("Link", "")` → "". Good.

And `resp.read()` → bytes → decode → json.loads.

Everything checks out.

One more: the module prints warnings? No.

Now: what about `HEADERS`? `urllib.request.Request(url, headers=HEADERS, method=method)` — if HEADERS contains a header value with non-ASCII... not our problem. But what if HEADERS is None? Then `headers=None` → Request handles None? `Request.__init__` does `for key, value in headers.items()` — if None, AttributeError! Hmm. Let's check: `Request(url, data=None, headers={}, ...)`; `if headers is None: headers = {}`? Actually:

```python
def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=False, method=None):
    self.full_url = url
    self.headers = {}
    ...
    self.method = method
    ...
    try:
        self.full_url, self.fragment = _splittag(self.full_url)
    except ValueError:
        ...
    self.data = data
    if data is not None:
        self.add_header('Content-type', 'application/x-www-form-urlencoded')
    ...
    for key, value in headers.items():
        self.add_header(key, value)
```

So if HEADERS were None → AttributeError. But HEADERS is used in the real code, so it must be a dict. Fine.

Hmm, but what if HEADERS is built from an env var at import: `HEADERS = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}` → KeyError at import! Then `importlib.import_module` would raise and everything fails. Hmm. That's a risk I can't control; the task says to import it as given.

OK, writing the final code now.

One more decision: should the repo names be unique per case? Yes, different files.

Also I should ensure the function actually uses `_module.REST_API` — we set it on the module before any call. Since the module's function reads the global at call time. Good.

Let me also think: should I set `_module.ORG`? No, use it as-is.

Now writing.

```python
import importlib
import json
import random
import urllib.parse

_module = importlib.import_module('move-to-emeritus')
_get_repo_commenters = _module._get_repo_commenters

_ORG = _module.ORG
_BASE = WORKDIR.resolve()
_module.REST_API = "file://" + str(_BASE)
```

Hmm — careful! If `_BASE` = "/" then REST_API = "file:///" ... fine, not our case.

Now the case definitions return (repo, cutoff, comments).

Let me write everything into a big module-level build.

```python
def _ts(rng):
    return (f"2024-{rng.randint(2, 6):02d}-{rng.randint(1, 28):02d}"
            f"T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}Z")


def _comment(repo, idx, user, created, number, is_pr):
    seg = "pull" if is_pr else "issues"
    issue_url = ""
    if number:
        issue_url = f"https://api.github.com/repos/{_ORG}/{repo}/issues/{number}"
    return {
        "created_at": created,
        "user": None if user is None else {"login": user},
        "html_url": f"https://github.com/{_ORG}/{repo}/{seg}/{number if number else 1}#issuecomment-{idx}",
        "issue_url": issue_url,
    }
```

Hmm, for the "no issue_url" case, I set number=0 → issue_url "" and html_url uses 1. OK.

Now the case builders... let me write them inline in a `_build_all()` function called at module level.

```python
def _sample(rng, n):
    ...
```

I'll write:

```python
def _build_cases():
    built = []

    # --- case: mixed typical ...
```

Let me write each explicitly.

Case A (mixed):
```python
    repo = "otel-mixed-activity"
    rng = random.Random(1)
    nums = [1000 + i for i in range(4000)]
    pool = []
    out = []
    for i in range(20_000):
        if pool and rng.random() < 0.15:
            user, num, is_pr = pool[rng.randrange(len(pool))]
        else:
            user = "user%04d" % rng.randrange(800)
            num = nums[rng.randrange(len(nums))]
            is_pr = rng.random() < 0.5
            pool.append((user, num, is_pr))
        out.append(_comment(repo, i, user, _ts(rng), num, is_pr))
    built.append((repo, CUTOFF, out))
```

Case B (power user):
```python
    repo = "otel-power-commenter"
    rng = random.Random(2)
    out = []
    for i in range(3500):
        if i < 2500:
            num = 2000 + i
        else:
            num = 2000 + rng.randrange(2500)
        out.append(_comment(repo, i, "power-user", _ts(rng), num, True))
    built.append((repo, CUTOFF, out))
```
Wait — the first 2500 are distinct PR numbers, so the membership check scans the growing list. Then the remaining 1000 repeat existing numbers (mostly hits). Total list of 2500 ints. Sum of comparisons ≈ 2500²/2 = 3.1M. OK.

Case C (issues only, many users):
```python
    repo = "otel-issue-chatter"
    rng = random.Random(3)
    out = []
    for i in range(15_000):
        user = "chatter%04d" % rng.randrange(600)
        num = 1 + rng.randrange(3000)
        out.append(_comment(repo, i, user, _ts(rng), num, False))
    built.append((repo, CUTOFF, out))
```

Case D (prs only, heavy duplicates):
```python
    repo = "otel-pr-reviewers"
    rng = random.Random(4)
    prs = [5000 + rng.randrange(400) for _ in range(15_000)]  # hmm
```
Better: choose the PR number from a small set of 400 distinct values.
```python
    out = []
    numbers = [5000 + i for i in range(400)]
    for i in range(15_000):
        user = "reviewer%03d" % rng.randrange(300)
        num = numbers[rng.randrange(400)]
        out.append(_comment(repo, i, user, _ts(rng), num, True))
```
This has a high hit ratio (400 numbers, 300 users, 15,000 comments → mostly duplicates → fast membership on short lists). Hmm, "high hit ratio" — this case does less work per comment. But json parsing dominates.

Case E (many distinct users, thin):
```python
    repo = "otel-drive-by-commenters"
    rng = random.Random(5)
    out = []
    for i in range(12_000):
        user = "driveby%05d" % i
        num = 20000 + i
        is_pr = i % 2 == 0
        out.append(_comment(repo, i, user, _ts(rng), num, is_pr))
    built.append((repo, CUTOFF, out))
```
Each user has exactly one comment → result 12,000 users → ~48k values. Hmm, borderline on the 100k limit. OK.

Case F (bad users):
```python
    repo = "otel-anonymous-comments"
    rng = random.Random(6)
    out = []
    for i in range(12_000):
        r = rng.random()
        if r < 0.45:
            c = _comment(repo, i, None, _ts(rng), 30000 + rng.randrange(2000), True)
        elif r < 0.65:
            c = _comment(repo, i, "", _ts(rng), 30000 + rng.randrange(2000), rng.random() < 0.5)
        else:
            c = _comment(repo, i, "named%03d" % rng.randrange(200), _ts(rng), 30000 + rng.randrange(2000), rng.random() < 0.5)
        out.append(c)
```
Note: `user=""` → `{"login": ""}` → truthy dict → login "" → `if not user: continue`. Good.

Case G (no issue_url):
```python
    repo = "otel-url-less-comments"
    rng = random.Random(7)
    out = []
    for i in range(12_000):
        user = "urluser%04d" % rng.randrange(500)
        num = 0 if rng.random() < 0.5 else 40000 + rng.randrange(3000)
        out.append(_comment(repo, i, user, _ts(rng), num, rng.random() < 0.5))
    built.append((repo, CUTOFF, out))
```

Case H (early cutoff):
```python
    repo = "otel-stale-comments"
    rng = random.Random(8)
    out = []
    for i in range(8000):
        if i < 5000:
            created = f"2024-06-{rng.randint(1,28):02d}T..."
        else:
            created = f"2023-{rng.randint(1,12):02d}-..."
```
Need descending order: the first 5000 in 2024-06/05, then the rest in 2023. Let's make: i<5000 → "2024-06-XX", else "2023-XX-XX". Since the loop stops at the first < cutoff, the exact ordering within groups doesn't matter for correctness, but let's keep groups ordered.

Actually let me make the boundary more interesting: 4000 in 2024, then at i=4000 a comment from 2023-12-31 (< 2024-01-01) → return.

```python
    for i in range(8000):
        if i < 4000:
            created = f"2024-0{rng.randint(2,6)}-{rng.randint(1,28):02d}T{rng.randint(0,23):02d}:00:00Z"
        else:
            created = f"2023-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T00:00:00Z"
        ...
```
The function returns at i=4000. Work = parse the whole file + process 4000. Fine.

Now, the cutoff for all cases is "2024-01-01".

Hmm, for case H, `if created < cutoff` → "2023-12-31" < "2024-01-01" → True → cache and return.

Now, careful: the return value is the partial commenters dict. Fine.

Now let's assemble. Each builder returns (repo, cutoff, comments) and I call `_publish`.

Module-level: build all 8 and publish. Then `cases()` returns the thunks with constant repos.

Let me write the final structure:

```python
_CUTOFF = "2024-01-01"

def _publish(repo, cutoff, comments):
    d = _BASE / "repos" / _ORG / repo / "issues"
    d.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(comments).encode("utf-8")
    qs = _query(cutoff)
    for name in dict.fromkeys(["comments?" + qs, "comments?" + urllib.parse.unquote(qs)]):
        (d / name).write_bytes(payload)
```

Then:

```python
_CASES = {}   # label -> repo
for _label, _repo, _comments in _build():
    _publish(_repo, _CUTOFF, _comments)
    _CASES[_label] = _repo
```

Hmm, but building all of them inside one function is fine. Memory: after publishing, the comment lists are freed (`del`). Let's do it in a loop that doesn't keep them.

Let me write `_build()` as a generator yielding (label, repo, comments).

Careful: generator + writing while iterating: each comments list is freed after publishing. Good for memory.

Now `cases()`:

```python
def cases():
    return [
        (label, _thunk(repo, _CUTOFF))
        for label, repo in _CASES.items()
    ]
```

This gives exactly 8 (as long as _build yields 8).

And `_thunk`:
```python
def _thunk(repo, cutoff):
    def thunk():
        _cache.clear()
        return (repo, cutoff)
    return thunk
```
where `_cache = _module._repo_comments_cache` — hmm, capture the dict object at module level. But if the module rebinds it (it doesn't), fine. Actually safer: `_module._repo_comments_cache.clear()` each time, reading the attribute. But if the modified version rebinds... doesn't matter. I'll use `getattr(_module, "_repo_comments_cache").clear()`. Hmm, simpler: `_module._repo_comments_cache.clear()`.

Wait, but should I even clear it? Let me reconsider once more... Yes, clear it. If it's not cleared, the first call populates it and subsequent calls return instantly → ~zero work for the original. Then the 4 heaviest would all be trivial. Bad. So clearing is essential.

Hmm, unless... the harness creates a fresh process per measurement? Probably not. Clearing is the safe route.

Now, checks():

```python
def checks():
    return [
        ("empty-page", _thunk(_CHK_EMPTY, _CUTOFF)),
        ("single-comment", _thunk(_CHK_SINGLE, _CUTOFF)),
        ("stale-only", _thunk(_CHK_STALE, _CUTOFF)),
    ]
```
with module-level publishing of tiny files.

Empty page: `[]`. Then the function processes nothing, url=None, caches {} and returns {}. 

Single comment: one comment with created 2024-05-05, user "alice", PR 42.
Stale: one comment with created "2023-05-05" → early return {}.

These are small edge cases involving the same code paths (empty list, single element, early cutoff). Good.

Hmm, should checks include something that raises (per "These may raise")? Not required. I'll keep them non-raising for safety.

Now, one consideration on `_publish` for checks: same repo names, different files. Fine.

Order of module-level code: define _BASE, set REST_API, define helpers, publish.

Also note: the module-level `data` generation must be deterministic (seeded).

Let me now think about total time: 8 cases with ~20k, 3.5k, 15k, 15k, 12k, 12k, 12k, 8k = ~98k comments. json.dumps each → maybe 0.3-0.5 s. Writing ~25 MB → maybe 1-2 s. OK.

Memory during build: the biggest list is 20k dicts (~10 MB as Python objects, maybe 20 MB). Freed after publishing. Peak ~30 MB. OK.

Hmm, one important detail: `json.dumps(comments)` produces a JSON array. The function does `read_json(resp)` → a list. Then iterates. Good.

Let me also double check `_comment` when `number=0`: `html_url` = ".../pull/1#issuecomment-{i}" if is_pr else ".../issues/1#...". Fine.

Now, is there a problem that `int(issue_url.rstrip("/").split("/")[-1])` could raise ValueError? Only if the last segment isn't an int — our URLs end with the number. Good.

Let's write the final code.

One more thought on the "unquote" double-file trick: writing two files with the same content doubles disk/memory writes but it's cheap.

Also, careful with `dict.fromkeys([...])` — preserves order and dedups. Good.

Another detail: `(d / name).write_bytes(payload)` where name contains "?" and "&" and "=" and ":". On Linux that's fine.

But hmm — one risk: if WORKDIR is on a filesystem mounted with restrictions... unlikely.

Now, the REST_API: `"file://" + str(_BASE)`. If _BASE is "/tmp/x", we get "file:///tmp/x". Then url = "file:///tmp/x/repos/open-telemetry/repo/issues/comments?..." and selector = "/tmp/x/repos/...". Good.

Now the directory: `_BASE / "repos" / ORG / repo / "issues"`. Good.

Let me write it all out.

```python
import importlib
import json
import random
import urllib.parse

_module = importlib.import_module('move-to-emeritus')
_get_repo_commenters = _module._get_repo_commenters

_ORG = _module.ORG
_BASE = WORKDIR.resolve()
_module.REST_API = "file://" + str(_BASE)

_CUTOFF = "2024-01-01"


def _query(cutoff):
    return urllib.parse.urlencode({
        "since": f"{cutoff}T00:00:00Z",
        "per_page": 100,
        "sort": "created",
        "direction": "desc",
    })


def _publish(repo, cutoff, comments):
    d = _BASE / "repos" / _ORG / repo / "issues"
    d.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(comments).encode("utf-8")
    qs = _query(cutoff)
    for name in dict.fromkeys(("comments?" + qs, "comments?" + urllib.parse.unquote(qs))):
        (d / name).write_bytes(payload)
```

Then `_ts`, `_comment`, `_build` generator.

Then:

```python
_REPOS = {}
for _label, _repo, _comments in _build():
    _publish(_repo, _CUTOFF, _comments)
    _REPOS[_label] = _repo
```

Hmm — a for loop at module level with `_label` etc. leaking is fine.

Then checks' repos:
```python
_CHK = {}
_c = [{"created_at": "2024-05-05T10:00:00Z", "user": {"login": "alice"},
       "html_url": f"https://github.com/{_ORG}/otel-checks/pull/42#issuecomment-1",
       "issue_url": f"https://api.github.com/repos/{_ORG}/otel-checks/issues/42"}]
```

Let me define the three check files:
- "otel-check-empty-comments": []
- "otel-check-one-comment": [one]
- "otel-check-stale-comment": [one with created_at "2023-11-20T..."]

Publish them.

Then:
```python
def _thunk(repo, cutoff=_CUTOFF):
    def thunk():
        _module._repo_comments_cache.clear()
        return (repo, cutoff)
    return thunk
```

Hmm — `_module._repo_comments_cache` — but what if the module has been reloaded? Fine.

Hmm, another thought: should I also clear the cache for the checks? Yes, same thunk.

But careful: for the check with the stale comment, the function early-returns and caches; clearing each time is fine.

Now, one thing I should double check: for the "empty page" check, `while url:` — url is truthy, resp is the file of `[]`, comments=[], the for loop does nothing, then link = "" → next_url None → url = None → exit loop → cache {} and return {}. Good.

Now let me write the cases builder and make sure I get exactly 8 labels:

1. "mixed-typical"
2. "power-commenter"
3. "issue-chatter"
4. "pr-reviewers"
5. "drive-by-commenters"
6. "anonymous-comments"
7. "url-less-comments"
8. "stale-cutoff"

Now writing `_build`:

```python
def _build():
    # 1
    repo = "otel-mixed-activity"
    rng = random.Random(1)
    nums = [1000 + i for i in range(4000)]
    pool = []
    out = []
    for i in range(20_000):
        if pool and rng.random() < 0.15:
            user, num, is_pr = pool[rng.randrange(len(pool))]
        else:
            user = "user%04d" % rng.randrange(800)
            num = nums[rng.randrange(len(nums))]
            is_pr = rng.random() < 0.5
            pool.append((user, num, is_pr))
        out.append(_comment(repo, i, user, _ts(rng), num, is_pr))
    yield "mixed-typical", repo, out
    ...
```

Careful: this is a generator; when it yields, the caller publishes. Good.

Now about `_ts(rng)` being called multiple times per comment — fine.

Let me write out all 8 and the checks.

Also, I need `random.Random(0)` per the instructions? It says "a fixed random seed (random.Random(0)) when generating data" — meaning a fixed seed; I'll use different seeds per case (still fixed). That's fine and gives diversity.

Final check on the harness's "renders arguments before and after each call to see whether it changed them": (repo, cutoff) strings — unchanged. Good.

One more potential issue: the harness may run the original and the modified version in the same process, sharing the module state. Both will use our REST_API and cache. Fine.

Let me write the final code now.

Also should I worry that the function might be called with keyword args? No, positional.

I'll write it.

def _comment(...) — note repo is embedded in the URLs inside the JSON, and the JSON is published under the repo's directory. Consistent (doesn't matter anyway).

Writing now.

One last consideration on `_BASE / "repos" / _ORG`: `_ORG` = "open-telemetry". Fine.

Also: `d.mkdir(parents=True, exist_ok=True)` — if the dir already exists from a previous run (harness reruns?), `write_bytes` overwrites. Fine.

Ok, final code.

Actually, one more: the `checks()` thunks should probably NOT clear the cache... it doesn't hurt.

And the labels must be distinct within checks and within cases. Yes.

Write it out.