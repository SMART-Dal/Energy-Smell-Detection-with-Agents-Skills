#!/usr/bin/env bash
# Prepare this machine to reproduce the experiment.
#
#   ./setup.sh                        all repositories in experiment/repos.tsv
#   ./setup.sh --repos community      only these repositories
#
# 1. Checks the requirements: Linux, Python 3.10, git, Claude Code, readable RAPL counters.
# 2. Checks the two key files in ~/energy-exp (an Anthropic API key and an OpenRouter key).
# 3. Clones each repository at the commit the experiment used.
# 4. Builds one venv per repository (the repository's dependencies, numpy, pandas,
#    scipy, requests, pyyaml and requirements.txt).
#
# Set ENERGY_EXP to use a folder other than ~/energy-exp, and PYTHON to build the
# venvs with an interpreter other than python3.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
source experiment/config.sh

repos=()
while [ $# -gt 0 ]; do
  case "$1" in
    --repos) read -r -a repos <<< "$2"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
done

ok=1
fail() { echo "  MISSING  $*"; ok=0; }
pass() { echo "  ok       $*"; }

echo "Requirements"
[ "$(uname -s)" = Linux ] && pass "Linux" || fail "Linux is required (energy is read from Intel RAPL counters)"
py=${PYTHON:-python3}
version=$("$py" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)
if [ "$version" = 3.10 ]; then pass "$py is Python $version"
elif [ -n "$version" ]; then echo "  WARNING  $py is Python $version; the experiment used 3.10 (set PYTHON=python3.10)"
else fail "$py not found"; fi
command -v git > /dev/null && pass "git" || fail "git"
command -v claude > /dev/null && pass "Claude Code $(claude --version 2>/dev/null | head -1)" \
  || fail "Claude Code (https://docs.claude.com/en/docs/claude-code)"
command -v tmux > /dev/null && pass "tmux" || echo "  optional tmux (to keep long runs alive after you log out)"
rapl=$(ls /sys/class/powercap/intel-rapl:*/energy_uj 2>/dev/null | grep -E 'intel-rapl:[0-9]+/energy_uj$' | head -1)
if [ -z "$rapl" ]; then fail "RAPL counters (/sys/class/powercap/intel-rapl:*): an Intel CPU is required"
elif [ -r "$rapl" ]; then pass "RAPL counters are readable"
else fail "read access to $rapl (for example: sudo chmod a+r /sys/class/powercap/intel-rapl:[0-9]*/energy_uj)"; fi

echo "Keys in $EXP"
mkdir -p "$EXP" && chmod 700 "$EXP"
for key in api-key openrouter-key; do
  if [ -s "$EXP/$key" ]; then pass "$EXP/$key"
  else fail "$EXP/$key: create it with your key on one line, readable only by you (chmod 600)"; fi
done
[ "$ok" = 1 ] || { echo; echo "Fix the items marked MISSING, then run ./setup.sh again."; exit 1; }

list=$REPOS_FILE
if [ ${#repos[@]} -gt 0 ]; then
  list=$(mktemp)
  for r in "${repos[@]}"; do
    grep -P "^$r\t" "$REPOS_FILE" >> "$list" || { echo "$r is not in $REPOS_FILE"; exit 2; }
  done
fi

echo; echo "Repositories"
ENERGY_REPOS=$list experiment/setup_repos.sh || exit 1
echo; echo "Venvs (a few minutes per repository)"
ENERGY_REPOS=$list experiment/setup_venvs.sh || exit 1

echo
echo "Done. Next:"
echo "  ./run.sh --check                                  Claude Code can start (one short call)"
echo "  ./run.sh --dry-run --repos community              the whole pipeline without Claude"
echo "  ./run.sh --repos community --skills core --models haiku   one real run"
