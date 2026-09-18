"""C5.S1 Inefficient Data Structure Choice -- records as dicts, read as fields.

The taxonomy's own second example for this root cause, which had no
implementation: "storing records as dicts of dicts when a list of namedtuples
would provide faster attribute access and lower memory overhead".

The other measured files in this root cause change the container to change the
cost of *membership* or of *popping*. This one changes it to change the cost of
a field read: a dict lookup hashes the key string and probes a table, where a
namedtuple field is a fixed index into a tuple resolved at class creation.

The memory half of the claim is the larger one and is not what the window
measures: a namedtuple carries no per-instance dict, so a million records is
tens of megabytes rather than hundreds. The reading here is the access cost
alone, and the card should say so rather than claim both.
"""

from collections import namedtuple

Record = namedtuple("Record", ("id", "name", "score"))


def before(rows):
    total = 0
    for row in rows:
        total += row["id"] + row["score"]
    return total


def after(rows):
    records = [Record(r["id"], r["name"], r["score"]) for r in rows]
    total = 0
    for record in records:
        total += record.id + record.score
    return total


def _rows(n):
    return [{"id": i, "name": f"n{i}", "score": i % 97} for i in range(n)]


def cases():
    return [("many-reads", lambda: (_rows(300_000),)),
            ("few-reads",  lambda: (_rows(3_000),))]
