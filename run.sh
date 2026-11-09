#!/usr/bin/env bash
# Run the experiment: every repository x skill x model, one session at a time.
#
#   ./run.sh                                              the whole experiment (18 sessions)
#   ./run.sh --repos community --skills core --models haiku   one session
#   ./run.sh --check                                      Claude Code can start (one short call)
#   ./run.sh --dry-run --repos community                  the whole pipeline without Claude
#
# Options:
#   --repos "a b"       repositories from experiment/repos.tsv (default: all)
#   --skills "a b"      core, core+tax, full (default: all three)
#   --models "a b"      sonnet, haiku, opus or a full model ID (default: sonnet haiku)
#   --effort LEVEL      reasoning effort of every model (default: high)
#   --again             run a finished session again; the earlier one is kept
#
# Finished sessions are skipped, so running the same command again resumes.
# Each session lasts up to 2 hours plus up to 40 minutes of re-measurement.
# Results: ~/energy-exp/archive/<repo>/<skill>/<model>/ and ~/energy-exp/archive/summary.csv
set -uo pipefail
cd "$(dirname "$0")" || exit 1

skills="core core+tax full"
models="sonnet haiku"
effort=high
rest=()
while [ $# -gt 0 ]; do
  case "$1" in
    --skills) skills=$2; shift 2 ;;
    --models) models=$2; shift 2 ;;
    --effort) effort=$2; shift 2 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) rest+=("$1"); shift ;;
  esac
done

ids=()
for m in $models; do
  case "$m" in
    sonnet) ids+=(claude-sonnet-5-5) ;;
    haiku)  ids+=(claude-haiku-5-5) ;;
    opus)   ids+=(claude-opus-5-5) ;;
    *)      ids+=("$m") ;;
  esac
done

exec experiment/run_all.sh --arms "$skills" --models "${ids[*]}" --effort "$effort" "${rest[@]}"
