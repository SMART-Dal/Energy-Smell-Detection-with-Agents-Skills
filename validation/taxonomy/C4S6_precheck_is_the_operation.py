"""C4.S6 Expensive Exception Control Flow -- the pre-check has
to do the work to know the answer.

The description's own example replaces `try: d[key]` with `d.get(key, default)`,
and `C4S6_exception_control_flow` measures the membership form at +73.8% when
the key is usually absent. The precondition is a *cheap* test that predicts the
raise.

There is no cheap test here. The only way to know whether `_decode` raises is to
run `_decode`, so LBYL means decoding twice on every input that succeeds and
once on every input that fails. Where most inputs are valid that is close to
double the work, and the exception it removed was never being raised.

The clause the card needs is the one the description states and readers skip:
the smell is exceptions in a *high-frequency* context, and the repair needs a
predicate strictly cheaper than the operation. Missing either condition turns
the repair into a regression.
"""

def _decode(blob):
    total = 0
    for i, character in enumerate(blob):
        total += (ord(character) * (i + 1)) % 251
    if total % 1_000 == 0:
        raise ValueError(blob)
    return total


def _decodes(blob):
    try:
        _decode(blob)
    except ValueError:
        return False
    return True


def before(blobs):
    out = []
    for blob in blobs:
        try:
            out.append(_decode(blob))
        except ValueError:
            out.append(0)
    return out


def after(blobs):
    out = []
    for blob in blobs:
        if _decodes(blob):                 # the pre-check is the operation
            out.append(_decode(blob))
        else:
            out.append(0)
    return out


def cases():
    blobs = [f"payload-{i}-{i * 7919 % 9973}" for i in range(40_000)]
    return [("mostly-valid", lambda: (list(blobs),)),
            ("short-blobs",  lambda: ([f"p{i}" for i in range(40_000)],)),
            ("edge",         lambda: ([],))]
