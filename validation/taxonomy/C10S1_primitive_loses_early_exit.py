"""C10.S1 Manual Implementation Of Built-ins -- the hand loop wins, because it
stops.

From the project's own sample set. `''.join(a) == ''.join(b)` hands the whole
job to C and materialises both sequences; the element-wise loop returns at the
first mismatch. The card says a primitive that materialises everything loses to
a loop that short-circuits however C-level it is, and this puts the mismatch
position on either side: early, where the loop wins, and absent, where the
primitive should.

`before` is the primitive here, so a *negative* reading is the card being right.
"""

def before(a, b):
    return "".join(a) == "".join(b)


def after(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x != y:
            return False
    return True


def _pair(n, mismatch_at):
    a = [f"s{i % 97}" for i in range(n)]
    b = list(a)
    if mismatch_at is not None:
        b[mismatch_at] = "different"
    return a, b


def cases():
    return [("mismatch-early", lambda: _pair(400_000, 5)),
            ("identical",      lambda: _pair(400_000, None))]
