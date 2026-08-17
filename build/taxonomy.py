"""Loads the energy smell taxonomy from the published Excel files.

The taxonomy is a two-level tree: 12 categories (C1..C12), each with a handful
of root causes (C1.S1, C1.S2, ...), for 65 root causes in total.  Two flavours
ship with identical IDs and names but different prose:

    generic  -- language-agnostic (energy_smells_taxonomy.xlsx)
    python   -- Python-specific   (energy_smells_taxonomy_python_desc.xlsx)

Everything downstream refers to nodes by ID, so the flavour only affects the
text shown to the LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TAXONOMY_FILES = {
    "generic": PROJECT_ROOT / "taxonomy" / "energy_smells_taxonomy.xlsx",
    "python": PROJECT_ROOT / "taxonomy" / "energy_smells_taxonomy_python_desc.xlsx",
}

EXPECTED_CATEGORIES = 12
EXPECTED_ROOT_CAUSES = 65


@dataclass(frozen=True)
class Node:
    """A category or a root cause. Both levels share the same shape."""

    id: str
    name: str
    description: str
    example: str
    parent_id: str | None

    @property
    def is_category(self) -> bool:
        return self.parent_id is None

    def __str__(self) -> str:
        return f"{self.id} {self.name}"


class Taxonomy:
    """The loaded taxonomy, indexed by ID.

    Deliberately a plain object with a dict inside rather than anything clever:
    every lookup in the codebase is "give me the node with this ID".
    """

    def __init__(self, nodes: list[Node], flavour: str):
        self.flavour = flavour
        self._by_id = {n.id: n for n in nodes}
        self.categories = [n for n in nodes if n.is_category]
        self.root_causes = [n for n in nodes if not n.is_category]

    def __getitem__(self, node_id: str) -> Node:
        try:
            return self._by_id[node_id]
        except KeyError:
            raise KeyError(f"unknown taxonomy id: {node_id!r}") from None

    def __contains__(self, node_id: object) -> bool:
        return node_id in self._by_id

    def children_of(self, category_id: str) -> list[Node]:
        """Root causes belonging to a category, in taxonomy order."""
        return [n for n in self.root_causes if n.parent_id == category_id]

    def category_of(self, root_cause_id: str) -> Node:
        """The parent category of a root cause ("C7.S1" -> node C7)."""
        return self[root_cause_id.split(".")[0]]

    @property
    def root_cause_ids(self) -> list[str]:
        """All 65 IDs, in taxonomy order."""
        return [n.id for n in self.root_causes]

    @property
    def category_ids(self) -> list[str]:
        return [n.id for n in self.categories]

    def validate(self) -> None:
        """Fail loudly if the spreadsheet does not match the published paper."""
        problems = []
        if len(self.categories) != EXPECTED_CATEGORIES:
            problems.append(
                f"expected {EXPECTED_CATEGORIES} categories, found {len(self.categories)}"
            )
        if len(self.root_causes) != EXPECTED_ROOT_CAUSES:
            problems.append(
                f"expected {EXPECTED_ROOT_CAUSES} root causes, found {len(self.root_causes)}"
            )
        for node in self.root_causes:
            if node.parent_id not in self._by_id:
                problems.append(f"{node.id} has unknown parent {node.parent_id!r}")
            if not node.description.strip():
                problems.append(f"{node.id} has an empty description")
        if problems:
            raise ValueError("invalid taxonomy:\n  " + "\n  ".join(problems))


def _clean(value: object) -> str:
    """Excel empty cells arrive as NaN; normalise them to empty strings."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


@lru_cache(maxsize=None)
def load_taxonomy(flavour: str = "python") -> Taxonomy:
    """Load and validate a taxonomy flavour. Cached: the files never change."""
    if flavour not in TAXONOMY_FILES:
        raise ValueError(
            f"unknown flavour {flavour!r}, expected one of {sorted(TAXONOMY_FILES)}"
        )
    path = TAXONOMY_FILES[flavour]
    if not path.exists():
        raise FileNotFoundError(f"taxonomy file missing: {path}")

    frame = pd.read_excel(path)
    nodes = [
        Node(
            id=_clean(row["ID"]),
            name=_clean(row["Name"]),
            description=_clean(row["Description"]),
            example=_clean(row["Example"]),
            parent_id=_clean(row["Parent_ID"]) or None,
        )
        for _, row in frame.iterrows()
    ]
    taxonomy = Taxonomy(nodes, flavour)
    taxonomy.validate()
    return taxonomy
