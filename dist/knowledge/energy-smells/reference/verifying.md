# Verifying a smell

A smell is a claim that a specific refactoring saves energy. This is how the
claim gets tested. Read this before writing your first case file.

The rule: **no finding is reported as a smell until its repair has been measured
on this machine.** The only exception is a root cause whose card says *advisory
only* — its repair is one bytecode instruction and provably cannot clear any
noise floor, so it is reported as unmeasured rather than measured badly.

---

## The case file

One file per candidate smell. Three things are required:

```python
"""C10.S4 in src/render.py::Report.render — string built with += in a loop."""

def _row(i):
    return f"<td>{i}</td>"


def before(rows):
    out = ""
    for r in rows:
        out += _row(r)
    return out


def after(rows):
    return "".join(_row(r) for r in rows)


def cases():
    return [
        ("empty",  lambda: ([],)),
        ("single", lambda: ([0],)),
        ("large",  lambda: (list(range(200_000)),)),
    ]
```

| Name | Contract |
|---|---|
| `before(*args)` | the code as it is in the repository |
| `after(*args)`  | the same code with the repair applied, **and no other change** |
| `cases()`       | `list[tuple[str, callable]]` — a label and a thunk returning a fresh args tuple |

**Thunks, not values.** The thunk is called again for every repetition, outside
the measured window, so a `before` that mutates its input cannot poison the
next sample. A case that returns a shared list is the most common way to get a
nonsense result.

**`after` must differ by the repair alone.** If you also rename a variable,
inline a helper, or fix a second smell, the measurement no longer attributes to
one root cause and the finding is unusable. One case file, one root cause.

Module-level code runs once at import, outside all measurement, so expensive
fixtures can live there.

## `before` must be the real function

This is the part that goes wrong most often, and it invalidates everything
downstream when it does.

`before` is not an illustration of the pattern. It is **this repository's
function, copied**, with as little removed as you can manage. Keep:

- the surrounding work in the same function, even the parts your repair does
  not touch — they are what the saving has to be large enough to show up
  against, and a repair worth 30% of a one-line function may be worth 2% of the
  real one;
- the real data shapes: if the loop runs over dicts with eleven keys, do not
  hand it a list of ints;
- the helper calls, brought along as real code. Only stub what genuinely cannot
  run here — a network call, a live database — and when you stub one, make it
  cost roughly what the original cost, or say in the docstring that you could
  not.

Trim only what makes the file unable to run: imports of the application's own
configuration, framework decorators, logging setup. If trimming starts to
change what the function spends its time on, stop — measure the smaller
enclosing unit instead, or say the candidate is `blocked`.

A simplified `before` produces a real number about a function nobody wrote. It
will usually be a *larger* saving than the truth, because you have deleted
exactly the surrounding work that dilutes it.

The same applies to `after`: it is the repair as you would actually commit it.
If the repair only works because the toy version dropped an edge case, that is
something you need to discover here rather than after the report.

## Choosing cases

Three is usually right:

- **an edge case** — empty, one element, or whatever the boundary is;
- **a small case** — a realistic-but-modest input;
- **a large case** — big enough that one call takes milliseconds, not
  microseconds.

Sizes should come from the repository, not from convenience. If its own tests,
fixtures or documentation say what a normal input looks like, use that for the
small case and scale it for the large one. If nothing says, pick something you
can defend in one sentence and put that sentence in the docstring.

You do **not** need to add outer loops to make short cases measurable. The
script times one call and picks a repeat count so every measured window lasts
about a second — a 40 µs edge case simply gets run twenty-five thousand times.
Write the case at its natural size.

Two things the cases must be able to show:

- that the saving is **real on the largest case** — this is what confirms;
- that the repair **does not make realistic small inputs worse**. A repair that
  wins on 200 000 elements and loses on 2 000 is a trade-off, not a fix.

Losses are judged in absolute terms, not as percentages. Joining an empty list
costs 1.3 µs where returning `""` costs 0.4, so a good repair routinely
measures three times worse on an empty case — a true statement about a quantity
nobody cares about. A loss only counts against the verdict when it is worth
more than 1% of the *largest* case's per-call cost. The report prints both
numbers so you can see which kind you are looking at.

Sizing depends on the root cause. If the card says the effect *scales with
calls* rather than with input, the large case should call the unit many times
over a small input, not once over a large one. The card's workload hint says
which.

**The shape of the large case can matter as much as its size.** Two cases of
the same repair, on the same host: a string accumulator fed 200 000 short parts
measured +18.4%, and the same accumulator fed 2 000 parts ten times the total
length measured +1.2%. Same total bytes moved, same code, and one case would
have reported a real effect while the other reported nothing. So when the
mechanism suggests a variable — a count against a length, a hit rate, a
duplicate ratio — vary that variable across your cases rather than only the
overall size, and say in the docstring which one the repair actually tracks.

## When "identical" is stricter than "the same answer"

