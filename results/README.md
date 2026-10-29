# Main experiment results

One folder per run: `results/<repository>/<configuration>/<model>/`, copied as-is
from `~/energy-exp/archive/` after the run finished. The folder is in
`.gitignore` until it is decided whether to push it. `summary.csv` holds one
row per run, as `experiment/lib/summarize.py` wrote it.

Configurations use the repository's names: `knowledge` is **Taxonomy** in the
paper, `full` is **Taxonomy+Rules**, `control` is **Unguided**.

## Runs

| Run | Date | Project commit | Model, effort | Auth | Agent / review |
|---|---|---|---|---|---|
| `sample-apps/knowledge/sonnet` | 2026-10-26 10:40 | `1068f79` | claude-sonnet-5-5, high | subscription | 40.6 min / 27.4 min |
| `dx-toolkit/full/sonnet` | 2026-10-26 17:15 | `1068f79` | claude-sonnet-5-5, high | subscription | 87.3 min (77.6 working, then 9.6 waiting on its own stale wait loop) / 16.5 min |
| `dx-toolkit/full/haiku` | 2026-10-26 20:02 | `1068f79` | claude-haiku-5-5, high | api | 52.7 min / 14.0 min |
| `dx-toolkit/control/sonnet` | 2026-10-27 06:32 | `1068f79` | claude-sonnet-5-5, high | subscription | 43.6 min (about 35 working; 8 waiting on its own stale wait loop) / 21.2 min |
| `sample-apps/full/sonnet` | 2026-10-26 21:18 | `1068f79` | claude-sonnet-5-5, high | subscription | 55.7 min (about 34 working; verify had finished at 32 min, and the agent waited 22 min on its own stale wait loop) / 18.5 min |
| `dx-toolkit/knowledge/sonnet` | 2026-10-27 10:02 | `1068f79` | claude-sonnet-5-5, high | subscription | 95.3 min (about 38 working; 57 waiting on its own stale wait loops, 32 after the first verify and 25 after the second) / 22.6 min |

