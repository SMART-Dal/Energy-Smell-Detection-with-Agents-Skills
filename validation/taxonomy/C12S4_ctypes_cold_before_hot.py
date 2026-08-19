"""C12.S4 Inefficient Array Declaration Order -- a real declared layout.

The other C12.S4 case reorders `__slots__`, which the card says is not this
root cause at all: CPython stores slots as pointers to objects elsewhere on the
heap, so two slots are never adjacent whatever the order. It read +0.6%, which
is the correct answer to the wrong question.

Here the layout is declared. A 4 KB cold buffer in front of the hot field means
every `samples[0]` read touches a line 4 KB into the structure and the stride
between consecutive frames is 4 KB; moving `samples` to the base puts the hot
bytes at the front of each frame.

Both arrays are built at import, outside every measured window, because
building them is far more expensive than walking them and would otherwise be
the only thing this measured.
"""

import ctypes

FRAMES = 40_000


class Cold(ctypes.Structure):
    _fields_ = [("error_log", ctypes.c_char * 4096),
                ("samples", ctypes.c_double * 4)]


class Hot(ctypes.Structure):
    _fields_ = [("samples", ctypes.c_double * 4),
                ("error_log", ctypes.c_char * 4096)]


def _build(kind, n):
    array = (kind * n)()
    for i in range(n):
        array[i].samples[0] = float(i)
    return array


_COLD_FIRST = _build(Cold, FRAMES)
_HOT_FIRST = _build(Hot, FRAMES)


def before(count):
    total = 0.0
    for i in range(count):
        total += _COLD_FIRST[i].samples[0]
    return total


def after(count):
    total = 0.0
    for i in range(count):
        total += _HOT_FIRST[i].samples[0]
    return total


def cases():
    return [("many-frames", lambda: (FRAMES,)),
            ("few-frames",  lambda: (40,)),
            ("edge",        lambda: (1,))]
