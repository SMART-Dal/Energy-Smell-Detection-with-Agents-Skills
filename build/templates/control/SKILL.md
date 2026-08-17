---
name: energy-efficiency
description: Find places where Python code wastes energy, refactor them, and prove the saving by measuring it. Use when asked to analyse code or a repository for energy waste, energy efficiency, power consumption, or wasteful computation.
---

# Energy Efficiency Analysis

You are finding **energy waste**: code that spends energy on work the program
does not need, and that a specific refactoring can remove without changing what
the program does.

Paths below are relative to this file's directory — call it `$SKILL`. Work out
what `$SKILL` is once, at the start, and use it throughout.

---

## What counts as a finding

> A finding is a **repair**: a concrete edit to *this* code, with a stated
> reason why the edit saves energy, and measured.

Three consequences you have to hold onto:

- **No repair, no finding.** If you cannot write the actual edit for this code,
  you have not found anything — you have made an observation.
- **No measurement, no claim.** Step 5 is not optional. Received wisdom about
  what is fast in Python is wrong often enough that an unmeasured claim is
  worth nothing, however confident it sounds.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It goes in the report.

## One repair, one reason

Attribute each repair to a single reason: the thing about the code that
explains why the edit saves energy.

Repairs overlap, and that is normal. Fixing how a function searches can make a
redundant conversion, a needless copy and a hoistable lookup all disappear at
once, because they only existed to serve the search. When that happens:

- report **one** finding, for the repair you actually made;
- list the observations it absorbed under `subsumed`;
- do **not** widen the repair to cover extra observations, and do not split one
  edit into several findings to raise the count.

So after a repair lands, **re-read the unit** (step 6) and see what is left.
What survives gets its own repair. What evaporated gets recorded as subsumed.

## Two things that are not energy waste

**Style.** Unreadable, undocumented, poorly named, badly typed code is not
energy waste. If the repair does not change what the machine does, it is out of
scope here.

**Cold code.** A wasteful pattern in a function called once at import time
wastes nothing measurable, however ugly it is. Before accepting anything, ask
where this unit sits in the program's actual work. If the answer is "it runs a
fixed handful of times whatever the input", stop there and record why — that is
a cheaper and more honest rejection than measuring it later.

## Energy is not time

They usually move together, but not always. Spreading work across cores cuts
wall-clock time while raising energy. A busy-wait poll burns power while making
no progress. A blocked event loop keeps a core hot for nothing. Judge energy,
and when the two diverge, say so — those cases are the most interesting ones
you can find.

---

## Procedure

Six steps, in order, one unit at a time. Each step says what it takes in and
what it must produce; do not carry work forward that the step did not produce.

### 1. Select — *in:* a path · *out:* a ranked list of units to examine

Choose the units yourself.

Read the repository first: its entry points, what its tests exercise, what its
README says it is for. Then pick the units where energy is actually spent, in
this order of priority:

1. **work that repeats** — the deepest loop nests, and the helpers those loops
   call, which is where a cheap-looking function gets paid thousands of times;
2. **work proportional to input size**, rather than to a fixed constant;
3. **the repository's own hot path** — what it benchmarks, what its main entry
   point spends its time in.

Examine at least 10 units, or all of them if the target has fewer. Record every
unit you looked at, including the ones you cleared.

### 2. Read and observe — *in:* one unit · *out:* `observations[]`

**2a. Read the code and say what it does.** Read the whole unit, then follow it
outward in both directions:

- **Down, into what it calls.** If the unit calls something you have not read,
  read it. A three-line loop body calling `normalise(row)` may be compiling a
  regex and rebuilding two dicts per iteration, and none of that is visible
  from the loop. Keep going until you reach the standard library or code that
  plainly does no work.
- **Up, into what calls it.** Cost is paid per execution. A cheap function
  called from inside someone else's nested loop is expensive; an expensive one
  called once at startup is not.

Then write two sentences: what it computes, and what would dominate its cost on
a large input.

Reading outward is not politeness about context. Some waste sits in a line — a
conversion, a lookup, a concatenation — and you can see it where it is. The
expensive kind usually sits in the *arrangement*: a value computed in one place
and thrown away in another; a shape chosen early that every later step has to
compensate for; six functions doing what a different split does in two; a
result recomputed on each of three paths that each look reasonable alone. None
of that is visible from any single statement, and no amount of care about
individual lines will find it. That is what you are reading outward for.

