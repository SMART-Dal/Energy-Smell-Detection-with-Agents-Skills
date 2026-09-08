"""C12.S4 Inefficient Array Declaration Order -- alignment padding from an
interleaved field order.

The card's second repair example. Interleaving one-byte and eight-byte fields
makes the compiler pad to keep the doubles aligned; grouping them removes the
padding, the structure gets smaller, and more of them fit per cache line. The
module prints nothing, but `ctypes.sizeof` on the two classes is the whole
claim and the docstring records it: 32 bytes against 24.

This is footprint rather than per-element work, which is why the card marks the
root cause advisory. Whether a smaller stride shows up at all is the question.
"""

import ctypes

SAMPLES = 400_000


class Interleaved(ctypes.Structure):
    _fields_ = [("flag", ctypes.c_uint8),
                ("value", ctypes.c_double),
                ("kind", ctypes.c_uint8),
                ("weight", ctypes.c_double)]


class Grouped(ctypes.Structure):
    _fields_ = [("value", ctypes.c_double),
                ("weight", ctypes.c_double),
                ("flag", ctypes.c_uint8),
                ("kind", ctypes.c_uint8)]


def _build(kind, n):
    array = (kind * n)()
    for i in range(n):
        array[i].value = float(i)
        array[i].weight = 1.0
    return array


_INTERLEAVED = _build(Interleaved, SAMPLES)
_GROUPED = _build(Grouped, SAMPLES)


def before(count):
    total = 0.0
    for i in range(count):
        sample = _INTERLEAVED[i]
        total += sample.value * sample.weight
    return total


def after(count):
    total = 0.0
    for i in range(count):
        sample = _GROUPED[i]
        total += sample.value * sample.weight
    return total


def cases():
    return [("many-samples", lambda: (SAMPLES,)),
            ("few-samples",  lambda: (300,))]
