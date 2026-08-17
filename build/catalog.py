"""The refactoring catalog: one canonical repair per root cause.

This is what makes the project's central rule executable:

    a finding is a repair, attributed to the one root cause that explains why
    the repair helps.

An entry therefore describes not just *what* a root cause is, but the specific
edit that removes it.  That single decision does a lot of work:

* the agent writes a bounded patch instead of rewriting a function;
* two root causes whose repairs are the same edit at the same patch shape are
  operationally the same finding, so taxonomy overlap gets measured rather than
  argued about;
* a root cause whose repair is too small to measure is declared as such up
  front, instead of being silently reported as unverifiable.

Repairs overlap, and the catalog does not pretend otherwise.  One edit routinely
makes several candidates disappear, because they only existed to serve the thing
that was fixed.  What the agent owes in that case is a record -- one finding,
and the absorbed candidates listed as subsumed -- not an artificially separated
count.

Two fields carry the most weight in practice.  `not_a_smell_when` records the
contexts where the pattern is present and correct, because a pattern firing is
not the same as a pattern being wrong.  `counter_examples` records the
near-misses: code that matches the shape exactly and is right as written, which
is what actually decides the hard cases.

This module is *build-time only*.  It reads `catalog/*.yaml`, validates it
against the taxonomy, and feeds the card renderer and the signal compiler.
Nothing that ships imports it.  See `CARD_SPEC.md` for how to write an entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path

import yaml

from .taxonomy import load_taxonomy

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


class PatchShape(str, Enum):
    """How large an edit the canonical repair is.

    This bounds what the repair *changes*.  It says nothing about how much code
    may be read while deciding, and nothing about where the waste is allowed to
    live -- a repair that has to move a computation between two methods of one
    class is `structural`, not forbidden.

    Its real job is comparison: two root causes whose repairs are the same edit
    at the same shape are operationally the same finding, which is how taxonomy
    overlap gets measured instead of argued about.
    """

    EXPRESSION = "expression"
    """Rewrite one expression in place."""

    STATEMENT_LOCAL = "statement_local"
    """Change a few adjacent statements, e.g. hoist one line out of a loop."""

    SIGNATURE = "signature"
    """Change the unit's signature or decorators."""

    STRUCTURAL = "structural"
    """Reorganise control flow or data structures.

    May span the methods of one class, or one call chain, as long as the
    behaviour seen at the entry point is unchanged.  Adding an index in
    `__init__` and reading it in a method is one structural repair, not two.
    """

    CROSS_UNIT = "cross_unit"
    """Requires editing call sites outside the code being repaired."""


class Measurability(str, Enum):
    """How large an effect the repair can be expected to produce.

    Some root causes are real but cost a single bytecode instruction, and no
    amount of repetition lifts them above measurement noise.  Declaring that
    here lets the tool report them honestly as advisory instead of pretending
    an unmeasurable effect was measured.
    """

    SCALES_WITH_INPUT = "scales_with_input"
    """Effect grows with data size: reliably measurable on a big enough driver."""

    SCALES_WITH_CALLS = "scales_with_calls"
    """Effect grows with call count: measurable if the unit is called enough."""

    CONSTANT_SMALL = "constant_small"
    """Fixed, tiny cost per execution: advisory only, do not expect to measure."""


@dataclass(frozen=True)
class Discriminator:
    """A neighbouring root cause that matches similar-looking code.

    Written in terms of what the *repair* changes, because that is the only
    reliable way to tell sibling root causes apart -- their prose descriptions
    overlap heavily, but their canonical repairs do not.

    These are rendered as an invitation to open the neighbour's card, not as an
    exclusion test.  The taxonomy overlaps; when two cards both fit, the useful
    question is which repair you would actually write, and either answer is
    better than forcing a distinction the code does not make.
    """

    against: str
    """The root cause ID being distinguished from."""

    rule: str
    """When to pick this one instead of that one."""


@dataclass(frozen=True)
class Example:
    """One before/after pair showing the repair on a concrete piece of code."""

    before: str
    after: str
    title: str = ""
    """What kind of case this is, e.g. "the shape is chosen three calls earlier"."""
    note: str = ""
    """What changed and why it costs less. One or two sentences."""


