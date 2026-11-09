Let me analyze the function.

`wait_for_depends_on(depends_on, all_job_outputs)`:
- if len(depends_on) > 0:
  - for each an_id in depends_on:
    - if starts with 'localjob': check all_job_outputs.get(an_id) is None -> raise. Otherwise ok.
    - elif starts with 'job': dxpy.DXJob(an_id).wait_on_done() -> network!
    - else: dxpy.get_handler(an_id).describe(), handler._wait_on_close() -> network!

So to avoid network, we need depends_on entries that are all localjob ids present in all_job_outputs. That path just does dict lookups and prints.

But wait — that's the only path that runs without network. The 'job' and other paths require network. So cases must use localjob ids that exist in all_job_outputs.

But then the work is trivial — just dict lookups. Hmm. But that's the only runnable path. The task says "If the function cannot run here at all... reply CANNOT RUN". But it can run with localjob ids.

Actually, can we make it do substantial work? The work is: printing (fill), dict lookups. The printing goes to stdout... Actually the loop prints for each id. We could have many localjob ids, e.g. thousands. Each iteration prints a line. That's real work. But is it "substantial and different work"? The function has essentially one path available. We need 8 cases with different sizes.

Hmm, but the instruction says cases must run on original without raising. localjob ids present in all_job_outputs work.

Wait, but can we fake dxpy.DXJob / get_handler? No — no mocks. So we can't test the job path. We must use localjob ids.

Actually, could we set up a real dxpy job? No network.

So the realistic inputs: depends_on lists of localjob ids, all present in all_job_outputs. Different sizes and hit/miss ratios... but misses raise. So all must be hits. Hmm, but we could have all_job_outputs with many entries and depends_on with many entries.

Actually wait — the raise happens when all_job_outputs.get(an_id) is None. So every localjob id in depends_on must be a key with non-None value.

Let me think about what "work" means. The loop is O(n) with prints. Printing is I/O to stdout which is captured. With n large (e.g. 50,000), each call prints 50000 lines... that might be slow and output huge. The task says keep output under ~100,000 values. Hmm, printing isn't a returned value though. But it says "anything it writes" under 100,000 values. Prints to stdout... probably fine but let's keep reasonable.

Actually, the timing is only the call. Printing many lines could take significant time. Let's target 1-200ms per call. Printing ~10,000 lines is maybe a few ms. Let's do varied sizes.

But honestly all cases will be structurally identical (localjob ids present). The variation: number of ids, and the all_job_outputs dict size (large dict with many keys, lookups). Different ratios of depends_on size to dict size.

Hmm, is there any other path? What if an_id starts with 'localjob' but all_job_outputs.get returns None -> raises. Not allowed for cases (must complete). For checks we can use that (may raise).

So cases: all localjob ids present. That's the only non-network path. Let me just make varied sizes.

Wait, maybe we can make the 'job' path work without network? dxpy.DXJob(an_id) — creating a DXJob object doesn't make a network call necessarily, but wait_on_done() does. So no.

The else branch: dxpy.get_handler(an_id) — for a data object id like 'file-xxxx', get_handler creates a handler without network? Then handler.describe() makes a network call. So no.

Therefore only localjob path.

Hmm, but is this a satisfying "real workload"? The repository's actual use: depends_on from get_implicit_depends_on, which can include localjob ids and data object ids. In a local execution context, localjob ids are common. So yes, realistic.

Let me design:

all_job_outputs: a dict mapping job ids to outputs. In real repo, this is built from finished local jobs. Keys like 'localjob-XXXX'. Values are output hashes (dicts).

depends_on: list of ids.

Cases with varying n: 100, 1000, 5000, 20000, etc. And dict sizes varying.

Also, maybe mix: depends_on could contain ids that are localjob but... all must be present.

Actually wait — can we include non-localjob ids that resolve without network? No.

Hmm, let me reconsider: could there be a case where depends_on is empty? Then function does nothing (len 0). That's fast, not "most work". But could be one of the 8, though it won't be kept. Actually we need 8 cases and 4 kept. The empty case would be dropped. Fine.

