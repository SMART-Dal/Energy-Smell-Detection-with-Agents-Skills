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
  "id": "{{SUBMISSION_ID_EXAMPLE}}",
{{ROOT_CAUSE_FIELD}}  "unit": "src/render.py::Report.render",
  "changed": {
    "src/render.py::Report.render": "def render(self):\n    return \"\".join(_row(r) for r in self.rows)"
  },
  "related": [],
  "sole_caller_evidence": null,
  "equivalence": "strict",
  "equivalent": null,
  "notes": "{{NOTES_EXAMPLE}}"
}
```

**Every line has every field below, and no others** — none is optional; the
ones with nothing to say take the empty value shown.

| Field | What it holds |
|---|---|
| `id` | a name for this repair, unique in the file |
{{ROOT_CAUSE_ROW}}| `unit` | the function or method whose behaviour must be preserved, as `path::qualname` |
| `changed` | `path::qualname` → the full replacement source of that function |
| `related` | ids of other repairs of the same code; `[]` if none |
| `sole_caller_evidence` | how you know nothing else calls or reads what you changed; `null` when `changed` holds only the unit |
| `equivalence` | `"strict"`, or `"returns_only"`; see below |
| `equivalent` | `null`, or the source of `def equivalent(before, after)`; see below |
| `notes` | a few sentences a reader would otherwise have to guess; `""` if none |
| `agent_measurement` | written by the script, never by you |

`changed` holds **source text, not a diff and not an AST**: the whole function
as you would commit it, decorators and `def` line included, written at column
zero even when it is a method. Each entry replaces exactly that function and
nothing around it.

## You do not supply `before`

`before` is the function already in the repository, loaded from the file you
named. You cannot simplify it or substitute an illustration of the pattern,
because you never write it. A repair worth 30% of a five-line sketch and 2% of
the real function always measures against the real function.

The rest is real too: the helpers are the real helpers, the constants the real
constants, the imports the real imports. So the replacement must differ from
the repository by **the repair alone**. If it also renames a variable, inlines
a helper or fixes a second thing, the measurement no longer attributes to
{{ONE_BASIS}} and the result is unusable.

## Changing more than the unit

The unit's **contract** is what has to survive: the same return value, the
same effect on its arguments, the same output, the same exception type.
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
- **Different edits to the same code** are separate repairs. Submit each, and
  list each in the other's `related`.
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

The request returns at once. Generation runs outside this session, every unit
at the same time, and usually takes a minute or two; a hard unit can take
five. So ask as soon as you know which units you will measure, and write the
repairs meanwhile. Ask for all of them in one request; a unit you add later is
another request, and a session has at most 20.

verify.py does not measure while anything is still being generated: it waits
first, up to ten minutes, printing which units it is waiting for. Give its
first run a timeout to match — fifteen minutes plus a minute per repair — or
run it in the background. A unit still not ready after that comes back
`no_inputs` and is measured by the next run.

Each unit's inputs are one file in `.energy-inputs/`, read-only. Read it before
you write the repair: it is exactly what the repair will be measured on. They
cannot be changed or generated again, and editing the file would change
nothing that counts — the result after the session is measured on our copy.
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
repetition. Every call gets the original input — a unit that changes its input
gets a fresh copy for each call — and the outputs are compared once, on the
first call, before anything is measured.

**A coroutine is run, a generator is drained.** An `async def` unit is run to
completion on an event loop of its own, and a generator's output is collected
and compared as what it yielded — so a repair that turns a list into a
generator counts as returning something different.

**Files are output like any other.** Inputs put the files a unit reads under
`WORKDIR`, a directory the script gives each side, and every file the unit
creates, changes or deletes, under `WORKDIR` or inside the repository, has to
come out the same on both sides.

**A unit with no inputs.** When the generator cannot build inputs that run
here — the unit needs the network, a service, credentials, hardware —
`inputs.py status` lists it as `failed` with the reason, and verify.py reports
its repairs as `no_inputs`. Record their suspicions as `blocked`, with that
reason.

## When "identical" is stricter than "the same answer"

By default the replacement must match the original on the return value, the
state of the arguments afterwards, the files it writes, stdout, and the
exception type. Two escape
hatches exist for when that is genuinely too strict. Both are recorded in the
result, and both must be repeated wherever the saving is quoted.

**The repair stops mutating the caller's data** — `lst.sort()` becomes
`sorted(lst)`, `a.extend(b)` becomes `a + b`. The answer is the same; the side
effect is not.

```jsonc
"equivalence": "returns_only"
```

Use it only when you have checked the call sites and none of them relies on
the mutation, and say so in `notes`.

**The result is the same answer in a different form** — an unordered
collection, a tolerance on a float. Give the comparison in `equivalent`, as
source text holding that one function and nothing else but imports:

```python
def equivalent(before, after):
    """Same set of matches; the repair returns them in hash order."""
    return sorted(before) == sorted(after)
