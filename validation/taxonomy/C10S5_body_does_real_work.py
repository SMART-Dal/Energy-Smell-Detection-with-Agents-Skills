"""C10.S5 Global Variable Access In Loops -- the same alias, in a body that
does something.

The card's fourth `NOT a smell when` clause: one global read in a body that
already does substantial work is a negligible proportion. Identical repair to
the three-globals case, and the only difference is that each iteration also
formats a string -- which should bury the lookup entirely. If it does, the card
can state the ratio instead of saying "unless the loop is hot".
"""

FORMAT = "{:>12.4f}"


def before(values):
    out = []
    for value in values:
        out.append(FORMAT.format(value))
    return len(out)


def after(values):
    fmt = FORMAT
    out = []
    for value in values:
        out.append(fmt.format(value))
    return len(out)


def cases():
    return [("large",  lambda: ([i * 1.5 for i in range(400_000)],)),
            ("normal", lambda: ([i * 1.5 for i in range(4_000)],)),
            ("edge",   lambda: ([],))]
