# Writing a catalog entry

`catalog/C*.yaml` is the source for every level-2 card. One entry per root
cause, rendered by `build/cards.py`. This file says what an entry contains,
where each part comes from, and what may be written by hand.

---

## The audience

A coding agent that has read an unfamiliar function and formed a rough
suspicion. It opens the card to decide whether the suspicion is *this* root
cause and what the repair looks like. It cannot ask anyone, and it will believe
what the card says -- so nothing on a card may be a guess.

## The card

| section | comes from |
|---|---|
| Definition, Example from the reference | the taxonomy spreadsheet, verbatim |
| What to look for | `look_for` -- written |
| Repair: the one-line summary | `refactoring.summary` -- written once, also in the category table |
| Repair: each sample's title | `validation/alignment/decisions.yaml`, else the case file's docstring |
| Repair: before / after | the case file under `validation/taxonomy/`, extracted with its helpers |
| Repair: the **Measured** line | the latest run in `validation/results/taxonomy.jsonl` |
| Repair: the note under a sample | `repairs[].note` -- carried over from the old card |
| Looks like it, but is not | `not_this` -- written, each with a checkable `source` |
| Similar root causes | `similar` ids; each neighbour's own `in_one_line` |

How to read a card -- that the repairs are ideas rather than templates, what
each **Measured** action means, that a matching pattern does not guarantee a
saving -- is said once in SKILL.md's step 3, never on a card.

## Fields

```yaml
- id: C3.S7
  signals:
  - mutation_during_iteration
  in_one_line: |
    a collection edited while it is being walked
  look_for: |
    ...three or four lines...
  refactoring:
    summary: build the items to keep into a new collection instead of editing the one being walked
  repairs:
  - case: C3S7_mutation_in_loop
    note: |
      ...
  - case: C3S7_delete_while_scanning
  excluded:
  - case: C3S7_iterating_a_snapshot
    reason: |
      its after applies C7.S1's repair, not this one's
  not_this:
  - title: a work list that is meant to grow
    source: rule:mutation_during_iteration/work_list
    code: |
      ...
    tempting: |
      ...
    why: |
      ...
  similar:
  - C6.S2
```

Any other key is a build error.

### `in_one_line` -- what this root cause hunts for

One clause, lower case, no full stop, written as a thing to look for. It renders
in the category table, the full index, and every card that lists this one as
similar.

### `look_for` -- what to look for

Three or four lines: what the waste looks like in code, and what the machine
does that it need not. Written **only** from

- this root cause's case files (`validation/taxonomy/<C>S<n>_*.py`: the
  `before` functions and the docstrings),
- the positives of this entry's rules: the functions named in `EXPECTED` in
  `tests/rules/<signal>/test_main.py`, for each of the entry's `signals` that
  has a directory there,
- the entry's previous `what_to_look_for` and `notes`.

Say what the root cause *is*. What it is not belongs in `not_this`. No claim the
sources do not make, and no numbers.

### `repairs` -- every sample, in order

One item per case file of this root cause, already listed. Only `note` is
authored, and it is carried over verbatim from the old card. Edit a note only
to:

- shorten it to one or two sentences, keeping the fact that is specific to
  this sample;
- delete it when it only restates what the before/after shows;
- remove anything the **Measured** line contradicts (it says the repair saves,
  and the sample cost more), any measured number, and any mention of advisory
  status, patch shape, measurability, workload hints, subsumption or case
  files.

Never add a claim a note did not make.

### `excluded` -- a sample that repairs another root cause

When a case file's `after` applies a *different* root cause's repair -- its
docstring says so, or the change is plainly that root cause's -- move it from
`repairs` to `excluded`, with a one-line `reason` naming the other root cause.
A sample is never excluded for costing more: that is what **Try both
directions** is for. The build checks that every case file is either shown or
excluded.

### `not_this` -- looks like it, but is not

At most five. Each is code that has this root cause's pattern where applying
this card's repair would be wrong, because it changes what the code does --
results, errors, order, laziness, side effects, memory bounds, concurrency --
or undoes something the author did on purpose. Each has:

- `title` -- what makes this one different, lower case;
- `code` -- the code as found;
- `tempting` -- this card's repair applied to it, as an agent would write it;
- `why` -- one or two sentences: what the tempting repair breaks;
- `source` -- where it comes from, checked by the build:
  - `catalog` -- the entry's previous `not_a_smell_when` or `counter_examples`;
  - `rule:<rule>/<function>` -- a negative in that rule's fixtures
    (`tests/rules/<rule>/test_cases.py`, not in `EXPECTED`);
  - `known` -- documented Python behaviour, which `why` names. Use sparingly.

Not a near-miss:

- a validation sample from `validation/taxonomy/`;
- anything a measured repair on the same card contradicts (a shape a sample
  confirmed is not "not a smell");
- "the input is small" or "the code is not hot" -- that is for the
  measurement, not the card;
- a rule negative that differs trivially (another variable, no loop, already
  repaired, a different type) -- those test the rule, they teach nothing;
- a shape that is simply another root cause -- that is what `similar` is for.

Fewer than five is fine; none is fine when no source has a good one.

### `similar` -- where else to look

A list of root cause ids, rendered with each neighbour's own `in_one_line`.
`load_catalog` mirrors every edge, and a card may end up with at most five.

### Retired keys

`what_to_look_for`, `not_a_smell_when`, `counter_examples`, `notes` and
`refactoring.examples` belong to the old card. An entry with `repairs` must not
carry them. `patch_shape`, `measurability` and `min_workload_hint` are
accepted and ignored (`RETIRED_KEYS`), and are no longer written.

---

## What measurement may and may not change

The taxonomy is the reference. Its 65 root causes come from a peer-reviewed
literature review, and the definition and example render verbatim. **Nothing
measured here revises them, and no authored field may argue that one of them is
wrong.** A repair that cost more on one host, in the shapes we tried, is a fact
about those shapes.

So the cards never hide a regressed sample and never explain it away. Its
**Measured** line says what happened and tells the agent to try both
directions; the definition stands either way.

## House rules

**Consistency inside a card.** `in_one_line`, `look_for`, the notes and the
near-misses must agree with each other and with the measured repairs. A card whose symptoms describe one thing and whose repair shows
another is worse than either half alone. Changing `in_one_line` reaches further
than the card it sits on, since every neighbour renders it.

**Fidelity to the taxonomy.** The `description` and `example` come from the
published spreadsheet and are rendered above your text. Your fields must be
about the same root cause the description defines — narrower is fine, different
is not. **Never invent a root cause, never widen one to cover something the
description excludes, and never write a card that argues its own description is
mistaken.**

**No fabricated numbers.** The result line under each repair carries the
measurement; authored text carries none. Complexity (`O(n*m)`) is mechanism and
is fine.

**Voice.** Plain declarative sentences. Say what to do and why. No hedging
adverbs, no "simply", no exclamation marks. British spelling.

## YAML

`code`, `tempting`, `look_for`, `note`, `why` and `reason` are block scalars
(`|`). A plain scalar cannot contain `": "` -- YAML reads it as a mapping key.

Check an entry without building `dist/`:

    .venv/bin/python <preview.py> --check C3.S7     # problems only
    .venv/bin/python <preview.py> C3.S7             # problems and the rendered card

`python -m build` validates the whole catalog against the taxonomy and writes
`dist/`.
