"""Renders the taxonomy and catalog as progressive-disclosure knowledge cards.

Two card levels are generated here; the third (`SKILL.md`) is a template, since
it holds the protocol rather than per-node knowledge.

    level 0  SKILL.md          what am I doing, and which categories exist?
    level 1  categories/C7.md  is the smell anywhere in this category?
    level 2  root-causes/…     is it *this* one, and what exactly would fix it?

The point of the split is not saving tokens.  It is suppressing the label
prior: shown all sixty-five root causes at once, a model gravitates to whichever
labels feel most central, which is visible in the published LeetCode labelling
where C7.S1 alone took 27% of assignments and C11 took 0.07%.  Narrowing the
candidate set *before* the choice is made keeps the decision driven by the code
in front of it.

The one place all sixty-five appear together is `render_root_cause_index`, and
it is deliberately positioned late in the protocol -- the agent sweeps it only
after it has read the code and written its own account of what is wrong, so the
list is a check for omissions rather than a menu to choose from.

Cards are generated, never hand-edited, so `catalog/*.yaml` and the taxonomy
spreadsheet stay the single source of truth.
"""

from __future__ import annotations

from .catalog import Catalog
from .taxonomy import Taxonomy

CATEGORY_PATH = "reference/categories/{id}.md"
ROOT_CAUSE_PATH = "reference/root-causes/{id}.md"


# -- level 0 fragments -----------------------------------------------------


def render_category_index(taxonomy: Taxonomy, catalog: Catalog) -> str:
    """The twelve-line category table that `SKILL.md` embeds.

    Generated rather than typed into the template so that a change to the
    taxonomy cannot leave the entry point describing categories that moved.
    """
    lines = ["| ID | Category | Covers | Card |", "|---|---|---|---|"]
    for category in taxonomy.categories:
        count = len(taxonomy.children_of(category.id))
        lines.append(
            f"| **{category.id}** | {category.name} | {_one_line(category.description)} "
            f"| `{CATEGORY_PATH.format(id=category.id)}` ({count}) |"
        )
    return "\n".join(lines)


def render_root_cause_index(taxonomy: Taxonomy, catalog: Catalog) -> str:
    """All sixty-five root causes, one line each, grouped by category.

    This is the list the agent reads at the end of step 2, against code it has
    already formed a view about.  One line per root cause is the right width
    for that: enough to recognise something already noticed and dismissed as
    unnameable, not enough to decide anything from.
    """
    lines = []
    for category in taxonomy.categories:
        lines += [
            f"### {category.id} — {category.name}",
            "",
            "| ID | Name | Looks for |",
            "|---|---|---|",
        ]
        for node in taxonomy.children_of(category.id):
            entry = catalog.entries.get(node.id)
            looks_for = entry.in_one_line if entry else "—"
            lines.append(f"| **{node.id}** | {_cell(node.name)} | {_cell(looks_for)} |")
        lines.append("")
    return "\n".join(lines).rstrip()


# -- level 1 ---------------------------------------------------------------


def render_category(category_id: str, taxonomy: Taxonomy, catalog: Catalog) -> str:
    """What this category covers, and which root causes to consider inside it."""
    category = taxonomy[category_id]
    children = taxonomy.children_of(category_id)

    lines = [
        f"# {category.id} — {category.name}",
        "",
        f"*Level 1 card. {len(children)} root causes. "
        f"Open the level-2 card before accepting any of them.*",
        "",
        category.description,
        "",
        "## Root causes in this category",
        "",
        "| ID | Name | Looks for | The repair |",
        "|---|---|---|---|",
    ]
    for node in children:
        entry = catalog.entries.get(node.id)
        repair = entry.refactoring.summary if entry and entry.refactoring else "—"
        looks_for = entry.in_one_line if entry else "—"
        lines.append(
            f"| **{node.id}** | {_cell(node.name)} | {_cell(looks_for)} "
            f"| {_cell(repair)} |"
        )

    lines += [
        "",
        "Card paths: " + ", ".join(
            f"`{ROOT_CAUSE_PATH.format(id=node.id)}`" for node in children
        ),
        "",
        "## If nothing here fits",
        "",
        "Say so and move on. Reporting a weak match from a category you have "
        "already opened is the most common way this analysis goes wrong: the "
        "category is open because something drew you here, which is not the same "
        "as a smell being present.",
        "",
    ]
    return "\n".join(lines)


