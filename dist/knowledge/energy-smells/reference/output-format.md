# Output format

A run leaves two files in the directory it was started in. They are your
record of the work, not edits to the code:

- **`findings.jsonl`** — what you did, one JSON line per step per unit,
  appended as you go.
- **`submissions.jsonl`** — the repairs, one per line. The script measures each
  and writes the result into it.

Nothing else is written. Your summary at the end of the run is your final
message, not a file.

---

## findings.jsonl

One JSON object per line, tagged with the step that produced it, in the order
you produced them. Shown expanded here; each is written on a single line.

```jsonc
{"step": 1, "target": "src/", "unit_limit": 10, "units_considered": 128,
 "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize"]}
```

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
    {"label": "a", "root_cause": "C10.S4", "lines": [47],    "confidence": "high",
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "found_by": "reading"},
    {"label": "b", "root_cause": "C3.S2",  "lines": [44,45], "confidence": "medium",
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row",
     "found_by": "sweep"}
  ]
}
```

```jsonc
{"step": 2, "unit": "src/parse.py::tokenize",
 "what_it_does": "splits a header into fields",
 "cost_driver": "one pass over a header of at most 16 bytes",
 "own_hypotheses": ["nothing here scales — the loop is bounded by the header"],
 "suspicions": [],
 "cleared_because": "no work here is proportional to input size"}
```

Step 3 and step 4 records are shown in `SKILL.md`, at those steps: one per unit
with suspicions, listing `decisions` and `outcomes` by `label`.

### Field rules

**`label`** names a suspicion within its unit — `a`, `b`, `c` — and is how steps
3 and 4 refer to it. A suspicion added in step 3 gets a label of its own.

**`why`** must be specific to this code. Name the variable, the line, the
structure. "Inefficient string handling" is not a reason; "`self.buf` is grown
with `+=` across `rows`" is.

**`hotness`**, on a step-3 decision, is how often the code runs and how large
its inputs get. It is what a reader checks when a saving looks marginal, and
what you size the five cases from.

**`own_hypotheses`** is what you thought before opening any card. Without it there is
no way to tell whether you read the code or the labels.

**`found_by`**, on every suspicion, records how you came to suspect it:
`reading`, `sweep` for the index pass at the end of step 2, or `cards` for a
root cause that first appeared while you were reading a card in step 3. It is
the difference between an analysis you did and a list you were handed, and it
is measured across runs, so record it honestly — including the cases where you
missed something.

**`also_considered`**, optional on a step-3 decision, names the similar cards
you opened and did not file this under. Not a requirement to prove one card
excludes another — these overlap on purpose — but a record of where you looked.

**`unit_limit`**, in step 1, is the number of units you were asked to
examine, or `null` when you were not given one and examine the whole target.

**`outcomes`**, in step 4, gives every accepted suspicion exactly one of:
`submission` (an `id` in `submissions.jsonl`), `same_repair_as` (the `id` of
the submission that already makes this edit), `blocked` (why no repair could
be measured), or `deferred` (accepted, but outside the repairs chosen for
measurement). A deferred suspicion is still a finding.

Every unit from step 1 has a step-2 record, and every suspicion is accounted
for: rejected in step 3, or given an outcome in step 4. A run that examined
three functions and one that examined three hundred have to be
distinguishable, and so do a suspicion you dropped and one you forgot.

---

## submissions.jsonl

The fields are in `$SKILL/reference/verifying.md`. Three rules connect it to the
findings:

- every `submission` in a step-4 record names a line here, and every line here
  is named by exactly one;
- every line ends with the `agent_measurement` the script wrote. Never write
  or edit it, and never write a verdict anywhere yourself;
- every measured repair stays, whatever its verdict.

What the script writes into a line:

```jsonc
"agent_measurement": {
  "status": "confirmed",
  "reason": "25.9% +-3.0% energy saved on 'many-rows', clearing the 1.4% noise floor. ...",
  "profile": "fast",
  "noise_floor_pct": 1.4,
  "noise_floor_from": "session calibration",
  "equivalence_relaxed": [],      // weakenings of the check; repeat them wherever the saving is quoted
  "stubbed": [],                  // uninstalled packages stood in for while loading; normally empty
  "per_case": [
    {"label": "typical", "repeats": 9500, "clamped": false,
     "before_energy_j": 51.03, "after_energy_j": 47.29,
     "before_time_s": 1.04, "after_time_s": 0.96,
     "energy_ci_pct": 1.2, "significant": true}
    // ... one row per case, all five
  ],
  "submission_hash": "3f2a9c01d4e5b6a7"
  // abridged: a few more fields record provenance -- the meter, its coverage, the canary case
}
```

`per_case` carries joules and seconds for each version on every case, and no
percentage: the joules are the result, and a percentage stored beside them is a
second copy that can disagree. `energy_ci_pct` is not a saving — it is the
half-width of the 95% interval on the paired comparison, which `significant`
is judged from.
