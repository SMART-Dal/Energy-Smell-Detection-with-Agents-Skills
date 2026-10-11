"""The catalog: common patterns, and the measured repairs, per root cause.

This is what makes the project's central rule executable:

    a finding is a repair, attributed to a root cause whose definition the
    repair actually matches.

An entry is mostly references. Its repairs name case files under
`validation/taxonomy/`, whose code and measured results the card shows as they
are; its near-misses are lookalike specimens or a sourced example. What is
written by hand is short: the common patterns, a note under a sample when it has
something specific to say, and why each near-miss breaks under the repair.

This module is *build-time only*.  It reads `catalog/*.yaml`, validates it
against the taxonomy and the case files, and feeds the card renderer and the
signal compiler. Nothing that ships imports it.  See `CARD_SPEC.md` for how to
write an entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

import yaml

from .taxonomy import load_taxonomy

CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


@dataclass(frozen=True)
class Refactoring:
    """The canonical repair for a root cause, in one line.

    Shown at the top of the card's repair section and in the category table;
    the measured samples below it show what the repair looks like in code.
    """

    summary: str


@dataclass(frozen=True)
class RepairSample:
    """A measured sample shown as a repair.

    Only the note is authored. The code and the title come from the case file,
    and the verdict from the latest results -- see `samples.py`.
    """

    case: str
    """Stem of the case file under `validation/taxonomy/`."""
    note: str = ""
    """Carried over from the old card's example note; trimmed, never invented."""


@dataclass(frozen=True)
class NotThis:
    """Code that matches the pattern, the repair it invites, and why that is wrong."""

    title: str
    code: str
    tempting: str
    why: str
    source: str
    """Where it comes from, so it can be checked: `lookalike:<stem>` (a
    specimen under `validation/lookalikes/`, whose code, repair and title are
    read from the file), `catalog` (the `not_a_smell_when` or `counter_examples`
    of the card before the October 2026 rewrite, in git history),
    `rule:<rule>/<function>` (a negative in that rule's
    test fixtures), or `known` (documented Python behaviour, which `why`
    names)."""


@dataclass(frozen=True)
class CatalogEntry:
    """Everything we know about how to recognise and repair one root cause."""

    id: str

    in_one_line: str = ""
    """What this root cause hunts for, in a single clause.

    Written once and reused in three places: the category card's table, the
    full index the agent sweeps at step 2e, and every *other* card that lists
    this one as similar.  Writing it once is what keeps those three consistent;
    it also means a card describes its neighbours in the neighbours' own words
    rather than in its own.
    """

    signals: tuple[str, ...] = ()
    """Evidence kinds from `scan.py` that suggest this root cause."""

    look_for: str = ""
    """Common patterns: three or four lines summarising the measured samples.

    Written from the samples and the rule fixtures, in the card's own terms,
    and only about what the root cause is -- what it is not lives in
    `not_this`. It says what the waste looks like and what the machine does
    that it need not; the concrete shapes are the repairs below it, which read
    as illustrations rather than as a list of the permitted cases.
    """

    refactoring: Refactoring | None = None

    similar: tuple[str, ...] = ()
    """Root causes worth opening when this card does not quite fit.

    Not a discrimination test.  An earlier version of this field carried a rule
    per neighbour explaining how to tell the two apart, which was a lot of prose
    defending a distinction the project does not need: two agents that repair
    the same waste and attribute it to two overlapping root causes have both
    done the job, provided each repair matches the definition it was filed
    under.  What the reader actually needs is a way out of a card that nearly
    fits, so the list is bare IDs and the renderer fills in each target's own
    `in_one_line`.

    The relation is symmetric -- `load_catalog` mirrors every edge -- because a
    neighbour reachable in one direction only is a dead end for whichever
    reader arrives from the wrong side.
    """

    repairs: tuple[RepairSample, ...] = ()
    """Every measured sample that repairs this root cause, in the order shown."""

    not_this: tuple[NotThis, ...] = ()
    """Up to five near-misses: the pattern is there and the repair would be wrong."""

    excluded: tuple[tuple[str, str], ...] = ()
    """(case stem, reason): samples filed under this root cause that repair another one."""

    @property
    def category_id(self) -> str:
        return self.id.split(".")[0]


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

