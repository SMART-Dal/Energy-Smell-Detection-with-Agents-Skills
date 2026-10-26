# Verifying a saving

A repair comes with a claim: that this refactoring saves energy. This is how
the claim gets tested. Read this before writing your first submission.

The rule: **no repair is reported as saving anything until it has been
measured on this machine.**

You do not edit the repository. You describe the repair; the script applies it
to a copy, and `before` is whatever the repository already contains.

---

## The submission

One JSON object per line of `submissions.jsonl`, one line per repair:

```jsonc
{
  "id": "render-concat",
  "unit": "src/render.py::Report.render",
  "changed": {
    "src/render.py::Report.render": "def render(self):\n    return \"\".join(_row(r) for r in self.rows)"
  },
  "sole_caller_evidence": null,
  "notes": "Sizes taken from the fixtures in tests/; `_row` left as the real helper."
}
```

**Every line has every field below, and no others** — none is optional; the
ones with nothing to say take the empty value shown.

| Field | What it holds |
|---|---|
| `id` | a name for this repair, unique in the file |
| `unit` | the function or method whose behaviour must be preserved, as `path::qualname` |
| `changed` | `path::qualname` → the full replacement source of that function |
| `sole_caller_evidence` | how you know nothing else calls or reads what you changed; `null` when `changed` holds only the unit |
| `notes` | a few sentences a reader would otherwise have to guess; `""` if none |
| `agent_measurement` | written by the script, never by you |

`changed` holds **source text, not a diff and not an AST**: the whole function
as you would commit it, decorators and `def` line included, written at column
zero even when it is a method. Each entry replaces exactly that function and
nothing around it — so a repair that needs a module the file does not import
yet imports it inside the function. After the first call, an `import`
statement is a single dictionary lookup.

## You do not supply `before`

`before` is the function already in the repository, loaded from the file you
named. You cannot simplify it or substitute an illustration of the pattern,
because you never write it. A repair worth 30% of a five-line sketch and 2% of
the real function always measures against the real function.

The rest is real too: the helpers are the real helpers, the constants the real
constants, the imports the real imports. So the replacement must differ from
the repository by **the repair alone**. If it also renames a variable, inlines
a helper or fixes a second thing, the measurement no longer attributes to
one reason and the result is unusable.

## Changing more than the unit

The unit's **contract** is what has to survive: everything a caller can see,
listed under "What "the same" means" below.
Anything only the unit depends on — a helper nothing else calls, state nothing
else reads — is implementation detail, and may change.

Give each changed function its own entry in `changed`, in whatever file it
lives, and fill in `sole_caller_evidence`: the search you ran, or the call sites
and attribute reads you checked. The check watches the unit's contract only, so
anything else broken by the change would pass every check here. A submission
that changes more than the unit without this is rejected.

## Several repairs in one unit

Each repair is written against the original code and measured against it, on
its own. There is no order to take them in, and no repair is built on another.

- **The same edit** for two suspicions is one repair. Submit it once; the other
  suspicion is `same_repair_as` it.
- **Different edits to the same code** are separate repairs. Submit each.
- **Every repair of one unit is measured on that unit's inputs**, so their
  savings are measured on identical inputs and can be compared.

## The inputs

You do not write them. Ask for every unit you will measure, in one request:

```bash
python $SKILL/scripts/inputs.py request src/render.py::Report.render src/parse.py::tokenize
python $SKILL/scripts/inputs.py status          # which are ready
```

A generator outside this session writes each unit's inputs from the
repository's own code — the unit, its class, what it uses, and where the
repository calls it. It asks for more candidates than it needs, runs each on
the original code, keeps those that complete and give the same output on a
second, fresh run, and of those keeps the four that do the most work. They are
fixed for the unit: every repair of it is measured on the same four, and so is
the re-measurement after the session, which uses our own copy of them.

Requests open in step 3, at `step.py done 2`. The request returns at once.
Generation runs outside this session, every unit at the same time, and usually
takes a minute or two; a hard unit can take five. Ask for all of them in one
request; a unit you add later is another request. Up to 30 units can have
inputs or be generating at once: more than the 20 repairs measured, so there is
room for units you decide against. A unit that fails gives its place back, so
ask for another in its place; up to 30 different units may fail in a session.

verify.py does not measure while anything is still being generated: it waits
first, up to ten minutes, printing which units it is waiting for. Give its
first run a timeout to match — fifteen minutes plus a minute per repair — or
run it in the background. A unit still not ready after that comes back
`no_inputs` and is measured by the next run.

