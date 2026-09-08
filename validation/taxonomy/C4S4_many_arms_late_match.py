"""C4.S4 Independent Sequential Conditions -- twelve arms, matching late.

The card says the saving is proportional to the number of arms and to how late
the matching one sits. This is the favourable end: twelve `if`s all evaluated
on every pass, against a chain that stops at the first match. Exclusive by
construction, since one value cannot equal two distinct constants.
"""

_GRADES = "ABCDEFGHIJKL"


def before(grades):
    total = 0
    for grade in grades:
        bonus = 0
        if grade == "A": bonus = 12
        if grade == "B": bonus = 11
        if grade == "C": bonus = 10
        if grade == "D": bonus = 9
        if grade == "E": bonus = 8
        if grade == "F": bonus = 7
        if grade == "G": bonus = 6
        if grade == "H": bonus = 5
        if grade == "I": bonus = 4
        if grade == "J": bonus = 3
        if grade == "K": bonus = 2
        if grade == "L": bonus = 1
        total += bonus
    return total


def after(grades):
    total = 0
    for grade in grades:
        if grade == "A": total += 12
        elif grade == "B": total += 11
        elif grade == "C": total += 10
        elif grade == "D": total += 9
        elif grade == "E": total += 8
        elif grade == "F": total += 7
        elif grade == "G": total += 6
        elif grade == "H": total += 5
        elif grade == "I": total += 4
        elif grade == "J": total += 3
        elif grade == "K": total += 2
        elif grade == "L": total += 1
    return total


def cases():
    return [("late-match",  lambda: (["L"] * 300_000,)),
            ("early-match", lambda: (["A"] * 300_000,))]
