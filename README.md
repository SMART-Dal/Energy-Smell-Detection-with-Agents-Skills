# Energy smells — an agent skill

A loadable skill that lets a coding agent find energy smells in Python against
the taxonomy from *Watts This Smell* (12 categories, 65 root causes), and prove
each one by measuring a refactoring that removes it.

We do not ship a detector. We ship the knowledge and the referee.

> A smell claim is admitted only if it is falsifiable and survives falsification.

## The deliverables

`python -m build` writes five skill directories under `dist/`. The first four
differ in **one** thing — what static evidence the agent is given — so a
difference between them is attributable to the evidence rather than to the
instructions. The fifth is the control.

| Directory | Given | Question it answers |
|---|---|---|
| `dist/full/energy-smells` | cards + 43 AST analyzers + 36 ruff rules | do the two evidence sources compose? |
| `dist/ast/energy-smells` | cards + the AST analyzers | what do the taxonomy-specific rules add? |
| `dist/ruff/energy-smells` | cards + the ruff rules | how far does an off-the-shelf linter get? |
| `dist/knowledge/energy-smells` | cards only | how well does the agent do on the taxonomy alone? |
| `dist/control/energy-efficiency` | **no taxonomy at all** | does the taxonomy help a frontier model, or would it have found these anyway? |

The four taxonomy arms all ship a directory called `energy-smells`, and differ
only in the parent directory holding it. That is not tidiness: the skill's own
name is something the agent reads, so naming one arm `energy-smells-knowledge`
would tell it that a fuller version exists. The parent is the experimenter's
filing and never leaves this repository.

The arm is fixed at build time, not chosen by a flag. An arm ships only the code
its condition allows: the knowledge arm has no scanner and no analyzer source on
disk, because an agent that can read `rules/loops.py` has been handed the static
analysis in its most direct form whatever the flags said.

**No arm may reveal that the others exist.** No condition file, no sentence
explaining what is absent, no enum value nothing there can produce. `scan.py`
therefore *discovers* its analyzers -- any module in `lib/analysis` defining
`collect()` is one -- so an installation with fewer of them behaves exactly like
one that never had more. The control arm gets the same task, the same rigour and
the same verifier with none of this taxonomy's vocabulary anywhere in it; without
it we cannot tell whether the cards help or whether the model was going to find
these things regardless.

```bash
cp -r dist/full/energy-smells ~/some-repo/.claude/skills/energy-smells
```

**Install exactly one arm per environment.** Two of them side by side, or one
left behind from an earlier run, gives the agent both conditions at once and
there is nothing in the output that would show it happened.

For an agent without native skill loading, point its instruction file at
`SKILL.md` — the progressive disclosure is written as explicit instructions
("open `reference/categories/C7.md` before deciding"), not as a host feature.

**Runtime: Python 3.9+ and the standard library.** `ruff` is optional. Nothing
calls a network.

## Layout

| Path | Role |
|---|---|
| `taxonomy/*.xlsx` | the published taxonomy — source |
| `catalog/C*.yaml` | authored knowledge: symptoms and cost, exceptions, near-misses, repairs, neighbours |
| `src/` | the scanner and the verifier — authored Python |
| `build/` | renders cards, compiles the routing table, emits the five arms. `CARD_SPEC.md` says how to write an entry |
| `dist/` | **the deliverables** — generated, never edited |
| `validation/` | measures the taxonomy's own claims (see below) |
| `tests/rules/` | one folder per analyzer: what it must flag, and what it must not |
| `eval/` | protocol for cold-agent runs |

```bash
python3 -m venv .venv && .venv/bin/pip install pandas openpyxl pyyaml ruff
.venv/bin/python -m build            # regenerate dist/
.venv/bin/python -m build --check    # fail if dist/ is stale
```

## The two scripts

```bash
python dist/full/energy-smells/scripts/scan.py PATH --units   # ranked reading list
python dist/full/energy-smells/scripts/scan.py PATH [--top N] [--json]
python src/verify.py CASE_FILE [--json]
python src/verify.py --calibrate
```

`scan.py` answers two questions and keeps them apart. `--units` ranks every
function by how hot it looks and says nothing about what might be wrong with any
of them, so it can be run before the agent has formed a view; the default report
groups facts under the root causes they point at, never a verdict. Hotness counts
the loops a unit is *reached* through as well as the ones it contains, so a
helper called from inside someone else's nested loop outranks the loop itself.

`verify.py` takes a case file defining `before`, `after` and `cases()`, checks
behaviour is preserved, sizes each case so its measured window lasts about a
second, and measures the two variants interleaved in one process. Run
`--calibrate` first: it measures identical code against itself, and the width of
that interval is what this host can resolve.

## Validating the taxonomy

`validation/` measures the claims rather than assuming them.

```bash
python validation/preflight.py               # is this host fit to measure on?
python validation/generate_sample_cases.py   # convert data/manual_sampling
python validation/run.py samples             # 84 hand-written before/after pairs
python validation/run.py taxonomy            # cases per contested root cause
```

Results land in `validation/results/*.jsonl`. Run `preflight.py` first: it asks
three questions and stops at the first failure — identical code reads ~0%, a
known saving is detected, and the same pair *swapped* reads negative. The third
matters because a rig that answers "saving" in both directions is broken in a way
the null canary alone cannot see.

`validation/RESULTS.md` records what has been measured and what has not. The
short version: sharing the host moved the median null canary from 0.63% to 8.25%
and one reading to 51%, and every question worth settling landed on a
contaminated floor. `verify.py` reports `inconclusive` rather than `refuted` in
that band, because "the repair does nothing" and "this machine could not tell"
are opposite claims.

Analyzer precision has its own suite, which is not shipped:

```bash
python tests/rules/run.py                    # every rule
python tests/rules/run.py missing_early_exit --verbose
```

Each folder holds one `test_cases.py` of hand-written units and an `EXPECTED`
map from unit qualname to hit count; anything unlisted must produce nothing. Of
347 units, 191 exist to stay silent. The quiet cases are the point: a rule the
reader learns to ignore is worse than no rule.

## Why measurement is not optional

C10.S4 has now been rewritten from measurement twice, in opposite directions,
and the second time was the more instructive.

It began saying what every style guide says: growing a string with `+=` in a
loop is quadratic, so collect the parts and join once. Measured, the textbook
example got **slower**. CPython resizes a string in place when its reference
count is one, so the canonical example was already linear, and the analyzer had
been written to fire on exactly the case that is *not* a smell. The real root
cause turned out to be aliasing: through an attribute, where the in-place
optimisation cannot fire, the same repair measures **+99.9%**. The card, the
analyzer and the workload hint were rewritten from that.

The rewrite then over-corrected, and said the plain-local form was not a smell
at all. Measured again on an idle host, that is also wrong. The resize does fire
and both forms are linear in bytes, but per-part interpreter work remains, and
the join is worth **+18.4% ± 0.6** over 200 000 short parts and **+1.2%** over
2 000 long ones. So the deciding variable is the number of parts, not the total
length, and one card carries two findings of very different size.

Neither correction was available by reasoning. Both came from a paired
measurement on a floor low enough to believe — which is why the verifier is not
an optional final step, and why a card that has been measured says what it
measured and on what.
