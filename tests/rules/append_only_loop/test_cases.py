"""Cases for append_only_loop."""


def parse_all(lines):
    # The whole body is one append: a comprehension in disguise.
    records = []
    for line in lines:
        records.append(parse(line))
    return records


def collect_names(rows):
    # Same shape appending to an attribute rather than a local.
    holder = Holder()
    for row in rows:
        holder.names.append(row.name)
    return holder


def keep_valid(rows):
    # An `if` around the append is a comprehension with a filter.
    kept = []
    for row in rows:
        if row.valid:
            kept.append(row)
    return kept


def count_and_collect(rows):
    # Two statements: the counter cannot move into a comprehension.
    seen = []
    total = 0
    for row in rows:
        seen.append(row.id)
        total += row.value
    return seen, total


def stop_at_limit(rows, limit):
    # The `break` is the point; a comprehension would walk everything.
    kept = []
    for row in rows:
        kept.append(row)
        if len(kept) >= limit:
            break
    return kept


def log_each(rows):
    # A single call that is not an append.
    for row in rows:
        emit(row)


def extend_once(rows, extra):
    # `extend` is the batched form already.
    out = []
    for row in rows:
        out.extend(row.children)
    return out


def build_in_closure(rows):
    # The loop belongs to the closure, not the factory.
    def run():
        out = []
        for row in rows:
            out.append(row.value)
        return out

    return run


def bucket_by_key(rows, buckets):
    # Each iteration appends to a different list, so there is no one
    # comprehension that replaces this.
    for row in rows:
        buckets[row.key].append(row)


def populate_queue(shared_queue, new_items):
    # The repair rebinds the receiver. `shared_queue = [i.data for i in
    # new_items]` builds a fresh local and leaves the caller holding the list
    # it passed in, still empty.
    for item in new_items:
        shared_queue.append(item.data)


def keep_valid_and_scored(rows):
    # A comprehension takes as many filters as you like, so nested `if`s are
    # still one: `[r for r in rows if r.valid if r.score > 10]`.
    kept = []
    for row in rows:
        if row.valid:
            if row.score > 10:
                kept.append(row)
    return kept


def reads_the_list_it_builds(xs):
    # Silent. A comprehension can carry a filter, but not one that consults the
    # list being built -- `out` is empty while the comprehension runs, so the
    # condition means something different there.
    out = []
    for x in xs:
        if x not in out:
            out.append(x)
    return out


def two_loops_one_list(a, b):
    # The first loop is a comprehension. The second is not: `out` already holds
    # the first loop's output, so `[y for y in b]` would discard it. The repair
    # there is `out.extend(b)`, which is a different signal.
    out = []
    for x in a:
        out.append(x)
    for y in b:
        out.append(y)
    return out
