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
  signals: [sort_then_slice, filter_after_transform]   # analyzer kinds, optional
  mechanism: >
    ...
  how_to_tell:
    - >
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
  discriminators:
    - vs: C3.S6
      rule: >
        ...
  notes: >
    ...
```

### `mechanism` — where the energy goes

Two to five sentences on **what the machine does differently**, in terms of
work: what gets allocated, copied, hashed, dispatched, re-entered, or paid per
element, and how that scales.

This is the field that turns a pattern into a cost the reader can reason about.
Without it a card teaches a shape to match, and an agent that has only learned
shapes cannot tell a smell from its near-miss.

Not "this is slower". *Why* it is slower, mechanically.

### `how_to_tell` — the recognition procedure

Three to six **full sentences**, in the order you would actually check them.
Each one names something to look at in the code and says what would settle it.
Every step must hold for the root cause to apply.

This replaced a field called `preconditions`, which was a list of terse clauses.
Two things went wrong with those, and both are easy to reintroduce:

- **Unreadable without the answer.** "the container's construction site is
  editable" tells someone who already knows what to do exactly nothing new.
  Write "Find where the container is built. The repair changes that line, so if
  it is built somewhere you cannot edit, the repair is not available."
- **Read instead of the card.** A short checklist under a definitive heading
  invites the description above it to be skipped. These steps are written to be
  read *after* the description, and they should sound like it — they add the
  operational detail the paper's prose does not carry.

Order matters. Put the step that rejects most candidates first.

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
measurements; if you cite a number, it must come from `NUANCES.md`.

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

### `discriminators` — neighbours

Root causes that match similar-looking code. Written in terms of **what the
repair changes**, because prose descriptions overlap where repairs do not.

These are rendered as an invitation to open the neighbour's card, not as an
exclusion test: when two fit, the reader is told to pick the one whose repair
they would actually write, and to say so if it was a coin toss. They are also
the "I am stuck, where else should I look" list.

Two or three each. Include cross-category neighbours — those are the ones a
reader will never open by accident.

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

## House rules

**Consistency inside a card.** If you change the repair, re-read the mechanism,
the steps, the exceptions and the neighbours and make them agree. A card whose
`how_to_tell` describes one thing and whose `refactoring` shows another is worse
than either half alone.

**Fidelity to the taxonomy.** The `description` and `example` come from the
published spreadsheet and are rendered above your text. Your fields must be
about the same root cause the description defines — narrower is fine, different
is not. **Never invent a root cause, never widen one to cover something the
description excludes.**

**No fabricated numbers.** Cite a measurement only if it appears in
`NUANCES.md` or `validation/RESULTS.md`. Everything else is mechanism, not
measurement.

**Voice.** Plain declarative sentences. Say what to do and why. No hedging
adverbs, no "simply", no exclamation marks. British spelling.

## YAML gotchas

A plain scalar cannot contain `": "` — YAML reads it as a mapping key. Every
prose item under `how_to_tell` and `not_a_smell_when` is therefore written as a
folded block:

```yaml
  how_to_tell:
    - >
      Name the operation this container is used for most often on the hot
      path: membership, positional access, ordered traversal.
```

`mechanism`, `why`, `note`, `rule` and `min_workload_hint` use `>` for the same
reason. `code`, `before` and `after` use `|`, which preserves newlines.

After editing, run `python -m build` from the project root. It validates the
catalog against the taxonomy and will tell you what is wrong.
