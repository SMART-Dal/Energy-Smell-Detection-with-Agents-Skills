#!/usr/bin/env bash
# Rebuilds every RQ1 and RQ2 number, table and figure, and the texts, in order.
# Run from the project root:
#   bash analysis/run_results.sh
set -e                                             # stop at the first error
python3 experiment/lib/repo_stats.py sample-apps dx-toolkit community > analysis/output/repo_stats.tsv
cd analysis
# RQ1
python3 rq1_step1.py                               # Step 1 numbers
python3 rq1_step2.py                               # Step 2 numbers
python3 rq1_step3.py                               # Step 3 numbers
python3 rq1_together.py                            # the six runs on a repository together
python3 rq1_categories.py                          # per category and root cause, per run (reasons for deferring)
python3 rq1_repairs.py                             # size and kind of each repair, rule flags, intervals
python3 rq1_unguided_savings.py                    # why Unguided's Sonnet runs have the highest median
python3 rq1_cost.py                                # cost, tokens, time, tool calls, subagents
python3 rq1_latex.py                               # RQ1 numbers, tables, and the ledger numbers.md
python3 rq1_figure.py                              # the RQ1 figure
# RQ2
python3 rq2_root_causes.py                         # instances (root cause, unit), per root cause and category
python3 rq2_repair_dossiers.py                     # every edit of the frequent root causes, to read
python3 rq2_strategies.py                          # the hand-coded strategies, counted
python3 rq2_agreement.py                           # agreement between models and configurations
python3 rq2_examples.py                            # the table of example repairs
python3 rq2_figure.py                              # the RQ2 figure
python3 rq2_latex.py                               # RQ2 numbers, tables, and the ledger
# Texts
python3 render_text.py                             # rq1.tex, rq2.tex and their annotated copies
