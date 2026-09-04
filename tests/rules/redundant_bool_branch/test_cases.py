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


def is_configured(settings):
    # A truthiness test, not a boolean one: `return settings.get("api_key")`
    # hands back the key. The advice has to say `bool(...)`, which it now does.
    if settings.get("api_key"):
        return True
    else:
        return False


def validate_token(token):
    # An early-return guard has no `else`, and requiring one skipped the
    # commonest way this is written. The answer is `bool(token)`.
    if not token:
        return False
    return True
