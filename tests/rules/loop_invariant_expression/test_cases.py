"""Cases for loop_invariant_expression."""

WEIGHTS = {"default": 1.0, "boosted": 2.5}


def filter_rows(rows, config):
    # One invariant nested inside another: the subscript is part of the call,
    # so the pair must be reported once and not twice.
    kept = []
    for row in rows:
        if row.score > float(config["min_score"]):
            kept.append(row)
    return kept


def take_while_small(values, limit):
    # A `while` test *is* re-evaluated every pass, unlike a `for` iterable.
    index = 0
    while index < len(values) and index < limit:
        emit(values[index])
        index += 1


def cross_check(orders, customers, region):
    # Invariant in a nest: one finding, attributed to the innermost loop.
    for order in orders:
        for customer in customers:
            if customer.region == region.strip().lower():
                link(order, customer)


def score_all(records):
    # A module-level dict indexed by a constant key: nothing here can change.
    total = 0
    for record in records:
        total += record.weight * WEIGHTS["default"]
    return total


def index_walk(values):
    # `len(values)` sits in the iterable clause, which runs once before the loop.
    for i in range(len(values)):
        process(values[i], i)


def walk_tree(queue):
    # The length must be recomputed: `extend` grows the very list it measures.
    position = 0
    while position < len(queue):
        queue.extend(children_of(queue[position]))
        position += 1
    return queue


def compact(values):
    # `del` shortens the list, so hoisting the bound would read past the end.
    i = 0
    while i < len(values):
        if values[i] is None:
            del values[i]
        else:
            i += 1
    return values


def bucket_lengths(rows):
    # Looks repetitive, reads the loop variable: a different value every pass.
    sizes = []
    for row in rows:
        sizes.append(len(row.items))
    return sizes


def take_until_full(rows, ceiling):
    # `ceiling - len(out)` reads the container the loop is filling, so it is
    # invariant in text only.
    out = []
    for row in rows:
        capacity = ceiling - len(out)
        if capacity > 0:
            out.append(row)
    return out


def best_per_group(groups):
    # `x` is the lambda's own parameter, rebound on every call.
    picked = {}
    for key, rows in groups.items():
        picked[key] = max(rows, key=lambda x: x[1])
    return picked


def report_failures(futures):
    # `e` is rebound by every iteration that raises, so `str(e)` is not
    # invariant -- and `except ... as e` carries its name as a bare string,
    # which no walk over Name nodes can see.
    for future in futures:
        label = futures[future]
        try:
            future.result(timeout=60)
        except Exception as e:
            print(f"failed {label}: {str(e)}")

