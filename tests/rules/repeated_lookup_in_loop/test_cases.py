"""Cases for repeated_lookup_in_loop."""

import math


class Gauge:
    def clamp(self, values):
        # A three-link chain read three times a pass: one finding, not one per link.
        clamped = []
        for value in values:
            if value < self.limits.window.low:
                value = self.limits.window.low
            clamped.append(min(value, self.limits.window.high))
        return clamped


class Meter:
    def accumulate(self, samples):
        # The chain is rebound every pass, so a local binding would go stale.
        for sample in samples:
            self.total = self.total + sample.value
            if self.total > self.ceiling:
                self.total = 0


def render_matrix(rows, theme):
    # One chain inside a nest: reported once, not once per enclosing loop.
    painted = []
    for row in rows:
        for cell in row:
            painted.append(
                (theme.palette.fill.r, theme.palette.fill.g, theme.palette.fill.b, cell)
            )
    return painted


def flush_all(batches, sink):
    # Every use is a call, so the repair is `write = sink.writer.write`: the
    # bound-method alias, measured at 10.6% however many dots lead to it.
    for batch in batches:
        sink.writer.write(batch.header)
        sink.writer.write(batch.body)
        sink.writer.write(batch.footer)


def apply_theme(cells, style):
    # Two dots resolved three times: the plain shape the rule exists for.
    for cell in cells:
        cell.background = style.theme.fill
        cell.border = style.theme.fill
        cell.outline = style.theme.fill


def apply_fill(cells, style):
    # One dot, three times. Caching it saves one lookup per access, which is
    # how `C8S3_bound_method_alias` measured: inside the 15% that counts as none.
    for cell in cells:
        cell.background = style.fill
        cell.border = style.fill
        cell.outline = style.fill


def collect_parts(chunks):
    # The same for a bound method on a local: `parts.append` is how everyone
    # writes it, and binding `append = parts.append` is not worth asking for.
    parts = []
    for chunk in chunks:
        if chunk.kind == "text":
            parts.append(chunk.text)
        elif chunk.kind == "tool":
            parts.append(f"[tool: {chunk.name}]")
        else:
            parts.append(str(chunk))
    return parts


def consume(queue, worker):
    # Read once a pass, and deliberately -- hoisting it makes this uncancellable.
    for item in queue:
        if worker.state.cancelled:
            break
        worker.handle(item)


def total_amount(rows):
    # Repeated, but the base is the loop variable, so nothing is invariant.
    total = 0
    for row in rows:
        total += row.amount
        if row.amount < 0:
            raise ValueError(row)
    return total


def notify_all(rows, session):
    # One resolution per pass: below the threshold the rule claims.
    for row in rows:
        deliver(row, session.config.timeout)


def paint_pair(cells, style):
    # Twice is not a finding: two dict lookups against a local the next reader
    # has to carry is the shape of ordinary code.
    for cell in cells:
        cell.background = style.fill
        cell.border = style.fill


def norms(points):
    # A module attribute, four times a pass. Left alone: nothing asks anyone
    # to bind `math` to a local, so asking for `sqrt = math.sqrt` one dot
    # later would be the same advice in a costume -- and a module attribute is
    # one plain dict probe, no MRO, no descriptor.
    out = []
    for x, y, z, w in points:
        out.append(math.sqrt(x) + math.sqrt(y) + math.sqrt(z) + math.sqrt(w))
    return out


def stage_typed(groups, models):
    # An attribute chain, four times a pass, all of it annotation. `models`
    # arrives as a parameter here rather than an `import`, so the module-alias
    # exclusion does not cover it and the annotation check has to.
    out = []
    for group in groups:
        a: models.Order = None
        b: models.Order = None
        c: models.Order = None
        d: models.Order = None
        out.append((a, b, c, d, group))
    return out