But all 8 need to run without raising. Empty runs fine.

Let me create varied cases:
1. empty depends_on, big dict
2. small: 10 ids
3. medium: 500 ids
4. large: 5000 ids
5. large dict, few ids (sparse lookups)
6. many ids, small dict (dense)
7. huge: 50000 ids
8. depends_on with many ids where dict is huge

Let me think about timing. Each iteration: startswith, dict.get, print. Printing is the dominant cost. 50,000 prints might be ~50-100ms. Let's measure roughly. Python print to a captured stdout (StringIO?) Actually the harness captures stdout probably. Hmm.

Let me keep max around 20000-30000 ids to stay under 200ms.

Actually, the prints: `print(fill('Processing...'))` once, then per id `print('  Waiting for ' + an_id + '...')`. fill does string formatting. Let's check fill signature: fill(string, width_adjustment=0, **kwargs) — probably colors/pads. Cheap.

Let's estimate print cost ~1-2 µs each? Actually print with flush... sys.stdout in test might be redirected. Let's be conservative: 20000 ids ~ maybe 20-40 ms. Good.

Let me build the data.

```python
import random

def _make_job_outputs(n, seed):
    rng = random.Random(seed)
    d = {}
    for i in range(n):
        jid = 'localjob-%s' % _id(rng)
        d[jid] = {'out': rng.randint(0, 1000)}
    return d
```

Better: generate ids deterministically. Use a helper to produce unique localjob ids.

```python
def _jid(i):
    return 'localjob-%04d-abcdefghijklmnopqrstuvwxyz012345' % i
```

Hmm, real dx localjob ids look like 'localjob-0000-...'? Actually dxpy local job ids are like 'localjob-XXXX' where XXXX is a hex-ish. Let's not worry; startswith('localjob') is what matters.

Let me generate ids as 'localjob-' + 24 hex chars.

Plan module-level:

```python
import random

def _gen_ids(n, seed):
    rng = random.Random(seed)
    ids = []
    seen = set()
    while len(ids) < n:
        s = 'localjob-' + ''.join(rng.choice('0123456789abcdef') for _ in range(24))
        if s not in seen:
            seen.add(s)
            ids.append(s)
    return ids
```

Then build dicts and depends_on lists.

For each case, all_job_outputs must contain all depends_on ids. We can build a big pool of ids, then dict = {id: output for id in pool}, depends_on = subset.

Let's create a pool of e.g. 60,000 ids at module level, build dict once, then cases use subsets.

Actually building the pool of 60000 with the while loop and random choice per char (24 chars) = 1.44M rng calls, fine (<1s).

Let me structure:

```python
_POOL = _gen_ids(60000, 0)
_ALL_OUTPUTS = {jid: {"output": i, "value": i * 2} for i, jid in enumerate(_POOL)}
```

Wait, values should be non-None. Good.

Cases:
- ("empty", lambda: ([], _ALL_OUTPUTS))  -- len 0, fast
- ("single", lambda: (_POOL[:1], _ALL_OUTPUTS))
- ("small-10", lambda: (_POOL[:10], _ALL_OUTPUTS))
- ("medium-500", lambda: (_POOL[:500], _ALL_OUTPUTS))
- ("large-5000", lambda: (_POOL[:5000], _ALL_OUTPUTS))
- ("large-20000", lambda: (_POOL[:20000], _ALL_OUTPUTS))
- ("sparse-dict", lambda: (random sample of 1000 from pool, big dict))  -- same as large really
- ("dense-small-dict", lambda: (all ids of a small dict, small dict))

Hmm need diversity. Let me make dict sizes vary too: build a small dict of 1000 entries and depends_on = all 1000. And a huge dict of 60000 with depends_on = 20000.

Also depends_on order: maybe shuffled to avoid sorted pattern.

Let me define:

```python
def _shuffled(n, seed):
    rng = random.Random(seed)
    ids = list(_POOL[:n])
    rng.shuffle(ids)
    return ids
```

But careful: ids must be from _ALL_OUTPUTS keys. Yes.

Cases:
1. empty: ([], _ALL_OUTPUTS)
2. single: (_POOL[0:1], _ALL_OUTPUTS)
3. small: (_shuffled(50, 1), _ALL_OUTPUTS)
4. medium: (_shuffled(1000, 2), _ALL_OUTPUTS)
5. large: (_shuffled(8000, 3), _ALL_OUTPUTS)
6. huge: (_shuffled(25000, 4), _ALL_OUTPUTS)
7. small dict dense: (_SMALL_POOL ids, _SMALL_OUTPUTS) where small dict has 2000 entries and depends_on = all 2000 shuffled.
8. mixed sizes: depends_on from a medium dict of 10000, all present, 10000 ids.

Hmm, these are all the same code path. The differences are size and dict density. That's the best we can do.

Wait — is there any way to get the function to do more "different" work without network? The only branch is localjob. So no.

Hold on. Let me reconsider whether dxpy.DXJob(an_id) construction requires network. DXJob.__init__ probably just stores the id. But wait_on_done() polls the API. So no.

What about get_handler for a data object then describe() — network. No.

So yes, only localjob path.

Given that, the "4 that do the most work" will be the largest depends_on lists. Fine.

Now, output: the function returns None. So output comparison trivial. But stdout prints... The harness compares outputs — probably return value only. Prints might be captured but not compared. Fine.

Actually the task says "The function's output is compared in full after every input". Return value is None. Good.

Concern: printing 25000 lines per call, repeated many times — could be a lot of I/O. But it's what the function does. Maybe reduce max to 20000.

Also the prints include fill() which may add color codes. Fine.

Let me also consider: the timing harness might redirect stdout to devnull or capture. Either way.

Let me estimate: 25000 iterations of print. In CPython, print to a buffered stream maybe ~1µs each = 25ms. Plus string concat. OK.

Let me pick sizes: 1, 50, 1000, 4000, 10000, 20000, and two dict-density variants. Let's do 8:

1. empty
2. single (1 id)
3. small (100 ids, big dict)
4. medium (2000 ids, big dict)
5. large (10000 ids, big dict)
6. huge (25000 ids, big dict)
7. dense-small-dict (3000 ids, dict of exactly 3000)
8. sparse-medium-dict (5000 ids drawn from dict of 50000)

Hmm cases 4,5,6,8 similar. Whatever.

Actually, to make them more distinct, vary the all_job_outputs dict: some cases pass a dict with many extra keys not in depends_on (so get is a lookup in a large dict), others a dict sized exactly to depends_on.

Let me build:
- _ALL_OUTPUTS: 60000 entries.
- _SMALL_OUTPUTS: 3000 entries (subset of pool).
- _MED_OUTPUTS: 20000 entries.

But depends_on ids must be keys in the dict passed. So for _SMALL_OUTPUTS, depends_on must be subset of its keys.

Let me define pools:
_POOL = 60000 ids
_SMALL_IDS = _POOL[:3000]; _SMALL_OUTPUTS = {jid: _ALL_OUTPUTS[jid] for jid in _SMALL_IDS}
_MED_IDS = _POOL[:20000]; _MED_OUTPUTS = {...}

Then cases:
1. empty: ([], _ALL_OUTPUTS)
2. single: (_POOL[:1], _ALL_OUTPUTS)
3. small-bigdict: (_shuffled(_POOL, 100, 1), _ALL_OUTPUTS)
4. medium-bigdict: (_shuffled(_POOL, 3000, 2), _ALL_OUTPUTS)
5. large-bigdict: (_shuffled(_POOL, 12000, 3), _ALL_OUTPUTS)
6. huge-bigdict: (_shuffled(_POOL, 25000, 4), _ALL_OUTPUTS)
7. dense-small-dict: (shuffled(_SMALL_IDS), _SMALL_OUTPUTS)  (3000 ids, 3000-key dict)
8. dense-med-dict: (shuffled(_MED_IDS), _MED_OUTPUTS)  (20000 ids, 20000-key dict)

