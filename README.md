# Dr. Greens

**Find and repair energy smells in Python code with Claude Code.**

Dr. Greens is an agent skill: a folder you copy into your project, which Claude
Code loads when you ask it to look for energy waste. The agent reads your code,
finds **energy smells** (code that does more work than its task requires),
writes a repair for each one, and has every repair checked for identical
behaviour and measured for energy on your machine. It never edits your code;
you choose which measured repairs to apply.

This repository accompanies the paper *Ctrl+Shift+Left: Detecting and
Refactoring Energy Smells using Agent Skills* (Mohammadjavad Mehditabar,
Saurabhsingh Rajput, Tushar Sharma; Dalhousie University).

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [The three skills](#the-three-skills)
- [Reproducing the evaluation](#reproducing-the-evaluation)
- [Repository layout](#repository-layout)
- [Citation](#citation)

## How it works

The agent follows four steps:

1. **Find.** It reads every function in the target and lists each suspected energy smell.
2. **Decide.** It accepts or rejects each suspicion after studying it in depth.
3. **Repair and measure.** It writes a repair for each accepted suspicion. A
   verifier runs the original and the repaired function on the same inputs,
   checks that they behave identically, and measures the energy of both.
4. **Finish.** It summarises every repair, its root cause and its verdict.

The inputs a repair is measured on are written by a separate **input
generator**, which uses an LLM (DeepSeek V4.1 Flash through OpenRouter). It
runs outside the Claude Code session, so the agent cannot choose the inputs its
own repairs are measured on.

## Requirements

| | |
|---|---|
| Operating system | Linux on an Intel CPU, with readable RAPL energy counters |
| Python | 3.10 or newer, in the project's venv |
| Agent | [Claude Code](https://docs.claude.com/en/docs/claude-code), installed and signed in |
| Input generator | an [OpenRouter](https://openrouter.ai/keys) API key; inputs cost about a quarter of a cent per function |

If the RAPL counters are readable only by root:
`sudo chmod a+r /sys/class/powercap/intel-rapl:[0-9]*/energy_uj`.
Energy is read for the whole CPU package, so measure on an otherwise idle machine.

## Installation

Download and unzip the release:

```bash
curl -L -o dr-greens.zip https://github.com/SMART-Dal/Energy-Smell-Detection-with-Agents-Skills/releases/latest/download/dr-greens.zip
unzip dr-greens.zip -d ~          # creates ~/dr-greens
```

```
~/dr-greens/
├── skills/                   the three skills: core, core+tax, full
├── start_inputs.sh           starts the input generator
├── apply.sh                  writes the chosen repairs into your code
├── requirements-skill.txt    packages the skill needs in your venv
├── tools/, src/              code used by the two scripts
└── README.md
```

## Usage

The examples analyse a project at `~/my-project` with the `full` skill.

### 1. Add a skill to your project

Claude Code loads skills from `.claude/skills/` in your project:

```bash
mkdir -p ~/my-project/.claude/skills
cp -r ~/dr-greens/skills/full/energy-smells ~/my-project/.claude/skills/
```

Install one skill at a time. The other two are `skills/core+tax/energy-smells`
and `skills/core/energy-efficiency` ([which to choose](#the-three-skills)).

### 2. Prepare your project's environment

The skill runs and measures your code in your project's venv. Activate it and
add the skill's packages (CodeGreen, Ruff, NumPy, pandas, SciPy, Requests, PyYAML):

```bash
source ~/my-project/.venv/bin/activate
pip install -r ~/dr-greens/requirements-skill.txt
```

If your project has no venv yet, create one and install its dependencies first:

```bash
python3 -m venv ~/my-project/.venv
source ~/my-project/.venv/bin/activate
pip install -r ~/my-project/requirements.txt         # or: pip install -e ~/my-project
```

If your project does not declare its dependencies, install the packages its
code imports.

### 3. Start the input generator

Save your OpenRouter key in a file that holds only the key, on one line:

```bash
nano ~/openrouter-key          # paste the key (sk-or-...), save with Ctrl-O, exit with Ctrl-X
chmod 600 ~/openrouter-key
```

Then, in a terminal with your project's venv activated, start the generator
and leave it running while you use the skill:

```bash
~/dr-greens/start_inputs.sh ~/my-project ~/openrouter-key
```

### 4. Ask Claude Code

In a second terminal, activate the same venv, point Claude Code at the
generator, and start it in your project:

```bash
source ~/my-project/.venv/bin/activate
export ENERGY_INPUTS_SOCKET=~/.energy-skill/my-project/inputs.sock    # printed by start_inputs.sh
cd ~/my-project
claude
```

Then ask, for example:

```
Find the energy smells in this repository using the energy-smells skill.
Find the energy smells in src/parser.py using the energy-smells skill.
Find the energy smells in src/parser.py::Parser.tokenize using the energy-smells skill.
```

With the `core` skill, ask: `Find where this repository wastes energy, using the
energy-efficiency skill.` Any Claude model works; choose it with `/model`.

### 5. Read the results

The agent writes four files in your project's root: `step1.jsonl` (what it
suspected), `step2.jsonl` (what it accepted or rejected, and why),
`step3.jsonl` (what became of each accepted suspicion), and `submissions.jsonl`
(one repair per line: the new source of the function, and its verdict in
`agent_measurement.status`).

| Verdict | Meaning |
|---|---|
| `confirmed` | saves energy on every input |
| `partial` | saves energy on some inputs, no measurable change on the others |
| `mixed` | saves on some inputs, costs more on others |
| `regressed` | costs more on every input that changed |
| `negligible` | no change beyond the measurement noise |
| `inconclusive` | the machine was too noisy to resolve the effect |

Repairs that could not be measured are `not_equivalent` (behaviour differs),
`no_inputs` (no inputs could be generated, for example because the code needs
the network), `invalid`, `error` or `over_limit`. A session measures at most 20
repairs; other accepted suspicions are recorded as `deferred` in `step3.jsonl`.

### 6. Apply the repairs

`apply.sh` writes, for each function, the `confirmed` repair with the largest
energy saving into your code, replacing only that function. Run it with your
project's venv activated:

```bash
~/dr-greens/apply.sh ~/my-project                                  # every confirmed repair
~/dr-greens/apply.sh ~/my-project --only C3S2-sort-once src/io.py::load   # only these repairs or functions
~/dr-greens/apply.sh ~/my-project --remeasure                      # measure every repair again first
~/dr-greens/apply.sh ~/my-project --dry-run                        # report only, change no code
```

| Option | Effect |
|---|---|
| (none) | uses the measurements the agent recorded |
| `--only ID ...` | considers only these repairs (their `id` in `submissions.jsonl`) or functions (`path::qualname`) |
| `--remeasure` | measures every considered repair again on a fresh copy of your project first (about a minute each) |
| `--dry-run` | writes the report without changing any code |

The options can be combined. Each run writes `REPORT.md` and `results.jsonl`
to your project's root, listing every repair, its verdict, and whether it was
applied or why not. Only `confirmed` repairs are applied, at most one per
function. Review the change with `git diff` and run your tests.

To start a new session in the same project, remove the previous session's files:

```bash
cd ~/my-project
chmod -R u+w .energy-inputs; rm -rf step?.jsonl submissions.jsonl results.jsonl REPORT.md .energy-inputs .energy-scan
```

## The three skills

Each skill adds a layer of knowledge to the one before it. All three follow the
same four steps and use the same verifier, energy probe and input generator.

| Skill | Folder | Adds |
|---|---|---|
| `core` | `skills/core/energy-efficiency` | the procedure, the energy probe, the input generator and the verifier |
| `core+tax` | `skills/core+tax/energy-smells` | a taxonomy of 12 energy smells and 65 root causes: an index, 12 category cards, and 65 root-cause cards with measured repair examples and near-misses |
| `full` | `skills/full/energy-smells` | a static analyzer: 40 rules of our own and 31 Ruff rules, each mapped to root causes |

```
energy-smells/
├── SKILL.md               the procedure the agent follows
├── reference/             taxonomy index, category and root-cause cards, verification guide, output format
└── scripts/
    ├── step.py            marks a step as finished
    ├── scan.py            static rules (full only)
    ├── inputs.py          requests inputs from the input generator
    ├── verify.py          checks behaviour and measures the energy of each repair
    ├── energy.py          measures the energy of any call, at any step
    └── lib/               shared code
```

## Reproducing the evaluation

The evaluation ran each skill with Claude Sonnet 5.5 and Claude Haiku 5.5, at
high reasoning effort, on three open-source repositories: 18 sessions. Every
recorded session is in [`results/`](results/README.md). Reproducing it needs
this whole repository, an Anthropic API key, and about 25 GB of free disk space.

| Repository | Commit | Domain |
|---|---|---|
| `vespa-engine/sample-apps` | `e2ed22d` | search application samples |
| `dnanexus/dx-toolkit` | `accd86a` | genomics cloud toolkit |
| `open-telemetry/community` | `910f85d` | project automation scripts |

**1. Clone the repository.**

```bash
git clone https://github.com/SMART-Dal/Energy-Smell-Detection-with-Agents-Skills.git ~/dr-greens-repo
cd ~/dr-greens-repo
```

**2. Save the keys.** Two files in `~/energy-exp`, each holding only the key,
on one line: an Anthropic API key ([console.anthropic.com](https://console.anthropic.com),
`sk-ant-...`) and an OpenRouter key (`sk-or-...`).

```bash
mkdir -p ~/energy-exp && chmod 700 ~/energy-exp
nano ~/energy-exp/api-key            # paste the Anthropic key, save, exit
nano ~/energy-exp/openrouter-key     # paste the OpenRouter key, save, exit
chmod 600 ~/energy-exp/api-key ~/energy-exp/openrouter-key
```

The agent never sees the keys: `~/energy-exp` is locked while a session runs.

**3. Set up.** Clones each repository at its commit and builds one venv per repository:

```bash
./setup.sh                      # or only one repository's venv: ./setup.sh community
```

**4. Run.**

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

Sessions run one at a time on the same machine. Each lasts up to 2 hours,
followed by up to 40 minutes in which every repair is measured again. Finished
sessions are skipped, so running the same command again resumes. To keep a run
alive after you log out: `tmux new -d -s exp ./run.sh`.

**5. Results.** Each session is saved in
`~/energy-exp/archive/<repo>/<skill>/<model>/`, with one row per session in
`~/energy-exp/archive/summary.csv`, in the same layout as
[`results/`](results/README.md). Agents are not deterministic, so a new session
finds and repairs different code than the recorded one, and energy readings
depend on the hardware. The harness is described in
[`experiment/README.md`](experiment/README.md).

## Repository layout

```
.
├── dist/                  the three skills (skills/ in the release), generated by build/
├── src/                   the skills' scripts: verifier, static analyzer, energy meter
├── taxonomy/              the energy smell taxonomy (12 smells, 65 root causes)
├── catalog/               per root cause: patterns, measured repairs, near-misses
├── build/                 renders the taxonomy, catalog and templates into dist/
├── tools/
│   ├── inputs/            the input generator and its service
│   ├── review.py          chooses, re-measures and applies repairs (used by apply.sh)
│   └── make_bundle.sh     builds the release archive dr-greens.zip
├── experiment/            the evaluation harness (run_all.sh, config.sh, repos.tsv)
├── results/               every recorded session of the evaluation
├── validation/            measured repair cases behind the cards, near-miss specimens
├── tests/rules/           tests of every static rule
├── data/manual_sampling/  hand-written before/after sample pairs
├── start_inputs.sh        starts the input generator
├── apply.sh               applies repairs to a project
├── setup.sh, run.sh       reproduce the evaluation
├── requirements.txt       packages of the harness and the build
└── requirements-skill.txt packages the skill needs in a project's venv
```

To rebuild the skills from their sources:
`pip install -r requirements.txt && python -m build`.

## Citation

Mohammadjavad Mehditabar, Saurabhsingh Rajput, and Tushar Sharma.
*Ctrl+Shift+Left: Detecting and Refactoring Energy Smells using Agent Skills.*
