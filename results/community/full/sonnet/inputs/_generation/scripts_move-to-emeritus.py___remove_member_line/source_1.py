import importlib
import random

_remove_member_line = importlib.import_module('move-to-emeritus')._remove_member_line

_FIRST = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi",
          "Ivan", "Judy", "Ken", "Leo", "Mona", "Nina", "Oscar", "Peggy",
          "Quinn", "Rita", "Sam", "Tina"]
_LAST = ["Smith", "Jones", "Brown", "Garcia", "Miller", "Davis", "Rodriguez",
         "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
         "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez"]


def _display_name(rng):
    return f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"


def _member_line(rng, username):
    joined = f"20{rng.randint(10, 24)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    return f"- [{_display_name(rng)}](https://github.com/{username}) - joined {joined}\n"


def _make_readme(section_name, usernames, header_level=2, leading=(), trailing=True, seed=0):
    rng = random.Random(seed)
    parts = ["# Community\n\nWe are a community of contributors.\n\n"]
    for name, users in leading:
        parts.append(f"{'#' * header_level} {name}\n\n")
        parts.append("".join(_member_line(rng, u) for u in users))
        parts.append("\n")
    parts.append(f"{'#' * header_level} {section_name}\n\n")
    parts.append("".join(_member_line(rng, u) for u in usernames))
    parts.append("\n")
    if trailing:
        parts.append(f"{'#' * header_level} Resources\n\nSee the docs and the contributing guide.\n")
    return "".join(parts)


def _users(n, prefix="user"):
    return [f"{prefix}{i}" for i in range(n)]


# --- case 1: small section, hit on the first line -------------------------
_R1 = _make_readme("Triagers", _users(200), seed=1)

# --- case 2: large section, hit on the last line --------------------------
_u2 = _users(100_000)
_u2[99_999] = "targetuser"
_R2 = _make_readme("Approvers", _u2, seed=2)

# --- case 3: large section, complete miss --------------------------------
_R3 = _make_readme("Maintainers", _users(100_000), seed=3)

# --- case 4: section not present at all, big multi-section readme ---------
_R4 = _make_readme(
    "Archived Maintainers",
    _users(20_000),
    leading=[("Triagers", _users(20_000, "tri")),
             ("Approvers", _users(20_000, "app")),
             ("Maintainers", _users(20_000, "main")),
             ("Emeritus Maintainers", _users(20_000, "emer"))],
    seed=4,
)

# --- case 5: many duplicate lines for the same user ----------------------
_u5 = _users(60_000)
for i in range(0, 60_000, 1_000):
    _u5[i] = "dupuser"
_R5 = _make_readme("Triagers", _u5, seed=5)

# --- case 6: case-insensitive username match -----------------------------
_u6 = _users(60_000)
_u6[30_000] = "MixedCaseUser"
_R6 = _make_readme("Approvers", _u6, seed=6)

# --- case 7: level-3 section, hit near the end ---------------------------
_u7 = _users(80_000)
_u7[79_999] = "level3target"
_R7 = _make_readme("Maintainers", _u7, header_level=3, seed=7)

# --- case 8: target section runs to the end of the readme ----------------
_u8 = _users(100_000)
_u8[50_000] = "endtarget"
_R8 = _make_readme("Triagers", _u8, trailing=False, seed=8)


def checks():
    return [
        ("empty-readme", lambda: ("", "Triagers", "alice")),
        ("no-such-section",
         lambda: ("# Title\n\n## Other\n- [A](https://github.com/a) - x\n", "Triagers", "a")),
        ("user-absent",
         lambda: ("# T\n\n## Triagers\n- [A](https://github.com/a) - x\n", "Triagers", "nobody")),
    ]


def cases():
    return [
        ("small-hit-first", lambda: (_R1, "Triagers", "user0")),
        ("large-hit-last", lambda: (_R2, "Approvers", "targetuser")),
        ("large-miss", lambda: (_R3, "Maintainers", "ghostuser")),
        ("section-not-found", lambda: (_R4, "Archived Maintainers", "user5")),
        ("duplicate-lines", lambda: (_R5, "Triagers", "dupuser")),
        ("case-insensitive", lambda: (_R6, "Approvers", "mixedcaseuser")),
        ("level3-section", lambda: (_R7, "Maintainers", "level3target")),
        ("section-at-eof", lambda: (_R8, "Triagers", "endtarget")),
    ]
