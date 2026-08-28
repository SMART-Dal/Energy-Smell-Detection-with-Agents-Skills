"""Turns static evidence into the root causes worth considering.

This is the retrieval step, and it is a deterministic table lookup rather than
an embedding search.  That is deliberate.  The taxonomy is a closed hierarchy
of 77 nodes whose sibling root causes are near-identical in embedding space --
"Inefficient Nested Iteration" and "Suboptimal Algorithm Choice" are
semantically adjacent but operationally different, and cosine similarity over
their prose cannot separate them.  What *does* separate them is which analyzer
fired and what the repair would change, so routing keys off exactly that.

The table lives in `signals.json`, compiled from `catalog/*.yaml` by
`python -m build`.  Shipping it compiled keeps this side of the deliverable on
the standard library: no YAML parser, no spreadsheet reader, no install step.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from .analysis.models import Evidence, Strength

SIGNALS_PATH = Path(__file__).resolve().parent / "signals.json"

MAX_CANDIDATE_ROOT_CAUSES = 12
"""Cap on how many root causes are proposed for one unit.

Past roughly a dozen the shortlist stops being a shortlist and becomes the
whole taxonomy again, which reintroduces the label-prior problem that
progressive disclosure exists to avoid."""

_STRENGTH_WEIGHT = {
    Strength.DEFINITE: 4,
    Strength.LIKELY: 2,
    Strength.CONTEXTUAL: 1,
}


@dataclass(frozen=True)
class RootCause:
    """The little we need about a root cause to name it and point at its card."""

    id: str
    name: str
    category: str
    category_name: str
    measurability: str
    advisory_only: bool
    repair: str
    card: str
    impact: int = 1
    """Measured worth of the repair, 1..4, compiled from `validation/results/`.

    The lowest confirmed saving across this root cause's measured shapes, not
    the highest: every root cause has a shape whose loop body is nothing but the
    thing under test, and those read high while the same repair in a function
    that also does work reads a few percent. See `build/impact.py`."""


class SignalTable:
    """Evidence kind -> root causes, plus enough metadata to report them."""

    def __init__(self, payload: dict):
        self._by_signal: dict[str, list[str]] = payload["signal_to_root_causes"]
        self.root_causes = {
            rc_id: RootCause(id=rc_id, **fields)
            for rc_id, fields in payload["root_causes"].items()
        }
        self.categories = payload["categories"]

    def __contains__(self, root_cause_id: object) -> bool:
        return root_cause_id in self.root_causes

    def targets_of(self, evidence: Evidence) -> set[str]:
        """Root causes this one piece of evidence points at.

        An analyzer's own `suggests` is the primary route; the compiled table
        is the reverse mapping and catches anything the analyzer did not think
        to name.
        """
        candidates = set(evidence.suggests) | set(self._by_signal.get(evidence.kind, ()))
        return {rc for rc in candidates if rc in self.root_causes}


@lru_cache(maxsize=1)
def load_signals() -> SignalTable:
    if not SIGNALS_PATH.exists():
        raise FileNotFoundError(
            f"{SIGNALS_PATH} is missing -- run `python -m build` from the "
            f"project root to regenerate the skill."
        )
    return SignalTable(json.loads(SIGNALS_PATH.read_text()))


def rank_candidates(
    evidence: list[Evidence], table: SignalTable
) -> list[tuple[str, list[Evidence]]]:
    """Candidate root causes for one unit, best-supported first.

    Kept for callers that want the by-root-cause view -- the JSON report and
    anything asking "what could this unit be an instance of". The readable
    report groups the other way round; see `group_findings`.
    """
    by_root_cause: dict[str, list[Evidence]] = {}
    for item in evidence:
        for root_cause_id in table.targets_of(item):
            by_root_cause.setdefault(root_cause_id, []).append(item)

    ranked = sorted(
        by_root_cause,
        key=lambda rc: (_support(by_root_cause[rc]), len(by_root_cause[rc]), rc),
        reverse=True,
    )
    return [(rc, by_root_cause[rc]) for rc in ranked[:MAX_CANDIDATE_ROOT_CAUSES]]


def _support(evidence: list[Evidence]) -> int:
    """How strongly a body of evidence backs one candidate."""
    return sum(_STRENGTH_WEIGHT[item.strength] for item in evidence)


# -- ranking facts rather than labels --------------------------------------


@dataclass(frozen=True)
class Finding:
    """Every occurrence of one rule in one unit, as a single reportable item.

    A rule that fires thirteen times says one thing thirteen times; printed as
    thirteen entries it crowds out twelve other things the reader has not seen
    yet. The occurrences are collapsed here and the line numbers carried along,
    so nothing is lost and the report costs one entry.
    """

    kind: str
    source: str
    strength: Strength
    root_causes: tuple[str, ...]
    messages: tuple[tuple[str, tuple[int, ...]], ...]
    """Each distinct wording, with the lines that produced it."""

    corroborated_by: tuple[str, ...] = ()
    """Other rules that reported the same lines for the same root causes.

    Two analyzers agreeing is worth saying once, not printing twice: `ruff_B006`
    and `mutable_default_argument` are the same sentence about the same line."""

    @property
    def lines(self) -> tuple[int, ...]:
        return tuple(sorted({n for _, ns in self.messages for n in ns}))

    @property
    def count(self) -> int:
        return len(self.lines)


def impact_of(root_causes, table: SignalTable) -> int:
    """The weakest reading of an ambiguous fact.

    `nested_loops` points at both C7.S1, where the repair measured 100%, and
    C3.S4, where the least of its shapes measured 16%. Taking the lower one
    means an ambiguous fact ranks as what it is worth if it turns out to be the
    cheaper of the two -- the conservative direction, and the one that stops a
    single high-impact label from floating every fact that can reach it.
    """
    tiers = [table.root_causes[rc].impact for rc in root_causes if rc in table]
    return min(tiers) if tiers else 1


def score(strength: Strength, impact: int) -> int:
    """How far up the report one finding belongs.

    The product of two independent things, because neither alone orders the
    list correctly. Strength is how sure the rule is that the fact is real;
    impact is what the repair is worth if it is. Summing strength across
    occurrences -- the old ranking -- measured neither, and let thirteen
    contextual notes outrank one definite defect.
    """
    return _STRENGTH_WEIGHT[strength] * impact


def group_findings(evidence: list[Evidence], table: SignalTable) -> list[Finding]:
    """One entry per rule per unit, worth-ordered.

    Grouping is by rule rather than by root cause, which is what removes the
    duplication the by-root-cause view cannot avoid: a fact routing to two root
    causes was printed in full under both, and identical facts are printed once
    with their lines listed.
    """
    by_kind: dict[str, list[Evidence]] = {}
    for item in evidence:
        by_kind.setdefault(item.kind, []).append(item)

    findings = []
    for kind, items in by_kind.items():
        root_causes = sorted({rc for item in items for rc in table.targets_of(item)})
        wordings: dict[str, set[int]] = {}
        for item in items:
            wordings.setdefault(item.message, set()).add(item.lineno)
        findings.append(Finding(
            kind=kind,
            source=items[0].source,
            strength=min((item.strength for item in items), key=STRENGTH_RANK.get),
            root_causes=tuple(root_causes),
            messages=tuple(
                (message, tuple(sorted(lines)))
                for message, lines in sorted(wordings.items(), key=lambda kv: min(kv[1]))
            ),
        ))

    return sorted(_merge_agreeing(findings), key=lambda f: (
        -score(f.strength, impact_of(f.root_causes, table)),
        -_STRENGTH_WEIGHT[f.strength],
        -f.count,
        f.kind,
    ))


def _merge_agreeing(findings: list[Finding]) -> list[Finding]:
    """Collapse rules that said the same thing about the same lines.

    Two rules agree when they point at the same root causes and the same lines.
    That is corroboration, and corroboration reads as one stronger finding
    rather than as two -- the reader who sees `mutable_default_argument` at 522
    and then `ruff_B006` at 522 has to work out that they are one defect, and
    the second entry has displaced something they have not seen yet.

    The surviving wording is the strongest rule's, because the taxonomy's own
    rules explain the mechanism and a linter's message names its own check.
    """
    merged: dict[tuple, Finding] = {}
    for finding in sorted(findings, key=lambda f: STRENGTH_RANK[f.strength]):
        key = (finding.root_causes, finding.lines)
        if key not in merged:
            merged[key] = finding
            continue
        kept = merged[key]
        merged[key] = replace(
            kept, corroborated_by=kept.corroborated_by + (finding.kind,)
        )
    return list(merged.values())


STRENGTH_RANK = {Strength.DEFINITE: 0, Strength.LIKELY: 1, Strength.CONTEXTUAL: 2}
"""Strongest first. `min` over this picks the strongest claim a rule made."""


def budget(line_count: int) -> int:
    """How many findings one unit may show before the rest are named only.

    Three per ten lines, never fewer than five. A long unit has earned more
    attention than a short one, and a short one still deserves the handful it
    takes to cover it. This is a ceiling, not a target: after grouping, most
    units come in far under it.
    """
    return max(MIN_FINDINGS_SHOWN, PER_TEN_LINES * line_count // 10)


MIN_FINDINGS_SHOWN = 5
PER_TEN_LINES = 3
