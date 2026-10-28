"""Regenerate the shipped skills from the taxonomy and the catalog.

    python -m build            write dist/
    python -m build --check    fail if dist/ is out of date, write nothing

`--check` exists so a deliverable cannot silently drift from its sources: run
it before shipping, and a card edited by hand shows up as a diff.

One directory per arm (see `arms.py`), each self-contained:

    <arm>/SKILL.md                              from templates/<tree>/
    <arm>/reference/categories/C1.md … C12.md   level-1 cards
    <arm>/reference/root-causes/C1.S1.md … …    level-2 cards  (65)
    <arm>/scripts/…                             src/, minus what the arm withholds
    <arm>/scripts/lib/signals.json              evidence kind -> root cause

Nothing an arm withholds may be inferable from what it ships. The build is the
place that has to hold that line, since it is the only code that knows the arms
exist -- so there is no manifest, no condition file, and no generated comment
naming what was left out.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .arms import ARMS, Arm
from .cards import (
    render_category,
    render_category_index,
    render_root_cause,
    render_root_cause_index,
)
from .catalog import Catalog, load_catalog
from .taxonomy import Taxonomy, load_taxonomy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
SOURCE_SCRIPTS = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"

TOKENS = {
    "{{CATEGORY_INDEX}}": lambda arm, rendered: rendered["categories"],
    "{{ROOT_CAUSE_INDEX}}": lambda arm, rendered: rendered["root_causes"],
    "{{STEP_EVIDENCE}}": lambda arm, rendered: arm.step_evidence,
}
"""Placeholders substituted into templates, and what fills each one.

Two kinds. `{{CATEGORY_INDEX}}` and `{{ROOT_CAUSE_INDEX}}` are the taxonomy
rendered as tables, identical in every arm that ships it. `{{STEP_EVIDENCE}}`
is the part of the protocol that differs by arm -- the rules, in step 1 --
which is the whole experiment, so it lives on the arm rather than in the
template.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m build", description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report files that would change, without writing them",
    )
    args = parser.parse_args(argv)

    taxonomy = load_taxonomy("python")
    catalog = load_catalog()

    per_arm = {arm: _render_arm(arm, taxonomy, catalog) for arm in ARMS}
    outputs: dict[Path, str] = {}
    for files in per_arm.values():
        outputs.update(files)

    stale = [path for path, text in outputs.items() if _differs(path, text)]
    orphans = [
        path
        for arm, files in per_arm.items()
        for path in _orphans(DIST_DIR / arm.directory, set(files))
    ]

    if args.check:
        if stale or orphans:
            for path in sorted(stale):
                print(f"  out of date: {path.relative_to(PROJECT_ROOT)}")
            for path in sorted(orphans):
                print(f"  should not exist: {path.relative_to(PROJECT_ROOT)}")
            return 1
        print(f"dist/ is up to date ({len(outputs)} files across {len(ARMS)} arms).")
        return 0

    for arm, files in per_arm.items():
        _prune(DIST_DIR / arm.directory, set(files))
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    _report(taxonomy, catalog, written=len(outputs), changed=len(stale))
    return 0


