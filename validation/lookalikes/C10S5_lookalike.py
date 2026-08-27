"""C10.S5 Inefficient Scope Lookup -- LOOKS THE SAME, IS NOT: the loop calls something
that rebinds the global.

"Assigning a frequently accessed global to a local variable before a loop
converts each access from LOAD_GLOBAL to LOAD_FAST" is the description, and
`C10S5_three_globals_per_iteration` measures the hoist at +38.8%.

The hoist is only a copy of the name's *current* value. `_recalibrate` writes to
`THRESHOLD`, so the loop is reading a moving number on purpose; a local bound
above the loop freezes it at whatever it was on entry and the classification
changes from the first recalibration onward.

The check is whether anything the loop reaches can write the name -- which
includes functions in this module, functions in other modules that were handed
`globals()`, and anything a `global` statement appears in. Where the value
genuinely does not move, the hoist is free; where it does, the global lookup is
what makes the code correct.
"""

THRESHOLD = 500


def _recalibrate(sample):
    global THRESHOLD
    THRESHOLD = 400 + (sample % 200)


def before(values):
    global THRESHOLD
    THRESHOLD = 500
    above = 0
    for index, value in enumerate(values):
        if index and index % 1_000 == 0:
            _recalibrate(value)
        if value > THRESHOLD:
            above += 1
    return above


def after(values):
    global THRESHOLD
    THRESHOLD = 500
    threshold = THRESHOLD                     # hoisted, and then stale
    above = 0
    for index, value in enumerate(values):
        if index and index % 1_000 == 0:
            _recalibrate(value)
        if value > threshold:
            above += 1
    return above


def cases():
    return [("recalibrating", lambda: ([(i * 7919) % 1_000 for i in range(400_000)],)),
            ("steady",        lambda: ([(i * 7919) % 1_000 for i in range(999)],)),
            ("edge",          lambda: ([],))]
