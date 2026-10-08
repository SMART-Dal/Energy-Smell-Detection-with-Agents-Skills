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
| `tools/` | our side of an agent run: re-measure, decide what to apply, report — never shipped |
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
python src/verify.py --calibrate                               # this host's noise floor
python src/verify.py SUBMISSIONS.jsonl --repo PATH             # an agent's repairs
python src/verify.py SUBMISSIONS.jsonl --repo PATH --no-record --json   # re-measure, ours
python src/verify.py CASE_FILE.py [--json]                     # a validation sample
```

`scan.py` answers two questions and keeps them apart. `--units` ranks every
function by how hot it looks and says nothing about what might be wrong with any
of them, so it can be run before the agent has formed a view; the default report
groups facts under the root causes they point at, never a verdict. Hotness counts
the loops a unit is *reached* through as well as the ones it contains, so a
helper called from inside someone else's nested loop outranks the loop itself.

`verify.py` measures one repair against the code it replaces: it checks
behaviour is preserved, sizes each case so its measured window is long enough,
and measures the two versions alternately, window by window, on one thread.

It takes its pair from either of two sources, and the four stages after loading
are the same code. A **submission** (`.jsonl`) is what an agent produces: it
names a unit as `path::qualname` and gives the replacement source, and `before`
is read from the repository, never from the submission — which is what stops a
baseline being shaped to flatter the result. A pristine copy and a patched copy
of the repository are imported side by side in one worker process under their
real package names, nothing renamed and no import rewritten. A **case file**
(`.py`) defines `before`, `after` and `cases()` itself, and is how our own
validation samples are written.

Submissions are measured one way, by the agent and when we re-measure them: 1 s
windows, 5 pairs, the noise floor calibrated once per session — about a minute
a repair. The agent's run writes each result back into its line as
`agent_measurement`; a measured result is final, and editing a measured line
makes it `invalid`. Validation case files keep the settings every recorded
result used (3 s windows, 9 pairs, a canary per case), so those results stay
comparable. `--calibrate` measures two copies of identical code against each
other; the width of that interval is what this host can resolve.

## Asking for an analysis

The skill works on a **target**, an optional **number of units**, and a cap on
how many repairs it measures — all taken from the request:

| Ask for | It examines | It measures |
|---|---|---|
| "Find energy smells in this repository" | every unit, hottest first | the 15 most promising repairs |
| "… in `src/render/`" or "… in `src/render.py`" | every unit there | the 15 most promising |
| "… in `src/render.py::Report.render`" | that one method | its repairs |
| "… examine 10 units" | the 10 hottest units | the 15 most promising |
| "… and measure every repair" | as above | all of them |

A number limits units only, never suspicions or root causes; the agent may
change which units those are as it goes, but never examines more.
Accepted suspicions beyond the measured 15 are recorded as `deferred`: still
findings, with no saving claimed. Name a single function as
`path/to/file.py::qualname` — a method as `Class.method` — the same form every
result uses; a loose name ("the render function") also works, and the agent
records what it resolved it to.

Time is roughly 3–4 minutes of agent work per unit plus about a minute per
measured repair, so "examine 10 units" is around 45–55 minutes. With no number,
every unit in the target is examined, which on a large repository runs to
hours: give a number for anything bigger than a few dozen functions.

## An agent run, and our side of it

The agent never edits the repository. It leaves two files:

- `findings.jsonl` — its work, one line per step per unit: what it selected,
  what it suspected and why, what it accepted, and what became of each;
- `submissions.jsonl` — one repair per line, each carrying the measurement
  `verify.py` wrote into it.

```bash
python tools/review.py REPO RUN_DIR            # re-measure, decide, write the report
python tools/review.py REPO RUN_DIR --apply    # ...and write the applied repairs into REPO
```

`review.py` re-measures every submission on a fresh copy, on an idle machine,
writes `results.jsonl` and `REPORT.md` into `RUN_DIR`, and decides
what to apply. Every repair was written against the original code, so at most
one per function can be: among a function's `confirmed` repairs, the one with
the highest mean saving across its five cases — they share their inputs, so the
means compare — and every other repair is recorded with the reason it was not
applied. Nothing that is not `confirmed` is applied; `mixed` included.

## Validating the taxonomy

`validation/` measures the claims rather than assuming them.

```bash
python validation/preflight.py               # is this host fit to measure on?
python validation/generate_sample_cases.py   # convert data/manual_sampling
python validation/run.py samples             # 84 of the 92 hand-written pairs
python validation/run.py taxonomy            # cases per contested root cause
```

`data/manual_sampling/` holds 92 hand-written pairs; 84 of them convert into
runnable cases, which is the count the sample run reports.
`build/SAMPLE_NUANCES.md` reads the full 92.

Results land in `validation/results/*.jsonl`. Run `preflight.py` first: it asks
three questions and stops at the first failure — identical code reads ~0%, a
known saving is detected, and the same pair *swapped* reads negative. The third
matters because a rig that answers "saving" in both directions is broken in a way
the null canary alone cannot see.

`validation/RESULTS.md` records what has been measured and what has not. The
short version, from an idle host: **all 65 root causes are measured**, across
230 cases — 146 confirmed, 43 mixed, 32 regressed, 5 negligible, 3
inconclusive, 1 timeout. Median per-case canary 1.73%, with 50 of 229 readings
above 3%.

A regressed or mixed case is not a refutation of the taxonomy. The published
taxonomy is the reference; our measurements are 3-4 cases per root cause on one
host, and which direction a repair pays in can turn on the loop body rather
than the input size — `sum(x for x in l)` favours the comprehension while
`sum(x * 2 for x in l)` favours the generator, on the same machine. What a
regression changes is the advice beside the card, not the card.

`verify.py` reports `inconclusive` rather than `negligible` when the canary is
too high to resolve an effect, because "the repair does nothing" and "this
machine could not tell" are opposite claims.

Analyzer precision has its own suite, which is not shipped:

```bash
python tests/rules/run.py                    # every rule
python tests/rules/run.py missing_early_exit --verbose
```

Each folder holds one `test_cases.py` of hand-written units and an `EXPECTED`
map from unit qualname to hit count; anything unlisted must produce nothing. Of
347 units, 191 exist to stay silent. The quiet cases are the point: a rule the
reader learns to ignore is worse than no rule.

## What measurement is for

**The taxonomy is the reference, and measurement does not sit in judgement on
it.** The 65 root causes come from a literature review; each one names a real
mechanism, and a repair that fails to pay on one host in one shape does not make
the mechanism imaginary. What measurement settles is narrower and more useful:
*where* a root cause pays, *how much*, and *where it does not* — so the cards can
tell an agent what to expect instead of asserting a rule.

C10.S4 is the standing example. Its published description says each `+=`
allocates and copies, so N concatenations of average length M cost O(N*M). That
is exactly right, and the guidance around it has been rewritten twice from
measurement without the description changing once.

Through an aliased target — an attribute, a subscript, a global — the described
cost is what happens, and the repair measures **+99.9%**. Through a plain local
that nothing else reads, CPython resizes the string in place, the O(N*M) term
collapses, and what remains is per-part interpreter work: **+18.4% ± 0.6** over
200 000 short parts and **+1.2%** over 2 000 long ones. So the deciding variable
is the number of parts, not the total length, and one card now carries two
findings of very different size.

None of that was available by reasoning. It came from paired measurement on a
floor low enough to believe — which is why the verifier is not an optional final
step, and why a card that has been measured says what it measured and on what.
