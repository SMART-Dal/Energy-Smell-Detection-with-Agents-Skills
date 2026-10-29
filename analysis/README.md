# Analysis for the paper's Results

Every number in the Results comes from a script in this folder, and each
script writes its numbers to a file under `output/`. A number in the paper
can always be traced to one line of one output file.

The scripts only read the copied runs in `../results/`, and only our own
measurements (`review/results.jsonl`), never the agent's. They use plain
Python, with no libraries to install.

## How to run

```bash
bash analysis/run_rq1.sh      # from the project root: everything below, in order
```

It runs, in this order: `experiment/lib/repo_stats.py` (repository sizes),
`rq1_step1.py`, `rq1_step2.py`, `rq1_step3.py`, `rq1_latex.py`, `rq1_figure.py`.

## How to check a number in the paper

The RQ1 text (`temp_main_paper/results/rq1.tex`) contains no typed numbers. It
uses LaTeX commands such as `\rqOneSavingRepairs`, defined in
`output/rq1/latex/numbers.tex`. To check one:

1. Find the command in `output/rq1/latex/numbers.md`. It gives the value, the
   file it was read from, the line in that file, and what it means.
2. Open that file at that line. The step script that wrote the file explains,
   in its comments, how the value was computed.

The table (`table_runs.tex`) works the same way. Every cell is listed at the end
of `numbers.md` with its file and line. `rq1_latex.py` only looks numbers up and
computes nothing, so a wrong number can only come from a step script. The two
`.tex` files and the figure are also copied to `temp_main_paper/results/generated/`,
which is where the paper reads them.

## Files

| File | What it does |
|---|---|
| `common.py` | Where the files are, the 18 runs, reading and writing files. Computes nothing. |
| `compare.py` | The three comparisons: models (9 cells), skills (6 cells), repositories (6 cells). |
| `rq1_step1.py` | Step 1, *find*: units and suspicions listed, overlap with the static rules and between runs. |
| `rq1_step2.py` | Step 2, *decide*: accepted smells, smelly units, share of the repository, categories. |
| `rq1_step3.py` | Step 3, *repair and measure*: repairs that save energy and how much, per run and overall. |
| `rq1_latex.py` | Looks up every number the RQ1 text uses and writes `numbers.tex`, `table_runs.tex` and the ledger `numbers.md`. |
| `rq1_figure.py` | The RQ1 figure: the saving of every repair that saves energy. |
| `run_rq1.sh` | Runs all of the above in order. |
| `output/repo_stats.tsv` | Repository sizes (from `experiment/lib/repo_stats.py`). |
| `output/rq1/*` | Every table and count the RQ1 text uses; each script's docstring lists its files. |

## Definitions used everywhere

- **Run**: one repository x one skill x one model; 18 in all.
- **Unit**: a function or method, as in the methodology. A function defined
  inside another function is not a unit (`experiment/lib/repo_stats.py`).
- **Skill names**: `full` = Taxonomy+Rules, `knowledge` = Taxonomy, `control` = Unguided.
- **Smell**: a suspicion accepted in step 2. **Smelly unit**: a unit with at least one smell.
- **Saves energy**: our verdict is `confirmed` or `partial`. A partial repair saves
  beyond its confidence interval on some inputs and costs more on none, so it is
  counted with the confirmed ones.
- **Measured**: our verdict is one of confirmed, partial, mixed, regressed, negligible.
- **Saving**: `mean_saving_pct` in `review/results.jsonl`, the mean over the four inputs.
- **Test file**: as in `experiment/lib/repo_stats.py` (under `test/` or `tests/`,
  or named `test_*.py` / `*_test.py`).
