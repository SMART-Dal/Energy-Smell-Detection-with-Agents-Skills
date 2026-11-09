The function is simple: takes a dict, returns sorted list of items by (-len(value), key).

Need to build dicts where values are lists (len used). Note `rank_gc(load)` uses `load.items()` and sorts by `-len(v)`.

Let me write cases with varied dict sizes, value lengths, duplicates.

The "load" presumably maps something to lists. We can use string keys to arbitrary values (lists). Since only len is used, just need lists.

8 cases, diverse: large dicts, varied lengths, many ties, unsorted keys, etc.

Keep under 100k output values.

Let me design:

1. typical: 5000 keys, values lists of random lengths 0-10 with small strings.
2. many ties: all values same length -> sorting falls back on key ordering; many keys.
3. flat: 20000 keys each with single-element lists (heavy string sort).
4. one big value: dict with one key, huge list -> len large.
5. empty values: many keys, empty lists.
6. wide range lengths: 5000 keys with lengths up to 1000.
7. reverse sorted keys and increasing lengths -> adversarial.
8. large: 30000 keys random.

Keep total data under 100MB, outputs under 100k.

I'll write a helper to build dicts.

Note: items.sort sorts tuples; returns list of (key, value) tuples — output size equals number of keys, keep <100k. Fine.

For checks: empty dict, single key, non-list? The function uses len so value needs __len__. Could use string values too (len works). Odd type: value as a string, or key as int. Keys sorted by kv[0] — mixed types would fail comparison. Use int keys consistently.

checks:
- ("empty", lambda: ({},))
- ("single", lambda: ({"a": [1,2,3]},))
- ("string-values", lambda: ({"a": "hello", "b": "hi"},)) — len works on strings, sorting by (-len, key). Fine, may raise? no, works. But maybe "odd type" as key non-comparable — skip to avoid raising weirdly. Actually checks may raise, but that's fine. Keep simple.

Let me build data with random.

def _mk(n, maxlen, seed, alphabet=...): build dict {f"k{i}": [ ... list of length ]}.

Value content doesn't matter for len, but memory. Use small lists of ints.

Write cases.

Case sizes: aim 1ms-200ms. Sorting 20000 items is fast (<10ms). To hit ~tens of ms, need bigger n maybe 100k? But output limited to 100k values — output is list of items, so n <= 100k. Let's use up to 50k.

Actually sorting 50k tuples ~ 20ms. Fine.

Let's craft:

def _load(n, lengths_fn, key_fn): returns dict.

Simplify with helper:

def _make(keys, lengths, seed):
    rng = random.Random(seed)
    return {k: [rng.randint(0,255) for _ in range(l)] for k, l in zip(keys, lengths)}

But building lists of arbitrary length for large lengths expensive; use `[0]*l` for large, random for small. Simplify: use range(l) as list? range isn't list but len works. But value should be list per repo? Only len used, so any sequence works. Use `list(range(l))` or `[0]*l`. Cheap.

Let's just use `[0] * l` — cheap memory. Hmm but that's uniform; only len matters so fine.

Cases:

1. typical: 5000 keys "k%05d", lengths random 0-9.
2. ties: 20000 keys, all lengths equal to 5 -> heaavy comparison on keys (strings). Sorting 20k with all equal first element -> compares keys.
3. many-empty: 20000 keys, all empty lists.
4. skewed: 10000 keys lengths from power law: mostly small, few huge (like 100000? memory ok). lengths up to 5000.
5. wide: 3000 keys, lengths 0..3000 diverse.
6. reverse-adversarial: keys in reverse sorted order with increasing lengths.
7. big: 60000 keys random lengths 0-20.
8. duplicates-keys? keys unique required for dict. Use int keys mixed with string keys? mixing causes compare of int vs str in tie-break -> error. Avoid.

Case 8: integer keys with varied lengths: dict {i: [0]*l} — sorting by (-len, key) with int keys compares ints. Realistic? load keys are probably strings (group names?). Fine either way.

Let's write.

For case with huge lengths, e.g. one key with length 1_000_000 -> memory 8MB, fine but len only. Keep moderate.

Let me write code.

Sizes of output: n keys each -> n tuples. Keep n <= 90000.

Write:

import random, importlib
rank_gc = importlib.import_module('generate-sponsorship-ledger').rank_gc

Module level builds.

def _vals(lengths):
    return [ [0]*l for l in lengths ]

Actually need dict.

def _load(keys, lengths):
    return dict(zip(keys, ([0]*l for l in lengths)))

But wait: building [0]*l for l up to 1e6 many times → total memory. Fine.

Cases should be distinct work paths. Let's define:

rng = random.Random(0)

Case1: n=8000, lengths = [rng.randrange(0,10) for _], keys "k%06d" sorted increasing? Use shuffled to avoid patterns? Sorting stable output; patterns could let tricks exploit... but sort is sort. Use varied.

Let me just write it.

Case list:

1. "typical-8k": 8000 keys, lengths 0..9 random.
2. "all-ties-30k": 30000 keys, all length 4.
3. "all-empty-30k": 30000 keys, empty lists.
4. "powerlaw-20k": 20000 keys, lengths: 90% 0-3, 10% up to 5000.
5. "few-huge": 100 keys, one huge length 2_000_000? memory 2M ints in list of [0] — list of 2M references ~ 16MB; times... only one. Keep 500_000 to be safe. Actually a single list with repeated 0 (small int cached) is 8 bytes per pointer → 4MB for 500k. Fine. But wait, output is 100 tuples only, work is trivial (sorting 100 items by len). That's not much work — maybe under 1ms. Skip or combine with other keys.

Let me make case5: wide range lengths 0..20000 for 5000 keys — building lists sum ~50M references → 400MB. Too much. Keep lengths sum bounded.

Keep total memory < 100MB. `[0]*l` uses 8 bytes per element. Total lengths across all dicts should be < ~10M. Keep.

Case4 powerlaw: 20000 keys, most length small, 100 keys of length 2000 → sum ~ 200k + small. Fine.

Case5: 3000 keys lengths random 0..500 → sum 750k. Fine.

Case6: reverse adversarial: keys descending, lengths ascending by key index, n=20000, lengths 0..19999 → sum 200M. Too big. Instead lengths cycling small but correlated with reverse key order: lengths = i % 8 while keys descending. n=40000.

Case7: 60000 keys random lengths 0..20 → sum ~600k, sorting 60k items heavy.

Case8: int keys, n=50000, lengths random 0..50 → sum 1.25M.

Good.

Let's write helper.

def _mk(keys, lengths):
    return dict(zip(keys, ([0]*l for l in lengths)))

But since function reads only len, values could even be tuples. Keep lists.

Memory-wise fine.

checks:
- ("empty", lambda: ({},))
- ("single", lambda: ({"only": [1,2,3]},))
- ("none-value", lambda: ({"a": None, "b": [1]},)) — rank_gc will call len(None) -> TypeError, that's allowed to raise. Good edge check.

Write final code.