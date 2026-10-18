---
name: {{SKILL_NAME}}
description: {{SKILL_DESCRIPTION}}
---

# {{TITLE}}

You are finding **{{SUBJECT}}**: code that spends energy on work the program
does not need, and that a specific refactoring can remove without changing what
the program does.

Paths below are relative to this file's directory — call it `$SKILL`. Work out
what `$SKILL` is once, at the start, and use it throughout.

---

## What counts as a finding

{{FINDING_RULE}}

Three consequences you have to hold onto:

- **No repair, no finding.** If you cannot write the actual edit for this code,
  you have not found anything — you have recognised a pattern.
- **No measurement, no claim.** A repair is said to save energy only once it
  has been measured. One left unmeasured is still a finding — with no claim
  attached to it.
- **Report the failures too.** A repair you built, measured, and found saves
  nothing is a result. It stays in `submissions.jsonl`, with its verdict.

## {{ATTRIBUTION_HEADING}}

{{ATTRIBUTION_RULE}}One unit can have several repairs, and they can overlap: fixing how a function
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
attributed to {{ONE_BASIS}}, and the measurement stops meaning anything. The
second problem is a second finding, or it is nothing.

## What is not {{SUBJECT_SINGULAR}}

**Style.** Unreadable, undocumented, poorly named, badly typed code is not
{{SUBJECT_SINGULAR}}. If the repair does not change what the machine does, it
is out of scope here.

Everything else that wastes work is in scope. How hot the code is tells you how
much a saving is worth — but a real repair on a cold path is still a real
repair, and the measurement will say what it came to.

## Energy is not time

They usually move together, but not always. Spreading work across cores cuts
wall-clock time while raising energy. A busy-wait poll burns power while making
no progress. A blocked event loop keeps a core hot for nothing. Judge energy,
and when the two diverge, say so — those cases are the most interesting ones
you can find.

---

## Procedure

Five steps, in order. Steps 2 and 3 go one unit at a time — read and suspect,
decide, then the next unit. Step 4 starts once every unit has been through step
3, and takes all of them at once. Each step states what it takes in and what it
must produce. Produce it before moving on, and append it to `findings.jsonl` as
one JSON line tagged with its step — as you go, not reconstructed at the end.
Every step after the second one is a check on what the second one wrote down,
and a check you run against nothing checks nothing.

Each record has **exactly the keys its example below shows — all of them, and
no others**; a key with nothing to say is `null` or `[]`.
`$SKILL/reference/output-format.md` lists every key and what it holds.
`findings.jsonl` and `submissions.jsonl` both go in the repository's root, the
directory you were started in — nowhere else.

### 1. Select — *in:* a target · *out:* the units you will examine, in order

**The target** is what you were asked to look at: the whole repository, a
directory, a file, or a single unit. Choose units only from inside it; read
outside it as far as you need. A unit named loosely — "the render function" —
is yours to pin down: find it, and record the exact `path::qualname` it
resolved to. If more than one function matches, all of them are the target.

**How many:** every unit in the target, unless you were asked for a number of
units — then at most that many, the hottest first. You may change which units
those are at any point, if something you read later shows you a hotter one; just
do not go over the number. It limits units and nothing else: within a unit,
record every suspicion you have.

Read the repository first: its entry points, what its tests exercise, what its
README says it is for. Then pick the units where energy is actually spent, in
this order of priority:

1. **work that repeats** — the deepest loop nests, and the helpers those loops
   call, which is where a cheap-looking function gets paid thousands of times;
2. **work proportional to input size**, rather than to a fixed constant;
3. **the repository's own hot path** — what it benchmarks, what its main entry
   point spends its time in.
{{SCANNER_HINT}}
**Order them by how much energy you expect a repair to save** — how often the
unit runs, multiplied by how much work one run does — and work from the top.
With a number to keep to, the units you examine have to be the ones where most
of the energy goes.

```jsonc
{"step": 1, "target": "src/", "unit_limit": 10, "units_considered": 128,
 "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize"]}
```

If you change the list, append another step-1 record with the list as it now
stands; the last one is the list you examined.

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

{{STEP_2B}}

This is the only defence against reading code through a label you have already
picked, and it only works if you do it first and record it.