**A module that does work when it is imported can still be measured** — a
script that reads `sys.argv`, opens files or calls a server at its top level.
When importing it fails, it is loaded one top-level statement at a time: the
statements that fail are skipped and reported, and the unit is measured if it
is still defined. So ask for its inputs rather than assuming it cannot run; the
generator says so when it cannot.

**A unit listed as `failed` can be asked for again** once you have fixed what
stopped it. If the reason is a package missing from this environment, install
it into this venv — whatever you install stays for the re-measurement after
the session — and request the unit again; it is generated once more, up to
three times a session. When the generator simply did not manage — none of its
inputs ran on the original, or it produced none — another try may succeed: it
writes new inputs every time. `inputs.py status` says which case each failure
is.

Each unit's inputs are one file in `.energy-inputs/`, read-only. Read it before
you write the repair: it is exactly what the repair will be measured on. They
cannot be changed, and editing the file would change nothing that counts —
the result after the session is measured on our copy.
The file defines two functions, each returning `(label, thunk)` pairs:

- **`checks()`** — edge inputs: empty, one element, `None`, an odd type. Both
  versions run them and must behave the same; they are never measured.
- **`cases()`** — the four measured inputs, each making the unit do different
  work. Every one counts on its own: a repair is `confirmed` only if it saves
  energy on all four, and one that measurably loses on any of them is `mixed`.

A thunk returns the unit's arguments as a tuple, or `call(...)` when the unit
takes keyword arguments. **A method takes its instance as the first
argument**, so the thunk builds the instance and passes it.

**Why each input is called many times.** One call is usually too short for the
energy meter to see, so each input is called many times in a row and the
energy of all the calls is added up. That is the only reason for the
repetition. Every call gets a fresh copy of the input, built before the
calls are measured, and the outputs are compared once, before anything is
measured.

**A coroutine is run, a generator is drained.** An `async def` unit is run to
completion on an event loop of its own, and a generator's output is collected
and compared as what it yielded — so a repair that turns a list into a
generator counts as returning something different.

**Files are output like any other.** Inputs put the files a unit reads under
`WORKDIR`, a directory the script gives each side, and every file the unit
creates, changes or deletes, under `WORKDIR` or inside the repository, has to
come out the same on both sides.

**A unit with no inputs.** An input counts only if the original completes on
it here, from this machine alone, and gives the same output on every run: that
is what lets the two versions be compared. A unit that needs the network, a
remote service, credentials, hardware or data the repository does not hold, or
whose own output changes from run to run, cannot give that, whatever the input.
`inputs.py status` lists it as `failed`, with the reason and what to do next,
and verify.py reports its repairs as `no_inputs` with the same. Record their
suspicions as `blocked`, quoting the reason — the suspicion is still a
finding; only its saving cannot be measured here — and ask for the next unit
you would measure in its place: a failed unit does not count toward the 30.

**`blocked` needs that evidence.** A suspicion is `blocked` only when the tools
showed it cannot be measured here: its inputs could not be generated, its
module does not load, the result is `error` for something you cannot install,
or the repair cannot be made to behave identically. Quote the message as
`why`. One you did not ask inputs for — because you expect it cannot run, or
because it is outside the 20 — is `deferred`, not blocked: ask for its inputs
instead whenever you can, and let the generator say whether it runs.

## What "the same" means

The replacement must do everything the original does, on every input:

- the same **return value**;
- the same effect on its **arguments**, an object's own attributes included;
- the same changes to the **module-level and class-level values** the
  original's code uses;
- the same **files** written;
- the same **printed output** and the same **log records**;
- the same **exception** type.

Nothing in a submission relaxes this. A repair that stops changing the
caller's data — `lst.sort()` becomes `sorted(lst)` — stops updating a
module-level cache, or drops a log call changes what callers can see, and
comes back `not_equivalent`; so does one that returns the same answer in a
different form. Two things are left out on purpose: the numbers inside a log
message, so a logged duration is not behaviour, and a new module-level value
the repair keeps for itself, such as a cache only it reads.

## Running it

```bash
python $SKILL/scripts/verify.py --calibrate                    # optional, see below
python $SKILL/scripts/verify.py submissions.jsonl --repo .     # the whole file
```

`--calibrate` measures two copies of identical code against each other, the
way repairs are measured. The answer must come back
*insignificant*; its width is this host's resolution limit, and the bar every
real effect has to clear. It is kept for the session, and taken automatically
if you forget. If it comes back significant, something else is using the
machine, and nothing measured until it stops means anything.

