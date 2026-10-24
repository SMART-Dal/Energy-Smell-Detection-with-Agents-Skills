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
into a target repository. It is also why the rules part of step 1 is an
arm-supplied fragment rather than template text: an arm without rules has to
read as if nothing had ever been there.

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
    step_evidence: str = ""
    """The part of step 1 that runs the static rules, after the agent's own
    reading and before the list closes. Empty when there are none."""
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
    "ORDER_CHECKS": """The root-cause
cards open at `done 1`, all of them. `inputs.py` and `verify.py` run between
`done 2` and `done 3`.""",
    "ATTRIBUTION_HEADING": 'One repair, one root cause',
    "ATTRIBUTION_RULE": """Attribute each repair to one root cause: the one whose definition describes the
waste your edit removes. That is a rule about *attribution*, not about counting,
and it is not a demand that you find a uniquely correct label.

The cards overlap. Two of them might both describe what you repaired, and when
that happens either attribution is fine — say which you chose and that it was
close. What is not fine is filing a repair under a root cause whose definition
it does not match, because then the label is doing no work at all.

""",
    "CATEGORY_SECTION": """---

## Categories

{{CATEGORY_INDEX}}

Full index, with one line per root cause: `$SKILL/reference/README.md`.

""",
    "CONTEXT_POINTER": """   That is what the cards' near-misses are for, and skipping them is the
   fastest way to produce confident nonsense.""",
    "DECIDE_APPLIES": """Does the card's definition describe what this code
   does — not something adjacent? If one of its near-misses (`Looks like it,
   but is not`) fits, reject and name it. If another root cause fits better,
   reject this one and add that.""",
    "DECIDE_GROWTH": """A unit's suspicions may also **grow** here: reading the cards is one of the
better ways to find a root cause nobody suspected. Its units do not — they
were settled in step 1. A rejection with a reason is as much a result as an
acceptance.""",
    "DECIDE_MOVE": """Every suspicion ends this step **accepted** or **rejected**, and nothing is
edited in place. If the card says a suspicion belongs somewhere else, reject it
and add a new one, with a new label, for the root cause that fits. That keeps
what you first thought on the record, which is the part worth reading later.""",
    "DECIDE_PREAMBLE": """The root-cause cards are open from `step.py done 1` on. Go through the root
causes on your list one at a time: open `$SKILL/reference/root-causes/<ID>.md`,
read the whole card — the reference's definition, common patterns, the
measured repairs, and near-misses — and then decide every suspicion that names
it, in whichever units they are. Each card is read once and serves all of
them; the records stay one per unit.

**Skipping a card costs you.** The index line you listed from is a summary;
the card is the detail behind it: each repair as we wrote and measured it,
what it saved or did not, and the near-misses where the pattern is there but
the repair is not what the code needs. A suspicion decided without its card
can carry a repair that does not work on this code, and that shows only in
step 3, when `step2.jsonl` can no longer change. The card's patterns, repairs
and near-misses are what show exactly whether this code matches, and how.

- **The patterns and repairs are what we tested, not the whole root cause.**
  Real code might look like them, but not necessarily: it is usually longer,
  and the waste — and the repair — can run across several functions or
  classes. Waste the definition describes in a form no pattern or repair shows
  is still a finding.
- **A matching pattern does not guarantee a saving.** The author may have had a
  reason, and the current form may already be the efficient one for this code.
  Understand what the unit does before deciding the repair fits. If you judge
  the current form is better, reject it — or, if you are unsure, accept it and
  let the measurement decide.
- **Each repair ends with what our measurement found, and an action:**
  **Apply the after** — it saved energy; where the code has the *before*, write
  the *after*. **Decide which form fits** — on some inputs the *before* was
  the cheaper form, although the reference gives the *after*. Whichever form
  the code has now, judge from this repository — the code around the unit and
  the inputs it actually receives — whether the *before* or the *after* is
  better here, and measure when you cannot tell. **Report it; no need to measure** — nothing moved on any
  input: accept it if it fits and record it `deferred` in step 3.
  **Measure it** — our host could not resolve it.
- **Near-misses** (`Looks like it, but is not`) have the pattern, and there the
  repair would change what the code does or undo something done on purpose.""",
    "DECIDE_ROWS": """    "label": "a", "root_cause": "C5.S2", "lines": [58], "verdict": "rejected",
    "why": "`Looks like it, but is not` — nothing needs the list's order, so the container's type changes rather than an index being added beside it. Added `b` instead."
  },
  {
    "label": "b", "root_cause": "C5.S1", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request, built in __init__ at line 31 and read nowhere else; as a set each search is one hash lookup"
  }""",
    "DECISION_KEYS": '`label`, `root_cause`, `lines`, `verdict`, `why`',
    "EVIDENCE_AGAINST": 'the taxonomy',
    "FAILURE_MODES_CARDS": """1. **Listing from the index instead of the code.** A line in the index sounds
   like something, and the unit goes on the list without its code doing it.
   The index tells you what to look for; what the code does is what you list.
1. **Deciding from the label.** "Nested loops, so it must be an algorithmic
   complexity problem." Open the card; most of them are narrower than the name.
1. **One label dominating.** If a third of your findings share a root cause,
   you are pattern-matching. Re-derive them from the code.
""",
    "FINDING_RULE": """> A finding is a **repair**: a concrete edit to *this* code, attributed to a
> root cause whose definition the edit matches. That it saves energy is a
> separate claim, and only a measurement makes it.""",
    "ROOT_CAUSE_FIELD_RULE": """**`root_cause`** is one of the 65 IDs exactly as its card names it, such as
`C5.S1` — never a category such as `C5`. In step 1 it is the one the index
line matched; step 2 settles it against the card.

""",
    "NOTES_EXAMPLE": 'C10.S4. Sizes taken from the fixtures in tests/; `_row` left as the real helper.',
    "ONE_BASIS": 'one root cause',
    "REPAIR_BASIS": 'its root cause',
    "ROOT_CAUSE_FIELD": """  "root_cause": "C10.S4",
""",
    "ROOT_CAUSE_ROW": """| `root_cause` | the root cause the repair removes, as it appears on its card |
""",
    "SCOPE_IDS": """Python. Root cause IDs are exactly the 65 on the cards — never invent one, and
never report a bare category as a finding.""",
    "SKILL_DESCRIPTION": 'Find energy smells in Python code using the Watts This Smell taxonomy (12 categories, 65 root causes), and prove each one by measuring a refactoring that removes it. Use when asked to analyse code or a repository for energy smells, energy waste, power consumption, or energy inefficiency.',
    "SKILL_NAME": 'energy-smells',
    "STEP1_LENS": """**Know what you are looking for.** Read `$SKILL/reference/README.md` before
you read any code. Its twelve categories and sixty-five root causes, one line
each, are the kinds of waste this skill finds: keep them beside you as you
read, and ask of every function whether any of them is happening there. They
are for recognising waste, not for deciding it — code that does what a line
describes is reason enough to list a suspicion, and step 2 settles it with the
root cause's card.
`$SKILL/reference/root-causes/` stays locked until then, by design, not by
fault: it opens, all of it, at `python $SKILL/scripts/step.py done 1`. Waste
you see that no line names is still a suspicion: give it the root cause that
comes closest, and say in `why` what you saw.""",
    "SUBAGENT_LENS": 'the root causes listed in `$SKILL/reference/README.md` (give them its full path)',
    "SUSPICION_WHAT": 'the root cause from the index it looks like, the lines, and why',
    "SUBJECT": 'energy smells',
    "SUBJECT_SINGULAR": 'an energy smell',
    "SUBMISSION_ID_EXAMPLE": 'C10S4-render-concat',
    "SUSPICION_KEYS": '`label`, `root_cause`, `lines`, `why`',
    "SUSPICION_ROWS": """  {"label": "a", "root_cause": "C10.S4", "lines": [47],
   "why": "`self.buf` is grown with += once per row; nothing reads it in the loop"},
  {"label": "b", "root_cause": "C3.S2",  "lines": [44,45],
   "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row"}""",
    "TITLE": 'Energy Smell Identification',
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
    "ORDER_CHECKS": """`inputs.py` and
`verify.py` run between `done 2` and `done 3`.""",
    "ATTRIBUTION_HEADING": 'One repair, one reason',
    "ATTRIBUTION_RULE": """Attribute each repair to a single reason: the thing about the code that
explains why the edit saves energy.

""",
    "CATEGORY_SECTION": '',
    "CONTEXT_POINTER": '   Ask what the author was required to do before deciding they were wrong.',
    "DECIDE_APPLIES": """Does your account of the waste still hold on a second
   reading, or was it the shape of the code rather than what it does?""",
    "DECIDE_GROWTH": """A unit's suspicions may also **grow** here: reading a second time to write a
repair is one of the better ways to notice something you missed. Its units do
not — they were settled in step 1. A rejection with a reason is as much a
result as an acceptance.""",
    "DECIDE_MOVE": """Every suspicion ends this step **accepted** or **rejected**, and nothing is
edited in place. If the second reading changes your mind, reject the suspicion
and add a new one, with a new label, saying what you now think. That keeps what
you first thought on the record, which is the part worth reading later.""",
    "DECIDE_PREAMBLE": """Read the unit a second time, now with the repair in mind. What the edit would
have to be is usually what tells you whether your first reading was right.""",
    "DECIDE_ROWS": """    "label": "a", "lines": [58], "verdict": "rejected",
    "why": "the repair belongs where the container is built, not where it is searched. Added `b` instead."
  },
  {
    "label": "b", "lines": [31], "verdict": "accepted",
    "why": "`self.blocked` is a list searched once per request, built in __init__ at line 31 and read nowhere else; as a set each search is one hash lookup"
  }""",
    "DECISION_KEYS": '`label`, `lines`, `verdict`, `why`',
    "EVIDENCE_AGAINST": 'the repair',
    "FAILURE_MODES_CARDS": '',
    "FINDING_RULE": """> A finding is a **repair**: a concrete edit to *this* code, with a stated
> reason why the edit saves energy. That it does is a separate claim, and only
> a measurement makes it.""",
    "ROOT_CAUSE_FIELD_RULE": '',
    "NOTES_EXAMPLE": 'Sizes taken from the fixtures in tests/; `_row` left as the real helper.',
    "ONE_BASIS": 'one reason',
    "REPAIR_BASIS": 'what it repairs',
    "ROOT_CAUSE_FIELD": '',
    "ROOT_CAUSE_ROW": '',
    "SCOPE_IDS": 'Python. A finding is a repair with a reason, not a label.',
    "SKILL_DESCRIPTION": 'Find places where Python code wastes energy, refactor them, and prove the saving by measuring it. Use when asked to analyse code or a repository for energy waste, energy efficiency, power consumption, or wasteful computation.',
    "SKILL_NAME": 'energy-efficiency',
    "STEP1_LENS": """**Know what you are looking for:** work the program does not need, work done
more often than necessary, or work done in a more expensive way than its result
requires. Ask of every function whether any of these is happening there.""",
    "SUBAGENT_LENS": 'these three kinds of waste',
    "SUSPICION_WHAT": 'the lines, and why',
    "SUBJECT": 'energy waste',
    "SUBJECT_SINGULAR": 'energy waste',
    "SUBMISSION_ID_EXAMPLE": 'render-concat',
    "SUSPICION_KEYS": '`label`, `lines`, `why`',
    "SUSPICION_ROWS": """  {"label": "a", "lines": [47],
   "why": "`self.buf` is grown with += once per row; nothing reads it in the loop"},
  {"label": "b", "lines": [44,45],
   "why": "`sorted(self.columns)` is recomputed per row and does not depend on the row"}""",
    "TITLE": 'Energy Efficiency Analysis',
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


