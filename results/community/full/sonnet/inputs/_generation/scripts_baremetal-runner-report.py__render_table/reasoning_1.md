Let me design the inputs.

The function `render_table(records, since)` takes a list of dicts with keys: started (datetime), repo, wf_file, wf_name, run_id, duration, qwait. And since is a datetime.

We need to import it via importlib.import_module('baremetal-runner-report'). The module is at scripts/baremetal-runner-report.py. We need to make sure the import works — need to add scripts dir to sys.path? The task says import as `render_table = importlib.import_module('baremetal-runner-report').render_table`. Hmm, so they expect us to do that. But to import a module named 'baremetal-runner-report', the directory must be on sys.path. The repository's own callers... Let's just do the import in module-level code, possibly with sys.path manipulation. But the instructions say "Import the repository's modules exactly as shown in the task." So we should do exactly that. But we may need to add the scripts directory to sys.path. Hmm.

Actually, maybe the task runner sets up the path. The instruction says "Import the repository's modules exactly as shown in the task." So let's write:

```python
import importlib
render_table = importlib.import_module('baremetal-runner-report').render_table
```

But to be safe, we could add the scripts dir. Actually, the function under test is in scripts/baremetal-runner-report.py. The import statement given is `render_table = importlib.import_module('baremetal-runner-report').render_table`. That implies the module is importable. Perhaps the harness puts the repo root on sys.path and the module is at the root? Hmm. Well, I'll follow the instruction exactly. Maybe add a fallback: if import fails, add scripts dir to sys.path and retry. But that might be considered "not exactly as shown". I think it's fine to do a small sys.path adjustment since the repository's own callers run it as a script. Actually the repo calls it via `python scripts/baremetal-runner-report.py`, so the script's directory is on sys.path. But the harness imports it... Let me just do the direct import as stated, and to be safe, insert the scripts directory into sys.path before importing.

Hmm, but WORKDIR is provided. The repo root is presumably cwd. Let me do:

```python
import os, sys, importlib
_here = os.path.dirname(os.path.abspath(__file__))  # our file's dir? no.
```

We don't know where our file lives. Let's just try:

```python
try:
    render_table = importlib.import_module('baremetal-runner-report').render_table
except ModuleNotFoundError:
    import pathlib
    sys.path.insert(0, str(pathlib.Path.cwd() / 'scripts'))
    render_table = importlib.import_module('baremetal-runner-report').render_table
```

That's reasonable. Actually, keep it simple: the harness presumably handles it. But adding a fallback doesn't hurt.

Now the data. Records: list of dicts. Fields:
- started: datetime (compared with since)
- repo: str like "org/repo"
- wf_file: str like "ci.yml"
- wf_name: str
- run_id: int
- duration: float
- qwait: float

The function aggregates by (repo, wf_file, wf_name). Groups with many records, many runs. Sorted by total descending. Output rows.

Scale: to take ~1ms-200ms. Let's make records of e.g. 20,000-100,000 records with many distinct groups.

Important: the function mutates? It builds agg from records, doesn't mutate records. So thunk can return the same list each time. Good — no need to copy.

But wait: it does `a["runs"].add(...)`, `a["run_totals"][r["run_id"]] += ...`. These are new structures. Records unchanged. So sharing is fine.

Output size: number of rows = number of groups. Keep under 100,000. So groups up to a few thousand.

Input size: records under 1,000,000 values. Each record has ~7 values, so up to ~140,000 records. Keep it moderate.

Let's design 8 cases with different characteristics:
1. Many groups, few records each, all after since.
2. Few groups, many records each (many runs per group).
3. Mixed: some before since (filtered out).
4. Many duplicate run_ids (runs set dedup) — affects avg calc.
5. Large qwait values, varied durations.
6. Repos without "/" (repo_short branch).
7. Single group.
8. All records before since -> empty output (only header). Hmm, that's fast. Maybe not.

Actually need each to do substantial work. Let's aim for ~10k-100k records.

Let me think about timing: the loop is simple. 100k records maybe ~50-100ms in Python. Good. Let's vary.

Let me write a generator:

```python
def _records(n, n_groups, seed, since, before_ratio=0.0, dup_ratio=0.0, slash_ratio=1.0):
    rng = random.Random(seed)
    recs = []
    for i in range(n):
        g = rng.randrange(n_groups)
        repo = f"org{g % 7}/repo{g}" if rng.random() < slash_ratio else f"repo{g}"
        wf_file = f"wf{g}.yml"
        wf_name = f"Workflow {g}"
        if rng.random() < before_ratio:
            started = since - timedelta(days=rng.uniform(0.1, 30))
        else:
            started = since + timedelta(seconds=rng.uniform(0, 86400*30))
        run_id = g * 1000 + (i % 10 if rng.random() < dup_ratio else i)
        duration = rng.uniform(1, 3600)
        qwait = rng.uniform(0, 600)
        recs.append({...})
    return recs
```

Hmm, but `since` needs to be a datetime. We can use a fixed since = datetime(2024,1,1,tzinfo=timezone.utc). But the function compares `r["started"] < since`. Both tz-aware or both naive. Fine.

Actually the repository uses `now - timedelta(days=days)`, tz-aware probably. Let's use timezone.utc.

Let me make each case distinct. Let me define helper that builds records with parameters.

Let me think about the number of values: records with 7 fields each. 100k records = 700k values, under 1M. Good. But building 8 such lists ~ maybe heavy but under 10s. Let's keep total records across cases moderate, like 8 cases * ~50k = 400k records. Building that fast.

Actually careful: "keep each input's data under about 1,000,000 values". 100k records * 7 = 700k. OK.

Let me now design 8 cases:

1. "wide-groups": 60,000 records, 3,000 groups, all after since, all with slash.
2. "deep-runs": 50,000 records, 50 groups, many duplicate run_ids (each group ~ maybe 20 runs with many records). dup_ratio high.
3. "filtered": 80,000 records, 2,000 groups, 50% before since.
4. "no-slash": 40,000 records, 1,500 groups, slash_ratio=0.
5. "huge-qwait": 30,000 records, 800 groups, qwait up to 100000, durations up to 100000.
6. "single-group": 100,000 records, 1 group, many runs.
7. "mixed-slash": 60,000 records, 2,500 groups, slash_ratio=0.5, before_ratio=0.2.
8. "tiny-durations": 70,000 records, 3,500 groups, durations small (0-60s), qwait small.

Hmm case 8 similar to others. Maybe "empty-after-filter": all records before since -> output just header. That's fast but is a valid edge... but the requirement says each case should do substantial work. Let's avoid.

Alternatively "many-distinct-runs": 50,000 records, 5,000 groups, each with single run.

Let me just make 8 diverse ones.

Note: `max_run = max(v["run_totals"].values(), default=0.0)` — if a group has runs. All groups have at least one record so fine.

Also note avg = total/n_runs. With duplicate run_ids, n_runs smaller.

Now checks() — 2-3 small edge inputs:
- empty records list.
- records with one entry.
- records where all before since (empty output).

These may raise? They shouldn't. Fine.

Let me write the code.

One concern: the module-level import. The file name has dashes, importlib.import_module handles it. But we need scripts dir on sys.path. Let me do:

```python
import importlib, sys, pathlib
try:
    _mod = importlib.import_module('baremetal-runner-report')
except ModuleNotFoundError:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'scripts'))
    _mod = importlib.import_module('baremetal-runner-report')
render_table = _mod.render_table
```

Hmm, but we don't know our file's location. Actually our source file will be placed somewhere by the harness, likely in the repo root or a temp dir. The task says "Import the repository's modules exactly as shown in the task." So maybe the harness already handles sys.path. I'll include a robust fallback scanning cwd for 'scripts'.

Actually, simpler: just do the exact import as shown. The harness presumably sets things up. But to be safe add fallback. Let me include:

```python
import importlib, sys
from pathlib import Path
try:
    render_table = importlib.import_module('baremetal-runner-report').render_table
except ModuleNotFoundError:
    for _p in (Path.cwd() / 'scripts', Path.cwd()):
        sys.path.insert(0, str(_p))
    render_table = importlib.import_module('baremetal-runner-report').render_table
```

Wait but the module at import time — does it execute main()? No, it has `if __name__ == "__main__":` presumably. Importing is fine. It imports argparse, json, subprocess, sys, collections, datetime, typing. All fine.

