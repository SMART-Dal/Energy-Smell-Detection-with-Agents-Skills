"""C3.S7 Inefficient Array Mutation in Loop -- LOOKS THE SAME, IS NOT: rebinding is not
rebuilding.

Removing from a list while iterating it is a defect, and the repair is to build
the survivors instead; `C3S7_mutation_in_loop` measures that at +99.8%. The
repair has two spellings that differ by three characters:

    values[:] = [v for v in values if keep(v)]     # rewrites the list
    values    = [v for v in values if keep(v)]     # rebinds the name

The second is what gets written, because it reads better and because the
function usually returns the list anyway. It leaves every other reference to the
original list -- the caller's, the dict entry it came from, the other object
holding it -- pointing at the unfiltered version.

The pattern is a defect either way; the repair has to preserve identity when
anything else can see the container.
"""

def before(batches):
    for values in batches:
        i = 0
        while i < len(values):
            if values[i] % 3 == 0:
                del values[i]
            else:
                i += 1
    return sum(len(v) for v in batches)


def after(batches):
    for values in batches:
        values = [v for v in values if v % 3]     # rebinds the local only
    return sum(len(v) for v in batches)


def _batches(count, width):
    return [list(range(width)) for _ in range(count)]


def cases():
    return [("many-batches", lambda: (_batches(4_000, 60),)),
            ("wide-batches", lambda: (_batches(40, 6_000),)),
            ("edge",         lambda: ([[]],))]
