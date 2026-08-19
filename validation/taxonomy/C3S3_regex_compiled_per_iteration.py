"""C3.S3 Per-Iteration Object Creation -- a pattern looked up on every call.

The card's first repair example, with the caveat it also names: `re.search`
looks the pattern up in a module-level cache on every call, so what the
compiled object saves is a dict probe plus the call rather than the whole
compilation. That makes this smaller than the shape suggests, and the card
should say so with a number rather than describing `re.compile` as removing a
compilation it does not.

`long-lines` and `short-lines` vary what the match itself costs, so the saving
can be read as a proportion of the work rather than in isolation.
"""

import re

_ID = re.compile(r"id=(\d+)")


def before(lines):
    found = []
    for line in lines:
        match = re.search(r"id=(\d+)", line)
        if match:
            found.append(int(match.group(1)))
    return found


def after(lines):
    found = []
    for line in lines:
        match = _ID.search(line)
        if match:
            found.append(int(match.group(1)))
    return found


def cases():
    return [("short-lines", lambda: ([f"id={i} x" for i in range(200_000)],)),
            ("long-lines",  lambda: ([("pad " * 60) + f"id={i}" for i in range(40_000)],)),
            ("edge",        lambda: ([],))]
