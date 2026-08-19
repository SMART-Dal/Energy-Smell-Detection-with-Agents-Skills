"""C5.S4 Unnecessary Representation Change -- one function serialises, the next
immediately parses.

The card's third repair example and the form it says matters in real code: the
round trip is two full passes and two allocations per row, buying nothing, and
it is invisible from either function alone. Finding it needs the caller and the
callee read together, which is what makes it a reading job rather than a rule
one.
"""

import json


def _store_from_payloads(payloads, sink):
    for payload in payloads:
        record = json.loads(payload)
        sink[record["id"]] = record["value"]
    return len(sink)


def _store_from_records(records, sink):
    for record in records:
        sink[record["id"]] = record["value"]
    return len(sink)


def before(rows):
    payloads = [json.dumps(r) for r in rows]
    return _store_from_payloads(payloads, {})


def after(rows):
    return _store_from_records(rows, {})


def cases():
    return [("large",  lambda: ([{"id": i, "value": i * 2} for i in range(120_000)],)),
            ("normal", lambda: ([{"id": i, "value": i * 2} for i in range(1_200)],)),
            ("edge",   lambda: ([],))]