The second command goes through the file once — about a minute per repair,
plus half a minute to calibrate, after any inputs still being generated are
ready — so give the command a timeout to match, or run it in the background
and wait for it. It writes each result into its line,
as `agent_measurement`, with the verdict in `agent_measurement.status`. Run it again after fixing broken lines and it
measures only what needs it: a line never measured, a line that was
`not_equivalent`, `invalid` or `error` and has since been fixed, and anything
`inconclusive` or `error`, which is simply tried again.

A line with a measured result — `confirmed`, `partial`, `mixed`,
`regressed`, `negligible` — is final and is never measured again. If it has been edited
since, the script reports it `invalid` and leaves the result it had exactly as
it was. A different repair is a new line.

## When the environment gets in the way

- **A package is missing** — the result is `error`, naming it: install it into
  this environment, `python -m pip install <package>`, and run again. Never
  install the repository's own code, and never create another environment.
- **Anything else cannot run here** — the result says what failed: record the
  suspicion as `blocked`, with the message.

Always measure with `--repo .`, against the repository itself: a result taken
against an edited copy is discarded.

## What the script does

1. **Stages** two fresh copies of the repository, the second with your
   replacements spliced in, and loads both side by side in one process.
2. **Equivalence.** Every input from `checks()` and `cases()` runs once
   through both versions, and everything in "What "the same" means" above is
   compared. A mismatch is `not_equivalent`, and nothing is measured.
3. **Measurement.** The two versions take turns, one window of about a second
   each, three pairs per input, the order flipped every pair, so the machine's
   own drift affects both alike.
4. **Statistics.** The energy difference is averaged over the pairs, with a 95%
   confidence interval. Energy decides the verdict; time is reported beside it
   and decides nothing.

## Verdicts

| Verdict | What it means | What to do |
|---|---|---|
| `confirmed` | saves energy on all four inputs, each clearing the noise floor | nothing — final |
| `partial` | saves energy on some inputs, and moves nothing beyond the noise on the others | nothing — final. A narrower claim: it pays on some of the work the unit does |
| `mixed` | saves energy on some inputs, costs it on others — both clearing the floor | nothing — final. A trade-off: which side wins depends on the input |
| `regressed` | every case that moved measurably, got worse | nothing — final |
| `negligible` | measured on a clean floor, and nothing moved more than the noise | nothing — final |
| `inconclusive` | the host's noise was too high to resolve an effect this size | nothing; the next run measures it again. It is **not** `negligible` |
| `not_equivalent` | the replacement behaves differently from the original | fix the repair and run again |
| `invalid` | the line is malformed, the inputs do not load against the repair, or a measured line was edited | fix it as the message says |
| `no_inputs` | the unit has no inputs: none were requested, or none could be generated | request them; if they could not be generated, record `blocked` with the message |
| `error` | the environment failed: an import, the meter, a library the unit needs | what the message says: install a missing package and run again, or record `blocked` |
| `over_limit` | 20 repairs in this session already have a verdict, the most it measures; this one was not measured | record its suspicion as `deferred` |

Every verdict stays. A file that proposes ten repairs and has three come back
`negligible` says more than one that quietly dropped them.

`negligible` and `inconclusive` are different claims. `negligible` says the
repair does nothing, on a machine quiet enough to tell — that is evidence.
`inconclusive` says this machine could not tell, which is a fact about the host
and says nothing about the code. Reporting the second as the first writes a
busy host down as evidence against the repair.

`mixed` is not a softer `regressed`. Both effects are real: the repair pays on
one input and costs on another, and which one the code actually sees decides
whether it is worth having.

## What the numbers mean

The meter reads the whole machine's CPU package energy over each window, idle
cores included. A version that finishes sooner also spends less idle power, so
the comparison holds, but it cannot tell a change in power from a change in
duration. When energy improves while wall-clock time does not, say so — that is
more interesting than a performance bug.

## When received wisdom is wrong

It happens, and measurement is how you find out.

Every style guide says growing a string with `+=` in a loop is quadratic, so
collect the parts and join them. Measured, the textbook example got *slower* —
62 ms against 56 ms at 400 000 iterations. CPython resizes a string in place
when nothing else refers to it, so the classic example was already linear. The
real waste turned out to be about aliasing: through an attribute, where the
optimisation cannot fire, the same repair saves 94.8% ± 0.1%.

If a repair you were confident about comes back `negligible`, that is a result.
Report it, and say what you measured. Do not quietly drop it and try a
different one until something sticks.

