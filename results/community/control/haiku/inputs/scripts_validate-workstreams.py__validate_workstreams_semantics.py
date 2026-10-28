# Inputs for scripts/validate-workstreams.py::validate_workstreams_semantics, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import importlib
import random

validate_workstreams_semantics = importlib.import_module('validate-workstreams').validate_workstreams_semantics

TBD = "tbd"
NONE = "none"


def _people_data(gc, tc, ss):
    return {"teams": {
        "governance-committee": list(gc),
        "technical-committee": list(tc),
        "spec-sponsors": list(ss),
    }}


def _ws(wid, kind="sig", parent=None, people=None, tc_sponsorship=None):
    w = {"id": wid, "kind": kind}
    if parent is not None:
        w["parent"] = parent
    if people is not None:
        w["people"] = people
    if tc_sponsorship is not None:
        w["tcSponsorship"] = tc_sponsorship
    return w


def _case_typical():
    rng = random.Random(0)
    gc = [f"gc{i}" for i in range(8)]
    tc = [f"tc{i}" for i in range(12)]
    ss = [f"ss{i}" for i in range(15)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(500):
        wid = f"ws-{i:04d}"
        parent = None if i < 25 else f"ws-{rng.randrange(i):04d}"
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        if rng.random() < 0.4:
            people.append({"specSponsor": rng.choice(ss)})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


def _case_duplicates():
    rng = random.Random(1)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(600):
        wid = f"dup-{i % 150:04d}"
        parent = f"ghost-{rng.randrange(400):04d}"
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


def _case_deep_chain():
    rng = random.Random(2)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    n = 1200
    ws = []
    for i in range(n):
        wid = f"chain-{i:05d}"
        parent = None if i == 0 else f"chain-{i - 1:05d}"
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


def _case_cycle():
    rng = random.Random(3)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    ws = []
    cycle_len = 400
    for i in range(cycle_len):
        wid = f"cyc-{i:04d}"
        parent = f"cyc-{(i + 1) % cycle_len:04d}"
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        ws.append(_ws(wid, "sig", parent, people))
    for i in range(200):
        wid = f"norm-{i:04d}"
        parent = None if i < 10 else f"norm-{rng.randrange(i):04d}"
        people = [
            {"gcLiaison": rng.choice(gc)},
            {"tcSponsor": {"username": rng.choice(tc)}},
        ]
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


def _case_role_errors():
    rng = random.Random(4)
    gc = [f"gc{i}" for i in range(6)]
    tc = [f"tc{i}" for i in range(6)]
    ss = [f"ss{i}" for i in range(6)]
    pd = _people_data(gc, tc, ss)
    outsiders = [f"out{i}" for i in range(20)]
    ws = []
    for i in range(400):
        wid = f"role-{i:04d}"
        parent = None if i < 20 else f"role-{rng.randrange(i):04d}"
        people = []
        if rng.random() < 0.7:
            people.append({"gcLiaison": rng.choice(outsiders + gc)})
        if rng.random() < 0.7:
            people.append({"tcSponsor": {"username": rng.choice(outsiders + tc)}})
        if rng.random() < 0.5:
            people.append({"specSponsor": rng.choice(outsiders + ss)})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


def _case_collective():
    rng = random.Random(5)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(10)]
    ss = [f"ss{i}" for i in range(8)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(300):
        wid = f"coll-{i:04d}"
        parent = None if i < 10 else f"coll-{rng.randrange(i):04d}"
        if rng.random() < 0.5:
            listed = list(tc)
        else:
            listed = [f"tc{rng.randrange(10)}" for _ in range(rng.randrange(1, 6))]
        people = [{"gcLiaison": rng.choice(gc)}]
        for u in listed:
            people.append({"tcSponsor": {"username": u}})
        ws.append(_ws(wid, "sig", parent, people, tc_sponsorship="collective"))
    return ws, pd


def _case_large_mixed():
    rng = random.Random(6)
    gc = [f"gc{i}" for i in range(10)]
    tc = [f"tc{i}" for i in range(15)]
    ss = [f"ss{i}" for i in range(12)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(2000):
        wid = f"mix-{i:04d}"
        r = rng.random()
        if r < 0.1:
            parent = None
        elif r < 0.2:
            parent = NONE
        elif r < 0.3:
            parent = wid
        elif r < 0.4:
            parent = f"ghost-{i}"
        elif i == 0:
            parent = None
        else:
            parent = f"mix-{rng.randrange(i):04d}"
        people = []
        if rng.random() < 0.8:
            people.append({"gcLiaison": rng.choice(gc + [TBD])})
        if rng.random() < 0.8:
            people.append({"tcSponsor": {"username": rng.choice(tc + [TBD])}})
        if rng.random() < 0.3:
            people.append({"specSponsor": rng.choice(ss)})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


def _case_tbd_none():
    rng = random.Random(7)
    gc = [f"gc{i}" for i in range(5)]
    tc = [f"tc{i}" for i in range(5)]
    ss = [f"ss{i}" for i in range(5)]
    pd = _people_data(gc, tc, ss)
    ws = []
    for i in range(400):
        wid = f"tbd-{i:04d}"
        if i % 3 == 0:
            parent = NONE
        elif i % 3 == 1:
            parent = None
        elif i == 0:
            parent = None
        else:
            parent = f"tbd-{rng.randrange(i):04d}"
        people = [
            {"gcLiaison": TBD},
            {"tcSponsor": {"username": TBD}},
        ]
        if i % 2 == 0:
            people.append({"specSponsor": TBD})
        ws.append(_ws(wid, "sig", parent, people))
    return ws, pd


_C1 = _case_typical()
_C2 = _case_duplicates()
_C3 = _case_deep_chain()
_C4 = _case_cycle()
_C5 = _case_role_errors()
_C6 = _case_collective()
_C7 = _case_large_mixed()
_C8 = _case_tbd_none()


def checks():
    return [
        ("empty", lambda: ([], {})),
        ("single-no-people", lambda: ([{"id": "w1"}], {"teams": {}})),
        ("missing-id", lambda: (
            [{"kind": "sig", "people": [{"gcLiaison": "alice"}]}],
            {},
        )),
    ]


def cases():
    return [
        ("typical-tree", lambda: _C1),
        ("duplicates-missing-parents", lambda: _C2),
        ("deep-parent-chain", lambda: _C3),
        ("parent-cycle", lambda: _C4),
        ("role-membership-errors", lambda: _C5),
        ("collective-tcsponsorship", lambda: _C6),
        ("large-mixed", lambda: _C7),
        ("tbd-and-none", lambda: _C8),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['deep-parent-chain', 'parent-cycle', 'large-mixed', 'typical-tree']
_KEEP_CHECKS = ['empty', 'single-no-people', 'missing-id']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
