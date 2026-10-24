# Experiment harness

Runs coding agents (Claude Code, `claude -p`) on real repositories with one
skill arm each, re-measures every repair they submit, and writes one row per run
to `summary.csv`. Everything needed to repeat the runs is in this folder; what
the runs produce, and the keys, live outside the repository.

Three places:

| Place | What | Agent can read it? |
|---|---|---|
| `experiment/` (here) | scripts, settings (`config.sh`), the repositories and commits (`repos.tsv`) | yes, like the rest of this repository |
| `$EXP` = `~/energy-exp/` | keys, clean clones, venvs, the inputs cache, results, logs | **no** — locked (`chmod 000`) while an agent runs |
| `$RUN` = `~/energy-run/` | the current run only: the repo copy with its skill, its venv, its Claude config | yes — wiped and rebuilt for every run |

`$EXP` and `$RUN` can be moved with the `ENERGY_EXP` and `ENERGY_RUN` environment variables.

## Files

| Path | What |
|---|---|
| `config.sh` | models, arms, effort, timeouts, prompts — edit here |
| `run_all.sh` | runs the grid one run at a time; run it again to resume |
| `repos.tsv` | the repositories: name, `owner/repo`, the commit every run uses, `.py` files |
| `setup_repos.sh` | clones every repo in `repos.tsv` at its commit into `$EXP/pristine/` (`setup_repos.sh CSV N` is how the list was chosen) |
| `setup_venvs.sh [repos]` | one venv per repo (our tools + numpy, pandas, scipy, requests, pyyaml + the repo's requirements, in one pip resolve, then `pip check`) saved as `$EXP/venvs/<repo>.tar`; WARNING lines say what had to give |
| `lib/repo_deps.py` | the one-resolve install `setup_venvs.sh` uses |
| `lib/summarize.py` | after each run: `meta.json` and a row of `summary.csv` — time, cost, tokens, units examined, cards opened, rule scans, what the comparison with the rules added (full, ast, ruff), verdicts, which accepted findings a rule also flags, and leak / protocol / environment flags |

In `$EXP`, two files you provide, never committed and never printed:

| File | What |
|---|---|
| `api-key` | the Anthropic Console key. Never in the environment: each run gets a one-time copy that Claude reads once and deletes before the agent's first command |
| `openrouter-key` | the key of the input generator (`tools/inputs/`), which runs outside the agent's session |

Results: `$EXP/archive/<repo>/<arm>/<model>/` holds a run — `transcript.jsonl`,
`agent/` (its outputs), `record/` (each step as the agent finished it, every
repair it measured, each comparison of the rules with its list), `inputs/` (the generated inputs), `review/` (our
re-measurement), `rules.json` (every rule on the untouched repository, for
comparing with the agent's findings), `venv_before/after.txt`,
`tmp_created.txt`, `meta.json`.
Earlier attempts of the same run are `<model>.1`, `.2`, ... One row per run in
`$EXP/archive/summary.csv`.

## Commands

From the repository's root:

```bash
experiment/setup_repos.sh                             # clones, at the listed commits
experiment/setup_venvs.sh                             # one venv per repo
experiment/run_all.sh --check                         # one tiny API call (< $0.01)
experiment/run_all.sh --dry-run --repos gedcom        # whole pipeline without Claude
tmux new-session -d -s exp "$(pwd)/experiment/run_all.sh --repos amazon-neptune-tools"
tmux new-session -d -s exp "$(pwd)/experiment/run_all.sh --again --repos amazon-neptune-tools --arms full --models claude-haiku-5-5"
tmux attach -t exp                                    # watch (Ctrl-b d to leave)
column -s, -t < ~/energy-exp/archive/summary.csv      # results
```

While an agent runs, `~/energy-exp` is locked for you too: watch with `tmux attach`.

## The agent

`claude -p` in the repo copy, with `--effort medium`, `bypassPermissions` (every
command allowed, `pip install` included), a time limit, and a clean environment
with `TMPDIR` inside the run folder. It is given no dollar budget:
`--max-budget-usd` shows the budget to the model on every turn, and a model
told it has a budget spends less of its time; cap spending on the Console. What
it installs into its venv stays for the review, which re-measures in that same
venv (both sides of every pair run in it, so it cannot favour either), and dies
with the venv copy. What it creates directly in `/tmp` is listed in
`tmp_created.txt` and deleted after the run, so the next run cannot read this
one's repairs. Cost in `summary.csv` is Claude Code's estimate; the Console bill
is authoritative.
