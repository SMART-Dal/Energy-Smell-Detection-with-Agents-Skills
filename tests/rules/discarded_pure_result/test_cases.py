"""Cases for discarded_pure_result."""


def rank(rows):
    # `sorted` builds a list nothing receives.
    sorted(rows, key=lambda r: r.score)
    return rows


def measure(values):
    # `len` computed and dropped.
    len(values)
    return values


def order_in_place(rows):
    # `list.sort` mutates; the result being None is the point.
    rows.sort(key=lambda r: r.score)
    return rows


def validate(record, schema):
    # Kept for the exception it may raise, not for its value.
    schema.validate(record)
    return record


def warm(cache, keys):
    # The results are discarded and the call is the whole purpose.
    for key in keys:
        cache.lookup(key)


def emit(rows):
    # `print` is not pure.
    print(len(rows))
    return rows
