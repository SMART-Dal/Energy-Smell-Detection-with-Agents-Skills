# Validation results

Two suites, both run on 2026-08-18/19 on an idle host. The earlier run of the
samples suite happened while the machine was shared and is superseded — its
median null canary was 8.25% and one reading reached 51%, which put every
question worth settling on a contaminated floor.

## The host, this time

`validation/preflight.py` passed before either batch: null canary **2.43%**,
the known saving read +99.1%, and the same pair swapped read negative. The
per-case canaries are the number to trust, and they were much better than the
preflight suggests.

| | shared host (superseded) | idle host (this run) |
|---|---|---|
| median per-case canary | 8.25% | **1.07%** |
| 90th percentile | — | 2.44% |
| readings above 3% | most | **5 of 69** |

The one bad floor is `C11S5_missed_parallelism` at 25.1%, and the cause is the
case itself: it starts a thread pool, so the canary measures a host the case
file is disturbing. Its +86.4% clears even that, but treat the magnitude as
approximate.

---

## Taxonomy suite: 69 cases, all 65 root causes

**49 confirmed, 8 refuted, 12 regressed.** Every root cause now has at least one
measurement on a floor low enough to believe, which was the point of the suite
and had never been done.

### What the confirmations establish

The large effects are where the taxonomy says they are — complexity, external
access, and work that never needed doing:

| | |
|---|---|
| +100% | C1.S8 runtime management (`gc.collect()` per iteration) |
| +99.9% | C10.S4 aliased string concatenation · C7.S1 algorithm choice · C7.S2 decomposition |
| +99.8% | C3.S7 mutation during iteration |
| +99.5% | C5.S2 missing index · C3.S4 nested scan · C8.S4 redundant fetching |
| +99.2% | C3.S3 per-iteration setup · C5.S1 membership on a list |
| +98.8% | C11.S4 blocking call in a coroutine |
| +97.0% | C9.S1 fragmented I/O |

and the small ones are small, in the range a card should describe as advisory
or nearly so: C4.S3 conditional nesting +1.7%, C1.S2 redundant assignment
+2.9%, C1.S7 single-use temporary +3.4%, C1.S3 redundant boolean branch +6.1%.

### Eight clean refutations

Measured, equivalent, and no saving on a floor low enough to mean it:

| Case | Reading | Floor | What it says |
|---|---|---|---|
| `C4S1_short_circuit_order` | −1.0% | 1.2% | reordering the operands bought nothing here |
| `C6S7_mutable_default` | −0.7% | 0.3% | the correctness bug is real; the energy claim is not |
| `C1S6_unnecessary_init` | −0.7% | 2.8% | moving the setup into the branch saved nothing at this hit rate |
| `C12S4_declaration_order` | +0.6% | 2.1% | `__slots__` order does not decide layout in CPython, as the card says |
| `C4S7_edge_case_guard` | +0.2% | 0.8% | the guard's cost across all calls matched what it saved on the few |
| `C11S1_lock_contention` | +0.2% | 0.9% | narrowing a critical section with no contention present |
| `C11S2_serial_bottleneck` | −0.2% | 0.9% | |
| `C11S3_leaked_thread` | −0.1% | 1.4% | |

The C11 cluster is a limit of the harness rather than a fact about the
taxonomy, and the cards now say so. A one-second paired window cannot exercise
contention, cannot accumulate leaked threads, and cannot make a bottleneck bite.
What those three cards claim is a failure mode at scale, and the honest report
for them is the mechanism plus a count, not an energy figure.

### Twelve regressed, and they are not one thing

`regressed` means the repair helped the deciding case and hurt another one by
more than 1% of the deciding case's own cost. That covers three different
situations, and lumping them together would misread the taxonomy badly.

**Five are the card's own precondition, measured.** The case file deliberately
includes the input where the card says to reject the candidate, and the repair
loses there. These confirm the cards rather than contradicting them:

| Case | Where it holds | Where it does not |
|---|---|---|
| `C8S1_memoization` | +89.4% many repeats | −14.2% all distinct |
| `C10S1_counter` | +63.1% many duplicates | −12.5% all distinct |
| `C4S6_exception_control_flow` | +73.8% always raises | −36.4% never raises |
| `C7S4_sort_then_slice` | +69.9% k tiny, n large | −971% k near n |
| `C9S2_oversized_retrieval` | +99.9% needs few columns | −204% needs all |

