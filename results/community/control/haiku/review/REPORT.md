# Energy report — community @ 910f85d

27 units listed, 11 with an accepted suspicion · 12 repairs submitted, 0 deferred · 2 confirmed · 2 partial · 2 regressed · 6 no_inputs · 2 applied
Noise floor 1.3% (from: session calibration).

## Applied

### `scripts/gc-elections/create-github-comments.py::sync` — sync-single-pass-removal

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +74.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 64.46 | 55.16 | +14.4% | 10.4% | yes |
| all-stale | 103.15 | 4.76 | +95.4% | 6.8% | yes |
| large-comments | 91.98 | 3.74 | +95.9% | 5.2% | yes |
| big-file | 106.54 | 10.50 | +90.1% | 5.5% | yes |

### `scripts/move-to-emeritus.py::_add_to_emeritus` — add-emeritus-single-scan

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +14.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 64.64 | 55.55 | +14.1% | 0.5% | yes |
| existing-level2 | 66.92 | 56.37 | +15.8% | 6.2% | yes |
| existing-mixed-markers | 65.01 | 55.21 | +15.1% | 5.4% | yes |
| existing-case-insensitive | 64.73 | 55.78 | +13.8% | 0.5% | yes |

## Measured, not confirmed

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — validate-drop-parent-kind

**regressed** — the repair costs more than the code it replaces: 5.5% lost on 'deep-parent-chain', above the 1.3% noise floor, and no case improved. Worse on 2 of 4 cases ('deep-parent-chain', 'parent-cycle').
Mean saving across its cases: -2.3%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `regressed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 56.43 | 56.71 | -0.5% | 2.7% | no: pairs disagree |
| deep-parent-chain | 65.82 | 69.43 | -5.5% | 1.1% | yes |
| parent-cycle | 59.64 | 61.97 | -3.9% | 3.7% | yes |
| large-mixed | 58.24 | 57.80 | +0.8% | 0.3% | no: within the floor |

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — validate-hoist-team-sets

**partial** — saves energy on 3 of 4 inputs ('typical-tree', 'parent-cycle', 'large-mixed'; best 57.7% +-1.0% on 'large-mixed'), and no saving that can be told from noise on the rest: 'deep-parent-chain' +0.9% +-0.6% (within the 1.3% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +28.5%.
The agent measured `confirmed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 104.09 | 49.46 | +52.5% | 0.3% | yes |
| deep-parent-chain | 67.28 | 66.69 | +0.9% | 0.6% | no: within the floor |
| parent-cycle | 56.63 | 54.92 | +3.0% | 1.7% | yes |
| large-mixed | 102.89 | 43.57 | +57.7% | 1.0% | yes |

### `scripts/gc-elections/create-github-comments.py::sync` — sync-reuse-mentions

**partial** — saves energy on 1 of 4 inputs ('many-comments-few-stale'; best 13.9% +-3.5% on 'many-comments-few-stale'), and no saving that can be told from noise on the rest: 'all-stale' +0.7% +-0.5% (within the 1.3% noise floor); 'large-comments' +0.7% +-0.9% (its pairs disagree too much to tell); 'big-file' +0.8% +-3.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.0%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 67.96 | 58.53 | +13.9% | 3.5% | yes |
| all-stale | 74.06 | 73.55 | +0.7% | 0.5% | no: within the floor |
| large-comments | 58.98 | 58.54 | +0.7% | 0.9% | no: pairs disagree |
| big-file | 66.16 | 65.66 | +0.8% | 3.0% | no: pairs disagree |

### `scripts/move-to-emeritus.py::_check_events` — events-stop-when-all-found

**regressed** — the repair costs more than the code it replaces: 47.4% lost on 'huge-remaining', above the 1.3% noise floor, and no case improved. Worse on 4 of 4 cases ('big-mixed', 'single-type', 'huge-remaining', 'exclude-all').
Mean saving across its cases: -75.0%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-mixed | 56.77 | 92.96 | -63.7% | 32.4% | yes |
| single-type | 48.95 | 95.56 | -95.2% | 2.4% | yes |
| huge-remaining | 59.09 | 87.11 | -47.4% | 5.6% | yes |
| exclude-all | 47.16 | 91.22 | -93.4% | 13.0% | yes |

## Not measured

### `scripts/gc-elections/generate-voters-roll.py::get_github_login` — gh-login-session

**no_inputs** — no inputs could be generated for scripts/gc-elections/generate-voters-roll.py::get_github_login: it cannot run here: `get_github_login` performs a live HTTP request to `https://api.github.com/users/{username}` via `requests.get`, which requires network access that is unavailable here. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::_get_repo_commenters` — commenters-set-membership

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_get_repo_commenters: it cannot run here: `_get_repo_commenters` performs live HTTP GET requests to the GitHub REST API (`request_with_retry("GET", url)` → `urllib.request.urlopen`) on every non-cached path, so it requires network access to api.github.com; the only network-free path is the trivial `_repo_comments_cache` hit that does no work, and the environment provides no network. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::_verify_review_candidates` — verify-reviews-cache

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_verify_review_candidates: it cannot run here: `_verify_review_candidates` performs live GitHub REST requests via `request_with_retry`/`urllib.request.urlopen` to the hardcoded `https://api.github.com` endpoint; it needs network access (and credentials/rate limits) and cannot be exercised here without mocking the request layer, which is forbidden. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::check_triager_activity` — triager-guard-debug

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::check_triager_activity: it cannot run here: `check_triager_activity` delegates to `_check_comments`/`_check_events`, which call `_get_repo_commenters(repo, cutoff)` / `_get_repo_events(repo, cutoff)` — these fetch GitHub repository data over the network (via `paginate_rest`/`request_with_retry`), and neither their cache format nor any offline data source is given, so no input can make the function run without network access. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::check_approver_activity` — approver-guard-debug

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::check_approver_activity: it cannot run here: `check_approver_activity` reaches the GitHub API on every call — it invokes `_check_comments` (which calls `_get_repo_commenters` and its REST requests) and `_check_reviews` (which posts a GraphQL query via `request_with_retry`), so no input can avoid network access and credentials. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

### `scripts/move-to-emeritus.py::check_maintainer_activity` — maintainer-guard-debug

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::check_maintainer_activity: it cannot run here: `check_maintainer_activity` needs network access to the GitHub API — its first step for any non-empty input is `_check_comments` → `_get_repo_commenters` (REST pagination) and later `_check_reviews`/authored-PR queries hit `GRAPHQL_API`/`api.github.com` with credentials; the only input that avoids the network is empty `usernames`/`repos`, which does no work. Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `scripts/move-to-emeritus.py::create_emeritus_prs` a: blocked — inputs.py: it cannot run here: `create_emeritus_prs` calls `fetch_readme`, which performs an HTTP request to the GitHub API (`https://api.github.com/repos/.../readme`) via `request_with_retry`/`urllib.request`; the function cannot run without network access and credentials, and no input can avoid that.
