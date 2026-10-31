# Analysis for the paper's Results

Every number in the Results comes from a script in this folder, and each
script writes its numbers to a file under `output/`. A number in the paper
can always be traced to one line of one output file.

The scripts read the copied runs in `../results/`, and only our own
measurements (`review/results.jsonl`), never the agent's. The repairs listed in
`excluded_repairs.csv` stay measured but are never confirmed: `common.review_results()`
gives them the status `excluded` (none of the five verdicts) and no saving, and every
script reads our review through it. Two scripts also
read the untouched repositories in `~/energy-exp/pristine/`, the copies every
run started from: `experiment/lib/repo_stats.py` (repository sizes) and
`rq1_repairs.py` (the original code of each repaired function). Everything is
plain Python except the figure, which needs matplotlib.

## How to run

```bash
bash analysis/run_results.sh  # from the project root: everything below, in order
```

It runs `experiment/lib/repo_stats.py`, the RQ1 scripts (`rq1_step1.py` to
`rq1_figure.py`), the RQ2 scripts (`rq2_root_causes.py`, `rq2_repair_dossiers.py`,
`rq2_strategies.py`, `rq2_agreement.py`, `rq2_examples.py`, `rq2_figure.py`,
`rq2_latex.py`), and finally `render_text.py`.

## The texts: one template, two outputs

Each RQ's text is written once, in `temp_main_paper/results/rq<N>_template.tex`,
where every number is a LaTeX command (such as `\rqOneSavingPct` or
`\rqTwoInstances`) and `\src{...}` marks the end of one or two sentences.
`render_text.py` writes two files from each:

- `rq<N>.tex`, the paper's text, with the numbers typed in and the tables pasted in;
- `rq<N>_annotated.tex`, the same text with a blue note after every `\src{...}`
  that gives, for each number since the previous note, its value, what it is,
  the file and line it was read from, and the script and function that wrote
  that file.

Edit the template, not `rq<N>.tex`: the next run would overwrite it. To keep hand
edits from being lost, `render_text.py` stops if `rq<N>.tex` changed since it last
wrote it.

## How to check a number in the paper

1. Find the number in `rq<N>_annotated.tex`, or its command in
   `output/rq1/latex/numbers.md` or `output/rq2/latex/numbers.md`. Both give the value, the file it was read
   from, the line in that file, and the script that wrote the file.
2. Open that file at that line. The script's comments explain how the value
   was computed.

Every table cell is listed at the end of `numbers.md` the same way.
`rq1_latex.py` only looks numbers up and computes nothing, so a wrong number
can only come from the script that wrote its file. The tables, `numbers.tex`,
`numbers.json`, `numbers.md` and the figure are also copied to
`temp_main_paper/results/generated/`, which is where the paper reads them.

## Files