ENTRY_KEYS = {
    "id", "in_one_line", "signals", "look_for", "refactoring", "repairs",
    "excluded", "not_this", "similar",
}
"""Every key an entry may carry.

Checked rather than ignored, because a misspelled key used to vanish silently
and take a whole section of a card with it. The old card's keys --
`what_to_look_for`, `not_a_smell_when`, `counter_examples`, `notes`,
`refactoring.examples`, `patch_shape`, `measurability`, `min_workload_hint` --
are errors too, so none of them can come back by accident.
"""


def _entry_from_dict(raw: dict) -> CatalogEntry:
    unknown = set(raw) - ENTRY_KEYS
    if unknown:
        raise ValueError(
            f"{raw.get('id', '<no id>')} has unknown catalog keys: "
            f"{sorted(unknown)} -- see CARD_SPEC.md"
        )

    refactoring = None
    if "refactoring" in raw:
        unknown = set(raw["refactoring"]) - {"summary"}
        if unknown:
            raise ValueError(f"{raw['id']} refactoring has unknown keys: {sorted(unknown)}")
        refactoring = Refactoring(summary=raw["refactoring"]["summary"].strip())
    return CatalogEntry(
        id=raw["id"],
        in_one_line=raw.get("in_one_line", "").strip(),
        signals=tuple(raw.get("signals", ())),
        look_for=raw.get("look_for", "").strip(),
        refactoring=refactoring,
        similar=tuple(raw.get("similar", ())),
        repairs=tuple(
            RepairSample(case=r["case"], note=(r.get("note") or "").strip())
            for r in raw.get("repairs", ())
        ),
        not_this=tuple(
            NotThis(title=n.get("title", "").strip(), code=n.get("code", "").rstrip(),
                    tempting=n.get("tempting", "").rstrip(), why=n["why"].strip(),
                    source=n.get("source", "").strip())
            for n in raw.get("not_this", ())
        ),
        excluded=tuple((x["case"], x["reason"].strip()) for x in raw.get("excluded", ())),
    )


def _mirrored(entries: dict[str, CatalogEntry]) -> dict[str, CatalogEntry]:
    """Make `similar` symmetric: if A points at B, B points back at A.

    Written one way round in the YAML and completed here, so that adding an
    edge is one line of authoring rather than two that can drift apart.  The
    reader who arrives at B from an unrelated direction gets the same way out
    as the reader who arrives from A.
    """
    neighbours = {entry_id: set(entry.similar) for entry_id, entry in entries.items()}
    for entry_id, targets in list(neighbours.items()):
        for target in targets:
            neighbours.setdefault(target, set()).add(entry_id)
    return {
        entry_id: replace(entry, similar=tuple(sorted(neighbours[entry_id])))
        for entry_id, entry in entries.items()
    }


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

    catalog = Catalog(entries=_mirrored(entries))
    _validate(catalog, strict=strict)
    return catalog


MAX_NOT_THIS = 5


