---
name: energy-efficiency
description: Find places where Python code wastes energy, refactor them, and prove the saving by measuring it. Use when asked to analyse code or a repository for energy waste, energy efficiency, power consumption, or wasteful computation.
---

# Energy Efficiency Analysis

You are finding **energy waste**: code that spends energy on work the program
does not need, and that a specific refactoring can remove without changing what
the program does.

**The task is to cover everything you were asked to look at** — every file,
every function and every method — and to report every case you find there, not
a few that turn up early in one or two files. A run that stops after two or
three findings has not done it. Keep going until every file has been read, and
report what you find whether or not it can be measured here.

Paths below are relative to this file's directory — call it `$SKILL`. Work out
what `$SKILL` is once, at the start, and use it throughout.

**Time:** you have 60 minutes for the whole run, thinking and measuring
included, and the session is stopped at 60. That is enough to be thorough, so
do not rush: give each unit the reading it needs, and keep enough of the hour
for step 4, where measuring takes about a minute a repair. Run `date` when you
start and again as you go, so you know how much of the hour is left.

---

## What counts as a finding

> A finding is a **repair**: a concrete edit to *this* code, with a stated
> reason why the edit saves energy. That it does is a separate claim, and only
> a measurement makes it.

Three consequences you have to hold onto:

- **No repair, no finding.** If you cannot write the actual edit for this code,
  you have not found anything — you have recognised a pattern.
- **No measurement, no claim.** A repair is said to save energy only once it
  has been measured. One left unmeasured is still a finding — with no claim
  attached to it.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It stays in `submissions.jsonl`, with its verdict.

## One repair, one reason

Attribute each repair to a single reason: the thing about the code that
explains why the edit saves energy.

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
effect on its arguments and on the module- and class-level values it uses, the
same printed and logged output, the same files, the same exception type. That
is what gets checked, for every repair, and it is the whole of what callers are
entitled to.

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
attributed to one reason, and the measurement stops meaning anything. The
second problem is a second finding, or it is nothing.

## What is not energy waste

**Style.** Unreadable, undocumented, poorly named, badly typed code is not
energy waste. If the repair does not change what the machine does, it
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
`inputs.py` runs
from `done 2`, and `verify.py` between `done 3` and `done 4`.

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

**Then you must go through every file in the target, and every unit in each
file.** List the target's Python files first, so you know what there is to
read, and work through that list file by file, reading every function and
method in each. Do not stop at the first files that turn something up: the
target is not done until every file in it has been read.

**Leave nothing out because of what you expect later.** Code that calls a
network or a service, code you doubt any input could be generated for, a
script, a long file: read it all the same, and pick what looks inefficient in
it. Whether a repair can be measured is step 4's question — ask for its inputs
and let the generator say — and one that cannot is still a finding, recorded
as `blocked` with the message that showed it.

As you read, pick out every unit where something looks inefficient to you:
work the program does not need, work done more often than necessary, or work
done in a more expensive way than its result requires. Those are the units you
will examine. Nothing limits how many units you pick or how many smells you
report — one, ten, a hundred or a thousand, whatever the code holds. Within a
unit, record every suspicion you have.

If you were asked for a number of units, examine at most that many. You may
change which units those are until you finish step 1; just do not go over the
number.

```jsonc
{"step": 1, "target": "src/", "unit_limit": null, "units_considered": 128,
 "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize",
                  "src/parse.py::Lexer.advance", "src/index.py::Index.add",
                  "src/index.py::Index.lookup", "src/export.py::write_rows",
                  ...]}   // shortened here: every unit where something looked inefficient
```

Write it to `step1.jsonl`. Rewrite it as often as you like while step 1 is
open; when the list is final, run `python $SKILL/scripts/step.py done 1`.

Keep this list. Every unit on it gets a step-2 record, including the ones you
clear — a run that examined three functions and one that examined three
hundred have to be distinguishable.

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

**2b. Say what looks wasteful, in your own words, before naming it.** Just:
which work here does not need to happen, is done more often than necessary, or
is done in a more expensive way than the result requires? Write this down — it
goes in the output as `own_hypotheses`.

