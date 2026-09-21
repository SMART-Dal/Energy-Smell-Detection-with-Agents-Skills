# Output format

A run produces two files in the target repository's working directory:

- **`findings.json`** — the record. Everything downstream reads this.
- **`REPORT.md`** — the same content in prose, rendered *from* the JSON.

Write the JSON first, then the report from it. If the two disagree, the JSON is
right.

---

## findings.json

```jsonc
{
  "schema_version": 2,

  "target": {
    "path": "/home/me/repos/acme-parser",
    "commit": "a1b2c3d",                  // null if not a git checkout
    "files_scanned": 120,
    "units_examined": 15
  },

  "config": {
    "agent": "claude-code",
    "model": "claude-opus-5",
    "noise_floor_pct": 1.6                // from `verify.py --calibrate`
  },

  "findings": [
    {
      "unit": "src/render.py::Report.render",
      "line": 42,

      "why": "`self.buf` is grown with += across `rows` and is never read inside the loop, so the accumulation is O(n^2) in the total output length.",
      "hotness": "called once per HTTP response; `rows` is typically 5k-50k long",
      "found_by": "reading",

      "subsumed": [
        {"what": "the per-row temporary list", "why": "it only existed to feed the +=; the repair removed it"}
      ],

      "spans_units": ["src/render.py::Report.render"],

      "repair": {
        "summary": "collect the parts in a list and join once after the loop",
        "diff": "-    self.buf += _row(r)\n+    parts.append(_row(r))"
      },

      "verification": {
        "status": "confirmed",
        "case_file": "cases/case_render_concat.py",
        "cases_checked": 2,
        // No case is promoted to the top of the row. `status` says whether
        // every case improved, some did, or none did; `per_case` carries what
        // each one measured, in joules and seconds. No percentage is stored --
        // it is a view of those numbers, and keeping a derived figure beside
        // its inputs lets the two disagree.
        "noise_floor_pct": 1.6,
        // Which case the floor was measured on. Provenance for that one
        // number, not a headline.
        "canary_case": "large",
        "equivalence_relaxed": [],
        "per_case": [
          // Each case is judged on its own: significant, and clearing the
          // floor. Compare the joules yourself to see which input matters.
          {"label": "small", "repeats": 9500, "clamped": false,
           "before_energy_j": 151.0300, "after_energy_j": 137.2900,
           "before_time_s": 3.0400, "after_time_s": 2.7700,
           // Not a saving: half-width of the 95% interval on the paired
           // per-repetition comparison. `significant` needs it.
           "energy_ci_pct": 1.2, "significant": true},
          {"label": "large", "repeats": 40, "clamped": false,
           "before_energy_j": 148.2100, "after_energy_j": 109.8200,
           "before_time_s": 3.0100, "after_time_s": 2.2300,
           "energy_ci_pct": 3.0, "significant": true}
        ]
      }
    }
  ],

  "negligible": [
    // Same object shape. Candidates that were accepted at step 3, repaired,
    // measured, and moved nothing more than the noise on a clean floor. Keep
    // them: a repair that turned out not to help is a result, not a failure to hide.
  ],

  "mixed": [
    // Same object shape. The repair pays on some inputs and costs on others.
    // Report both, and say which input each applies to.
  ],

  "regressed": [
    // Same object shape. Worse everywhere it measurably moved.
  ],

  "inconclusive": [
    // Same object shape. Measured, but the host could not resolve an effect
    // this size. A different claim from `negligible` — do not merge the two.
    // `negligible` is evidence about the code; this is a fact about the host.
  ],

  "units_examined": [
    {
      "unit": "src/parse.py::tokenize",
      "what_it_does": "splits a header into fields",
      "own_hypotheses": ["nothing here scales — the loop is bounded by a 16-byte header"],
      "suspicions": [],
      "cleared_because": "no work here is proportional to input size"
    },
    {
      "unit": "src/render.py::Report.render",
      "what_it_does": "renders one HTML table from a list of row dicts",
      "own_hypotheses": ["the output string is rebuilt on every row"],
      "suspicions": [
        {"lines": [47],    "confidence": "high"},
        {"lines": [44,45], "confidence": "medium"},
        {"lines": [51],    "confidence": "low"}
      ],
      "dropped": [
        {"lines": [51], "at_step": 3, "why": "the conversion feeds a second use, so nothing is redundant"}
      ],
      "found": [47]
    }
  ]
}
```

### Field rules

**`why`** must be specific to this code. Name the variable, the line, the
structure. "Inefficient string handling" is not a reason; "`self.buf` is grown
with `+=` across `rows`" is.

**`hotness`** is where you record what you learned in step 2. Most of these
patterns only waste anything on a hot path, and this is the field a reader
checks when a finding looks marginal.

**`found_by`** records how you came to suspect it. With no tool in the loop it
is `reading` throughout, and it is kept so a reader can tell an analysis you
did from a list you were handed.

**`subsumed`** lists candidates that disappeared when this repair landed —
checked in step 4, after applying it and re-deciding what was left. Each needs
a reason. Do not put anything here that you did not actually re-check.

**`spans_units`** names every unit the repair edits. One entry for most
findings; more when the waste lived in the arrangement rather than in a line.

**`verification.status`** is copied verbatim from `verify.py`. Never write
`confirmed` yourself.

**`verification.equivalence_relaxed`** is copied verbatim too. If it is
non-empty, the report must say so next to the number: the saving was measured
under a weakened definition of "same behaviour", and a reader who does not know
that is being misled.

**`units_examined`** covers every unit you looked at, cleared or not, with the
hypotheses you formed before naming anything. Without it, a run that examined
three functions and one that examined three hundred are indistinguishable, and
there is no way to tell whether you read the code or the labels.

---

## REPORT.md

Rendered from the JSON, grouped by file. For each finding: the lines,
one paragraph of `why`, the repair as a diff, and the measured
result. Then a short section for `mixed`, `regressed`, `negligible` and
`inconclusive`, and one line for
anything `advisory` or `blocked`.

Open with a summary the reader can act on:

```markdown
# Energy efficiency — acme-parser @ a1b2c3d

15 units examined, 4 repairs confirmed, 1 mixed, 1 regressed, 2 negligible,
1 inconclusive.
Host noise floor 1.6%; every confirmed saving clears it.

| Unit | What was repaired | Energy saved |
|---|---|---|
| `src/render.py::Report.render` | string built with `+=` in a loop | 25.9% ± 3.0% |
```

State the noise floor. A saving of 2% means nothing on a host that cannot
resolve better than 1.6%, and the reader has no way to know that unless you
say it.

Close with the subsumption record: which repairs made which other candidates go
away. It is short, and it is the part that says which repairs were doing the
real work.
