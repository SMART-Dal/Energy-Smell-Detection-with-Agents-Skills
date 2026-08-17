# What changed in this pass

Git was initialised at the end of this pass, so it cannot show you a diff
against the previous version. This file is that diff, written by hand. From the
first commit onward `git log` replaces it.

Grouped by the concern that prompted each change.

---

## 1. The ablation is four deliverables, not a runtime flag

**Was:** one `skill/` directory and `scan.py --mode {full,ast,ruff,off}`.

**Now:** `python -m build` writes four directories under `dist/`. Each ships
only the code its condition allows, and the arm is read from a generated
`lib/arm.json` that has no command-line override.

| Arm | Ships |
|---|---|
| `dist/energy-smells` | everything |
| `dist/energy-smells-ast` | no `linters.py` |
| `dist/energy-smells-ruff` | no `rules/` package |
| `dist/energy-smells-knowledge` | no `scan.py`, no `analysis/`, no `signals.*` |

**Why beyond your reason:** `--mode off` still left `scripts/lib/analysis/rules/`
on disk. Those files are a plain-language list of every pattern we treat as
suspicious. An agent that reads them has been handed the static analysis in its
most direct form, whatever the flag said. Withholding has to be physical.

**New/changed files:** `build/arms.py` (new), `build/__main__.py` (rewritten
around `_render_arm`), `src/scan.py` (`--mode` removed, `load_arm()` added),
`src/lib/analysis/engine.py` (analyzer imports made lazy so a withheld family is
not an import error).

**Moved:** `skill/scripts/` → `src/`. `skill/` is now generated output under
`dist/` and should be deleted once you have looked at it.

## 2. The agent is no longer confined to what the scanner found

- `SKILL.md` step 1 now states that 13 root causes have no rule at all, that
  silence about a category is silence rather than absence, and instructs the
  agent to **pick at least two categories the scan said nothing about** and
  check them by hand after working the ranked list.
- Step 3 adds: pick categories from what the code does, not only from what you
  were handed; no category is ruled out by not appearing in the evidence.
- New `reference/README.md` in every arm: the full 12-category index plus a
  **generated** table of exactly which root causes no rule can reach. Generated
  rather than typed, so the figure cannot go stale and understate the blind spot
  it exists to warn about.
- `scan.py`'s footer says the same thing in the place the agent is actually
  looking.

## 3. Scan output is grouped under root causes

**Was:** two disconnected lists per unit — evidence, then candidate IDs.

**Now:** one block per candidate root cause, each carrying the card to read, the
repair, whether a claim of it can be measured, and the evidence that pointed at
it with strength, line, message and source.

```
1. models.py:412  Request.prepare_body
   loop depth 1 | but runs at depth 3 via send:88 | called from 2 place(s)

   C7.S1  Suboptimal Algorithm Choice
     read     reference/root-causes/C7.S1.md
     repair   replace the algorithm with the better-known one
     verify   scales_with_input -- measurable, so a claim here must be verified
     because  (1 definite, 1 likely)
       definite   line 418   `x in candidates` scans a list inside a loop over
                             `items`, so the pair costs len(items)*len(candidates)
                             [ast/membership_test_on_sequence]
```

Every step now ends with the next action stated explicitly, and the scan closes
with a `NEXT:` line.

## 4. Ranking counts callers, not just a unit's own loops

Your example — a helper called from inside someone else's nested loop is ranked
as though it ran once — was correct.

**New:** `src/lib/analysis/callgraph.py`. Resolves calls within a file, then
propagates loop depth to callees and counts fan-in and fan-out.

```
1. cluster.py:1  distance
   loop depth 1 | but runs at depth 3 via cluster:11 | called from 1 place(s)
2. cluster.py:7  cluster
   loop depth 2
```

`distance` now outranks `cluster`. Ranking key changed from
`(max_loop_depth, evidence_weight, n_root_causes)` to
`(reached_at_depth, min(fan_in, 5), evidence_weight, n_root_causes)` — so a hot
utility in no loop at all can still rank, which was your second point.

Resolution stops at the file boundary on purpose: following calls across
modules means resolving imports, aliases and re-exports, and inventing an edge
that does not exist is worse than admitting the graph ends. The agent is told to
follow them by reading instead.

## 5. Cross-function and whole-path reading is now instructed

`SKILL.md` step 2 was two sentences. It now requires:

- **down** into every callee that is not obviously trivial — a three-line loop
  body calling `normalise(row)` may be compiling a regex per iteration;
- **up** into callers, because cost is paid per execution;
- and a new paragraph: **judge the whole path, not one statement.** If the
  inefficiency lives in the arrangement across several methods rather than in
  any one line, that is still a finding — attribute it to the root cause that
  describes the arrangement (C2.S3, C7.S4, C7.S5, C9.S3), scope the repair to
  the smallest set of units that fixes it, and say which units it spans.

