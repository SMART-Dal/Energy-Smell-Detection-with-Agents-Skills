# Validation results

Two suites. `samples` has run; `taxonomy` has not, and the reason matters.

## The machine was shared, and it cost us the interesting half

Every run records a **null canary**: `before` measured against `before`, identical
code compared to itself. Whatever that reads is contamination, because the true
answer is zero.

| | idle host (earlier session) | shared host (this run) |
|---|---|---|
| median canary | 0.63% | **8.25%** |
| worst canary | 0.84% | **51.07%** |
| direct reading, 14:15 | — | **−3.99% ± 12.98%** |

Nothing smaller than about 13% is resolvable while the machine is shared. Large
effects still are — a 96% saving clears a 10% floor comfortably — which is why
the confirmations below stand and the null results do not.

**Consequence for the verdicts.** `refuted` used to mean two different things:
"we measured cleanly and the repair does nothing", and "we could not tell".
Those are opposite claims, and collapsing them writes a busy machine down as
evidence against the taxonomy. `verify.py` now emits **`inconclusive`** when the
canary exceeds `USABLE_FLOOR_PCT` (3.0%), and `validation/preflight.py` refuses
to start a batch on a host that fails it.

Re-grading the 84 completed sample runs under that rule:

| Verdict | Count |
|---|---|
| confirmed, effect ≫ floor | **50** |
| confirmed, effect near floor | 7 |
| inconclusive (floor too high) | 11 |
| refuted on a clean floor | 4 |
| regressed | 3 |
| not equivalent | 9 |

## What is established

50 of your 92 pairs confirm with the effect far above the floor. That is the
taxonomy working: `min`/`max` over a hand loop (+48%), a set over a linear scan
(+85–96%), `Counter` over manual tallying where the data has duplicates (+96%),
memoisation over recomputation (+95%), `str * n` over `"".join([str] * n)`
(+98.7%), iterative over recursive factorial (+39.5%).

Three results are worth more than the rest because they refine a card rather
than confirm it, and all three landed on a floor low enough to believe:

| Sample | Result | What it settles |
|---|---|---|
| `MultiplyByFactor` | **+39.0% ± 0.5** (floor 1.2) | C5.S3 holds: `x * 3.0` against `x * 3` is a real 39% on integer data. Validates the new `float_literal_on_int_data` analyzer. |
| `ChangeListElementsType` | **+46.8% ± 4.3** (floor 4.0) | `map` with a **C builtin** beats a comprehension. |
| `SumFilterMap` | **+24.6% ± 1.5** (floor 0.8) | a comprehension beats `map` with a **lambda**. |

The last two together resolve the apparent contradiction between two of your own
samples. The rule is not "prefer `map`" or "prefer comprehensions" — it is
whether the mapped callable re-enters the interpreter. `map(float, xs)` is an
improvement; `map(lambda x: x*2, xs)` is a regression. C10.S2's card now carries
that as a counter-example.

## Nine of your pairs are not behaviour-preserving

These were rejected before measurement, which is the equivalence check doing its
job. They are not useless — several are interesting — but they cannot be used as
evidence about energy, because the two sides compute different things.

| Pair | What differs |
|---|---|
| `BuiltInBehavior/SumTopK` | `lst.sort()` mutates the caller's list; also only wins because the driver re-runs on already-sorted data |
| `OveruseOfLoops/MergeLists` | `lst1.extend(lst2)` mutates its argument, `lst1 + lst2` does not |
| `BuiltInBehavior/OperatingOnList2` | rewrites the input in place and returns it |
| `ImproperDataStructure/DifferenceBetweenNumbers` | different return shape entirely (dict of lists vs list of lists) |
| `ImproperDataStructure/GreaterThanK` | returns a set where the original returned a list |
| `OveruseOfLoops/FindMultipleItems` | returns indices where the original returned values |
| `OveruseOfLoops/OccurenceOfOddItems2`, `3` | off-by-one in the seeded counts |
| `ExtraUsageOfArrays/MatMulNumpy` | float dtype vs int arithmetic |

## What is NOT established, and why it matters

Every claim I most wanted to settle landed on a contaminated floor:

| Question | Reading | Floor | Status |
|---|---|---|---|
| Does a hand loop beat `Counter`? (C10.S1) | −4.5% ± 1.0 | 10.0% | inconclusive |
| Is a listcomp faster than a genexp for `sum`? (C6.S3) | +22.1% ± 0.6 | **51.1%** | inconclusive |
| Is the plain-local `+=` really not a smell? (C10.S4) | −18.9% ± 23.0 | 16.2% | inconclusive |
| Is `isinstance` slower than `type(x) ==`? | −0.5% ± 21.5 | 25.6% | inconclusive |
| Is a constant tuple faster than a list literal? (C5.S3) | +14.9% ± 10.5 | 13.5% | inconclusive |

The `SumMap1` row is the clearest illustration: a **±0.6%** confidence interval
on the effect, and a **51%** canary. The effect is probably real, and I will not
write it down as a fact until the canary agrees.

## To finish this

On an idle machine:

```bash
python validation/preflight.py          # must pass before anything else
python validation/run.py samples --restart
python validation/run.py taxonomy --restart
```

`validation/taxonomy/` holds **69 case files covering all 65 root causes**, each
with 2–3 input cases spanning large / small / edge, plus second files for the
root causes where a sample contradicts a card. All 69 pass the equivalence check
already, so the remaining cost is measurement time — roughly 90 minutes for the
taxonomy suite and 80 for the samples.

Cards will be revised from those results, not before them. The eight
counter-examples written so far all cite a measurement that cleared its floor.
