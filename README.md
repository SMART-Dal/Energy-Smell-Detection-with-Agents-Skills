# Dr. Greens: detecting and refactoring energy smells with agent skills

Dr. Greens is an agent skill for Claude Code that finds **energy smells** in
Python code (code that does more work than its task requires) and repairs them.
Each repair is checked to behave exactly like the original code, and the energy
of both versions is measured on the CPU's energy counters.

The agent works in four steps:

1. **Find**: read every function in the target and list each suspected smell.
2. **Decide**: accept or reject each suspicion after studying it in depth.
3. **Repair and measure**: write a repair for each accepted suspicion. A verifier
   checks that the repair preserves behaviour and measures its energy on inputs
   written by a separate input generator.
4. **Finish**: summarise each repair, its root cause and its verdict.

The agent never edits the repository. It writes its findings and repairs to
files, and only repairs that save energy are recommended.

This repository is the replication package of the paper *Ctrl+Shift+Left:
Detecting and Refactoring Energy Smells using Agent Skills* (Mohammadjavad
Mehditabar, Saurabhsingh Rajput, Tushar Sharma; Dalhousie University). It
contains the three skills, the harness that ran the evaluation, and every
recorded session.

## Contents

- [The three skills](#the-three-skills)
- [Requirements](#requirements)
- [A. Use a skill on your own repository](#a-use-a-skill-on-your-own-repository)
- [B. Reproduce the evaluation](#b-reproduce-the-evaluation)
- [Repository layout](#repository-layout)

## The three skills

Each skill adds one layer of knowledge to the one before it. All three follow
the same four steps and use the same verifier, energy probe and input generator.

| Skill | Folder | What it adds |
|---|---|---|
| **core** | `dist/core/energy-efficiency` | the procedure, the energy probe (`energy.py`), the input generator and the verifier |
| **core+tax** | `dist/core+tax/energy-smells` | the taxonomy: an index of 12 energy smells and 65 root causes, 12 category cards, and 65 root-cause cards with measured repair examples and near-misses |
| **full** | `dist/full/energy-smells` | a static analyzer (`scan.py`): 40 rules of our own and 31 Ruff rules, each mapped to root causes |

A skill folder holds everything the agent needs:

```
energy-smells/
├── SKILL.md               the procedure the agent follows
├── reference/             taxonomy index, category and root-cause cards, how to verify, output format
└── scripts/
    ├── step.py            marks a step as finished
    ├── scan.py            static rules (full only)
    ├── inputs.py          requests inputs from the input generator
    ├── verify.py          checks behaviour and measures energy of each repair
    ├── energy.py          measures the energy of any call, at any step
    └── lib/               shared code (standard library only)
```

## Requirements

- **Linux on an Intel CPU** with readable RAPL energy counters
  (`/sys/class/powercap/intel-rapl:N/energy_uj`). If they are readable only by
  root: `sudo chmod a+r /sys/class/powercap/intel-rapl:[0-9]*/energy_uj`.
- **Python 3.10** or newer for the skill. The evaluation used Python 3.10.12
  (Ubuntu 22.04's `python3`).
- **[Claude Code](https://docs.claude.com/en/docs/claude-code)**, installed and signed in.
- **An [OpenRouter](https://openrouter.ai) API key.** The input generator uses
  DeepSeek V4.1 Flash through OpenRouter to write the inputs each repair is
  measured on. The evaluation's 523 units cost $1.23 in total, about a quarter
  of a cent each.
- For section B only: an Anthropic API key, `git`, and about 25 GB of free disk space.

Energy readings cover the whole CPU package, so measure on an otherwise idle machine.

## A. Use a skill on your own repository

You need two folders of this repository: `dist/` (the skills) and `tools/` (the
input generator). Download it with **Code > Download ZIP**, or `git clone` it.
Below, `dr-greens/` is where you put it and `~/my-project` is your repository.

**1. Copy one skill into your repository.** Claude Code loads skills from
`.claude/skills/`:

```bash
mkdir -p ~/my-project/.claude/skills
cp -r dr-greens/dist/full/energy-smells ~/my-project/.claude/skills/
```

For the other skills, copy `dist/core+tax/energy-smells` or
`dist/core/energy-efficiency` instead. Install one skill at a time.

**2. Activate your project's venv and add the skill's packages.** The skill
runs and measures your code in this venv.

```bash
source ~/my-project/.venv/bin/activate
pip install -r dr-greens/requirements-skill.txt      # codegreen, ruff, numpy, pandas, scipy, requests, pyyaml
```

If your project has no venv yet, create one and install its dependencies first:

```bash
python3 -m venv ~/my-project/.venv
source ~/my-project/.venv/bin/activate
pip install -r ~/my-project/requirements.txt         # or: pip install -e ~/my-project
```

If your project declares no dependencies, install the packages its code
imports. For example, `open-telemetry/community` also needs `jsonschema`.

**3. Start the input generator** in a terminal with the venv activated, and
leave it running. It writes the inputs each repair is measured on, with your
OpenRouter key. It runs outside the Claude Code session, so the agent never
sees the key and cannot choose the inputs its repairs are measured on.

The generator reads the key from a file. Create a key at
[openrouter.ai/keys](https://openrouter.ai/keys) (it starts with `sk-or-`),
then save it in a text file that holds only the key, on one line:

```bash
nano ~/openrouter-key          # paste the key, save with Ctrl-O, exit with Ctrl-X
chmod 600 ~/openrouter-key     # readable only by you
```

Then start the generator, giving it your repository and the key file:

```bash
dr-greens/start_inputs.sh ~/my-project ~/openrouter-key
```

**4. Start Claude Code** in a second terminal, with the same venv activated:

```bash
cd ~/my-project
export ENERGY_INPUTS_SOCKET=~/.energy-skill/my-project/inputs.sock   # printed by start_inputs.sh
claude
```

Then ask, for example:

```
Find the energy smells in this repository using the energy-smells skill.
Find the energy smells in src/parser.py using the energy-smells skill.
Find the energy smells in src/parser.py::Parser.tokenize using the energy-smells skill.
```

With the core skill, ask: `Find where this repository wastes energy, using the
energy-efficiency skill.` Any model works; choose it with `/model`.

**5. Read the results.** The agent does not edit your code. It writes
`step1.jsonl`, `step2.jsonl`, `step3.jsonl` and `submissions.jsonl` in the
repository root. Each line of `submissions.jsonl` is one repair: the new source
of the function, and its verdict in `agent_measurement.status`:

| Verdict | Meaning |
|---|---|
| `confirmed` | saves energy on every input |
| `partial` | saves energy on some inputs, no measurable change on the others |
| `mixed` | saves on some inputs, costs more on others |
| `regressed` | costs more on every input that changed |
| `negligible` | no change beyond the measurement noise |
| `inconclusive` | the machine was too noisy to resolve the effect |

Repairs that were not measured are `not_equivalent` (behaviour differs),
`no_inputs` (no inputs could be generated, for example because the code needs
the network), `invalid`, `error` or `over_limit`. A session measures at most 20
repairs; other accepted suspicions are recorded as `deferred` in `step3.jsonl`.

Before a new session in the same repository, remove the previous session's files:

```bash
chmod -R u+w .energy-inputs; rm -rf step?.jsonl submissions.jsonl .energy-inputs .energy-scan
```

## B. Reproduce the evaluation

The evaluation runs every skill with Claude Sonnet 5.5 and Claude Haiku 5.5, at
high reasoning effort, on three repositories (`experiment/repos.tsv`):

| Repository | Commit | Domain |
|---|---|---|
| `vespa-engine/sample-apps` | `e2ed22d` | search application samples |
| `dnanexus/dx-toolkit` | `accd86a` | genomics cloud toolkit |
| `open-telemetry/community` | `910f85d` | project automation scripts |

**1. Keys.** The harness reads two keys from two files in `~/energy-exp`, each
holding only the key, on one line: an Anthropic API key
([console.anthropic.com](https://console.anthropic.com), it starts with
`sk-ant-`) and an OpenRouter key ([openrouter.ai/keys](https://openrouter.ai/keys),
it starts with `sk-or-`).

```bash
mkdir -p ~/energy-exp && chmod 700 ~/energy-exp
nano ~/energy-exp/api-key            # paste the Anthropic key, save with Ctrl-O, exit with Ctrl-X
nano ~/energy-exp/openrouter-key     # paste the OpenRouter key, save, exit
chmod 600 ~/energy-exp/api-key ~/energy-exp/openrouter-key
```

The keys are never visible to the agent: Claude Code reads the API key once,
and `~/energy-exp` is locked (`chmod 000`) while a session runs.

**2. Setup.** Clones each repository at its commit and builds one venv per
repository:

```bash
./setup.sh                      # or only one venv: ./setup.sh community
```

**3. Check, then run.**

```bash
./run.sh --check                                          # Claude Code starts (one short call)
./run.sh --dry-run --repos community                      # the whole pipeline without Claude
./run.sh --repos community --skills full --models haiku   # one session
./run.sh                                                  # all 18 sessions
```

| Option | Values | Default |
|---|---|---|
| `--repos` | names from `experiment/repos.tsv` | all three |
| `--skills` | `core`, `core+tax`, `full` | all three |
| `--models` | `sonnet`, `haiku`, `opus` | `sonnet haiku` |
| `--again` | run a finished session again (the earlier one is kept) | |

Sessions run one at a time, since energy is measured on the same machine. A
session lasts up to 2 hours, followed by up to 40 minutes of re-measurement.
Finished sessions are skipped, so running the same command again resumes the
grid. Run it inside `tmux` to keep it alive after you log out:
`tmux new -d -s exp ./run.sh`.

**4. Results.** Each session is saved in
`~/energy-exp/archive/<repo>/<skill>/<model>/`, with one row per session in
`~/energy-exp/archive/summary.csv`. The folder layout is the same as in
`results/`, described in [`results/README.md`](results/README.md). Agents are
not deterministic, so a new session finds and repairs different code than the
recorded one, and energy readings depend on the hardware.

More on the harness, its settings and its environment variables:
[`experiment/README.md`](experiment/README.md).

## Repository layout

```
.
├── dist/                  the three skills, ready to copy (generated)
│   ├── core/energy-efficiency/
│   ├── core+tax/energy-smells/
│   └── full/energy-smells/
├── src/                   source of the skills' scripts: verifier, scanner, energy meter
├── taxonomy/              the energy smell taxonomy (12 smells, 65 root causes)
├── catalog/               per root cause: patterns, measured repairs, near-misses
├── build/                 renders the taxonomy, catalog and templates into dist/
├── tools/
│   ├── inputs/            the input generator and its service
│   └── review.py          re-measures submitted repairs and writes a report
├── experiment/            the evaluation harness (run_all.sh, config.sh, repos.tsv)
├── results/               every recorded session of the evaluation
├── validation/            measured repair cases behind the cards, near-miss specimens
├── tests/rules/           tests of every static rule
├── data/manual_sampling/  hand-written before/after sample pairs
├── setup.sh, run.sh       reproduce the evaluation (section B)
├── start_inputs.sh        start the input generator for your repository (section A)
├── requirements.txt       packages of the harness and the build
└── requirements-skill.txt packages the skill needs in your venv
```
