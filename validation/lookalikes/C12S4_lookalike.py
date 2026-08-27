"""C12.S4 Inefficient Array Declaration Order -- LOOKS THE SAME, IS NOT: the order is
the wire format.

`C12S4_ctypes_cold_before_hot` is the case where declaration order is real:
moving a hot field to the front of a `ctypes.Structure` changes where the bytes
sit. The repair is to reorder the fields.

These fields are the layout of a record another program wrote. Reordering the
declaration does not move the bytes on disk; it changes how this program reads
them, so every field is parsed out of the wrong offset. The struct gets smaller
and better-aligned and every value in it is wrong.

Layout is only free to change where nothing outside the process depends on it. A
`_fields_` list that mirrors a file header, a network packet, a shared-memory
segment or a C ABI is a contract -- and where the layout is genuinely private,
the padding argument in `C12S4_ctypes_padding` is the one that applies.
"""

import ctypes

RECORDS = 200_000


class WireOrder(ctypes.Structure):
    """Exactly the order the producer wrote."""

    _fields_ = [("flag", ctypes.c_uint8),
                ("value", ctypes.c_double),
                ("kind", ctypes.c_uint8),
                ("weight", ctypes.c_double)]


class PackedOrder(ctypes.Structure):
    """Grouped to remove padding -- and no longer the order on the wire."""

    _fields_ = [("value", ctypes.c_double),
                ("weight", ctypes.c_double),
                ("flag", ctypes.c_uint8),
                ("kind", ctypes.c_uint8)]


def _payload(n):
    """The bytes as the producer laid them out."""
    array = (WireOrder * n)()
    for i in range(n):
        array[i].flag = 1
        array[i].value = float(i % 1_000)
        array[i].kind = 2
        array[i].weight = 2.0
    return bytes(array)


_PAYLOAD = _payload(RECORDS)


def before(count):
    records = (WireOrder * RECORDS).from_buffer_copy(_PAYLOAD)
    total = 0.0
    for i in range(count):
        record = records[i]
        total += record.value * record.weight
    return round(total, 3)


def after(count):
    # Same bytes, read through the reordered declaration.
    packed = ctypes.sizeof(PackedOrder)
    buffer = _PAYLOAD[:packed * RECORDS].ljust(packed * RECORDS, b"\x00")
    records = (PackedOrder * RECORDS).from_buffer_copy(buffer)
    total = 0.0
    for i in range(count):
        record = records[i]
        total += record.value * record.weight
    return round(total, 3)


def cases():
    return [("many-records", lambda: (RECORDS,)),
            ("few-records",  lambda: (300,)),
            ("edge",         lambda: (1,))]