Good enough.

Now checks: 2-3 small edge inputs, may raise.
- empty depends_on: ([], {}) — runs fine (no raise).
- localjob missing from outputs: (['localjob-000000000000000000000000'], {}) — raises Exception. That's fine for checks.
- None? The function does len(depends_on) so None would raise TypeError. Could include (None, {}). Hmm, may raise. That's allowed. But maybe keep it simple.

Actually checks are "checked only for identical behaviour, never measured. These may raise." So raising is fine.

checks:
1. ("empty", lambda: ([], {}))
2. ("missing-localjob", lambda: (["localjob-abc"], {}))  -> raises
3. ("none-depends-on", lambda: (None, {})) -> raises TypeError

Wait for #2, an_id.startswith('localjob') true, all_job_outputs.get('localjob-abc') is None -> raise Exception. Good.

Hmm, but the modified version might behave differently — that's the point, to detect divergence.

Now, one issue: the function prints for non-empty depends_on. Fine.

Let me also double check `fill` import works. It's imported in the module already.

Now write the code.

Need `WORKDIR`? Not needed, no files.

Let me write generation carefully to be fast.

```python
import random

_HEX = '0123456789abcdef'

def _gen_ids(n, seed):
    rng = random.Random(seed)
    seen = set()
    ids = []
    while len(ids) < n:
        s = 'localjob-' + ''.join(rng.choice(_HEX) for _ in range(24))
        if s not in seen:
            seen.add(s)
            ids.append(s)
    return ids
```

60000 * 24 = 1.44M choices, fast.

Then:

```python
_POOL = _gen_ids(60000, 0)
_ALL_OUTPUTS = {jid: {'output': i, 'job': jid} for i, jid in enumerate(_POOL)}
```

Hmm values should be realistic-ish; a dict is fine.

```python
def _subset_ids(n, seed):
    rng = random.Random(seed)
    ids = list(_POOL[:n])
    rng.shuffle(ids)
    return ids
```

Wait, but the dict keys are _POOL[:n] for small dicts. For big-dict cases I want depends_on to be a random subset of the whole pool, not just the first n. Let me have:

```python
def _sample_ids(n, seed):
    rng = random.Random(seed)
    return rng.sample(_POOL, n)
```

rng.sample from 60000 list — fine.

For dense-small-dict: dict = {jid: ... for jid in _POOL[:3000]}, depends_on = shuffled first 3000.

Let me write:

```python
_SMALL_DICT_IDS = _POOL[:3000]
_SMALL_OUTPUTS = {jid: _ALL_OUTPUTS[jid] for jid in _SMALL_DICT_IDS}

def _shuffled(ids, seed):
    rng = random.Random(seed)
    out = list(ids)
    rng.shuffle(out)
    return out
```

Cases thunks must return tuples of args. Since depends_on lists are precomputed at module level and the function doesn't modify them (it only iterates), we can reuse. Actually the function doesn't modify depends_on or all_job_outputs. So safe to reuse same objects across calls. Good — cheap thunks.

But caution: "Anything the function changes outside its arguments carries over". It doesn't change anything. Good.

So precompute depends_on lists at module level.

Let me finalize:

```python
_CASE_EMPTY = []
_CASE_SINGLE = _POOL[:1]
_CASE_SMALL = _sample(100, 1)
_CASE_MED = _sample(3000, 2)
_CASE_LARGE = _sample(12000, 3)
_CASE_HUGE = _sample(25000, 4)
_CASE_DENSE_SMALL = _shuffled(_SMALL_DICT_IDS, 5)
_CASE_DENSE_MED = _shuffled(_MED_DICT_IDS, 6)
```

where _MED_DICT_IDS = _POOL[:20000], _MED_OUTPUTS.

