"""The experimental arms, each built as its own self-contained skill.

An arm is a condition, not a runtime option. It decides what the agent is
*given*, so it has to be chosen by whoever runs the experiment and baked into
the directory they hand over. A `--mode` flag got this wrong twice:

  - the agent chose its own condition, so nothing stopped it running `--mode
    full` in what was supposed to be the knowledge-only arm;
  - and even when it obeyed, `--mode off` left `scripts/lib/analysis/rules/`
    sitting in the skill directory. Those files are a plain-language list of
    every pattern we consider suspicious. An agent that reads them has been
    handed the static analysis after all, in the most direct form possible.

So each arm ships only the code its condition allows, and the scanner discovers
its analyzers rather than being told about them: with no `rules/` package on
disk there are no tree-walking rules, with no `linters.py` there is no external
linter, and the same `scan.py` runs unchanged in every case.

**Nothing inside an arm may reveal that the other arms exist.** Not a config
file naming the condition, not a sentence explaining what is absent, not an
enum with a value nothing here can produce. An agent that works out it is in an
ablation is answering a different question from the one we asked, and the
comparison is spoiled. Anything an arm needs to say about its own limits has to
be sayable from inside, as a statement about static analysis in general.

That constraint reaches further than it looks, which is why the four taxonomy
arms all ship a directory named `energy-smells` and differ only in the *parent*
directory holding it -- the parent is the experimenter's filing, never copied
into a target repository. It is also why the sub-steps of step 2 are assembled
from arm-supplied fragments rather than written into the template with fixed
letters: an arm whose step 2 ran a, b, c, e would be announcing that something
used to sit at d.

**Every arm renders the same templates.** There is one `SKILL.md`, one
`verifying.md` and one `output-format.md`, and an arm fills `{{WORD}}` slots in
them. A slot exists only where the arm genuinely has something the others do
not: a card to open, a category index to read, a root cause to name. The build
refuses to ship a file with a slot left unfilled.

That is not tidiness. Two template trees drifted apart once already -- the
control arm ended up calling the same field `observations` where the others
called it `suspicions`, omitted `own_hypotheses` entirely, and kept a
description of the statistics that had been superseded months earlier. Every
one of those is a difference in what the agent was told to do, inside an
experiment whose whole purpose is to compare arms that were told the same
thing. A single source makes that class of drift impossible rather than
unlikely.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Arm:
    """One deliverable: a skill directory with a fixed evidence condition."""

    name: str
    directory: str
    """Path under `dist/`, as `<condition>/<skill name>`.

    The last component is what gets copied into a target repository, so it has
    to be the same in every arm that ships the taxonomy. The condition lives in
    the component above it, which stays behind.
    """

    question: str
    """What this arm is for. Printed by the build; never shipped."""
    templates: str = "shared"
    """Which template tree under `build/templates/` this arm renders.

    Every arm renders the same one. The field survives so the build does not
    hard-code a path, not because the arms differ here.
    """
    words: dict = field(default_factory=dict, compare=False)
    """What this arm fills into the shared template's `{{WORD}}` slots.

    Every arm must supply every key, so a slot cannot silently render empty in
    one arm and not another. Excluded from equality because an `Arm` is used as
    a dict key and a dict field is unhashable.
    """
    omit_templates: tuple[str, ...] = field(default=())
    """Template files this arm does not ship, as paths under the tree."""
    scanner_hint: str = ""
    """One line in step 1 pointing at the scanner. Empty where there is none."""
    step_evidence: str = ""
    """The sub-step of step 2 that runs the static rules. Empty when there are none."""
    step_sweep: str = ""
    """The sub-step of step 2 that sweeps the full index.

    Carries its own sub-step letter, which is why it differs between arms that
    have a rules sub-step before it and arms that do not.
    """
    excluded: tuple[str, ...] = field(default=())
    """Paths under scripts/ that must not exist in this arm."""
    ships_taxonomy: bool = True
    """Whether the cards and the routing table are rendered into this arm."""

    @property
    def ships_scanner(self) -> bool:
        return "scan.py" not in self.excluded


# -- the words each arm fills into the shared template ---------------------
#
# Every arm renders the same SKILL.md. These are the only places the text may
# differ, and each one exists because the arm genuinely has something the other
# does not -- a card to open, a category index to read, a root cause to name.
# Anything else being different would mean one arm was told more about how to
# do the work than another, and the comparison would be measuring the
# instructions rather than the evidence.

_TAXONOMY_WORDS = {
    "ADVISORY_NOTE": """Root causes marked **advisory only** on their card are exempt from measurement:
