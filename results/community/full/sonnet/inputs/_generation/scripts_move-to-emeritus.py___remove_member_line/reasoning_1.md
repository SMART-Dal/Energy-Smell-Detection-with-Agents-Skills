Let me write the code. The function is a pure string function. Need to import via importlib.

I need realistic README content with sections. Let me construct a README with sections like "Triagers", "Approvers", "Maintainers" etc. The `_find_section` looks for `^#{2,3}\s+section_name\s*$` case-insensitive. End at next header at same or higher level.

Let me build a realistic README with many member lines.

Let me design 8 cases with varying sizes, sections, hit/miss, duplicates, case variations, long names, etc.

Let me write generator.

Section names: from ROLE_SECTIONS presumably mapping role labels to section names. Let's just use plausible ones: "Triagers", "Approvers", "Maintainers", "Emeritus Maintainers".

Build README:

```
# Community

Some intro text...

## Triagers

- [Alice](https://github.com/alice) - 2023
- [Bob](https://github.com/bob)
...

## Approvers

...

### Subsection
```

Note end_pattern: `^#{1,header_level}(?!#)\s` — for header_level 2, matches 1 or 2 hashes followed by not-# and whitespace. So `# ` or `## `.

Careful: `### Subsection` — `#{1,2}` would match `##` then next char is `#` which fails `(?!#)`, so no match. Good.

Let me build a generator that produces a README with a given section containing n member lines.

I'll write helper `_make_readme(section_name, members, header_level=2, extra_sections=True)`.

Members are usernames; lines formatted `- [Display Name](https://github.com/username) - joined date\n`.

Let me make realistic sizes: section with up to ~20,000 member lines. Each line ~60 chars → 1.2 MB. Fine.

Cases:
1. small section, hit at start.
2. large section (20k lines), hit near end.
3. large section, miss (user not present).
4. section not found (returns None) — but that's cheap; still fine as a case, though we keep the 4 that do most work. Let's include anyway.
5. case-insensitive username match.
6. duplicates of the same user (multiple lines) — regex removes first match only.
7. long usernames / special regex chars? Username with dots/hyphens. re.escape handles.
8. section at end of readme (no following header) — end = len(readme).
9. header level 3 section.

Let's generate 8 diverse ones.

Let me write:

```python
import importlib
import random

_mod = importlib.import_module('move-to-emeritus')
_remove_member_line = _mod._remove_member_line
```

Wait, the import path: file is `scripts/move-to-emeritus.py`. The task says import it as `importlib.import_module('move-to-emeritus')`. So scripts dir must be on sys.path — presumably the harness handles it. Just use that.

Now build READMEs.

```python
def _member_line(rng, i, username=None):
    if username is None:
        username = f"user{i}"
    name = f"User {i}"
    return f"- [{name}](https://github.com/{username}) - joined 2024-01-01\n"
```

Let me create a function to build a readme.

```python
def _build_readme(section_name, usernames, header_level=2, prefix_sections=(), suffix=True, seed=0):
    rng = random.Random(seed)
    parts = ["# Community Project\n\nWelcome to the community.\n\n"]
    for name, users in prefix_sections:
        parts.append(f"{'#'*header_level} {name}\n\n")
        for i, u in enumerate(users):
            parts.append(_member_line(rng, i, u))
        parts.append("\n")
    parts.append(f"{'#'*header_level} {section_name}\n\n")
    for i, u in enumerate(usernames):
        parts.append(_member_line(rng, i, u))
    parts.append("\n")
    if suffix:
        parts.append(f"{'#'*header_level} Other Section\n\nSome other content here.\n")
    return "".join(parts)
```

Hmm but `_find_section` end pattern uses `#{1,header_level}` — for header_level 2 it matches `#` or `##`. Our prefix sections are also level 2, fine.

Now cases. Need each thunk to return args tuple `(readme, section_name, username)`. Since function doesn't modify readme (strings immutable), we can reuse the same readme object across calls — fine.

Cases:

1. "small-hit-first": section ~50 members, username first.
2. "large-hit-late": 20000 members, username near end.
3. "large-miss": 20000 members, username absent.
4. "not-found-section": section name not present, big readme.
5. "duplicate-user": user appears many times.
6. "case-insensitive": username in different case.
7. "level3-section": header level 3.
8. "no-following-header": section at end of readme.

Also maybe a case with many sections and the target section among many.

Let me make sure each takes reasonable time. 20k lines ~1.2MB; regex search over that is fast, maybe <1ms. Hmm, need ~1ms-200ms. To get more work, make sections bigger: 200k lines ~12MB. That's under 100MB. Regex search over 12MB with MULTILINE... maybe a few ms. Good.

Actually building 200k lines per case × several cases could be slow-ish but under 10s. Let's be moderate: use 100k lines for large cases (~6MB). Let's estimate: 100k lines * ~60 chars = 6MB. Regex search over 6MB maybe 5-20ms. Good.

