# Energy Smell Skill — Plan (v3)

> **v3 replaces v2.** v2 built a detector: our own pipeline that called an LLM
> through an API, adjudicated candidates and returned claims. That is gone. We
> do not detect. We ship the *knowledge and the referee* that let someone
> else's agent detect well, and we measure how well it did.

---

## 1. What we deliver

One directory, `skill/`, copyable into any repository:

```
skill/
  SKILL.md                       always loaded — protocol + 12 category index
  reference/
    categories/C1.md … C12.md    opened when a category is in play
    root-causes/C1.S1.md … …     opened when a root cause is a candidate  (65)
    verifying.md                 how to prove a saving is real
    output-format.md             the exact shape of findings.json
  scripts/
    scan.py                      static evidence  (optional, ablatable)
    verify.py                    equivalence + paired energy measurement
    lib/                         the code both scripts use
```

The agent — Claude Code, Codex, whatever comes next — reads `SKILL.md`, follows
the protocol, opens reference files on demand, runs the two scripts, and writes
`findings.json` + `REPORT.md`.

**Runtime dependency: Python 3.9+ standard library.** `ruff` is optional and
`scan.py` degrades without it. Nothing calls a network. No API keys.

### What "good" means here

Our deliverable is good when a *cold* agent — no memory of this project — points
at an unfamiliar GitHub repository and produces findings that survive
measurement. Every design choice below serves that sentence.

---

## 2. The organising principle (kept from v2, unchanged)

> **If a unit has N energy smells, there are N distinct refactorings, each
> removing exactly one of them.**

If removing smell A also makes smell B disappear, B was never a separate smell.
This is the whole reason the deliverable can be evaluated rather than admired.
It gives us, for free:

- a **counting rule** — findings are refactorings, not labels;
- a **granularity rule** — one patch, one root cause, minimal edit;
- a **falsification rule** — a claimed smell whose repair saves no energy is not
  a smell, and gets dropped.

The second-order effect matters most: an agent that must produce a working
patch and watch it be measured cannot pattern-match its way to a plausible
answer. That is the mechanism by which a skill beats zero-shot prompting.

---

## 3. Repository layout

| Path | Role | Shipped? |
|---|---|---|
| `taxonomy/*.xlsx` | the published taxonomy, 12 categories / 65 root causes | no — source |
| `catalog/C*.yaml` | authored per-root-cause knowledge (see §5) | no — source |
| `build/` | renders `catalog/` + `taxonomy/` into `skill/reference/` | no — tooling |
| `skill/` | **the deliverable** | yes |
| `eval/` | harness that runs cold agents across repos and arms | no |
| `tests/` | fixtures and self-tests for the scripts | no |
| `data/` | the LeetCode-derived labelled set, retained for spot checks only | no |

Cards are **generated, never hand-edited**: `catalog/*.yaml` is the single
source of truth, so a discriminator gets fixed in exactly one place. Run
`python -m build` to regenerate `skill/reference/`.

`build/` also compiles `catalog/*.yaml` into `skill/scripts/lib/signals.json`,
the evidence-kind → root-cause table, so `scan.py` needs no YAML parser at
runtime.

---

## 4. Progressive disclosure

Three levels. The reason is **not** token cost.

Shown all 65 root causes at once, a model gravitates to whichever labels feel
central. In the published LeetCode labelling, C7.S1 took 27% of all assignments
and C11 took 0.07%. Narrowing the candidate set *before* the choice is made
keeps the decision driven by the code in front of it.

| Level | File | Answers |
|---|---|---|
| 0 | `SKILL.md` | What am I doing? Which of the 12 categories are in play? |
| 1 | `reference/categories/C7.md` | Is it anywhere in this category? Which root causes live here? |
| 2 | `reference/root-causes/C7.S1.md` | Is it *this* one? What exactly would fix it? |

Level 2 is where the work is. Each card carries:

- the taxonomy's own description and example;
- **`Applies only when`** — preconditions;
- **`NOT a smell when`** — context exceptions (179 of them across the catalog).
  This field does the most work in practice and is the answer to "one rule does
  not fit every case";
- **canonical repair** with before/after and a patch-shape bound;
- **discriminators** against neighbouring root causes;
- **measurability** — whether measurement can possibly resolve this repair.

Depth is a hypothesis, not a conviction. If evaluation shows the category level
adds nothing, collapse to two levels; if 65 cards is too coarse a fan-out at
level 1, add a level. This is a thing to test, not to argue about.

---