| `sample-apps/control/haiku` | 2026-10-27 14:38 | `1068f79` | claude-haiku-5-5, high | api | 57.8 min / 18.6 min |
| `dx-toolkit/knowledge/haiku` | 2026-10-27 16:55 | `1068f79` + uncommitted leak fix (comments and the Unguided skill only; this skill's behaviour unchanged) | claude-haiku-5-5, high | subscription | 25.4 min / 9.0 min; $20.23 list price, from re-starting one Monitor 265 times |
| `sample-apps/knowledge/haiku` | 2026-10-27 19:26 | `1068f79` + uncommitted leak fix | claude-haiku-5-5, high | api | 49.8 min / 26.7 min |
| `dx-toolkit/control/haiku` | 2026-10-27 21:19 | `1068f79` + uncommitted leak fix (first Unguided run with it) | claude-haiku-5-5, high | subscription | 50.1 min / 7.3 min; only 6 of 31 units got inputs, most of the rest need the network |
| `sample-apps/full/haiku` | 2026-10-28 04:22 | `1068f79` + uncommitted leak fix | claude-haiku-5-5, high | subscription | 40.3 min / 27.9 min; the agent pip-installed `tiktoken` into its venv |
| `sample-apps/control/sonnet` | 2026-10-28 06:13 | `024f75f` (the leak fix, committed) | claude-sonnet-5-5, high | subscription | 39.2 min / 19.4 min |
| `community/control/haiku` | 2026-10-28 07:22 | `024f75f` | claude-haiku-5-5, high | subscription | 28.9 min / 5.9 min; 7 of 11 units need the GitHub API |
| `community/full/haiku` | 2026-10-28 08:03 | `024f75f` | claude-haiku-5-5, high | subscription | 12.6 min / 3.7 min; 9 of 13 units need the GitHub API |
| `community/full/sonnet` | 2026-10-28 08:40 | `024f75f` | claude-sonnet-5-5, high | subscription | 27.6 min / 16.6 min |
| `community/knowledge/sonnet` | 2026-10-28 12:28 | `024f75f` | claude-sonnet-5-5, high | subscription | 34.6 min / 14.8 min |
| `community/knowledge/haiku` | 2026-10-28 14:30 | `024f75f` | claude-haiku-5-5, high | subscription | 20.2 min / 6.0 min; only 5 of 15 units got inputs (the GitHub API) |
| `community/control/sonnet` | 2026-10-28 14:56 | `024f75f` | claude-sonnet-5-5, high | subscription | 10.3 min / 6.7 min |
| `sample-apps/full/opus` | 2026-10-28 09:34 | `024f75f` | claude-opus-5-5, high | subscription | 36.2 min / 22.6 min; extra to the 18 main runs. The agent upgraded `colpali_engine` (0.2.2 to 0.3.18) in its venv, so colpali functions ran here and nowhere else |

| `sample-apps/knowledge/opus` | 2026-10-28 15:19 | `024f75f` | claude-opus-5-5, high | subscription | 51.9 min / 22.6 min; extra to the 18 main runs. 31 repairs written, 11 beyond the 20 places; 4 colpali repairs errored in the agent's own verify because the module does not load here |

| `sample-apps/control/opus` | 2026-10-28 19:51 | `024f75f` | claude-opus-5-5, high | subscription | 38.8 min / 24.5 min; extra to the 18 main runs. `match-semantic-yql-once` (confirmed 91.9%) builds a query string that depends on no argument once and keeps it in a module global, like the constant tables below |

All 18 main runs (3 repositories x 3 configurations x Sonnet and Haiku) are here,
plus all three configurations on Opus for sample-apps.

## Known problems in these results (found Oct 28, after the runs)

- **Repairs that cache across calls.** The inputs build large objects once and
  every measured call receives the same object, so a repair that stores results
  on it (or on a function attribute or a global) is faster from the second call
  on. Four do, and their savings are not per-call savings:
  `sample-apps/control/haiku` `sample-valid-data-cache-tensors` (confirmed 97.8%),
  `dx-toolkit/control/haiku` `pool-manager-cache` (confirmed 37.4%),
  `sample-apps/control/sonnet` `ctrl-translate` (confirmed 92.4%; a lazily filled
  table of fixed Unicode facts, borderline), and `dx-toolkit/full/sonnet`
  `C8S1-final-payload-columns` (partial 3.5%).
- **One behaviour change the equivalence check missed.**
  `sample-apps/full/haiku` `C1S5-read-data-no-timestamp` (confirmed 66.1%) drops
  the `timestamp` key from every record. `MindData.__init__` calls `read_data`,
  so the two sides' objects already differed before the call, and verify.py
  skips the argument comparison when that happens.
- **Constant tables built on the first call** (correct, but their one-time
  cost is not measured): `escape_folder_str`, `escape_unicode_string` (twice),
  and `remove_control_characters` in `sample-apps/knowledge/haiku`
  (`C10S1-control-translate`, a table over all 1.1 million code points).

The archive's `sample-apps/full/haiku.8` is an Oct 19 pilot (medium effort, commit
`89d6c47`) that sat in this run's folder; it is not part of the main experiment.

A first start of `dx-toolkit/knowledge/haiku` at 13:09 hit the plan's session
limit after about 30 minutes and was stopped by hand. It is not here; the run
above is the restart.

A first start of `dx-toolkit/knowledge/sonnet` at 09:00 hit the plan's session
limit after 10 minutes. It was discarded and is not here; the run above is the
restart.

The morning pilot of `sample-apps/full/sonnet` (project commit `5107c0a`) is not
here: it ran before the last fixes, and is kept in the archive as `sonnet.11`.

## What a run folder holds

| Path | What |
|---|---|
| `run.json`, `meta.json` | the run's settings, and everything `summarize.py` derived from it |
| `transcript.jsonl` | Claude Code's stream-json output, verbatim |
| `agent/` | the agent's files: `step1-3.jsonl`, `submissions.jsonl`, `findings.jsonl` (the three steps joined), and its read-only copy of the inputs (`.energy-inputs/`) |
| `record/` | what the step keeper kept: each step's file at `step.py done N` (`steps/`), every measured repair (`measured.jsonl`, `submissions_all.jsonl`), events |
| `inputs/` | our copy of the generated inputs, which the review measures with; `_generation/` holds each generation's prompt, reasoning, reply and report |
| `review/` | our re-measurement: `results.jsonl` (one row per repair, the verdicts we report) and `REPORT.md` |
| `rules.json` | every static rule run over the untouched repository, for comparing with the agent's findings in every configuration |
| `tmp_created/` | what the agent left in `/tmp`: its own scripts and its `verify.py` log (dx-toolkit: also two folders holding empty Unix sockets that `DXLogHandler` inputs created) |
| `venv_before.txt`, `venv_after.txt` | the environment's packages before and after the agent |
| `repo_changes.*` | changes the agent made to the repository (none) |

No credentials: every file was checked against the three keys before copying.
