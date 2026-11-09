#!/usr/bin/env bash
# Prepare this machine to reproduce the evaluation: clone each repository at the
# commit the evaluation used, and build its venv.
#
#   ./setup.sh                 all repositories in experiment/repos.tsv
#   ./setup.sh community       build the venv of these repositories only
#
# Save your two keys first, one per file: ~/energy-exp/api-key (Anthropic) and
# ~/energy-exp/openrouter-key (OpenRouter).
set -uo pipefail
cd "$(dirname "$0")"
source experiment/config.sh

for key in api-key openrouter-key; do
  [ -s "$EXP/$key" ] || { echo "Missing $EXP/$key: save your key there first (see README.md)."; exit 1; }
done

experiment/setup_repos.sh          # clone each repository at its commit
experiment/setup_venvs.sh "$@"     # one venv per repository
