# Energy smells — an agent skill

A loadable skill that lets a coding agent find energy smells in Python against
the taxonomy from *Watts This Smell* (12 categories, 65 root causes), and prove
each one by measuring a refactoring that removes it.

We do not ship a detector. We ship the knowledge and the referee.

> A smell claim is admitted only if it is falsifiable and survives falsification.

## The deliverables

`python -m build` writes four skill directories under `dist/`. They differ in
**one** thing — what static evidence the agent is given — so a difference in
results is attributable to the evidence and not to the instructions.

| Directory | Evidence | Question it answers |
|---|---|---|
| `dist/energy-smells` | AST + ruff | do the two sources compose? |
| `dist/energy-smells-ast` | 43 AST analyzers | what do the taxonomy-specific rules add? |
| `dist/energy-smells-ruff` | 36 ruff rules | how far does an off-the-shelf linter get? |
| `dist/energy-smells-knowledge` | none | how well does the agent do on the taxonomy alone? |

The arm is fixed at build time, not chosen by a flag. An arm ships only the code
its condition allows: the knowledge arm has no scanner and no analyzer source on
disk, because an agent that can read `rules/loops.py` has been handed the static
analysis in its most direct form whatever the flags said.

```bash
cp -r dist/energy-smells ~/some-repo/.claude/skills/energy-smells
```

For an agent without native skill loading, point its instruction file at
`SKILL.md` — the progressive disclosure is written as explicit instructions
("open `reference/categories/C7.md` before deciding"), not as a host feature.

**Runtime: Python 3.9+ and the standard library.** `ruff` is optional. Nothing
calls a network.

## Layout

| Path | Role |
|---|---|
| `taxonomy/*.xlsx` | the published taxonomy — source |
| `catalog/C*.yaml` | authored knowledge: preconditions, exceptions, repairs, discriminators |
| `src/` | the scanner and the verifier — authored Python |
| `build/` | renders cards, compiles the routing table, emits the four arms |
| `dist/` | **the deliverables** — generated, never edited |
| `validation/` | measures the taxonomy's own claims (see below) |
| `eval/` | protocol for cold-agent runs |

```bash
python3 -m venv .venv && .venv/bin/pip install pandas openpyxl pyyaml ruff
.venv/bin/python -m build            # regenerate dist/
.venv/bin/python -m build --check    # fail if dist/ is stale
```

## The two scripts

```bash
python dist/energy-smells/scripts/scan.py PATH [--top N] [--json]
python src/verify.py CASE_FILE [--json]
python src/verify.py --calibrate
```

`scan.py` reports facts grouped under the root causes they point at — never a
verdict. Units are ranked by how hot they are, which counts the loops a unit is
*reached* through as well as the ones it contains: a helper called from inside
someone else's nested loop outranks the loop itself.

`verify.py` takes a case file defining `before`, `after` and `cases()`, checks
behaviour is preserved, sizes each case so its measured window lasts about a
second, and measures the two variants interleaved in one process. Run
`--calibrate` first: it measures identical code against itself, and the width of
that interval is what this host can resolve.

## Validating the taxonomy

`validation/` measures the claims rather than assuming them.

```bash
python validation/generate_sample_cases.py   # convert data/manual_sampling
python validation/run.py samples             # 84 hand-written before/after pairs
python validation/run.py taxonomy            # cases per contested root cause
```

Results land in `validation/results/*.jsonl`.

## Why measurement is not optional

C10.S4 used to say what every style guide says: growing a string with `+=` in a
loop is quadratic, so collect the parts and join once.

Measured, the textbook example got **slower** — 62 ms against 56 ms at 400 000
iterations. CPython resizes a string in place when nothing else refers to it, so
the canonical example was already linear, and the analyzer had been written to
fire on exactly the case that is *not* a smell.

The real root cause is aliasing. Through an attribute, where the in-place
optimisation cannot fire, the same repair measures **94.8% ± 0.1%** against a
0.7% noise floor. The card, the analyzer and the workload hint were rewritten
from that measurement.

That is the deliverable working as intended, and the reason the verifier is not
an optional final step.
