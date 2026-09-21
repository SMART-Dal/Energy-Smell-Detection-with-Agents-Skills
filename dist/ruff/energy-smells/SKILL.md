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

> A finding is a **repair**: a concrete edit to *this* code, attributed to a
> root cause whose definition the edit matches, and measured.

Three consequences you have to hold onto:

- **No repair, no finding.** If you cannot write the actual edit for this code,
  you have not found anything — you have recognised a pattern.
- **No measurement, no claim.** Step 4 is not optional. A claim nobody tested
  is worth nothing.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It goes in the report.

## One repair, one root cause

Attribute each repair to one root cause: the one whose definition describes the
waste your edit removes. That is a rule about *attribution*, not about counting,
and it is not a demand that you find a uniquely correct label.

The cards overlap. Two of them might both describe what you repaired, and when
that happens either attribution is fine — say which you chose and that it was
close. What is not fine is filing a repair under a root cause whose definition
it does not match, because then the label is doing no work at all.


Repairs overlap too, and more consequentially. Fixing how a function searches
can make a redundant conversion, a needless copy and a hoistable lookup all
disappear at once, because they only existed to serve the search. When that
happens:

- report **one** finding, for the repair you actually made;
- list the other candidates under `subsumed`, and say they went away;
- do **not** widen the repair to cover extra candidates, and do not split one
  edit into several findings to raise the count.

Two agents that report three and seven candidates for the same function have
not necessarily disagreed. What they must both do is say which candidates
turned into repairs, and which were absorbed by another repair.

## How much you may change

Each card names a patch shape. It bounds the **size** of the edit, never its
location, and never how much code you may read to decide.

So you may edit more than one function when that is where the waste lives. A
value shaped wrongly by its producer and compensated for by three consumers is
one repair, made in the producer. A list built in `__init__` and searched in a
method is one repair, made in `__init__`. Moving work between a caller and a
callee, or changing a helper's signature and its call sites, is allowed when
that is what removes the waste. Name every unit you touched in
`spans_units`.

What you may not do is bring anything else along. A patch that also renames
variables, tidies an unrelated branch, or fixes a second problem cannot be
attributed to one root cause, and the measurement stops meaning anything. The
second problem is a second finding, or it is nothing.

## What is not energy smells

**Style.** Unreadable, undocumented, poorly named, badly typed code is not
an energy smell. If the repair does not change what the machine does, it
is out of scope here.

Everything else that wastes work is in scope. Record how hot the code is,
because it tells a reader how much the saving is worth — but a real repair on a
cold path is still a real repair, and the measurement will say what it came to.

## Energy is not time

They usually move together, but not always. Spreading work across cores cuts
wall-clock time while raising energy. A busy-wait poll burns power while making
no progress. A blocked event loop keeps a core hot for nothing. Judge energy,
and when the two diverge, say so — those cases are the most interesting ones
you can find.

---

## Procedure

Five steps, in order, one unit at a time. Each step states what it takes in and
what it must produce. Produce it before moving on: every step after the second
one is a check on what the second one wrote down, and a check you run against
nothing checks nothing.

### 1. Select — *in:* a path · *out:* the units you will examine, in order

Choose the units yourself.

Read the repository first: its entry points, what its tests exercise, what its
README says it is for. Then pick the units where energy is actually spent, in
this order of priority:

1. **work that repeats** — the deepest loop nests, and the helpers those loops
   call, which is where a cheap-looking function gets paid thousands of times;
2. **work proportional to input size**, rather than to a fixed constant;
3. **the repository's own hot path** — what it benchmarks, what its main entry
   point spends its time in.

`python $SKILL/scripts/scan.py <path> --units --top 20` will also list the
units, ordered by loop nesting and how many places call them. It is a guess
made from syntax and says nothing about what might be wrong with any of them,
so treat it as a second opinion on the order rather than the order itself.

**Order them by how much energy you expect a repair to save**: how often the
unit runs, multiplied by how much work one run does. Examine at least 10 units,
or all of them if the target has fewer.

```jsonc
{
  "units_considered": 128,
  "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize"]
}
```

Keep this list. Every unit on it appears in the final report, including the
ones you clear — a run that examined three functions and one that examined
three hundred have to be distinguishable.

### 2. Read and suspect — *in:* one unit · *out:* one record, with `suspicions[]`

Work through the sub-steps in the order given. That order is the whole point:
you write down what you think before anything tells you what to think.

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

Read outward because the expensive waste is not in any one line. Some waste
is — a conversion, a lookup, a concatenation — and you can see it where it
sits. The larger kind is in the *arrangement*: a value computed in one place
and thrown away in another; a shape chosen early that every later step has to
compensate for; six functions doing what a different split does in two; a
result recomputed on each of three paths that each look reasonable alone. No
single statement shows any of it.

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
suggests them. Nothing restricts which you may consider.

