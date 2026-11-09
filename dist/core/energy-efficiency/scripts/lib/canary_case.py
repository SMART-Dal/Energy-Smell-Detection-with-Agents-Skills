"""The calibration workload for `verify.py --calibrate`.

A case file like any other, except that `before` and `after` are the same
computation. Measured against itself it must come back insignificant; the width
of that interval is what this host can resolve, and it is the bar every real
saving has to clear.

The workload is deliberately dull: integer arithmetic in a tight loop, no
allocation, no I/O, no data structure that grows. Anything livelier would make
the canary measure garbage collection rather than the machine.
"""


def _mix(n: int) -> int:
    total = 0
    for i in range(n):
        total = (total * 31 + i) & 0xFFFFFFFF
    return total


def before(n):
    return _mix(n)


def after(n):
    return _mix(n)


def cases():
    return [("canary", lambda: (200_000,))]