But careful: input data under 1,000,000 values. 100k lines is fine.

Let me vary: 
- case 2: 120k members, hit near end.
- case 3: 120k members, miss.
- case 4: big readme with many sections, section not found.
- case 5: 80k members with many duplicates of target user.
- case 6: 60k members, case-insensitive match.
- case 7: level-3 section with 80k members.
- case 8: 100k members, no following header (end=len).

Also case 1: small 200 members hit first.

Distinct labels.

Now checks: empty readme, section missing, username with regex special chars maybe. Let's do:
- ("empty-readme", lambda: ("", "Triagers", "alice")) → returns None.
- ("no-section", lambda: ("# Title\n\n## Other\n- [A](https://github.com/a)\n", "Triagers", "a")) → None.
- ("user-not-in-section", small readme with section, absent user) → None. Actually that's a miss, fine as check.

These may raise; they don't.

Let me also consider: section_name with regex chars? Not needed.

Now write generator carefully. The `_member_line` uses rng for display name variety maybe. Let's keep display names varied: some with spaces, brackets? Display name inside `[^\]]+` so no `]`. Use realistic names.

Let's generate display names from a list of first/last names with rng.

Let me write:

```python
_FIRST = ["Alice","Bob","Carol","Dave","Eve","Frank","Grace","Heidi","Ivan","Judy","Ken","Leo","Mona","Nina","Oscar","Peggy","Quinn","Rita","Sam","Tina"]
_LAST = ["Smith","Jones","Brown","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez"]

def _display_name(rng):
    return f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
```

Line: `- [{name}](https://github.com/{username}) - joined {date}\n`.

Now build.

For duplicates case: usernames list where "dupuser" appears at many positions.

Let me write cases function building data at module level (so thunks are cheap). Actually building in module-level code is fine, but the harness imports our module — module-level code runs at import. That's fine and setup isn't timed. But careful: building 8 readmes of several MB each, total maybe 40MB, fine.

Actually let me build them lazily in module-level variables via a function called at module level.

Let me just write it plainly.

```python
_SMALL = _build_readme("Triagers", [f"user{i}" for i in range(200)], header_level=2, seed=1)
```
Wait username first: "user0".

Case 2: 120k members, target = "user119999".

Building 120k usernames list: fine.

Let me write a helper that builds directly from count and target.

```python
def _section_readme(section_name, n, target_index=None, target_username=None, header_level=2, suffix=True, seed=0):
    rng = random.Random(seed)
    lines = []
    for i in range(n):
        u = target_username if (target_index is not None and i == target_index) else f"user{i}"
        lines.append(_member_line(rng, u))
    ...
```

Hmm need usernames unique-ish. Let me just generate usernames as f"user{i}" and allow override at target index.

Let me write final code.

```python
import importlib
import random

_remove_member_line = importlib.import_module('move-to-emeritus')._remove_member_line

_FIRST = [...]
_LAST = [...]

def _display_name(rng):
    return f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"

def _member_line(rng, username, joined=None):
    if joined is None:
        joined = f"20{rng.randint(10,24)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"
    return f"- [{_display_name(rng)}](https://github.com/{username}) - joined {joined}\n"
```

Build readme:

```python
def _make_readme(section_name, usernames, header_level=2, leading=(), trailing=True, seed=0):
    rng = random.Random(seed)
    parts = ["# Community\n\nWe are a community of contributors.\n\n"]
    for name, users in leading:
        parts.append(f"{'#'*header_level} {name}\n\n")
        parts.append("".join(_member_line(rng, u) for u in users))
        parts.append("\n")
    parts.append(f"{'#'*header_level} {section_name}\n\n")
    parts.append("".join(_member_line(rng, u) for u in usernames))
    parts.append("\n")
    if trailing:
        parts.append(f"{'#'*header_level} Resources\n\nSee the docs.\n")
    return "".join(parts)
```

Note: end_pattern `^#{1,header_level}(?!#)\s` — with header_level=2, a line "## Resources" matches "##" then space. Good. A line "# Community" matches "#" then " " (next char is space, since after "#" comes " "). Wait "# Community" — `#{1,2}` matches "#", then `(?!#)` next char is " ", ok, then `\s` matches " ". So "# Community" is a valid end. But it's before the section, so search starts from match.end() of section header. Fine.

Now cases data.

Let me define module-level data.

```python
def _users(n, prefix="user"):
    return [f"{prefix}{i}" for i in range(n)]

# case 1: small
_R1 = _make_readme("Triagers", _users(200), seed=1)
# case 2: large, hit near end
_u2 = _users(120000)
_u2[119999] = "targetuser"
_R2 = _make_readme("Approvers", _u2, seed=2)
```

Hmm but _users(120000) with prefix "user" and then override index 119999 to "targetuser" — that removes "user119999". Fine.

