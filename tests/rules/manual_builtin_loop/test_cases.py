"""Cases for manual_builtin_loop."""


def largest(values):
    # A running maximum by hand.
    best = values[0]
    for value in values:
        if value > best:
            best = value
    return best


def total(values):
    # A running total by hand.
    running = 0
    for value in values:
        running += value
    return running


def smallest_score(records):
    # A running minimum, guarded by an `if`.
    lowest = None
    for record in records:
        if lowest is None or record.score < lowest:
            lowest = record.score
    return lowest


def best_record(records):
    # Tracks the *element*, not the value: `max(records, key=...)` is the repair,
    # and the loop keeps two variables in step, which `max` alone cannot.
    best = None
    best_score = 0
    for record in records:
        if record.score > best_score:
            best, best_score = record, record.score
    return best


def running_maximum(values):
    # Every prefix maximum is kept, so no single call replaces the loop.
    out = []
    best = values[0]
    for value in values:
        if value > best:
            best = value
        out.append(best)
    return out


def use_builtin(values):
    # Already the repair.
    return max(values) - min(values)


def count_matching(rows, needle):
    # A counter, not an extreme or a total over the iterable.
    found = 0
    for row in rows:
        if needle in row:
            found += 1
    return found


def total_even(values):
    # A filtered sum: `sum()` still does the adding in C.
    running = 0
    for value in values:
        if value % 2 == 0:
            running += value
    return running
