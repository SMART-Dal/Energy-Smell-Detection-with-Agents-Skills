#!/usr/bin/env bash
# Rebuilds every RQ1 number, table and figure, in order. Run from the project root:
#   bash analysis/run_rq1.sh
set -e                                             # stop at the first error
python3 experiment/lib/repo_stats.py sample-apps dx-toolkit community > analysis/output/repo_stats.tsv
cd analysis
python3 rq1_step1.py                               # Step 1 numbers
python3 rq1_step2.py                               # Step 2 numbers
python3 rq1_step3.py                               # Step 3 numbers
python3 rq1_latex.py                               # LaTeX commands, table, and the ledger numbers.md
python3 rq1_figure.py                              # the figure
