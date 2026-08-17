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
from dataclasses import dataclass
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

    Ordering matters more than it looks: the reader works down the list, and
    putting weakly-supported candidates at the top invites accepting them.
    Rank by the strength of the evidence behind each candidate, then by how
    many separate signals agree.
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
