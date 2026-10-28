```python
import importlib
import random

_build_pr_body = importlib.import_module('move-to-emeritus')._build_pr_body

_ROLES = ["Maintainer", "Approver", "Triager", "Member"]
_TEAMS = [
    "maintainers", "approvers", "triagers", "java-maintainers",
    "python-approvers", "collector-maintainers", "spec-approvers",
    "docs-maintainers", "sdk-triagers", "operator-approvers",
    "ebpf-maintainers", "profiling-approvers",
]
_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"
_CUTOFF = "2024-06-01T00:00:00Z"


def _gen(n, seed, teams_lo=1, teams_hi=3, roles=None, name_len=9,
         team_len=None, unicode_names=False, dup_users=False):
    rng = random.Random(seed)
    if roles is None:
        roles = _ROLES
    out = []
    for _ in range(n):
        if dup_users:
            user = "user%05d" % (rng.randrange(max(1, n // 10)))
        elif unicode_names:
            user = "".join(chr(0x4e00 + rng.randrange(3000)) for _ in range(name_len))
        else:
            user = "".join(rng.choice(_ALNUM) for _ in range(name_len))
        role = rng.choice(roles)
        nt = rng.randint(teams_lo, teams_hi)
        if team_len:
            teams = ["".join(rng.choice(_ALNUM) for _ in range(team_len)) for _ in range(nt)]
        else:
            teams = [rng.choice(_TEAMS) for _ in range(nt)]
        out.append((user, role, teams))
    return out


# Build the workloads once, at import time; the thunks just hand them back.
_TYPICAL = _gen(400, 0)
_LARGE = _gen(30_000, 1)
_MANY_TEAMS = _gen(3_000, 2, teams_lo=8, teams_hi=20)
_LONG_NAMES = _gen(5_000, 3, name_len=40, team_len=45)
_UNICODE = _gen(5_000, 4, unicode_names=True)
_WARNING_CHANGES = _gen(10_000, 5)
_SAME_ROLE = _gen(20_000, 6, teams_lo=2, teams_hi=5, roles=["Maintainer"])
_DUPS = _gen(8_000, 7, dup_users=True)

_WARNING = ("WARNING: Could not determine activity for repo 'collector' "
            "due to a transient API failure; its members were skipped this run.")


def checks():
    return [
        ("empty", lambda: ("community", [], _CUTOFF)),
        ("single", lambda: ("community", [("alice", "Maintainer", ["maintainers"])], _CUTOFF)),
        ("empty-teams", lambda: ("community", [("bob", "Approver", [])], _CUTOFF, "WARNING: x")),
    ]


def cases():
    return [
        ("typical", lambda: ("community", _TYPICAL, _CUTOFF)),
        ("large", lambda: ("community", _LARGE, _CUTOFF)),
        ("many-teams", lambda: ("community", _MANY_TEAMS, _CUTOFF)),
        ("long-names", lambda: ("community", _LONG_NAMES, _CUTOFF)),
        ("unicode", lambda: ("community", _UNICODE, _CUTOFF)),
        ("with-warning", lambda: ("community", _WARNING_CHANGES, _CUTOFF, _WARNING)),
        ("same-role", lambda: ("community", _SAME_ROLE, _CUTOFF)),
        ("duplicates", lambda: ("community", _DUPS, _CUTOFF)),
    ]
```