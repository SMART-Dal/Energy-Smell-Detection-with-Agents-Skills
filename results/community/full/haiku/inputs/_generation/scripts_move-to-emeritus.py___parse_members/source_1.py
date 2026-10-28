import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members

_NAMES = [
    "Alice Smith", "Bob Jones", "Carol White", "David Brown", "Eve Davis",
    "Frank Miller", "Grace Lee", "Henry Wilson", "Ivy Chen", "Jack Taylor",
    "Kara Novak", "Liam O'Brien", "Mia Garcia", "Noah Muller", "Olivia Rossi",
    "Pablo Fernandez", "Quinn Adams", "Rosa Kim", "Sam Patel", "Tina Nguyen",
    "Umar Hassan", "Vera Petrova", "Wes Clark", "Xena Papadopoulos",
    "Yuki Tanaka", "Zara Ali", "Zoe Angstrom", "Jose Maria Lopez",
    "Ann-Marie O'Neil", "Bjorn Thorsson", "Nguyen Van A", "Mary-Jane Watson",
]

_UNICODE_NAMES = [
    "José María López", "李雷", "王小明", "Björn Þórsson", "Nguyễn Văn A",
    "🦊 Fox Dev", "Zoë Ångström", "Ann-Marie O'Neil", "Müller, Hans",
    "Пётр Иванов", "محمد علي", "שלום כהן", "Emoji 🚀 Rocket",
    "C++ Guru", "Name (with parens)", "O'Brien, Sean", "Ana-Maria Popescu",
    "François Lefèvre", "李小龙", "山田太郎",
]

_DESC_WORDS = [
    "maintainer", "emeritus", "since", "2019", "2020", "SIG", "Docs",
    "release", "team", "lead", "contributor", "Kubernetes", "steering",
    "committee", "alumni", "reviewer", "approver", "owner", "and", "the",
    "working", "group", "subproject", "inactive", "former",
]

_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789-"


def _username(rng):
    n = rng.randint(3, 16)
    s = "".join(rng.choice(_ALNUM) for _ in range(n)).strip("-")
    return s or "user"


def _desc(rng, words):
    return " ".join(rng.choice(_DESC_WORDS) for _ in range(words))


def _entry(rng, marker, trailing):
    name = rng.choice(_NAMES)
    user = _username(rng)
    line = f"{marker} [{name}](https://github.com/{user})"
    if trailing:
        line += ", " + _desc(rng, rng.randint(1, 6))
    return line


def _build_typical():
    rng = random.Random(0)
    lines = ["# Emeritus Maintainers", "",
             "The following members have moved to emeritus:", ""]
    for _ in range(4000):
        lines.append(_entry(rng, "-", rng.random() < 0.3))
    lines.append("")
    return "\n".join(lines)


def _build_large_mixed():
    rng = random.Random(1)
    lines = ["## Emeritus", ""]
    for _ in range(25000):
        lines.append(_entry(rng, rng.choice("-*+"), rng.random() < 0.5))
    return "\n".join(lines)


def _build_mostly_misses():
    rng = random.Random(2)
    lines = ["# Section", ""]
    for _ in range(15000):
        r = rng.random()
        name = rng.choice(_NAMES)
        user = _username(rng)
        if r < 0.01:
            lines.append(_entry(rng, "-", rng.random() < 0.5))
        elif r < 0.18:
            lines.append(f"- [{name}](http://github.com/{user})")
        elif r < 0.32:
            lines.append(f"- [{name}](https://gitlab.com/{user})")
        elif r < 0.46:
            lines.append(f"- [{name}](https://github.com/{user}),")
        elif r < 0.60:
            lines.append(f"  - [{name}](https://github.com/{user})")
        elif r < 0.72:
            lines.append(f"* [{name}] (https://github.com/{user})")
        elif r < 0.82:
            lines.append(f"- [{name}](https://github.com/{user}) ")
        elif r < 0.90:
            lines.append("")
        else:
            lines.append(f"Some prose about {name} and their past work on the project.")
    return "\n".join(lines)


