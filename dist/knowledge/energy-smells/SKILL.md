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

**Time:** you have 60 minutes for the whole run, thinking and measuring
included, and the session is stopped at 60. That is enough to be thorough, so
do not rush: give each unit the reading it needs, and keep enough of the hour
for step 4, where measuring takes about a minute a repair. Run `date` when you
start and again as you go, so you know how much of the hour is left.

---

## What counts as a finding

> A finding is a **repair**: a concrete edit to *this* code, attributed to a
> root cause whose definition the edit matches. That it saves energy is a
> separate claim, and only a measurement makes it.

Three consequences you have to hold onto:

- **No repair, no finding.** If you cannot write the actual edit for this code,
  you have not found anything — you have recognised a pattern.
- **No measurement, no claim.** A repair is said to save energy only once it
  has been measured. One left unmeasured is still a finding — with no claim
  attached to it.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It stays in `submissions.jsonl`, with its verdict.

## One repair, one root cause

Attribute each repair to one root cause: the one whose definition describes the
waste your edit removes. That is a rule about *attribution*, not about counting,
and it is not a demand that you find a uniquely correct label.

The cards overlap. Two of them might both describe what you repaired, and when
that happens either attribution is fine — say which you chose and that it was
close. What is not fine is filing a repair under a root cause whose definition
it does not match, because then the label is doing no work at all.

One unit can have several repairs, and they can overlap: fixing how a function
searches can make a redundant conversion and a needless copy disappear too,
because they only existed to serve the search. The rule is the same either
way — **every accepted suspicion gets its own repair, written against the
original code, and its own measurement.** That is what says what each one is
worth on its own.

- Two suspicions that would get **exactly the same edit** are one repair:
  submit it once, and record the other as `same_repair_as`.
- Two that get **different edits to the same code** are two repairs: submit
  both, and list each in the other's `related`.
- Do **not** widen a repair to cover a second suspicion, and do not split one
  edit into several submissions to raise the count.

Since each repair is written against the original, at most one per function
can ever be applied. Choosing it is not part of your job: submit every repair,
measured, and the measurements decide.

## How much you may change

The edit should be as small as removing the waste allows. That bounds its
**size**, never its location, and never how much code you may read to decide.

**What must survive is the unit's contract**: the same return value, the same
effect on its arguments, the same output, the same exception type. That is what
gets checked, and it is the whole of what callers are entitled to.

Anything **only the unit depends on** is implementation detail: a helper
nothing else calls, state nothing else reads. You may change a helper's
signature, its return shape or its behaviour, if that is what removes the
waste. A list built in `__init__` and searched only in this method is one
repair, made in both. A value shaped wrongly by a producer and compensated for
by its consumers is one repair, made in all of them — when nothing but the unit
reaches them.

Two obligations come with reaching outside the unit:

- **Give every function you change its own entry** in the submission, named
  `path::qualname`, in whichever file it lives.
- **Establish that nothing else depends on what you changed** — no other
  caller of a changed function, no other reader of changed state — and say how
  in `sole_caller_evidence`. Anything else that depends on it is not
  implementation detail: the change reaches it too, and the check on this unit
  would not notice.

What you may not do is bring anything else along. A patch that also renames
variables, tidies an unrelated branch, or fixes a second problem cannot be
attributed to one root cause, and the measurement stops meaning anything. The
second problem is a second finding, or it is nothing.

## What is not an energy smell

**Style.** Unreadable, undocumented, poorly named, badly typed code is not
an energy smell. If the repair does not change what the machine does, it
is out of scope here.

Everything else that wastes work is in scope, wherever it is in the program:
a real repair is a real repair, and the measurement will say what it came to.

## Energy is not time

They usually move together, but not always. Spreading work across cores cuts
wall-clock time while raising energy. A busy-wait poll burns power while making
no progress. A blocked event loop keeps a core hot for nothing. Judge energy,
and when the two diverge, say so — those cases are the most interesting ones
you can find.

---

## Procedure

Five steps, in order. **Each step writes its own file in the repository's
root, and when the step is finished you say so** — then the next step begins:

