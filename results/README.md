# Recorded sessions

Every session of the evaluation, copied from the harness's archive after it
finished: `results/<repository>/<skill>/<model>/`. `summary.csv` has one row per
session, as `experiment/lib/summarize.py` wrote it.

The evaluation is the 18 sessions with Sonnet and Haiku (3 repositories x 3
skills x 2 models). The three sessions with Opus on `sample-apps` are additional.

## Sessions

| Session | Model | Effort | Agent (min) | Review (min) | Submissions reviewed |
|---|---|---|---:|---:|---:|
| `sample-apps/core/sonnet` | claude-sonnet-5-5 | high | 39.2 | 19.4 | 30 |
| `sample-apps/core/haiku` | claude-haiku-5-5 | high | 57.8 | 18.6 | 16 |
| `sample-apps/core+tax/sonnet` | claude-sonnet-5-5 | high | 40.6 | 27.4 | 27 |
| `sample-apps/core+tax/haiku` | claude-haiku-5-5 | high | 49.8 | 26.7 | 22 |
| `sample-apps/full/sonnet` | claude-sonnet-5-5 | high | 55.7 | 18.5 | 26 |
| `sample-apps/full/haiku` | claude-haiku-5-5 | high | 40.3 | 27.9 | 20 |
| `dx-toolkit/core/sonnet` | claude-sonnet-5-5 | high | 43.6 | 21.2 | 24 |
| `dx-toolkit/core/haiku` | claude-haiku-5-5 | high | 50.1 | 7.3 | 7 |
| `dx-toolkit/core+tax/sonnet` | claude-sonnet-5-5 | high | 95.3 | 22.6 | 24 |
| `dx-toolkit/core+tax/haiku` | claude-haiku-5-5 | high | 25.4 | 9.0 | 9 |
| `dx-toolkit/full/sonnet` | claude-sonnet-5-5 | high | 87.3 | 16.5 | 26 |
| `dx-toolkit/full/haiku` | claude-haiku-5-5 | high | 52.7 | 14.0 | 13 |
| `community/core/sonnet` | claude-sonnet-5-5 | high | 10.3 | 6.7 | 8 |
| `community/core/haiku` | claude-haiku-5-5 | high | 28.9 | 5.9 | 12 |
| `community/core+tax/sonnet` | claude-sonnet-5-5 | high | 34.6 | 14.8 | 15 |
| `community/core+tax/haiku` | claude-haiku-5-5 | high | 20.2 | 6.0 | 7 |
| `community/full/sonnet` | claude-sonnet-5-5 | high | 27.6 | 16.6 | 17 |
| `community/full/haiku` | claude-haiku-5-5 | high | 12.6 | 3.7 | 14 |
| `sample-apps/core/opus` | claude-opus-5-5 | high | 38.8 | 24.5 | 29 |
| `sample-apps/core+tax/opus` | claude-opus-5-5 | high | 51.9 | 22.6 | 31 |
| `sample-apps/full/opus` | claude-opus-5-5 | high | 36.2 | 22.6 | 22 |

## What a session folder holds

| Path | What |
|---|---|
| `run.json` | the session's settings: repository and commit, skill, model, effort, times |
| `meta.json` | everything `summarize.py` derived from the session (the `summary.csv` row, in full) |
| `transcript.jsonl` | Claude Code's `stream-json` output, verbatim |
| `agent/` | the agent's files: `step1.jsonl`, `step2.jsonl`, `step3.jsonl`, `submissions.jsonl`, `findings.jsonl` (the three steps joined), its read-only copy of the inputs (`.energy-inputs/`) and, with `full`, the rules comparison (`.energy-scan/`) |
| `record/` | what the input service recorded: each step's file when it was finished (`steps/`), every repair the agent measured (`measured.jsonl`, `submissions_all.jsonl`), every rules comparison (`scans.jsonl`), events |
| `inputs/` | the generated inputs, which the review measures with; `_generation/` holds each generation's prompt, reasoning, reply and report |
| `review/` | our re-measurement: `results.jsonl` (one verdict per repair) and `REPORT.md` |
| `rules.json` | every static rule run over the untouched repository |
| `tmp_created.txt`, `tmp_created/` | what the agent created in `/tmp` |
| `venv_before.txt`, `venv_after.txt` | the venv's packages before and after the session |
| `repo_changes.txt`, `repo_changes.diff` | changes the agent made to the repository (none) |
| `inputs-service.log`, `review.log`, `rules.log`, `stderr.log` | logs |

Unit names have the form `path/to/file.py::Class.method`. Every file was
checked for credentials before it was copied here.
