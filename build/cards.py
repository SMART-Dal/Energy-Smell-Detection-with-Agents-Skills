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

Cards are generated, never hand-edited, so `catalog/*.yaml` and the taxonomy
spreadsheet stay the single source of truth.
"""

from __future__ import annotations

from .catalog import Catalog, CatalogEntry
from .taxonomy import Taxonomy

CATEGORY_PATH = "reference/categories/{id}.md"
ROOT_CAUSE_PATH = "reference/root-causes/{id}.md"


# -- level 0 fragment ------------------------------------------------------


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
        "| ID | Name | The repair | Measurable? |",
        "|---|---|---|---|",
    ]
    for node in children:
        entry = catalog.entries.get(node.id)
        repair = entry.refactoring.summary if entry and entry.refactoring else "—"
        lines.append(
            f"| **{node.id}** | {_cell(node.name)} | {_cell(repair)} "
            f"| {_measurability_flag(entry)} |"
        )

    lines += [
        "",
        "Card paths: " + ", ".join(
            f"`{ROOT_CAUSE_PATH.format(id=node.id)}`" for node in children
        ),
        "",
    ]

    cross = _cross_category_discriminators(category_id, catalog, taxonomy)
    if cross:
        lines += [
            "## Telling this category from its neighbours",
            "",
            "These come up often enough to check before you commit:",
            "",
            *cross,
            "",
        ]

    lines += [
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

    if entry.mechanism:
        lines += ["## Where the energy goes", "", entry.mechanism, ""]

    if entry.how_to_tell:
        lines += [
            "## How to tell",
            "",
            "The description above says what this root cause *is*. This says how "
            "to decide whether a particular piece of code has it. Work through "
            "the steps in order; every one has to hold, and you should be able "
            "to point at the code that settles each.",
            "",
            *[f"{n}. {item}" for n, item in enumerate(entry.how_to_tell, start=1)],
            "",
            "If a step cannot be answered from the code in front of you, that is "
            "an answer: read further out until it can be, or reject the "
            "candidate and say which step you could not settle.",
            "",
        ]

    if entry.not_a_smell_when:
        lines += [
            "## NOT a smell when",
            "",
            "The pattern is present but is the right call. If any of these hold, "
            "reject the candidate and record which clause applied.",
            "",
            *[f"- {item}" for item in entry.not_a_smell_when],
            "",
        ]

    if entry.counter_examples:
        lines += [
            "## Looks the same, is not",
            "",
            "Each of these matches the pattern and is correct as written. Compare "
            "the code you are judging against them before accepting the candidate: "
            "if it is one of these, reject it.",
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
            "That bounds what the repair *changes*. It does not bound how much "
            "code you may read to decide, and it does not mean the waste has to "
            "live in one place. A patch that rewrites everything cannot be "
            "attributed to any one root cause, which is the only thing this "
            "constraint is protecting.",
            "",
        ]

    if entry.discriminators:
        lines += [
            "## Neighbours",
            "",
            "These root causes match similar-looking code. Open them before you "
            "decide, and pick the one whose repair is the edit you would "
            "actually make. If two fit equally well, pick either and say so — "
            "the repair is what gets measured, and forcing a distinction the "
            "code does not make helps nobody.",
            "",
            "They are also where to look when this card nearly fits and you "
            "cannot write a repair from it.",
            "",
        ]
        for discriminator in entry.discriminators:
            neighbour = taxonomy[discriminator.against]
            lines += [
                f"- **[{neighbour.id} {neighbour.name}]"
                f"(../root-causes/{neighbour.id}.md)** — {discriminator.rule}",
            ]
        lines.append("")

    lines += ["## Verifying it", "", _verification_note(entry), ""]
    if entry.min_workload_hint:
        lines += [f"Workload hint: {entry.min_workload_hint}", ""]

    if entry.notes:
        lines += ["## Notes", "", entry.notes, ""]

    lines += [
        "## Decision",
        "",
        "1. Every `How to tell` step holds, and I can name the code for each.",
        "2. No `NOT a smell when` clause applies.",
        "3. This is not one of the `Looks the same, is not` cases.",
        "4. No neighbour describes it better.",
        "5. I can write the repair for *this* code, at this patch shape.",
        "6. This code runs often enough for the saving to exist at all.",
        "",
        "All six, or reject — and record which one decided it.",
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


def _cross_category_discriminators(
    category_id: str, catalog: Catalog, taxonomy: Taxonomy
) -> list[str]:
    """Discriminators pointing outside this category, surfaced one level early.

    A root cause in another category is exactly what a level-1 reader is most
    likely to miss, because they will never open its card by accident.
    """
    lines = []
    for entry in catalog.entries.values():
        if entry.category_id != category_id:
            continue
        for discriminator in entry.discriminators:
            if discriminator.against.split(".")[0] == category_id:
                continue
            neighbour = taxonomy[discriminator.against]
            lines.append(
                f"- **{entry.id} vs {neighbour.id} {neighbour.name}** — "
                f"{discriminator.rule}"
            )
    return lines


def _one_line(text: str) -> str:
    """First sentence of a description, for a table cell."""
    return _cell(text.split(". ")[0].strip().rstrip("."))


def _cell(text: str) -> str:
    """Escape text so a stray pipe or newline cannot break a markdown table."""
    return text.replace("|", "\\|").replace("\n", " ")
