#!/usr/bin/env bash
# Drain the taxonomy suite repeatedly, picking up case files as they are added.
#
# The suite is being widened from one function per root cause to three, and the
# files are authored in batches. Each pass skips everything already recorded in
# results/taxonomy.jsonl, so re-running costs only the new files.
#
#   tmux new-session -d -s expand validation/run_expanding.sh
#   tail -f validation/results/taxonomy.log
#
# Stop it when authoring is finished and the log reports "0 to run" twice.
#
# Do NOT edit anything under src/ while this is running. Each case runs as a
# fresh subprocess that re-imports the verifier, so a half-finished edit is
# picked up immediately and every case in flight fails against it -- once, this
# turned thirty-two cases into `NameError` rows that had to be deleted and
# redone. Stop the loop, edit, restart.
set -u
cd /home/javad/energy_smell_detection
while true; do
  echo "=== pass $(date -Is) ===" >> validation/results/taxonomy.log
  .venv/bin/python -u validation/run.py taxonomy >> validation/results/taxonomy.log 2>&1
  sleep 45
done
