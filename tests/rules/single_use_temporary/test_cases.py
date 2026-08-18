"""Cases for single_use_temporary."""


def render(template, row):
    # Bound only to be returned on the next line.
    result = template.format(**row)
    return result


def tenure_days(user):
    # The name is the only thing explaining the arithmetic, but the shape is
    # identical -- the rule reports it and stays advisory.
    days = (today() - user.joined).days
    return days


def total(rows):
    # Used twice, so the binding is doing work.
    running = sum(r.value for r in rows)
    log(running)
    return running


def widen(value):
    # Something stands between the store and the return.
    scaled = value * 2
    check(value)
    return scaled


def direct(template, row):
    # Already inlined.
    return template.format(**row)


def two_names(row):
    # `first` is dead, but `second` is bound and returned: still this.
    first = row.a
    second = row.b
    return second