their repair is worth a single bytecode instruction and cannot clear any noise
floor. Report them as `advisory`, and do not build a case file.

""",
    "ADVISORY_ROW": """| `advisory` | card says advisory only; never measured | report as advisory, no numbers |
""",
    "ADVISORY_RULE": """The only exception is a root cause whose card
says *advisory only* — its repair is one bytecode instruction and provably
cannot clear any noise floor, so it is reported as unmeasured rather than
measured badly.""",
    "ATTRIBUTION_HEADING": 'One repair, one root cause',
    "ATTRIBUTION_RULE": """Attribute each repair to one root cause: the one whose definition describes the
waste your edit removes. That is a rule about *attribution*, not about counting,
and it is not a demand that you find a uniquely correct label.

The cards overlap. Two of them might both describe what you repaired, and when
that happens either attribution is fine — say which you chose and that it was
close. What is not fine is filing a repair under a root cause whose definition
it does not match, because then the label is doing no work at all.

""",
    "BEFORE_NAMING": 'before opening any card',
    "CASE_DOCSTRING": 'C10.S4 in src/render.py::Report.render — string built with += in a loop.',
    "CASE_FILE_EXAMPLE": 'case_C10S4',
    "CATEGORY_SECTION": """---

## Categories

{{CATEGORY_INDEX}}

Full index, with one line per root cause: `$SKILL/reference/README.md`.

""",
    "CONTEXT_POINTER": """   That is what the cards' exception sections are for, and skipping them is
   the fastest way to produce confident nonsense.""",
    "DECIDE_CARD_CHECKS": """1. **Apply `NOT a smell when` and `Looks the same, is not`.** These are the
   cases where the pattern is present and correct, and they are the most
   valuable thing on the card. If one fits, reject and record which.
""",
    "DECIDE_CHANGEABLE": """- **`root_cause`** — a card in the `Similar root causes` list fitted better.
  Open those; that is what they are there for.
- **`lines`** — the card made clear the real site is somewhere else. The
  membership test you flagged is a symptom; the line the repair changes is
  where the container is built.
- **`why`** — rewritten against the card, instead of your first impression.
""",
    "DECIDE_GROWTH": """Opening one card and following its similar list is one of the better ways to
find a root cause nobody suspected. When that happens, add it with
`found_by: "cards"` and hold it to exactly the same checks.""",
    "DECIDE_PREAMBLE": """Open `$SKILL/reference/root-causes/<ID>.md` for every suspicion.

**Read the whole card**, not the section whose heading matches your question.
The description at the top, `What to look for`, the exceptions, the
near-misses, the repair examples — all of it is evidence about whether this is
the right root cause. The near-misses decide the hard cases, and the repair
examples are where you find out what the edit actually involves, which is
usually not what the name suggested.
""",
    "DECIDE_ROWS": """    "root_cause": "C5.S1", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request; built in __init__ at line 31",
    "changed_from": {"root_cause": "C5.S2", "lines": [58]},
    "why_changed": "nothing needs the list's order, so the container's type changes rather than an index being added beside it",
    "hotness": "one call per request; `routes` is 400-2000 entries",
    "repair_sketch": "build `self.blocked` as a set",
    "patch_shape": "expression",
    "spans_units": ["src/router.py::Router.__init__"],
    "found_by": "reading"
  },
  {
    "root_cause": "C3.S4", "lines": [58], "verdict": "rejected",
    "why_rejected": "the hotness check — `handle` runs once per process, over the static route table",
    "found_by": "rules"
  }""",
    "EVIDENCE_AGAINST": 'the taxonomy',
    "EVIDENCE_FIELDS": """
      "evidence": ["string_concat_in_loop"],

      "also_considered": [
        {"id": "C10.S1", "why": "no repeated type conversion; the parts are already strings"}
      ],