```

It receives the two results as plain data — lists, dicts, numbers and
strings — because each version's objects are instances of its own copy of the
code and would never compare equal as they are. A set or tuple arrives as a
list, an object as a dict of its attributes. The docstring is required, because a
comparison that always returns `True` would turn a broken repair into a
confirmed one with nothing in the output to show it.

Neither hatch covers a repair that computes something different. Returning
indices where the original returned values, or being off by one, is a bug in
your repair — fix it.

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

Measurements run in the environment you are in, and only there do they say
anything about this repository.

- **A package is missing** — `error`, naming it: install it into this
  environment, `python -m pip install <package>`, and run again. Never install
  the repository's own code: an installed copy would stand in for the copies
  being compared. Never create another environment.
- **The module fails while loading** — a stray line at the end of a script,
  arguments parsed at import, a package `__init__` that looks for files only an
  installed copy has: the script loads it, or the package above it, one
  top-level statement at a time, skips the ones that fail, and lists them in
  the result. If the unit
  needs one of them, the result is `error` and says so.
- **Anything else that cannot run** is `blocked`: record it, with the message.

Never measure against an edited copy of the repository, or with `--repo`
pointing anywhere but the repository: the number would be about code the
repository does not contain. Every result records a digest of the code it was
measured against, and one that does not match the repository is discarded.

## What the script does

1. **Stages** two fresh copies of the repository: one untouched, one with your
   replacements spliced into the files they name. Nothing is renamed and no
   import is rewritten.
2. **Loads** both copies side by side in one Python process, each under its
   real package names: one copy's modules are set aside while the other's are
   in use, so every import the unit makes resolves to its own copy. If the
   environment lacks a package the unit's module imports but the unit itself
   never uses, a stand-in is supplied, and the result says so; if the unit uses
   it while running, the result is `error`. A module that fails while loading,
   or whose package does, is loaded one top-level statement at a time,
   skipping those that fail.
3. **Equivalence.** Every input from `checks()` and `cases()` goes through both
   versions: same return value, same argument state afterwards, same files
   written, same stdout, same exception type. A mismatch is fatal — the repair is wrong, not the
   waste absent.
4. **Sizing.** Times one call of each version and picks a repeat count so the
   faster one fills about a second. Both run that same count.
5. **Paired measurement.** The two versions take turns on one thread, one
   measured window each, three pairs per case, the order flipped every pair —
   so each pair of readings is taken back to back, on the same core, close
   enough that the machine's own drift affects both alike.
6. **Statistics.** The energy difference is computed per pair and averaged,
   with a 95% confidence interval. Energy decides the verdict; wall-clock time
   is measured and reported but never decides anything.

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

Every verdict stays. A file that proposes ten repairs and has three come back
`negligible` says more than one that quietly dropped them.

`negligible` and `inconclusive` are different claims. `negligible` says the
repair does nothing, on a machine quiet enough to tell — that is evidence.
`inconclusive` says this machine could not tell, which is a fact about the host
and says nothing about the code. Reporting the second as the first writes a
busy host down as evidence against {{EVIDENCE_AGAINST}}.

`mixed` is not a softer `regressed`. Both effects are real: the repair pays on
one input and costs on another, and which one the code actually sees decides
whether it is worth having.

## What the numbers mean

The meter reports whole-machine CPU package energy over each window, with
nothing subtracted. On a many-core host much of that is idle power from cores
doing nothing, so only a fraction of any reading is work you caused.

That does not dilute the result the way it looks like it should, because the
window is not a fixed length: a version that finishes sooner accrues less idle
power too. What the figure cannot do is separate a change in power draw from a
change in duration.

**Every verdict is decided on energy alone.** Time and power are recorded
beside it, and are worth reading — when energy improves while wall-clock time
does not, you have found something more interesting than a performance bug,
and should say so — but no rule reads them. A result carries the joules and
seconds of each version rather than a percentage, because the percentage is a
view of those numbers, and storing it beside them lets the two disagree.

{{WHEN_WRONG}}