@dataclass(frozen=True)
class Refactoring:
    """The canonical repair for a root cause, with the examples that teach it.

    More than one example is normal.  A single minimal pair teaches the shape
    of the syntax and nothing about the judgement, and the judgement is the
    hard part: the same repair looks different when the waste is spread over
    three methods than when it sits in one expression.
    """

    summary: str
    examples: tuple[Example, ...] = ()

    @property
    def before(self) -> str:
        """The first example's `before`, for callers that want just one."""
        return self.examples[0].before if self.examples else ""

    @property
    def after(self) -> str:
        return self.examples[0].after if self.examples else ""


@dataclass(frozen=True)
class CounterExample:
    """Code that matches the pattern and is not a smell.

    A second positive example teaches nothing a first one did not. What decides
    a hard case is the near-miss: the snippet that looks identical and is
    correct as written, plus the one difference that makes it so.

    C10.S4 is why this field exists. Three examples of `s += x` inside a loop
    would all have been wrong, because the published claim was wrong. What
    separates the smell from the non-smell is one character of the assignment
    target -- `out +=` against `self.buf +=` -- and no amount of positive
    examples surfaces that.
    """

    code: str
    why: str
    """The single difference that makes this one fine."""


@dataclass(frozen=True)
class CatalogEntry:
    """Everything we know about how to recognise and repair one root cause."""

    id: str

    signals: tuple[str, ...] = ()
    """Evidence kinds from `scan.py` that suggest this root cause."""

    mechanism: str = ""
    """What the waste costs, and what the repair stops the machine doing.

    One short paragraph, in terms of work: what gets allocated, copied,
    dispatched or re-entered, and how that scales.  Without it a card teaches a
    pattern to match rather than a cost to reason about, and an agent that has
    only learned patterns cannot tell the smell from the near-miss.
    """

    how_to_tell: tuple[str, ...] = ()
    """Steps for deciding whether this root cause applies to a piece of code.

    Replaced an earlier `preconditions` field, which was a list of terse
    clauses presented as a gate.  Two things went wrong with that.  Clauses
    like "the container's construction site is editable" are not readable
    without already knowing the answer; and putting a short checklist under a
    heading that sounds definitive invited the card's actual description to be
    skipped.

    So these are full sentences that name what to look at in the code and what
    would settle it, they are meant to be read *after* the description rather
    than instead of it, and every one of them has to hold.
    """

    not_a_smell_when: tuple[str, ...] = ()
    """Contexts where the pattern is present but is the right thing to do."""

    refactoring: Refactoring | None = None
    counter_examples: tuple[CounterExample, ...] = ()
    """Code that matches the pattern and is nonetheless correct as written."""
    discriminators: tuple[Discriminator, ...] = ()
    patch_shape: PatchShape = PatchShape.STATEMENT_LOCAL
    measurability: Measurability = Measurability.SCALES_WITH_INPUT
    min_workload_hint: str = ""
    notes: str = ""

    @property
    def category_id(self) -> str:
        return self.id.split(".")[0]

    @property
    def is_advisory_only(self) -> bool:
        """Whether measurement can realistically confirm this root cause."""
        return self.measurability is Measurability.CONSTANT_SMALL


@dataclass
class Catalog:
    """All catalog entries, indexed by root cause ID."""

    entries: dict[str, CatalogEntry] = field(default_factory=dict)

    def __getitem__(self, root_cause_id: str) -> CatalogEntry:
        try:
            return self.entries[root_cause_id]
        except KeyError:
            raise KeyError(f"no catalog entry for {root_cause_id!r}") from None

    def __contains__(self, root_cause_id: object) -> bool:
        return root_cause_id in self.entries

    def signal_index(self) -> dict[str, list[str]]:
        """Evidence kind -> root cause IDs: the deterministic routing table.

        Derived from the entries rather than kept as a separate mapping, so a
        root cause and the signals that reach it can never drift apart.  This
        is what gets compiled into `skill/scripts/lib/signals.json`.
        """
        index: dict[str, list[str]] = {}
        for entry in self.entries.values():
            for signal in entry.signals:
                index.setdefault(signal, []).append(entry.id)
        return {signal: sorted(ids) for signal, ids in sorted(index.items())}


