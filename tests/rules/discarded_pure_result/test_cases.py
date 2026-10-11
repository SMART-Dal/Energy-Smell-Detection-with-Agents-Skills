"""Cases for discarded_pure_result."""


def rank(rows):
    # `sorted` builds a list nothing receives.
    sorted(rows, key=lambda r: r.score)
    return rows


def measure(values):
    # `len` computed and dropped: dead, but a call's worth, not work.
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


def render(parts):
    # A literal receiver: this really is `str.join`, and nothing takes it.
    ", ".join(parts)
    return len(parts)


def wait_for(worker):
    # `Thread.join` shares a name with `str.join` and blocks until the thread ends.
    worker.start()
    worker.join()


def drain(queue, sink):
    # `Queue.get` removes an item; `dict.get` does not. The name cannot say which.
    queue.get()
    sink.flush()


def numeric_port(port):
    # The exception is the answer: deleting the call deletes the check.
    try:
        int(port)
    except ValueError:
        return None
    return port


def first_or_none(rows):
    # In the `except` arm, running normally, so its result really is dropped.
    try:
        return rows[0]
    except IndexError:
        sorted(rows)
        return None


def test_digest_is_hex(build):
    # Unguarded, but in a test the exception is the assertion.
    assert len(build["sha256"]) == 64
    int(build["sha256"], 16)