def _card_problems(entry: CatalogEntry) -> list[str]:
    """What is missing or unverifiable in one entry's card."""
    from .samples import case_files, lookalike, measured, rule_negative   # reads the case files

    problems = []
    if not entry.look_for:
        problems.append(f"{entry.id} has no `look_for`")
    if not entry.repairs:
        problems.append(f"{entry.id} shows no measured repair")

    # Every sample filed under this root cause is shown or excluded with a
    # reason; none disappears because nobody listed it.
    shown = [sample.case for sample in entry.repairs]
    dropped = [case for case, _ in entry.excluded]
    listed = shown + dropped
    duplicates = sorted({case for case in listed if listed.count(case) > 1})
    if duplicates:
        problems.append(f"{entry.id} lists these samples twice: {duplicates}")
    missing = sorted(set(case_files(entry.id)) - set(listed))
    stray = sorted(set(listed) - set(case_files(entry.id)))
    if missing:
        problems.append(f"{entry.id} neither shows nor excludes: {missing}")
    if stray:
        problems.append(f"{entry.id} lists samples that are not its case files: {stray}")
    for case in shown:
        try:
            measured(case)
        except (FileNotFoundError, KeyError, SyntaxError) as exc:
            problems.append(f"{entry.id} repair {case}: {exc}")

    if len(entry.not_this) > MAX_NOT_THIS:
        problems.append(f"{entry.id} has {len(entry.not_this)} `not_this` entries; "
                        f"at most {MAX_NOT_THIS}")
    for item in entry.not_this:
        source = item.source
        if source.startswith("lookalike:"):
            try:
                lookalike(source[len("lookalike:"):])
            except (FileNotFoundError, KeyError, SyntaxError) as exc:
                problems.append(f"{entry.id} near-miss {source}: {exc}")
            if item.code or item.tempting or item.title:
                problems.append(f"{entry.id} near-miss {source}: title, code and "
                                f"tempting come from the file; do not write them")
            continue
        if not (item.title and item.code and item.tempting):
            problems.append(f"{entry.id} near-miss {item.title or source!r} needs "
                            f"title, code and tempting")
        if source in ("catalog", "known"):
            continue
        if source.startswith("rule:"):
            problem = rule_negative(source[len("rule:"):])
            if problem:
                problems.append(f"{entry.id} near-miss {item.title!r}: {problem}")
            continue
        problems.append(f"{entry.id} near-miss {item.title!r} has source {source!r}; "
                        f"expected lookalike:<stem>, catalog, known, or rule:<rule>/<function>")
    return problems


MAX_SIMILAR = 5
"""How many `similar` entries one card may end up with after mirroring.

A cross-reference list is for getting the reader to the two or three cards they
might have wanted instead; past five it stops ranking anything and becomes a
second table of contents.
"""


def _validate(catalog: Catalog, *, strict: bool) -> None:
    taxonomy = load_taxonomy("python")
    known = set(taxonomy.root_cause_ids)
    problems = []

    unknown = set(catalog.entries) - known
    if unknown:
        problems.append(f"catalog entries with no taxonomy node: {sorted(unknown)}")

    for entry in catalog.entries.values():
        if not entry.in_one_line:
            problems.append(f"{entry.id} has no in_one_line")
        if entry.id in entry.similar:
            problems.append(f"{entry.id} lists itself as similar")
        if len(entry.similar) > MAX_SIMILAR:
            # Checked after `_mirrored`, which is the only place this can be
            # exceeded without anyone noticing: the YAML shows a card's
            # hand-written half, and the back-links completed from other cards
            # do not appear next to it. Thirteen cards once rendered with more
            # than five neighbours that way, one with nine, none of which was
            # visible in the file anyone would have looked at.
            problems.append(
                f"{entry.id} has {len(entry.similar)} similar entries, over the "
                f"cap of {MAX_SIMILAR}: {list(entry.similar)}. Some of them are "
                f"back-links from cards that name it; drop the weakest edge at "
                f"whichever end it is written."
            )
        for target in entry.similar:
            if target not in known:
                problems.append(f"{entry.id} points at unknown root cause {target}")
        if entry.refactoring is None:
            problems.append(f"{entry.id} has no refactoring: every root cause needs a repair to measure")
        problems.extend(_card_problems(entry))

    if strict:
        missing = known - set(catalog.entries)
        if missing:
            problems.append(f"root causes with no catalog entry: {sorted(missing)}")

    if problems:
        raise ValueError("invalid catalog:\n  " + "\n  ".join(problems))
