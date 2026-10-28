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
Function under test: `_check_reviews` in `scripts/move-to-emeritus.py`
Import it as `_check_reviews = importlib.import_module('move-to-emeritus')._check_reviews` (the file name is not an identifier).

## The function
```python
def _check_reviews(remaining, repo, cutoff, exclude_pr=None):
    """Check for PR review activity. Returns dict of {username: [pr_numbers]}.

    Batches the first GraphQL page for up to 10 users at a time, then
    REST-verifies candidates. Users not confirmed active from the first page
    are paginated individually through remaining results.
    exclude_pr: PR number to skip (activity on the move-to-emeritus PR itself doesn't count).
    """
    if not remaining:
        return {}

    active = {}
    remaining_list = list(remaining)
    batch_size = 10
    page_size = 10

    for i in range(0, len(remaining_list), batch_size):
        batch_users = remaining_list[i : i + batch_size]
        if not batch_users:
            continue

        # Batched first-page GraphQL query for all users in this batch
        aliases = []
        for user in batch_users:
            safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
            review_q = f'type:pr repo:{ORG}/{repo} reviewed-by:{user} updated:>={cutoff}'
            aliases.append(
                f'{safe}_reviews: search(query: "{review_q}", type: ISSUE, first: {page_size}) '
                f'{{ pageInfo {{ hasNextPage endCursor }} nodes {{ ... on PullRequest {{ number }} }} }}'
            )

        query = "query { " + "\n".join(aliases) + " }"
        resp = request_with_retry("POST", GRAPHQL_API, data={"query": query})
        data = read_json(resp)
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}", file=sys.stderr)
            sys.exit(1)

        # Verify candidates and paginate if needed
        for user in batch_users:
            safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
            result = data["data"].get(f"{safe}_reviews") or {}
            candidate_prs = [n["number"] for n in result.get("nodes", []) if "number" in n]
            if exclude_pr is not None:
                candidate_prs = [n for n in candidate_prs if n != exclude_pr]

            pr = _verify_review_candidates(user, candidate_prs, repo, cutoff)
            if pr is not None:
                active[user] = [pr]
                continue

            # First page didn't confirm activity — paginate if more pages exist
            page_info = result.get("pageInfo", {})
            if page_info.get("hasNextPage"):
                cursor = page_info.get("endCursor")
                pr = _check_reviews_paginated(user, repo, cutoff, cursor, exclude_pr=exclude_pr)
                if pr is not None:
                    active[user] = [pr]

    return active
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

## Definitions it uses from the same module
```python
ORG = "open-telemetry"

GRAPHQL_API = "https://api.github.com/graphql"

def request_with_retry(method, url, data=None, retries=5):
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=HEADERS, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
            body = json.dumps(data).encode("utf-8")
        else:
            body = None
        try:
            resp = urllib.request.urlopen(req, body, timeout=30)
            remaining = resp.headers.get("x-ratelimit-remaining")
            if remaining is not None and int(remaining) < 100:
                print(f"  [WARN] Rate limit low: {remaining} requests remaining")
            return resp
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                remaining = e.headers.get("x-ratelimit-remaining", "?")
                retry_after = e.headers.get("retry-after")
                reset_time = e.headers.get("x-ratelimit-reset")
                if retry_after:
                    wait = int(retry_after)
                elif reset_time:
                    wait = max(0, int(reset_time) - int(time.time())) + 1
                else:
                    wait = 60
                wait = min(wait, MAX_RATE_LIMIT_WAIT)
                print(f"Rate limited ({remaining} remaining). Waiting {wait}s before retry...")
                time.sleep(wait)
                continue
            if 500 <= e.code < 600:
                # Transient server error — retry with backoff
                print(f"Attempt {attempt} failed: HTTP {e.code}")
                if attempt < retries:
                    time.sleep(2 ** attempt)
                else:
                    raise
                continue
            # 4xx (other than 429/403): deterministic — don't retry
            raise
        except (TimeoutError, OSError) as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(2)
            else:
                raise
    return None