| Step | Writes | When it is finished |
|---|---|---|
| 1. Select | `step1.jsonl` | `python $SKILL/scripts/step.py done 1` |
| 2. Read and suspect | `step2.jsonl` | `python $SKILL/scripts/step.py done 2` |
| 3. Decide | `step3.jsonl` | `python $SKILL/scripts/step.py done 3` |
| 4. Repair and measure | `submissions.jsonl`, `step4.jsonl` | `python $SKILL/scripts/step.py done 4` |
| 5. Finish | your final message | — |

While a step is open, its file is yours: write it, rewrite it, fix it. `done`
keeps the file, outside this session, as that step's output, and makes it
read-only — a finished step is never changed. If a later step shows you
something an earlier one missed, say so in the later step's file: step 3
rejects a step-2 suspicion and adds a new one; it does not touch
`step2.jsonl`. Do not start a step's file before the previous step is done.
The root-cause
cards open at `done 2`, all of them. `inputs.py` runs from `done 2`, and
`verify.py` between `done 3` and `done 4`.

Every step after the second one is a check on what the second one wrote down,
and a check you run against nothing checks nothing.

Each record is one JSON line with **exactly the keys its example below shows —
all of them, and no others**; a key with nothing to say is `null` or `[]`.
`$SKILL/reference/output-format.md` lists every key and what it holds. Every
file goes in the repository's root, the directory you were started in —
nowhere else.

### 1. Select — *in:* a target · *out:* the units you will examine

**The target** is what you were asked to look at: the whole repository, a
directory, a file, or a single unit. Choose units only from inside it; read
outside it as far as you need. A unit named loosely — "the render function" —
is yours to pin down: find it, and record the exact `path::qualname` it
resolved to. If more than one function matches, all of them are the target.

Read the repository first — its entry points, what its tests exercise, what
its README says it is for — so that you know what each part of it is for.

**Then go through every unit in the target** and pick out each one where
something looks inefficient to you: work the program does not need, work done
more often than necessary, or work done in a more expensive way than its result
requires. Those are the units you will examine. Nothing limits how many units
you pick or how many smells you report — one, ten, a hundred or a thousand,
whatever the code holds. Within a unit, record every suspicion you have.

**Every unit gets a decision, written down.** The ones you pick go in
`will_examine`; every other unit of the target goes in `passed_over`, with a
few words on why nothing in it looked inefficient. Together the two lists hold
every unit of the target, each once — a unit in neither was not passed over, it
was missed.

If you were asked for a number of units, examine at most that many. You may
change which units those are until you finish step 1; just do not go over the
number.

```jsonc
{"step": 1, "target": "src/", "unit_limit": null, "units_considered": 128,
 "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize",
                  "src/parse.py::Lexer.advance", "src/index.py::Index.add",
                  "src/index.py::Index.lookup", "src/export.py::write_rows",
                  ...],
 "passed_over": [
   {"unit": "src/cli.py::main", "why": "parses three flags and calls run(); does no work of its own"},
   {"unit": "src/config.py::Config.__init__", "why": "stores four arguments as attributes, once"},
   ...]}   // shortened here: the two lists hold all 128 units, each once
```

Write it to `step1.jsonl`. Rewrite it as often as you like while step 1 is
open; when the list is final, run `python $SKILL/scripts/step.py done 1`.

Keep this list. Every unit in `will_examine` gets a step-2 record, including
the ones you clear — a run that examined three functions and one that examined
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
- **Up, into what calls it.** See what it is given and what is done with what
  it returns: waste can sit between a unit and its callers — a result the
  caller throws away, a shape the caller has to undo.

Then write two sentences: what it computes, and where its work goes.

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
verdicts. The cards belong to step 3, and `$SKILL/reference/root-causes/` is
locked until then — by design, not a fault. It opens, all of it, when you have
finished step 2 and run `python $SKILL/scripts/step.py done 2`, and stays open.

Open the categories your reading pointed you at, and open others if the code
suggests them. Nothing restricts which you may consider.

