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
- **No measurement, no claim.** Step 4 is not optional. This taxonomy has
  sixty-five plausible-sounding labels, which is more than enough to justify
  anything after the fact. A claim nobody tested is worth nothing.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It goes in the report.

## One repair, one root cause

Attribute each repair to one root cause: the one whose definition describes the
waste your edit removes. That is a rule about *attribution*, not about counting,
and it is not a demand that you find a uniquely correct label.

The cards overlap. Two of them will often both describe what you repaired, and
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

{{STEP_SELECT}}
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

{{STEP_EVIDENCE}}{{STEP_SWEEP}}**Output of this step.** For each unit, one record:

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

**Read the whole card.** The description at the top, `What to look for`, the
exceptions, the near-misses, the repair examples: all of it is evidence about
whether this is the right root cause, and the examples in particular are where
you find out what the repair actually involves. A card read only for the
section that sounds like a checklist has been used as a label, not as
knowledge.

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
checks. Step 2's cap does not apply to this step: narrowing is not the goal,
and a rejection carrying a reason is as much a result as an acceptance.

**Each card ends with five checks.** Work through them. In summary: say in your
own words what the machine is doing that it need not do; apply the `NOT a smell
when` clauses and the `Looks the same, is not` cases; write the repair for
*this* code; confirm the repair removes what this root cause names rather than
something adjacent; and say how often the code runs.

The last one rejects more candidates than the rest put together, and it costs
nothing to apply here. A real pattern on a path that runs eleven times per
process is not a finding, and finding that out now is much cheaper than finding
it out after you have built a case file.

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
was refuted, what the host could not resolve, what each repair subsumed, and
every unit you cleared. A run that only lists what it found cannot be
distinguished from a run that only looked where it expected to find something.

---

## Categories

{{CATEGORY_INDEX}}

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

It is not a boundary on anything else. Read as far as you need in either
direction. Repair across as many units as the root cause requires. And when the
waste exists only in the arrangement — two methods of a class that each look
reasonable and are wrong together, a helper whose shape forces its four callers
to compensate — report it against the unit where you would make the edit, and
name the rest in `spans_units`.
