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
Function under test: `main` in `scripts/move-to-emeritus.py`
Import it as `main = importlib.import_module('move-to-emeritus').main` (the file name is not an identifier).

## The function
```python
def main():
    global DEBUG
    parser = argparse.ArgumentParser(description="Check for inactive org members")
    parser.add_argument("--debug", action="store_true",
                        help="Print why each member was marked as active")
    parser.add_argument("--create-prs", action="store_true",
                        help="Create PRs to move inactive members to emeritus in each repo")
    parser.add_argument("--repo", nargs="+", default=None,
                        help="Only check specific repo(s) (e.g. opentelemetry-python opentelemetry-collector)")
    args = parser.parse_args()
    DEBUG = args.debug

    cutoff = get_cutoff_date()
    print(f"Checking for inactivity since {cutoff} ...\n")

    role_priority = {"Triager": 0, "Approver": 1, "Maintainer": 2}
    check_fns = {
        "Triager": check_triager_activity,
        "Approver": check_approver_activity,
        "Maintainer": check_maintainer_activity,
    }

    # Phase 1: Collect all user-team-repo relationships
    # user -> {"role": highest role, "entries": [(team_name, role_label)],
    #          "team_repos": {team_name: set(repos)}}
    all_user_data = {}
    team_repos_map = {}  # team_name -> set(repos)
    repo_maintainer_count = {}

    for role in ROLES:
        keyword = role["keyword"]
        label = role["label"]

        print(f"Fetching {label.lower()} teams...")
        teams = get_teams_by_role(keyword)
        if not teams:
            print(f"No {label.lower()} teams found.\n")
            continue

        for team in teams:
            slug = team["slug"]
            name = team["name"]
            team_name_lower = name.lower()
            print(f"  Fetching members and repos for '{name}'...")
            members = get_team_members(slug)
            repos = get_team_repos(slug, cutoff)

            # Filter to a list of repos if --repo is specified
            if args.repo:
                repos = [r for r in repos if r in args.repo]

            # Filter out ignored repos
            repos = [r for r in repos if r not in IGNORED_REPOS]

            # For repos with allowed-teams lists, skip this team if not allowed
            filtered_repos = []
            for r in repos:
                if r in REPO_ALLOWED_TEAMS:
                    if slug not in REPO_ALLOWED_TEAMS[r]:
                        continue
                if r in REPO_IGNORED_TEAM_KEYWORDS:
                    if any(kw in team_name_lower for kw in REPO_IGNORED_TEAM_KEYWORDS[r]):
                        continue
                filtered_repos.append(r)
            repos = filtered_repos

            print(f"Team '{name}': {len(members)} member(s), {len(repos)} repo(s)")

            if not members or not repos:
                continue

            # Track maintainer counts per repo
            if keyword == "maintainer":
                for repo in repos:
                    repo_maintainer_count.setdefault(repo, set())
                    repo_maintainer_count[repo].update(members)

            # Record team -> repos mapping
            team_repos_map[name] = set(repos)

            # Record user data
            for user in members:
                if user not in all_user_data:
                    all_user_data[user] = {
                        "role": label,
                        "priority": role_priority[label],
                        "entries": [],
                        "team_repos": {},
                    }
                all_user_data[user]["entries"].append((name, label))
                all_user_data[user]["team_repos"].setdefault(name, set()).update(repos)
                if role_priority[label] > all_user_data[user]["priority"]:
                    all_user_data[user]["role"] = label
                    all_user_data[user]["priority"] = role_priority[label]

        print()

    if not all_user_data:
        print("No users found to check.")
        return

    # Phase 2: Check activity per repo using the user's highest role for that repo.
    # If a user is on X-maintainer and X-approver (both covering repo X),
    # they are checked with maintainer criteria only. Activity on any repo in a
    # team satisfies that team.

    # Step 2a: For each user+repo, determine the highest role across all teams
    # user_repo_role: {user -> {repo -> highest_role}}
    user_repo_role = {}
    for user, data in all_user_data.items():
        for team_name, role_label in data["entries"]:
            for repo in data["team_repos"].get(team_name, set()):
                user_repo_role.setdefault(user, {})
                current = user_repo_role[user].get(repo)
                if current is None or role_priority[role_label] > role_priority[current]:
                    user_repo_role[user][repo] = role_label

    # Step 2b: Group by (repo, role) for batched checking
    repo_role_users = {}  # repo -> {role_label -> set(usernames)}
    for user, repo_roles in user_repo_role.items():
        for repo, role_label in repo_roles.items():
            repo_role_users.setdefault(repo, {})
            repo_role_users[repo].setdefault(role_label, set()).add(user)

    # Step 2c: Check activity per repo
    repo_active = {}  # repo -> set of active usernames
    all_repos = sorted(repo_role_users.keys())
    print(f"Checking activity across {len(all_repos)} repo(s)...")
    for repo in all_repos:
        # Exclude the existing move-to-emeritus PR so users who only commented/approved
        # that PR are not mistakenly counted as active contributors.
        emeritus_pr = _get_emeritus_pr_number(repo)
        active_on_repo = set()
        for role_label in ["Maintainer", "Approver", "Triager"]:
            users = list(repo_role_users[repo].get(role_label, []))
            if not users:
                continue
            check_fn = check_fns[role_label]
            active = check_fn(users, [repo], cutoff, exclude_pr=emeritus_pr)
            active_on_repo.update(active)
        repo_active[repo] = active_on_repo

    # Step 2d: Map repo-level activity back to teams.
    # A user is active for a team if they are active on ANY of that team's repos.
    team_active = {}  # team_name -> set of active usernames
    for user, data in all_user_data.items():
        for team_name in data["team_repos"]:
            for repo in data["team_repos"][team_name]:
                if user in repo_active.get(repo, set()):
                    team_active.setdefault(team_name, set()).add(user)
                    break

    # Phase 3: Build inactive report
    # repo -> list of (username, team_name, role_label)
    # A user is flagged on a repo only if they are inactive for the team
    # that links them to that repo.
    inactive_report = {}
    for user, data in all_user_data.items():
        for team_name, role_label in data["entries"]:
            if user in team_active.get(team_name, set()):
                continue
            # User is inactive for this team — flag on all of the team's repos
            for repo in data["team_repos"].get(team_name, set()):
                inactive_report.setdefault(repo, [])
                inactive_report[repo].append((user, team_name, role_label))

    # Print report
    if not inactive_report:
        print("All members have been active. Nothing to report.")
        return

    print("=" * 60)
    print("INACTIVE MEMBERS REPORT")
    print(f"(no activity since {cutoff})")
    print("=" * 60)

    # Pre-compute maintainer health warnings per repo
    repo_warnings = {}
    for repo, inactive in inactive_report.items():
        if repo not in repo_maintainer_count:
            continue
        inactive_maintainers = {
            user for user, _, role_label in inactive
            if role_label == "Maintainer"
        }
        if not inactive_maintainers:
            continue
        total = len(repo_maintainer_count[repo])
        remaining = total - len(inactive_maintainers & repo_maintainer_count[repo])
        if remaining <= 1:
            if remaining == 0:
                repo_warnings[repo] = f"  WARNING: {total} -> 0 maintainers. Repo will have NO maintainers! Consider adding new maintainers before merging this PR."
            else:
                repo_warnings[repo] = f"  WARNING: {total} -> {remaining} maintainer. Repo will have only 1 maintainer! Consider adding new maintainers before merging this PR."

    total_inactive = 0
    for repo, inactive in sorted(inactive_report.items()):
        print(f"\n{ORG}/{repo}:")
        if repo in repo_warnings:
            print(repo_warnings[repo])
    # ... (truncated)
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
DEBUG = False

def debug(msg):
    if DEBUG:
        print(f"  [DEBUG] {msg}")

ORG = "open-telemetry"

IGNORED_REPOS = {
    "community",
    "cpp-build-tools", # Low traffic and stable repo
    "govanityurls", # Low traffic repo
    "opentelemetry-go-build-tools", # Low traffic repo
    "opentelemetry-network", # Low traffic and stable repo
    "opentelemetry-specification", # Too complex for simple checks. More checks can be added in the future
    "semantic-conventions", # Too complex for simple checks. More checks can be added in the future
    "opentelemetry-proto", # Too complex for simple checks. More checks can be added in the future
    "opentelemetry-proto-java", # Inherits maintainers/approvers from other repos
    "opentelemetry-java-examples", # Inherits maintainers/approvers from other repos
    "semantic-conventions-java", # Inherits maintainers/approvers from other repos
    "sig-contributor-experience", # Majority of work is done outside of github
    "sig-developer-experience", # Majority of work is done outside of github
    "sig-end-user", # Majority of work is done outside of github
}

REPO_ALLOWED_TEAMS = {
    "opentelemetry.io": {
        "docs-triagers",
        "docs-approvers",
        "docs-maintainers",
        "blog-approvers",
    },
}

REPO_IGNORED_TEAM_KEYWORDS = {
    "opentelemetry-js": ["browser"],
    "opentelemetry-js-contrib": ["browser", "javascript-contrib-triagers"], # Contrib triager is a complex team working similar to codeowners, so we skip it for now
    "opentelemetry-collector-releases": ["helm", "collector-contrib"], # Those teams are able to review PRs, but have low activity level
    "weaver": ["semconv"], # Semconv team is a complex team that won't always be active, so we skip it for now
}

def get_cutoff_date():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=INACTIVITY_MONTHS * 30)
    return cutoff.strftime("%Y-%m-%d")

def get_teams_by_role(role_keyword):
    """Get all org teams with the given keyword in the name."""
    return [t for t in _get_all_teams() if role_keyword in t["name"].lower()]

def get_team_members(team_slug):
    """Get all members of a team."""
    members = paginate_rest(f"{REST_API}/orgs/{ORG}/teams/{team_slug}/members")
    return [m["login"] for m in members]

def get_team_repos(team_slug, cutoff):
    """Get all public repos assigned to a team, excluding repos created after cutoff."""
    repos = paginate_rest(f"{REST_API}/orgs/{ORG}/teams/{team_slug}/repos")
    return [
        r["name"] for r in repos
        if not r.get("private", False)
        and r.get("created_at", "")[:10] <= cutoff
    ]

def check_triager_activity(usernames, repos, cutoff, exclude_pr=None):
    """Check if triagers are active across any of the given repos since cutoff.

    Returns a set of usernames that have been active.
    A triager is considered active if they did any of the following
    on ANY repo in the team:
      - Added a comment on an issue or PR
      - Added or removed a label
      - Closed an issue
    Short-circuits: once a user is found active on one repo, they are
    not checked on the remaining repos.
    exclude_pr: PR number to exclude from activity (e.g. the move-to-emeritus PR itself).
    """
    if not usernames or not repos:
        return set()

    active = set()
    remaining = set(usernames)

    for repo in repos:
        if not remaining:
            break

        # 1. Check comments via REST API
        found = _check_comments(remaining, repo, cutoff, exclude_pr=exclude_pr)
        for user, numbers in found.items():
            debug(f"triager {user} active on {repo}: commented on issue/PR{_fmt_numbers(numbers)}")
        active.update(found.keys())
        remaining -= found.keys()
        if not remaining:
            return active

        # 2. Check label changes and issue closes via cached issue events
        found_events = _check_events(remaining, repo, cutoff, {"labeled", "unlabeled", "closed"}, exclude_pr=exclude_pr)
        for actor, event_list in found_events.items():
            event_type, issue_num = event_list[0]
            debug(f"triager {actor} active on {repo}: {event_type} event #{issue_num}")
            active.add(actor)
            remaining.discard(actor)

    for user in remaining:
        debug(f"triager {user}: not active")
    return active

def check_approver_activity(usernames, repos, cutoff, exclude_pr=None):
    """Check if approvers are active across any of the given repos since cutoff.

    Returns a set of usernames that have been active.
    An approver is considered active if they did any of the following
    on ANY repo in the team:
      - Added a comment on a PR
      - Approved / reviewed a PR
      - Added a comment on an issue
    Short-circuits: once a user is found active on one repo, they are
    not checked on the remaining repos.
    exclude_pr: PR number to exclude from activity (e.g. the move-to-emeritus PR itself).
    """
    if not usernames or not repos:
        return set()

    active = set()
    remaining = set(usernames)

    for repo in repos:
        if not remaining:
            break

        # 1. Check PR comments via REST (avoids updated:>= false positives)
        found_pr = _check_comments(remaining, repo, cutoff, comment_type="pr", exclude_pr=exclude_pr)
        for user, numbers in found_pr.items():
            debug(f"approver {user} active on {repo}: PR comments{_fmt_numbers(numbers)}")
            active.add(user)
            remaining.discard(user)
        if not remaining:
            return active

        # 2. Check issue comments via REST
        found_issue = _check_comments(remaining, repo, cutoff, comment_type="issue", exclude_pr=exclude_pr)
        for user, numbers in found_issue.items():
            debug(f"approver {user} active on {repo}: issue comments{_fmt_numbers(numbers)}")
            active.add(user)
            remaining.discard(user)
        if not remaining:
            return active

        # 3. Check PR reviews via REST
        found_reviews = _check_reviews(remaining, repo, cutoff, exclude_pr=exclude_pr)
        for user, numbers in found_reviews.items():
            debug(f"approver {user} active on {repo}: PR reviews{_fmt_numbers(numbers)}")
            active.add(user)
            remaining.discard(user)
        if not remaining:
            return active

    for user in remaining:
        debug(f"approver {user}: not active")
    return active

def check_maintainer_activity(usernames, repos, cutoff, exclude_pr=None):
    """Check if maintainers are active across any of the given repos since cutoff.

    Returns a set of usernames that have been active.
    A maintainer is considered active if they did ANY of the following
    on any repo in the team:
      - Reviewed PRs
      - Commented on PRs
      - Merged PRs
      - Authored PRs
      - Commented on issues
    Short-circuits once a user is found active.
    exclude_pr: PR number to exclude from activity (e.g. the move-to-emeritus PR itself).
    """
    if not usernames or not repos:
        return set()

    active = set()
    remaining = set(usernames)

    for repo in repos:
        if not remaining:
            break

        # 1. Check PR comments via REST (avoids updated:>= false positives)
        found_pr = _check_comments(remaining, repo, cutoff, comment_type="pr", exclude_pr=exclude_pr)
        for user, numbers in found_pr.items():
            debug(f"maintainer {user} active on {repo}: PR comments{_fmt_numbers(numbers)}")
            active.add(user)
            remaining.discard(user)
        if not remaining:
            return active

        # 2. Check issue comments via REST
        found_issue = _check_comments(remaining, repo, cutoff, comment_type="issue", exclude_pr=exclude_pr)
        for user, numbers in found_issue.items():
            debug(f"maintainer {user} active on {repo}: issue comments{_fmt_numbers(numbers)}")
            active.add(user)
            remaining.discard(user)
        if not remaining:
            return active

        # 3. Check PR reviews via REST
        found_reviews = _check_reviews(remaining, repo, cutoff, exclude_pr=exclude_pr)
        for user, numbers in found_reviews.items():
            debug(f"maintainer {user} active on {repo}: PR reviews{_fmt_numbers(numbers)}")
            active.add(user)
            remaining.discard(user)
        if not remaining:
            return active

        # 4. Check authored PRs via GraphQL (author + created:>= is accurate)
        remaining_list = list(remaining)
        batch_size = 10
        for i in range(0, len(remaining_list), batch_size):
            batch_users = [u for u in remaining_list[i : i + batch_size] if u in remaining]
            if not batch_users:
                continue

            aliases = []
    # ... (truncated)

ROLES = [
    {
        "keyword": "triager",
        "label": "Triager",
        "check_fn": check_triager_activity,
    },
    {
        "keyword": "approver",
        "label": "Approver",
        "check_fn": check_approver_activity,
    },
    {
        "keyword": "maintainer",
        "label": "Maintainer",
        "check_fn": check_maintainer_activity,
    },
]
```

## Everything else its module defines (headers only)
```python
def _search_fields():
def _extract_numbers(search_result):
def _fmt_numbers(numbers):
def request_with_retry(method, url, data=None, retries=5):
def read_json(resp):
def paginate_rest(url, params=None):
def _get_all_teams():
def _get_repo_commenters(repo, cutoff):
def _get_repo_events(repo, cutoff):
def _check_comments(remaining, repo, cutoff, comment_type=None, exclude_pr=None):
def _check_events(remaining, repo, cutoff, event_types, exclude_pr=None):
def _verify_review_candidates(user, candidate_prs, repo, cutoff):
def _check_reviews_paginated(user, repo, cutoff, start_cursor, exclude_pr=None):
def _check_reviews(remaining, repo, cutoff, exclude_pr=None):
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
```

## Where the repository calls it or builds its class
```python
# scripts/move-to-emeritus.py:1504
        create_emeritus_prs(inactive_report, repo_warnings, cutoff)


if __name__ == "__main__":
    main()
```

Write `checks()` and `cases()` for `main`. Remember: setup in the thunk or at module level, never timed.