#!/usr/bin/env bash
# Run the taxonomy validation suite in tmux.
#
#   bash validation/run_next.sh
#
# Two rules, both learned the hard way and both non-negotiable:
#
#   1. ONE MEASUREMENT AT A TIME. Every process on this host reads the same
#      package energy counter. Two runs at once do not halve each other's
#      accuracy, they corrupt both, and nothing in the output says so. This
#      script refuses to start if it finds one already running.
#
#   2. DO NOT EDIT src/ WHILE THIS IS LIVE. Each case runs in a fresh
#      subprocess that re-imports the verifier, so a half-finished edit is
#      picked up mid-batch. Thirty-two rows were once written by a verifier
#      that had `sys.modules` but not `import sys`.
#
# The batch is resumable: a case file already in results/taxonomy.jsonl is
# skipped, so an interrupted run costs only the case it was on. Re-running
# this script after an interruption picks up where it stopped.
set -euo pipefail
cd "$(dirname "$0")/.."

if pgrep -af "validation/run\.py|src/verify\.py" > /dev/null; then
  echo "a measurement is already running; refusing to start a second one:"
  pgrep -af "validation/run\.py|src/verify\.py"
  exit 1
fi

if tmux has-session -t measure 2>/dev/null; then
  echo "tmux session 'measure' already exists. Attach with: tmux attach -t measure"
  exit 1
fi

tmux new-session -d -s measure "bash validation/_taxonomy_batch.sh"

echo "started in tmux session 'measure'."
echo "  follow it:  tmux attach -t measure        (detach again with ctrl-b d)"
echo "  or the log: tail -f validation/results/taxonomy.log"
echo "  progress:   wc -l validation/results/taxonomy.jsonl"
echo
echo "It survives a closed terminal. Preflight runs first; the suite only"
echo "starts if it passes. Several minutes per case file: each case pays a 10s"
echo "machine warmup and 9 paired reps over 3s windows, and the canary repeats"
echo "all of that once more for the deciding case."
