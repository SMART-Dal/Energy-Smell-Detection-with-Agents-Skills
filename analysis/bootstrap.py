"""Confidence intervals by resampling whole runs (a cluster bootstrap).

The repairs of one run are not independent of each other: they share the
model, the skill, the repository and the session. So we never resample single
repairs. We resample the 18 RUNS with replacement, pool the repairs of the runs
drawn, and compute the statistic on that pool. Doing this many times gives the
spread of the statistic; the middle 95% of that spread is the interval.

Every interval uses the same seed, so the numbers come out the same on every run
of the script.
"""

import random

SEED = 7              # fixed, so every interval can be reproduced exactly
RESAMPLES = 10000     # how many times the runs are drawn again


def percentile(ordered, fraction):
    """The value at `fraction` (0 to 1) of a sorted list, by the nearest-rank rule."""
    index = int(round(fraction * (len(ordered) - 1)))   # position in the sorted list
    return ordered[index]


def run_bootstrap(rows_by_run, statistic, level=95.0):
    """The statistic on all rows, and its interval from resampling runs.

    rows_by_run   {run: [rows of that run]}, e.g. {("dx-toolkit", "full", "haiku"): [...]}
    statistic     a function that takes a list of rows and returns one number,
                  or None when the rows are not enough to compute it
    level         the width of the interval in percent (95 means the middle 95%)

    Returns (value on all rows, lower end, upper end).
    """
    runs = list(rows_by_run.keys())                     # the 18 runs
    everything = []                                     # all rows of all runs
    for run in runs:
        everything.extend(rows_by_run[run])
    value = statistic(everything)                       # the statistic we report

    generator = random.Random(SEED)                     # our own generator, seeded
    results = []                                        # the statistic in each resample
    for _ in range(RESAMPLES):
        pool = []                                       # the rows of this resample
        for _ in runs:                                  # draw as many runs as there are
            drawn = generator.choice(runs)              # one run, with replacement
            pool.extend(rows_by_run[drawn])
        result = statistic(pool)
        if result is not None:                          # skip draws where it cannot be computed
            results.append(result)

    results.sort()
    tail = (100.0 - level) / 200.0                      # e.g. 95% leaves 2.5% on each side
    return value, percentile(results, tail), percentile(results, 1.0 - tail)
