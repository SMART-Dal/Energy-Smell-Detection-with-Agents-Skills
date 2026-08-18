"""Cases for deep_conditional_nesting."""


def dispatch_request(request, router, session):
    # Five `if` levels, and `request.method` is re-tested on the way down.
    if request is not None:
        if request.method == "POST":
            if request.path in router.table:
                if session.is_authenticated:
                    if request.method == "POST" and session.can_write:
                        return router.table[request.path](request)
    return None


class ImportPlan:
    def resolve(self, modules, graph):
        # Five levels reached through a loop; `dep.optional` is asked twice.
        for name in modules:
            if name in graph:
                if not graph[name].resolved:
                    for dep in graph[name].deps:
                        if dep.optional:
                            if dep.available:
                                if not dep.optional or dep.pinned:
                                    self.order.append(dep)
        return self.order


def parse_header(stream, spec):
    # `with` between the levels does not change how many tests the bottom pays.
    with stream.open() as handle:
        if handle.readable():
            for line in handle:
                if line.startswith("#"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        if key in spec.fields:
                            if spec.fields[key].required:
                                yield key, value.strip()


def build_validator(schema):
    # The nesting belongs to `check`; charging it to the factory as well counts
    # one piece of code twice.
    def check(record):
        if record:
            if schema.strict:
                if record.get("kind") in schema.kinds:
                    if record.get("id"):
                        if not record.get("deleted"):
                            return True
        return False
    return check


def classify_latency(ms):
    # Card counter-example: an `elif` chain is a linear search over ordered
    # boundaries, not a nest -- no path evaluates all of them, and ranges give
    # nothing to dispatch on.
    if ms < 10:
        return "fast"
    elif ms < 50:
        return "brisk"
    elif ms < 200:
        return "average"
    elif ms < 1000:
        return "slow"
    elif ms < 5000:
        return "degraded"
    return "timeout"


def render_tree(node, depth=0):
    # Card counter-example: each level asks a different question about a
    # different thing, so flattening removes no work.
    if node.visible:
        if node.children:
            for child in node.children:
                render_tree(child, depth + 1)
        else:
            emit(node, depth)


def open_ledger(path, rows):
    # Depth from `try`, `with` and `for`, which is not this root cause.
    try:
        with open(path) as handle:
            for row in rows:
                for field in row:
                    handle.write(str(field))
    except OSError:
        if path.endswith(".tmp"):
            cleanup(path)


def validate_row(row, schema):
    # Exactly four levels: the boundary the rule stops short of.
    if row:
        if schema.strict:
            if len(row) == schema.width:
                if row[0] not in schema.reserved:
                    return True
    return False
