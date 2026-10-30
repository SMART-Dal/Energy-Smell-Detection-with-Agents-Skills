#!/usr/bin/env bash
# Rebuilds every RQ1 number, table and figure, in order. Run from the project root:
#   bash analysis/run_rq1.sh
set -e                                             # stop at the first error
python3 experiment/lib/repo_stats.py sample-apps dx-toolkit community > analysis/output/repo_stats.tsv
cd analysis
python3 rq1_step1.py                               # Step 1 numbers
python3 rq1_step2.py                               # Step 2 numbers
python3 rq1_step3.py                               # Step 3 numbers
python3 rq1_together.py                            # the six runs on a repository together
python3 rq1_categories.py                          # from smells to confirmed repairs, per category
python3 rq1_repairs.py                             # size and kind of each repair, rule flags, intervals
python3 rq1_cost.py                                # cost, tokens, time, tool calls, subagents
python3 rq1_latex.py                               # LaTeX numbers, the five tables, and the ledger numbers.md
python3 rq1_figure.py                              # the figure
python3 rq1_render.py                              # rq1.tex (plain numbers) and rq1_annotated.tex