def _render_arm(arm: Arm, taxonomy: Taxonomy, catalog: Catalog) -> dict[Path, str]:
    """Every file of one arm's skill directory, as path -> contents.

    The cards and the verifier are identical in every arm that ships them: only
    the template words, the rules part of step 1 and the set of shipped
    analyzers change, which is what makes a difference between two arms
    attributable to the evidence rather than to the instructions.
    """
    root = DIST_DIR / arm.directory
    files: dict[Path, str] = {}

    if arm.ships_taxonomy:
        for category in taxonomy.categories:
            files[root / "reference" / "categories" / f"{category.id}.md"] = (
                render_category(category.id, taxonomy, catalog)
            )
        for node in taxonomy.root_causes:
            files[root / "reference" / "root-causes" / f"{node.id}.md"] = (
                render_root_cause(node.id, taxonomy, catalog)
            )

    rendered = {
        "categories": render_category_index(taxonomy, catalog),
        "root_causes": render_root_cause_index(taxonomy, catalog),
    }
    template_root = TEMPLATE_DIR / arm.templates
    for source in sorted(template_root.rglob("*.md")):
        relative = source.relative_to(template_root)
        if relative.as_posix() in arm.omit_templates:
            continue
        text = source.read_text()
        # The arm's words go in first: one of them carries the category
        # section, which itself contains a token filled in the pass below.
        for word, fill in arm.words.items():
            text = text.replace("{{" + word + "}}", fill)
        for token, fill in TOKENS.items():
            text = text.replace(token, fill(arm, rendered))
        _assert_filled(arm, relative, text)
        files[root / relative] = text

    for source in sorted(SOURCE_SCRIPTS.rglob("*.py")):
        relative = source.relative_to(SOURCE_SCRIPTS)
        if _excluded(relative, arm):
            continue
        files[root / "scripts" / relative] = _withhold_blocks(source.read_text(), arm, relative)

    if arm.ships_scanner:
        files[root / "scripts" / "lib" / "signals.json"] = _render_signals(taxonomy, catalog)
    if not arm.ships_taxonomy:
        _assert_no_taxonomy(arm, files)
    return files


WITHHELD_BEGIN = "# <taxonomy>"
WITHHELD_END = "# </taxonomy>"


def _withhold_blocks(text: str, arm: Arm, relative: Path) -> str:
    """A shared script as this arm ships it.

    Lines between `# <taxonomy>` and `# </taxonomy>` are code only an arm with
    the taxonomy runs, such as a submission's `root_cause` key. They are dropped
    from an arm without it. The marker lines are dropped from every arm, so no
    shipped file shows that a block was there.
    """
    kept, inside = [], False
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        mark = line.strip()
        if mark in (WITHHELD_BEGIN, WITHHELD_END):
            if (mark == WITHHELD_BEGIN) == inside:
                raise SystemExit(f"{relative}:{number}: unbalanced `{mark}`")
            inside = mark == WITHHELD_BEGIN
            continue
        if inside and not arm.ships_taxonomy:
            continue
        kept.append(line)
    if inside:
        raise SystemExit(f"{relative}: `{WITHHELD_BEGIN}` is never closed")
    return "".join(kept)


TAXONOMY_TRACE = re.compile(
    r"\bC\d{1,2}\.S\d{1,2}\b|root[ _-]?causes?|taxonom|\bsmells?\b|\bcards?\b", re.IGNORECASE)
"""A word an arm without the taxonomy must not ship: a root-cause ID, the words
for the taxonomy and its cards, or "smell"."""


def _assert_no_taxonomy(arm: Arm, files: dict[Path, str]) -> None:
    """An arm without the taxonomy ships no trace of it.

    On Oct 27 an Unguided agent read `lib/submission.py` and found the
    `root_cause` key, an example ID and the word "taxonomy" in a comment. The
    build checks every file of such an arm, so a comment added later cannot do
    the same.
    """
    found = [
        f"{path.relative_to(DIST_DIR)}:{number}: {line.strip()[:100]}"
        for path, text in files.items()
        for number, line in enumerate(text.splitlines(), 1)
        if TAXONOMY_TRACE.search(line)
    ]
    if found:
        raise SystemExit(f"{arm.name} would ship taxonomy words:\n  " + "\n  ".join(found))


def _assert_filled(arm: Arm, relative: Path, text: str) -> None:
    """No `{{TOKEN}}` may survive into a shipped file.

    A slot left unfilled would ship as literal braces in one arm and as prose
    in another, which is exactly the kind of difference the arms must not have.
    """
    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))
    if leftover:
        raise SystemExit(
            f"{arm.name}: {relative} still contains {', '.join(leftover)}"
        )


