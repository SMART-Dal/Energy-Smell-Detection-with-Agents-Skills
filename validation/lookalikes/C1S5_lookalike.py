"""C1.S5 Resultless Computation -- LOOKS THE SAME, IS NOT: only the last iteration is
read, and every earlier one still had to run.

The description names this shape: "loops where only the final iteration matters
but all prior iterations also execute". `C1S5_last_iteration_only` measures the
repair at +100%, because there `_score` is pure and the last call can be made
directly.

`_score` here keeps a rolling checksum on the scorer, so call number 200_000
does not return what it would have returned as call number 1. The loop is not
computing a value 199_999 times and throwing it away; it is walking a state
machine, and only the last state is reported.

Nothing in the shape distinguishes the two. What distinguishes them is whether
the callee is pure -- which means reading it, not the loop.
"""

class Scorer:
    __slots__ = ("rolling",)

    def __init__(self):
        self.rolling = 0

    def score(self, candidate):
        self.rolling = (self.rolling * 31 + len(candidate)) % 1_000_003
        return self.rolling


def before(candidates):
    scorer = Scorer()
    for candidate in candidates:
        match = scorer.score(candidate)
    return match


def after(candidates):
    scorer = Scorer()
    return scorer.score(candidates[-1])


def cases():
    return [("many-candidates", lambda: ([f"candidate-{i}" for i in range(200_000)],)),
            ("few-candidates",  lambda: ([f"candidate-{i}" for i in range(20)],)),
            ("edge",            lambda: (["only"],))]