# -- level 2 ---------------------------------------------------------------


def render_root_cause(
    root_cause_id: str, taxonomy: Taxonomy, catalog: Catalog
) -> str:
    """The full working card: the reference, what to look for, and the measured repairs.

    Five parts: the reference's definition and example, what to look for, the
    measured repairs, near-misses, and similar root causes. How to read them --
    that the repairs are ideas rather than templates, what each result line
    asks for, that a near-miss means the repair would be wrong -- is said once,
    in SKILL.md's step 3, rather than on every card.
    """
    node = taxonomy[root_cause_id]
    entry = catalog[root_cause_id]
    category = taxonomy[entry.category_id]
    from .samples import decision, lookalike, measured, title_of   # reads the case files

    lines = [
        f"# {node.id} — {node.name}",
        "",
        f"*Level 2 card. Category [{category.id} {category.name}]"
        f"(../categories/{category.id}.md).*",
        "",
        "## Definition",
        "",
        node.description,
        "",
    ]
    if node.example:
        lines += ["## Example from the reference", "", node.example, ""]
    lines += ["## What to look for", "", _paragraphs(entry.look_for), ""]

    lines += ["## Repair", ""]
    if entry.refactoring and entry.refactoring.summary:
        lines += [entry.refactoring.summary[0].upper() + entry.refactoring.summary[1:]
                  .rstrip(".") + ".", ""]
    for position, sample in enumerate(entry.repairs, 1):
        result = measured(sample.case)
        lines += [
            f"### {position}. {title_of(sample.case)}",
            "",
            "Before:", "", "```python", result.before.rstrip(), "```", "",
            "After:", "", "```python", result.after.rstrip(), "```", "",
            decision(result), "",
        ]
        if sample.note:
            lines += [_paragraphs(sample.note), ""]

    if entry.not_this:
        lines += ["## Looks like it, but is not", ""]
        for item in entry.not_this:
            title, code, tempting = item.title, item.code, item.tempting
            if item.source.startswith("lookalike:"):
                title, code, tempting = lookalike(item.source[len("lookalike:"):])
            lines += [
                f"### {title}", "",
                "```python", code.rstrip(), "```", "",
                "The tempting repair:", "",
                "```python", tempting.rstrip(), "```", "",
                f"**Why not:** {_one_paragraph(item.why)}", "",
            ]

    if entry.similar:
        lines += ["## Similar root causes", ""]
        for neighbour_id in entry.similar:
            neighbour = taxonomy[neighbour_id]
            lines.append(f"- **[{neighbour.id} {neighbour.name}]"
                         f"(../root-causes/{neighbour.id}.md)** — "
                         f"{catalog[neighbour_id].in_one_line}")
        lines.append("")
    return "\n".join(lines)


# -- helpers ---------------------------------------------------------------


def _paragraphs(text: str) -> str:
    """Turn a folded scalar's paragraph breaks into markdown ones.

    YAML's `>` joins wrapped lines with a space and collapses a blank line to a
    single newline, which markdown then renders as the same paragraph. Every
    newline surviving into the loaded value was therefore a deliberate break in
    the source, and markdown wants two.
    """
    return "\n\n".join(part.strip() for part in text.split("\n") if part.strip())


def _one_paragraph(text: str) -> str:
    """A block scalar's lines joined into one paragraph."""
    return " ".join(text.split())


def _one_line(text: str) -> str:
    """First sentence of a description, for a table cell."""
    return _cell(text.split(". ")[0].strip().rstrip("."))


def _cell(text: str) -> str:
    """Escape text so a stray pipe or newline cannot break a markdown table."""
    return text.replace("|", "\\|").replace("\n", " ")