""",
    "FAILURE_MODES_CARDS": """1. **Deciding from the label.** "Nested loops, so it must be an algorithmic
   complexity problem." Open the card; most of them are narrower than the name.
1. **One label dominating.** If a third of your findings share a root cause,
   you are pattern-matching. Re-derive them from the code.
""",
    "FINDING_ID_FIELDS": """      "root_cause": "C10.S4",
      "name": "Inefficient String Concatenation",
      "category": "C10",
""",
    "FINDING_RULE": """> A finding is a **repair**: a concrete edit to *this* code, attributed to a
> root cause whose definition the edit matches, and measured.""",
    "FOUND_BY_EXAMPLE": 'both',
    "FOUND_BY_FIELD_RULES": """**`found_by`** records how you came to suspect it: `reading`, `rules`, `both`,
`sweep` for the index pass at the end of step 2, or `cards` for a root cause
that first appeared while you were reading a card in step 3. It is the
difference between an analysis you did and a list you were handed, and it is
measured across runs, so record it honestly — including the cases where you
missed something.

**`evidence`** lists any deterministic observation that pointed here, named
exactly as it was reported to you. Leave it `[]` when you found it by reading,
which is the normal case.

**`also_considered`** names the similar cards you opened and did not file this
under. Not a requirement to prove one card excludes another — these overlap on
purpose — but a record of where you looked. Leave it out if you opened none.

""",
    "FOUND_BY_NOTE": """
`found_by` says how you came to suspect it, and is recorded honestly:
`"reading"` from 2a–2b, `"rules"` from a tool, `"both"`, or `"sweep"` from the
index pass. It is the difference between an analysis you did and a list you
were handed.
""",
    "NEGLIGIBLE_VALUE": 'they are evidence about the taxonomy, not failures to hide.',
    "ONE_BASIS": 'one root cause',
    "PATCH_BOUND": """Each card names a patch shape. It bounds the **size** of the edit, never its
location, and never how much code you may read to decide.""",
    "PATCH_SHAPE_ROW": """        "patch_shape": "statement_local",
""",
    "REDECIDE": """re-open the cards for every remaining accepted
   candidate.""",
    "REPAIR_ORDER": """Sort by how much of the code the repair moves: `cross_unit` and `structural`
first, then `signature`, then `statement_local`, then `expression`.""",
    "REPORT_ADVISORY": ', 1 advisory',
    "REPORT_HEADING_FIELDS": 'the root cause and its name,',
    "REPORT_TABLE": """| Unit | Root cause | Energy saved |
|---|---|---|
| `src/render.py::Report.render` | C10.S4 Inefficient String Concatenation | 25.9% ± 3.0% |""",
    "REPORT_TITLE": 'Energy smells',
    "SCOPE_IDS": """Python. Root cause IDs are exactly the 65 on the cards — never invent one, and
never report a bare category as a finding.""",
    "SIZING_HINT": " The card's workload hint says which.",
    "SKILL_DESCRIPTION": 'Find energy smells in Python code using the Watts This Smell taxonomy (12 categories, 65 root causes), and prove each one by measuring a refactoring that removes it. Use when asked to analyse code or a repository for energy smells, energy waste, power consumption, or energy inefficiency.',
    "SKILL_NAME": 'energy-smells',
    "STEP_2B": """**2b. Say what looks wasteful, in your own words, before opening any card.**
