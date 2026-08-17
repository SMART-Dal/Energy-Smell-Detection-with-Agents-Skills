# Evaluating the skill

The skill cannot be evaluated by whoever wrote it. A session that has been
discussing the taxonomy for hours will find smells the skill did not teach it,
and will forgive gaps the skill left open. Every run below therefore starts
**cold**: a fresh agent session, in a directory that is not this repository,
with no context except the skill itself.

## One cold run

```bash
# 1. a target that is not this repo
cd /tmp && git clone --depth 1 https://github.com/psf/requests.git
cd requests

# 2. install the skill
mkdir -p .claude/skills
cp -r /home/javad/energy_smell_detection/skill .claude/skills/energy-smells

# 3. start a new session here and give it exactly this:
```

> Find the energy smells in `src/requests` using the energy-smells skill.
> Write `findings.json` and `REPORT.md`.

Say nothing else. Anything you add is a hint the skill should have contained.

## What to record

For each run: the arm, the repo, and from `findings.json` —

| Metric | Where from |
|---|---|
| **precision** | `confirmed / (confirmed + refuted)` |
| units examined | `len(units_examined)` |
| findings per unit | `len(findings) / len(units_examined)` |
| label concentration | most common `root_cause` as a share of all findings |
| unprompted findings | findings whose `evidence` is `[]` in a non-`off` arm |
| cost | wall clock, tokens |

Precision needs no ground truth: the verifier is the oracle. That is the point
of making measurement mandatory, and it is what lets any repository be a test
set.

Recall does need ground truth, so it needs the seeded corpus below.

## The arms

Same repo, same agent, one variable. Set the arm by telling the session which
mode to pass:

| Arm | Command the agent runs | Question it answers |
|---|---|---|
| `off` | `scan.py … --mode off` | how well does the agent do on knowledge alone? |
| `ruff` | `scan.py … --mode ruff` | what does an off-the-shelf linter contribute? |
| `ast` | `scan.py … --mode ast` | what do our 27 analyzers contribute? |
| `full` | `scan.py … --mode full` | do the two evidence sources compose? |

On `psf/requests`, the static layer alone gives: ruff 13 evidence items over 8
units, AST 64 over 34, full 77 over 39. Whether that translates into better
*findings* is exactly what the `off` arm is there to test — more evidence is
not the same as more truth, and an anchored agent is a real risk.

## The corpus

5–10 Python repositories, ≥200 stars, with tests, spanning domains. Pin the
commit. Avoid anything whose hot path needs a network, a database or a GPU:
those produce `blocked` verdicts and measure nothing.

## Seeded smells, for recall

Not built yet. One file per root cause, containing exactly one planted
instance, with the answer recorded outside the file. `found / planted` is
recall, and per-root-cause it shows which cards are unusable.

Two cautions learned the hard way:

- A seeded smell must be one that *measures*. Eight root causes are advisory
  only; planting those tests the cards but never the verifier.
- Plant the smell in code that does something. A smell in a function nobody
  would ever call is a test of pattern matching, which is the thing we are
  trying not to reward.