## 5. The protocol in `SKILL.md`

Six steps. Each has one input and one output, stated in the skill itself so the
agent cannot drift.

| # | Step | In | Out |
|---|---|---|---|
| 1 | **Select** | repo path | ranked list of units worth examining |
| 2 | **Understand** | one unit's source | what it computes; where work concentrates |
| 3 | **Narrow** | evidence + level-0 index | ≤3 categories, then ≤5 candidate root causes |
| 4 | **Decide** | level-2 cards | per candidate: accept / reject **with the clause that decided it** |
| 5 | **Verify** | accepted candidates | a case file per candidate → `confirmed` / `refuted` / `advisory` |
| 6 | **Report** | verdicts | `findings.json` + `REPORT.md` |

Step 1 is where `scan.py` enters, and it is the ablation point:

```
scripts/scan.py PATH --mode full   # AST rules + ruff        (default)
scripts/scan.py PATH --mode ast    # AST rules only
scripts/scan.py PATH --mode ruff   # ruff only
scripts/scan.py PATH --mode off    # emits: static analysis disabled
```

In `--mode off` the script prints an explicit instruction to select and read
units manually using the same criteria. The knowledge-only arm therefore runs a
*complete* protocol with a missing accelerator, not a broken one.

Steps 2–4 never see the whole taxonomy or the whole repository. That bound is
what keeps this runnable on a small model, and it is the property to protect if
the prompts are ever rewritten.

---

## 6. Verification — the referee

**Nothing is reported as a smell until a repair for it has been measured.**
Without this the agent can assert anything, and the taxonomy becomes decoration.

### The interface the agent must produce

One self-contained file per candidate:

```python
# case_C10S4.py
def before(rows): ...        # the pattern, extracted
def after(rows):  ...        # the canonical repair, and nothing else

def cases():
    """(label, thunk) — the thunk returns a fresh args tuple each call."""
    return [
        ("empty",  lambda: ([],)),
        ("single", lambda: ([mk(0)],)),
        ("large",  lambda: ([mk(i) for i in range(200_000)],)),
    ]
```

Thunks, not values, because `before` may mutate its arguments; each repetition
gets a fresh input, built outside the measured window.

### What `verify.py` does with it

1. **Equivalence.** For every case: same return value, same post-call argument
   state, same stdout, same exception type. A mismatch is fatal — the repair is
   wrong, not the smell.
2. **Scale the workload.** Time one call; choose a repeat count so each measured
   window is ≥ 2 s. This is the answer to "short cases are all noise": a 40 µs
   edge case is run 50 000 times. Capped, so a pathological case cannot hang.
3. **Measure paired and interleaved.** Both variants alternate inside one
   process, 7 paired repetitions, order flipped each rep. (Separate processes
   per variant were tried and gave ~3.5× wider intervals — the dominant noise is
   idle-power drift, so paired samples must sit close together in time.)
4. **Compare against the null canary.** `before` vs a copy of itself must come
   back insignificant; its interval is this host's resolution limit.

### Verdicts

| Verdict | Meaning |
|---|---|
| `confirmed` | equivalent on all cases; the large case saves significantly, clearing the noise floor; no case regresses significantly |
| `refuted` | equivalent, measured, no significant saving → **not a smell**, dropped from findings |
| `advisory` | measurability is `constant_small` — the repair is one bytecode instruction and provably cannot clear any realistic floor. Reported honestly as unmeasured, never as verified |
| `blocked` | no runnable case file could be built (needs a database, network, GPU) |

`refuted` is kept in the output on purpose. An agent that proposes ten smells
and has three refuted is telling us something we need to know.

On measurement noise: reported figures are *system* energy over the workload
window, on a host that idles at ~48 W while one busy Python thread adds ~10 W.
So savings read conservatively. That is fine — the noise applies to both arms of
a paired comparison equally, and the null canary bounds it. Time is recorded
separately so energy/time divergence stays visible.

---

## 7. Output contract

