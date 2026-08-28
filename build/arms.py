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

Two things stay identical across every arm: the verifier, and what a finding
has to be to count. Otherwise the arms would not be comparable.
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
    templates: str = "taxonomy"
    """Which template tree under `build/templates/` this arm renders."""
    step_select: str = ""
    """Body of `1. Select` in SKILL.md."""
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


# -- step 1, for arms that have a scanner ----------------------------------

_SCANNER_SELECT = """\
Rank the units by how much work they are likely to do:

```bash
python $SKILL/scripts/scan.py <path> --units --top 20
```

This orders every function in the target by loop nesting, the nesting of the
callers that reach it, and how many places call it. It says nothing at all
about what might be wrong with any of them — that comes later, on purpose.

The ordering is a guess made from syntax. It cannot see how many times a loop
actually trips, which branches are taken in practice, or anything about calls
from other files. So read the repository too — its entry points, what its tests
exercise, what its README says it is for — and override the order wherever you
know better.

Examine at least 10 units, or all of them if the target has fewer.
"""

_KNOWLEDGE_SELECT = """\
Choose the units yourself.

Read the repository first: its entry points, what its tests exercise, what its
README says it is for. Then pick the units where energy is actually spent, in
this order of priority:

1. **work that repeats** — the deepest loop nests, and the helpers those loops
   call, which is where a cheap-looking function gets paid thousands of times;
2. **work proportional to input size**, rather than to a fixed constant;
3. **the repository's own hot path** — what it benchmarks, what its main entry
   point spends its time in.

Examine at least 10 units, or all of them if the target has fewer.
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
one thing to look at, not two. Facts are graded twice, and the two grades answer
different questions:

| `strength` | how sure the rule is that the fact is real |
|---|---|
| `definite` | a smell in essentially any context — confirm and move on |
| `likely` | usually a smell; check the card's exceptions |
| `contextual` | a fact and nothing more. **Justify it against this specific code, or drop it.** |

| `worth` | what the repair measured, in code that also does other work |
|---|---|
| `high` | 40% or more of the energy on the path it sits on |
| `medium` | roughly 10–40% |
| `low` | under 10% — real, and rarely what you should spend the change on |
| `unmeasured` | no shape of this root cause has a confirmed measurement, or the ones measured did not pay |

`worth` orders the list. It does not decide anything: a `low` fact inside a loop
that runs a billion times beats a `high` one that runs twice, and which is which
is exactly the part you can see and the rule cannot.

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
    step_select=_SCANNER_SELECT,
    step_evidence=_SCANNER_EVIDENCE,
    step_sweep=_sweep("e"),
)

AST_ONLY = Arm(
    name="ast",
    directory="ast/energy-smells",
    question="What do the taxonomy-specific analyzers contribute on their own?",
    step_select=_SCANNER_SELECT,
    step_evidence=_SCANNER_EVIDENCE,
    step_sweep=_sweep("e"),
    excluded=("lib/analysis/linters.py",),
)

RUFF_ONLY = Arm(
    name="ruff",
    directory="ruff/energy-smells",
    question="How far does an off-the-shelf linter get, with the same cards and protocol?",
    step_select=_SCANNER_SELECT,
    step_evidence=_SCANNER_EVIDENCE,
    step_sweep=_sweep("e"),
    excluded=("lib/analysis/rules",),
)

KNOWLEDGE_ONLY = Arm(
    name="knowledge",
    directory="knowledge/energy-smells",
    question="How well does the agent do on the taxonomy alone?",
    step_select=_KNOWLEDGE_SELECT,
    step_evidence="",
    step_sweep=_sweep("d"),
    excluded=("scan.py", "lib/analysis", "lib/signals.py"),
)

CONTROL = Arm(
    name="control",
    directory="control/energy-efficiency",
    question="How much does a frontier model save with no taxonomy, given the "
             "same task, the same rigour and the same verifier?",
    templates="control",
    excluded=("scan.py", "lib/analysis", "lib/signals.py"),
    ships_taxonomy=False,
)

ARMS = (FULL, AST_ONLY, RUFF_ONLY, KNOWLEDGE_ONLY, CONTROL)
