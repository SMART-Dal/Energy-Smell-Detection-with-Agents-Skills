import importlib
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    render_table = importlib.import_module('baremetal-runner-report').render_table
except ModuleNotFoundError:
    for _p in (Path.cwd() / 'scripts', Path.cwd()):
        if _p.is_dir():
            sys.path.insert(0, str(_p))
    render_table = importlib.import_module('baremetal-runner-report').render_table

SINCE = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _make_records(n, n_groups, seed, *, before_ratio=0.0, dup_ratio=0.0,
                  slash_ratio=1.0, max_dur=3600.0, max_qwait=600.0, run_span=10):
    rng = random.Random(seed)
    recs = []
    for i in range(n):
        g = rng.randrange(n_groups)
        repo = f"org{g % 13}/repo{g}" if rng.random() < slash_ratio else f"repo{g}"
        if rng.random() < before_ratio:
            started = SINCE - timedelta(days=rng.uniform(0.5, 60))
        else:
            started = SINCE + timedelta(days=rng.uniform(0, 90))
        if rng.random() < dup_ratio:
            run_id = g * run_span + rng.randrange(run_span)
        else:
            run_id = g * 100000 + i
        recs.append({
            "started": started,
            "repo": repo,
            "wf_file": f"wf{g}.yml",
            "wf_name": f"Workflow {g}",
            "run_id": run_id,
            "duration": rng.uniform(0.5, max_dur),
            "qwait": rng.uniform(0.0, max_qwait),
        })
    return recs


_C1 = _make_records(20_000, 2_000, 0)
_C2 = _make_records(15_000, 40, 1, dup_ratio=0.9, run_span=20)
_C3 = _make_records(25_000, 1_500, 2, before_ratio=0.5)
_C4 = _make_records(12_000, 1_000, 3, slash_ratio=0.0)
_C5 = _make_records(12_000, 500, 4, max_dur=200_000.0, max_qwait=100_000.0)
_C6 = _make_records(25_000, 1, 5, dup_ratio=0.8, run_span=50)
_C7 = _make_records(20_000, 1_500, 6, before_ratio=0.2, slash_ratio=0.5, dup_ratio=0.3)
_C8 = _make_records(15_000, 3_000, 7)


def checks():
    return [
        ("empty", lambda: ([], SINCE)),
        ("single", lambda: ([{
            "started": SINCE + timedelta(days=1),
            "repo": "org/repo",
            "wf_file": "ci.yml",
            "wf_name": "CI",
            "run_id": 1,
            "duration": 12.5,
            "qwait": 3.0,
        }], SINCE)),
        ("all-before", lambda: ([{
            "started": SINCE - timedelta(days=1),
            "repo": "org/repo",
            "wf_file": "ci.yml",
            "wf_name": "CI",
            "run_id": 1,
            "duration": 12.5,
            "qwait": 3.0,
        }], SINCE)),
    ]


def cases():
    return [
        ("wide-groups", lambda: (_C1, SINCE)),
        ("deep-runs", lambda: (_C2, SINCE)),
        ("half-filtered", lambda: (_C3, SINCE)),
        ("no-slash-repos", lambda: (_C4, SINCE)),
        ("huge-values", lambda: (_C5, SINCE)),
        ("single-group", lambda: (_C6, SINCE)),
        ("mixed", lambda: (_C7, SINCE)),
        ("many-distinct-runs", lambda: (_C8, SINCE)),
    ]