This is the only defence against reading code through a label you have already
picked, and it only works if you do it first and record it.

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
    {"label": "a", "lines": [47],
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop"},
    {"label": "b", "lines": [44,45],
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row"}
  ],
  "cleared_because": null
}
```

Give each suspicion a `label` — `a`, `b`, `c` — unique within the unit. Steps 3
and 4 refer to it. A unit with nothing suspicious gets the same record with
`"suspicions": []` and `cleared_because` saying why.

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

Read the unit a second time, now with the repair in mind. What the edit would
have to be is usually what tells you whether your first reading was right.

Every suspicion ends this step **accepted** or **rejected**, and nothing is
edited in place. If the second reading changes your mind, reject the suspicion
and add a new one, with a new label, saying what you now think. That keeps what
you first thought on the record, which is the part worth reading later.

The list may also **grow** here: reading a second time to write a repair is one
of the better ways to notice something you missed. A rejection with a reason
is as much a result as an acceptance.

**For each suspicion:**

1. **Does it apply here?** Does your account of the waste still hold on a second
   reading, or was it the shape of the code rather than what it does?
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
    "label": "a", "lines": [58], "verdict": "rejected",
    "why": "the repair belongs where the container is built, not where it is searched. Added `c` instead."
  },
  {
    "label": "c", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request, built in __init__ at line 31 and read nowhere else; as a set each search is one hash lookup"
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
   `blocked`, with that reason. When the reason is a package missing from this
   environment, install it into this venv and request the unit again first.
   A failed unit does not count toward the 20 units with inputs: ask for
   another in its place — up to 30 different units in all.

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
   listed in `related` — both are kept. A suspicion is `blocked` only when the
   tools showed it cannot be measured: its unit's inputs could not be generated,
   its module does not load, or its repair cannot be made to behave identically
   — quote that message as `why`. One you did not try, because you expect it
   cannot run or it is outside the 20, is `deferred`: ask for its inputs instead
   whenever you can.

6. **Record what happened to every accepted suspicion** in `step4.jsonl`, one
   record per unit:

   ```jsonc
   {"step": 4, "unit": "src/render.py::Report.render", "outcomes": [
     {"label": "a", "outcome": "submitted",      "submission": "render-concat", "why": null},
     {"label": "b", "outcome": "same_repair_as", "submission": "render-concat", "why": null},
     {"label": "c", "outcome": "blocked",        "submission": null, "why": "inputs.py: no inputs could be generated: every call opens a database connection"},
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
what it repairs, the verdict, and what it saved across its four inputs. Lead
with what was confirmed, say plainly what was not, and say how many accepted
suspicions were deferred unmeasured.

`$SKILL/reference/output-format.md` has the exact shape of every file.

---

## How this goes wrong

Failure modes, in the order they actually happen:

1. **Stopping early.** Reading a few files, picking two or three units from
   them and taking those through to the end. It feels like progress and leaves
   most of the target unread. Read every file first, and pick from all of them.
1. **Repeating what you have read about Python performance.** Much of it is
   out of date, and some of it was never true. Every claim here gets measured,
   and the ones you are most certain about are the ones worth measuring first.
1. **Submitting one edit twice.** One edit is one repair, attributed to
   one reason; another suspicion it also fixes is `same_repair_as`.
1. **Building one repair on top of another.** Every repair is written against
   the original code. One written against your previous repair is measured
   against code that does not exist.
1. **Ignoring context.** Almost every pattern that looks wasteful is the right
   call somewhere. A bare `except` in a retry loop, a materialised list that
   gets indexed twice, a wrapper that is public API.
   Ask what the author was required to do before deciding they were wrong.
1. **Skipping measurement because the waste is obvious.** The obvious ones are
   exactly where a wrong assumption hides.
1. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to one reason, and cannot be measured against one. Change what removes
   the waste and stop.
1. **Changing more than the unit without checking what else depends on it.**
   The check watches the unit's contract, so another caller or another reader
   of the changed state breaks silently.

## Scope

Python. A finding is a repair with a reason, not a label.

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