**2b. Say what is wasteful, and be specific.** For each thing you find, name
the lines and say in one or two sentences what work is being done that the
result does not require. "Inefficient string handling" is not an observation;
"`self.buf` is grown with `+=` once per row and nothing reads it inside the
loop" is.

**Output of this step.** For each unit, one record:

```jsonc
{
  "unit": "src/render.py::Report.render",
  "what_it_does": "renders one HTML table from a list of row dicts",
  "cost_driver": "one pass per row, and string building across all rows",
  "observations": [
    {"lines": [47], "confidence": "high",
     "what": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "why_wasteful": "each += allocates a new string and copies everything already built"},
    {"lines": [44, 45], "confidence": "medium",
     "what": "`sorted(self.columns)` is recomputed on every row",
     "why_wasteful": "the result cannot change inside the loop, so the sort is paid n times"}
  ]
}
```

**At most 8 observations per unit.** The cap is there to make you rank rather
than list. If you have more than eight, keep the ones you would actually spend
an hour repairing.

### 3. Narrow — *in:* `observations[]` · *out:* ≤5 `candidates[]` per unit

Not everything wasteful is worth repairing. Drop an observation when:

- the saving is a fixed, tiny amount per execution that no input size can grow;
- the unit does not run often enough for any saving to exist;
- the repair would change behaviour, not just cost;
- the expense buys something — a check that is there for correctness, a copy
  that protects a caller, a wrapper that is public API.

Carry at most **5 candidates per unit** into step 4, and record what you
dropped and why.

### 4. Decide — *in:* `candidates[]` · *out:* accepted / rejected, each with a reason

For each candidate:

1. Can you write the repair for *this* code, as a minimal edit rather than a
   rewrite of the unit?
2. Does the repair preserve behaviour on every input, including the edge cases?
3. Does this unit run often enough, on large enough data, for the saving to be
   measurable at all?
4. Is the reason you expect a saving something you can state mechanically —
   what work stops happening, and why — rather than a rule of thumb?

Accept only if you can answer all four. Record every rejection with the check
that decided it; a rejection with a reason is a result.

### 5. Repair and measure — *in:* accepted candidates · *out:* a verdict each

Write the repair, then one case file per candidate, then measure it:

```bash
python $SKILL/scripts/verify.py cases/case_render_concat.py
```

Read `$SKILL/reference/verifying.md` before your first case file. It has the
contract, how to build a case that resembles the real code rather than a toy,
the sizing rules, and what each verdict means.

If a repair's saving is a fixed and very small amount per execution — a single
bytecode instruction, say — no workload size will lift it above the noise
floor. Report it as `advisory` with your reasoning, and do not claim it was
measured.

### 6. Re-check and report — *in:* verdicts · *out:* `findings.json` + `REPORT.md`

Before writing anything, apply each confirmed repair and **read the unit
again**. For every remaining candidate, ask whether it still applies. Those
that do not are `subsumed` by the repair that removed them — record them there,
not as separate findings.

Then write both files. `$SKILL/reference/output-format.md` has the exact schema.

---

## How this goes wrong

Five failure modes, in the order they actually happen:

1. **Repeating what you have read about Python performance.** Much of it is
   out of date, and some of it was never true. Every claim here gets measured,
   and the ones you are most certain about are the ones worth measuring first.
2. **Splitting one repair into several findings.** One edit, one finding, one
   reason; the rest are `subsumed`.
3. **Ignoring context.** Almost every pattern that looks wasteful is the right
   call somewhere. A bare `except` in a retry loop, a materialised list that
   gets indexed twice, a wrapper that is public API. Ask what the author was
   required to do before deciding they were wrong.
4. **Skipping measurement because the waste is obvious.** The obvious ones are
   exactly where a wrong assumption about hotness hides.
5. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to one reason, and cannot be measured against one. Keep the edit minimal —
   that bounds what you *change*, never what you are allowed to read.

## Scope

Python.

A unit is normally a function or a method: it is the granularity at which a
repair is scoped and measured. It is not a limit on how much code you may read,
and it is not a limit on where the waste may live. When the waste is in the
arrangement of several units, say which units it spans and repair the smallest
set that removes it.
