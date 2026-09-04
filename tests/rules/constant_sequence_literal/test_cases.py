"""Cases for constant_sequence_literal."""


def assign_type(number):
    # Rebuilt element by element on every call and only ever indexed.
    types = ["red", "blue", "green"]
    return types[number % 3]


def bucket_for(value):
    # The same shape inside a loop, where it is paid per iteration.
    out = []
    for item in value:
        limits = [10, 100, 1000]
        out.append(sum(1 for limit in limits if item > limit))
    return out


def collect_defaults(extra):
    # Mutated afterwards, so a tuple would break it.
    names = ["stdout", "stderr"]
    names.append(extra)
    return names


def rebind_later(flag):
    # Rebinding is not mutation: both literals can become tuples.
    modes = ["r", "w"]
    if flag:
        modes = ["rb", "wb"]
    return modes


def from_expressions(width):
    # The elements are not constants.
    sizes = [width, width * 2]
    return sizes


def already_a_tuple(number):
    # The repaired form.
    types = ("red", "blue", "green")
    return types[number % 3]


def empty_accumulator(rows):
    # An empty list is an accumulator, not a constant table.
    out = []
    for row in rows:
        out.append(row)
    return out


def build_command(csv):
    # `cmd += [...]` is `list.__iadd__`, an in-place extend. As a tuple it
    # stops being in-place, and `tuple += list` raises outright.
    cmd = ["perf", "stat"]
    if csv:
        cmd += ["-x", ","]
    return cmd
