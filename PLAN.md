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
    output-format.md             the exact shape of findings.jsonl and submissions.jsonl
  scripts/
    scan.py                      static evidence  (optional, ablatable)
    verify.py                    equivalence + paired energy measurement
    lib/                         the code both scripts use
```

The agent — Claude Code, Codex, whatever comes next — reads `SKILL.md`, follows
the protocol, opens reference files on demand, runs the two scripts, and writes
`findings.jsonl` (its work, step by step) and `submissions.jsonl` (its repairs,
each measured). It never edits the repository; `tools/review.py`, on our side,
re-measures, decides what to apply and writes `REPORT.md`.

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

- the taxonomy's own definition and example, verbatim;
- **Common patterns** — three or four lines drawn from our samples and the
  rules' positive fixtures;
- **Repair** — every measured sample of this root cause, before and after,
  each ending with what it measured and what to do about it (apply the after,
  decide which form fits, report without measuring, or measure);
- **Looks like it, but is not** — up to five near-misses where the repair
  would change behaviour, most of them the behaviour-checked specimens in
  `validation/lookalikes/`;
- **Similar root causes**, in each neighbour's own one-line description.

`build/CARD_SPEC.md` says where each part comes from; everything but the
written lines is read from the case files and the results at build time.

Depth is a hypothesis, not a conviction. If evaluation shows the category level
adds nothing, collapse to two levels; if 65 cards is too coarse a fan-out at
level 1, add a level. This is a thing to test, not to argue about.

---

## 5. The protocol in `SKILL.md`

Five steps, matching the shipped `SKILL.md` exactly. Each has one input and one
output, stated in the skill itself so the agent cannot drift, and each output is
appended to `findings.jsonl` as it is produced:

| # | Step | In | Out |
|---|---|---|---|
| 1 | **Select** | repo path | ranked list of units worth examining |
| 2 | **Read and suspect** | one unit's source | what it computes, where work concentrates, `suspicions[]` — written before any card is opened |
| 3 | **Decide** | `suspicions[]` | each one accepted or rejected, **with the clause that decided it** |
| 4 | **Repair and measure** | one unit's accepted suspicions | one submission per suspicion, each measured; an outcome for every one |
| 5 | **Finish** | both files | both complete, and a short summary |

The agent does not edit the repository. Step 4 produces submissions — the unit,
the replacement source for it and for any callee changed, and a factory that
builds the inputs — and `before` is read from the repository rather than
supplied. That is what stops a fabricated baseline, and it is why the artifact
is re-run on our side before anything is believed or applied.

Every repair is written against the original code, never on top of another, so
the order the agent takes them in does not matter and each one's saving is its
own. A suspicion whose repair is the identical edit to one already submitted is
recorded as `same_repair_as`; different edits to the same code are each
submitted and list each other as `related`. Since each is written against the
original, at most one per function can be applied, and `tools/review.py` picks
the confirmed one with the highest mean saving across the five shared cases.

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

One line of `submissions.jsonl` per repair. The agent names the unit and gives
the replacement source; it never writes `before`.

```jsonc
{"id": "C10S4-render-concat", "root_cause": "C10.S4",
 "unit": "src/render.py::Report.render",
 "changed": {"src/render.py::Report.render": "def render(self):\n    ..."},
 "cases_source": "def checks():\n    ...   # edge inputs: behaviour only\n"
                 "def cases():\n    ...    # exactly five, each measured"}