No IDs yet. Just: which work here does not need to happen, is done more often
than necessary, or is done in a more expensive way than the result requires?
Write this down — it goes in the output as `own_hypotheses`.""",
    "STEP_DECIDE": '',
    "STEP_TAXONOMY_MATCH": """**2c. Now match against the taxonomy, at the shallow level only.** Read the
category index at the bottom of this file. Open
`$SKILL/reference/categories/<ID>.md` for any category that might apply — each
one lists its root causes with a line apiece, which is usually enough to tell
whether one is worth a closer look.

**Do not open root-cause cards yet.** You are producing suspicions, not
verdicts.

Open the categories your reading pointed you at, and open others if the code
suggests them. Nothing restricts which you may consider.

""",
    "SUBJECT": 'energy smells',
    "SUBJECT_SINGULAR": 'an energy smell',
    "SUBSUMED_ROW": """        {"id": "C6.S1", "why": "the per-row temporary only existed to feed the +=; the repair removed it"}""",
    "SUSPICION_ROWS": """    {"root_cause": "C10.S4", "lines": [47],    "confidence": "high",
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "found_by": "both"},
    {"root_cause": "C3.S2",  "lines": [44,45], "confidence": "medium",
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row",
     "found_by": "reading"}""",
    "TITLE": 'Energy Smell Identification',
    "UNIT_SUSPICIONS": """      "suspicions": [
        {"root_cause": "C10.S4", "confidence": "high",   "found_by": "both"},
        {"root_cause": "C3.S2",  "confidence": "medium", "found_by": "reading"},
        {"root_cause": "C6.S1",  "confidence": "low",    "found_by": "rules"},
        {"root_cause": "C5.S4",  "confidence": "low",    "found_by": "sweep"}
      ],
      "dropped": [
        {"root_cause": "C5.S4", "at_step": 3, "why": "the conversion feeds a second use, so nothing is redundant"},
        {"root_cause": "C6.S1", "at_step": 4, "why": "subsumed by the C10.S4 repair"}
      ],
      "found": ["C10.S4"]""",
    "WHEN_WRONG": """## When the card is wrong

It happens, and measurement is how you find out.

C10.S4 used to say what every style guide says: growing a string with `+=` in a
loop is quadratic, so collect the parts and join them. Measured, the textbook
example got *slower* — 62 ms against 56 ms at 400 000 iterations. CPython
resizes a string in place when nothing else refers to it, so the classic
example was already linear. The real waste turned out to be about aliasing:
through an attribute, where the optimisation cannot fire, the same repair saves
94.8% ± 0.1%.

If a repair you built faithfully from a card comes back `negligible`, that is a
result. Report it, say which card, and say what you measured. Do not quietly
drop it and try a different root cause until one sticks.
""",
}

_CONTROL_WORDS = {
    "ADVISORY_NOTE": '',
    "ADVISORY_ROW": '',
    "ADVISORY_RULE": """The only exception is a repair worth a fixed and
very small amount per execution — a single bytecode instruction, say — which
provably cannot clear any noise floor, and is reported as unmeasured rather
than measured badly.""",
    "ATTRIBUTION_HEADING": 'One repair, one reason',
    "ATTRIBUTION_RULE": """Attribute each repair to a single reason: the thing about the code that
explains why the edit saves energy.

""",
    "BEFORE_NAMING": 'before naming anything',
    "CASE_DOCSTRING": 'src/render.py::Report.render — string built with += in a loop.',
    "CASE_FILE_EXAMPLE": 'case_render_concat',
    "CATEGORY_SECTION": '',
    "CONTEXT_POINTER": '   Ask what the author was required to do before deciding they were wrong.',
    "DECIDE_CARD_CHECKS": '',
    "DECIDE_CHANGEABLE": """- **`lines`** — the second reading made clear the real site is somewhere else.
  The membership test you flagged is a symptom; the line the repair changes is
  where the container is built.