# The knowledge arm ships the taxonomy and no scanner, so nothing in it may
# mention rules, a tool's findings, or evidence "reported to you" -- that would
# tell the agent a fuller condition exists. The taxonomy words above say nothing
# of the kind (the rules live in `step_evidence` alone), so it uses them as
# they are.


# -- the rules part of step 1, for arms that have a scanner -----------------
#
# After the agent's own reading and before the list closes: the rules are there
# to catch what the reading missed, so they may add units, and they can only do
# that while step 1 is open. Whether a rule flags a finding is measured after
# the run, on the untouched repository (summarize.py), not asked of the agent.

_SCANNER_EVIDENCE = """\
**When you have been through every file and written `step1.jsonl`, compare the
rules with it** — after your own reading, so that what you list first is what
you saw. The rules stay closed until `step1.jsonl` exists:

```bash
python $SKILL/scripts/scan.py <path>
```

It reads your `step1.jsonl`, runs every rule over `<path>`, and writes
everything to one file, `.energy-scan/scan.txt`; the terminal shows only how
many entries each part holds. Read that file whole. It has three parts:

1. **units the rules flag that are not on your list;**
2. **units on your list where a rule names a root cause you did not suspect
   there;**
3. **units on your list where a rule agrees with you.**

Every entry in parts 1 and 2 shows the root causes, the fact the rule saw, its
lines, and the code on them. For each one, read the unit's code and decide for
yourself: add the unit, or the suspicion, to `step1.jsonl` if you agree, and
leave it if you do not. If the file is long you may hand groups of its entries
to subagents, as with the reading; look at the code of whatever they bring back
before you list it.

`step.py done 1` checks that this comparison was made.

This is an assistant, not an authority. It applies a fixed set of deterministic
rules and reports **facts** — "a string is grown with `+=` inside a loop at line
45" — one entry per rule per unit, tagged with every root cause that fact could
point at. Two labels on one fact means the shape alone does not say which; it is
one thing to look at, not two.

Within each part the entries are in file and line order. The order says nothing
about which findings matter — read in whatever order you think right. There is
no confidence score and no per-finding number, because either would be a
judgement about this code that the rule is in no position to make.

Two things follow from what a rule is, and they point in opposite directions.

**It reports shapes, so some of what it reports is wrong here.** Whether a
pattern is waste depends on what the code is for, what the author was
constrained by, and how often it runs — none of which a rule can see. Be
careful, and spend your time on the ones you can show are real.

**It only knows shapes somebody described in advance, so it misses the rest.**
Waste that lives in the arrangement of a program has no fixed syntax and leaves
no trace here however expensive it is. Silence from this tool is not evidence of
anything.

So reconcile it against the list you already wrote, and keep your own judgement:

- **it agrees with you** — you now have two independent reasons;
- **it saw something you did not** — read that code and decide for yourself,
  and add the suspicion, or the unit, if you agree. Being pointed at a line is
  not being told it is wrong;
- **it flags something you judged fine** — you may well be right. Keep your
  judgement and move on;
- **it is silent where you are suspicious** — that means nothing at all. Keep
  the suspicion.

Do this before step 1 is finished: the rules can add a unit only while the list
is still open.

"""


# -- the arms ---------------------------------------------------------------

FULL = Arm(
    name="full",
    directory="full/energy-smells",
    question="Do the two evidence sources compose, or does one crowd out the other?",
    words=_TAXONOMY_WORDS,
    step_evidence=_SCANNER_EVIDENCE,
)

AST_ONLY = Arm(
    name="ast",
    directory="ast/energy-smells",
    question="What do the taxonomy-specific analyzers contribute on their own?",
    words=_TAXONOMY_WORDS,
    step_evidence=_SCANNER_EVIDENCE,
    excluded=("lib/analysis/linters.py",),
)

RUFF_ONLY = Arm(
    name="ruff",
    directory="ruff/energy-smells",
    question="How far does an off-the-shelf linter get, with the same cards and protocol?",
    words=_TAXONOMY_WORDS,
    step_evidence=_SCANNER_EVIDENCE,
    excluded=("lib/analysis/rules",),
)

KNOWLEDGE_ONLY = Arm(
    name="knowledge",
    directory="knowledge/energy-smells",
    question="How well does the agent do on the taxonomy alone?",
    words=_TAXONOMY_WORDS,
    step_evidence="",
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