By default `after` has to match `before` on the return value, the state of the
arguments afterwards, stdout, and the exception type. Two escape hatches exist
for the cases where that is genuinely too strict. Both are declared in the case
file, both are printed in the verdict, and both must be repeated in your report.

**The repair stops mutating the caller's data** — `lst.sort()` becomes
`sorted(lst)`, `a.extend(b)` becomes `a + b`. The answer is the same; the side
effect is not.

```python
EQUIVALENCE = "returns_only"
```

Only use it when you have checked the call sites and none of them relies on the
mutation. That check is the claim you are making, so put it in the docstring.

**The result is the same answer in a different form** — floats where the
original produced ints, an unordered collection, a tolerance on a numeric
result.

```python
def equivalent(before, after):
    """Same set of matches; the repair returns them in hash order."""
    return sorted(before) == sorted(after)
```

The docstring is required, because a comparison that always returns `True`
would otherwise turn a broken repair into a confirmed finding, and nothing in
the output would show it.

Neither hatch covers a repair that computes something different. Returning
indices where the original returned values, or being off by one, is a bug in
your repair — fix it.

## Running it

```bash
python $SKILL/scripts/verify.py cases/case_C10S4.py          # human-readable
python $SKILL/scripts/verify.py cases/case_C10S4.py --json   # for findings.json
python $SKILL/scripts/verify.py --calibrate                  # host noise floor
```

Run `--calibrate` once per session before trusting anything. It measures a
workload against an identical copy of itself; the answer must be
*insignificant*. The width of that interval is this host's resolution limit,
and it is the bar every real effect has to clear.

If calibration comes back significant, the machine is too noisy right now —
something else is running. Nothing measured in that state means anything.

## What the script does

1. **Equivalence.** For every case: same return value, same argument state
   afterwards, same stdout, same exception type. A mismatch is fatal — it means
   the repair is wrong, not that the smell is absent. Fix `after` and re-run.
2. **Scaling.** Times one call of `before`, picks a repeat count so each
   measured window lasts about a second. Shorter windows lose badly: sweeping
   the null canary on the development host gave ±8.1% at a quarter second and
   ±0.6% at one second.
3. **Paired measurement.** Both variants alternate inside one process, nine
   paired repetitions, order flipped each repetition. Paired samples must sit
   close together in time because the dominant noise source is drift in the
   machine's idle power.
4. **The canary.** The deciding case measured against *itself*, `before` versus
   `before`. The true answer is zero, so whatever it reads is contamination,
   and it is the floor every real effect has to clear.
5. **Statistics.** Savings are computed per repetition and averaged, with a 95%
   confidence interval. Energy and wall-clock time are reported separately.

## Verdicts

| Verdict | What it means | What to do |
|---|---|---|
| `confirmed` | equivalent everywhere; the large case saves significantly and clears the noise floor; nothing regresses significantly | report it, with the numbers |
| `refuted` | equivalent and measured on a clean floor, and no significant saving | **not a smell.** Report under `refuted` |
| `inconclusive` | the host's noise floor was too high to resolve an effect this size | report as inconclusive. **Do not** report it as refuted — that is a different claim |
| `regressed` | the repair made something significantly worse | not a smell. Report under `refuted`, and say which case |
| `not_equivalent` | `after` behaves differently from `before` | your repair is broken. Fix it and re-run; do not report either way |
| `advisory` | card says advisory only; never measured | report as advisory, no numbers |
| `blocked` | no runnable case file could be built | report as blocked, and say what was missing |

`refuted` and `inconclusive` findings stay in the output. A run that proposes
ten smells and has three refuted is more informative than one that quietly
drops them.

The difference between the two matters more than it looks. `refuted` says the
repair does nothing. `inconclusive` says this machine could not tell. Reporting
the second as the first writes a busy host down as evidence against the
taxonomy.

## What the numbers mean

The meter reports CPU package + DRAM energy over the workload window. On a
many-core host most of that is idle power from cores doing nothing — this
machine idles at 47.3 W and one busy Python thread takes it to 55.4 W.

That does not dilute the result the way it looks like it should, because the
window is not a fixed length: a variant that finishes sooner accrues less idle
power too. What the figure cannot do is separate a change in power draw from a
change in duration. Energy and time are therefore reported separately, and when
energy improves while wall-clock time does not, you have found something more
interesting than a performance bug — say so explicitly in the report.

## When the card is wrong

It happens, and measurement is how you find out.

C10.S4 used to say what every style guide says: growing a string with `+=` in a
loop is quadratic, so collect the parts and join them. Measured, the textbook
example got *slower* — 62 ms against 56 ms at 400 000 iterations. CPython
resizes a string in place when nothing else refers to it, so the classic
example was already linear. The real smell turned out to be about aliasing:
through an attribute, where the optimisation cannot fire, the same repair saves
94.8% ± 0.1%.

If a repair you built faithfully from a card comes back `refuted`, that is a
result. Report it, say which card, and say what you measured. Do not quietly
drop it and try a different root cause until one sticks.
