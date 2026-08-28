"""Cases for dead_initialization."""


def load(path):
    # Built and immediately replaced without being read.
    rows = []
    rows = parse(path)
    return rows


def summarise(records):
    # A whole dict comprehension discarded a line later.
    index = {r.key: r for r in records}
    index = build_index(records)
    return index


def accumulate(rows):
    # Read between the two assignments, so the first value is used.
    out = []
    out.append(rows[0])
    out = list(out)
    return out


def conditional_default(flag):
    # The initialisation is what the `else` path relies on.
    mode = "r"
    if flag:
        mode = "rb"
    return mode


def loop_accumulator(rows):
    # Reassigned inside a loop, which reads it every pass.
    total = 0
    for row in rows:
        total = total + row.value
    return total


def impure_first_value(path):
    # The first value has a side effect, so dropping it changes behaviour.
    handle = open(path)
    handle = None
    return handle


def strip_header(record):
    # The name is never read again, but `pop` also removes the element: the
    # binding is dead and the call is not.
    header = record.pop(0)
    return sum(record)