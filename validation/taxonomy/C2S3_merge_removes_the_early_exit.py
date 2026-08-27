"""C2.S3 Excessive Modularization in Hot Path -- merging the
layers merges away the early return.

`C2S3_bypass_on_bulk_path` measures the real repair at +68.3%: three frames per
element collapse to none and every layer survives for its other callers.

The layers here are the same three thin functions, but the first one rejects
most of the input. Merging them into a single `transform` -- which is what
"inline the trivial wrappers" produces if the merge is done mechanically --
gives the combined function no place to stop, so the parse and the format run on
rows that used to be discarded after one comparison. Three frames saved per row,
against a parse paid on nine rows in ten that never needed it.

`all-valid` is the case where the merge is fine: nothing was being rejected, so
nothing new runs. The gap between the two readings is the whole finding.
"""

def _valid(row):
    return row["status"] == 0


def _parse(row):
    return sum(ord(c) for c in row["payload"])


def _format(value):
    return f"{value:08d}"


def before(rows):
    out = []
    for row in rows:
        if not _valid(row):
            continue
        out.append(_format(_parse(row)))
    return out


def after(rows):
    out = []
    for row in rows:
        # one function, one frame -- and no early exit left
        value = sum(ord(c) for c in row["payload"])
        formatted = f"{value:08d}"
        if row["status"] == 0:
            out.append(formatted)
    return out


def _rows(n, valid_ratio):
    step = max(1, int(1 / valid_ratio)) if valid_ratio else n + 1
    return [{"status": 0 if i % step == 0 else 1, "payload": f"payload-{i}" * 3}
            for i in range(n)]


def cases():
    return [("mostly-rejected", lambda: (_rows(200_000, 0.1),)),
            ("all-valid",       lambda: (_rows(200_000, 1.0),)),
            ("edge",            lambda: ([],))]
