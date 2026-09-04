"""Cases for expensive_comparison."""


def same_members(first, second):
    # Two sorts and two lists to answer yes or no.
    return sorted(first) == sorted(second)


def same_text(left, right):
    # Two conversions inside a loop, paid per element.
    matches = []
    for a, b in zip(left, right):
        if str(a) == str(b):
            matches.append(a)
    return matches


def same_set(first, second):
    # `set()` builds two containers for one comparison.
    return set(first) == set(second)


def compare_directly(first, second):
    # No object built at all.
    return first == second


def sorted_for_output(values):
    # `sorted` is used for its result, not for a comparison.
    return sorted(values)


def compare_lengths(first, second):
    # `len` is not in the expensive set, and it should not be.
    return len(first) == len(second)


def sorted_then_compared(first, second):
    # Naming the operands changes nothing: the same two sorts are paid for the
    # same yes or no, and neither name is read anywhere else.
    left = sorted(first)
    right = sorted(second)
    return left == right


def sorted_and_returned(first, second):
    # `left` has a second reader, so the sort was not built for the comparison
    # alone and there is nothing to take away.
    left = sorted(first)
    if left == sorted(second):
        return []
    return left


def sorted_then_rebound(values, extra):
    # `left` is a slot, not an alias -- the name does not stand for one call.
    left = sorted(values)
    if extra:
        left = sorted(extra)
    return left == sorted(extra)


def same_lines(left, right):
    # Two whole strings built to answer one yes or no.
    return "".join(left) == "".join(right)


def check_status(user_id, error_obj):
    # A type conversion against a literal is the ordinary way to compare an
    # int to text. There is nothing built and thrown away -- the conversion
    # *is* the comparison.
    if str(user_id) == "1001":
        grant_admin()
    if str(error_obj) == "Timeout":
        retry()


def names_match(results):
    # The same with a set display on the other side.
    return set(results) == {"baseline", "volatility", "slippage"}
