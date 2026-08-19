# Writing a catalog entry

`catalog/C*.yaml` is the source for every level-2 knowledge card. One entry per
root cause, rendered by `build/cards.py`. This file says what an entry has to
contain and why each part exists.

Read `catalog/C5.yaml` first — it is the worked example, and the standard.

---

## The audience

A coding agent that has just read an unfamiliar function and formed a rough
suspicion. It opens this card to decide whether the suspicion is *this* root
cause, and if so, what exactly to change. It will not have measured anything
yet, it cannot ask anyone, and it will believe what the card says.

So the card has to survive being taken literally.

## Fields

```yaml
- id: C7.S4
  in_one_line: >
    ...
  signals: [sort_then_slice, filter_after_transform]   # analyzer kinds, optional
  what_to_look_for: >
    ...
  not_a_smell_when:
    - >
      ...
  counter_examples:
    - code: |
        ...
      why: >
        ...
  refactoring:
    summary: one line, imperative
    examples:
      - title: ...
        before: |
          ...
        after: |
          ...
        note: >
          ...
  patch_shape: expression | statement_local | signature | structural | cross_unit
  measurability: scales_with_input | scales_with_calls | constant_small
  min_workload_hint: >
    ...
  similar: [C3.S6, C4.S1]
  notes: >
    ...
```

Any key not on that list is a build error. A misspelled one used to be ignored
silently and take a whole section of a card with it.

### `in_one_line` — what this root cause hunts for

One clause, lower case, no full stop. Written as a thing to look for rather
than as a definition: "an inner loop that searches, where a lookup would turn
n*m into n+m", not "inefficient nested iteration".

It is written once and rendered in three places — the category card's table,
the full index the agent sweeps at the end of step 2, and every *other* card
that lists this one under `similar`. That is what keeps those three consistent,
and it means each card describes its neighbours in the neighbours' own words.

Precise enough to recognise something by; not enough to decide anything from.

### `what_to_look_for` — the symptom and its cost, together

One passage, five to twelve sentences. It has to do two jobs at once:

- **the cost, mechanically.** What gets allocated, copied, hashed, dispatched,
  re-entered, or paid per element, and how that scales. Not "this is slower" —
  *why* it is slower. Without this a card teaches a shape to match, and an agent
  that has only learned shapes cannot tell a smell from its near-miss.
- **the symptom, in general terms.** What the redundancy looks like, what
  usually decides the case, and what most often makes the pattern correct as
  written. Name the one or two checks that reject most candidates, and say what
  each turns on.

**Write it as prose, not as a checklist.** This field replaced a numbered
`how_to_tell` whose every step had to hold, and the numbering was the problem:
under a definitive heading, a list of steps reads as the set of permitted cases,
and an agent that has learned the enumerated shapes rejects everything else. The
expensive instances of most of these root causes are the ones nobody enumerated.

Concrete shapes belong in `refactoring.examples`, where they read as
illustrations. Facts belong here — `in` is linear on a list and a probe on a
set, a `for` loop evaluates its iterable once, a log call's arguments are built
before the level is checked. Carry every fact the old steps carried; drop only
the framing that made them a gate.

Cite a measurement if there is one, with the number and what it was measured
on. `validation/results/` and `SAMPLE_NUANCES.md` are the only sources.

### `not_a_smell_when` — contexts where the pattern is correct

Where the pattern is present and is the right call. Every pattern in this
taxonomy is right somewhere; this is where that goes.

Aim for four or five. Include at least one about *size* (too small to matter),
one about *semantics* (the repair would change behaviour), and one about
*boundaries* (an API, a caller, a format fixes the choice).

### `counter_examples` — looks the same, is not

Runnable code that matches the pattern and is correct as written, plus the one
difference that makes it so.

**This is the highest-value field on the card.** A second positive example
teaches nothing a first one did not; what decides a hard case is the near-miss.
C10.S4 is the proof: three examples of `s += x` in a loop would all have been
wrong, because what separates the smell from the non-smell is the assignment
target — `out +=` against `self.buf +=`.

One or two per root cause. Prefer near-misses that a competent reader would
actually get wrong, especially ones this project has measured. Do not invent
measurements; if you cite a number, it must come from `SAMPLE_NUANCES.md` or
`validation/results/`.

### `refactoring.examples` — one to three before/after pairs

One is enough when the repair genuinely is one expression. Most root causes need
two or three, and they must show **different things**, not the same edit twice:

1. **the plain case** — the repair at its simplest, so the shape is clear;
2. **the real case** — the same repair where the waste and the fix are in
   different places: different methods, a caller and a callee, a value shaped
   wrongly three functions earlier. This is what code actually looks like, and
   a card that only shows one-liners teaches an agent to only find one-liners;
3. **a different form of the same root cause** — when the root cause covers more
   than one shape, show the second one.

Each example takes a `title` (a short phrase, lower case) and a `note` (one to
three sentences: what changed, why it costs less, and what you had to check
before making the edit).

