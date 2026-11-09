# Inputs for scripts/update-sig-tables.py::render_group, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random


def _meeting(rng):
    m = {
        "schedule": "Weekly, %s at %02d:00 PT"
        % (rng.choice(["Mon", "Tue", "Wed", "Thu", "Fri"]), rng.randrange(8, 20)),
    }
    if rng.random() < 0.8:
        m["gDocNotes"] = "1" + "".join(
            rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
            for _ in range(43)
        )
    if rng.random() < 0.7:
        m["calendarInviteGroup"] = "otel-%d" % rng.randrange(1000)
    return {"meeting": m}


def _sig(name, rng, n_meeting=1, n_slack=1, n_disc=0, n_gc=0, n_tc=0, n_spec=0,
         collective=False):
    ws = {"name": name, "resources": [], "people": []}
    for _ in range(n_meeting):
        ws["resources"].append(_meeting(rng))
    for _ in range(n_slack):
        ws["resources"].append(
            {"slack": {"name": "#chan-%d" % rng.randrange(100000),
                       "id": "C%010d" % rng.randrange(10 ** 10)}}
        )
    for _ in range(n_disc):
        ws["resources"].append(
            {"githubDiscussion":
             "https://github.com/open-telemetry/community/discussions/%d"
             % rng.randrange(100000)}
        )
    for _ in range(n_gc):
        ws["people"].append({"gcLiaison": "gc%d" % rng.randrange(1000000)})
    for _ in range(n_tc):
        sp = {"username": "tc%d" % rng.randrange(1000000)}
        if rng.random() < 0.6:
            sp["level"] = rng.choice(["collector", "contributor", "tbd"])
        ws["people"].append({"tcSponsor": sp})
    for _ in range(n_spec):
        ws["people"].append({"specSponsor": "spec%d" % rng.randrange(1000000)})
    if collective:
        ws["tcSponsorship"] = "collective"
    return ws


def _build(n, seed, name_fn, **kw):
    rng = random.Random(seed)
    return [_sig(name_fn(i, rng), rng, **kw) for i in range(n)]


# ---------------------------------------------------------------------------
# module level input construction (never timed)
# ---------------------------------------------------------------------------

_CASE1 = _build(350, 11, lambda i, r: "SIG %d" % i,
                n_meeting=1, n_slack=1, n_disc=20, n_gc=10, n_tc=10, n_spec=5)

_CASE2 = _build(100, 12, lambda i, r: "Deep SIG %d" % i,
                n_meeting=3, n_slack=2, n_disc=300, n_gc=50, n_tc=50, n_spec=50)

_CASE3 = _build(200, 13, lambda i, r: "Slack SIG %d" % i,
                n_meeting=1, n_slack=3, n_disc=10, n_gc=5, n_tc=5, n_spec=5)

_CASE4 = _build(250, 14, lambda i, r: "People SIG %d" % i,
                n_meeting=1, n_slack=1, n_disc=5, n_gc=40, n_tc=40, n_spec=40)


def _build_collective(n, seed):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append(_sig("Collective SIG %d" % i, rng,
                        n_meeting=1, n_slack=1, n_disc=15,
                        n_gc=8, n_tc=8, n_spec=8,
                        collective=(i % 2 == 0)))
    return out


_CASE5 = _build_collective(300, 15)


def _build_bare(n, seed):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        ws = {"name": "Bare SIG %d" % i, "resources": [], "people": []}
        ws["resources"].append(
            {"meeting": {"schedule": "Biweekly, %s" % rng.choice(["Mon", "Wed", "Fri"])}}
        )
        for _ in range(100):
            ws["resources"].append(
                {"githubDiscussion":
                 "https://github.com/open-telemetry/community/discussions/%d"
                 % rng.randrange(100000)}
            )
        out.append(ws)
    return out


_CASE6 = _build_bare(400, 16)

_SPECIAL_NAMES = [
    "[Specification](https://github.com/open-telemetry/opentelemetry-specification) SIG",
    "SIG: C++ / Rust / Go",
    "Unicode & Special SIG",
    "  Spaced   Name  ",
    "ALL CAPS SIG",
    "sig-with-many-hyphens-and-numbers-1234567890",
    "Mixed CASE Sig 42",
]


def _special_name(i, rng):
    return "%s %d" % (_SPECIAL_NAMES[i % len(_SPECIAL_NAMES)], i)


_CASE7 = _build(250, 17, _special_name,
                n_meeting=1, n_slack=1, n_disc=10, n_gc=5, n_tc=5, n_spec=5)

_CASE8 = _build(200, 18, lambda i, r: "Mixed SIG %d" % i,
                n_meeting=2, n_slack=1, n_disc=150, n_gc=30, n_tc=30, n_spec=30)


# ---------------------------------------------------------------------------
# test definitions
# ---------------------------------------------------------------------------

def checks():
    return [
        ("empty-group", lambda: ("Empty Group", [])),
        ("one-element",
         lambda: ("Solo Group",
                  [{"name": "Solo SIG", "resources": [], "people": []}])),
        ("none-sigs", lambda: ("None Group", None)),
    ]


def cases():
    return [
        ("many-sigs", lambda: ("Specification SIGs", _CASE1)),
        ("deep-resources", lambda: ("Implementation SIGs", _CASE2)),
        ("slack-heavy", lambda: ("Cross-Cutting SIGs", _CASE3)),
        ("people-heavy", lambda: ("Localization Teams", _CASE4)),
        ("collective-sponsors", lambda: ("Collective SIGs", _CASE5)),
        ("bare-meetings", lambda: ("Bare SIGs", _CASE6)),
        ("special-names", lambda: ("Special SIGs", _CASE7)),
        ("mixed-large", lambda: ("Mixed SIGs", _CASE8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['people-heavy', 'mixed-large', 'deep-resources', 'bare-meetings']
_KEEP_CHECKS = ['empty-group', 'one-element', 'none-sigs']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
