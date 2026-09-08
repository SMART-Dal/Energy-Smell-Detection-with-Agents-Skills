"""C10.S3 Missing Bulk Operations -- an element-at-a-time transfer against one
bulk call.

`lst.append(x)` in a Python loop resolves the attribute and makes a call per
element; `extend` does one of each and copies the pointers in C. The card calls
this the most reliably positive family in the taxonomy, so this is the plain
confirmation -- and the small case says how many elements it takes.
"""

def before(target, source):
    for item in source:
        target.append(item)
    return len(target)


def after(target, source):
    target.extend(source)
    return len(target)


def cases():
    return [("large",  lambda: ([], list(range(1_000_000)))),
            ("normal", lambda: ([], list(range(1_000))))]
