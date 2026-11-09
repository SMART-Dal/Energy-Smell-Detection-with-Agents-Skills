#!/usr/bin/env bash
# Write the agent's repairs into your repository: for each function, the
# confirmed repair with the largest energy saving.
#
#   ./apply.sh REPO                       use the measurements the agent recorded
#   ./apply.sh REPO --remeasure           measure every repair again first (about a minute each)
#   ./apply.sh REPO --only ID [ID ...]    only these repairs: ids from submissions.jsonl, or path::qualname
#   ./apply.sh REPO --dry-run             report what would be applied, change no code
#
# Options can be combined. Run it with the repository's venv activated.
# REPORT.md and results.jsonl are written to the repository's root.
set -euo pipefail

tool=$(cd "$(dirname "$0")" && pwd)
repo=$1
shift

trust=--trust-agent
apply=--apply
rest=()
for arg in "$@"; do
  case "$arg" in
    --remeasure) trust= ;;
    --dry-run)   apply= ;;
    *)           rest+=("$arg") ;;
  esac
done

python "$tool/tools/review.py" "$repo" $trust $apply "${rest[@]}"
