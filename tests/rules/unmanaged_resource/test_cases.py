"""Cases for unmanaged_resource."""

import json


def load_config(path):
    # The card's own example: opened, read, abandoned to the collector.
    handle = open(path, encoding="utf-8")
    text = handle.read()
    return json.loads(text)


def merge_parts(paths, destination):
    # Two acquisitions leak here, and the per-iteration one is still one finding.
    output = open(destination, "w", encoding="utf-8")
    for path in paths:
        part = open(path, encoding="utf-8")
        output.write(part.read())


def fetch_rows(connection, query):
    # A cursor is an acquisition too, and this one outlives the answer.
    cursor = connection.cursor()
    rows = cursor.execute(query).fetchall()
    connection.commit()
    return rows


def make_appender(path):
    # The leak belongs to the closure; charging the factory for it too is noise.
    def append(line):
        handle = open(path, "a", encoding="utf-8")
        handle.write(line)

    return append


def append_audit(path, entry, file_lock):
    # The `with` locks by filename; it never adopts the handle it read a name off.
    audit = open(path, "a", encoding="utf-8")
    with file_lock(audit.name):
        audit.write(entry)


class IndexBuilder:
    def read_manifest(self, path):
        # What is stored on `self` is the parsed manifest, not the handle.
        handle = open(path, encoding="utf-8")
        self.manifest = json.load(handle)
        return self.manifest

    def attach(self, path):
        # Here the handle itself is stored, so the instance owns it from now on.
        handle = open(path, "rb")
        self._raw = handle
        return self


def open_log(path):
    # A factory: the caller owns what it is handed, and closing it here is wrong.
    handle = open(path, "a", encoding="utf-8")
    handle.write("--- session start\n")
    return handle


def write_payload(path, payload):
    # NumPy's shape: the acquisition is a line above the `with` that adopts it.
    ctx = open(path, "wb")
    with ctx as f:
        f.write(payload)


def dump_rows(path, rows):
    # Closed on every path, which is the commonest thing to misreport.
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.writelines(rows)
    finally:
        handle.close()


def tail_with_cleanup(path, stack):
    # The closer is registered with the caller's stack, which unwinds it later.
    handle = open(path, "rb")
    stack.callback(handle.close)
    handle.seek(-4096, 2)
    return handle.read()


def digest_of(path, hasher):
    # Used inline rather than bound: a different pattern, and out of scope here.
    return hasher(open(path, "rb").read()).hexdigest()


def open_report(path):
    # The handle is the return value; a `with` here closes it before the caller
    # can read it.
    return open(path, encoding="utf-8")


def bind_events(view, graph, node_a, node_b):
    # A Qt signal, a graph edge and a text cursor. None is an OS handle, and
    # trusting every receiver named `.connect()` or `.cursor()` reported all
    # three as leaked files.
    conn = view.clicked.connect(view.refresh)
    edge = graph.connect(node_a, node_b)
    csr = view.document.cursor()
    log(conn, edge, csr)


def write_audit_log(entry):
    # `Path(...).open()` is how modern Python opens a file, and the receiver
    # is a call, which a module-name check can never match.
    log_file = Path("/var/log/audit.log").open("a")
    log_file.write(entry)


def read_payload():
    # An annotated assignment opens exactly the same file.
    handle: object = open("payload.bin", "r")
    return handle.read()


def read_fallback():
    # And so does a walrus.
    if (stream := open("fallback.bin", "r")):
        return stream.read()
    return None


def silenced_stderr():
    # A descriptor from `os.open`, closed by `os.close` in the `finally`.
    saved = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, 2)
    finally:
        os.dup2(saved, 2)
        os.close(devnull_fd)
