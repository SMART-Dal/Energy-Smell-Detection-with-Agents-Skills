"""C10.S4 Inefficient String Concatenation -- there are three
parts.

"For N concatenations of average length M, this is O(N*M) total copying" is the
description's argument, and `C10S4_aliased` measures the join repair at +99.9%
where N is forty thousand.

N is three here. Building a list, appending three times, resolving `.join` and
calling it costs more than two `+=` on an unaliased local -- which CPython
resizes in place when the reference count is one, so the quadratic term the
description describes never starts. The repair is a list allocation and four
extra calls per row, paid on every row.

Both the loop count and the aliasing matter. `s += part` inside a loop over an
unknown-length input is the finding; the same operator over a fixed handful of
pieces is an f-string at worst, and the join form is slower than either.
"""

def before(rows):
    out = []
    for name, value, unit in rows:
        line = ""
        line += name
        line += "="
        line += f"{value}{unit}"
        out.append(line)
    return len(out)


def after(rows):
    out = []
    for name, value, unit in rows:
        parts = []
        parts.append(name)
        parts.append("=")
        parts.append(f"{value}{unit}")
        out.append("".join(parts))
    return len(out)


def _rows(n, width):
    return [(f"metric{i}" * width, i, "ms") for i in range(n)]


def cases():
    return [("three-parts",  lambda: (_rows(300_000, 1),)),
            ("long-parts",   lambda: (_rows(20_000, 200),)),
            ("edge",         lambda: ([],))]
