You are a performance testing expert. You will write the inputs for an energy measurement of one Python function from a real repository. We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs.

# What to write
Python source defining two functions, `checks()` and `cases()`. Each returns a list of `(label, thunk)` pairs with distinct labels. A thunk takes no arguments and returns a tuple of positional arguments for the function, e.g. `lambda: (rows, 3)`. For keyword arguments the thunk returns `call(...)`, e.g. `lambda: call(rows, sep=",")`; `call` is provided, do not import or define it. A method is called as a plain function: the thunk builds the instance and passes it as the first argument (a classmethod gets its class there, a staticmethod nothing; the task says which).
**The thunk returns the arguments; it never calls the function under test.** We call the function with them, and time only that call.

# Instructions
1. **Setup is never timed**: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed.

2. **`cases()`: exactly 8 measured inputs.** We run them on the original function and keep the 4 that do the most work.
    - Define a real workload: the kind of data this function gets in this repository (see where the repository calls it). Use realistic scale and complexity, and a fixed random seed (`random.Random(0)`) when generating data.
    - Generate stressful inputs: complex, time-consuming, as diverse as possible. Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths.
    - Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes.
    - One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped. Keep the data in memory under about 100 MB, and building all inputs under about 10 s.
    - The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values.
    - Every case must run to completion on the original function without raising.