But careful: importing the module might do something at module level? The headers show only function defs. Should be fine.

Now, the function's output is a string. Compared in full. Fine.

Let's write the generator carefully.

```python
from datetime import datetime, timedelta, timezone

SINCE = datetime(2024, 1, 1, tzinfo=timezone.utc)

def _make_records(n, n_groups, seed, *, before_ratio=0.0, dup_ratio=0.0,
                  slash_ratio=1.0, max_dur=3600.0, max_qwait=600.0, run_span=10):
    rng = random.Random(seed)
    recs = []
    for i in range(n):
        g = rng.randrange(n_groups)
        if rng.random() < slash_ratio:
            repo = f"org{g % 13}/repo{g}"
        else:
            repo = f"repo{g}"
        wf_file = f"wf{g}.yml"
        wf_name = f"Workflow {g}"
        if rng.random() < before_ratio:
            started = SINCE - timedelta(days=rng.uniform(0.5, 60))
        else:
            started = SINCE + timedelta(days=rng.uniform(0, 90))
        if rng.random() < dup_ratio:
            run_id = g * run_span + rng.randrange(run_span)
        else:
            run_id = g * 100000 + i
        duration = rng.uniform(0.5, max_dur)
        qwait = rng.uniform(0.0, max_qwait)
        recs.append({
            "started": started,
            "repo": repo,
            "wf_file": wf_file,
            "wf_name": wf_name,
            "run_id": run_id,
            "duration": duration,
            "qwait": qwait,
        })
    return recs
```

Wait, run_id = g*100000+i could collide across groups? g*100000+i with i<n. If n < 100000, and g ranges over n_groups, g*100000 + i unique per (g,i). Fine.

Now cases:

```python
def cases():
    return [
        ("wide-groups", lambda: (_make_records(60_000, 3_000, 0), SINCE)),
        ("deep-runs", lambda: (_make_records(50_000, 60, 1, dup_ratio=0.9, run_span=20), SINCE)),
        ("half-filtered", lambda: (_make_records(80_000, 2_000, 2, before_ratio=0.5), SINCE)),
        ("no-slash-repos", lambda: (_make_records(40_000, 1_500, 3, slash_ratio=0.0), SINCE)),
        ("huge-values", lambda: (_make_records(30_000, 800, 4, max_dur=200_000.0, max_qwait=100_000.0), SINCE)),
        ("single-group", lambda: (_make_records(100_000, 1, 5, dup_ratio=0.8, run_span=50), SINCE)),
        ("mixed", lambda: (_make_records(60_000, 2_500, 6, before_ratio=0.2, slash_ratio=0.5, dup_ratio=0.3), SINCE)),
        ("many-distinct-runs", lambda: (_make_records(50_000, 5_000, 7), SINCE)),
    ]
```

Hmm, "wide-groups" 60k records, 3000 groups → output 3000 rows, fine.

Now checks:

```python
def checks():
    return [
        ("empty", lambda: ([], SINCE)),
        ("single", lambda: ([{...}], SINCE)),
        ("all-before", lambda: ([{...started before since...}], SINCE)),
    ]
```

Single record: started after since.

Now, one issue: the function is repeated many times per input. The thunk returns the same list each time — the function doesn't mutate it. Good. But building the list each thunk call would be expensive; we build at module level? The task says "build large data once, in module-level code, and have the thunk return it". Let me build at module level.

So define `_CASES_DATA = {...}` at module level, and thunks return them.

But careful: module-level building happens at import, before timing. Good.

Let me restructure: build all record lists at module level.

Also the `since` is fixed.

Let me also double check output size limit: 5000 rows max, each row a string. Fine.

Let me also consider `repo.split("/", 1)[1]` — for "org/repo" gives "repo". Fine.

Now let me double check the import fallback doesn't break. Actually `__file__` may not be defined if exec'd... but scripts are files. I'll use Path.cwd().

Let me write final code.

Also need `random` import.

One more thought: should the thunk return `(records, since)` positionally? Yes.

Let me finalize.

Potential concern: building 8 lists totaling ~470k records at module level. Each record is a dict with 7 entries. 470k dicts — memory maybe ~300MB? Hmm, dicts are heavy. Each dict ~ 300 bytes, plus datetime objects etc. 470k * ~500 bytes = 235MB. That might exceed 100MB "keep the data in memory under about 100 MB". Hmm.

