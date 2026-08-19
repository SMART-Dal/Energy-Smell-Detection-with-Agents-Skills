"""C1.S4 Repeated Computation -- one expensive call made twice per invocation.

The other C1.S4 case repeats a cheap `len(str(r))` per element, so its saving
is a per-element constant. This one repeats a parse once per call, which is the
form the card says is worth reporting whatever the loop count -- the saving is
the whole of the second parse.
"""

def _parse_manifest(text):
    entries = {}
    for line in text.split(";"):
        if "=" in line:
            key, _, value = line.partition("=")
            entries[key] = int(value)
    return entries


def before(text):
    if _parse_manifest(text)["version"] < 2:
        return None
    return _parse_manifest(text)["entries"]


def after(text):
    manifest = _parse_manifest(text)
    if manifest["version"] < 2:
        return None
    return manifest["entries"]


def _manifest(n):
    return "version=9;entries=%d;" % n + ";".join(f"k{i}={i}" for i in range(n))


def cases():
    return [("large",  lambda: (_manifest(20_000),)),
            ("normal", lambda: (_manifest(200),)),
            ("edge",   lambda: ("version=1;entries=0;",))]
