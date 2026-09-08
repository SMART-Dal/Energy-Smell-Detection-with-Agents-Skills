"""C4.S4 Independent Sequential Conditions -- two arms, which the card calls
close to advisory.

The adversarial end of the same claim: with two arms the chain saves at most
half a comparison per pass. If this reads near zero while the twelve-arm case
reads well above it, the card can say where the line is instead of saying
"count the arms".
"""

def before(values, lower, upper):
    assert upper > lower
    below, above = 0, 0
    for x in values:
        if x > upper:
            above += 1
        if x < lower:
            below += 1
    return below, above


def after(values, lower, upper):
    assert upper > lower
    below, above = 0, 0
    for x in values:
        if x > upper:
            above += 1
        elif x < lower:
            below += 1
    return below, above


def cases():
    return [("large",  lambda: ([(i * 7919) % 1000 for i in range(500_000)], 100, 900)),
            ("normal", lambda: ([(i * 7919) % 1000 for i in range(5_000)], 100, 900))]
