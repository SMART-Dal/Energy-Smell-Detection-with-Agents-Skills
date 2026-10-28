# Energy report — community @ 910f85d

20 units listed, 15 with an accepted suspicion · 7 repairs submitted, 0 deferred · 2 confirmed · 2 partial · 2 mixed · 1 negligible · 1 applied
Noise floor 1.2% (from: session calibration).

## Applied

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C10S2-add-emeritus-startswith (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +26.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 78.87 | 57.83 | +26.7% | 1.3% | yes |
| existing-level2 | 79.35 | 57.87 | +27.1% | 0.8% | yes |
| existing-mixed-markers | 79.50 | 58.27 | +26.7% | 0.9% | yes |
| existing-case-insensitive | 79.26 | 57.66 | +27.2% | 0.3% | yes |

## Confirmed, not applied

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C1S4-add-emeritus-one-pass (C1.S4)

**confirmed** — not applied: changes the same function as C10S2-add-emeritus-startswith, which is applied; both were written against the original, so only one can be
Mean saving across its cases: +15.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 70.89 | 59.24 | +16.4% | 1.6% | yes |
| existing-level2 | 68.35 | 57.63 | +15.7% | 0.2% | yes |
| existing-mixed-markers | 69.58 | 58.46 | +16.0% | 0.3% | yes |
| existing-case-insensitive | 68.34 | 57.62 | +15.7% | 0.2% | yes |

## Measured, not confirmed

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C3S2-validate-hoist-sets (C3.S2)

**mixed** — a trade-off, not a fix: 58.0% saved on 'large-mixed' but 3.4% lost on 'deep-parent-chain', both clearing the 1.2% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: +26.9%.
The agent measured `partial`; re-measured `mixed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 111.92 | 53.15 | +52.5% | 2.1% | yes |
| deep-parent-chain | 63.92 | 66.12 | -3.4% | 2.3% | yes |
| parent-cycle | 54.53 | 54.27 | +0.5% | 0.8% | no: pairs disagree |
| large-mixed | 110.13 | 46.25 | +58.0% | 1.2% | yes |

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C1S1-validate-dead-parent-kind (C1.S1)

**partial** — saves energy on 1 of 4 inputs ('typical-tree'; best 2.5% +-1.3% on 'typical-tree'), and no saving that can be told from noise on the rest: 'deep-parent-chain' -0.4% +-1.2% (its pairs disagree too much to tell); 'parent-cycle' -1.2% +-1.6% (its pairs disagree too much to tell); 'large-mixed' -0.6% +-1.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +0.1%.
The agent measured `regressed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 57.24 | 55.83 | +2.5% | 1.3% | yes |
| deep-parent-chain | 64.30 | 64.53 | -0.4% | 1.2% | no: pairs disagree |
| parent-cycle | 57.45 | 58.15 | -1.2% | 1.6% | no: pairs disagree |
| large-mixed | 56.61 | 56.94 | -0.6% | 1.7% | no: pairs disagree |

### `scripts/update-sig-tables.py::render_group` — C10S4-render-group-join (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +3.0% +-3.0% on 'bare-meetings', against a clean 1.2% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +1.1%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| deep-resources | 58.08 | 57.34 | +1.3% | 3.6% | no: pairs disagree |
| people-heavy | 58.29 | 58.34 | -0.1% | 2.9% | no: pairs disagree |
| bare-meetings | 59.28 | 57.52 | +3.0% | 3.0% | no: pairs disagree |
| mixed-large | 57.90 | 57.68 | +0.4% | 1.6% | no: pairs disagree |

### `scripts/gc-elections/create-github-comments.py::sync` — C1S4-sync-mentions-once (C1.S4)

**partial** — saves energy on 2 of 4 inputs ('many-comments-few-stale', 'big-file'; best 16.5% +-6.2% on 'many-comments-few-stale'), and no saving that can be told from noise on the rest: 'all-stale' -0.0% +-0.5% (its pairs disagree too much to tell); 'large-comments' +0.7% +-1.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.7%.
The agent measured `negligible`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 67.51 | 56.33 | +16.6% | 6.2% | yes |
| all-stale | 68.83 | 68.83 | -0.0% | 0.5% | no: pairs disagree |
| large-comments | 55.25 | 54.86 | +0.7% | 1.0% | no: pairs disagree |
| big-file | 62.41 | 61.55 | +1.4% | 1.1% | yes |

### `scripts/move-to-emeritus.py::_check_events` — C3S5-check-events-early-exit (C3.S5)

**mixed** — a trade-off, not a fix: 17.8% saved on 'big-mixed' but 17.0% lost on 'huge-remaining', both clearing the 1.2% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -1.6%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-mixed | 68.27 | 56.09 | +17.8% | 0.4% | yes |
| single-type | 56.33 | 59.76 | -6.1% | 0.9% | yes |
| huge-remaining | 59.39 | 69.47 | -17.0% | 3.5% | yes |
| exclude-all | 56.56 | 57.28 | -1.3% | 0.6% | yes |

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `scripts/gc-elections/generate-voters-roll.py::get_github_login` a: blocked — inputs.py: it cannot run here: get_github_login performs a live HTTP request to https://api.github.com/users/{username} via requests.get, which requires network access that is unavailable here.
- `scripts/baremetal-runner-report.py::collect_jobs` a: blocked — inputs.py: it cannot run here: collect_jobs performs all of its work through gh_paginated, which shells out to the gh api command to fetch workflow runs and jobs from GitHub; it needs network access and a working gh binary, and no input can avoid that.
- `scripts/baremetal-runner-report.py::collect_jobs` b: blocked — inputs.py: it cannot run here: collect_jobs performs all of its work through gh_paginated, which shells out to the gh api command to fetch workflow runs and jobs from GitHub; it needs network access and a working gh binary, and no input can avoid that.
- `scripts/move-to-emeritus.py::_get_repo_commenters` a: blocked — inputs.py: it cannot run here: _get_repo_commenters always begins with request_with_retry("GET", ...) calling urllib.request.urlopen against https://api.github.com, and reads the response via read_json; no input can avoid the network request, and faking the endpoint or serving fake responses is not allowed.
- `scripts/move-to-emeritus.py::_verify_review_candidates` a: blocked — inputs.py: it cannot run here: _verify_review_candidates performs live HTTP requests to https://api.github.com via request_with_retry and urllib.request.urlopen for every candidate PR; there is no way to supply the review data without network access, and intercepting the request would require mocking the repository's own code.
- `scripts/move-to-emeritus.py::_check_reviews` a: blocked — inputs.py: it cannot run here: _check_reviews performs live HTTP requests to the GitHub GraphQL and REST APIs; it needs network access and GitHub credentials, and no input could avoid that.
- `scripts/move-to-emeritus.py::check_triager_activity` a: blocked — inputs.py: it cannot run here: check_triager_activity reaches the network through _check_comments and _check_events, which call _get_repo_commenters and _get_repo_events; these fetch GitHub API data, and the task exposes no cache variable or other data hook that could supply that data without a request.
- `scripts/move-to-emeritus.py::check_approver_activity` a: blocked — inputs.py: it cannot run here: check_approver_activity performs live GitHub API requests (via _get_repo_commenters and the GraphQL search in _check_reviews) to api.github.com; no non-trivial input can avoid network access, and mocking the requests is not allowed.
- `scripts/move-to-emeritus.py::check_maintainer_activity` a: blocked — inputs.py: it cannot run here: check_maintainer_activity performs its work by calling the GitHub API over the network (_check_comments and _get_repo_commenters over REST, _check_reviews as a GraphQL POST, and _check_events and _get_repo_events over REST), so any non-empty input requires live network access and credentials, which cannot be provided or faked here.
- `scripts/move-to-emeritus.py::check_maintainer_activity` b: blocked — inputs.py: it cannot run here: check_maintainer_activity performs its work by calling the GitHub API over the network (_check_comments and _get_repo_commenters over REST, _check_reviews as a GraphQL POST, and _check_events and _get_repo_events over REST), so any non-empty input requires live network access and credentials, which cannot be provided or faked here.
- `scripts/move-to-emeritus.py::check_maintainer_activity` c: blocked — inputs.py: it cannot run here: check_maintainer_activity performs its work by calling the GitHub API over the network (_check_comments and _get_repo_commenters over REST, _check_reviews as a GraphQL POST, and _check_events and _get_repo_events over REST), so any non-empty input requires live network access and credentials, which cannot be provided or faked here.
- `scripts/move-to-emeritus.py::create_emeritus_prs` a: blocked — inputs.py: it cannot run here: the function fetches each repo's README over the network via fetch_readme, request_with_retry and urllib.request.urlopen (GitHub REST API), and also creates forks, branches, commits and PRs through the same API; there is no input that avoids these HTTP requests, and no network access is available.
- `scripts/move-to-emeritus.py::main` a: blocked — inputs.py: it cannot run here: main fetches teams, members, repos and activity from the GitHub REST and GraphQL API via urllib.request; there is no network access here and the calls cannot be avoided or mocked.
