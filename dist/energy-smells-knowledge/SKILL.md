---
name: energy-smells
description: Find energy smells in Python code using the Watts This Smell taxonomy (12 categories, 65 root causes), and prove each one by measuring a refactoring that removes it. Use when asked to analyse code or a repository for energy smells, energy waste, power consumption, or energy inefficiency.
---

# Energy Smell Identification

You are finding **energy smells**: code that spends energy on work the program
does not need, and that a specific refactoring can remove without changing what
the program does.

Paths below are relative to this file's directory — call it `$SKILL`. Work out
what `$SKILL` is once, at the start, and use it throughout.

---

## What counts as a finding

> A finding is a **repair**: a concrete edit to *this* code, attributed to the
> one root cause that explains why the edit helps, and measured.

Three consequences you have to hold onto:

- **No repair, no finding.** If you cannot write the actual edit for this code,
  you have not found anything — you have recognised a pattern.
- **No measurement, no claim.** Step 5 is not optional. This taxonomy has
  sixty-five plausible-sounding labels, which is more than enough to justify
  anything after the fact. A claim nobody tested is worth nothing.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It goes in the report.

## One repair, one root cause

Attribute each repair to a single root cause: the one that explains why the
edit saves energy. That is a rule about *attribution*, not about counting.

Repairs overlap, and that is normal. Fixing how a function searches can make a
redundant conversion, a needless copy and a hoistable lookup all disappear at
once, because they only existed to serve the search. When that happens:

- report **one** finding, for the repair you actually made;
- list the other candidates under `subsumed`, and say they went away;
- do **not** widen the repair to cover extra candidates, and do not split one
  edit into several findings to raise the count.

So after a repair lands, **re-read the unit** (step 6) and see what is left.
Candidates that survive get their own repair. Candidates that evaporated get
recorded as subsumed — that record is useful in itself, because it shows which
root causes are the ones that actually carry weight.

Two agents that report three and seven candidates for the same function have
not necessarily disagreed. What they must both do is say which candidates
turned into repairs, and which were absorbed by another repair.

## Two things that are not energy smells

**Style.** Unreadable, undocumented, poorly named, badly typed code is not an
energy smell. If the repair does not change what the machine does, it is out of
scope here.

**Cold code.** A pattern in a function called once at import time wastes
nothing measurable, however ugly it is. Before accepting anything, ask where
this unit sits in the program's actual work. If the answer is "it runs a fixed
handful of times whatever the input", stop there and record why — that is a
cheaper and more honest rejection than measuring it later.

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


### 2. Read and suspect — *in:* one unit · *out:* `suspicions[]`

Three moves, in this order. The order is the point.

**2a. Read the code and say what it does.** Read the whole unit, then follow it
outward in both directions:

- **Down, into what it calls.** If the unit calls something you have not read,
  read it. A three-line loop body calling `normalise(row)` may be compiling a
  regex and rebuilding two dicts per iteration, and none of that is visible
  from the loop.  Keep going until you reach the standard library or code that
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

**2b. Say what looks wasteful, in your own words, before opening any card.**
No IDs yet. Just: which work here does not need to happen, is done more often
than necessary, or is done in a more expensive way than the result requires?
Write this down — it goes in the output as `own_hypotheses`.

This is the only defence against reading code through a label you have already
picked, and it only works if you do it first and record it.

**2c. Now match against the taxonomy, at the shallow level only.** Read the
category index at the bottom of this file. Open
`$SKILL/reference/categories/<ID>.md` for any category that might apply — each
one lists its root causes with a line apiece, which is usually enough to tell
whether one is worth a closer look.

**Do not open root-cause cards yet.** You are producing suspicions, not
verdicts.

Open the categories your reading pointed you at, and open others if the code
suggests them. Nothing restricts which categories you may consider, and a
category you were not steered toward is not thereby excluded.



**Output of this step.** For each unit, one record:

```jsonc
{
  "unit": "src/render.py::Report.render",
  "what_it_does": "renders one HTML table from a list of row dicts",
  "cost_driver": "one pass per row, and string building across all rows",
  "own_hypotheses": [
    "the output string is rebuilt on every row",
    "`self.columns` is re-derived inside the row loop and never changes"
  ],
  "suspicions": [
    {"root_cause": "C10.S4", "lines": [47],    "confidence": "high",
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "found_by": "both"},
    {"root_cause": "C3.S2",  "lines": [44,45], "confidence": "medium",
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row",
     "found_by": "reading"}
  ]
}
```

`found_by` is `reading`, `scan`, or `both` — record it honestly, including when
the scan saw something you did not.

**At most 8 suspicions per unit.** The cap is there to make you rank rather
than list. If you have more than eight, you are matching patterns rather than
reading code; keep the ones you would actually spend an hour repairing.

### 3. Narrow — *in:* `suspicions[]` · *out:* ≤5 `candidates[]` per unit

Now open `$SKILL/reference/root-causes/<ID>.md` for each suspicion.

**Open the card. Do not work from the name or from memory.** The names are
short and several of them mean something considerably narrower — or wider —
than they sound.

Drop a suspicion when the card describes something that is not what this code
does. Keep it when the card's `How to tell` steps are answerable here, even if
you are not yet sure of the answer — that is step 4's job.

Cards list **neighbours**: root causes that match similar-looking code. Open
those too. They exist because this taxonomy overlaps in places, and the
neighbour is often the better fit — or the one that finally makes the code make
sense when the card you started from does not quite.

Carry at most **5 candidates per unit** into step 4, and record what you
dropped and why.

