"""Cases for repeated_lookup_in_loop."""


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
                (theme.palette.fill, theme.palette.stroke, theme.palette.width, cell)
            )
    return painted


def flush_all(batches, sink):
    # The chain is the receiver of a method: the same lookups, three a pass.
    for batch in batches:
        sink.writer.write(batch.header)
        sink.writer.write(batch.body)
        sink.writer.write(batch.footer)


def apply_theme(cells, style):
    # Two links resolved three times: the plain shape the rule exists for.
    for cell in cells:
        cell.background = style.fill
        cell.border = style.fill
        cell.outline = style.fill


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