- **`why`** — rewritten against the code, instead of your first impression.
""",
    "DECIDE_GROWTH": """Reading a second time to write a repair is one of the better ways to notice
something you missed.""",
    "DECIDE_PREAMBLE": """Not everything wasteful is worth repairing, and this is where that gets
settled. Read the unit a second time, now with the repair in mind: what the
edit would have to be is usually what tells you whether your first reading of
the waste was right.
""",
    "DECIDE_ROWS": """    "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request; built in __init__ at line 31",
    "changed_from": {"lines": [58]},
    "why_changed": "the repair changes where the container is built, not where it is searched",
    "hotness": "one call per request; `routes` is 400-2000 entries",
    "repair_sketch": "build `self.blocked` as a set",
    "spans_units": ["src/router.py::Router.__init__"],
    "found_by": "reading"
  },
  {
    "lines": [58], "verdict": "rejected",
    "why_rejected": "the hotness check — `handle` runs once per process, over the static route table",
    "found_by": "reading"
  }""",
    "EVIDENCE_AGAINST": 'the repair',
    "EVIDENCE_FIELDS": '',
    "FAILURE_MODES_CARDS": '',
    "FINDING_ID_FIELDS": '',
    "FINDING_RULE": """> A finding is a **repair**: a concrete edit to *this* code, with a stated
> reason why the edit saves energy, and measured.""",
    "FOUND_BY_EXAMPLE": 'reading',
    "FOUND_BY_FIELD_RULES": """**`found_by`** records how you came to suspect it. With no tool in the loop it
is `reading` throughout, and it is kept so a reader can tell an analysis you
did from a list you were handed.

""",
    "FOUND_BY_NOTE": '',
    "NEGLIGIBLE_VALUE": 'a repair that turned out not to help is a result, not a failure to hide.',
    "ONE_BASIS": 'one reason',
    "PATCH_BOUND": """The edit should be as small as removing the waste allows. That bounds its
**size**, never its location, and never how much code you may read to decide.""",
    "PATCH_SHAPE_ROW": '',
    "REDECIDE": 're-decide every remaining accepted candidate.',
    "REPAIR_ORDER": 'Sort by how much of the code the repair moves, largest first.',
    "REPORT_ADVISORY": '',
    "REPORT_HEADING_FIELDS": 'the lines,',
    "REPORT_TABLE": """| Unit | What was repaired | Energy saved |
|---|---|---|
| `src/render.py::Report.render` | string built with `+=` in a loop | 25.9% ± 3.0% |""",
    "REPORT_TITLE": 'Energy efficiency',
    "SCOPE_IDS": 'Python. A finding is a repair with a reason, not a label.',
    "SIZING_HINT": '',
    "SKILL_DESCRIPTION": 'Find places where Python code wastes energy, refactor them, and prove the saving by measuring it. Use when asked to analyse code or a repository for energy waste, energy efficiency, power consumption, or wasteful computation.',
    "SKILL_NAME": 'energy-efficiency',
    "STEP_2B": """**2b. Say what looks wasteful, in your own words, before naming it.** Just:
which work here does not need to happen, is done more often than necessary, or
is done in a more expensive way than the result requires? Write this down — it
goes in the output as `own_hypotheses`.""",
    "STEP_DECIDE": '',
    "STEP_TAXONOMY_MATCH": '',
    "SUBJECT": 'energy waste',
    "SUBJECT_SINGULAR": 'energy waste',
    "SUBSUMED_ROW": """        {"what": "the per-row temporary list", "why": "it only existed to feed the +=; the repair removed it"}""",
    "SUSPICION_ROWS": """    {"lines": [47],    "confidence": "high",
     "why": "`self.buf` is grown with += once per row; nothing reads it in the loop",
     "found_by": "reading"},
    {"lines": [44,45], "confidence": "medium",
     "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row",
     "found_by": "reading"}""",
    "TITLE": 'Energy Efficiency Analysis',
    "UNIT_SUSPICIONS": """      "suspicions": [
        {"lines": [47],    "confidence": "high"},
        {"lines": [44,45], "confidence": "medium"},
        {"lines": [51],    "confidence": "low"}
      ],
      "dropped": [
        {"lines": [51], "at_step": 3, "why": "the conversion feeds a second use, so nothing is redundant"}
      ],
      "found": [47]""",
    "WHEN_WRONG": """## When received wisdom is wrong

