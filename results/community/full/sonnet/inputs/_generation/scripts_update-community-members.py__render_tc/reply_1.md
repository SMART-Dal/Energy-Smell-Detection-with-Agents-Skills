```python
import importlib
import random

_mod = importlib.import_module('update-community-members')
render_tc = _mod.render_tc

_UNI = "aàáâäçèéêëìíîïñòóôöùúûüß漢字"


def _build(n, seed, present=1.0, named=1.0, with_company=0.7,
           prefix_len=0, digits=7, dup=0, unicode_names=False):
    """Build (usernames, people) the way the repository's metadata supplies them."""
    rng = random.Random(seed)
    people = {}
    usernames = []
    for i in range(n):
        u = f"member{i:07d}"
        usernames.append(u)
        if rng.random() < present:
            entry = {}
            if rng.random() < named:
                if unicode_names:
                    entry["name"] = "".join(
                        rng.choice(_UNI) for _ in range(rng.randint(1, 12))
                    )
                else:
                    entry["name"] = (
                        "a" * prefix_len
                        + f"{rng.randrange(10 ** digits):0{digits}d}"
                    )
            if rng.random() < with_company:
                entry["company"] = f"Corp {rng.randrange(10 ** 5):05d}"
            people[u] = entry
    if dup:
        for _ in range(dup):
            usernames.append(usernames[rng.randrange(n)])
    return usernames, people


_C1 = _build(4000, 0, present=1.0, named=1.0, with_company=0.9)
_C2 = _build(40000, 1, present=0.95, named=1.0, with_company=0.8)
_C3 = _build(25000, 2, present=0.3, named=0.8, with_company=0.5)
_C4 = _build(20000, 3, present=1.0, named=0.0, with_company=0.7)
_C5 = _build(12000, 4, present=0.9, named=0.9, with_company=0.6, dup=12000)
_C6 = _build(20000, 5, present=1.0, named=1.0, with_company=0.4, prefix_len=60)
_C7 = _build(20000, 6, present=1.0, named=1.0, with_company=0.5, unicode_names=True)
_C8 = _build(25000, 7, present=0.7, named=0.6, with_company=0.05)


def _use(usernames, people):
    _mod.teams = {"technical-committee": usernames}
    _mod.people = people
    return ()


def _use_teams(teams, people):
    _mod.teams = teams
    _mod.people = people
    return ()


def checks():
    return [
        ("no-teams-key", lambda: _use_teams({}, {})),
        ("empty-tc", lambda: _use_teams({"technical-committee": []}, {})),
        ("tc-none", lambda: _use_teams({"technical-committee": None}, {})),
    ]


def cases():
    return [
        ("typical", lambda: _use(_C1[0], _C1[1])),
        ("large", lambda: _use(_C2[0], _C2[1])),
        ("many-missing", lambda: _use(_C3[0], _C3[1])),
        ("no-names", lambda: _use(_C4[0], _C4[1])),
        ("duplicates", lambda: _use(_C5[0], _C5[1])),
        ("long-prefixes", lambda: _use(_C6[0], _C6[1])),
        ("unicode-names", lambda: _use(_C7[0], _C7[1])),
        ("sparse-companies", lambda: _use(_C8[0], _C8[1])),
    ]
```