### 4. Decide — *in:* `candidates[]` · *out:* accepted / rejected, each with a reason

For each candidate, work through the card:

1. Does every step of `How to tell` hold here? Name the line that settles each.
2. Does any `NOT a smell when` clause apply?
3. Does the code match anything under `Looks the same, is not`?
4. Does a neighbour describe it better?
5. Can you write the repair for *this* code — not the card's example — and does
   it stay within the stated patch shape?
6. Does this unit run often enough for the saving to exist at all?

Accept only if you can answer all six. Record every rejection with the check
that decided it; a rejection with a reason is a result, and the reasons are
what distinguish analysis from labelling.

### 5. Repair and measure — *in:* accepted candidates · *out:* a verdict each

Write the repair, then one case file per candidate, then measure it:

```bash
python $SKILL/scripts/verify.py cases/case_C10S4.py
```

Read `$SKILL/reference/verifying.md` before your first case file. It has the
contract, how to build a case that resembles the real code rather than a toy,
the sizing rules, and what each verdict means.

Root causes marked **advisory only** on their card are exempt: their repair is
worth a single bytecode instruction and cannot clear any noise floor. Report
them as `advisory` and do not build a case file.

### 6. Re-check and report — *in:* verdicts · *out:* `findings.json` + `REPORT.md`

Before writing anything, apply each confirmed repair and **read the unit
again**. For every remaining candidate, ask whether it still applies. Those
that do not are `subsumed` by the repair that removed them — record them there,
not as separate findings.

Then write both files. `$SKILL/reference/output-format.md` has the exact schema.

---

## Categories

| ID | Category | Covers | Card |
|---|---|---|---|
| **C1** | Redundant Computation | Energy waste from executing work that does not contribute to the program's required output or that leaves program state unchanged | `reference/categories/C1.md` (8) |
| **C2** | Unnecessary Call Overhead | Energy waste from extra layers of function calls, method delegation, or dynamic dispatch that add overhead without proportional benefit | `reference/categories/C2.md` (3) |
| **C3** | Inefficient Iteration Patterns | Energy waste from loops that perform more per-iteration work than necessary, iterate more times than required, use suboptimal loop constructs, or fail to terminate correctly | `reference/categories/C3.md` (7) |
| **C4** | Inefficient Control Flow | Energy waste from branching, conditions, or dispatch logic that performs unnecessary checks, uses suboptimal evaluation order, or employs patterns that prevent interpreter optimization | `reference/categories/C4.md` (8) |
| **C5** | Suboptimal Data Structures | Energy waste from choosing, provisioning, or converting data structures that do not match the workload's access pattern or size requirements | `reference/categories/C5.md` (4) |
| **C6** | Unnecessary Memory Usage | Patterns that allocate, copy, retain, or leak memory beyond what the workload requires, increasing garbage collection overhead, memory-bus traffic, and system energy consumption | `reference/categories/C6.md` (7) |
| **C7** | Suboptimal Algorithmic | Energy waste from choosing an algorithm, decomposition, or computation strategy that explores more of the problem space than necessary or uses higher complexity than the problem requires | `reference/categories/C7.md` (5) |
| **C8** | Missing Reuse | Energy waste from failing to store and reuse results of expensive computations, lookups, or data fetches, causing the same work to be repeated across calls, requests, or access sites | `reference/categories/C8.md` (4) |
| **C9** | Inefficient External Data Access | Energy waste from inefficient interaction with external systems: databases, file systems, network services, and APIs | `reference/categories/C9.md` (4) |
| **C10** | Underused Language Primitives | Energy waste from not using available optimized language features, standard library functions, or runtime-specific constructs that would accomplish the same task more efficiently | `reference/categories/C10.md` (6) |
| **C11** | Inefficient Concurrency Management | Energy waste from thread/task misuse, synchronization overhead, contention, or failure to exploit available parallelism | `reference/categories/C11.md` (5) |
| **C12** | Poor Hardware Locality Usage | Energy waste driven by CPU and memory hierarchy behavior such as cache misses, branch misprediction, and suboptimal memory access patterns | `reference/categories/C12.md` (4) |

Full index, including the level-1 and level-2 card paths:
`$SKILL/reference/README.md`.

---

## How this goes wrong

Six failure modes, in the order they actually happen:

1. **Deciding from the label.** "Nested loops, so it must be an algorithmic
   complexity problem." Open the card; most of them are narrower than the name.
2. **One label dominating.** If a third of your findings share a root cause,
   you are pattern-matching. Re-derive them from the code.
3. **Splitting one repair into several findings.** One edit, one finding, one
   root cause; the rest are `subsumed`.
4. **Ignoring context.** Every pattern in this taxonomy is the right call
   somewhere. A bare `except` in a retry loop, a materialised list that gets
   indexed twice, a wrapper that is public API. That is what the cards'
   exception sections are for, and skipping them is the fastest way to produce
   confident nonsense.
5. **Skipping measurement because the smell is obvious.** The obvious ones are
   exactly where a wrong assumption about hotness hides.
6. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to one root cause. Keep the edit inside the card's patch shape — that bounds
   what you *change*, never what you are allowed to read.

## Scope

Python. Root cause IDs are exactly the 65 on the cards — never invent one, and
never report a bare category as a finding.

A unit is normally a function or a method: it is the granularity at which a
repair is scoped and measured. It is not a limit on how much code you may read,
and it is not a limit on where the waste may live. When the waste is in the
arrangement of several units, say which units it spans and repair the smallest
set that removes it.