It happens, and measurement is how you find out.

Every style guide says growing a string with `+=` in a loop is quadratic, so
collect the parts and join them. Measured, the textbook example got *slower* —
62 ms against 56 ms at 400 000 iterations. CPython resizes a string in place
when nothing else refers to it, so the classic example was already linear. The
real waste turned out to be about aliasing: through an attribute, where the
optimisation cannot fire, the same repair saves 94.8% ± 0.1%.

If a repair you were confident about comes back `negligible`, that is a result.
Report it, and say what you measured. Do not quietly drop it and try a
different one until something sticks.
""",
}


# -- step 1's one optional line -------------------------------------------
#
# Step 1 is identical in every arm: read the repository, pick the units, order
# them by expected saving. An arm that ships the scanner adds a single line
# offering it as a second opinion. It is deliberately not a step -- making the
# agent run a tool to choose units would be a different instruction from the
# one the other arms get, and the difference between arms has to be the
# evidence available, not the procedure.

_SCANNER_HINT = """
`python $SKILL/scripts/scan.py <path> --units --top 20` will also list the
units, ordered by loop nesting and how many places call them. It is a guess
made from syntax and says nothing about what might be wrong with any of them,
so treat it as a second opinion on the order rather than the order itself.
"""

# -- the rules sub-step, for arms that have a scanner ----------------------

_SCANNER_EVIDENCE = """\
**2d. Now, and only now, run the rules.**

```bash
python $SKILL/scripts/scan.py <path>              # index: which units, how much
python $SKILL/scripts/scan.py <path> --unit NAME  # one unit's findings in full
```

The first command prints an **index** and writes the detail to a file. That is
deliberate: read the index, pick the units you already care about, and open
those. Do not open every unit, and do not read the detail file end to end — the
whole of it is longer than your account of the code should be, and a list read
in full becomes the account instead of checking it.

This is an assistant, not an authority. It applies a fixed set of deterministic
rules and reports **facts** — "a string is grown with `+=` inside a loop at line
45" — one entry per rule per unit, tagged with every root cause that fact could
point at. Two labels on one fact means the shape alone does not say which; it is
one thing to look at, not two.

Each fact carries one number: **what this repair measured elsewhere.** It is the
mean energy saved across our own benchmark shapes for that root cause, with
shapes where the repair did not pay counted as zero. So 0% does not mean
unmeasured — it means measured and it did not reliably pay.

That number orders the list and decides nothing else. It is a prior from other
code, not a prediction for this code: a 5% repair inside a loop that runs a
billion times beats a 90% one that runs twice, and which is which is exactly the
part you can see and the rule cannot.

There is no confidence score, deliberately. Every one of these shapes is the
right thing to write somewhere, so none of them is graded as more or less likely
to be a real smell — that judgement is yours, made against this code, and a
label claiming to have made it for you would only be in the way.

Two things follow from what a rule is, and they point in opposite directions.

**It reports shapes, so some of what it reports is wrong.** Every pattern here
is the right thing to write somewhere. Whether it is right *in this code*
depends on what the code is for, what the author was constrained by, and how
often it runs — three things you can read and the rule cannot. Expect false
positives and say so when you find one.

