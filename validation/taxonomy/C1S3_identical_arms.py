"""C1.S3 Redundant Control Flow -- two arms that compute the same answer.

The other C1.S3 case collapses `if c: return True else: return False`. This one
keeps a branch whose arms differ textually and not in effect, which is the
shape the description names first and which no rule matching on `return True`
would see.
"""

def before(values, limit):
    out = []
    for value in values:
        if value > limit:
            out.append(value * 2)
        elif value == limit:
            out.append(value * 2)
        else:
            out.append(value * 2)
    return out


def after(values, limit):
    out = []
    for value in values:
        out.append(value * 2)
    return out


def cases():
    return [("large",  lambda: (list(range(500_000)), 250_000)),
            ("normal", lambda: (list(range(5_000)), 2_500)),
            ("edge",   lambda: ([], 0))]
