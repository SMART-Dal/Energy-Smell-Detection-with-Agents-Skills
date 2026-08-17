"""C10.S4 -- string accumulator grown through an attribute, so it cannot resize in place."""


class Report:
    def __init__(self):
        self.buf = ""


def before(rows):
    report = Report()
    for r in rows:
        report.buf += str(r)
    return report.buf


def after(rows):
    parts = []
    for r in rows:
        parts.append(str(r))
    report = Report()
    report.buf = "".join(parts)
    return report.buf


def cases():
    return [
        ("empty",  lambda: ([],)),
        ("single", lambda: ([0],)),
        ("large",  lambda: (list(range(40_000)),)),
    ]