| File | What it does |
|---|---|
| `common.py` | Where the files are, the 18 runs, reading and writing files, our review (see `excluded_repairs.csv`). Computes nothing. |
| `excluded_repairs.csv` | Repairs counted as measured but never confirmed (status `excluded`, no saving), each with the reason. |
| `compare.py` | Compares models, skills and repositories with the other factors held fixed. |
| `bootstrap.py` | Confidence intervals by resampling the 18 runs (seed 7, 10,000 resamples). |
| `rq1_step1.py` | Step 1, *find*: units and suspicions listed, overlap with the static rules and between runs. |
| `rq1_step2.py` | Step 2, *decide*: accepted smells, smelly units, share of the repository, categories. |
| `rq1_step3.py` | Step 3, *repair and measure*: confirmed repairs and their savings, inputs, per run and overall. |
| `rq1_together.py` | The six runs on a repository together: how far the runs complement each other. |
| `rq1_categories.py` | Per category and root cause: smells, repairs, confirmed repairs, and why smells were not repaired. |
| `rq1_repairs.py` | Each measured repair: lines changed, what it does to the loops, rule flag; identical edits merged; the intervals. |
| `rq1_unguided_savings.py` | Why Unguided's Sonnet runs have the highest median saving: same units, same savings; other units. |
| `rq1_cost.py` | Cost, tokens, time, tool calls and subagents, from Claude Code's own accounting. |
| `rq1_latex.py` | Looks up every number and writes `numbers.tex`, `numbers.json`, the five tables and the ledger `numbers.md`. |
| `rq1_figure.py` | The RQ1 figure: the saving of every confirmed repair. |
| `rq2_root_causes.py` | RQ2: instances (root cause, unit), per root cause and per category. |
| `rq2_repair_dossiers.py` | RQ2: every edit of each frequent root cause written out as a diff, to read. |
| `rq2_strategy_coding.csv` | RQ2: the repair strategy of every edit, named by hand after reading the dossiers. |
| `rq2_strategies.py` | RQ2: the hand-coded strategies, counted per root cause and overall. |
| `rq2_agreement.py` | RQ2: how far two runs agree on smelly units and on their root causes. |
| `rq2_examples.py` | RQ2: the table of example repairs, each code line checked against its diff. |
| `rq2_figure.py` | RQ2 figure: each frequent root cause by median saving and share confirmed. |
| `rq2_latex.py` | RQ2 numbers, tables and ledger, like `rq1_latex.py`. |
| `render_text.py` | Writes `rq1.tex`, `rq2.tex` and their annotated copies from the templates. |
| `run_results.sh` | Runs all of the above in order. |
| `output/repo_stats.tsv` | Repository sizes (from `experiment/lib/repo_stats.py`). |
| `output/rq1/*` | Every table and count the RQ1 text uses; each script's docstring lists its files. |

## Definitions used everywhere

- **Run**: one repository x one skill x one model; 18 in all.
- **Unit**: a function or method, as in the methodology. A function defined
  inside another function is not a unit (`experiment/lib/repo_stats.py`).
- **Skill names**: `full` = Taxonomy+Rules, `knowledge` = Taxonomy, `control` = Unguided.
- **Smell**: a suspicion accepted in step 2. **Smelly unit**: a unit with at least one smell.
- **Confirmed**: our verdict is `confirmed` or `partial` (`SAVES` in `common.py`). A
  partial repair saves beyond its confidence interval on some inputs and costs
  more on none, so it is counted with the confirmed ones.
- **Measured**: our verdict is one of confirmed, partial, mixed, regressed, negligible, or the
  repair is in `excluded_repairs.csv` (status `excluded`: measured, never confirmed, no saving).
- **Saving**: `mean_saving_pct` in `review/results.jsonl`, the mean over the four inputs.
- **Test file**: as in `experiment/lib/repo_stats.py` (under `test/` or `tests/`,
  or named `test_*.py` / `*_test.py`).
- **Lines changed**: lines removed plus lines added between the original function
  and the repaired one, after Python's `ast.unparse` has removed comments,
  blank lines and formatting (`rq1_repairs.py`).
- **Change to the loops**: from Python's parse of both versions, the first that
  fits of: changes the loops (number or deepest nesting), fewer calls inside
  loops, fewer calls outside loops, same loops and calls (`rq1_repairs.py`).
- **Rule-flagged unit**: a unit some static rule flags in `rules.json`, which the
  rules wrote on the untouched repository after the run, in every skill.
- **Distinct edit**: repairs of the same unit whose code is identical (all whitespace
  removed) are one edit, even when several runs wrote it (`rq1_repairs.py`).
- **Instance** (RQ2): one root cause in one unit. It counts once however many runs found
  or repaired it; it is confirmed when at least one of its repairs was (`rq2_root_causes.py`).
- **What counts once**: RQ1 counts repairs per run (headline, runs table, configuration and
  model rows) or distinct edits (the other rows of the repairs table), and units as distinct
  (repository, unit); RQ2 counts instances, and in the strategies (instance, strategy) pairs.
- **Intervals**: 95% from resampling the 18 runs; the three comparisons between
  groups of repairs are Bonferroni-adjusted to 98.3% (`bootstrap.py`, `rq1_repairs.py`).
