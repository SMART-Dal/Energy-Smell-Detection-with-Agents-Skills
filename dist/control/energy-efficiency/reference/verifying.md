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
  "related": [],
  "sole_caller_evidence": null,
  "equivalence": "strict",
  "cases_source": "def checks():\n    ...\n\ndef cases():\n    ...",
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
| `related` | ids of other repairs of the same code; `[]` if none |
| `sole_caller_evidence` | how you know nothing else calls or reads what you changed; `null` when `changed` holds only the unit |
| `equivalence` | `"strict"`, or `"returns_only"`; see below |
| `cases_source` | Python source defining `checks()` and `cases()` |
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
one reason and the result is unusable.

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
- **Every submission for one unit uses the same `cases_source`**, so their
  savings are measured on identical inputs. The script rejects a file where
  they differ.

## `cases_source`

Python source defining two functions. Each returns `(label, thunk)` pairs, and
the thunk returns a **tuple of arguments** for the unit.

```python
from src.render import Report    # the repository's own modules, by their real names

def _rows(n, *, wide=False):
    columns = 12 if wide else 3
    return [{f"c{j}": i * j for j in range(columns)} for i in range(n)]

def checks():                     # behaviour only, never measured
    return [
        ("empty",      lambda: (Report([]),)),
        ("one-row",    lambda: (Report(_rows(1)),)),
        ("none-value", lambda: (Report([{"c0": None}]),)),
    ]

def cases():                      # exactly five, each measured
    return [
        ("typical",    lambda: (Report(_rows(200)),)),
        ("many-rows",  lambda: (Report(_rows(50_000)),)),
        ("wide-rows",  lambda: (Report(_rows(5_000, wide=True)),)),
        ("long-text",  lambda: (Report([{"c0": "x" * 4_000}] * 2_000),)),
        ("worst-case", lambda: (Report(_rows(20)),)),   # where joining costs most
    ]
```

**`checks()` is for behaviour.** The edge inputs — empty, one element, `None`,
an odd type — are run through both versions and compared, and never measured.
On an empty list a repair can easily cost more than the code it replaces — by
nanojoules, on an input that costs nothing either way — and measuring that
would only make a good repair look like a trade-off.

**`cases()` is for energy: exactly five inputs, each making the unit behave
differently.** Not five sizes of the same input — five behaviours: the paths
the code takes, how often a lookup hits, how many duplicates there are, how
long one element is against how many there are. Include the input each repair
is *most likely to lose on*, because the verdict needs to see it. Every case
counts on its own, and one that measurably loses makes the result `mixed`.

**Thunks, not values.** The thunk is called again before every measured
window, outside it, so a unit that mutates its input cannot poison the next
one.

**A method takes its instance as the first argument.** `Report.render` is
called as a plain function, so the thunk builds the `Report` and passes it.

**Import the repository's modules the way its own code does.** A package by
its package name — `from mypkg.render import Report`, wherever `mypkg/` sits —
and a standalone script by its file name, as if run from its own directory:
`from convert import main` for `tools/convert.py`. A file whose name is not an
identifier needs `importlib.import_module("csv-tool")`.

**A coroutine is run, a generator is drained.** An `async def` unit is run to
completion on an event loop of its own, and a generator's output is collected
and compared as what it yielded — so a repair that turns a list into a
generator counts as returning something different.

**Anything the unit writes to disk goes under `WORKDIR`**, a directory the
script gives each side. Files are output like any other: every file the unit
creates, changes or deletes, under `WORKDIR` or inside the repository, has to
come out the same on both sides.

**Build the inputs; do not fake library objects.** If the unit needs an object
the environment cannot construct, record the suspicion as `blocked` and say
why. A faked object measures something nobody runs.

`cases_source` may also define `equivalent()`; see below. Module-level code in
it runs once per side, outside all measurement.

## Choosing the five

Sizes should come from the repository, not from convenience. If its tests,
fixtures or documentation say what a normal input looks like, start from that.
If nothing says, pick something you can defend in one sentence and put the
sentence in `notes`.

You do **not** need outer loops to make a short case measurable. The script
times one call and repeats it until the window is long enough — a 40 µs case
is simply run tens of thousands of times. Write each case at its natural size.

When the effect grows with the number of *calls* rather than with input size —
removing per-call overhead, say — give the unit many calls over a small input
rather than one over a large one.

**The shape of a case can matter as much as its size.** Two cases of one
repair, on one host: a string accumulator fed 200 000 short parts measured
+18.4%, and the same accumulator fed 2 000 parts ten times the total length
measured +1.2%. Same total bytes, same code, opposite conclusions. When the
mechanism depends on a variable — a count against a length, a hit rate, a
duplicate ratio — vary that variable across the five, and say in `notes` which
one the repair tracks.

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
collection, a tolerance on a float. Define `equivalent()` in `cases_source`:

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

The second command goes through the file once, under a minute per repair, and
writes each result into its line. Run it again after fixing broken lines and it
measures only what needs it: a line never measured, a line that was
`not_equivalent`, `invalid` or `error` and has since been fixed, and anything
`inconclusive` or `error`, which is simply tried again.

A line with a measured result — `confirmed`, `mixed`, `regressed`,
`negligible` — is final and is never measured again. If it has been edited
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
  arguments parsed at import: the script loads it one top-level statement at a
  time, skips the ones that fail, and lists them in the result. If the unit
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
   it while running, the result is `error`. A module that fails while loading
   is loaded one top-level statement at a time, skipping those that fail.
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
| `confirmed` | every case that moved, moved the right way, clearing the noise floor | nothing — final |
| `mixed` | saves energy on some cases, costs it on others — both clearing the floor | nothing — final. A trade-off: which side wins depends on the input |
| `regressed` | every case that moved measurably, got worse | nothing — final |
| `negligible` | measured on a clean floor, and nothing moved more than the noise | nothing — final |
| `inconclusive` | the host's noise was too high to resolve an effect this size | nothing; the next run measures it again. It is **not** `negligible` |
| `not_equivalent` | the replacement behaves differently from the original | fix the repair and run again |
| `invalid` | the line is malformed, its `cases_source` fails, or a measured line was edited | fix it as the message says |
| `error` | the environment failed: an import, the meter, a library the unit needs | what the message says: install a missing package and run again, or record `blocked` |

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

