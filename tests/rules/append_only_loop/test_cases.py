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