# -- loading ---------------------------------------------------------------


def _examples(block: dict) -> list[Example]:
    """Read a refactoring's examples, in either supported form.

    A top-level `before`/`after` pair is the one-example shorthand; the
    `examples:` list is what a root cause uses once one pair is not enough to
    show what the repair actually involves.
    """
    if "before" in block or "after" in block:
        return [
            Example(
                before=block.get("before", "").rstrip(),
                after=block.get("after", "").rstrip(),
                title=block.get("title", ""),
                note=block.get("note", "").strip(),
            )
        ]
    return [
        Example(
            before=item.get("before", "").rstrip(),
            after=item.get("after", "").rstrip(),
            title=item.get("title", "").strip(),
            note=item.get("note", "").strip(),
        )
        for item in block.get("examples", ())
    ]


def _entry_from_dict(raw: dict) -> CatalogEntry:
    refactoring = None
    if "refactoring" in raw:
        block = raw["refactoring"]
        refactoring = Refactoring(
            summary=block["summary"].strip(),
            examples=tuple(_examples(block)),
        )
    return CatalogEntry(
        id=raw["id"],
        signals=tuple(raw.get("signals", ())),
        mechanism=raw.get("mechanism", "").strip(),
        # YAML folded scalars keep a trailing newline, which renders as a blank
        # line between every bullet. These are prose items; strip them.
        how_to_tell=tuple(item.strip() for item in raw.get("how_to_tell", ())),
        not_a_smell_when=tuple(
            item.strip() for item in raw.get("not_a_smell_when", ())
        ),
        refactoring=refactoring,
        counter_examples=tuple(
            CounterExample(code=c["code"].rstrip(), why=c["why"].strip())
            for c in raw.get("counter_examples", ())
        ),
        discriminators=tuple(
            Discriminator(against=d["vs"], rule=d["rule"].strip())
            for d in raw.get("discriminators", ())
        ),
        patch_shape=PatchShape(raw.get("patch_shape", "statement_local")),
        measurability=Measurability(raw.get("measurability", "scales_with_input")),
        min_workload_hint=raw.get("min_workload_hint", ""),
        notes=raw.get("notes", ""),
    )


@lru_cache(maxsize=None)
def load_catalog(strict: bool = True) -> Catalog:
    """Load every catalog file and validate it against the taxonomy.

    With `strict`, a missing entry for any of the 65 root causes is an error.
    That check is the reason the catalog cannot quietly fall out of sync with
    the published taxonomy.
    """
    entries: dict[str, CatalogEntry] = {}
    for path in sorted(CATALOG_DIR.glob("*.yaml")):
        for raw in yaml.safe_load(path.read_text()) or []:
            entry = _entry_from_dict(raw)
            if entry.id in entries:
                raise ValueError(f"duplicate catalog entry for {entry.id}")
            entries[entry.id] = entry

    catalog = Catalog(entries=entries)
    _validate(catalog, strict=strict)
    return catalog


def _validate(catalog: Catalog, *, strict: bool) -> None:
    taxonomy = load_taxonomy("python")
    known = set(taxonomy.root_cause_ids)
    problems = []

    unknown = set(catalog.entries) - known
    if unknown:
        problems.append(f"catalog entries with no taxonomy node: {sorted(unknown)}")

    for entry in catalog.entries.values():
        for discriminator in entry.discriminators:
            if discriminator.against not in known:
                problems.append(
                    f"{entry.id} discriminates against unknown {discriminator.against}"
                )
        if entry.refactoring is None and not entry.is_advisory_only:
            problems.append(f"{entry.id} has no refactoring but is not advisory-only")

    if strict:
        missing = known - set(catalog.entries)
        if missing:
            problems.append(f"root causes with no catalog entry: {sorted(missing)}")

    if problems:
        raise ValueError("invalid catalog:\n  " + "\n  ".join(problems))