The `before` must be code someone would plausibly write. Do not write
`if items: if items:` — nobody writes that, and a card whose example is a
strawman gets pattern-matched against nothing.

### `similar` — where else to look

A bare list of root cause IDs. The renderer fills each one in with that card's
own `in_one_line`, so there is no prose to write and none to keep in sync.

This is not a discrimination test, and it deliberately no longer carries one.
Two agents that repair the same waste and file it under two overlapping root
causes have both done the job, as long as each repair matches the definition it
was filed under — so the paragraphs that used to defend each distinction were
defending something the project does not need. What a reader actually needs is
a way out of a card that nearly fits.

Two to four each, and include cross-category ones: those are the neighbours a
reader will never open by accident.

**The relation is symmetric.** `load_catalog` mirrors every edge, so writing it
once on either side is enough, and a card can end up listing a neighbour it does
not itself name. That is intended — a neighbour reachable in one direction only
is a dead end for whichever reader arrives from the wrong side.

### `patch_shape`

What the repair *changes*. Not a limit on how much code may be read.

- `expression` — one expression, nothing else
- `statement_local` — a few adjacent statements
- `signature` — the signature or decorators; body untouched
- `structural` — control flow or data structures reorganised. **May span the
  methods of one class or one call chain** — building an index in `__init__`
  and reading it in a method is one structural repair
- `cross_unit` — has to change call sites outside the code being repaired

### `measurability`

- `scales_with_input` — the effect grows with data size
- `scales_with_calls` — it grows with call count, so the largest case must call
  the unit many times over a small input
- `constant_small` — a fixed tiny cost per execution that no workload can lift
  above a noise floor. Rendered as **advisory only**: reported, never measured.
  Use it honestly; it is the difference between an unmeasurable claim and a
  claim measured badly.

---

## What measurement may and may not change

The taxonomy is the reference. Its 65 root causes come from a literature
review, and `description` and `example` render verbatim from the spreadsheet.
**Nothing measured here revises them, and no authored field may argue that one
of them is wrong.** A repair that fails to pay, on one host, in the shapes we
happened to try, is a fact about those shapes -- not evidence that the root
cause is imaginary.

What measurement is for is the authored half: saying where a root cause pays,
how much, and where it does not, so an agent knows what to expect before it
spends a measurement of its own.

Every root cause has three case files under `validation/taxonomy/`, deliberately
different in shape, each with large / normal / edge cases and, where the card
makes a conditional claim, a case that puts the condition on the wrong side.
Write the results in according to what they show:

**All three pay.** Put the derivation in `what_to_look_for` -- what the size
tracks, roughly how big it gets, what the numbers were. That is the most useful
thing a card can carry, because it lets the agent size a candidate before
building anything.

**Some pay and some do not.** Say in `what_to_look_for` what to expect in
general and what decides it. Put the shapes that did not pay into
`not_a_smell_when` and `counter_examples`, with the readings. And put **only
the shapes that paid** into `refactoring.examples` -- an example the agent is
told to copy should be one that worked.

**None of them pay.** Do not reject the root cause and do not write it down as
refuted. Say plainly that the repair did not pay in the shapes tried, that it
may still pay in ones we did not, and leave the judgement with the agent for
its own context. Mark it advisory if the mechanism says the effect is
constant-small; otherwise let the agent decide and measure. The definition
stands either way -- read it and it makes sense, and Python may simply not be
where the mechanism shows.

Phrase all of this as *where to expect it to work*, never as a correction. "The
description names X; measured here it costs more, because ..." is right. "The
description is wrong about X" is not.

## House rules

**Consistency inside a card.** If you change the repair, re-read
`in_one_line`, `what_to_look_for`, the exceptions and the near-misses and make
them agree. A card whose symptoms describe one thing and whose repair shows
another is worse than either half alone. Changing `in_one_line` reaches further
than the card it sits on, since every neighbour renders it.

**Fidelity to the taxonomy.** The `description` and `example` come from the
published spreadsheet and are rendered above your text. Your fields must be
about the same root cause the description defines — narrower is fine, different
is not. **Never invent a root cause, never widen one to cover something the
description excludes, and never write a card that argues its own description is
mistaken.**

**No fabricated numbers.** Cite a measurement only if it appears in
`SAMPLE_NUANCES.md` or `validation/RESULTS.md`. Everything else is mechanism, not
measurement.

**Voice.** Plain declarative sentences. Say what to do and why. No hedging
adverbs, no "simply", no exclamation marks. British spelling.

## YAML gotchas

A plain scalar cannot contain `": "` — YAML reads it as a mapping key. Every
prose item under `not_a_smell_when` is therefore written as a folded block:

```yaml
  not_a_smell_when:
    - >
      the type is fixed by an API boundary: a caller's argument, or a return
      value other code depends on
```

`in_one_line`, `what_to_look_for`, `why`, `note` and `min_workload_hint` use
`>` for the same reason. `code`, `before` and `after` use `|`, which preserves
newlines.

After editing, run `python -m build` from the project root. It validates the
catalog against the taxonomy and will tell you what is wrong.
