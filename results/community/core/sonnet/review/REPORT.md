# Energy report — community @ 910f85d

14 units listed, 9 with an accepted suspicion · 8 repairs submitted, 0 deferred · 3 confirmed · 4 partial · 1 negligible · 3 applied
Noise floor 2.1% (from: session calibration).

## Applied

### `scripts/baremetal-runner-report.py::render_table` — render-table-runs-set

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +10.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-groups | 68.00 | 58.98 | +13.3% | 7.6% | yes |
| half-filtered | 67.17 | 59.38 | +11.6% | 6.6% | yes |
| mixed | 68.06 | 61.59 | +9.5% | 3.5% | yes |
| many-distinct-runs | 65.69 | 60.17 | +8.4% | 7.6% | yes |

### `scripts/move-to-emeritus.py::_add_to_emeritus` — emeritus-single-match-pass

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +15.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 99 `if not token:` (SystemExit).
Loaded skipping failing top-level statements: line 99 `if not token:` (SystemExit).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| existing-large | 68.49 | 58.05 | +15.2% | 4.2% | yes |
| existing-level2 | 68.33 | 57.77 | +15.5% | 0.3% | yes |
| existing-mixed-markers | 67.80 | 56.98 | +16.0% | 0.5% | yes |
| existing-case-insensitive | 68.66 | 57.67 | +16.0% | 0.8% | yes |

### `scripts/update-sig-tables.py::render_group` — render-group-skip-people

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +48.5%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| deep-resources | 112.10 | 52.83 | +52.9% | 2.8% | yes |
| people-heavy | 111.64 | 16.98 | +84.8% | 1.0% | yes |
| bare-meetings | 57.39 | 56.18 | +2.1% | 0.3% | yes |
| mixed-large | 112.66 | 51.49 | +54.3% | 1.3% | yes |

## Measured, not confirmed

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — validate-team-sets

**partial** — saves energy on 3 of 4 inputs ('typical-tree', 'parent-cycle', 'large-mixed'; best 58.5% +-2.1% on 'large-mixed'), and no saving that can be told from noise on the rest: 'deep-parent-chain' +1.4% +-0.5% (within the 2.1% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +28.9%.
The agent measured `confirmed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 100.89 | 47.85 | +52.6% | 0.2% | yes |
| deep-parent-chain | 63.44 | 62.57 | +1.4% | 0.5% | no: within the floor |
| parent-cycle | 56.25 | 54.44 | +3.2% | 1.9% | yes |
| large-mixed | 104.15 | 43.21 | +58.5% | 2.0% | yes |

### `scripts/validate-workstreams.py::validate_workstreams_semantics` — validate-dead-parent-kind

**negligible** — no case moved more than the noise: the largest reading was -2.3% +-2.5% on 'parent-cycle', against a clean 2.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-tree | 53.34 | 53.08 | +0.5% | 2.0% | no: pairs disagree |
| deep-parent-chain | 65.08 | 65.52 | -0.7% | 0.9% | no: pairs disagree |
| parent-cycle | 58.53 | 59.88 | -2.3% | 2.5% | no: pairs disagree |
| large-mixed | 56.51 | 56.30 | +0.4% | 2.3% | no: pairs disagree |

### `scripts/gc-elections/create-github-comments.py::sync` — sync-single-pass-removal

**partial** — saves energy on 3 of 4 inputs ('all-stale', 'large-comments', 'big-file'; best 95.8% +-5.1% on 'large-comments'), and no saving that can be told from noise on the rest: 'many-comments-few-stale' +11.1% +-11.2% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +73.0%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `confirmed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 64.47 | 57.26 | +11.2% | 11.2% | no: pairs disagree |
| all-stale | 102.88 | 4.98 | +95.2% | 6.6% | yes |
| large-comments | 91.78 | 3.84 | +95.8% | 5.2% | yes |
| big-file | 106.40 | 10.83 | +89.8% | 5.4% | yes |

### `scripts/gc-elections/create-github-comments.py::sync` — sync-mentions-once

**partial** — saves energy on 1 of 4 inputs ('many-comments-few-stale'; best 14.0% +-3.4% on 'many-comments-few-stale'), and no saving that can be told from noise on the rest: 'all-stale' -0.4% +-4.0% (its pairs disagree too much to tell); 'large-comments' +0.7% +-0.6% (within the 2.1% noise floor); 'big-file' +1.6% +-0.1% (within the 2.1% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-comments-few-stale | 63.58 | 54.66 | +14.0% | 3.4% | yes |
| all-stale | 71.33 | 71.60 | -0.4% | 4.0% | no: pairs disagree |
| large-comments | 57.08 | 56.66 | +0.7% | 0.6% | no: within the floor |
| big-file | 64.45 | 63.41 | +1.6% | 0.1% | no: within the floor |

### `scripts/gc-elections/create-github-comments.py::is_voter_comment` — voter-comment-header-prefilter

**partial** — saves energy on 1 of 4 inputs ('no-header-long'; best 93.8% +-0.2% on 'no-header-long'), and no saving that can be told from noise on the rest: 'header-first-200k' -2.1% +-6.1% (its pairs disagree too much to tell); 'header-late-miss' -1.0% +-3.2% (its pairs disagree too much to tell); 'header-padded' +1.6% +-2.1% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +23.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| header-first-200k | 55.89 | 57.02 | -2.0% | 6.1% | no: pairs disagree |
| header-late-miss | 54.91 | 55.42 | -0.9% | 3.2% | no: pairs disagree |
| no-header-long | 106.33 | 6.60 | +93.8% | 0.2% | yes |
| header-padded | 51.53 | 50.73 | +1.6% | 2.1% | no: pairs disagree |

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `scripts/baremetal-runner-report.py::collect_jobs` a: blocked — inputs.py: it cannot run here: `collect_jobs` fetches GitHub Actions workflow runs and jobs via `gh_paginated`, which shells out to the `gh api` CLI to query github.com — it needs network access and subprocesses, both unavailable here
- `scripts/move-to-emeritus.py::_get_repo_commenters` a: blocked — inputs.py: it cannot run here: `_get_repo_commenters` calls `request_with_retry("GET", url)` which performs a live HTTP request to https://api.github.com; no input can avoid it
- `scripts/gc-elections/generate-voters-roll.py::build_devstats_rows` a: blocked — inputs.py: it cannot run here: `build_devstats_rows` calls `get_github_login` for every name, which issues `requests.get` to https://api.github.com/users/{username}; it needs live network access to GitHub
