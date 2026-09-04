"""Cases for repeated_pure_call."""


def summarise(path):
    # The same parse three times in one scope with nothing changing between.
    if parse_manifest(path).version < 2:
        raise Unsupported(path)
    if parse_manifest(path).entries:
        return parse_manifest(path).entries
    return []


def describe(record):
    # Twice is below the threshold; the rule wants three before it speaks.
    header = format_row(record)
    footer = format_row(record)
    return header + footer


def measure(values):
    # `len` is cheap enough that repeating it is not worth a claim.
    if len(values) > 2 and len(values) < 100:
        return len(values)
    return 0


def poll_twice(queue):
    # Same text, different results: `get` is not pure.
    return queue.get(), queue.get(), queue.get()


def per_row(rows):
    # Inside a loop this belongs to the loop analyzer, not here.
    out = []
    for row in rows:
        out.append(normalise(row.key) + normalise(row.key) + normalise(row.key))
    return out


def different_arguments(a, b, c):
    # The same function, three different calls.
    return score(a) + score(b) + score(c)


def budget_after_append(jobs, ceiling):
    # `len(pending)` twice, with an `append` to `pending` in between.
    pending = []
    for job in jobs:
        if len(pending) < ceiling:
            pending.append(job)
        budget = ceiling - len(pending)
        yield budget


def roll_three_dice():
    # Caching this is not a saving, it is three identical dice.
    d1 = randint(1, 6)
    d2 = randint(1, 6)
    d3 = randint(1, 6)
    return d1, d2, d3


def audit_data(data):
    # Three separate `if` statements, all of which can run. A running counter
    # gave them three arm numbers, so they read as three alternatives.
    if check_a():
        log(parse(data))
    if check_b():
        notify(parse(data))
    if check_c():
        save(parse(data))