3. **`checks()`: 2 or 3 small edge inputs** (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise.

4. **Build real inputs; never replace code.** No mocks, no monkeypatching, no `unittest.mock`, no assigning functions or lambdas to attributes, and no subclass that overrides a method of a repository or library class -- a subclass whose `get` returns canned data instead of making the request is a mock too. Setting data (a module's configuration, an object's fields) to build an input is fine. No network access, no subprocesses. Do not fake the environment either: no stand-in programs on `PATH`, no fake system files.
    - Module globals the function reads must be set on the repository's own module (`import pricing; pricing.args = ...`, `hyperlink.slugs.update(...)`); a variable of the same name in your source is a different variable and the function never sees it.
    - Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk.

5. **Files**: if the function reads files, create them under `WORKDIR` (a provided `pathlib.Path`; do not define it), in module-level code or in the thunk. Anything the function writes must go under `WORKDIR` too.

6. **Same work on every call**: the call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts. So keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy (`list(data)`, `dict(data)`) if the function changes it (adds to a dict, sorts or fills a list in place). Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys (e.g. with `itertools.count()`), so every call takes the same path. If it creates files, have the thunk remove them first. No time-dependent or unseeded random behaviour.

7. Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports. Everything you can know about the repository is in the task: do not try to recall its code from memory, and build the inputs from the classes and functions shown there.

8. **If the function cannot run here at all** -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`. A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer.

Decide on the inputs and write the code: simple inputs that run are better than clever ones that do not.

# Output format
Exactly one ```python block holding the complete source. An example for a function `summarize(rows, top=10)`:
```python
import random

def _rows(n, columns, seed):
    rng = random.Random(seed)
    return [{f"c{j}": rng.randint(0, 10**6) for j in range(columns)} for _ in range(n)]

def checks():
    return [
        ("empty",      lambda: ([],)),                            # summarize([])
        ("none-value", lambda: ([{"c0": None}],)),
    ]

def cases():
    return [
        ("typical",    lambda: (_rows(2_000, 4, 0),)),            # summarize(rows)
        ("top-100",    lambda: call(_rows(5_000, 4, 1), top=100)), # summarize(rows, top=100)
        # ... 8 in total
    ]
```
A second example, for a method `Index.lookup(self, words)` of `search/index.py`. The instance is built in the thunk and passed first; the vocabulary file it reads is created under `WORKDIR`; a module setting it reads is set on the repository's own module; and because it records the words it has seen in `self.seen`, every thunk call gets words of its own, so that every call takes the same path:
```python
import itertools
import random
import search.index
from search.index import Index

search.index.CASE_SENSITIVE = False                  # a setting the method reads: data, set on its module
_VOCAB = WORKDIR / "vocab.txt"                       # a file it reads
_VOCAB.write_text("\n".join(f"w{i}" for i in range(50_000)))
_batch = itertools.count()

def _words(n, hit_ratio, seed):
    rng = random.Random(seed)
    b = next(_batch)                                 # fresh misses for every thunk call
    return [f"w{rng.randrange(50_000)}" if rng.random() < hit_ratio else f"x{b}_{i}"
            for i in range(n)]

def checks():
    return [("no-words", lambda: (Index(_VOCAB), []))]

def cases():
    return [
        ("mostly-hits",   lambda: (Index(_VOCAB), _words(20_000, 0.9, 0))),
        ("mostly-misses", lambda: (Index(_VOCAB), _words(20_000, 0.1, 1))),
        # ... 8 in total
    ]
```


=== USER ===

Repository: community
Function under test: `_parse_members` in `scripts/move-to-emeritus.py`
Import it as `_parse_members = importlib.import_module('move-to-emeritus')._parse_members` (the file name is not an identifier).

## The function
```python
def _parse_members(text):
    """Parse member entries from a README section text.

    Returns list of dicts: {"name", "username", "line"}
    """
    member_re = re.compile(
        r'^[-*+] \[([^\]]+)\]\(https://github\.com/([^)]+)\)(?:,\s*(.+))?$',
        re.MULTILINE,
    )
    members = []
    for m in member_re.finditer(text):
        members.append({
            "name": m.group(1),
            "username": m.group(2),
            "line": m.group(0),
        })
    return members
```

## Imports of its module
```python
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta, timezone
```

## Everything else its module defines (headers only)
```python
def debug(msg):
def _search_fields():
def _extract_numbers(search_result):
def _fmt_numbers(numbers):
def get_cutoff_date():
def request_with_retry(method, url, data=None, retries=5):
def read_json(resp):
def paginate_rest(url, params=None):
def _get_all_teams():
def get_teams_by_role(role_keyword):
def get_team_members(team_slug):
def get_team_repos(team_slug, cutoff):
def _get_repo_commenters(repo, cutoff):
def _get_repo_events(repo, cutoff):
def _check_comments(remaining, repo, cutoff, comment_type=None, exclude_pr=None):
def _check_events(remaining, repo, cutoff, event_types, exclude_pr=None):
def _verify_review_candidates(user, candidate_prs, repo, cutoff):
def _check_reviews_paginated(user, repo, cutoff, start_cursor, exclude_pr=None):
def _check_reviews(remaining, repo, cutoff, exclude_pr=None):
def check_triager_activity(usernames, repos, cutoff, exclude_pr=None):
def check_approver_activity(usernames, repos, cutoff, exclude_pr=None):
def check_maintainer_activity(usernames, repos, cutoff, exclude_pr=None):
def _get_emeritus_pr_number(repo):
def fetch_readme(repo):
def _find_section(readme, section_name):
def _detect_list_marker(section_text):
def _remove_member_line(readme, section_name, username):
def _add_to_emeritus(readme, emeritus_title, member_entry, header_level=3):
def _get_display_name(username):
def _to_emeritus_entry(username, role_label, display_name=None, marker="-"):
def _get_fork_owner():
def _ensure_fork(repo):
def _get_default_branch_sha(repo):
def _ensure_branch(owner, repo, branch, base_sha):
def _update_file(owner, repo, path, content, sha, branch, message):
def _create_pr(repo, head_owner, branch, base, title, body):
def _build_pr_body(repo, changes, cutoff, warning=None):
def _build_issue_body(changes):
def _create_followup_issue(repo, changes):
def create_emeritus_prs(inactive_report, repo_warnings, cutoff):
def main():
```

## Where the repository calls it or builds its class
```python
# scripts/move-to-emeritus.py:1210
                section = _find_section(readme, section_name)
                if section:
                    start, end, header_level = section
                    section_text = readme[start:end]
                    for m in _parse_members(section_text):
                        if m["username"].lower() == user.lower():
                            display_name = m["name"]
                            marker = _detect_list_marker(section_text)
```

Write `checks()` and `cases()` for `_parse_members`. Remember: setup in the thunk or at module level, never timed.