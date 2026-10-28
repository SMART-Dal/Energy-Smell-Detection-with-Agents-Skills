```python
import importlib
import random

render_sig_details_group = importlib.import_module('update-sig-tables').render_sig_details_group


class _WS(dict):
    """A SIG record; keys that the module does not look for read as empty."""

    def __missing__(self, key):
        return ""


_WORDS = [
    "meeting", "notes", "calendar", "slack", "github", "roadmap", "sponsor",
    "liaison", "spec", "implementation", "collector", "protocol", "semantic",
    "conventions", "operator", "profiling", "logs", "metrics", "traces",
    "instrumentation", "sdk", "api", "community", "end-user", "security",
]


def _text(rng, n_words):
    return " ".join(rng.choice(_WORDS) for _ in range(n_words))


def _make_sig(i, rng, n_channels=5, n_repos=3, n_discussions=2,
              n_projects=2, n_sponsors=2, text_words=6, empty_ratio=0.0):
    ws = _WS()
    ws["name"] = f"SIG {i} {_text(rng, 2)}"
    ws["meeting_schedule"] = _text(rng, text_words)
    ws["notes_link"] = f"https://docs.google.com/document/d/{i:08d}/edit"
    ws["calendar"] = f"https://calendar.google.com/calendar/embed?src=sig-{i}"
    ws["slack_channels"] = [f"#sig-{i}-chan-{j}" for j in range(n_channels)]
    ws["discussions"] = [
        f"https://github.com/open-telemetry/community/discussions/{i}-{j}"
        for j in range(n_discussions)
    ]
    ws["repositories"] = [f"open-telemetry/repo-{i}-{j}" for j in range(n_repos)]
    ws["roadmap_projects"] = [f"Project {i}-{j}" for j in range(n_projects)]
    ws["tc_sponsors"] = [f"user-{i}-{j}" for j in range(n_sponsors)]
    ws["spec_sponsors"] = [f"spec-{i}-{j}" for j in range(n_sponsors)]
    ws["gc_liaisons"] = [f"gc-{i}-{j}" for j in range(max(0, n_sponsors - 1))]
    if empty_ratio:
        for key in ("meeting_schedule", "notes_link", "calendar",
                    "slack_channels", "discussions", "repositories",
                    "roadmap_projects", "tc_sponsors", "spec_sponsors",
                    "gc_liaisons"):
            if rng.random() < empty_ratio:
                ws[key] = "" if isinstance(ws[key], str) else []
    return ws


def _sigs(n, seed, **kw):
    rng = random.Random(seed)
    return [_make_sig(i, rng, **kw) for i in range(n)]


# Build every workload once, at module level; thunks only hand it back.
_SMALL = _sigs(50, 0)
_MEDIUM = _sigs(400, 1)
_LARGE = _sigs(2000, 2)
_MANY_CHANNELS = _sigs(150, 3, n_channels=80, n_discussions=12)
_MANY_REPOS = _sigs(250, 4, n_repos=50, n_projects=20)
_LONG_TEXT = _sigs(300, 5, text_words=500)
_HALF_EMPTY = _sigs(800, 6, empty_ratio=0.5)
_HUGE = _sigs(3000, 7, n_channels=8, n_repos=5, text_words=10)


def checks():
    return [
        ("empty-group", lambda: ("Empty Group", [])),
        ("single-sig", lambda: ("Single SIG", [_make_sig(0, random.Random(0))])),
        ("blank-sig", lambda: ("Blank SIG", [_WS()])),
    ]


def cases():
    return [
        ("small-typical", lambda: ("Specification SIGs", _SMALL)),
        ("medium", lambda: ("Implementation SIGs", _MEDIUM)),
        ("large", lambda: ("Cross-Cutting SIGs", _LARGE)),
        ("many-channels", lambda: ("Localization Teams", _MANY_CHANNELS)),
        ("many-repos", lambda: ("Repositories Heavy", _MANY_REPOS)),
        ("long-text", lambda: ("Long Descriptions", _LONG_TEXT)),
        ("half-empty", lambda: ("Sparse Fields", _HALF_EMPTY)),
        ("huge-mixed", lambda: ("Huge Mixed", _HUGE)),
    ]
```