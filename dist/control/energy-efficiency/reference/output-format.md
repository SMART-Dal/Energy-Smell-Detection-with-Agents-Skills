# Output format

A run leaves five files in the repository's root — the directory you were
started in, next to its README — and nowhere else: not in `.energy-scan/`, not
in a scratch directory. They are your record of the work, not edits to the
code, so writing them there does not touch the repository:

- **`step1.jsonl`**, **`step2.jsonl`**, **`step3.jsonl`**, **`step4.jsonl`** —
  what each step produced, one JSON line per record. Each is finished with
  `python $SKILL/scripts/step.py done N`, and read-only after that.
- **`submissions.jsonl`** — the repairs, one per line, written in step 4. The
  script measures each and writes the result into it.

Nothing else is written. Your summary at the end of the run is your final
message, not a file.

---

## step1.jsonl to step4.jsonl

One JSON object per line, in the file of the step that produced it, each
tagged with its step.

**Every record has exactly the keys listed for it — all of them, every time,
and no others.** A key with nothing to say is `null` or `[]`, never left out.
The same keys in every run are what make runs comparable.

| Record | One per | Keys |
|---|---|---|
| step 1, in `step1.jsonl` | run | `step`, `target`, `unit_limit`, `units_considered`, `will_examine` |
| step 2, in `step2.jsonl` | unit on the step-1 list | `step`, `unit`, `what_it_does`, `cost_driver`, `own_hypotheses`, `suspicions`, `cleared_because` |
| step 3, in `step3.jsonl` | unit with suspicions | `step`, `unit`, `decisions` |
| step 4, in `step4.jsonl` | unit with an accepted suspicion | `step`, `unit`, `outcomes` |
| a suspicion, in `suspicions` | | `label`, `lines`, `why` |
| a decision, in `decisions` | | `label`, `lines`, `verdict`, `why` |
| an outcome, in `outcomes` | | `label`, `outcome`, `submission`, `why` |

Step 5 writes no record: its output is your final message.

Shown expanded here; each is written on a single line.

```jsonc
{"step": 1, "target": "src/", "unit_limit": null, "units_considered": 128,
 "will_examine": ["src/render.py::Report.render", "src/parse.py::tokenize",
                  "src/parse.py::Lexer.advance", "src/index.py::Index.add",
                  "src/index.py::Index.lookup", "src/export.py::write_rows",
                  ...]}   // shortened here: every unit you will get through, hottest first
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
    {"label": "a", "lines": [47],
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop"},
    {"label": "b", "lines": [44,45],
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row"}
  ],
  "cleared_because": null
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

```jsonc
{"step": 4, "unit": "src/render.py::Report.render", "outcomes": [
  {"label": "a", "outcome": "submitted",      "submission": "render-concat", "why": null},
  {"label": "b", "outcome": "same_repair_as", "submission": "render-concat", "why": null},
  {"label": "c", "outcome": "blocked",        "submission": null, "why": "every input needs a live database connection"},
  {"label": "d", "outcome": "deferred",       "submission": null, "why": "outside the 20 repairs measured"}
]}
```

### Field rules

**`label`** names a suspicion within its unit — `a`, `b`, `c` — and is how steps
3 and 4 refer to it. A suspicion added in step 3 gets a label of its own.

**`lines`** is a list of line numbers in the unit's file.

**`why`** is the reason, under one name everywhere. On a suspicion: what looks
wasteful. On a decision: what decided it — for `accepted`, the mechanism, what
work stops happening; for `rejected`, the check that failed. On an outcome: why
it was `blocked` or `deferred`, and `null` otherwise. It must be specific to
this code: name the variable, the line, the structure. "Inefficient string
handling" is not a reason; "`self.buf` is grown with `+=` across `rows`" is.

**`verdict`** is `"accepted"` or `"rejected"`.

**`own_hypotheses`** is what you thought before naming anything. Without it there is
no way to tell whether you read the code or the labels.

**`cleared_because`** says why a unit with `"suspicions": []` is clean; it is
`null` when there are suspicions.

**`unit_limit`**, in step 1, is the number of units you were asked to
examine, or `null` when you were not given one and examine the whole target.

**`outcome`**, in step 4, is one of: `submitted` (`submission` is its `id` in
`submissions.jsonl`), `same_repair_as` (`submission` is the `id` of the
submission that already makes this edit), `blocked` (no repair could be
measured) or `deferred` (accepted, and not measured). A deferred suspicion is
still a finding.

Every unit from step 1 has a step-2 record, and every suspicion is accounted
for: rejected in step 3, or given an outcome in step 4. A run that examined
three functions and one that examined three hundred have to be
distinguishable, and so do a suspicion you dropped and one you forgot.

---

## submissions.jsonl

Every line has every field listed in `$SKILL/reference/verifying.md` — none
are optional, and no others are accepted. Three rules connect it to the
step files:

- every outcome `submitted` in `step4.jsonl` names a line here, and every line
  here is named by exactly one;
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
    // ... one row per input, all four
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
