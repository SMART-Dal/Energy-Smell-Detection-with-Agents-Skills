#!/usr/bin/env bash
# One-off runner for the batches left after the 2026-08-19 session.
#
# Runs strictly one measurement at a time: two concurrent measurements share
# the package energy counter and corrupt each other's readings, which is the
# whole reason this is a sequential script and not two background jobs.
#
#   tmux new-session -d -s energy validation/run_remaining.sh
#   tmux attach -t energy          # watch it
#   tail -f validation/results/samples.log
#
# Both suites are resumable: a case already in results/<suite>.jsonl is
# skipped, so this can be interrupted and restarted at no cost.
set -u
cd /home/javad/energy_smell_detection

echo "=== resumed $(date -Is) ===" >> validation/results/samples.log
.venv/bin/python -u validation/run.py samples  >> validation/results/samples.log  2>&1

echo "=== resumed $(date -Is) ===" >> validation/results/taxonomy.log
.venv/bin/python -u validation/run.py taxonomy >> validation/results/taxonomy.log 2>&1

echo "=== ALL BATCHES FINISHED $(date -Is) ===" | tee -a validation/results/samples.log \
                                                       >> validation/results/taxonomy.log
sleep infinity   # keep the tmux window alive so the summary stays readable
