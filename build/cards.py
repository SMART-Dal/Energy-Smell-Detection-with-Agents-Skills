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

from .catalog import Catalog, CatalogEntry
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
        "| ID | Name | Looks for | The repair | Measurable? |",
        "|---|---|---|---|---|",
    ]
    for node in children:
        entry = catalog.entries.get(node.id)
        repair = entry.refactoring.summary if entry and entry.refactoring else "—"
        looks_for = entry.in_one_line if entry else "—"
        lines.append(
            f"| **{node.id}** | {_cell(node.name)} | {_cell(looks_for)} "
            f"| {_cell(repair)} | {_measurability_flag(entry)} |"
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
    """The full working card: everything needed to accept, reject and repair."""
    node = taxonomy[root_cause_id]
    entry = catalog[root_cause_id]
    category = taxonomy[entry.category_id]

    lines = [
        f"# {node.id} — {node.name}",
        "",
        f"*Level 2 card. Category [{category.id} {category.name}]"
        f"(../categories/{category.id}.md).*",
        "",
        node.description,
        "",
    ]

    if node.example:
        lines += ["## Example from the taxonomy", "", node.example, ""]

    if entry.what_to_look_for:
        lines += ["## What to look for", "", entry.what_to_look_for, ""]

    if entry.not_a_smell_when:
        lines += [
            "## NOT a smell when",
            "",
            "The pattern is present and is the right call. If one of these holds, "
            "reject and record which.",
            "",
            *[f"- {item}" for item in entry.not_a_smell_when],
            "",
        ]

    if entry.counter_examples:
        lines += [
            "## Looks the same, is not",
            "",
            "Each of these matches the pattern and is correct as written. If the "
            "code you are judging is one of them, reject it.",
            "",
        ]
        for example in entry.counter_examples:
            lines += [
                "```python",
                example.code,
                "```",
                "",
                f"**Not a smell:** {example.why}",
                "",
            ]

    if entry.refactoring:
        lines += ["## The repair", "", entry.refactoring.summary, ""]
        examples = entry.refactoring.examples
        for position, example in enumerate(examples, start=1):
            if example.title:
                heading = (
                    f"### {example.title}" if len(examples) > 1
                    else f"**{example.title}**"
                )
                lines += [heading, ""]
            elif len(examples) > 1:
                lines += [f"### Example {position}", ""]
            lines += [
                "Before:", "", "```python", example.before, "```", "",
                "After:", "", "```python", example.after, "```", "",
            ]
            if example.note:
                lines += [example.note, ""]
        lines += [
            f"**Patch shape: `{entry.patch_shape.value}`** — "
            f"{_patch_shape_note(entry)}",
            "",
            "The examples are illustrations, not the permitted cases; the repair "
            "you write will not look like any of them.",
            "",
        ]

    if entry.similar:
        lines += [
            "## Similar root causes",
            "",
            "Open these when this card nearly fits and you cannot write a repair "
            "from it. Overlap is expected; if two both describe what you "
            "repaired, file it under either and say so.",
            "",
        ]
        for neighbour_id in entry.similar:
            neighbour = taxonomy[neighbour_id]
            summary = catalog[neighbour_id].in_one_line
            lines += [
                f"- **[{neighbour.id} {neighbour.name}]"
                f"(../root-causes/{neighbour.id}.md)** — {summary}",
            ]
        lines.append("")

    lines += ["## Verifying it", "", _verification_note(entry), ""]
    if entry.min_workload_hint:
        lines += [f"Workload hint: {entry.min_workload_hint}", ""]

    if entry.notes:
        lines += ["## Notes", "", entry.notes, ""]

    lines += [
        "## Before you accept this",
        "",
        "1. Say what the machine does here that it need not do, in your own words.",
        "2. Apply `NOT a smell when` and `Looks the same, is not`.",
        "3. Write the repair for *this* code.",
        "4. Check it removes what *this* root cause names, not something adjacent.",
        "5. Say how often the code runs and how large its inputs get.",
        "",
        "Record which one decided it, whichever way it went.",
        "",
    ]
    return "\n".join(lines)


# -- helpers ---------------------------------------------------------------


def _verification_note(entry: CatalogEntry) -> str:
    if entry.is_advisory_only:
        return (
            "**Advisory only.** The repair costs a fixed and very small amount "
            "per execution — typically a single bytecode instruction — so no "
            "workload size will lift it above a realistic noise floor. Report a "
            "genuine instance as `advisory`; do not build a case file for it, "
            "and never claim it was measured."
        )
    if entry.measurability.value == "scales_with_calls":
        return (
            "The effect grows with the number of **calls**, not with input size. "
            "The case file's largest case must therefore call the unit many "
            "times over a small input, rather than call it once over a large one."
        )
    return (
        "The effect grows with **input size**, so it is measurable given a large "
        "enough case. Make the largest case big enough that one call takes "
        "milliseconds, not microseconds."
    )


def _patch_shape_note(entry: CatalogEntry) -> str:
    return {
        "expression": "rewrite one expression in place and change nothing else.",
        "statement_local": "change a few adjacent statements and nothing else.",
        "signature": "change the signature or decorators; leave the body alone.",
        "structural": "reorganise control flow or data structures. This may span "
                      "the methods of one class or one call chain — adding an "
                      "index in one place and reading it in another is a single "
                      "repair — as long as behaviour at the entry point is "
                      "unchanged.",
        "cross_unit": "this one has to change call sites outside the code being "
                      "repaired, which makes it harder to attribute — name every "
                      "place you edited.",
    }[entry.patch_shape.value]


def _measurability_flag(entry: CatalogEntry | None) -> str:
    if entry is None:
        return "—"
    return {
        "scales_with_input": "yes, scales with input",
        "scales_with_calls": "yes, scales with call count",
        "constant_small": "**no — advisory only**",
    }[entry.measurability.value]


def _one_line(text: str) -> str:
    """First sentence of a description, for a table cell."""
    return _cell(text.split(". ")[0].strip().rstrip("."))


def _cell(text: str) -> str:
    """Escape text so a stray pipe or newline cannot break a markdown table."""
    return text.replace("|", "\\|").replace("\n", " ")
