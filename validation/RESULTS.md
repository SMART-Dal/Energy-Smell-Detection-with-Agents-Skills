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

| | |
|---|---|
| meter | CodeGreen 0.4.8, `totals.energy_j` verbatim |
| domains | whole-machine CPU package, **nothing subtracted** |
| affinity | none; the workload runs wherever the scheduler puts it |
| machine warmup | 10 s of unrelated arithmetic |
| window | ~3 s on the **faster** variant, both variants running the same count |
| slow-side budget | 15 s, after which the repeat count is clamped |
| repetitions | 9 paired, order alternating each rep (3 when one call exceeds the budget) |
| canary | one case measured against itself, per case file |
| hard timeout | 1200 s per case file |

There is no idle subtraction and no attempt to attribute energy to this
process. The reading is what the machine drew over the window.

**Sizing.** Both variants are timed first (median of 5 calls each), and the
repeat count is set so the *faster* one fills a 3 s window. Both then run that
same count, because equal work on both sides is what makes the comparison
fair. When one variant is far slower, that count is clamped so its window stays
under 15 s — which means the fast side gets less than a full window, and that
is safe: clamping only happens when the ratio between the variants is large,
and a large ratio is a large effect whose precision comes from the well
resolved slow side. The two conditions cannot bite at once.

Every row records the repeat count, both per-call costs, and the window each
variant actually got, so a short window is visible rather than silent.

**Energy decides everything.** Every rule is written against measured joules.
Time and power are still recorded and are worth reading -- energy improving
while duration does not is a real and interesting result -- but no rule reads
them.

**Each case is judged on its own**, and the row says whether all of them
improved, some did, or none did. No case is promoted to the top of the row as
the file's headline: a file's result is its cases, and picking one to stand for
the rest only invited that one number to be quoted as though it were the whole
answer. The one case named in a row is `canary_case`, which says where the
noise floor was measured and nothing more.

**Rows store measurements, not percentages.** Each case carries the joules and
seconds each variant actually used. A percentage of energy saved is a view of
those two numbers, and keeping a derived figure beside its inputs invites the
two to disagree. The one derived field kept is `energy_ci_pct`, which is not a
saving: it is the half-width of the 95% interval on the paired comparison, the
only quantity here that cannot be recovered from the means, and `significant`
cannot be judged without it.

## Verdicts

Five outcomes, answering five different questions:

| status | meaning |
|---|---|
| `confirmed` | every case that moved, moved the right way |
| `mixed` | helps some inputs, hurts others — a trade-off |
| `regressed` | every case that moved, got worse |
| `negligible` | measured cleanly; nothing moved more than the noise |
| `inconclusive` | this host could not resolve an effect of this size |

`negligible` and `inconclusive` must never be collapsed. The first says the
repair does nothing on a machine quiet enough to tell, which is evidence. The
second says the machine was too noisy to ask, which is no evidence about the
code at all. Three more statuses report that no verdict was reached:
`not_equivalent`, `timeout`, `error`.

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
