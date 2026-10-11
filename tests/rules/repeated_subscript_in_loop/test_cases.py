"""Cases for repeated_subscript_in_loop."""

LIMIT = 10


def tally(keys, d, seen):
    # Three lookups of the same entry in one pass; the key is the loop variable.
    total = 0
    for k in keys:
        if d[k] > LIMIT:
            total += d[k]
            seen.append(d[k])
    return total


def describe(keys, d):
    # The same in a comprehension's element.
    return [(d[k], d[k] * 2, str(d[k])) for k in keys]


def columns(rows, n):
    # `rows[i]` three times, each with a different field after it: one finding,
    # on the shared lookup, not one per field.
    out = []
    for i in range(n):
        out.append((rows[i]["a"], rows[i]["b"], rows[i]["c"]))
    return out


def by_id(items, cache):
    # The key is built at the top of the pass, before any read.
    out = []
    for item in items:
        key = item.id
        if cache[key] is not None:
            out.append(cache[key] + cache[key])
    return out


def twice(keys, d):
    # Two reads is ordinary code.
    return [d[k] + d[k] for k in keys]


def fixed_key(rows, d):
    # The key never changes: that is `loop_invariant_expression`'s finding.
    out = []
    for row in rows:
        out.append((row, d["a"], d["a"], d["a"]))
    return out


def counting(keys, counts):
    # The pass writes the entry it reads, so the reads see different values.
    for k in keys:
        counts[k] += 1
        if counts[k] > LIMIT and counts[k] % 2:
            print(counts[k])


def rebinding(keys, d):
    # `k` changes between the reads.
    out = []
    for k in keys:
        first = d[k]
        k = k.lower()
        out.append((first, d[k], d[k]))
    return out


def one_arm_each(keys, d, mode):
    # Only one arm runs per pass, so one lookup does.
    out = []
    for k in keys:
        if mode == "a":
            out.append(d[k])
        elif mode == "b":
            out.append(-d[k])
        else:
            out.append(d[k] * 2)
    return out


def slices(keys, text):
    # A slice copies; it is not a lookup.
    return [(text[k:], text[k:], text[k:]) for k in keys]