**2d. Now, and only now, run the rules.**

```bash
python $SKILL/scripts/scan.py <path>              # index: which units, what was seen
python $SKILL/scripts/scan.py <path> --unit NAME  # one unit's findings in full
```

The first command prints an **index** and writes the detail to a file. That is
deliberate: read the index, pick the units you already care about, and open
those. Do not open every unit, and do not read the detail file end to end — the
whole of it is longer than your account of the code should be, and a list read
in full becomes the account instead of checking it.

This is an assistant, not an authority. It applies a fixed set of deterministic
rules and reports **facts** — "a string is grown with `+=` inside a loop at line
45" — one entry per rule per unit, tagged with every root cause that fact could
point at. Two labels on one fact means the shape alone does not say which; it is
one thing to look at, not two.

The list comes in a pre-computed order, based on what these repairs measured on
other code. It is a starting point and nothing more — read in whatever order you
think right. There is no confidence score and no per-finding number, because
either would be a judgement about this code that the rule is in no position to
make.

Two things follow from what a rule is, and they point in opposite directions.

**It reports shapes, so some of what it reports is wrong here.** Whether a
pattern is waste depends on what the code is for, what the author was
constrained by, and how often it runs — none of which a rule can see. Be
careful, and spend your time on the ones you can show are real.

**It only knows shapes somebody described in advance, so it misses the rest.**
Waste that lives in the arrangement of a program has no fixed syntax and leaves
no trace here however expensive it is. Silence from this tool is not evidence of
anything.

So reconcile it against the list you already wrote, and keep your own judgement:

- **it agrees with you** — you now have two independent reasons;
- **it saw something you did not** — read that code again and decide for
  yourself. Being pointed at a line is not being told it is wrong;
- **it flags something you judged fine** — you may well be right. Keep your
  judgement and move on;
- **it is silent where you are suspicious** — that means nothing at all. Keep
  the suspicion and carry it forward.

Add `found_by` to every suspicion: `"reading"`, `"rules"`, or `"both"`.

**2e. Sweep the full index for what you have not named.**

Read `$SKILL/reference/README.md`, which lists all sixty-five root causes with
one line each. Go down it once, against this unit, asking a single question:

> is any of these happening here, that I have not already written down?

You are looking for two things in particular. Waste you *noticed* while reading
but could not name, which is what this index is for. And waste you did not
notice at all, where the one-line description makes you go back and look.

Add anything you find to `suspicions` with `found_by: "sweep"`. Do not revise
anything already on the list, and do not drop items because the sweep did not
independently produce them — the point of doing this last is that your own
reading stays the primary account and this only adds to it.

Expect most sweeps to add nothing. That is a normal outcome and not a sign you
did it wrong.

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

`found_by` says how you came to suspect it, and is recorded honestly:
`"reading"` from 2a–2b, `"rules"` from a tool, `"both"`, or `"sweep"` from the
index pass. It is the difference between an analysis you did and a list you
were handed.

**At most 12 suspicions per unit.** The cap makes you rank rather than list. If
you are at the cap, keep the ones you would actually spend an hour repairing.

### 3. Decide — *in:* `suspicions[]` · *out:* the same list, each one accepted or rejected

Open `$SKILL/reference/root-causes/<ID>.md` for every suspicion, and read the
whole card. The exceptions and the near-misses decide the hard cases, and the
repair examples are where you find out what the edit actually involves.

Every suspicion ends this step **accepted** or **rejected**, and nothing is
edited in place. If the card says a suspicion belongs somewhere else, reject it
and add a new one for the root cause that fits, with `found_by: "cards"`. That
keeps what you first thought on the record, which is the part worth reading
later.

The list may also **grow** here: following a card's similar list is one of the
better ways to find a root cause nobody suspected. Step 2's cap does not apply,
and a rejection with a reason is as much a result as an acceptance.

**For each suspicion:**

1. **Does it apply here?** Does the card's definition describe what this code
   does — not something adjacent? Apply `NOT a smell when` and `Looks the same,
   is not`; if one of them fits, reject and name it. If a card in
   `Similar root causes` fits better, reject this one and add that.
1. **Can you write the repair for *this* code**, as an edit rather than a
   rewrite of the unit? No repair, no finding.
1. **Does the repair preserve behaviour** on every input, including the edge
   cases and whatever the callers rely on?
1. **State the mechanism** — what work stops happening, and why that costs
   less. "Built-ins are faster" is not a mechanism, and it is wrong often
   enough to matter.
