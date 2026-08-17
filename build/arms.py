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
    question: str
    """What this arm is for. Printed by the build; never shipped."""
    templates: str = "taxonomy"
    """Which template tree under `build/templates/` this arm renders."""
    step_select: str = ""
    """Body of `1. Select` in SKILL.md."""
    step_evidence: str = ""
    """Body of `2d`, where the static rules enter. Empty when there are none."""
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

Examine at least 10 units, or all of them if the target has fewer. Record every
unit you looked at, including the ones you cleared.
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

Examine at least 10 units, or all of them if the target has fewer. Record every
unit you looked at, including the ones you cleared.
"""

# -- step 2d, for arms that have a scanner ---------------------------------

_SCANNER_EVIDENCE = """\
**2d. Now, and only now, run the rules.**

```bash
python $SKILL/scripts/scan.py <path> --top 15
```

This applies a fixed set of deterministic rules and reports **facts** — "a
string is grown with `+=` inside a loop at line 45" — grouped under the root
causes each fact could indicate. Facts are graded by how far the fact alone
gets you:

| Grade | Meaning |
|---|---|
| `definite` | a smell in essentially any context — confirm and move on |
| `likely` | usually a smell; check the card's exceptions |
| `contextual` | a fact and nothing more. **Justify it against this specific code, or drop it.** |

Treat the output as a **second opinion**, and reconcile it against the list you
have already written:

- **it agrees with you** — you now have two independent reasons;
- **it saw something you did not** — go back and read that code again, then
  decide for yourself. Being pointed at a line is not being told it is wrong;
- **it flags something you judged fine** — you may well be right. Keep your
  judgement, and record why;
- **it is silent where you are suspicious** — that means nothing at all. These
  rules recognise shapes someone thought to describe in advance. Waste that
  does not take one of those shapes leaves no trace here however expensive it
  is. Keep your suspicion and carry it forward.

Add a `found_by` field to every suspicion: `"reading"`, `"rules"`, or
`"both"`. Record it honestly, including the cases where the rules saw something
you had missed.

Every shape these rules match is the right thing to write somewhere. Deciding
whether it is right *here* needs to know what the code is for, what the author
was constrained by, and how often it runs. You can read all three. The rules
cannot read any of them.
"""

# -- the arms ---------------------------------------------------------------

FULL = Arm(
    name="full",
    directory="energy-smells",
    question="Do the two evidence sources compose, or does one crowd out the other?",
    step_select=_SCANNER_SELECT,
    step_evidence=_SCANNER_EVIDENCE,
)

AST_ONLY = Arm(
    name="ast",
    directory="energy-smells-ast",
    question="What do the taxonomy-specific analyzers contribute on their own?",
    step_select=_SCANNER_SELECT,
    step_evidence=_SCANNER_EVIDENCE,
    excluded=("lib/analysis/linters.py",),
)

RUFF_ONLY = Arm(
    name="ruff",
    directory="energy-smells-ruff",
    question="How far does an off-the-shelf linter get, with the same cards and protocol?",
    step_select=_SCANNER_SELECT,
    step_evidence=_SCANNER_EVIDENCE,
    excluded=("lib/analysis/rules",),
)

KNOWLEDGE_ONLY = Arm(
    name="knowledge",
    directory="energy-smells-knowledge",
    question="How well does the agent do on the taxonomy alone?",
    step_select=_KNOWLEDGE_SELECT,
    step_evidence="",
    excluded=("scan.py", "lib/analysis", "lib/signals.py"),
)

CONTROL = Arm(
    name="control",
    directory="energy-efficiency",
    question="How much does a frontier model save with no taxonomy, given the "
             "same task, the same rigour and the same verifier?",
    templates="control",
    excluded=("scan.py", "lib/analysis", "lib/signals.py"),
    ships_taxonomy=False,
)

ARMS = (FULL, AST_ONLY, RUFF_ONLY, KNOWLEDGE_ONLY, CONTROL)
