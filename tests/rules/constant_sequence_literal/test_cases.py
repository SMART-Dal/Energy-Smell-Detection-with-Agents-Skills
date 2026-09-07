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


def rebind_later(flag, requested):
    # Rebinding is not mutation: both literals can become tuples.
    modes = ["r", "w"]
    if flag:
        modes = ["rb", "wb"]
    return requested in modes


def handed_to_a_callee(rows):
    # The list leaves the unit, so what happens to it next is not visible here.
    # A tuple has no `append`, and the repair would move the failure into a
    # function this rule never looked at.
    fields = ["id", "name", "score"]
    register(fields)
    return len(fields)


def returned_to_the_caller():
    # Same reason: the caller receives a list and may treat it as one.
    labels = ["low", "medium", "high"]
    return labels


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
