# Energy report — community @ 910f85d

21 units listed, 16 with an accepted suspicion · 15 repairs submitted, 1 deferred · 5 confirmed · 5 partial · 1 mixed · 1 regressed · 2 negligible · 1 no_inputs · 4 applied
Noise floor 1.9% (from: session calibration).

## Applied

### `scripts/move-to-emeritus.py::_build_issue_body` — C10S4-issue-body (C10.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +9.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-members | 66.25 | 60.70 | +8.4% | 2.0% | yes |
| reverse-sorted | 75.22 | 61.18 | +18.7% | 12.5% | yes |
| duplicates | 64.86 | 60.83 | +6.2% | 0.7% | yes |
| unicode | 64.63 | 61.05 | +5.5% | 0.3% | yes |

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C8S3-add-emeritus-compiled (C8.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +40.8%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 95.78 | 56.55 | +41.0% | 1.3% | yes |
| existing-level2 | 94.93 | 56.68 | +40.3% | 0.7% | yes |
| existing-mixed-markers | 94.03 | 55.44 | +41.0% | 3.8% | yes |
| existing-case-insensitive | 89.62 | 53.05 | +40.8% | 0.9% | yes |

### `scripts/update-sig-tables.py::render_group` — C1S5-render-group-light (C1.S5)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +79.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| deep-resources | 106.37 | 16.67 | +84.3% | 0.8% | yes |
| people-heavy | 102.64 | 11.68 | +88.6% | 0.3% | yes |
| bare-meetings | 107.51 | 41.34 | +61.6% | 0.6% | yes |
| mixed-large | 104.41 | 17.79 | +83.0% | 0.3% | yes |

### `scripts/baremetal-runner-report.py::render_table` — C6S1-render-table-runs (C6.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +12.0%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-groups | 68.49 | 56.57 | +17.4% | 12.9% | yes |
| half-filtered | 63.11 | 56.32 | +10.8% | 8.7% | yes |
| mixed | 62.74 | 56.33 | +10.2% | 3.7% | yes |
| many-distinct-runs | 60.89 | 55.13 | +9.5% | 7.6% | yes |

## Confirmed, not applied

### `scripts/move-to-emeritus.py::_add_to_emeritus` — C1S4-add-emeritus-single-pass (C1.S4)

**confirmed** — not applied: changes the same function as C8S3-add-emeritus-compiled, which is applied; both were written against the original, so only one can be
Mean saving across its cases: +13.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 65.74 | 56.98 | +13.3% | 5.7% | yes |
| existing-level2 | 64.06 | 55.24 | +13.8% | 0.5% | yes |
| existing-mixed-markers | 63.10 | 54.38 | +13.8% | 2.1% | yes |
| existing-case-insensitive | 60.72 | 52.28 | +13.9% | 1.1% | yes |

## Measured, not confirmed

### `scripts/move-to-emeritus.py::_check_events` — C3S5-check-events (C3.S5)

**mixed** — a trade-off, not a fix: 17.4% saved on 'big-mixed' but 15.4% lost on 'huge-remaining', both clearing the 1.9% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -1.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| big-mixed | 63.11 | 52.08 | +17.5% | 7.7% | yes |
| single-type | 50.91 | 54.26 | -6.6% | 6.2% | yes |
| huge-remaining | 54.20 | 62.52 | -15.4% | 1.8% | yes |
| exclude-all | 51.68 | 53.35 | -3.2% | 3.3% | no: pairs disagree |

### `scripts/move-to-emeritus.py::_build_pr_body` — C10S4-pr-body (C10.S4)

**partial** — saves energy on 3 of 4 inputs ('large', 'with-warning', 'same-role'; best 6.6% +-0.1% on 'with-warning'), and no saving that can be told from noise on the rest: 'duplicates' +4.3% +-5.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Mean saving across its cases: +4.6%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 65.37 | 62.98 | +3.7% | 1.2% | yes |
| with-warning | 65.57 | 61.22 | +6.6% | 0.1% | yes |
| same-role | 63.37 | 61.03 | +3.7% | 1.7% | yes |
| duplicates | 64.17 | 61.40 | +4.3% | 5.8% | no: pairs disagree |

### `scripts/move-to-emeritus.py::_parse_members` — C3S1-parse-members-comp (C3.S1)

**partial** — saves energy on 2 of 4 inputs ('no-trailing-15k', 'unicode-8k'; best 2.8% +-0.9% on 'unicode-8k'), and no saving that can be told from noise on the rest: 'large-mixed-25k' +3.4% +-3.7% (its pairs disagree too much to tell); 'near-miss-12k' +4.4% +-4.5% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Mean saving across its cases: +3.2%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-mixed-25k | 64.19 | 62.01 | +3.4% | 3.7% | no: pairs disagree |
| no-trailing-15k | 58.71 | 57.27 | +2.4% | 1.5% | yes |
| unicode-8k | 55.36 | 53.84 | +2.8% | 0.9% | yes |
| near-miss-12k | 57.16 | 54.65 | +4.4% | 4.5% | no: pairs disagree |

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C3S2-validate-hoist-sets (C3.S2)

**partial** — saves energy on 3 of 4 inputs ('typical-tree', 'parent-cycle', 'large-mixed'; best 57.6% +-0.9% on 'large-mixed'), and no saving that can be told from noise on the rest: 'deep-parent-chain' +1.3% +-0.8% (within the 1.9% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +28.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 107.54 | 52.02 | +51.6% | 0.5% | yes |
| deep-parent-chain | 61.76 | 60.94 | +1.3% | 0.8% | no: within the floor |
| parent-cycle | 55.87 | 53.31 | +4.6% | 3.7% | yes |
| large-mixed | 104.80 | 44.47 | +57.6% | 0.9% | yes |

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — C1S1-validate-parent-kind (C1.S1)

**regressed** — the repair costs more than the code it replaces: 3.2% lost on 'parent-cycle', above the 1.9% noise floor, and no case improved. Worse on 1 of 4 cases ('parent-cycle').
Mean saving across its cases: -0.4%.
The agent measured `negligible`; re-measured `regressed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 56.35 | 55.36 | +1.8% | 0.4% | no: within the floor |
| deep-parent-chain | 64.06 | 65.53 | -2.3% | 2.7% | no: pairs disagree |
| parent-cycle | 57.18 | 59.00 | -3.2% | 0.5% | yes |
| large-mixed | 56.03 | 54.87 | +2.1% | 4.1% | no: pairs disagree |

### `scripts/update-sig-tables.py::render_group` — C10S4-render-group-join (C10.S4)

**partial** — saves energy on 1 of 4 inputs ('bare-meetings'; best 3.5% +-0.6% on 'bare-meetings'), and no saving that can be told from noise on the rest: 'deep-resources' +1.0% +-0.5% (within the 1.9% noise floor); 'people-heavy' +0.2% +-0.9% (its pairs disagree too much to tell); 'mixed-large' +2.7% +-5.3% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +1.8%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `negligible`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| deep-resources | 56.62 | 56.08 | +1.0% | 0.5% | no: within the floor |
| people-heavy | 56.93 | 56.83 | +0.2% | 0.9% | no: pairs disagree |
| bare-meetings | 57.82 | 55.83 | +3.5% | 0.6% | yes |
| mixed-large | 57.88 | 56.28 | +2.8% | 5.3% | no: pairs disagree |

### `scripts/update-sig-tables.py::render_sig_details_group` — C10S4-sig-details-join (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +1.4% +-6.1% on 'medium', against a clean 1.9% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.4%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| medium | 54.19 | 53.38 | +1.5% | 6.1% | no: pairs disagree |
| large | 56.63 | 57.18 | -1.0% | 10.9% | no: pairs disagree |
| half-empty | 57.29 | 57.17 | +0.2% | 5.7% | no: pairs disagree |
| huge-mixed | 57.62 | 57.04 | +1.0% | 1.7% | no: pairs disagree |

### `scripts/gc-elections/create-github-comments.py::sync` — C1S4-sync-mentions-once (C1.S4)

**partial** — saves energy on 1 of 4 inputs ('many-comments-few-stale'; best 14.3% +-2.6% on 'many-comments-few-stale'), and no saving that can be told from noise on the rest: 'all-stale' +0.2% +-1.0% (its pairs disagree too much to tell); 'large-comments' +0.6% +-0.8% (its pairs disagree too much to tell); 'big-file' +1.2% +-0.7% (within the 1.9% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 66.65 | 57.14 | +14.3% | 2.6% | yes |
| all-stale | 69.99 | 69.88 | +0.2% | 1.0% | no: pairs disagree |
| large-comments | 56.23 | 55.91 | +0.6% | 0.8% | no: pairs disagree |
| big-file | 63.39 | 62.62 | +1.2% | 0.8% | no: within the floor |

### `scripts/generate-sponsorship-ledger.py::rank_gc` — C6S2-rank-gc-sorted (C6.S2)

**negligible** — no case moved more than the noise: the largest reading was +4.6% +-35.0% on 'all-ties-30k', against a clean 1.9% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.9%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-ties-30k | 102.98 | 97.76 | +5.1% | 35.0% | no: pairs disagree |
| all-empty-30k | 86.47 | 87.58 | -1.3% | 3.8% | no: pairs disagree |
| big-60k | 61.45 | 62.18 | -1.2% | 15.1% | no: pairs disagree |
| int-keys-50k | 92.86 | 91.75 | +1.2% | 2.3% | no: pairs disagree |

## Not measured

### `scripts/move-to-emeritus.py::_get_repo_commenters` — C5S1-commenters-seen (C5.S1)

**no_inputs** — no inputs could be generated for scripts/move-to-emeritus.py::_get_repo_commenters: it cannot run here: `_get_repo_commenters` performs live HTTP requests to the GitHub REST API (`request_with_retry` → `urllib.request.urlopen` on `https://api.github.com/repos/open-telemetry/<repo>/issues/comments`), so every call requires network access to a remote service and credentials/rate limits; no input can avoid that (pre-filling the module cache or pointing the API base at fake data would be a mock, not a real input). Next: its repairs cannot be measured here: record their suspicions as `blocked`, quoting this reason, and ask for the next unit you would measure instead -- a failed unit does not use up one of the 30

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `scripts/move-to-emeritus.py::_get_repo_commenters` a: blocked — inputs.py: it cannot run here: _get_repo_commenters performs live HTTP requests to the GitHub REST API (request_with_retry -> urllib.request.urlopen); no input can avoid it. A first attempt also failed to load its generated inputs.
- `scripts/move-to-emeritus.py::_check_reviews` a: blocked — inputs.py: it cannot run here: _check_reviews performs live GitHub API calls (request_with_retry -> urllib.request.urlopen against GRAPHQL_API / REST_API) for every non-empty input, so no realistic input can run without network access.
- `scripts/move-to-emeritus.py::_check_reviews` b: blocked — inputs.py: it cannot run here: _check_reviews performs live GitHub API calls (request_with_retry -> urllib.request.urlopen against GRAPHQL_API / REST_API) for every non-empty input, so no realistic input can run without network access.
- `scripts/move-to-emeritus.py::check_maintainer_activity` a: blocked — inputs.py: it cannot run here: check_maintainer_activity makes GitHub REST/GraphQL requests; every non-trivial input requires network access to api.github.com, which is unavailable here.
- `scripts/move-to-emeritus.py::check_maintainer_activity` b: blocked — inputs.py: it cannot run here: check_maintainer_activity makes GitHub REST/GraphQL requests; every non-trivial input requires network access to api.github.com, which is unavailable here.
- `scripts/move-to-emeritus.py::check_maintainer_activity` c: blocked — inputs.py: it cannot run here: check_maintainer_activity makes GitHub REST/GraphQL requests; every non-trivial input requires network access to api.github.com, which is unavailable here.
- `scripts/move-to-emeritus.py::_parse_members` b: deferred — needs a module-level compiled constant, and a submission can only replace whole functions; a function-local compile would not remove the per-call compile
- `scripts/baremetal-runner-report.py::collect_jobs` a: blocked — inputs.py: it cannot run here: collect_jobs shells out through gh_paginated to the `gh api` CLI, needing network access, GitHub credentials and a gh binary; no argument avoids it.
- `scripts/baremetal-runner-report.py::collect_jobs` b: blocked — inputs.py: it cannot run here: collect_jobs shells out through gh_paginated to the `gh api` CLI, needing network access, GitHub credentials and a gh binary; no argument avoids it.
- `scripts/gc-elections/generate-voters-roll.py::build_devstats_rows` a: blocked — inputs.py: it cannot run here: build_devstats_rows calls get_github_login for every name, which issues an HTTP GET to api.github.com; no input can avoid it.
