# Output format

A run leaves four files in the repository's root — the directory you were
started in, next to its README — and nowhere else: not in a subdirectory, not
in a scratch directory. They are your record of the work, not edits to the
code, so writing them there does not touch the repository:

- **`step1.jsonl`**, **`step2.jsonl`**, **`step3.jsonl`** — what each step
  produced, one JSON line per record. Each is finished with
  `python $SKILL/scripts/step.py done N`, and read-only after that.
- **`submissions.jsonl`** — the repairs, one per line, written in step 3. The
  script measures each and writes the result into it.

Nothing else is written. Your summary at the end of the run is your final
message, not a file.

---

## step1.jsonl to step3.jsonl

One JSON object per line, in the file of the step that produced it, each
tagged with its step.

**Every record has exactly the keys listed for it — all of them, every time,
and no others.** A key with nothing to say is `null` or `[]`, never left out.
The same keys in every run are what make runs comparable.

| Record | One per | Keys |
|---|---|---|
| step 1, in `step1.jsonl` | unit where something may be wasteful | `step`, `unit`, `suspicions` |
| step 2, in `step2.jsonl` | unit on the step-1 list | `step`, `unit`, `what_it_does`, `decisions` |
| step 3, in `step3.jsonl` | unit with an accepted suspicion | `step`, `unit`, `outcomes` |
| a suspicion, in `suspicions` | | `label`, `root_cause`, `lines`, `why` |
| a decision, in `decisions` | | `label`, `root_cause`, `lines`, `verdict`, `why` |
| an outcome, in `outcomes` | | `label`, `outcome`, `submission`, `why` |

Step 4 writes no record: its output is your final message.

Shown expanded here; each is written on a single line.

```jsonc
{"step": 1, "unit": "src/render.py::Report.render", "suspicions": [
  {"label": "a", "root_cause": "C10.S4", "lines": [47],
   "why": "`self.buf` is grown with += once per row; nothing reads it in the loop"},
  {"label": "b", "root_cause": "C3.S2",  "lines": [44,45],
   "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row"}
]}
```

```jsonc
{"step": 2, "unit": "src/router.py::Router.allowed",
 "what_it_does": "checks each request against `self.blocked`, a list built once in __init__",
 "decisions": [
  {
    "label": "a", "root_cause": "C5.S2", "lines": [58], "verdict": "rejected",
    "why": "`Looks like it, but is not` — nothing needs the list's order, so the container's type changes rather than an index being added beside it. Added `b` instead."
  },
  {
    "label": "b", "root_cause": "C5.S1", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request, built in __init__ at line 31 and read nowhere else; as a set each search is one hash lookup"
  }
]}
```

```jsonc
{"step": 3, "unit": "src/render.py::Report.render", "outcomes": [
  {"label": "a", "outcome": "submitted",      "submission": "C10S4-render-concat", "why": null},
  {"label": "b", "outcome": "same_repair_as", "submission": "C10S4-render-concat", "why": null},
  {"label": "c", "outcome": "blocked",        "submission": null, "why": "inputs.py: no inputs could be generated: every call opens a database connection"},
  {"label": "d", "outcome": "deferred",       "submission": null, "why": "outside the 20 repairs measured"}
]}
```

### Field rules

**`label`** names a suspicion within its unit — `a`, `b`, `c` — and is how steps
2 and 3 refer to it. A suspicion added in step 2 gets a label of its own.

**`lines`** is a list of line numbers in the unit's file.

**`why`** is the reason, under one name everywhere. On a suspicion: what looks
wasteful. On a decision: what decided it — for `accepted`, the mechanism, what
work stops happening; for `rejected`, the check that failed. On an outcome: why
it was `blocked` or `deferred`, and `null` otherwise. It must be specific to
this code: name the variable, the line, the structure. "Inefficient string
handling" is not a reason; "`self.buf` is grown with `+=` across `rows`" is.

**`verdict`** is `"accepted"` or `"rejected"`.

**`what_it_does`**, in step 2, is one sentence: what the unit computes, and
where its work goes. It is written after reading the unit in full, which is
what it shows.

**`root_cause`** is one of the 65 IDs exactly as its card names it, such as
`C5.S1` — never a category such as `C5`. In step 1 it is the one the index
line matched; step 2 settles it against the card.

**`outcome`**, in step 3, is one of: `submitted` (`submission` is its `id` in
`submissions.jsonl`), `same_repair_as` (`submission` is the `id` of the
submission that already makes this edit), `blocked` (the tools showed no repair
can be measured here — inputs that could not be generated, a module that does
not load, a repair that cannot be made to behave identically — and `why`
quotes that message) or `deferred` (accepted, and not measured: outside the 20,
or never tried). A suspicion you did not ask inputs for is `deferred`, not
`blocked`. A deferred suspicion is still a finding.

Every unit from step 1 has a step-2 record, and every suspicion is accounted
for: rejected in step 2, or given an outcome in step 3. A run that examined
three functions and one that examined three hundred have to be
distinguishable, and so do a suspicion you dropped and one you forgot.

---

## submissions.jsonl

Every line has every field listed in `$SKILL/reference/verifying.md` — none
are optional, and no others are accepted. Three rules connect it to the
step files:

- every outcome `submitted` in `step3.jsonl` names a line here, and every line
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
  "equivalence_relaxed": [],      // what this environment weakened (stand-in packages, skipped statements); repeat wherever the saving is quoted
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
