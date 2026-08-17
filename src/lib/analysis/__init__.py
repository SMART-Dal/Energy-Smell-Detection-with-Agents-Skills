"""Static analyzers, and the types they produce.

An *analyzer family* is any module in this package that defines:

    collect(path, units, source, imports) -> list[Evidence]

and, optionally:

    unavailable_reason() -> str | None      why it cannot run right now

`engine.py` finds them by walking this package, so adding a family is a matter
of dropping in a module and nothing else, and removing one is a matter of
deleting the file.  Nothing anywhere holds a list of which families exist.

That is not only tidiness.  An installation with fewer analyzers has to behave
exactly like one that never had more -- same code, same messages, no mention of
an absent family -- because whoever is reading the output is supposed to be
judging the code, not reverse-engineering the tool.
"""
