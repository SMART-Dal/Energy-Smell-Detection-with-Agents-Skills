"""C10.S1 Skipping Optimized Built-ins -- the built-in called once per element,
on two scalars.

From Javad's OveruseOfLoops/SumMaxSubsequence, where the refactoring runs in the
direction this card does not expect: it *removes* `max`.

`C10S1_manual_sum` measures the claim where it holds -- `sum(xs)` replaces the
whole loop, so one C-level loop replaces N interpreted iterations, and it reads
+88.7%. Here the loop stays. `max(curr_max, curr_sum)` replaces one
`COMPARE_OP` and one conditional store with a global lookup, a tuple of
arguments, a call and a return, N times over. The built-in is still C, and C
called N times from Python is not the same thing as C looping N times.

`before` is the hand-written comparison, so a negative reading is the repair
losing.

The question is where the loop boundary sits relative to the built-in. A
built-in that consumes the iterable replaces the loop; a built-in called
*inside* the loop on two scalars only adds a frame to it -- and the same is true
of `min`, `abs`, `len` on a name that never changes, and `sorted` on a pair.
"""

def before(values):
    best = float("-inf")
    running = 0
    for value in values:
        running += value
        if running > best:
            best = running
        if running < 0:
            running = 0
    return best


def after(values):
    best = float("-inf")
    running = 0
    for value in values:
        running += value
        best = max(best, running)
        if running < 0:
            running = 0
    return best


def cases():
    return [("large",  lambda: ([((i * 7919) % 201) - 100 for i in range(1_000_000)],)),
            ("normal", lambda: ([((i * 7919) % 201) - 100 for i in range(10_000)],))]
