"""Cases for redundant_bool_branch."""


def above(value, limit):
    # Returns the truth value the comparison already produced.
    if value > limit:
        return True
    else:
        return False


def missing(value, table):
    # The inverted form.
    if value in table:
        return False
    else:
        return True


def is_ready(job):
    # An attribute test, same shape.
    if job.state == "ready":
        return True
    else:
        return False


def classify(value, limit):
    # The branches return different values, not a boolean pair.
    if value > limit:
        return "high"
    else:
        return "low"


def guard(value, limit):
    # No `else`: falling through is not the same as returning False.
    if value > limit:
        return True
    log(value)
    return False


def both_true(flag):
    # The same value on both sides; the branch is redundant for another reason.
    if flag:
        return True
    else:
        return True


def direct(value, limit):
    # Already the repair.
    return value > limit
