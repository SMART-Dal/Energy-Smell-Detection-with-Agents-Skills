"""C4.S6 Exception-Driven Control Flow -- a converter with an exact pre-check.

The card's second repair example, and it says getting the boundary right is
most of the work. Writing this file proved the point twice: the obvious
`value.isdigit()` accepts neither `"1_0"` (which `int` reads as 10, because
underscores are legal between digits) nor rejects `"²"` (which `isdigit`
accepts and `int` refuses). The pre-check below is exact, and the `messy` case
carries every input that broke a sloppier one.

So the three cases answer two different questions: whether replacing the raise
pays at a high raise rate, and whether the *exact* pre-check is still cheap
enough to be worth it once it is exact.
"""

def _int_or_zero(value):
    text = value.strip()
    if text[:1] in "+-":
        text = text[1:]
    if "_" in text:
        # `int` allows underscores between digits: "1_0" is 10, "_1" and "1__0"
        # are errors. Splitting reproduces that rule exactly.
        if not all(part.isdecimal() for part in text.split("_")):
            return 0
    elif not text.isdecimal():
        # `isdecimal` rather than `isdigit`: "²".isdigit() is True and int("²")
        # raises, so `isdigit` would change behaviour on it.
        return 0
    return int(value)


def before(values):
    out = []
    for value in values:
        try:
            out.append(int(value))
        except ValueError:
            out.append(0)
    return out


def after(values):
    return [_int_or_zero(value) for value in values]


def cases():
    return [("mostly-raises", lambda: ([f"x{i}" for i in range(120_000)],)),
            ("mostly-valid",  lambda: ([str(i) for i in range(120_000)],)),
            ("messy",         lambda: ([" 12 ", "+3", "-4", "1_0", "1__0", "_1",
                                        "1_", "", "  ", "5x", "²", "٣"] * 10_000,))]
