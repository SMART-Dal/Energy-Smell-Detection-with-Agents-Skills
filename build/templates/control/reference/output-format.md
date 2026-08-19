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

      "what": "`self.buf` is grown with += once per row",
      "why": "each += allocates a new string and copies everything already built, so the accumulation is O(n^2) in the total output length. Through an attribute, CPython's in-place resize cannot apply.",
      "hotness": "called once per HTTP response; `rows` is typically 5k-50k long",

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
        "cases_checked": 3,
        "repeats": 40,
        "energy_saved_pct": 25.9, "energy_ci_pct": 3.0,
        "time_saved_pct": 26.1,  "time_ci_pct": 2.4,
        "energy_only": false,
        "noise_floor_pct": 1.6,
        "equivalence_relaxed": [],
        "per_case": [
          {"label": "empty",  "energy_saved_pct":  0.4, "significant": false},
          {"label": "small",  "energy_saved_pct":  9.1, "significant": true},
          {"label": "large",  "energy_saved_pct": 25.9, "significant": true}
        ]
      }
    }
  ],

  "refuted": [
    // Same object shape. Candidates that were accepted at step 3, repaired,
    // measured, and did not save anything on a clean noise floor. Keep them:
    // a repair that turned out not to help is a result, not a failure to hide.
  ],

  "inconclusive": [
    // Same object shape. Measured, but the host could not resolve an effect
    // this size. A different claim from `refuted` — do not merge the two.
  ],

  "units_examined": [
    {
      "unit": "src/parse.py::tokenize",
      "what_it_does": "splits a header into fields",
      "observations": [],
      "cleared_because": "no work here is proportional to input size"
    },
    {
      "unit": "src/render.py::Report.render",
      "what_it_does": "renders one HTML table from a list of row dicts",
      "observations": [
        {"what": "the output string is rebuilt on every row", "confidence": "high"},
        {"what": "`sorted(self.columns)` is recomputed per row", "confidence": "medium"}
      ],
      "dropped": [
        {"what": "`sorted(self.columns)` recomputed per row", "at_step": 3,
         "why": "11 columns; the sort is ~1 microsecond against 40 for the row itself"}
      ],
      "found": ["the output string is rebuilt on every row"]
    }
  ]
}
```

### Field rules

**`what`** names the code and the work. "Inefficient string handling" is not an
observation; "`self.buf` is grown with `+=` across `rows`" is.

**`why`** says mechanically what work stops happening and why that costs less.
A rule of thumb is not a reason — "joining is faster than concatenating" says
nothing about this code. What allocates, what copies, what is called n times
instead of once: that is a reason.

**`hotness`** is where you record what you learned in step 2. Most waste is
only worth repairing on a hot path, and this is the field a reader checks when
a finding looks marginal.

**`subsumed`** lists observations that disappeared when this repair landed —
checked in step 4, after applying it and re-deciding what was left. Each
needs a reason. Do not put anything
here that you did not actually re-check.

**`spans_units`** names every unit the repair edits. One entry for most
findings; more when the waste lived in the arrangement rather than in a line.

**`verification.status`** is copied verbatim from `verify.py`. Never write
`confirmed` yourself.

**`verification.equivalence_relaxed`** is copied verbatim too. If it is
non-empty, the report must say so next to the number: the saving was measured
under a weakened definition of "same behaviour", and a reader who does not know
that is being misled.

**`units_examined`** covers every unit you looked at, cleared or not. Without
it, a run that examined three functions and one that examined three hundred are
indistinguishable.

---

## REPORT.md

Rendered from the JSON, grouped by file. For each finding: what the waste is,
one paragraph of `why`, the repair as a diff, and the measured result. Then a
short section for `refuted` and `inconclusive`, and one line for anything
`advisory` or `blocked`.

Open with a summary the reader can act on:

```markdown
# Energy efficiency — acme-parser @ a1b2c3d

15 units examined, 4 repairs confirmed, 2 refuted, 1 inconclusive, 1 advisory.
Host noise floor 1.6%; every confirmed saving clears it.

| Unit | Repair | Energy saved |
|---|---|---|
| `src/render.py::Report.render` | join once instead of += per row | 25.9% ± 3.0% |
```

State the noise floor. A saving of 2% means nothing on a host that cannot
resolve better than 1.6%, and the reader has no way to know that unless you
say it.

Close with the subsumption record: which repairs made which other observations
go away.
