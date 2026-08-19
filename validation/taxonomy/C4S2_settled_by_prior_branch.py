"""C4.S2 Redundant Conditional Evaluation -- a prior branch settles half the
next condition.

Reaching the second `if` means `first and last` was false, so once `last` holds
there, `not first` is already known. That is one operand, worth a bytecode, so
the measured entry points are drivers that evaluate it many times over a tiny
input -- which is what `scales_with_calls` means and how a claim this small has
to be sized.

Included because it is the shape the description is really about, and because
nothing syntactic separates it from two genuinely independent tests: what
settles it is a fact about the booleans.
"""

def _search_before(nums, target):
    first_exists = bool(nums) and nums[0] == target
    last_exists = bool(nums) and nums[-1] == target
    if first_exists and last_exists:
        return -1
    if last_exists and not first_exists:
        return nums[0]
    return 0


def _search_after(nums, target):
    first_exists = bool(nums) and nums[0] == target
    last_exists = bool(nums) and nums[-1] == target
    if first_exists and last_exists:
        return -1
    if last_exists:
        return nums[0]
    return 0


def before(nums, target, repeats):
    total = 0
    for _ in range(repeats):
        total += _search_before(nums, target)
    return total


def after(nums, target, repeats):
    total = 0
    for _ in range(repeats):
        total += _search_after(nums, target)
    return total


def cases():
    return [
        # reaches the second test and takes it: the redundant operand is evaluated
        ("last-only", lambda: ([9, 1, 2, 3], 3, 1_000_000)),
        # never reaches the second test's body: the operand is still evaluated
        ("neither",   lambda: ([1, 2, 3, 4], 99, 1_000_000)),
        ("few-calls", lambda: ([3, 1, 2, 3], 3, 100)),
    ]