```jsonc
{
  "schema_version": 1,
  "target":  {"path": "…", "commit": "…", "files_scanned": 120},
  "config":  {"scan_mode": "full", "agent": "claude-code", "model": "…"},
  "findings": [{
    "unit": "src/render.py::Report.render", "line": 42,
    "root_cause": "C10.S4", "name": "Inefficient String Concatenation",
    "why": "`out` grown by += across `rows`; never read inside the loop",
    "evidence": ["string_concat_in_loop"],          // [] when --mode off
    "rejected_neighbours": [{"id": "C10.S1", "why": "no repeated conversion"}],
    "repair": {"summary": "collect parts in a list, join once",
               "patch_shape": "statement_local"},
    "verification": {
      "status": "confirmed", "case_file": "cases/case_C10S4.py",
      "equivalent_on": 3, "repeats": 40,
      "energy_saved_pct": 25.9, "energy_ci_pct": 3.0,
      "time_saved_pct": 26.1,  "time_ci_pct": 2.4,
      "noise_floor_pct": 1.6,
      "per_case": [{"label": "large", "energy_saved_pct": 25.9}, …]
    }
  }],
  "refuted": [ … same shape, status "refuted" … ],
  "units_examined": [{"unit": "…", "no_smell_because": "…"}]
}
```

`units_examined` matters for evaluation: without it a run that examined three
functions and a run that examined three hundred look identical.

`REPORT.md` is rendered from this file, never written independently.

---

## 8. Portability to other agents

The deliverable is markdown plus two stdlib Python scripts, so the *content*
is portable by construction. What differs is how each host loads it:

| Host | Mechanism | Status |
|---|---|---|
| Claude Code | native skill — frontmatter + on-demand file reads | works today |
| Codex / AGENTS.md | `AGENTS.md` says "read `skill/SKILL.md` and follow it" | one-line shim |
| Cursor / Windsurf | rules file pointing at `SKILL.md` | one-line shim |
| Antigravity, others | unknown loading mechanism | to test |

Progressive disclosure is written as *explicit instructions* ("open
`reference/categories/C7.md` before deciding"), not as a host feature we depend
on. Any agent that can read a file and run a command can follow it. Where a host
lacks on-demand loading entirely, the fallback is a bundled single-file build —
worse, but functional. We test on Claude Code first and generalise from what
breaks.

---

## 9. Evaluation

**Precision needs no labels.** The verifier is the oracle:
`precision = confirmed / (confirmed + refuted)`. This is the headline number
and it is self-measuring on any repository.

**Recall needs seeded smells.** A fixture corpus with known planted root causes,
one per file, gives `found / planted`.

**Corpus.** 5–10 GitHub Python repositories, ≥200 stars, with tests, spanning
domains. Each run uses a cold agent session with no knowledge of this project.

**Arms.** `--mode off` / `ruff` / `ast` / `full`, same repos, same agent. The
question the professor asked — do the static analyzers help or do they just
anchor the agent — is answered by comparing precision and recall across those
four, plus a fifth diagnostic: how often the agent reports a root cause the
scanner never suggested.

**Also worth recording:** wall-clock and token cost per repo, distribution of
root causes reported (does one label dominate, as C7.S1 did?), and agreement
between two different agents on the same repo.

---

## 10. Status

**Carried over from v2 and still valid**

- 65 catalog entries, 40 discriminators, 179 `not_a_smell_when` clauses
- 27 AST analyzers + a Ruff adapter, validated on 179 files of pandas source
- Findings ranked by the measured saving of their repair, averaged over our own
  benchmark shapes — the one axis, replacing the hand-assigned strength grades
- Paired interleaved measurement, null canary, RAPL and CodeGreen meters
- Phase-0 gate: null canary −1.1% ±4.9% (insignificant), real C10.S4 repair
  +25.9% ±3.0% (significant)

**Deleted in v3** — the OpenRouter client, the three-step adjudication protocol,
the LLM response cache, the runtime card renderer, `detect`/`route` commands.

**To build**

1. `build/` — render 78 markdown cards, compile `signals.json`
2. `skill/SKILL.md` — the protocol above
3. `skill/scripts/scan.py` — evidence + candidates as JSON, four modes
4. `skill/scripts/verify.py` — the case-file contract of §6
5. `skill/reference/verifying.md`, `output-format.md`
6. Cold-agent test on one real repository, then `eval/`

**Deliberately deferred**

- Richer static metrics — fan-in/fan-out, call-graph hotness, bytecode counts.
  Promising, unproven; they belong in the ablation ladder once the base works.
- Cross-unit root causes (C2.S3, C9.S3, C11.*) need class- and module-level
  analyzers; today's units are functions and methods.
- Independence beyond the syntactic check: measuring A, B and A+B separately to
  confirm B contributes something A did not. Correct, and three times the cost.

**Open, to settle by testing rather than argument** — card depth (2 vs 3
levels); whether the catalog needs fields it does not yet have; whether
`--mode off` genuinely produces a clean knowledge-only arm.
