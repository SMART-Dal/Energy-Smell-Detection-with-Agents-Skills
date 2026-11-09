#!/usr/bin/env bash
# Run the evaluation, one session at a time, at high reasoning effort.
#
#   ./run.sh                                                  all 18 sessions
#   ./run.sh --repos community --skills full --models haiku   one session
#   ./run.sh --check                                          check that Claude Code starts
#   ./run.sh --dry-run --repos community                      the whole pipeline without Claude
#
#   --repos    names from experiment/repos.tsv (default: all)
#   --skills   core, core+tax, full (default: all three)
#   --models   sonnet, haiku, opus (default: sonnet haiku)
#   --again    run a finished session again
#
# Finished sessions are skipped. Results: ~/energy-exp/archive/
set -uo pipefail
cd "$(dirname "$0")"

skills="core core+tax full"
models="sonnet haiku"
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --skills) skills=$2; shift 2 ;;
    --models) models=$2; shift 2 ;;
    *)        args+=("$1"); shift ;;
  esac
done
models=$(echo "$models" | sed -E 's/\b(sonnet|haiku|opus)\b/claude-\1-5-5/g')

experiment/run_all.sh --arms "$skills" --models "$models" --effort high "${args[@]}"
