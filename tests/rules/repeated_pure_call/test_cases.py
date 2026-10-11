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


def start(
    host=Option("127.0.0.1"),
    realesrgan=Option(False),
    gfpgan=Option(False),
    restoreformer=Option(False),
):
    # Each default is its own object, built once when the `def` runs.
    return host, realesrgan, gfpgan, restoreformer


def reset_target(window):
    # Called for what it does: the result is dropped every time.
    if window.closing:
        set_taskbar_target(None)
    set_taskbar_target(None)
    set_taskbar_target(None)


def load_artifact(payload):
    # Three raises, one of which runs, each needing an exception of its own.
    if payload is None:
        raise CorruptArtifactError("The artifact payload is invalid.")
    if not payload.frame:
        raise CorruptArtifactError("The artifact payload is invalid.")
    if not payload.columns:
        raise CorruptArtifactError("The artifact payload is invalid.")
    return payload


def cleanup(paths):
    # Each `with` takes a context manager of its own.
    with suppress(OSError):
        remove(paths[0])
    with suppress(OSError):
        remove(paths[1])
    with suppress(OSError):
        remove(paths[2])


async def run_three(session, backend, prompt):
    # Awaited for its effect; the result is dropped each time.
    await _run(session, backend, prompt)
    await _run(session, backend, prompt)
    await _run(session, backend, prompt)


def group_three(rows):
    # Three separate dicts, each built on purpose.
    by_arm = defaultdict(list)
    by_task = defaultdict(list)
    by_trial = defaultdict(list)
    return by_arm, by_task, by_trial, rows
