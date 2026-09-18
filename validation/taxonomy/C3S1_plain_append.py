"""C3.S1 Inefficient Iteration -- an append loop whose body is only the append.

The card's note turns on this shape: the comprehension wins "only because the
body is exactly one append". Every other measured file in this root cause puts
something else in the body -- a filter, an early exit -- which changes what is
being compared. This is the plain form, so the claim the note rests on has a
measurement behind it.
"""


def _parse(line):
    return line.count(",") + len(line)


def before(lines):
    records = []
    for line in lines:
        records.append(_parse(line))
    return records


def after(lines):
    return [_parse(line) for line in lines]


def cases():
    return [("large",  lambda: ([f"a{i},b{i},c{i}" for i in range(400_000)],)),
            ("normal", lambda: ([f"a{i},b{i},c{i}" for i in range(4_000)],))]
