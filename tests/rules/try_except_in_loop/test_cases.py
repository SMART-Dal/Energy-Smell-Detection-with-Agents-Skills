"""Cases for try_except_in_loop."""


def lookup_all(keys, table):
    # A raise per missing key, on the per-iteration path.
    out = []
    for key in keys:
        try:
            out.append(table[key])
        except KeyError:
            out.append(None)
    return out


def parse_ports(values):
    # Same shape in a `while`.
    ports = []
    index = 0
    while index < len(values):
        try:
            ports.append(int(values[index]))
        except ValueError:
            ports.append(0)
        index += 1
    return ports


def load_each(paths):
    # Nested loop: still one report for one `try`.
    loaded = []
    for group in paths:
        for path in group:
            try:
                loaded.append(open(path).read())
            except OSError:
                continue
    return loaded


def load_all(paths):
    # The `try` wraps the whole loop, so it can raise at most once.
    try:
        return [open(path).read() for path in paths]
    except OSError:
        return []


def retry_once(action, attempts):
    # A loop inside the `try`, not the other way round.
    try:
        for _ in range(attempts):
            action()
    except RuntimeError:
        return False
    return True


def guarded_lookup(keys, table):
    # The repaired form: a test rather than a raise.
    return [table.get(key) for key in keys]


def build_handlers(specs):
    # The `try` belongs to the closure, not to the loop that makes them.
    handlers = []
    for spec in specs:
        def run(payload, spec=spec):
            try:
                return spec.apply(payload)
            except ValueError:
                return None
        handlers.append(run)
    return handlers


def cleanup_each_pass(rows):
    # Silent. `try/finally` with no `except` catches nothing, so there is no
    # exception path to be on. What is here is cleanup, and it has to run.
    for row in rows:
        try:
            use(row)
        finally:
            release(row)
