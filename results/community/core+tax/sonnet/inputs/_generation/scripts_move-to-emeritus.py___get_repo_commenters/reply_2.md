```python
import importlib
import json
import random
import urllib.parse

# The module file name is not an identifier.
_module = importlib.import_module('move-to-emeritus')
_get_repo_commenters = _module._get_repo_commenters

_ORG = _module.ORG

# The function reads REST_API from its own module.  Point it at a local
# file:// root so that the single HTTP "page" it fetches comes from a file we
# create under WORKDIR (setup only, never timed).
_BASE = WORKDIR.resolve()
_module.REST_API = "file://" + str(_BASE)

_CUTOFF = "2024-01-01"


def _query(cutoff):
    """Exactly the query string the function appends to its URL."""
    return urllib.parse.urlencode({
        "since": f"{cutoff}T00:00:00Z",
        "per_page": 100,
        "sort": "created",
        "direction": "desc",
    })


def _publish(repo, cutoff, comments):
    """Materialise the response body at the path the file:// handler will use.

    The URL the function builds carries its query string in the last path
    segment; urllib's file handler unquotes the selector, so we write both the
    quoted and the unquoted name (they are the same file name except for the
    percent-escapes of the timestamp).
    """
    d = _BASE / "repos" / _ORG / repo / "issues"
    d.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(comments).encode("utf-8")
    qs = _query(cutoff)
    for name in dict.fromkeys(("comments?" + qs, "comments?" + urllib.parse.unquote(qs))):
        (d / name).write_bytes(payload)


def _thunk(repo, cutoff=_CUTOFF):
    """Args for one call; the repo's cache entry is dropped so every call runs
    the whole body again (the function stores its result in a module cache)."""
    def thunk():
        _module._repo_comments_cache.clear()
        return (repo, cutoff)
    return thunk


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
        "html_url": f"https://github.com/{_ORG}/{repo}/{seg}/{number or 1}#issuecomment-{idx}",
        "issue_url": issue_url,
    }


def _build():
    """Yields (label, repo, comments) — one realistic response page each."""
    # 1. Typical mixed activity: many users, both PR and issue comments, plus
    #    some genuine repeats of an earlier (user, number, kind) triple.
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

    # 2. One power commenter: every distinct PR number forces the
    #    "number not in commenters[user][kind]" scan over a growing list.
    repo = "otel-power-commenter"
    rng = random.Random(2)
    out = []
    for i in range(3500):
        if i < 2500:
            num = 2000 + i
        else:
            num = 2000 + rng.randrange(2500)
        out.append(_comment(repo, i, "power-user", _ts(rng), num, True))
    yield "power-commenter", repo, out

    # 3. Issue-only chatter across many users.
    repo = "otel-issue-chatter"
    rng = random.Random(3)
    out = []
    for i in range(15_000):
        user = "chatter%04d" % rng.randrange(600)
        num = 1 + rng.randrange(3000)
        out.append(_comment(repo, i, user, _ts(rng), num, False))
    yield "issue-chatter", repo, out

    # 4. PR-only reviews with a heavy duplicate ratio (many membership hits).
    repo = "otel-pr-reviewers"
    rng = random.Random(4)
    numbers = [5000 + i for i in range(400)]
    out = []
    for i in range(15_000):
        user = "reviewer%03d" % rng.randrange(300)
        out.append(_comment(repo, i, user, _ts(rng), numbers[rng.randrange(400)], True))
    yield "pr-reviewers", repo, out

    # 5. One drive-by commenter per entry: 12k distinct users in the result.
    repo = "otel-drive-by-commenters"
    rng = random.Random(5)
    out = []
    for i in range(12_000):
        out.append(_comment(repo, i, "driveby%05d" % i, _ts(rng), 20000 + i, i % 2 == 0))
    yield "drive-by-commenters", repo, out

    # 6. Anonymous / blank-login comments that the function must skip.
    repo = "otel-anonymous-comments"
    rng = random.Random(6)
    out = []
    for i in range(12_000):
        r = rng.random()
        num = 30000 + rng.randrange(2000)
        is_pr = rng.random() < 0.5
        if r < 0.45:
            user = None
        elif r < 0.65:
            user = ""
        else:
            user = "named%03d" % rng.randrange(200)
        out.append(_comment(repo, i, user, _ts(rng), num, is_pr))
    yield "anonymous-comments", repo, out

    # 7. Half of the comments have no issue_url (number == 0 -> no append).
    repo = "otel-url-less-comments"
    rng = random.Random(7)
    out = []
    for i in range(12_000):
        user = "urluser%04d" % rng.randrange(500)
        num = 0 if rng.random() < 0.5 else 40000 + rng.randrange(3000)
        out.append(_comment(repo, i, user, _ts(rng), num, rng.random() < 0.5))
    yield "url-less-comments", repo, out

    # 8. Descending page that hits comments older than the cutoff: the loop
    #    bails out early after the first 4000 in-range comments.
    repo = "otel-stale-comments"
    rng = random.Random(8)
    out = []
    for i in range(8000):
        if i < 4000:
            created = (f"2024-{rng.randint(2, 6):02d}-{rng.randint(1, 28):02d}"
                       f"T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00Z")
        else:
            created = (f"2023-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
                       f"T{rng.randint(0, 23):02d}:00:00Z")
        out.append(_comment(repo, i, "user%04d" % rng.randrange(400),
                            created, 50000 + rng.randrange(1500), rng.random() < 0.5))
    yield "stale-cutoff", repo, out


_REPOS = {}
for _label, _repo, _comments in _build():
    _publish(_repo, _CUTOFF, _comments)
    _REPOS[_label] = _repo
del _label, _repo, _comments

# --- small edge inputs (never measured) ------------------------------------
_CHECKS = []
_CHECKS.append(("empty-page", "otel-check-empty-comments", []))
_CHECKS.append(("single-comment", "otel-check-one-comment", [
    {
        "created_at": "2024-05-05T10:00:00Z",
        "user": {"login": "alice"},
        "html_url": f"https://github.com/{_ORG}/otel-checks/pull/42#issuecomment-1",
        "issue_url": f"https://api.github.com/repos/{_ORG}/otel-checks/issues/42",
    },
]))
_CHECKS.append(("stale-comment", "otel-check-stale-comment", [
    {
        "created_at": "2023-11-20T08:00:00Z",
        "user": {"login": "bob"},
        "html_url": f"https://github.com/{_ORG}/otel-checks/issues/7#issuecomment-2",
        "issue_url": f"https://api.github.com/repos/{_ORG}/otel-checks/issues/7",
    },
]))

for _lbl, _r, _c in _CHECKS:
    _publish(_r, _CUTOFF, _c)
del _lbl, _r, _c


def checks():
    return [(_lbl, _thunk(_r)) for _lbl, _r in _CHECKS]


def cases():
    return [(_lbl, _thunk(_r)) for _lbl, _r in _REPOS.items()]
```