def read_json(resp):
    return json.loads(resp.read().decode("utf-8"))

def _verify_review_candidates(user, candidate_prs, repo, cutoff):
    """Verify candidate PRs via REST to confirm actual review dates.

    Returns the first PR number with a confirmed recent review, or None.
    """
    for pr_number in candidate_prs:
        reviews_url = f"{REST_API}/repos/{ORG}/{repo}/pulls/{pr_number}/reviews"
        rev_resp = request_with_retry("GET", reviews_url)
        reviews = read_json(rev_resp)
        for review in reviews:
            submitted = review.get("submitted_at", "")[:10]
            reviewer = (review.get("user") or {}).get("login", "")
            if reviewer == user and submitted >= cutoff:
                return pr_number
    return None

def _check_reviews_paginated(user, repo, cutoff, start_cursor, exclude_pr=None):
    """Paginate through remaining GraphQL results for a single user.

    Called only when the batched first page didn't confirm activity.
    Returns a PR number with confirmed review, or None.
    exclude_pr: PR number to skip.
    """
    safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
    review_q = f'type:pr repo:{ORG}/{repo} reviewed-by:{user} updated:>={cutoff}'
    cursor = start_cursor

    while cursor:
        query = (
            f'query {{ {safe}_reviews: search(query: "{review_q}", type: ISSUE, first: 10, after: "{cursor}") '
            f'{{ pageInfo {{ hasNextPage endCursor }} nodes {{ ... on PullRequest {{ number }} }} }} }}'
        )
        resp = request_with_retry("POST", GRAPHQL_API, data={"query": query})
        data = read_json(resp)
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}", file=sys.stderr)
            sys.exit(1)

        result = data["data"].get(f"{safe}_reviews") or {}
        candidate_prs = [n["number"] for n in result.get("nodes", []) if "number" in n]
        if exclude_pr is not None:
            candidate_prs = [n for n in candidate_prs if n != exclude_pr]

        pr = _verify_review_candidates(user, candidate_prs, repo, cutoff)
        if pr is not None:
            return pr

        page_info = result.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    return None
```

## Everything else its module defines (headers only)
```python
def debug(msg):
def _search_fields():
def _extract_numbers(search_result):
def _fmt_numbers(numbers):
def get_cutoff_date():
def paginate_rest(url, params=None):
def _get_all_teams():
def get_teams_by_role(role_keyword):
def get_team_members(team_slug):
def get_team_repos(team_slug, cutoff):
def _get_repo_commenters(repo, cutoff):
def _get_repo_events(repo, cutoff):
def _check_comments(remaining, repo, cutoff, comment_type=None, exclude_pr=None):
def _check_events(remaining, repo, cutoff, event_types, exclude_pr=None):
def check_triager_activity(usernames, repos, cutoff, exclude_pr=None):
def check_approver_activity(usernames, repos, cutoff, exclude_pr=None):
def check_maintainer_activity(usernames, repos, cutoff, exclude_pr=None):
def _get_emeritus_pr_number(repo):
def fetch_readme(repo):
def _find_section(readme, section_name):
def _parse_members(text):
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
# scripts/move-to-emeritus.py:557
        if not remaining:
            return active

        # 3. Check PR reviews via REST
        found_reviews = _check_reviews(remaining, repo, cutoff, exclude_pr=exclude_pr)
        for user, numbers in found_reviews.items():
            debug(f"approver {user} active on {repo}: PR reviews{_fmt_numbers(numbers)}")
            active.add(user)

# scripts/move-to-emeritus.py:613
        if not remaining:
            return active

        # 3. Check PR reviews via REST
        found_reviews = _check_reviews(remaining, repo, cutoff, exclude_pr=exclude_pr)
        for user, numbers in found_reviews.items():
            debug(f"maintainer {user} active on {repo}: PR reviews{_fmt_numbers(numbers)}")
            active.add(user)
```

Write `checks()` and `cases()` for `_check_reviews`. Remember: setup in the thunk or at module level, never timed.