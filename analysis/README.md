# Analysis for the paper's Results

Every number in the Results comes from a script in this folder, and each
script writes its numbers to a file under `output/`. A number in the paper
can always be traced to one line of one output file.

The scripts read the copied runs in `../results/`, and only our own
measurements (`review/results.jsonl`), never the agent's. Two scripts also
read the untouched repositories in `~/energy-exp/pristine/`, the copies every
run started from: `experiment/lib/repo_stats.py` (repository sizes) and
`rq1_repairs.py` (the original code of each repaired function). Everything is
plain Python except the figure, which needs matplotlib.

## How to run

```bash
bash analysis/run_rq1.sh      # from the project root: everything below, in order
```

It runs `experiment/lib/repo_stats.py`, then `rq1_step1.py`, `rq1_step2.py`,
`rq1_step3.py`, `rq1_together.py`, `rq1_categories.py`, `rq1_repairs.py`,
`rq1_cost.py`, `rq1_latex.py`, `rq1_figure.py` and `rq1_render.py`.

## The RQ1 text: one template, two outputs

The text is written once, in `temp_main_paper/results/rq1_template.tex`, where
every number is a LaTeX command (such as `\rqOneSavingPct`) and `\src{...}`
marks the end of one or two sentences. `rq1_render.py` writes two files from it:

- `rq1.tex`, the paper's text, with the numbers typed in and the tables pasted in;
- `rq1_annotated.tex`, the same text with a blue note after every `\src{...}`
  that gives, for each number since the previous note, its value, what it is,
  the file and line it was read from, and the script and function that wrote
  that file.

Edit the template, not `rq1.tex`: the next run would overwrite it. To keep hand
edits from being lost, `rq1_render.py` stops if `rq1.tex` changed since it last
wrote it.

## How to check a number in the paper

1. Find the number in `rq1_annotated.tex`, or its command in
   `output/rq1/latex/numbers.md`. Both give the value, the file it was read
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
| `common.py` | Where the files are, the 18 runs, reading and writing files. Computes nothing. |
| `compare.py` | Compares models, skills and repositories with the other factors held fixed. |
| `bootstrap.py` | Confidence intervals by resampling the 18 runs (seed 7, 10,000 resamples). |
| `rq1_step1.py` | Step 1, *find*: units and suspicions listed, overlap with the static rules and between runs. |
| `rq1_step2.py` | Step 2, *decide*: accepted smells, smelly units, share of the repository, categories. |
| `rq1_step3.py` | Step 3, *repair and measure*: confirmed repairs and their savings, inputs, per run and overall. |
| `rq1_together.py` | The six runs on a repository together: how far the runs complement each other. |
| `rq1_categories.py` | Per category and root cause: smells, repairs, confirmed repairs, and why smells were not repaired. |
| `rq1_repairs.py` | Each measured repair: lines changed, what it does to the loops, rule flag; the intervals. |
| `rq1_cost.py` | Cost, tokens, time, tool calls and subagents, from Claude Code's own accounting. |
| `rq1_latex.py` | Looks up every number and writes `numbers.tex`, `numbers.json`, the five tables and the ledger `numbers.md`. |
| `rq1_figure.py` | The RQ1 figure: the saving of every confirmed repair. |
| `rq1_render.py` | Writes `rq1.tex` and `rq1_annotated.tex` from the template. |
| `run_rq1.sh` | Runs all of the above in order. |
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
- **Measured**: our verdict is one of confirmed, partial, mixed, regressed, negligible.
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
- **Intervals**: 95% from resampling the 18 runs; the three comparisons between
  groups of repairs are Bonferroni-adjusted to 98.3% (`bootstrap.py`, `rq1_repairs.py`).
