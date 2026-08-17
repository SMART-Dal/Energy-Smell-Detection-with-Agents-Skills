"""A mutable default that this body never writes to -- and still fires.

This started as a `quiet_` case and was moved, because "the body does not
mutate it" is not the question.  The default is handed to the caller: in
`render_columns` the caller receives the shared list back, and in
`apply_defaults` the shared dict is passed on to `update_settings`, which is
free to write to it.  Proving no reachable code ever mutates it would take
whole-program analysis, and the repair -- default to `None` and build the
object in the body -- costs one line, so the trade is not worth making.  Ruff's
B006 draws the line in the same place.

Reading the default in place is genuinely harmless today; what the report is
telling the reader is that nothing stops the next caller from breaking it.
"""

from __future__ import annotations


def render_columns(row, columns=["id", "name", "status"]):  # EXPECT
    """Render the named columns of one row, in order."""
    return [row.get(column, "") for column in columns]


def apply_defaults(settings, fallbacks={"retries": 3, "timeout": 30}):  # EXPECT
    """Fill in any setting the caller left out."""
    merged = dict(fallbacks)
    merged.update(settings)
    return merged
