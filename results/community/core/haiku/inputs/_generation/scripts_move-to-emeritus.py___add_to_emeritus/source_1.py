import importlib
import os
import random
import sys

try:
    _mod = importlib.import_module('move-to-emeritus')
except ModuleNotFoundError:
    _scripts = os.path.join(os.getcwd(), 'scripts')
    if os.path.isdir(_scripts):
        sys.path.insert(0, _scripts)
    _mod = importlib.import_module('move-to-emeritus')

_add_to_emeritus = _mod._add_to_emeritus


def _member_line(name, username, marker='-'):
    return f"{marker} [{name}](https://github.com/{username})"


def _make_readme_with_section(
    n_members,
    header_level=3,
    title="Emeritus Maintainers",
    marker='-',
    seed=0,
    mixed=False,
    extra_lines=True,
):
    rng = random.Random(seed)
    lines = ["# Community", "", "Intro text.", "", "## Maintainers", ""]
    for i in range(100):
        lines.append(_member_line(f"Maint {i}", f"maint{i}", '-'))
    lines.append("")

    hashes = "#" * header_level
    lines.append(f"{hashes} {title}")
    lines.append("")

    members = []
    for i in range(n_members):
        m = marker
        if mixed:
            m = rng.choice(['-', '*', '+'])
        name = f"Person {rng.randrange(100000):05d} {rng.choice(['Alpha', 'beta', 'Gamma', 'delta'])}"
        username = f"user{i}_{rng.randrange(10000)}"
        members.append(_member_line(name, username, m))

    rng.shuffle(members)
    if extra_lines and n_members > 10:
        members.insert(5, "Some explanatory text.")
        members.insert(n_members // 2, "")
        members.insert(n_members - 5, "Another note.")

    lines.extend(members)
    lines.append("")

    if header_level == 2:
        lines.append("### Notes")
        lines.append("Some notes about emeritus.")
        lines.append("")

    lines.append("## Approvers")
    lines.append("")
    for i in range(50):
        lines.append(_member_line(f"App {i}", f"app{i}", '-'))
    lines.append("")
    lines.append("## Licenses")
    lines.append("")
    lines.append("License text.")
    return "\n".join(lines)


def _make_readme_duplicate(n_members=8000, seed=6):
    rng = random.Random(seed)
    lines = ["# Community", "", "## Maintainers", ""]
    for i in range(100):
        lines.append(_member_line(f"Maint {i}", f"maint{i}", '-'))
    lines.append("")
    lines.append("### Emeritus Maintainers")
    lines.append("")
    lines.append("- [Known User](https://github.com/known_user)")

    for i in range(n_members):
        name = f"Person {rng.randrange(100000):05d} {rng.choice(['Alpha', 'beta', 'Gamma'])}"
        username = f"user{i}_{rng.randrange(10000)}"
        lines.append(_member_line(name, username, '-'))

    lines.append("")
    lines.append("## Approvers")
    lines.append("")
    for i in range(50):
        lines.append(_member_line(f"App {i}", f"app{i}", '-'))
    lines.append("")
    lines.append("## Licenses")
    lines.append("")
    lines.append("License text.")
    return "\n".join(lines)


def _make_readme_no_emeritus(n_sections=200, marker=None, seed=0):
    rng = random.Random(seed)
    lines = ["# Community", ""]
    for s in range(n_sections):
        lines.append(f"## Section {s}")
        lines.append("")
        for i in range(20):
            lines.append(_member_line(f"Name {s}-{i}", f"user{s}_{i}", '-'))
        lines.append("")

    if marker == "learn":
        lines.append("Learn more about roles")
        lines.append("")
    elif marker == "licenses":
        lines.append("## Licenses")
        lines.append("")
        lines.append("License text.")
        lines.append("")
    elif marker == "license":
        lines.append("## License")
        lines.append("")
        lines.append("License text.")
        lines.append("")

    lines.append("## Footer")
    lines.append("")
    lines.append("Footer text.")
    return "\n".join(lines)


_README_LARGE = _make_readme_with_section(8000, header_level=3, seed=1)
_README_LEVEL2 = _make_readme_with_section(6000, header_level=2, seed=2)
_README_MIXED = _make_readme_with_section(7000, header_level=3, seed=3, mixed=True)
_README_CASE = _make_readme_with_section(5000, header_level=3, title="emeritus maintainers", seed=4)
_README_DUP = _make_readme_duplicate(8000, seed=5)
_README_NO_LEARN = _make_readme_no_emeritus(200, marker="learn", seed=6)
_README_NO_LICENSES = _make_readme_no_emeritus(200, marker="licenses", seed=7)
_README_NO_NONE = _make_readme_no_emeritus(200, marker=None, seed=8)

_NEW_ENTRY = "- [New Person](https://github.com/new_person)"
_DUP_ENTRY = "- [Known User](https://github.com/known_user)"
_TITLE = "Emeritus Maintainers"


def checks():
    return [
        ("empty-readme", lambda: ("", _TITLE, _NEW_ENTRY)),
        (
            "section-no-members",
            lambda: (
                "# Community\n\n### Emeritus Maintainers\n\n## Approvers\n",
                _TITLE,
                _NEW_ENTRY,
            ),
        ),
        (
            "duplicate-small",
            lambda: (
                "# Community\n\n### Emeritus Maintainers\n\n"
                "- [Old](https://github.com/old)\n\n## Approvers\n",
                _TITLE,
                "- [Old](https://github.com/old)",
            ),
        ),
    ]


def cases():
    return [
        ("existing-large", lambda: (_README_LARGE, _TITLE, _NEW_ENTRY, 3)),
        ("existing-level2", lambda: (_README_LEVEL2, _TITLE, _NEW_ENTRY, 2)),
        ("existing-mixed-markers", lambda: (_README_MIXED, _TITLE, _NEW_ENTRY, 3)),
        ("existing-case-insensitive", lambda: (_README_CASE, _TITLE, _NEW_ENTRY, 3)),
        ("existing-duplicate", lambda: (_README_DUP, _TITLE, _DUP_ENTRY, 3)),
        ("missing-learn-more", lambda: (_README_NO_LEARN, _TITLE, _NEW_ENTRY, 3)),
        ("missing-licenses", lambda: (_README_NO_LICENSES, _TITLE, _NEW_ENTRY, 3)),
        ("missing-none", lambda: (_README_NO_NONE, _TITLE, _NEW_ENTRY, 3)),
    ]