{{STEP_TAXONOMY_MATCH}}{{STEP_EVIDENCE}}{{STEP_SWEEP}}**Output of this step.** For each unit, one record:

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
{{SUSPICION_ROWS}}
  ],
  "cleared_because": null
}
```

Give each suspicion a `label` — `a`, `b`, `c` — unique within the unit. Steps 3
and 4 refer to it. A unit with nothing suspicious gets the same record with
`"suspicions": []` and `cleared_because` saying why.
{{FOUND_BY_NOTE}}
**At most 12 suspicions per unit.** The cap makes you rank rather than list. If
you are at the cap, keep the ones you would actually spend an hour repairing.

### 3. Decide — *in:* `suspicions[]` · *out:* one record, each suspicion accepted or rejected

{{DECIDE_PREAMBLE}}

{{DECIDE_MOVE}}

{{DECIDE_GROWTH}}

**For each suspicion:**

1. **Does it apply here?** {{DECIDE_APPLIES}}
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
{{DECIDE_ROWS}}
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

2. **Ask for the inputs of every unit you will measure, in one request.**

   ```bash
   python $SKILL/scripts/inputs.py request src/render.py::Report.render src/parse.py::tokenize
   ```

   You do not write the inputs a repair is measured on. A generator outside
   this session writes them for each unit: **four** measured inputs that make
   the unit do substantial and different work, and a few edge inputs checked
   only for identical behaviour. It keeps an input only if it runs on the
   original code and gives the same output twice. The request returns at once
   and generation takes a minute or two, all units together — go on to write
   the repairs meanwhile. Each unit's file appears in `.energy-inputs/`,
   read-only: read it to see what your repairs will face. After the session,
   every repair is measured again on our own copy of the same inputs.

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

   It first waits for any inputs still being generated, then measures every
   line in turn, under a minute each, on its unit's inputs, and writes the
   result into the line as `agent_measurement`: the verdict, and the joules
   and seconds of every input. Never write or edit it yourself.

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

6. **Record what happened to every accepted suspicion**, one record per unit:

   ```jsonc
   {"step": 4, "unit": "src/render.py::Report.render", "outcomes": [
     {"label": "a", "outcome": "submitted",      "submission": "{{SUBMISSION_ID_EXAMPLE}}", "why": null},
     {"label": "b", "outcome": "same_repair_as", "submission": "{{SUBMISSION_ID_EXAMPLE}}", "why": null},
     {"label": "c", "outcome": "blocked",        "submission": null, "why": "every input needs a live database connection"},
     {"label": "d", "outcome": "deferred",       "submission": null, "why": "outside the 20 repairs measured"}
   ]}
   ```

Every measured repair stays in `submissions.jsonl`, whatever its verdict.
`partial`, `negligible`, `regressed` and `mixed` are results, and a file that
kept only the wins could not be told apart from one that hid its losses.

### 5. Finish — *in:* both files · *out:* both files complete, and a short summary

This step writes no record to `findings.jsonl`.

Before you stop, check:

- every unit chosen in step 1 has a step-2 record, cleared or not;
- every suspicion accepted in step 3 has an outcome in a step-4 record;
- every line of `submissions.jsonl` carries the `agent_measurement` the script
  wrote, and nothing is left `inconclusive` or `error` that a run could still
  settle.

Then end with a short summary for whoever asked: for each submission, the unit,
{{REPAIR_BASIS}}, the verdict, and what it saved across its four inputs. Lead
with what was confirmed, say plainly what was not, and say how many accepted
suspicions were deferred unmeasured.

`$SKILL/reference/output-format.md` has the exact shape of both files.

{{CATEGORY_SECTION}}---

## How this goes wrong

Failure modes, in the order they actually happen:

{{FAILURE_MODES_CARDS}}1. **Repeating what you have read about Python performance.** Much of it is
   out of date, and some of it was never true. Every claim here gets measured,
   and the ones you are most certain about are the ones worth measuring first.
1. **Submitting one edit twice.** One edit is one repair, attributed to
   {{ONE_BASIS}}; another suspicion it also fixes is `same_repair_as`.
1. **Building one repair on top of another.** Every repair is written against
   the original code. One written against your previous repair is measured
   against code that does not exist.
1. **Ignoring context.** Almost every pattern that looks wasteful is the right
   call somewhere. A bare `except` in a retry loop, a materialised list that
   gets indexed twice, a wrapper that is public API.
{{CONTEXT_POINTER}}
1. **Skipping measurement because the waste is obvious.** The obvious ones are
   exactly where a wrong assumption about hotness hides.
1. **Rewriting the unit.** A patch that changes everything cannot be attributed
   to {{ONE_BASIS}}, and cannot be measured against one. Change what removes
   the waste and stop.
1. **Changing more than the unit without checking what else depends on it.**
   The check watches the unit's contract, so another caller or another reader
   of the changed state breaks silently.

## Scope

{{SCOPE_IDS}}

A **unit** is a function or a method. That is the granularity at which units are
ranked, cleared and reported, and at which a repair is measured — the cases
call something, and this is the something.

That is all it bounds. Read as far as you need in either direction, and
repair across as many units as the waste requires. When the waste exists
only in the arrangement — two methods of a class that each look
reasonable and are wrong together, a helper whose shape forces the code around
it to compensate — report it against the unit whose behaviour the repair must
preserve, and give every function you change its own entry in the submission.
