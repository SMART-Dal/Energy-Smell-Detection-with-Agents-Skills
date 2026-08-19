"""C1.S2 Redundant Assignment -- `.strip()` on text that is already stripped.

The card's own counter-example says this one *does* scale, because `str.strip`
scans from both ends whether or not there is anything to remove. Long strings
should therefore show more than short ones, which is the point of the two
sizes: this is the case that separates "a redundant store" from "a redundant
operation".
"""

def before(lines):
    out = []
    for line in lines:
        line = line.strip()              # nothing to strip; still scans
        out.append(line)
    return out


def after(lines):
    out = []
    for line in lines:
        out.append(line)
    return out


def cases():
    return [("long-strings",  lambda: (["x" * 4_000] * 20_000,)),
            ("short-strings", lambda: (["abc"] * 20_000,)),
            ("edge",          lambda: ([],))]
