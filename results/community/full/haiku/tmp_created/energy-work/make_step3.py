import json
from pathlib import Path

REPO = Path("/home/javad/energy-run/community")

def blocked(msg):
    return "inputs.py: no inputs could be generated: " + msg

NET = {
    "collect_jobs": "collect_jobs fetches every workflow run and job through gh_paginated, which shells out to `gh api --paginate` against the GitHub API — it needs network access and the gh CLI, and that request is the first thing the function does for each workflow.",
    "get_github_login": "`get_github_login` performs a live HTTP request to `https://api.github.com/users/{username}` via `requests.get` (plus a `time.sleep`), so it needs network access that is unavailable here and no input can avoid it.",
    "_check_reviews": "`_check_reviews` performs live GitHub API calls — it starts with a `request_with_retry(\"POST\", GRAPHQL_API, ...)` GraphQL request and then REST requests to `api.github.com`, requiring network access and credentials that are unavailable here; no input can avoid this, and mocking the HTTP layer is not allowed.",
    "_get_repo_commenters": "`_get_repo_commenters` fetches GitHub issue comments over HTTP via `request_with_retry`/`urllib.request.urlopen`; any real workload requires network access to `https://api.github.com`, and no input can avoid that (a cache hit would skip the function's work entirely).",
    "_get_repo_events": "`_get_repo_events` performs live HTTP requests to `https://api.github.com` via `request_with_retry`/`urllib.request.urlopen` before doing any other work, which requires network access and GitHub credentials/rate limits that are unavailable here; no input can avoid the request.",
    "_verify_review_candidates": "`_verify_review_candidates` calls `request_with_retry`, which performs live `urllib.request.urlopen` HTTP GETs to `https://api.github.com` for each candidate PR; its work begins with a network request and no input can avoid that.",
    "check_maintainer_activity": "`check_maintainer_activity` always starts by calling `_check_comments`/`_get_repo_commenters`, `_check_reviews` (GraphQL `request_with_retry` to `https://api.github.com/graphql`) and `_get_repo_events`, all of which make live GitHub API requests; there is no input that avoids network access, and mocking the HTTP layer is not allowed.",
    "create_emeritus_prs": "every non-empty `inactive_report` makes the function start with `fetch_readme(repo)`, an HTTP request to `https://api.github.com`, and it continues with `_get_fork_owner`, `_get_default_branch_sha`, `_ensure_fork`, `_update_file` and `_create_pr` — all network calls to GitHub that need credentials; no input can avoid this since the work is driven by the report contents.",
    "main": "`main` fetches teams, members, repos and activity from the GitHub REST/GraphQL API (`paginate_rest`, `request_with_retry`), so it needs network access and credentials that are unavailable here, and no input can avoid those requests.",
}

def sub(sid):
    return sid

records = [
    ("scripts/validate-workstreams.py::validate_workstreams_semantics", [
        ("a", "submitted", "C3S2-validate-hoist-sets", None),
        ("b", "submitted", "C1S1-validate-dead-parent-kind", None),
    ]),
    ("scripts/move-to-emeritus.py::_check_events", [
        ("a", "submitted", "C3S5-check-events-break", None),
    ]),
    ("scripts/move-to-emeritus.py::_get_repo_commenters", [
        ("a", "blocked", "C5S2-commenters-seen-set", blocked(NET["_get_repo_commenters"])),
    ]),
    ("scripts/move-to-emeritus.py::_add_to_emeritus", [
        ("a", "submitted", "C1S4-add-emeritus-single-match", None),
    ]),
    ("scripts/move-to-emeritus.py::_verify_review_candidates", [
        ("a", "blocked", "C8S4-verify-review-cache", blocked(NET["_verify_review_candidates"])),
    ]),
    ("scripts/move-to-emeritus.py::_get_repo_events", [
        ("a", "blocked", "C9S2-events-keep-consumed-types", blocked(NET["_get_repo_events"])),
    ]),
    ("scripts/move-to-emeritus.py::main", [
        ("a", "blocked", "C1S1-main-team-repos-map", blocked(NET["main"])),
    ]),
    ("scripts/gc-elections/generate-voters-roll.py::get_github_login", [
        ("a", "blocked", "C9S1-login-session", blocked(NET["get_github_login"])),
    ]),
    ("scripts/baremetal-runner-report.py::collect_jobs", [
        ("a", "rejected_in_step2_no_outcome", None, None),
        ("b", "blocked", "C3S2-collect-jobs-parse-run-start-once", blocked(NET["collect_jobs"])),
    ]),
    ("scripts/move-to-emeritus.py::_check_reviews", [
        ("a", "blocked", "C8S2-check-reviews-alias-once", blocked(NET["_check_reviews"])),
    ]),
    ("scripts/move-to-emeritus.py::check_maintainer_activity", [
        ("a", "blocked", "C8S2-check-maintainer-alias-once", blocked(NET["check_maintainer_activity"])),
    ]),
    ("scripts/move-to-emeritus.py::_parse_members", [
        ("a", "submitted", "C10S3-parse-members-comprehension", None),
    ]),
    ("scripts/move-to-emeritus.py::create_emeritus_prs", [
        ("a", "blocked", "C3S2-create-emeritus-lower-once", blocked(NET["create_emeritus_prs"])),
    ]),
]

out = []
for unit, outs in records:
    rows = []
    for label, outcome, subid, why in outs:
        if outcome == "rejected_in_step2_no_outcome":
            continue
        rows.append({"label": label, "outcome": outcome, "submission": subid, "why": why})
    out.append({"step": 3, "unit": unit, "outcomes": rows})

with (REPO / "step3.jsonl").open("w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(out), "records")