Case 3: large miss: _users(120000), target "ghostuser" not present.
Case 4: section not found: big readme with several sections, ask for "Nonexistent".
Case 5: duplicates: 60000 users, with "dupuser" at every 1000th index.
Case 6: case-insensitive: 60000 users, target "MixedCaseUser" and search "mixedcaseuser".
Case 7: level 3 section, 80000 users.
Case 8: no trailing header, 100000 users, hit near end.

Let me also add leading sections to make _find_section do more work (it scans whole readme). Good — add several leading sections.

For case 4 (section not found), make readme with many sections so the regex search scans everything and returns None.

Let me write it.

Memory: 120000 lines * ~70 chars = 8.4MB each. Several such → maybe 50MB total. Fine.

Time to build: generating 500k+ lines with rng calls — fast, under a few seconds.

Let me now consider the timing: regex search on 8MB with MULTILINE. Python re is maybe ~50-100 MB/s for simple patterns... could be 100ms+. That's within range. Good. Actually the pattern `^[-*+] \[[^\]]+\]\(https://github\.com/...` is more complex. Should be fine, a few ms to tens of ms.

Let me reduce counts a bit to be safe: large ones 100000. Total lines ~ 400k. Fine.

Let me finalize:

- case1: 200 members, Triagers, target "user0" (hit first).
- case2: 100000 members, Approvers, target at index 99999.
- case3: 100000 members, Maintainers, target "ghostuser" (miss).
- case4: section not found; readme with 5 leading sections of 20000 each + target section 20000, ask "Archived Maintainers".
- case5: 60000 members with duplicates of "dupuser" at indices 0, 1000, 2000, ...; target "dupuser".
- case6: 60000 members, target "MixedCaseUser" at index 30000, search "mixedcaseuser".
- case7: level 3 section, 80000 members, target at index 79999.
- case8: 100000 members, no trailing header, target at index 50000.

All distinct labels.

Wait case 7: header_level=3. End pattern `#{1,3}(?!#)\s`. Our trailing "### Resources" would match. Fine. But also note the leading "# Community" — level 1 matches `#{1,3}` then `(?!#)` space. But that's before. Fine.

Hmm, careful with case 7: `_find_section` pattern `^(#{2,3})\s+section\s*$`. Level 3 header "### Triagers" matches group(1)="###", header_level=3. Good.

For case 8, trailing=False so end=len(readme).

Now the thunk returns (readme, section_name, username).

Let me write checks:

```python
def checks():
    return [
        ("empty", lambda: ("", "Triagers", "alice")),
        ("no-such-section", lambda: ("# Title\n\n## Other\n- [A](https://github.com/a) - x\n", "Triagers", "a")),
        ("user-absent", lambda: ("# T\n\n## Triagers\n- [A](https://github.com/a) - x\n", "Triagers", "nobody")),
    ]
```

Good.

Now writing final code. Need WORKDIR? Not used. Fine.

One concern: `importlib.import_module('move-to-emeritus')` — module name with hyphens works via importlib. Good.

Also the module imports urllib etc., fine.

Let me write display name generation with rng — but for 100k lines calling rng.choice twice each is fine.

Potential issue: usernames like "user0" also appear in display names? No.

Another subtlety: the regex uses `re.escape(username)` and searches for `https://github.com/{username}`. Since usernames are "user1", "user10", "user100" — searching for "user1" would match "user1)" in... wait the pattern requires `\)` right after username. `https://github\.com/user1\)` — for "user10" the URL is "https://github.com/user10)" so after "user1" comes "0", not ")". So no false match. Good. But for target "user0": "https://github.com/user0)" — but "user0" is a prefix of "user01"? There's no "user01" since indices 0..199 → "user0".."user199". "user0)" only matches exact. Good.

Hmm but wait, for case 1 target "user0", the pattern `https://github\.com/user0\)` — could it match inside "https://github.com/user0..." where the next char is ")"? Only exact. Good.

For case 2 target at index 99999 = "targetuser". Good.

Let me double check the duplicates case: "dupuser" placed at indices 0, 1000, ... The regex removes the FIRST match only. Fine.

Now, does the function's output size stay under 100k values? Output is a string ~8MB. "under about 100 000 values" — a string is one value. Fine.

Input rendering: readme string as one value. Fine.

Let me write it.

Actually, let me reconsider build time: 100k lines each with 2 rng.choice and f-strings. ~600k lines total across cases. Each line maybe 2µs → ~1.2s. Fine.

Let me write the final code.

One more: `_make_readme` leading sections param. For case 4 I'll pass leading list.

Let me write:

```python
def _make_readme(section_name, usernames, header_level=2, leading=(), trailing=True, seed=0):
```

leading is tuple of (name, usernames list).

Now code.

I'll compute module-level readmes.

Let me be careful with memory: storing 8 readmes + username lists. Username lists of 100k strings ~ 6MB each. Could drop them after building readme (they're local). Fine.

Write final.