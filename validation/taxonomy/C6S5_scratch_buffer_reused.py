"""C6.S5 Over-Allocation -- the oversized buffer is allocated
once and the right-sized one is allocated per call.

"Pre-allocating very large fixed-size arrays for functions that typically
process small inputs" is the description, and `C6S5_worst_case_bytearray`
measures the shrink at +31.6% -- because there the buffer is built inside the
function and its zeroing is per-call work.

The buffer here is a module-level scratch area, reused across calls and never
resized. Sizing it to the input means allocating and zeroing a fresh
`bytearray` on every call, which is the cost the over-allocation existed to
avoid. The memory figure improves and the energy figure does not.

The question is where the allocation happens, not how big it is. A worst-case
buffer inside a hot function is waste; the same buffer hoisted out of it is the
standard fix for allocation churn, and shrinking it undoes that fix.
"""

CAPACITY = 1_000_000
_SCRATCH = bytearray(CAPACITY)


def before(payload):
    for i, byte in enumerate(payload):
        _SCRATCH[i] = byte
    return bytes(_SCRATCH[:len(payload)])


def after(payload):
    scratch = bytearray(len(payload))       # "right-sized", and per call
    for i, byte in enumerate(payload):
        scratch[i] = byte
    return bytes(scratch)


def cases():
    small = bytes(range(256)) * 4           # 1 KB, the typical input
    large = bytes(range(256)) * 2_000       # 512 KB
    return [("typical-input", lambda: (small,)),
            ("large-input",   lambda: (large,)),
            ("edge",          lambda: (b"",))]
