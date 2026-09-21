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

The cards overlap. Two of them might both describe what you repaired, and
when that happens either attribution is fine — say which you chose and that it
was close. What is not fine is filing a repair under a root cause whose
definition it does not match, because then the label is doing no work at all.

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
that is what removes the root cause. Name every unit you touched in
`spans_units`.

What you may not do is bring anything else along. A patch that also renames
variables, tidies an unrelated branch, or fixes a second smell cannot be
attributed to any one root cause, and the measurement stops meaning anything.
The second smell is a second finding, or it is nothing.

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

Five steps, in order, one unit at a time. Each step states what it takes in and
what it must produce. Produce it before moving on: every step after the second
one is a check on what the second one wrote down, and a check you run against
nothing checks nothing.

### 1. Select — *in:* a path · *out:* the units you will examine, in order

Rank the units by how much work they are likely to do:

```bash
python $SKILL/scripts/scan.py <path> --units --top 20
```

This orders every function in the target by loop nesting, the nesting of the
callers that reach it, and how many places call it. It says nothing at all
about what might be wrong with any of them — that comes later, on purpose.

The ordering is a guess made from syntax. It cannot see how many times a loop
actually trips, which branches are taken in practice, or anything about calls
from other files. So read the repository too — its entry points, what its tests
exercise, what its README says it is for — and override the order wherever you
know better.

Examine at least 10 units, or all of them if the target has fewer.

```jsonc
{
  "units_ranked": 128,
  "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize"],
  "order_changed": "promoted `parse_row`: cli.py calls it once per input line"
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
python $SKILL/scripts/scan.py <path>              # index: which units, how much
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

Each fact carries one number: **what this repair measured elsewhere.** It is the
mean energy saved across our own benchmark shapes for that root cause, with
shapes where the repair did not pay counted as zero. So 0% does not mean
unmeasured — it means measured and it did not reliably pay.

That number orders the list and decides nothing else. It is a prior from other
code, not a prediction for this code: a 5% repair inside a loop that runs a
billion times beats a 90% one that runs twice, and which is which is exactly the
part you can see and the rule cannot.

There is no confidence score, deliberately. Every one of these shapes is the
right thing to write somewhere, so none of them is graded as more or less likely
to be a real smell — that judgement is yours, made against this code, and a
label claiming to have made it for you would only be in the way.

Two things follow from what a rule is, and they point in opposite directions.

**It reports shapes, so some of what it reports is wrong.** Every pattern here
is the right thing to write somewhere. Whether it is right *in this code*
depends on what the code is for, what the author was constrained by, and how
often it runs — three things you can read and the rule cannot. Expect false
positives and say so when you find one.

**It only knows shapes somebody described in advance, so it misses the rest.**
Waste that lives in the arrangement of a program has no fixed syntax and leaves
no trace here however expensive it is. Silence from this tool is not evidence of
anything.

So reconcile it against the list you already wrote, and keep your own judgement:

- **it agrees with you** — you now have two independent reasons;
- **it saw something you did not** — read that code again and decide for
  yourself. Being pointed at a line is not being told it is wrong;
- **it flags something you judged fine** — you may well be right. Keep your
  judgement and record why;
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

Open `$SKILL/reference/root-causes/<ID>.md` for every suspicion.

**Read the whole card**, not the section whose heading matches your question.
The description at the top, `What to look for`, the exceptions, the
near-misses, the repair examples — all of it is evidence about whether this is
the right root cause. The near-misses decide the hard cases, and the repair
examples are where you find out what the edit actually involves, which is
usually not what the name suggested.

Now settle each suspicion. It carries forward as the same object, with its
values corrected wherever the card taught you better, plus the verdict. You may
change any of them:

- **`root_cause`** — a card in the `Similar root causes` list fitted better.
  Open those; that is what they are there for.
- **`lines`** — the card made clear the real site is somewhere else. The
  membership test you flagged is a symptom; the line the repair changes is
  where the container is built.
- **`why`** — rewritten against the card, instead of your first impression.

Record the change and the reason for it, so the report shows the reading
happened.

The list may also **grow** here. Opening one card and following its similar
list is one of the better ways to find a root cause nobody suspected. When that
happens, add it with `found_by: "cards"` and hold it to exactly the same
checks. Step 2's cap does not apply here — a rejection with a reason is as
much a result as an acceptance.

**Each card ends with the same five checks**, in a line apiece. What each one
is actually asking:

1. **Say what the machine does here that it need not do**, in your own words,
   naming the lines. If you cannot say it without the card's words, you have
   matched a shape rather than found something.
2. **Apply `NOT a smell when` and `Looks the same, is not`.** These are the
   cases where the pattern is present and correct, and they are the most
   valuable thing on the card. If one fits, reject and record which.
3. **Write the repair for *this* code**, not the card's example. No repair, no
   finding — and the repair is also where you discover that the card did not
   quite fit.
4. **Check the repair removes what this root cause names**, and not something
   adjacent. If what you actually fixed is better described by a similar card,
   file it there and say so.
5. **Say how often the code runs, and how large its inputs get.**

The fifth rejects more candidates than the other four together, and it costs
nothing here. A real pattern on a path that runs eleven times per process is
not a finding, and it is much cheaper to establish that now than after you have
built a case file.

```jsonc
[
  {
    "root_cause": "C5.S1", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request; built in __init__ at line 31",
    "changed_from": {"root_cause": "C5.S2", "lines": [58]},
    "why_changed": "nothing needs the list's order, so the container's type changes rather than an index being added beside it",
    "hotness": "one call per request; `routes` is 400-2000 entries",
    "repair_sketch": "build `self.blocked` as a set",
    "patch_shape": "expression",
    "spans_units": ["src/router.py::Router.__init__"],
    "found_by": "reading"
  },
  {
    "root_cause": "C3.S4", "lines": [58], "verdict": "rejected",
    "why_rejected": "check 5 — `handle` runs once per process, over the static route table",
    "found_by": "rules"
  }
]
```

### 4. Repair and measure — *in:* accepted candidates · *out:* a verdict each

**Order them before you start.** Sort by how much of the code the repair moves:
`cross_unit` and `structural` first, then `signature`, then `statement_local`,
then `expression`. Big repairs dissolve small ones — a search rewritten from
scratch takes the redundant conversion inside it with it — so doing the small
ones first means measuring work that was about to disappear anyway.

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
4. **Then go back to step 3 with what is left.** Re-read the repaired unit and
   re-open the cards for every remaining accepted candidate. This is a real
   re-decision, not a formality:
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
   to one root cause. Change what removes the root cause and stop.

## Scope

Python. Root cause IDs are exactly the 65 on the cards — never invent one, and
never report a bare category as a finding.

A **unit** is a function or a method. That is the granularity at which units are
ranked, cleared and reported, and at which a repair is measured — a case file
calls something, and this is the something.

That is all it bounds. Read as far as you need in either direction, and
repair across as many units as the root cause requires. When the waste exists
only in the arrangement — two methods of a class that each look
reasonable and are wrong together, a helper whose shape forces its four callers
to compensate — report it against the unit where you would make the edit, and
name the rest in `spans_units`.