Each of those "where it does not" columns is a `not_a_smell_when` clause on the
card, stated before the measurement. **This is an open question about the
harness, not about the taxonomy**: a case file that spans both regimes can only
ever come back `regressed`, so either the case files should stay inside the
stated precondition, or the verdict vocabulary needs a way to say "confirmed
where the card says it applies, and loses where the card says it does not". The
second is more informative and also more abusable, so it is left for a decision
rather than taken.

**Four are genuine, and two of those change a card.**

- `C12S2_sparse_access` **−126%**, on both cases, floor 0.8%. Sorting scattered
  indices before a gather costs far more than the cache misses it avoids. The
  card warned about this; it can now say it with a number.
- `C12S3_unpredictable_branch` **−35%** and **−65%**. Branchless arithmetic in
  interpreted Python is a loss: `total += x * (x > 0)` pays a comparison, a
  coercion and a multiply where `if x > 0` skips the work outright. The card
  said the effect is unreachable from CPython; it is worse than unreachable.
- `C2S2_static_method` **−5.3%** over many calls. The card already carried a
  warning that the direction was unconfirmed, and this settles it: on a modern
  CPython, `@staticmethod` is not the cheaper declaration.
- `C6S6_leaked_handle` −2.9%. Using `with` costs slightly more than not closing,
  which is true and beside the point — the claim is about descriptor exhaustion.

**Three were the case file, not the taxonomy**, and are rewritten and queued to
re-run: `C4S5_expensive_comparison` measured `sorted` against `Counter` and lost
by 1222%, which is a true reading of a claim C4.S5 does not make; `C9S3` and
`C9S4` stood a dict and a list in for the external store, which removes the only
cost C9 is about. C9.S1, which uses real file writes, confirmed at +97%.

### Cards changed by this run

| Card | Change |
|---|---|
| C10.S4 | the plain-local `+=` is a real 18.4% at 200 000 parts and 1.2% at 2 000; the part count decides it, not the total length. The card had said it was not a smell at all |
| C6.S4, C6.S5 | reclassified from advisory to measurable: +28.8% and +22.2% |
| C1.S2, C1.S3, C1.S7 | reclassified from advisory to `scales_with_calls`: +2.9%, +6.1%, +3.4%, all in loops that do almost nothing else |
| C12.S2, C12.S3 | the reflex repair measured as a large loss, with the number |
| C11.S1, C11.S3 | the precondition failing, and what to report instead of energy |
| C10.S2 | `Counter` against `sorted` on five-element lists: twelve times slower |

Advisory-only root causes: **eight before this run, three after** — C6.S6,
C11.S3 and C12.S4.

---

## Samples suite: 84 of the project owner's hand-written pairs

**Running, 48 of 84 recorded.** It continues in a detached tmux session started
on 2026-08-19; see *Finishing this* below. This section is written up when the
batch completes.

Of the 48 settled so far, the pattern matches the taxonomy suite: large,
clean confirmations where the taxonomy predicts them, and a handful of
refutations on floors low enough to mean it.

Superseded findings from the shared-host run that this batch re-tests: 50 of 84
confirmed with the effect far above the floor, 11 inconclusive on a floor too
high to resolve, 4 refuted, 3 regressed, 9 rejected by the equivalence check.

The nine that are not behaviour-preserving stay rejected and are a result in
themselves — `SumTopK` mutates the caller's list, `MergeLists` mutates its
argument, `GreaterThanK` returns a set where the original returned a list, and
so on. They cannot be used as evidence about energy because the two sides
compute different things.

---

## Finishing this

The remaining work runs itself:

```bash
tmux attach -t energy                       # watch it
tail -f validation/results/samples.log      # or just the log
```

`validation/run_remaining.sh` runs the samples suite to completion and then the
three rewritten taxonomy cases, **strictly one measurement at a time**. That
sequencing is not tidiness: two concurrent measurements share the package
energy counter and corrupt each other, which happened once during this session
and cost a restart.

It is finished when `=== ALL BATCHES FINISHED ===` appears in either log. At
that point `validation/results/samples.jsonl` has 84 rows and
`taxonomy.jsonl` has 69, and both want committing.

## Reproducing

```bash
python validation/preflight.py          # must pass before anything else
python validation/run.py taxonomy
python validation/run.py samples
```

Both are resumable: a case already in `validation/results/<suite>.jsonl` is
skipped, so an interrupted batch costs only the case it was on. To re-measure
one case, delete its line.

One caution learned in this run. `verify.py`'s verdict rules changed midway
through the first taxonomy batch — a loss now has to clear the host's noise
floor, the same bar a saving has to clear — so every `regressed` case was
re-run afterwards to keep the batch internally consistent. A batch measured
under two rule sets is not one batch.
