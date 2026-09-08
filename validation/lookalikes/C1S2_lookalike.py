"""C1.S2 Redundant Assignment -- LOOKS THE SAME, IS NOT: the conversion is idempotent
on almost every element, and that is not the same as idempotent.

The taxonomy names this shape directly: "repeating an idempotent operation
(e.g., converting an already-integer value with int())". `C1S2_idempotent_
conversion` measures exactly that and saves 58.9%, because there every element
really is an `int`.

Here 999 of every 1000 elements are `int` too. The thousandth is the string a
CSV reader produced, and `int()` is the only thing turning it into a number.
Deleting the "redundant" conversion does not raise -- `total += "7"` does, but
only after the sum has already been a str for a while, and on the `all-numeric`
case it never raises at all. That is what makes this worth a card entry: the
repair passes every test built from the common input.

The check is not "is this conversion usually redundant". It is "is there any
element for which it is not".
"""

def before(values):
    total = 0
    for value in values:
        value = int(value)              # looks idempotent; is not, once
        total += value
    return total


def after(values):
    total = 0
    for value in values:
        total += value
    return total


def _mostly_ints(n, strays):
    values = list(range(n))
    for position in range(0, n, max(1, n // strays)):
        values[position] = str(values[position])
    return values


def cases():
    return [("one-stray-in-a-thousand", lambda: (_mostly_ints(200_000, 200),)),
            ("all-numeric",             lambda: (list(range(200_000)),))]
