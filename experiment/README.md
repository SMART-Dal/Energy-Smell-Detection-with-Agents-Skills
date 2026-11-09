# Experiment harness

Runs Claude Code (`claude -p`) on each repository with one skill installed,
re-measures every repair the agent submits, and writes one row per session to
`summary.csv`. `../setup.sh` and `../run.sh` wrap these scripts; see the
top-level README for the usual commands.

## Files

| File | What it does |
|---|---|
| `config.sh` | settings: models, skills, effort, time limits, prompts, folders |
| `repos.tsv` | the repositories: name, `owner/repo`, the commit every session uses, number of `.py` files |
| `setup_repos.sh` | clones every repository in `repos.tsv` at its commit into `$EXP/pristine/` |
| `setup_venvs.sh [repos]` | builds one venv per repository and saves it as `$EXP/venvs/<repo>.tar` |
| `run_all.sh` | runs the grid one session at a time; finished sessions are skipped |
| `lib/repo_deps.py` | installs a repository's dependencies in one pip resolve (used by `setup_venvs.sh`) |
| `lib/summarize.py` | after each session: `meta.json` and a row of `summary.csv` |
| `lib/repo_stats.py` | files, units and lines of each repository at its commit |

## Folders

| Folder | Holds | Readable by the agent |
|---|---|---|
| `$EXP` = `~/energy-exp` | the key files, clean clones, venvs, the inputs cache, results, logs | no: locked (`chmod 000`) while a session runs |
| `$RUN` = `~/energy-run` | the current session: the repository copy with its skill, its venv, its Claude configuration | yes; rebuilt for every session |

Environment variables:

| Variable | Default | Sets |
|---|---|---|
| `ENERGY_EXP` | `~/energy-exp` | `$EXP` |
| `ENERGY_RUN` | `~/energy-run` | `$RUN` (keep the path short: it holds a Unix socket) |
| `ENERGY_REPOS` | `experiment/repos.tsv` | the repository list |
| `PYTHON` | `python3` | the interpreter the venvs are built with |

Two files you provide in `$EXP`, each holding one key: `api-key` (Anthropic)
and `openrouter-key` (the input generator, which runs outside the agent's session).

## One session

One session is one repository x one skill x one model:

1. `$RUN` gets a fresh copy of the repository with the skill in
   `.claude/skills/`, a fresh copy of the repository's venv, and an empty
   Claude configuration.
2. The input service (`tools/inputs/service.py`) starts. It writes the inputs
   repairs are measured on when the agent asks for them, records each finished
   step, and unlocks the root-cause cards after step 1.
3. `$EXP` is locked.
4. `claude -p` runs in the repository with the skill's prompt (`config.sh`),
   every command allowed, and a 120-minute limit.
5. `$EXP` is unlocked, the input service finishes, the agent's files are saved,
   every static rule is run on the untouched repository (`rules.json`), files
   the agent left in `/tmp` are recorded and deleted, `tools/review.py`
   re-measures every submission, and `lib/summarize.py` adds a row to
   `summary.csv`.

A session that ends on an API error before step 3 is finished is kept as
`<model>.cut-<time>` and runs again next time; on a usage limit the grid stops.

## Output

`$EXP/archive/<repo>/<skill>/<model>/` holds one session, in the layout
described in [`../results/README.md`](../results/README.md). An earlier session
of the same combination, kept by `--again`, is `<model>.1`, `<model>.2`, ...
Dry runs go to `$EXP/archive-dry/`.

```bash
column -s, -t < ~/energy-exp/archive/summary.csv | less -S
```
