# Validation results

## What this measures, and what it does not

**The taxonomy is the reference.** Its 65 root causes come from a literature
review, each names a real mechanism, and nothing here is evidence that one of
them is not a root cause. A repair that fails to pay, on this host, in the one
shape a case file happened to use, is not a refutation of anything — it is a
fact about that shape on that host.

What these suites are for is the *authored* half of each card: where a root
cause pays, how much, where it does not, and what an agent should expect before
it spends a measurement of its own. Every number below feeds `what_to_look_for`,
`NOT a smell when`, `Looks the same, is not` or the repair examples. None of it
feeds the description or the example, which are rendered verbatim from the
published taxonomy and are not ours to edit.

Where a repair did not pay anywhere we tried, the card says so and leaves the
judgement with the agent, because the shapes we tried are not all the shapes
there are.

---

## Status: no measurements

**Every number this file used to carry was measured on a different host and has
been discarded.** So have `validation/results/taxonomy.jsonl` and
`validation/results/samples.jsonl`. They are recoverable from git history at
`4ca956f` if a comparison is ever wanted, but they are not evidence about this
machine and nothing should be rewritten from them.

Discarded on 2026-09-08, when measurement moved to a second host.

The root-cause cards in `catalog/` still quote the previous host's figures.
Those are the output of this suite, not an input to it, so they stay as they
are until a batch on this host replaces them — at which point every card that
cites a percentage needs revisiting. Until then, treat a number in a card as
provisional and attributed to a host that is no longer measuring.

`build/impact.py` reads the results file to rank findings by measured saving.
With no results present it returns an empty mapping, so every root cause ranks
at zero impact until the first batch lands. That is the honest state, not a bug.

## The rig

What the measurement does, so a future run can be compared against this one:

| | |
|---|---|
| meter | CodeGreen 0.4.8, `TaskResult.energy_j` verbatim |
| domains | whole-machine CPU package + DRAM, **nothing subtracted** |
| machine warmup | 10 s of unrelated arithmetic on the pinned core |
| code warmup | 1 call of each variant |
| window | ~3 s, sized per case by `choose_repeats` |
| repetitions | 9 paired, order alternating each rep |
| interval | both variants in one process, back to back |
| canary | the deciding case measured against itself, per case file |
| hard timeout | 480 s per case file |

There is no idle subtraction and no attempt to attribute energy to this
process. The reading is what the machine drew over the window. `measure.py`
explains why that is the right choice and what it costs.

Every case file's cases are sized to fill a window, so a case whose input is
trivial gets repeated millions of times and ends up measuring interpreter
overhead rather than the repair. Those were removed on 2026-09-08: 144 of 597
taxonomy cases and 20 of 99 lookalike cases, keeping 453 and 79. The evidence
was the previous host's own data — 120 case rows needed a million repetitions
or more to fill a one-second window, 80 of them reported a statistically
significant result, 47 of those a *regression* on an empty or near-empty input,
and not one of them ever decided a verdict.

## Reproducing

```bash
python validation/preflight.py          # must pass before anything else
python validation/run.py taxonomy
python validation/run.py samples
```

Both are resumable: a case already in `validation/results/<suite>.jsonl` is
skipped, so an interrupted batch costs only the case it was on. To re-measure
one case, delete its line.

Run **strictly one measurement at a time**. That is not tidiness: two
concurrent measurements share the package energy counter and corrupt each
other.

A batch measured under two rule sets is not one batch. If `verify.py`'s verdict
rules change midway through, re-run what came before them.
