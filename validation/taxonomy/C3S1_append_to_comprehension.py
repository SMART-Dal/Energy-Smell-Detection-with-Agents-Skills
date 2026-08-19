"""C3.S1 Suboptimal Iteration Construct -- an append loop with nothing else in
the body.

The card's third example, and it stresses that this only holds because the body
is exactly one append: a `continue`, a `break` or a side effect blocks it. The
`with-filter` case keeps the repair available -- a comprehension can carry an
`if` -- so the two readings say what the filter costs rather than whether the
repair exists.
"""

def _parse(line):
    return line.count(",") + len(line)


def before(lines, minimum):
    records = []
    for line in lines:
        value = _parse(line)
        if value >= minimum:
            records.append(value)
    return records


def after(lines, minimum):
    return [v for v in (_parse(line) for line in lines) if v >= minimum]


def cases():
    lines = [f"a{i},b{i},c{i}" for i in range(400_000)]
    return [("keeps-all",   lambda: (list(lines), 0)),
            ("with-filter", lambda: (list(lines), 12)),
            ("edge",        lambda: ([], 0))]