**2d. Sweep the full index for what you have not named.**

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
  "step": 2,
  "unit": "src/render.py::Report.render",
  "what_it_does": "renders one HTML table from a list of row dicts",
  "cost_driver": "one pass per row, and string building across all rows",
  "own_hypotheses": [
    "the output string is rebuilt on every row",
    "`self.columns` is re-derived inside the row loop and never changes"
  ],
  "suspicions": [
    {"label": "a", "root_cause": "C10.S4", "lines": [47],
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "found_by": "reading"},
    {"label": "b", "root_cause": "C3.S2",  "lines": [44,45],
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row",
     "found_by": "sweep"}
  ],
  "cleared_because": null
}
```

Give each suspicion a `label` — `a`, `b`, `c` — unique within the unit. Steps 3
and 4 refer to it. A unit with nothing suspicious gets the same record with
`"suspicions": []` and `cleared_because` saying why.

`found_by` says how you came to suspect it, and is recorded honestly:
`"reading"` from 2a–2b, or `"sweep"` from the index pass. It is the difference
between an analysis you did and a list you were handed.

**Record every suspicion, however many.** Writing one down costs nothing, and
step 3 is where each is checked: do not hold one back because you are unsure.

Write each unit's record to `step2.jsonl`. When every unit you examine has its
record, step 2 is finished: run `python $SKILL/scripts/step.py done 2`.

### 3. Decide — *in:* `suspicions[]` · *out:* one record, each suspicion accepted or rejected

Start this step after `step.py done 2`, and write a step-3 record to
`step3.jsonl` for every unit with suspicions. As soon as you know a unit will
be repaired, ask for its inputs (step 4, item 2): they take a minute or two to
generate, and are then ready when you measure. When every record is written,
run `python $SKILL/scripts/step.py done 3`; step 4 starts after it.

The root-cause cards are open from `step.py done 2` on. Open
`$SKILL/reference/root-causes/<ID>.md` for every suspicion, and read the whole
card: the reference's definition, common patterns, the measured
repairs, and near-misses.

- **The patterns and repairs are what we tested, not the whole root cause.**
  Real code might look like them, but not necessarily: it is usually longer,
  and the waste — and the repair — can run across several functions or
  classes. Waste the definition describes in a form no pattern or repair shows
  is still a finding.
- **A matching pattern does not guarantee a saving.** The author may have had a
  reason, and the current form may already be the efficient one for this code.
  Understand what the unit does before deciding the repair fits. If you judge
  the current form is better, reject it — or, if you are unsure, accept it and
  let the measurement decide.
- **Each repair ends with what our measurement found, and an action:**
  **Apply the after** — it saved energy; where the code has the *before*, write
  the *after*. **Decide which form fits** — on some inputs the *before* was
  the cheaper form, although the reference gives the *after*. Whichever form
  the code has now, judge from this repository — the code around the unit and
  the inputs it actually receives — whether the *before* or the *after* is
  better here, and measure when you cannot tell. **Report it; no need to measure** — nothing moved on any
  input: accept it if it fits and record it `deferred` in step 4.
  **Measure it** — our host could not resolve it.
- **Near-misses** (`Looks like it, but is not`) have the pattern, and there the
  repair would change what the code does or undo something done on purpose.

Every suspicion ends this step **accepted** or **rejected**, and nothing is
edited in place. If the card says a suspicion belongs somewhere else, reject it
and add a new one, with a new label, for the root cause that fits, with
`found_by: "cards"`. That keeps what you first thought on the record, which is
the part worth reading later.

The list may also **grow** here: reading the cards is one of the
better ways to find a root cause nobody suspected. A rejection with a reason
is as much a result as an acceptance.

**For each suspicion:**

1. **Does it apply here?** Does the card's definition describe what this code
   does — not something adjacent? If one of its near-misses (`Looks like it,
   but is not`) fits, reject and name it. If another root cause fits better,
   reject this one and add that.
1. **Can you write the repair for *this* code**, as an edit rather than a
   rewrite of the unit? No repair, no finding.
1. **Does the repair preserve behaviour** on every input, including the edge
   cases and whatever the callers rely on?
1. **State the mechanism** — what work stops happening, and why that costs
   less. "Built-ins are faster" is not a mechanism, and it is wrong often
   enough to matter.

Accept if all of them hold, and give the mechanism as `why`. Otherwise reject,
and give the check that decided it as `why`.

```jsonc
{"step": 3, "unit": "src/router.py::Router.allowed", "decisions": [
  {
    "label": "a", "root_cause": "C5.S2", "lines": [58], "verdict": "rejected",
    "why": "`Looks like it, but is not` — nothing needs the list's order, so the container's type changes rather than an index being added beside it. Added `c` instead.",
    "found_by": "reading"
  },
  {
    "label": "c", "root_cause": "C5.S1", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request, built in __init__ at line 31 and read nowhere else; as a set each search is one hash lookup",
    "found_by": "cards"
  }
]}
```

### 4. Repair and measure — *in:* every accepted suspicion · *out:* `submissions.jsonl`, measured, and one record per unit

Start this step once every unit has been through step 3, and work from their
step-3 records.

**You do not edit the repository.** You describe each repair; the script
applies it to a copy and reads `before` from the repository as it stands. That
is what makes the baseline something you could not have shaped to suit the
result. Work in a scratch copy of your own if it helps you think, but the
repository you were pointed at stays untouched — and you measure against it,
`--repo .`, never against a copy: a number taken on edited code is discarded.

Read `$SKILL/reference/verifying.md` before your first submission.

1. **Choose what to measure.** Measuring takes under a minute a repair, so at
   most **20** repairs are measured — the ones you expect to save the most
   energy, across all units — unless you were asked to measure all of them, or
   a different number. Every other accepted suspicion is still a finding:
   record it as `deferred` in step 4's record.

2. **Ask for the inputs of every unit you will measure**, if you did not in
   step 3 — all of them in one request.

   ```bash
   python $SKILL/scripts/inputs.py request src/render.py::Report.render src/parse.py::tokenize
   ```

   You do not write the inputs a repair is measured on. A generator outside
   this session writes them for each unit: **four** measured inputs that make
   the unit do substantial and different work, and a few edge inputs checked
   only for identical behaviour. It keeps an input only if it runs on the
   original code and gives the same output twice. The request returns at once
   and generation takes a minute or two, all units together — up to five for a
   hard unit — so ask as soon as you know the units, and write the repairs
   meanwhile. Each unit's file appears in `.energy-inputs/`, read-only: read it
   to see what your repairs will face. You cannot change the inputs; after the
   session, every repair is measured again on our own copy of them.

   `python $SKILL/scripts/inputs.py status` shows which units are ready. A unit
   the generator could not build inputs for — it needs the network, a service,
   hardware — is listed as `failed` with the reason; its suspicions are
   `blocked`, with that reason.

3. **For each chosen suspicion, write the smallest repair of the original
   code** that removes its waste, as one line in `submissions.jsonl`. Every
   repair is written against the code as it is now, never on top of another —
   so the order does not matter, and nothing you submit changes what the next
   one is written against.
   - **The same edit as one you already wrote** for this unit: do not submit it
     again. Record its outcome in step 4 as `same_repair_as`, with that
     submission's `id` as `submission`.
   - **A different edit to the same code**: submit it, and list each in the
     other's `related`.

4. **Measure the whole file, once.**

   ```bash
   python $SKILL/scripts/verify.py submissions.jsonl --repo .
   ```

   It first waits — up to ten minutes, saying for what — for any inputs still
   being generated, then measures every line in turn, under a minute each, on
   its unit's inputs, and writes the result into that line as soon as it is
   measured, as `agent_measurement`: the verdict in `agent_measurement.status`,
   and the joules and seconds of every input. Never write or edit it yourself.
   Give the command a timeout to match, or run it in the background — and if it
   is still running, wait for it before you finish.

5. **Then fix only what is broken, and run the same command again.** It
   measures only the lines that need it.

   | Result | What you do |
   |---|---|
   | `not_equivalent` | the repair changes behaviour: fix that line |
   | `invalid` | the line is malformed, or the inputs do not load against your repair: fix it as the message says |
   | `no_inputs` | the unit has none: request them if you have not, otherwise record `blocked` with the message |
   | `error` | the environment could not run it: do what the message says — install a missing package here and run again, or record `blocked` |
   | `inconclusive` | the host was too noisy; the next run measures it again |
   | `confirmed` `partial` `mixed` `regressed` `negligible` | **final.** Do not touch the line |

   A measured result is never revised. Editing a measured line to get a better
   number makes it `invalid`, and the result it had stays on record. If you
   think a genuinely different repair would do better, that is a new line,
   listed in `related` — both are kept. A suspicion whose repair you cannot make
   behave identically, or whose unit has no inputs, is `blocked`.

6. **Record what happened to every accepted suspicion** in `step4.jsonl`, one
   record per unit:

   ```jsonc
   {"step": 4, "unit": "src/render.py::Report.render", "outcomes": [
     {"label": "a", "outcome": "submitted",      "submission": "C10S4-render-concat", "why": null},
     {"label": "b", "outcome": "same_repair_as", "submission": "C10S4-render-concat", "why": null},
     {"label": "c", "outcome": "blocked",        "submission": null, "why": "every input needs a live database connection"},
     {"label": "d", "outcome": "deferred",       "submission": null, "why": "outside the 20 repairs measured"}
   ]}
   ```

Every measured repair stays in `submissions.jsonl`, whatever its verdict —
one you delete is still measured after the session. `partial`, `negligible`,
`regressed` and `mixed` are results, and a file that kept only the wins could
not be told apart from one that hid its losses.

7. **Check, then finish the step.** Every suspicion accepted in step 3 has an
   outcome in `step4.jsonl`, and every line of `submissions.jsonl` carries the
   `agent_measurement` the script wrote, with nothing left `inconclusive` or
   `error` that a run could still settle. Then run
   `python $SKILL/scripts/step.py done 4`.

### 5. Finish — *in:* the four steps' files · *out:* a short summary

This step writes no file. End with a short summary for whoever asked: for each submission, the unit,
its root cause, the verdict, and what it saved across its four inputs. Lead
with what was confirmed, say plainly what was not, and say how many accepted
suspicions were deferred unmeasured.

`$SKILL/reference/output-format.md` has the exact shape of every file.

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
1. **Submitting one edit twice.** One edit is one repair, attributed to
   one root cause; another suspicion it also fixes is `same_repair_as`.
1. **Building one repair on top of another.** Every repair is written against
   the original code. One written against your previous repair is measured
   against code that does not exist.
1. **Ignoring context.** Almost every pattern that looks wasteful is the right
   call somewhere. A bare `except` in a retry loop, a materialised list that
   gets indexed twice, a wrapper that is public API.
   That is what the cards' near-misses are for, and skipping them is the
   fastest way to produce confident nonsense.
1. **Skipping measurement because the waste is obvious.** The obvious ones are
   exactly where a wrong assumption hides.
1. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to one root cause, and cannot be measured against one. Change what removes
   the waste and stop.
1. **Changing more than the unit without checking what else depends on it.**
   The check watches the unit's contract, so another caller or another reader
   of the changed state breaks silently.

## Scope

Python. Root cause IDs are exactly the 65 on the cards — never invent one, and
never report a bare category as a finding.

A **unit** is a function or a method. That is the granularity at which units are
examined, cleared and reported, and at which a repair is measured — the cases
call something, and this is the something. A function defined inside another
function is not one: nothing can call it on its own, so the function around it
is the unit.

That is all it bounds. Read as far as you need in either direction, and
repair across as many units as the waste requires. When the waste exists
only in the arrangement — two methods of a class that each look
reasonable and are wrong together, a helper whose shape forces the code around
it to compensate — report it against the unit whose behaviour the repair must
preserve, and give every function you change its own entry in the submission.