The instruction: "Keep the data in memory under about 100 MB". Total data across all cases? Probably per case or overall. Let's reduce sizes to be safe.

Let's target total ~200k records. Each dict maybe ~400-500 bytes with datetime objects. 200k * 500 = 100MB. Still borderline.

Hmm. Let me reduce more. Maybe total ~150k records. Let's see: we need each case to take ~1ms-200ms. Even 10k records takes maybe ~10ms. So we don't need huge counts.

Let me use counts around 20k-40k. Total ~200k. Hmm.

Actually let's estimate memory more carefully. A dict with 7 string/float/datetime keys: the dict itself ~ 184 bytes (for 7 entries, capacity 8) plus keys are shared strings (interned? no, but the same key strings reused across records — actually each dict literal creates new key references but the string objects... in a loop, `"started"` is a constant, so same object reused). Values: started datetime object ~ 48 bytes, repo string ~ 60 bytes, wf_file ~ 55, wf_name ~ 65, run_id int ~ 28, duration float ~ 24, qwait float ~ 24. So ~ 184 + 48+60+55+65+28+24+24 = ~488 bytes per record. Plus list pointer 8 bytes.

150k records * 500 = 75MB. OK-ish. Plus the aggregation during the run creates more.

Let's aim total ~120k records across 8 cases. Averages 15k each. Each call maybe 5-20ms. That's within 1ms-200ms. Fine.

But wait, we run the 4 that do the most work. So more work is better but must stay under 1s. 15k records ~ maybe 10ms. Fine.

Let me set sizes:
1. wide-groups: 25,000 records, 2,000 groups
2. deep-runs: 20,000 records, 40 groups, dup 0.9
3. half-filtered: 30,000 records, 1,500 groups, before 0.5
4. no-slash: 15,000 records, 1,000 groups
5. huge-values: 15,000 records, 500 groups
6. single-group: 30,000 records, 1 group
7. mixed: 25,000 records, 1,500 groups
8. many-distinct-runs: 20,000 records, 3,000 groups

Total 180k records. Hmm ~90MB. Borderline. Let's trim to ~130k.

Actually, "keep the data in memory under about 100 MB" — I'll aim under. Let's do:

1. 20,000 / 2,000
2. 15,000 / 40
3. 25,000 / 1,500
4. 12,000 / 1,000
5. 12,000 / 500
6. 25,000 / 1
7. 20,000 / 1,500
8. 15,000 / 3,000

Total 144k. ~72MB. Plus overhead. Should be fine. Actually the datetime objects: started datetime with timezone.utc tzinfo — tzinfo shared. datetime object ~48 bytes. Fine.

Hmm, but the aggregation dicts during the call: for single-group with 25k records, run_totals dict has maybe 50 entries. Fine. For wide-groups 2000 groups each with sets of runs — 2000 sets of ~10 elements each. Fine.

OK.

Actually, let me reconsider: is 144k records enough work to be "substantial"? Each call maybe 30-60ms total across... no, per call. 20k records loop with dict ops ~ 20ms. Good.

Let me also ensure the 4 heaviest are picked — doesn't matter which.

Now, one subtlety: run_id uniqueness across groups for the "deep-runs" case: run_id = g*run_span + rng.randrange(run_span) gives collisions within group intentionally. Good.

For non-dup case run_id = g*100000 + i, unique.

Now write checks.

Let me write final.

```python
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
```

Wait: the function under test name is render_table, imported. But we don't call it ourselves. The harness calls it. Good.

One issue: `_make_records` is called at module level, and it's fine.

But wait — "Everything you can know about the repository is in the task". The import fallback uses Path.cwd(). Fine.

Another thought: is `render_table` importable as 'baremetal-runner-report'? The task explicitly says to import it that way, so presumably yes in the harness. Good.

Let me double-check the function doesn't mutate records: it only reads. Good, so sharing the same list across repeated calls is fine.

Also output: strings joined. For wide-groups, 2000 rows. Fine.

I think this is good. Let me finalize.

Actually, one concern about `checks()`: "These may raise." Our checks shouldn't raise. Fine.

Let me also make sure the record dicts have all required keys. Yes.

Done.