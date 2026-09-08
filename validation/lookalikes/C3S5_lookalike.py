"""C3.S5 Missing Loop Early Exit -- LOOKS THE SAME, IS NOT: the loop is collecting the
failures, not detecting one.

The description's second example is "a validation loop that checks all 10,000
records even after finding an invalid one on the 3rd record", and
`C3S5_missing_early_exit` measures the `break` at +100% when that is what the
loop is doing.

This loop looks the same to a reader who stops at the `if`: a scan, a test, a
match, and no `break`. What it does with the match is the difference -- it
appends. A `break` after the first append turns a report of every bad row into a
report of the first bad row, and the caller that renders "3 problems found" now
renders one.

The test is what happens on the match. Setting a flag or returning is a search
and the exit is free; appending, counting, or accumulating is a fold and every
iteration is load-bearing.
"""

def _invalid(record):
    return record % 97 == 0


def before(records):
    problems = []
    for position, record in enumerate(records):
        if _invalid(record):
            problems.append(position)
    return problems


def after(records):
    problems = []
    for position, record in enumerate(records):
        if _invalid(record):
            problems.append(position)
            break                      # "stop at the first failure"
    return problems


def cases():
    return [("many-failures", lambda: (list(range(300_000)),)),
            ("no-failures",   lambda: ([i * 97 + 1 for i in range(300_000)],))]