1. **Say how often the code runs, and how large its inputs get.** Recorded, not
   a bar to clear: it tells a reader what the saving is worth, and it tells you
   how to size the case file in step 4.

Accept if all of them hold. Otherwise reject, and name the one that decided it.

```jsonc
[
  {
    "root_cause": "C5.S1", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request; built in __init__ at line 31",
    "hotness": "one call per request; `routes` is 400-2000 entries",
    "repair_sketch": "build `self.blocked` as a set",
    "patch_shape": "expression",
    "spans_units": ["src/router.py::Router.__init__"],
    "found_by": "reading"
  },
  {
    "root_cause": "C5.S2", "lines": [58], "verdict": "rejected",
    "why_rejected": "`NOT a smell when` — nothing needs the list's order, so the container's type changes rather than an index being added beside it. Added C5.S1 instead.",
    "found_by": "reading"
  }
]
```

### 4. Repair and measure — *in:* accepted candidates · *out:* a verdict each

**Order them before you start.**
Sort by how much of the code the repair moves: `cross_unit` and `structural`
first, then `signature`, then `statement_local`, then `expression`.
Big repairs dissolve small ones — a search rewritten from scratch takes the
redundant conversion inside it with it — so doing the small ones first means
measuring work that was about to disappear anyway.

Then, one candidate at a time:

1. **Write the repair** as you would commit it.
2. **Write the case file and measure it.** Read `$SKILL/reference/verifying.md`
   before your first one. The part that matters most is that `before` is this
   repository's function copied, not a small illustration of the pattern: a
   repair worth 30% of a five-line sketch can be worth 2% of the real function,
   and the sketch will not tell you which you have.

   ```bash
   python $SKILL/scripts/verify.py cases/case_C10S4.py
   ```

3. **If it is confirmed, apply it** to the working copy.
4. **Then go back to step 3 with what is left.** Re-read the repaired unit,
   then re-open the cards for every remaining accepted
   candidate.
   This is a real re-decision, not a formality:
   - candidates that no longer apply are `subsumed` by the repair that removed
     them. Record them there and **do not measure them** — the code they
     described is gone;
   - candidates that still apply keep their place in the queue, and their
     `lines` may have moved;
   - a candidate can also be *created* by a repair. Add it and decide it.

Repeat until the queue is empty.

Root causes marked **advisory only** on their card are exempt from measurement:
their repair is worth a single bytecode instruction and cannot clear any noise
floor. Report them as `advisory`, and do not build a case file.

### 5. Report — *in:* verdicts · *out:* `findings.json` + `REPORT.md`

Write the JSON first and the report from it.
`$SKILL/reference/output-format.md` has the exact schema.

The report has to carry the negative results as well as the positive ones: what
was negligible, what the host could not resolve, what each repair subsumed, and
every unit you cleared. A run that only lists what it found cannot be
distinguished from a run that only looked where it expected to find something.

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

Full index, with one line per root cause: `$SKILL/reference/README.md`.

---

## How this goes wrong

Failure modes, in the order they actually happen:

1. **Deciding from the label.** "Nested loops, so it must be an algorithmic
   complexity problem." Open the card; most of them are narrower than the name.
1. **One label dominating.** If a third of your findings share a root cause,
   you are pattern-matching. Re-derive them from the code.
1. **Repeating what you have read about Python performance.** Much of it is
   out of date, and some of it was never true. Every claim here gets measured,
   and the ones you are most certain about are the ones worth measuring first.
1. **Splitting one repair into several findings.** One edit, one finding,
   one root cause; the rest are `subsumed`.
1. **Ignoring context.** Almost every pattern that looks wasteful is the right
   call somewhere. A bare `except` in a retry loop, a materialised list that
   gets indexed twice, a wrapper that is public API.
   That is what the cards' exception sections are for, and skipping them is
   the fastest way to produce confident nonsense.
1. **Skipping measurement because the waste is obvious.** The obvious ones are
   exactly where a wrong assumption about hotness hides.
1. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to one root cause, and cannot be measured against one. Change what removes
   the waste and stop.

## Scope

Python. Root cause IDs are exactly the 65 on the cards — never invent one, and
never report a bare category as a finding.

A **unit** is a function or a method. That is the granularity at which units are
ranked, cleared and reported, and at which a repair is measured — a case file
calls something, and this is the something.

That is all it bounds. Read as far as you need in either direction, and
repair across as many units as the waste requires. When the waste exists
only in the arrangement — two methods of a class that each look
reasonable and are wrong together, a helper whose shape forces its four callers
to compensate — report it against the unit where you would make the edit, and
name the rest in `spans_units`.