def _excluded(relative: Path, arm: Arm) -> bool:
    """Whether this source file is withheld from the arm.

    Matching is by path prefix so an entry like `lib/analysis` withholds the
    whole package. Withholding matters as much as disabling: an agent that can
    read `rules/loops.py` has the pattern list even with the scanner turned off.
    """
    text = relative.as_posix()
    return any(text == item or text.startswith(item + "/") for item in arm.excluded)


IGNORED_IN_DIST = {"__pycache__"}
"""Directories that appear in an arm by running it, not by building it."""


def _generated(path: Path) -> bool:
    """Whether this file is ours to account for, rather than a run artefact."""
    return not any(part in IGNORED_IN_DIST for part in path.parts)


def _prune(root: Path, keep: set[Path]) -> None:
    """Delete everything in an arm that this build did not generate.

    Whitelist rather than blacklist, because the failure this guards against is
    a withheld file surviving from an earlier build -- and a blacklist only
    catches the exclusions somebody remembered to write down.
    """
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file() and path not in keep and _generated(path):
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def _render_signals(taxonomy: Taxonomy, catalog: Catalog) -> str:
    """Compile the routing table `scan.py` needs, so it can stay YAML-free.

    Everything here is derived; editing `signals.json` by hand is pointless
    because the next build overwrites it.
    """
    payload = {
        "_generated_by": "python -m build",
        "_source": "catalog/*.yaml + taxonomy/*.xlsx",
        "signal_to_root_causes": catalog.signal_index(),
        "root_causes": {
            node.id: {
                "name": node.name,
                "category": entry.category_id,
                "category_name": taxonomy[entry.category_id].name,
                "repair": entry.refactoring.summary if entry.refactoring else "",
                "card": f"reference/root-causes/{node.id}.md",
            }
            for node in taxonomy.root_causes
            if (entry := catalog.entries.get(node.id)) is not None
        },
        "categories": {
            category.id: {
                "name": category.name,
                "card": f"reference/categories/{category.id}.md",
            }
            for category in taxonomy.categories
        },
    }
    return json.dumps(payload, indent=1, sort_keys=False) + "\n"


def _orphans(root: Path, keep: set[Path]) -> list[Path]:
    """Files present in an arm that this build would not write."""
    if not root.exists():
        return []
    return [
        p for p in root.rglob("*")
        if p.is_file() and p not in keep and _generated(p)
    ]


def _differs(path: Path, text: str) -> bool:
    return not path.exists() or path.read_text() != text


def _report(taxonomy: Taxonomy, catalog: Catalog, *, written: int, changed: int) -> None:
    entries = catalog.entries.values()
    # `similar` is symmetric, so every edge is counted from both ends.
    edges = sum(len(e.similar) for e in entries) // 2
    repairs = sum(len(e.repairs) for e in entries)
    excluded = sum(len(e.excluded) for e in entries)
    near_misses = sum(len(e.not_this) for e in entries)
    signals = catalog.signal_index()

    routed = {rc for ids in signals.values() for rc in ids}
    print(f"wrote {written} files to dist/ ({changed} changed)")
    print(f"  {len(taxonomy.categories)} categories, "
          f"{len(taxonomy.root_causes)} root causes")
    print(f"  {repairs} measured repairs shown ({excluded} excluded), "
          f"{near_misses} near-misses, {edges} similarity edges")
    print(f"  {len(signals)} static signals routing to {len(routed)} root causes "
          f"({len(taxonomy.root_causes) - len(routed)} have none)")
    print("  arms:")
    for arm in ARMS:
        withheld = ", ".join(arm.excluded) if arm.excluded else "nothing"
        taxonomy_note = "" if arm.ships_taxonomy else ", no taxonomy"
        print(f"    dist/{arm.directory:<34} withholds {withheld}{taxonomy_note}")


if __name__ == "__main__":
    sys.exit(main())