**It only knows shapes somebody described in advance, so it misses the rest.**
Waste that lives in the arrangement of a program has no fixed syntax and leaves
no trace here however expensive it is. Silence from this tool is not evidence of
anything.

So reconcile it against the list you already wrote, and keep your own judgement:

- **it agrees with you** — you now have two independent reasons;
- **it saw something you did not** — read that code again and decide for
  yourself. Being pointed at a line is not being told it is wrong;
- **it flags something you judged fine** — you may well be right. Keep your
  judgement and record why;
- **it is silent where you are suspicious** — that means nothing at all. Keep
  the suspicion and carry it forward.

Add `found_by` to every suspicion: `"reading"`, `"rules"`, or `"both"`.

"""

# -- the index sweep, present in every arm that ships the taxonomy ---------


def _sweep(letter: str) -> str:
    """The final sub-step of step 2, lettered to follow whatever came before.

    Placed last on purpose. Read before the code, a list of sixty-five labels
    is a menu and the agent picks the familiar ones; read after the agent has
    written its own account of what is wrong, the same list is a check for
    omissions -- which is what it is here for.
    """
    return f"""\
**2{letter}. Sweep the full index for what you have not named.**

Read `$SKILL/reference/README.md`, which lists all sixty-five root causes with
one line each. Go down it once, against this unit, asking a single question:

> is any of these happening here, that I have not already written down?

You are looking for two things in particular. Waste you *noticed* while reading
but could not name, which is what this index is for. And waste you did not
notice at all, where the one-line description makes you go back and look.

Add anything you find to `suspicions` with `found_by: "sweep"`. Do not revise
anything already on the list, and do not drop items because the sweep did not
independently produce them — the point of doing this last is that your own
reading stays the primary account and this only adds to it.

Expect most sweeps to add nothing. That is a normal outcome and not a sign you
did it wrong.

"""


# -- the arms ---------------------------------------------------------------

FULL = Arm(
    name="full",
    directory="full/energy-smells",
    question="Do the two evidence sources compose, or does one crowd out the other?",
    words=_TAXONOMY_WORDS,
    scanner_hint=_SCANNER_HINT,
    step_evidence=_SCANNER_EVIDENCE,
    step_sweep=_sweep("e"),
)

AST_ONLY = Arm(
    name="ast",
    directory="ast/energy-smells",
    question="What do the taxonomy-specific analyzers contribute on their own?",
    words=_TAXONOMY_WORDS,
    scanner_hint=_SCANNER_HINT,
    step_evidence=_SCANNER_EVIDENCE,
    step_sweep=_sweep("e"),
    excluded=("lib/analysis/linters.py",),
)

RUFF_ONLY = Arm(
    name="ruff",
    directory="ruff/energy-smells",
    question="How far does an off-the-shelf linter get, with the same cards and protocol?",
    words=_TAXONOMY_WORDS,
    scanner_hint=_SCANNER_HINT,
    step_evidence=_SCANNER_EVIDENCE,
    step_sweep=_sweep("e"),
    excluded=("lib/analysis/rules",),
)

KNOWLEDGE_ONLY = Arm(
    name="knowledge",
    directory="knowledge/energy-smells",
    question="How well does the agent do on the taxonomy alone?",
    words=_TAXONOMY_WORDS,
    step_evidence="",
    step_sweep=_sweep("d"),
    excluded=("scan.py", "lib/analysis", "lib/signals.py"),
)

CONTROL = Arm(
    name="control",
    directory="control/energy-efficiency",
    question="How much does a frontier model save with no taxonomy, given the "
             "same task, the same rigour and the same verifier?",
    words=_CONTROL_WORDS,
    omit_templates=("reference/README.md",),
    excluded=("scan.py", "lib/analysis", "lib/signals.py"),
    ships_taxonomy=False,
)

ARMS = (FULL, AST_ONLY, RUFF_ONLY, KNOWLEDGE_ONLY, CONTROL)
