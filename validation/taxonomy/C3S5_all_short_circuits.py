"""C3.S5 Missing Loop Early Exit -- `all()` instead of a flag.

The card's first repair example and its central point: the saving is not a
property of the code but of the data, so the failure position is the variable.
`fails-early` is where it pays, `never-fails` is where it cannot, and both
belong in the report.
"""

class Record:
    __slots__ = ("ok",)

    def __init__(self, ok):
        self.ok = ok

    def check(self):
        return self.ok


def before(records):
    valid = True
    for record in records:
        if not record.check():
            valid = False
    return valid


def after(records):
    return all(record.check() for record in records)


def _records(n, fail_at):
    rows = [Record(True) for _ in range(n)]
    if fail_at is not None:
        rows[fail_at].ok = False
    return rows


def cases():
    return [("fails-early", lambda: (_records(400_000, 3),)),
            ("never-fails", lambda: (_records(400_000, None),)),
            ("edge",        lambda: ([],))]
