# Energy report — community @ 910f85d

18 units listed, 13 with an accepted suspicion · 14 repairs submitted, 0 deferred · 3 confirmed · 1 mixed · 1 negligible · 9 no_inputs · 3 applied
Noise floor 1.1% (from: session calibration).

## Applied

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C3S2-validate-hoist-sets (C3.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +29.4%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 101.74 | 47.11 | +53.7% | 1.2% | yes |
| deep-parent-chain | 64.35 | 63.49 | +1.3% | 0.9% | yes |
| parent-cycle | 54.19 | 52.13 | +3.8% | 1.6% | yes |
| large-mixed | 105.74 | 43.51 | +58.9% | 4.7% | yes |

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C1S4-add-emeritus-single-match (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +18.3%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 64.01 | 52.59 | +17.8% | 4.8% | yes |
| existing-level2 | 61.57 | 51.07 | +17.1% | 4.2% | yes |
| existing-mixed-markers | 63.98 | 52.69 | +17.7% | 15.9% | yes |
| existing-case-insensitive | 65.38 | 51.84 | +20.7% | 12.7% | yes |

### `scripts/move-to-emeritus.py::_parse_members` — C10S3-parse-members-comprehension (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +4.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
The agent measured `partial`; re-measured `confirmed`.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-mixed-25k | 62.48 | 59.19 | +5.3% | 4.1% | yes |
| no-trailing-15k | 62.30 | 58.07 | +6.8% | 2.3% | yes |
| unicode-8k | 59.31 | 56.97 | +3.9% | 1.5% | yes |
| near-miss-12k | 59.68 | 57.63 | +3.4% | 1.0% | yes |

## Measured, not confirmed

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C1S1-validate-dead-parent-kind (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +1.9% +-2.7% on 'large-mixed', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.
The agent measured `regressed`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 53.70 | 53.61 | +0.2% | 2.4% | no: pairs disagree |
| deep-parent-chain | 65.93 | 66.08 | -0.2% | 1.5% | no: pairs disagree |
| parent-cycle | 55.93 | 56.46 | -1.0% | 1.4% | no: pairs disagree |
| large-mixed | 54.38 | 53.34 | +1.9% | 2.7% | no: pairs disagree |

### `scripts/move-to-emeritus.py::_check_events` — C3S5-check-events-break (C3.S5)

**mixed** — a trade-off, not a fix: 18.8% saved on 'big-mixed' but 14.5% lost on 'huge-remaining', both clearing the 1.1% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -0.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-mixed | 68.34 | 55.50 | +18.8% | 1.5% | yes |
| single-type | 55.94 | 59.03 | -5.5% | 2.9% | yes |
| huge-remaining | 59.05 | 67.58 | -14.5% | 1.8% | yes |
| exclude-all | 57.69 | 58.17 | -0.8% | 1.4% | no: pairs disagree |

## Not measured

### `scripts/move-to-emeritus.py::_get_repo_commenters` — C5S2-commenters-seen-set (C5.S2)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_get_repo_commenters: it cannot run here: `_get_repo_commenters` fetches GitHub issue comments over HTTP via `request_with_retry`/`urllib.request.urlopen`; any real workload requires network access to `https://api.github.com`, and no input can avoid that (a cache hit would skip the function's work entirely). Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::_verify_review_candidates` — C8S4-verify-review-cache (C8.S4)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_verify_review_candidates: it cannot run here: `_verify_review_candidates` calls `request_with_retry`, which performs live `urllib.request.urlopen` HTTP GETs to `https://api.github.com` for each candidate PR; its work begins with a network request and no input can avoid that. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::_get_repo_events` — C9S2-events-keep-consumed-types (C9.S2)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_get_repo_events: it cannot run here: `_get_repo_events` performs live HTTP requests to `https://api.github.com` via `request_with_retry`/`urllib.request.urlopen` before doing any other work, which requires network access and GitHub credentials/rate limits that are unavailable here; no input can avoid the request. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::main` — C1S1-main-team-repos-map (C1.S1)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::main: it cannot run here: `main` fetches teams, members, repos and activity from the GitHub REST/GraphQL API (`paginate_rest`, `request_with_retry`), so it needs network access and credentials that are unavailable here, and no input can avoid those requests. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/gc-elections/generate-voters-roll.py::get_github_login` — C9S1-login-session (C9.S1)

**no_inputs** — no inputs could be generated for scripts/gc-elections/generate-voters-roll.py::get_github_login: it cannot run here: `get_github_login` performs a live HTTP request to `https://api.github.com/users/{username}` via `requests.get` (plus a `time.sleep`), so it needs network access that is unavailable here and no input can avoid it. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/baremetal-runner-report.py::collect_jobs` — C3S2-collect-jobs-parse-run-start-once (C3.S2)

**no_inputs** — no inputs could be generated for scripts/baremetal-runner-report.py::collect_jobs: it cannot run here: collect_jobs fetches every workflow run and job through gh_paginated, which shells out to `gh api --paginate` against the GitHub API — it needs network access and the gh CLI, and that request is the first thing the function does for each workflow. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::_check_reviews` — C8S2-check-reviews-alias-once (C8.S2)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_check_reviews: it cannot run here: `_check_reviews` performs live GitHub API calls — it starts with a `request_with_retry("POST", GRAPHQL_API, ...)` GraphQL request and then REST requests to `api.github.com`, requiring network access and credentials that are unavailable here; no input can avoid this, and mocking the HTTP layer is not allowed. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::check_maintainer_activity` — C8S2-check-maintainer-alias-once (C8.S2)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::check_maintainer_activity: it cannot run here: `check_maintainer_activity` always starts by calling `_check_comments`/`_get_repo_commenters`, `_check_reviews` (GraphQL `request_with_retry` to `https://api.github.com/graphql`) and `_get_repo_events`, all of which make live GitHub API requests; there is no input that avoids network access, and mocking the HTTP layer is not allowed. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::create_emeritus_prs` — C3S2-create-emeritus-lower-once (C3.S2)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::create_emeritus_prs: it cannot run here: every non-empty `inactive_report` makes the function start with `fetch_readme(repo)`, an HTTP request to `https://api.github.com`, and it continues with `_get_fork_owner`, `_get_default_branch_sha`, `_ensure_fork`, `_update_file` and `_create_pr` — all network calls to GitHub that need credentials; no input can avoid this since the work is driven by the report contents. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `scripts/move-to-emeritus.py::_get_repo_commenters` a: blocked — inputs.py: no inputs could be generated: `_get_repo_commenters` fetches GitHub issue comments over HTTP via `request_with_retry`/`urllib.request.urlopen`; any real workload requires network access to `https://api.github.com`, and no input can avoid that (a cache hit would skip the function's work entirely).
- `scripts/move-to-emeritus.py::_verify_review_candidates` a: blocked — inputs.py: no inputs could be generated: `_verify_review_candidates` calls `request_with_retry`, which performs live `urllib.request.urlopen` HTTP GETs to `https://api.github.com` for each candidate PR; its work begins with a network request and no input can avoid that.
- `scripts/move-to-emeritus.py::_get_repo_events` a: blocked — inputs.py: no inputs could be generated: `_get_repo_events` performs live HTTP requests to `https://api.github.com` via `request_with_retry`/`urllib.request.urlopen` before doing any other work, which requires network access and GitHub credentials/rate limits that are unavailable here; no input can avoid the request.
- `scripts/move-to-emeritus.py::main` a: blocked — inputs.py: no inputs could be generated: `main` fetches teams, members, repos and activity from the GitHub REST/GraphQL API (`paginate_rest`, `request_with_retry`), so it needs network access and credentials that are unavailable here, and no input can avoid those requests.
- `scripts/gc-elections/generate-voters-roll.py::get_github_login` a: blocked — inputs.py: no inputs could be generated: `get_github_login` performs a live HTTP request to `https://api.github.com/users/{username}` via `requests.get` (plus a `time.sleep`), so it needs network access that is unavailable here and no input can avoid it.
- `scripts/baremetal-runner-report.py::collect_jobs` b: blocked — inputs.py: no inputs could be generated: collect_jobs fetches every workflow run and job through gh_paginated, which shells out to `gh api --paginate` against the GitHub API — it needs network access and the gh CLI, and that request is the first thing the function does for each workflow.
- `scripts/move-to-emeritus.py::_check_reviews` a: blocked — inputs.py: no inputs could be generated: `_check_reviews` performs live GitHub API calls — it starts with a `request_with_retry("POST", GRAPHQL_API, ...)` GraphQL request and then REST requests to `api.github.com`, requiring network access and credentials that are unavailable here; no input can avoid this, and mocking the HTTP layer is not allowed.
- `scripts/move-to-emeritus.py::check_maintainer_activity` a: blocked — inputs.py: no inputs could be generated: `check_maintainer_activity` always starts by calling `_check_comments`/`_get_repo_commenters`, `_check_reviews` (GraphQL `request_with_retry` to `https://api.github.com/graphql`) and `_get_repo_events`, all of which make live GitHub API requests; there is no input that avoids network access, and mocking the HTTP layer is not allowed.
- `scripts/move-to-emeritus.py::create_emeritus_prs` a: blocked — inputs.py: no inputs could be generated: every non-empty `inactive_report` makes the function start with `fetch_readme(repo)`, an HTTP request to `https://api.github.com`, and it continues with `_get_fork_owner`, `_get_default_branch_sha`, `_ensure_fork`, `_update_file` and `_create_pr` — all network calls to GitHub that need credentials; no input can avoid this since the work is driven by the report contents.
