# Energy report — community @ 910f85d

24 units listed, 21 with an accepted suspicion · 17 repairs submitted, 1 deferred · 5 confirmed · 7 partial · 3 mixed · 2 negligible · 4 applied
Noise floor 0.9% (from: session calibration).

## Applied

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C8S2-emeritus-compiled-patterns (C8.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +35.4%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 88.35 | 57.92 | +34.4% | 8.1% | yes |
| existing-level2 | 92.44 | 59.48 | +35.7% | 3.9% | yes |
| existing-mixed-markers | 92.25 | 59.68 | +35.3% | 2.4% | yes |
| existing-case-insensitive | 93.61 | 59.60 | +36.3% | 2.8% | yes |

### `scripts/move-to-emeritus.py::_build_pr_body` — C10S4-pr-body-join (C10.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +5.0%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
The agent measured `partial`; re-measured `confirmed`.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 56.52 | 54.49 | +3.6% | 2.0% | yes |
| with-warning | 57.60 | 53.77 | +6.7% | 0.8% | yes |
| same-role | 56.54 | 54.57 | +3.5% | 1.5% | yes |
| duplicates | 57.34 | 53.82 | +6.1% | 0.8% | yes |

### `scripts/baremetal-runner-report.py::render_table` — C6S1-render-table-runs-set (C6.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +12.2%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-groups | 69.43 | 59.71 | +14.0% | 7.3% | yes |
| half-filtered | 68.57 | 60.58 | +11.7% | 7.3% | yes |
| mixed | 66.96 | 58.91 | +12.0% | 6.7% | yes |
| many-distinct-runs | 69.45 | 61.61 | +11.3% | 6.4% | yes |

### `scripts/gc-elections/create-github-comments.py::sync` — C3S3-sync-single-pass-removal (C3.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +73.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 66.35 | 57.41 | +13.5% | 9.3% | yes |
| all-stale | 105.21 | 4.87 | +95.4% | 6.5% | yes |
| large-comments | 108.20 | 4.67 | +95.7% | 3.9% | yes |
| big-file | 109.87 | 10.81 | +90.2% | 6.3% | yes |

## Confirmed, not applied

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C1S4-emeritus-member-flag (C1.S4)

**confirmed** — not applied: changes the same function as C8S2-emeritus-compiled-patterns, which is applied; both were written against the original, so only one can be
Mean saving across its cases: +13.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
The agent measured `partial`; re-measured `confirmed`.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 67.29 | 58.53 | +13.0% | 4.4% | yes |
| existing-level2 | 66.56 | 57.46 | +13.7% | 2.0% | yes |
| existing-mixed-markers | 67.28 | 58.15 | +13.6% | 1.0% | yes |
| existing-case-insensitive | 66.53 | 57.48 | +13.6% | 2.0% | yes |

## Measured, not confirmed

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C3S2-validate-team-sets (C3.S2)

**partial** — saves energy on 3 of 4 inputs ('typical-tree', 'deep-parent-chain', 'large-mixed'; best 56.0% +-3.3% on 'large-mixed'), and no saving that can be told from noise on the rest: 'parent-cycle' +2.4% +-5.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +28.3%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 110.94 | 51.99 | +53.1% | 1.2% | yes |
| deep-parent-chain | 67.56 | 66.49 | +1.6% | 0.7% | yes |
| parent-cycle | 56.45 | 55.09 | +2.4% | 5.7% | no: pairs disagree |
| large-mixed | 104.35 | 45.91 | +56.0% | 3.3% | yes |

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C1S1-validate-dead-kind (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +2.3% +-7.5% on 'large-mixed', against a clean 0.9% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +1.3%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `mixed`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 55.64 | 55.38 | +0.5% | 1.0% | no: pairs disagree |
| deep-parent-chain | 68.58 | 67.53 | +1.5% | 3.3% | no: pairs disagree |
| parent-cycle | 61.23 | 60.65 | +1.0% | 2.7% | no: pairs disagree |
| large-mixed | 57.41 | 56.07 | +2.3% | 7.5% | no: pairs disagree |

### `scripts/move-to-emeritus.py::_check_events` — C3S5-events-early-exit (C3.S5)

**mixed** — a trade-off, not a fix: 20.7% saved on 'big-mixed' but 16.9% lost on 'huge-remaining', both clearing the 0.9% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -0.3%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Measured twice: the first measurement came out `mixed` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-mixed | 66.52 | 52.77 | +20.7% | 0.5% | yes |
| single-type | 52.12 | 55.52 | -6.5% | 0.5% | yes |
| huge-remaining | 55.72 | 65.13 | -16.9% | 3.3% | yes |
| exclude-all | 53.05 | 52.20 | +1.6% | 1.0% | yes |

### `scripts/move-to-emeritus.py::_remove_member_line` — C6S2-remove-member-line-no-slice (C6.S2)

**partial** — saves energy on 3 of 4 inputs ('large-hit-last', 'level3-section', 'section-at-eof'; best 3.4% +-1.6% on 'section-at-eof'), and no saving that can be told from noise on the rest: 'large-miss' +0.7% +-0.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Mean saving across its cases: +1.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
The agent measured `negligible`; re-measured `partial`.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-hit-last | 62.49 | 60.91 | +2.5% | 1.2% | yes |
| large-miss | 60.95 | 60.52 | +0.7% | 0.8% | no: pairs disagree |
| level3-section | 59.67 | 58.98 | +1.2% | 1.1% | yes |
| section-at-eof | 59.86 | 57.81 | +3.4% | 1.6% | yes |

### `scripts/move-to-emeritus.py::_parse_members` — C3S1-parse-members-comprehension (C3.S1)

**partial** — saves energy on 3 of 4 inputs ('no-trailing-15k', 'unicode-8k', 'near-miss-12k'; best 7.8% +-0.6% on 'near-miss-12k'), and no saving that can be told from noise on the rest: 'large-mixed-25k' +2.1% +-2.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Mean saving across its cases: +4.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-mixed-25k | 59.21 | 57.98 | +2.1% | 2.4% | no: pairs disagree |
| no-trailing-15k | 57.51 | 54.98 | +4.4% | 2.0% | yes |
| unicode-8k | 57.43 | 55.31 | +3.7% | 1.8% | yes |
| near-miss-12k | 59.34 | 54.70 | +7.8% | 0.6% | yes |

### `scripts/move-to-emeritus.py::_parse_members` — C8S2-parse-members-module-pattern (C8.S2)

**negligible** — no case moved more than the noise: the largest reading was +1.1% +-8.0% on 'large-mixed-25k', against a clean 0.9% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-mixed-25k | 61.22 | 60.51 | +1.2% | 8.0% | no: pairs disagree |
| no-trailing-15k | 57.43 | 57.37 | +0.1% | 0.3% | no: pairs disagree |
| unicode-8k | 57.97 | 57.70 | +0.5% | 2.2% | no: pairs disagree |
| near-miss-12k | 56.92 | 56.79 | +0.2% | 0.6% | no: pairs disagree |

### `scripts/move-to-emeritus.py::_build_issue_body` — C10S4-issue-body-join (C10.S4)

**partial** — saves energy on 3 of 4 inputs ('many-members', 'reverse-sorted', 'duplicates'; best 8.9% +-1.7% on 'reverse-sorted'), and no saving that can be told from noise on the rest: 'unicode' +0.7% +-1.3% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Mean saving across its cases: +5.3%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-members | 56.67 | 54.56 | +3.7% | 1.1% | yes |
| reverse-sorted | 60.81 | 55.39 | +8.9% | 1.7% | yes |
| duplicates | 60.80 | 56.10 | +7.7% | 5.7% | yes |
| unicode | 57.56 | 57.15 | +0.7% | 1.3% | no: pairs disagree |

### `scripts/gc-elections/create-github-comments.py::sync` — C1S4-sync-mentions-once (C1.S4)

**partial** — saves energy on 3 of 4 inputs ('many-comments-few-stale', 'large-comments', 'big-file'; best 15.2% +-10.6% on 'many-comments-few-stale'), and no saving that can be told from noise on the rest: 'all-stale' +0.7% +-0.7% (within the 0.9% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 65.51 | 55.48 | +15.3% | 10.6% | yes |
| all-stale | 68.46 | 67.98 | +0.7% | 0.7% | no: within the floor |
| large-comments | 54.89 | 54.33 | +1.0% | 0.9% | yes |
| big-file | 61.64 | 60.69 | +1.5% | 0.4% | yes |

### `scripts/update-sig-tables.py::render_group` — C10S4-render-group-join (C10.S4)

**partial** — saves energy on 1 of 4 inputs ('bare-meetings'; best 3.5% +-1.5% on 'bare-meetings'), and no saving that can be told from noise on the rest: 'deep-resources' +0.5% +-0.6% (its pairs disagree too much to tell); 'people-heavy' +0.0% +-1.8% (its pairs disagree too much to tell); 'mixed-large' +0.9% +-2.6% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +1.2%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `negligible`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| deep-resources | 57.89 | 57.61 | +0.5% | 0.6% | no: pairs disagree |
| people-heavy | 58.07 | 58.06 | +0.0% | 1.8% | no: pairs disagree |
| bare-meetings | 60.47 | 58.33 | +3.5% | 1.5% | yes |
| mixed-large | 58.17 | 57.67 | +0.9% | 2.6% | no: pairs disagree |

### `scripts/update-sig-tables.py::render_sig_details_group` — C10S4-render-details-group-join (C10.S4)

**partial** — saves energy on 2 of 4 inputs ('medium', 'half-empty'; best 4.5% +-4.2% on 'half-empty'), and no saving that can be told from noise on the rest: 'large' +6.1% +-6.6% (its pairs disagree too much to tell); 'huge-mixed' +5.5% +-8.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +5.0%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| medium | 58.52 | 56.20 | +4.0% | 3.0% | yes |
| large | 58.97 | 55.36 | +6.1% | 6.6% | no: pairs disagree |
| half-empty | 58.09 | 55.45 | +4.5% | 4.2% | yes |
| huge-mixed | 59.22 | 55.98 | +5.5% | 8.4% | no: pairs disagree |

### `scripts/update-community-members.py::render_gc` — C1S4-render-gc-display-name (C1.S4)

**mixed** — a trade-off, not a fix: 4.3% saved on 'duplicates-80k' but 9.5% lost on 'full-40k', both clearing the 0.9% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -3.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-40k | 57.70 | 63.19 | -9.5% | 0.9% | yes |
| sparse-35k | 57.03 | 57.75 | -1.2% | 0.4% | yes |
| duplicates-80k | 57.71 | 55.20 | +4.3% | 0.1% | yes |
| mixed-40k | 56.01 | 59.11 | -5.5% | 1.6% | yes |

### `scripts/update-community-members.py::render_tc` — C1S4-render-tc-display-name (C1.S4)

**mixed** — a trade-off, not a fix: 3.0% saved on 'duplicates' but 6.3% lost on 'large', both clearing the 0.9% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -0.4%.
The agent measured `regressed`; re-measured `mixed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 56.73 | 60.31 | -6.3% | 5.2% | yes |
| duplicates | 56.46 | 54.75 | +3.0% | 0.6% | yes |
| long-prefixes | 55.88 | 54.93 | +1.7% | 1.5% | yes |
| unicode-names | 55.19 | 55.15 | +0.1% | 1.7% | no: pairs disagree |

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `scripts/move-to-emeritus.py::check_maintainer_activity` a: blocked — inputs.py: it cannot run here: `check_maintainer_activity` performs live GitHub API requests (GraphQL `request_with_retry` to `GRAPHQL_API` and REST helpers like `_get_repo_commenters`/`_get_repo_events`), which require network access and credentials that are unavailable here.
- `scripts/move-to-emeritus.py::check_maintainer_activity` b: blocked — inputs.py: it cannot run here: `check_maintainer_activity` performs live GitHub API requests (GraphQL `request_with_retry` to `GRAPHQL_API` and REST helpers like `_get_repo_commenters`/`_get_repo_events`), which require network access and credentials that are unavailable here.
- `scripts/move-to-emeritus.py::check_maintainer_activity` c: blocked — inputs.py: it cannot run here: `check_maintainer_activity` performs live GitHub API requests (GraphQL `request_with_retry` to `GRAPHQL_API` and REST helpers like `_get_repo_commenters`/`_get_repo_events`), which require network access and credentials that are unavailable here.
- `scripts/move-to-emeritus.py::_check_reviews` a: blocked — inputs.py: it cannot run here: `_check_reviews` performs GitHub GraphQL/REST requests via `request_with_retry` to `https://api.github.com/graphql` and `REST_API` for every user batch; its work begins with a network request to a remote service, so no input can avoid network access.
- `scripts/move-to-emeritus.py::_check_reviews` b: blocked — inputs.py: it cannot run here: `_check_reviews` performs GitHub GraphQL/REST requests via `request_with_retry` to `https://api.github.com/graphql` and `REST_API` for every user batch; its work begins with a network request to a remote service, so no input can avoid network access.
- `scripts/move-to-emeritus.py::_get_repo_commenters` a: blocked — inputs.py: it cannot run here: `_get_repo_commenters` performs live HTTP requests to `https://api.github.com` via `request_with_retry`/`urllib.request.urlopen` (and follows pagination links), needing network access and GitHub credentials.
- `scripts/move-to-emeritus.py::main` a: blocked — inputs.py: it cannot run here: `main` fetches teams, members, repos and activity from the GitHub REST/GraphQL API via `request_with_retry`/`paginate_rest`; its work begins with network requests that cannot be avoided or satisfied offline.
- `scripts/move-to-emeritus.py::main` b: blocked — inputs.py: it cannot run here: `main` fetches teams, members, repos and activity from the GitHub REST/GraphQL API via `request_with_retry`/`paginate_rest`; its work begins with network requests that cannot be avoided or satisfied offline.
- `scripts/move-to-emeritus.py::paginate_rest` a: blocked — inputs.py: it cannot run here: `paginate_rest` performs real HTTP requests (it calls `request_with_retry` -> `urllib.request.urlopen` against the GitHub REST API), so no input can avoid the network.
- `scripts/update-sig-tables.py::render_group` b: deferred — accepted but not tried: the memo lives in extract_row_data and pays only across render_group plus render_sig_details, which no single unit's inputs exercise; spare repair places were not enough to justify a cross-unit measurement
- `scripts/gc-elections/generate-voters-roll.py::build_devstats_rows` a: blocked — inputs.py: it cannot run here: `build_devstats_rows` calls `get_github_login` for every name, which performs `requests.get('https://api.github.com/users/...')` (plus `time.sleep(0.1)`), so it requires network access to GitHub.
- `scripts/gc-elections/generate-voters-roll.py::build_devstats_rows` c: blocked — inputs.py: it cannot run here: `build_devstats_rows` calls `get_github_login` for every name, which performs `requests.get('https://api.github.com/users/...')` (plus `time.sleep(0.1)`), so it requires network access to GitHub.
- `scripts/gc-elections/generate-voters-roll.py::get_github_login` a: blocked — inputs.py: it cannot run here: get_github_login performs a live HTTP request to https://api.github.com/users/<username> via requests.get; it needs network access and no input can avoid it.
- `scripts/baremetal-runner-report.py::collect_jobs` a: blocked — inputs.py: it cannot run here: `collect_jobs` fetches data by shelling out to the `gh` CLI (`subprocess.run(["gh", "api", ...])`) against the GitHub API, so it needs network access and an external program that cannot be provided here.
