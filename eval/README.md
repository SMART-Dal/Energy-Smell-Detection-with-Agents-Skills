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

# 2. install exactly one arm
mkdir -p .claude/skills
cp -r /home/javad/energy_smell_detection/dist/full/energy-smells .claude/skills/

# 3. start a new session here and give it exactly this:
```

> Find the energy smells in `src/requests` using the energy-smells skill.
> Write `findings.json` and `REPORT.md`.

Say nothing else. Anything you add is a hint the skill should have contained.

For the control arm the prompt has to change, because that arm has no taxonomy
and the word "smell" is taxonomy vocabulary:

> Find where `src/requests` wastes energy, using the energy-efficiency skill.
> Write `findings.json` and `REPORT.md`.

## The arms

The arm is fixed at build time, not chosen by a flag, so setting it means
copying a different directory. Nothing the agent can do changes its condition,
and nothing in the directory says which one it is.

| Arm | Install | Question it answers |
|---|---|---|
| full | `dist/full/energy-smells` | do the two evidence sources compose? |
| ast | `dist/ast/energy-smells` | what do the taxonomy-specific analyzers contribute? |
| ruff | `dist/ruff/energy-smells` | what does an off-the-shelf linter contribute? |
| knowledge | `dist/knowledge/energy-smells` | how well does the agent do on the taxonomy alone? |
| control | `dist/control/energy-efficiency` | would a frontier model have found these anyway? |

**One arm per environment.** All four taxonomy arms install as a directory
called `energy-smells`, so a second one does not sit visibly beside the first —
it overwrites it, or worse, leaves a mixture. Start from a clean checkout of the
target for every run.

## What to record

For each run: the arm, the repo, the commit, and from `findings.json` —

| Metric | Where from |
|---|---|
| **precision** | `confirmed / (confirmed + refuted)` |
| units examined | `len(units_examined)` |
| findings per unit | `len(findings) / len(units_examined)` |
| label concentration | most common `root_cause` as a share of all findings |
| unprompted findings | findings whose `evidence` is `[]`, in an arm that has a scanner |
| swept findings | findings whose `found_by` is `"sweep"` or `"cards"` |
| cost | wall clock, tokens |

Precision needs no ground truth: the verifier is the oracle. That is the point
of making measurement mandatory, and it is what lets any repository be a test
set.

Two of these measure things the protocol was changed to produce, so they are
worth reading together. **Unprompted findings** say whether the agent is
reading or being led. **Swept findings** say whether the index pass at the end
of step 2 earns its tokens; if it is consistently zero, drop it.

Recall does need ground truth, so it needs the seeded corpus below.

## The corpus

5–10 Python repositories, ≥200 stars, with tests, spanning domains. Pin the
commit. Avoid anything whose hot path needs a network, a database or a GPU:
those produce `blocked` verdicts and measure nothing.

## Seeded smells, for recall

Not built yet. One file per root cause, containing exactly one planted
instance, with the answer recorded outside the file. `found / planted` is
recall, and per-root-cause it shows which cards are unusable.

Three cautions, two of them learned the hard way:

- A seeded smell must be one that *measures*. Three root causes are advisory
  only; planting those tests the cards but never the verifier. (It was eight
  until the taxonomy suite measured five of them and found they were not.)
- Plant the smell in code that does something. A smell in a function nobody
  would ever call is a test of pattern matching, which is the thing we are
  trying not to reward.
- Plant some of them across two units. Thirteen root causes have no static
  signal at all, and the ones that matter most tend to live in the arrangement
  of a program rather than in a line — a corpus of single-line plants measures
  the easy half and reports it as recall.

## Before any of this

Run `validation/preflight.py` on the host, and record the noise floor beside
every result. A cold agent producing `refuted` verdicts on a busy machine is
measuring the machine.