```

`before` is read from the repository, so it cannot be a simplified sketch or a
baseline shaped to flatter the result. `checks()` holds the edge inputs, which
are compared but never measured; `cases()` holds five inputs that make the unit
behave differently, including the one the repair is most likely to lose on.
Thunks, not values, because the unit may mutate its arguments: every window
gets fresh input, built outside the measured region.

### What `verify.py` does with it

1. **Stage and load.** A pristine copy and a patched copy of the repository are
   imported side by side in one worker process, each under its real package
   names; one copy's modules are set aside while the other's run. Nothing is
   renamed, no import is rewritten.
2. **Equivalence.** For every input: same return value, same effect on the
   arguments, same stdout, same exception type. A mismatch is fatal — the
   repair is wrong, not the smell.
3. **Scale the workload.** Time one call of each version and choose a repeat
   count so the faster fills a 1 s window. Both run the same count.
4. **Measure paired and interleaved.** The two versions alternate on one thread
   — 5 paired repetitions, order flipped each time. Separate
   processes per version were tried twice: once early on (about 3.5× wider
   intervals) and again for this design, where identical code in two processes
   read "confirmed" in two of four runs. The pair has to share a process.
5. **Compare against the null.** Two copies of identical code must come back
   insignificant, measured once per session. Its interval is the bar every real
   effect has to clear. The agent's measurement and ours use exactly these
   settings; ours is simply taken again, on an idle machine. (Validation case
   files keep their original 3 s / 9-pair settings with a canary per case.)

### Verdicts

| Verdict | Meaning |
|---|---|
| `confirmed` | every case that moved, moved the right way, clearing the noise floor |
| `mixed` | saves on some cases, costs on others, both clearing the floor — a trade-off, not a fix |
| `regressed` | every case that moved measurably, got worse |
| `negligible` | measured on a clean floor, and nothing moved more than the noise |
| `inconclusive` | the floor was too high to resolve an effect this size — a fact about the host, not about the code |
| `not_equivalent` | the replacement behaves differently; the repair is broken |
| `rejected` | the submission is malformed or out of scope |
| `blocked` | no runnable set of cases could be built (needs a database, network, GPU) |

Every verdict is kept in the output on purpose. An agent that proposes ten
repairs and has three come back negligible is telling us something we need to
know. `negligible` and `inconclusive` are deliberately separate: the first is
evidence about the code, the second is evidence about the machine.

On measurement noise: reported figures are *system* energy over the workload
window, on a host that idles at ~48 W while one busy Python thread adds ~10 W.
So savings read conservatively. That is fine — the noise applies to both arms of
a paired comparison equally, and the null canary bounds it. Time is recorded
separately so energy/time divergence stays visible.

---

## 7. Output contract

Two files, both JSON Lines. The authoritative shapes are in
`build/templates/shared/reference/output-format.md` and `verifying.md`; what
follows is an illustration, and the templates win if they drift.

`findings.jsonl` — one record per step per unit, appended as the agent works:

```jsonc
{"step": 1, "units_considered": 128, "will_examine": ["src/render.py::Report.render", "…"]}
{"step": 2, "unit": "src/render.py::Report.render", "what_it_does": "…", "cost_driver": "…",
 "own_hypotheses": ["…"], "suspicions": [{"label": "a", "root_cause": "C10.S4", "lines": [47], "why": "…"}]}
{"step": 3, "unit": "src/render.py::Report.render", "decisions": [{"label": "a", "verdict": "accepted", "…": "…"}]}
{"step": 4, "unit": "src/render.py::Report.render", "outcomes": [{"label": "a", "submission": "C10S4-render-concat"}]}
```

`submissions.jsonl` — one repair per line, with what `verify.py` measured:

```jsonc
{"id": "C10S4-render-concat", "root_cause": "C10.S4",
 "unit": "src/render.py::Report.render",
 "changed": {"src/render.py::Report.render": "def render(self): …"},
 "related": [], "cases_source": "def checks(): …\ndef cases(): …",
 "agent_measurement": {"status": "confirmed", "profile": "fast", "noise_floor_pct": 1.6,
   "per_case": [{"label": "many-rows", "before_energy_j": 48.2, "after_energy_j": 35.7,
                 "before_time_s": 1.01, "after_time_s": 0.75, "energy_ci_pct": 3.0,
                 "significant": true}, …],
   "submission_hash": "…"}}
```

No percentage is stored anywhere. A saving is a view of the joules beside it,
and keeping a derived figure next to its inputs lets the two disagree.

The step-2 records matter for evaluation: without one per unit, a run that
examined three functions and a run that examined three hundred look identical.

`REPORT.md` is ours: `tools/review.py` writes it from both files and its own
re-measurement, alongside `results.jsonl` (verdict, applied or not, and why).

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

**Precision needs no labels.** The verifier is the oracle, and it is
self-measuring on any repository. The exact denominator is still **open**, and
it matters because the verdict set is no longer binary: `confirmed / (confirmed
+ negligible + regressed)` treats a trade-off as neither right nor wrong by
excluding `mixed`, while including `mixed` as a failure penalises a repair that
genuinely pays on the inputs the code actually sees. `inconclusive` must stay
out of the denominator either way — it says the host could not tell, which is
not a fact about the agent. Decide this before the first eval run, and state it
in the paper.

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

- 65 catalog entries: 228 measured repairs shown from the case files, 120 near-misses (33 of them behaviour-checked specimens from `validation/lookalikes/`)
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
