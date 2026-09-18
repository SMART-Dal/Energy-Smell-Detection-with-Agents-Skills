"""C5.S3 Over-Provisioned Data Type -- a one-character string where an int does.

The taxonomy's own first example for this root cause, which had no
implementation: "storing a single-character value as a full string object where
a character code would suffice in a tight numerical loop".

Every one-character string is a full `str` object with a header, a length and
an encoding kind, and comparing two of them enters the string compare path. An
`int` from `ord()` compares as a machine word. CPython interns single
characters, so the allocation is not the cost here -- the comparison path is.

The repair moves the conversion to the boundary: `after` pays one `ord()` per
element to buy integer comparisons for the whole loop, which is why it needs
the comparisons to outnumber the conversions to pay at all.
"""


def before(text, targets):
    hits = 0
    for character in text:
        for target in targets:
            if character == target:
                hits += 1
    return hits


def after(text, targets):
    codes = [ord(t) for t in targets]
    hits = 0
    for code in map(ord, text):
        for target in codes:
            if code == target:
                hits += 1
    return hits


def cases():
    return [("many-comparisons", lambda: ("abcdefgh" * 40_000, "aeiou")),
            ("one-comparison",   lambda: ("abcdefgh" * 40_000, "a"))]