## 6. Cards gained a counter-example section

**New schema field** `counter_examples: [{code, why}]`, rendered as
**"Looks the same, is not"**, placed before the repair so it is read first.

This is the answer to "are more examples needed". A second *positive* example
teaches nothing. What decides a hard case is the near-miss — and C10.S4 proves
it: three examples of `s += x` in a loop would all have been wrong, because what
separates smell from non-smell is `out +=` against `self.buf +=`.

Populated so far from measured evidence: C10.S4, C10.S1, C10.S2, C6.S3, C2.S2,
C3.S5, C8.S1, C6.S2. The rest are pending the full measurement run.

## 7. Static coverage: 38 → 52 of 65 root causes

**New:** `src/lib/analysis/rules/waste.py`, 16 analyzers. AST rules went 27 → 43.

Several were written from your samples rather than from a hunch:

| Analyzer | Root cause | From |
|---|---|---|
| `float_literal_on_int_data` | C5.S3 | ImproperDataStructure/MultiplyByFactor |
| `constant_sequence_literal` | C5.S3, C6.S1 | ImproperDataStructure/AssignType |
| `sort_then_slice` | C7.S4 | BuiltInBehavior/SumTopK |
| `trivial_delegation` | C2.S3 | ObjectOriented/InternalGetterSetter |

Others: `global_lookup_in_loop` (C10.S5), `copy_in_loop` (C6.S2),
`filter_after_transform` (C7.S4), `expensive_comparison` (C4.S5),
`redundant_bool_branch` (C1.S3), `dead_initialization` (C1.S6),
`single_use_temporary` (C1.S7), `discarded_pure_result` (C1.S5),
`runtime_management_in_loop` (C1.S8), `blocking_call_in_async` (C11.S4),
`unjoined_thread` (C11.S3), `column_major_traversal` (C12.S1).

**Tuned by running on real code, as you suggested.** The first
`global_lookup_in_loop` fired 45 times on `psf/requests` — more than every other
analyzer combined. Added a three-reads-per-iteration threshold and a two-per-loop
cap. No rule now exceeds 20% of total evidence.

The 13 root causes still uncovered are listed in every arm's
`reference/README.md`, generated from the catalog.

## 8. Discriminators: 46, no gaps among confusable pairs

Computed every pair of root causes reachable from a shared signal (13 pairs),
found 5 with no discriminator, wrote them: C10.S2/C4.S8, C3.S3/C4.S6,
C3.S6/C6.S3, C6.S3/C9.S2, C8.S4/C9.S3.

This covers *signal*-confusability only. Semantic overlap between root causes
that never share a signal is not measurable this way and needs the cold run.

## 9. Verdicts distinguish "saves nothing" from "could not tell"

**New verdict: `inconclusive`.** Previously a high noise floor produced
`refuted`, which asserts the repair does nothing — the opposite of what a noisy
host licenses you to say.

`USABLE_FLOOR_PCT = 3.0`. Above that canary reading, the verdict is
`inconclusive` with an instruction to re-run on an idle machine.

This was not hypothetical. See section 11.

## 10. A pre-flight check for the rig

**New:** `validation/preflight.py` and `validation/preflight/*.py`. Three
questions, stopping at the first failure:

1. identical code against itself reads ~0% (host is quiet);
2. a set lookup beats a 5000-element linear scan by >40% (the rig can see);
3. the same pair *swapped* reads negative (the rig is not just saying yes).

Question 1 alone is insufficient — a meter returning a constant would pass it.

## 11. Two suites that measure the taxonomy instead of assuming it

**New directory `validation/`.**

- `generate_sample_cases.py` converts `data/manual_sampling` mechanically: 84 of
  your 92 pairs became verifier case files. The 8 that did not are listed with
  the reason.
- `validation/taxonomy/` — **69 hand-written case files covering all 65 root
  causes**, each with 2–3 input cases spanning large / small / edge, and second
  files for the root causes where your samples contradict the cards.
  All 69 pass the equivalence check.
- `run.py` runs a suite in subprocesses, resumable, results to
  `validation/results/<suite>.jsonl`.

### Bugs this found in my own code

1. `equivalence.py` deep-copied arguments and compared with `==`. For a class
   with no `__eq__` that is identity, so **every argument containing a custom
   object looked mutated**. The `repr` fallback was worse: the default repr
   embeds the memory address, which the copy also changes.
2. Identity semantics hide one level down: `[AB(1)] == [AB(1)]` is False for the
   same reason. A `False` from `==` is no longer believed without a structural
   check.
3. The sample converter built inputs in a third namespace, so `type(a) == AB` was
   False for every element and the function under test did no work.

## 12. Files removed

`skill/` (superseded by `dist/`), `build/_*_old.py` scaffolding. The `repair`
field in `signals.json` — which I told you last session was dead — is now used:
it is what the scan prints under `repair` for each candidate.