Now thunks: `lambda: (_CASE_SMALL, _ALL_OUTPUTS)`.

For empty: `lambda: ([], _ALL_OUTPUTS)`.

Good.

Let me reconsider timing for huge (25000). Should be fine.

Actually, let me reconsider: is printing to stdout going to be captured by the harness in a way that's slow (e.g., a pipe)? Could be. But we can't avoid it; the function prints. Reduce huge to 20000 maybe. I'll use 20000.

Let me also double-check the function's behavior: for localjob id present, no exception. Good.

One more: `fill` is called with a string. fill may use terminal width. Fine.

Write final code.

Actually, I should double-check that `dxpy` import at module import time doesn't require network. The module imports dxpy which is fine. Importing the function module imports dxpy — that's the repository's own import, fine.

Let me write it.

Also need to ensure `_ALL_OUTPUTS` values are not None. Yes.

Final code:

```python
import random

_HEX = '0123456789abcdef'

def _gen_ids(n, seed):
    rng = random.Random(seed)
    seen = set()
    ids = []
    while len(ids) < n:
        s = 'localjob-' + ''.join(rng.choice(_HEX) for _ in range(24))
        if s not in seen:
            seen.add(s)
            ids.append(s)
    return ids

_POOL = _gen_ids(60000, 0)
_ALL_OUTPUTS = {jid: {'job': jid, 'output': {'value': i}} for i, jid in enumerate(_POOL)}

def _sample(n, seed):
    rng = random.Random(seed)
    return rng.sample(_POOL, n)

def _shuffled(ids, seed):
    rng = random.Random(seed)
    out = list(ids)
    rng.shuffle(out)
    return out

_SMALL_DICT_IDS = _POOL[:3000]
_SMALL_OUTPUTS = {jid: _ALL_OUTPUTS[jid] for jid in _SMALL_DICT_IDS}
_MED_DICT_IDS = _POOL[:20000]
_MED_OUTPUTS = {jid: _ALL_OUTPUTS[jid] for jid in _MED_DICT_IDS}

_C_EMPTY = []
_C_SINGLE = _POOL[:1]
_C_SMALL = _sample(100, 1)
_C_MED = _sample(3000, 2)
_C_LARGE = _sample(12000, 3)
_C_HUGE = _sample(20000, 4)
_C_DENSE_SMALL = _shuffled(_SMALL_DICT_IDS, 5)
_C_DENSE_MED = _shuffled(_MED_DICT_IDS, 6)


def checks():
    return [
        ("empty", lambda: ([], {})),
        ("missing-localjob", lambda: (["localjob-000000000000000000000000"], {})),
        ("none-depends-on", lambda: (None, {})),
    ]


def cases():
    return [
        ("empty", lambda: (_C_EMPTY, _ALL_OUTPUTS)),
        ("single", lambda: (_C_SINGLE, _ALL_OUTPUTS)),
        ("small", lambda: (_C_SMALL, _ALL_OUTPUTS)),
        ("medium", lambda: (_C_MED, _ALL_OUTPUTS)),
        ("large", lambda: (_C_LARGE, _ALL_OUTPUTS)),
        ("huge", lambda: (_C_HUGE, _ALL_OUTPUTS)),
        ("dense-small-dict", lambda: (_C_DENSE_SMALL, _SMALL_OUTPUTS)),
        ("dense-medium-dict", lambda: (_C_DENSE_MED, _MED_OUTPUTS)),
    ]
```

Wait, checks with None: `len(None)` raises TypeError. Fine. But the harness renders arguments before/after — None is fine.

Hmm, one concern: "Every case must run to completion on the original function without raising." Cases only. Checks may raise. Good.

Also, the `_C_EMPTY` case: len 0, function returns None immediately. It's one of the 8 but will be dropped. Fine.

I think this is good. Let me double check the label distinctness. Yes.

One more thought: should I worry that the huge case prints 20000 lines and the harness might treat stdout as "output" and compare? It says output compared in full — likely the return value. Return is None. Fine.

Let me finalize.