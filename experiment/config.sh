# Settings for run_all.sh, setup_repos.sh and setup_venvs.sh. Edit here, not in the scripts.

HARNESS=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)   # this folder: scripts, settings, repos.tsv
PROJECT=$(dirname "$HARNESS")                            # the repository: skills, tools, measurement
EXP=${ENERGY_EXP:-$HOME/energy-exp}   # ours: keys, clones, venvs, inputs cache, results. Locked during agent runs.
RUN=${ENERGY_RUN:-$HOME/energy-run}   # the current run only: repo copy, venv, Claude config. Wiped per run.

MODELS=(claude-opus-5-5 claude-sonnet-5-5 claude-haiku-5-5)
ARMS=(core core+tax full)
EFFORT=medium                   # the default of Opus 5.5 and Haiku 5.5 (Sonnet 5.5's is high), and the
                                # level Anthropic suggests starting agentic tool use at
# A model listed here runs at its own level instead. Sonnet at medium stopped
# after 2-3 units in every run, so it runs at high, its default.
declare -A EFFORT_OF=([claude-sonnet-5-5]=high)

# How Claude is paid for: `api` reads the Console key in $EXP/api-key (billed per
# token); `subscription` uses a claude.ai Pro/Max plan through the one-year
# token `claude setup-token` prints, saved in $EXP/oauth-token (counts against
# the plan's 5-hour and weekly limits). Tokens and turns are reported the same
# way either way; total_cost_usd is then a list-price estimate, not a bill.
AUTH=api

AGENT_TIMEOUT=120m              # the agent's whole session, its own measurements included.
                                # SKILL.md tells the agent "120 minutes" (build/templates/shared/SKILL.md): change both.
REVIEW_TIMEOUT=40m              # our re-measurement of submissions.jsonl afterwards: 20 repairs
                                # took 18 min, and noisy ones are now measured twice

# No dollar cap is given to the agent: `claude --max-budget-usd` shows it to the
# model on every turn ("USD budget: $0/$10; $10 remaining"), and Sonnet stopped
# after three units "working to a tight spending budget". Spending is
# capped on the Console instead, and the cost of every run is in summary.csv.

# Free space a run must find before it starts. Its peak is about 13 GB on the
# home disk (sample-apps: a 7 GB venv, the repo, the measurement's and the input
# generator's copies of it); $RUN is deleted after every run.
MIN_FREE_GB=25
MIN_TMP_GB=2

# Every venv gets these on top of our own requirements and the repo's own.
COMMON_PACKAGES="numpy pandas scipy requests pyyaml"

# Where each arm's skill comes from.
declare -A SKILL=([core]=dist/core/energy-efficiency [core+tax]=dist/core+tax/energy-smells [full]=dist/full/energy-smells)

# The same prompt for every run of an arm.
UNATTENDED="You are running unattended: nobody can answer questions, so make your own decisions and finish the task."
declare -A PROMPT=(
  [core]="Find where this repository wastes energy, using the energy-efficiency skill. $UNATTENDED"
  [core+tax]="Find the energy smells in this repository using the energy-smells skill. $UNATTENDED"
  [full]="Find the energy smells in this repository using the energy-smells skill. $UNATTENDED"
)
