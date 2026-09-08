"""C10.S4 -- the same repair where a second reference blocks the optimisation.

Writing through an attribute means the string is reachable from the instance as
well as from the local, so its refcount is above 1 and CPython must copy on
every concatenation. This is the shape the rewritten card claims is the smell.
"""

class Report:
    def __init__(self):
        self.buf = ""


def before(parts):
    report = Report()
    for p in parts:
        report.buf += p
    return report.buf


def after(parts):
    collected = []
    for p in parts:
        collected.append(p)
    report = Report()
    report.buf = "".join(collected)
    return report.buf


def cases():
    return [
        ("many-small", lambda: (["abcde"] * 40_000,)),
        ("few-large", lambda: (["abcde" * 200] * 4_000,)),
    ]
