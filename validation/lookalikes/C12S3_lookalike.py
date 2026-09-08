"""C12.S3 Unpredictable Branches -- LOOKS THE SAME, IS NOT: the branch was guarding the
expression, not choosing between two of them.

"Sorting the data first would make the branch pattern predictable" and the
branchless rewrite are the two repairs, and `C12S3_unpredictable_branch`
measures the branchless form on a condition that only selects.

The condition here also protects. `total += value / divisor` is safe only when
`divisor` is non-zero, so `total += (value / divisor) * (divisor != 0)`
evaluates the division first and raises on every zero. Branchless arithmetic
computes both sides; a guard exists precisely because one side must not be
computed.

The same trap is in `x[i] if i < len(x) else 0`, in `d[k] if k in d else 0`, and
in anything with a `None` check in front of it. A branch may be flattened into
arithmetic when both arms are total functions of the input -- and a guard, by
definition, is not.
"""

def before(pairs):
    total = 0.0
    for value, divisor in pairs:
        if divisor != 0:
            total += value / divisor
    return round(total, 6)


def after(pairs):
    total = 0.0
    for value, divisor in pairs:
        total += (value / divisor) * (divisor != 0)
    return round(total, 6)


def _pairs(n, with_zeros):
    out = []
    for i in range(n):
        divisor = 0 if (with_zeros and i % 1_000 == 0) else (i % 97) + 1
        out.append((float(i % 997), divisor))
    return out


def cases():
    return [("has-zeros", lambda: (_pairs(300_000, True),)),
            ("no-zeros",  lambda: (_pairs(300_000, False),))]
