#!/usr/bin/env bash
# The next measurement pass: 69 case files of 226, not the whole suite.
#
#   bash validation/run_next.sh
#
# Two rules, both learned the hard way and both non-negotiable:
#
#   1. ONE MEASUREMENT AT A TIME. Every process on this host reads the same
#      package energy counter. Two runs at once do not halve each other's
#      accuracy, they corrupt both, and nothing in the output says so. Check
#      `pgrep -af verify.py` before starting and make sure the machine is not
#      being used for anything else heavy.
#
#   2. DO NOT EDIT src/ WHILE THIS IS LIVE. Each case runs in a fresh
#      subprocess that re-imports the verifier, so a half-finished edit is
#      picked up mid-batch. Thirty-two rows were once written by a verifier
#      that had `sys.modules` but not `import sys`.
#
# What runs: every case file with no stored row (35 new ones), plus 34 stored
# rows dropped by --redo because their case file changed or their reading was
# unusable -- a timeout, a failed equivalence check, or a noise floor above 3%.
# Everything else keeps the number it already has.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 validation/preflight.py || {
  echo "preflight failed: the host is too busy to resolve anything. Nothing run."
  exit 1
}

tmux new-session -d -s measure \
  "python3 validation/run.py taxonomy --prune --redo '$(cat validation/redo.txt)' \
     2>&1 | tee -a validation/results/taxonomy.log"

echo "started in tmux session 'measure'. Follow it with: tmux attach -t measure"
echo "It survives a closed laptop. Roughly one to two minutes per case file."