def _build_long_lines():
    rng = random.Random(3)
    lines = []
    for _ in range(3000):
        name = " ".join(rng.choice(_NAMES) for _ in range(rng.randint(3, 8)))
        user = _username(rng)
        desc = _desc(rng, rng.randint(30, 60))
        lines.append(f"- [{name}](https://github.com/{user}), {desc}")
    return "\n".join(lines)


def _build_no_trailing():
    rng = random.Random(4)
    lines = []
    for _ in range(15000):
        lines.append(_entry(rng, "-", False))
    return "\n".join(lines)


def _build_unicode():
    rng = random.Random(5)
    lines = []
    for _ in range(8000):
        name = rng.choice(_UNICODE_NAMES)
        user = _username(rng)
        if rng.random() < 0.5:
            lines.append(f"- [{name}](https://github.com/{user}), "
                         f"{_desc(rng, rng.randint(1, 4))}")
        else:
            lines.append(f"* [{name}](https://github.com/{user})")
    return "\n".join(lines)


def _build_duplicates():
    rng = random.Random(6)
    users = [_username(rng) for _ in range(40)]
    lines = []
    for _ in range(10000):
        user = rng.choice(users)
        name = rng.choice(_NAMES)
        marker = rng.choice("-*+")
        if rng.random() < 0.4:
            lines.append(f"{marker} [{name}](https://github.com/{user}), "
                         f"{_desc(rng, rng.randint(1, 3))}")
        else:
            lines.append(f"{marker} [{name}](https://github.com/{user})")
    return "\n".join(lines)


def _build_near_miss():
    rng = random.Random(7)
    lines = []
    for _ in range(12000):
        name = rng.choice(_NAMES)
        user = _username(rng)
        r = rng.random()
        if r < 0.45:
            lines.append(_entry(rng, rng.choice("-*+"), rng.random() < 0.5))
        elif r < 0.55:
            lines.append(f"- [{name}](https://github.com/{user}),")
        elif r < 0.63:
            lines.append(f"- [{name}](https://github.com/{user}) trailing")
        elif r < 0.71:
            lines.append(f"+ [{name}](https://github.com/{user}))")
        elif r < 0.79:
            lines.append(f"- [{name}](https://github.com/)")
        elif r < 0.86:
            lines.append(f"- [](https://github.com/{user})")
        elif r < 0.93:
            lines.append(f"- [{name}](HTTPS://github.com/{user})")
        else:
            lines.append(f"- [{name}](https://github.com/{user}/{_username(rng)})")
    return "\n".join(lines)


_TEXTS = {
    "typical": _build_typical(),
    "large-mixed": _build_large_mixed(),
    "mostly-misses": _build_mostly_misses(),
    "long-lines": _build_long_lines(),
    "no-trailing": _build_no_trailing(),
    "unicode": _build_unicode(),
    "duplicates": _build_duplicates(),
    "near-miss": _build_near_miss(),
}


def checks():
    return [
        ("empty-text", lambda: ("",)),
        ("no-members", lambda: ("# Title\n\nJust prose, no member links here.\n",)),
        ("none-text", lambda: (None,)),
    ]


def cases():
    return [
        ("typical-4k", lambda: (_TEXTS["typical"],)),
        ("large-mixed-25k", lambda: (_TEXTS["large-mixed"],)),
        ("mostly-misses-15k", lambda: (_TEXTS["mostly-misses"],)),
        ("long-lines-3k", lambda: (_TEXTS["long-lines"],)),
        ("no-trailing-15k", lambda: (_TEXTS["no-trailing"],)),
        ("unicode-8k", lambda: (_TEXTS["unicode"],)),
        ("duplicates-10k", lambda: (_TEXTS["duplicates"],)),
        ("near-miss-12k", lambda: (_TEXTS["near-miss"],)),
    ]
