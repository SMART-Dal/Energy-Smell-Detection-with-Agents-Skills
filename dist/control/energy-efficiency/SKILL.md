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
  you have not found anything — you have recognised a pattern.
- **No measurement, no claim.** Step 4 is not optional. A claim nobody tested
  is worth nothing.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It goes in the report.

## One repair, one reason

Attribute each repair to a single reason: the thing about the code that
explains why the edit saves energy.


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

The edit should be as small as removing the waste allows. That bounds its
**size**, never its location, and never how much code you may read to decide.

So you may edit more than one function when that is where the waste lives. A
value shaped wrongly by its producer and compensated for by three consumers is
one repair, made in the producer. A list built in `__init__` and searched in a
method is one repair, made in `__init__`. Moving work between a caller and a
callee, or changing a helper's signature and its call sites, is allowed when
that is what removes the waste. Name every unit you touched in
`spans_units`.

What you may not do is bring anything else along. A patch that also renames
variables, tidies an unrelated branch, or fixes a second problem cannot be
attributed to one reason, and the measurement stops meaning anything. The
second problem is a second finding, or it is nothing.

## Two things that are not energy waste

**Style.** Unreadable, undocumented, poorly named, badly typed code is not
energy waste. If the repair does not change what the machine does, it
is out of scope here.

**Cold code.** A wasteful pattern in a function called once at import time
wastes
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

**2b. Say what looks wasteful, in your own words, before naming it.** Just:
which work here does not need to happen, is done more often than necessary, or
is done in a more expensive way than the result requires? Write this down — it
goes in the output as `own_hypotheses`.

This is the only defence against reading code through a label you have already
picked, and it only works if you do it first and record it.

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
    {"lines": [47],    "confidence": "high",
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "found_by": "reading"},
    {"lines": [44,45], "confidence": "medium",
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row",
     "found_by": "reading"}
  ]
}
```

**At most 12 suspicions per unit.** The cap makes you rank rather than list. If
you are at the cap, keep the ones you would actually spend an hour repairing.

### 3. Decide — *in:* `suspicions[]` · *out:* the same list, each one accepted or rejected

Not everything wasteful is worth repairing, and this is where that gets
settled. Read the unit a second time, now with the repair in mind: what the
edit would have to be is usually what tells you whether your first reading of
the waste was right.

Each suspicion carries forward as the same object, with its values corrected
wherever the second reading taught you better, plus the verdict. You may change
any of them:

- **`lines`** — the second reading made clear the real site is somewhere else.
  The membership test you flagged is a symptom; the line the repair changes is
  where the container is built.
- **`why`** — rewritten against the code, instead of your first impression.

Record the change and the reason for it, so the report shows the reading
happened.

The list may also **grow** here.
Reading a second time to write a repair is one of the better ways to notice
something you missed.
Step 2's cap does not apply here — a rejection with a reason is as much a
result as an acceptance.

**Work through these checks for each suspicion:**

1. **Say what the machine does here that it need not do**, in your own words,
   naming the lines. If you cannot say it without borrowing someone else's
   words, you have matched a shape rather than found something.
1. **Write the repair for *this* code**, as an edit rather than a rewrite of
   the unit. No repair, no finding — and the repair is also where you discover
   that your reading of the code was not quite right.
1. **Check the repair preserves behaviour** on every input, including the edge
   cases and whatever the callers rely on.
1. **State the mechanism** — what work stops happening, and why that costs
   less — rather than appealing to a rule of thumb. "Built-ins are faster" is
   not a mechanism, and it is wrong often enough to matter.
1. **Say how often the code runs, and how large its inputs get.**

The last one rejects more candidates than the rest together, and it costs
nothing here. A real pattern on a path that runs eleven times per process is
not a finding, and it is much cheaper to establish that now than after you have
built a case file.

Record every rejection with the check that decided it.

```jsonc
[
  {
    "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request; built in __init__ at line 31",
    "changed_from": {"lines": [58]},
    "why_changed": "the repair changes where the container is built, not where it is searched",
    "hotness": "one call per request; `routes` is 400-2000 entries",
    "repair_sketch": "build `self.blocked` as a set",
    "spans_units": ["src/router.py::Router.__init__"],
    "found_by": "reading"
  },
  {
    "lines": [58], "verdict": "rejected",
    "why_rejected": "the hotness check — `handle` runs once per process, over the static route table",
    "found_by": "reading"
  }
]
```

### 4. Repair and measure — *in:* accepted candidates · *out:* a verdict each

**Order them before you start.**
Sort by how much of the code the repair moves, largest first.
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
   python $SKILL/scripts/verify.py cases/case_render_concat.py
   ```

3. **If it is confirmed, apply it** to the working copy.
4. **Then go back to step 3 with what is left.** Re-read the repaired unit,
   then re-decide every remaining accepted candidate.
   This is a real re-decision, not a formality:
   - candidates that no longer apply are `subsumed` by the repair that removed
     them. Record them there and **do not measure them** — the code they
     described is gone;
   - candidates that still apply keep their place in the queue, and their
     `lines` may have moved;
   - a candidate can also be *created* by a repair. Add it and decide it.

Repeat until the queue is empty.

### 5. Report — *in:* verdicts · *out:* `findings.json` + `REPORT.md`

Write the JSON first and the report from it.
`$SKILL/reference/output-format.md` has the exact schema.

The report has to carry the negative results as well as the positive ones: what
was negligible, what the host could not resolve, what each repair subsumed, and
every unit you cleared. A run that only lists what it found cannot be
distinguished from a run that only looked where it expected to find something.

---

## How this goes wrong

Failure modes, in the order they actually happen:

1. **Repeating what you have read about Python performance.** Much of it is
   out of date, and some of it was never true. Every claim here gets measured,
   and the ones you are most certain about are the ones worth measuring first.
1. **Splitting one repair into several findings.** One edit, one finding,
   one reason; the rest are `subsumed`.
1. **Ignoring context.** Almost every pattern that looks wasteful is the right
   call somewhere. A bare `except` in a retry loop, a materialised list that
   gets indexed twice, a wrapper that is public API.
   Ask what the author was required to do before deciding they were wrong.
1. **Skipping measurement because the waste is obvious.** The obvious ones are
   exactly where a wrong assumption about hotness hides.
1. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to one reason, and cannot be measured against one. Change what removes
   the waste and stop.

## Scope

Python. A finding is a repair with a reason, not a label.

A **unit** is a function or a method. That is the granularity at which units are
ranked, cleared and reported, and at which a repair is measured — a case file
calls something, and this is the something.

That is all it bounds. Read as far as you need in either direction, and
repair across as many units as the waste requires. When the waste exists
only in the arrangement — two methods of a class that each look
reasonable and are wrong together, a helper whose shape forces its four callers
to compensate — report it against the unit where you would make the edit, and
name the rest in `spans_units`.
