Let me analyze the function. `split_unescaped(char, string, include_empty_strings=False)`.

It's O(n^2)-ish: for each split position it scans the string. Actually `get_last_pos_of_char` does `string[:pos].rfind(char)` which is O(n) each, and the outer loop calls it repeatedly. So total work can be quadratic in number of splits.

Realistic inputs from the repository:
- `parse_input_or_jbor`: splits on ':' — values like "job-xxxx:field_name", input values with colons.
- `parsers.py`: splits on '=' with include_empty_strings=True, e.g. "key=value", "key", "key=", "=value".
- `dx.py` get_matches: splits on ' ' for command line text.
- `rmproject`: splits on ':' for project names.

So realistic workloads: strings with colons, equals, spaces, backslashes escaping.

We need 8 cases with realistic scale. Make strings long (e.g. tens of thousands of chars) with many separators to make it take ~1-200ms.

Let me estimate: string length n, number of separators k. Each get_last_pos_of_char call scans back from lastpos to find the previous unescaped char. The rfind is on string[:pos] which is O(pos). So each iteration costs O(n). With k separators, total O(k*n). For n=100_000 and k=1000, that's 10^8 character ops... in Python maybe ~0.1-1s. Hmm, need to be careful.

Actually rfind is implemented in C, so it's fast. `string[:pos]` creates a copy — O(pos) per call. With k=1000 and n=100_000, that's 1000 * 100_000 = 10^8 bytes copied, plus rfind scans. Might be ~0.1s. Let's aim smaller.

Let's target: string length ~50_000 with ~500 separators → 500 * 50_000 = 2.5*10^7 char copies. That's maybe 20-50 ms. Good.

Actually the backslash counting loop also adds work. Escaped chars: `\:` requires counting backslashes. Let's include runs of backslashes to stress that.

Let me design cases:

1. Colon-separated input values (like `parse_input_or_jbor`): many "job-xxxx:field" patterns. String like "job-abc123:field1 job-...". Actually it's a single value. Let's do a long string with many colons.

2. Equals with include_empty_strings=True: "key=value" repeated, plus "key", "key=", "=value".

3. Space-split command line (get_matches): text with spaces, some escaped spaces `\ `.

4. Heavily escaped: many backslashes, e.g. `\\:` (escaped backslash then real colon), `\:` (escaped colon).

5. No separators at all — long string, worst case single scan. Actually that's cheap-ish: one rfind over whole string returns -1. O(n). Fast. But still a real case.

6. Very many separators (dense) — quadratic stress.

7. include_empty_strings=True with consecutive separators.

8. Mixed real-world path-like strings.

Let me think about how to generate. Use random.Random(0) with fixed seed.

We need each thunk to return a tuple of args. Since the function doesn't modify the string, we can reuse the same string object across calls. Good — build once at module level.

But careful: the function creates new lists each call; no mutation of args. So no copy needed.

Let's write generators.

Case A: colon-split, typical input value with a few colons but long. E.g. build a long string of tokens separated by ':' where tokens are random words. n tokens ~ 2000, each token ~10 chars → 20_000 chars, 2000 separators. Cost ~2000*20000 = 4*10^7. Maybe 30ms.

Hmm, let me be a bit conservative and test mentally. Actually I can't test. Let me pick moderate sizes.

Let me estimate Python's slicing cost: `string[:pos]` for pos=20000 copies 20000 chars — very fast, maybe 1-2 microseconds. rfind over it maybe 1 microsecond. So each outer iteration ~3µs. 2000 iterations → 6ms. Plus backslash loop. So that's fine, maybe a bit small. Could go bigger: 10_000 tokens of 10 chars = 100_000 chars, 10_000 separators → 10_000 * 100_000 = 10^9 bytes copied... at ~10GB/s memcpy that's 0.1s plus rfind. Might be ~0.2-0.5s. Risky.

Let's target around 3000-5000 separators with ~50k char strings. That gives ~5000*50000 = 2.5*10^8 bytes → ~25ms memcpy plus rfind ~ similar. Total maybe 50-100ms. Good.

Actually wait — the outer loop: for each separator found, `get_last_pos_of_char` is called with `string[:lastpos]`. The rfind scans from the end of the prefix backward until it finds char. Since separators are dense, it finds one quickly. But the slice copy is O(lastpos). So yes, dominated by slicing.

Also the final `words.append(string[pos+1:lastpos])` slices — total O(n) overall.

Let me construct diverse cases:

1. `colon_typical`: long string with ~4000 colon-separated fields, each a random alphanumeric token of length ~8-15. include_empty_strings=False.

2. `colon_escaped`: many escaped colons `\:` mixed with real colons. Backslash counting loop gets exercised.

3. `equals_include_empty`: "key=value" pairs, include_empty_strings=True, ~3000 pairs.

4. `equals_no_empty`: same but include_empty_strings=False.

5. `spaces_escaped`: command-line-like, spaces with many escaped spaces.

6. `dense_colons`: very dense separators, e.g. many consecutive colons "::::", include_empty_strings=True. But careful: consecutive colons — with include_empty_strings=True, each produces empty strings. The loop still runs per colon. Good stress.

7. `backslash_runs`: long runs of backslashes before separators, e.g. `\\\\\\\\:` — the inner while loop iterates over the run each time. Deep backslash runs make it O(run^2) potentially. Let's have runs of ~50-200 backslashes.

8. `no_separators`: long string with no target char at all — single pass. Cheap but realistic (e.g. a path with no colons). Maybe combine with something.

Hmm, but we want all 8 to be substantial. `no_separators` would be fast. But it's fine to have variety; the harness keeps the 4 that do the most work. Still, we should make each case do real work. Let's make no_separators a long string with a different char... Actually with no separators, get_last_pos_of_char does one rfind over whole string → O(n), returns -1, loop ends. Then append whole string. That's ~O(n) which for n=200k is fast (<1ms). Probably too fast. Let's instead make case 8 a mixed case with moderate separators and escaped chars.

Let me reconsider: maybe use longer strings for the no-separator case to be ~1ms. 200k chars rfind ~ maybe 0.2ms. Fine, it's allowed to be small but then it gets dropped. We need enough cases that do work. Let's just make all 8 meaningful.

Better plan for 8 diverse cases:

1. colon_split_typical (include_empty=False), n≈60k, ~4000 fields.
2. colon_split_escaped (include_empty=False), many `\:`.
3. equals_include_empty=True, ~4000 pairs.
4. equals_include_empty=False, ~4000 pairs.
5. space_split (get_matches style), ~5000 words, some escaped spaces.
6. dense_separators include_empty=True, ~8000 consecutive-ish separators.
7. backslash_heavy: long runs of backslashes before separators.
8. mixed_paths: realistic paths/ids with colons and backslashes, include_empty=True.

Let me write generators.

For tokens: use rng.choice of letters.

Let me write:

```python
import random
import string as _string
from dxpy.utils.resolver import split_unescaped

_ALPHA = _string.ascii_letters + _string.digits

def _token(rng, lo=4, hi=12):
    return ''.join(rng.choice(_ALPHA) for _ in range(rng.randint(lo, hi)))

def _colon_fields(n, seed, esc_ratio=0.0):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        t = _token(rng)
        if esc_ratio and rng.random() < esc_ratio:
            # insert an escaped colon inside the token
            i = rng.randrange(len(t)+1)
            t = t[:i] + '\\:' + t[i:]
        parts.append(t)
    return ':'.join(parts)
```

Wait: building with ':' join means exactly n-1 real separators. Good.

For escaped colons: `\:` inside a token means it's not a split point. Good.

Case 2: esc_ratio high, e.g. 0.3.

Case 3/4: equals.

```python
def _kv_pairs(n, seed, include_empty_when_built...):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        k = _token(rng)
        v = _token(rng)
        parts.append(k + '=' + v)
    return '='.join(parts)
```
Hmm that gives 2n-1 separators. Fine.

Actually to be more realistic to parsers.py, each keyeqval is a single string like "key=value". But here we test one long string. It's fine — the function is called per keyeqval but a long one is a valid stress.

Case 5: spaces. Words separated by spaces, some escaped spaces `\ `.

Case 6: dense separators with include_empty_strings=True: string like ':'*5000 or random runs. Let's do runs of colons of random length 1-5, total ~6000 colons, with tokens between.

Actually consecutive colons: with include_empty_strings=True, all produce empty entries. The algorithm: for each colon it appends string[pos+1:lastpos]. Fine.

Case 7: backslash heavy. Build tokens separated by ':' where before some separators we add runs of backslashes. Wait, backslashes before a colon: even number → colon is unescaped (split), odd → escaped. The algorithm's inner loop counts backslashes each time it finds a char. So runs of backslashes make it slow. Let's build: each field preceded by a run of backslashes of random length 0-100, then ':'. Hmm, but backslashes are part of the string content.

Let me build: parts joined by run-of-backslashes + ':'. E.g. field + '\\'*k + ':' + field...

The rfind finds the colon at position p, then counts backslashes before it: k of them. O(k). Total O(sum k). If k up to 200 and 3000 separators → 600k ops, fine. Plus the slicing dominates anyway.

To make the backslash loop dominate, we want large runs. But also rfind scanning... Let's just include it.

Case 8: mixed realistic: strings like "project-xxxx:folder/subfolder:file.txt" with escaped colons. Eh.

Let me just make case 8 a long string with a mix of unescaped and escaped colons and backslashes, include_empty_strings=True.

Now sizes. Let me compute rough total lengths.

Case 1: n=4000 fields, avg token ~8 chars → length ~4000*8 + 3999 = ~36000. Separators 3999. Cost ~3999 * 36000 = 1.4*10^8 bytes slicing. ~15-30ms. Good.

Hmm, but actually the rfind also scans. And `string[:lastpos]` — lastpos decreases. Sum of lastpos over iterations ≈ n^2/2 / ... wait, lastpos decreases from n to 0 across iterations. The sum of lastpos values ≈ n * k / 2 if evenly spaced... Actually lastpos goes n, then previous separator pos, etc. Sum ≈ sum of positions of separators from the end ≈ n*k/2? No: positions are roughly n, n-n/k, n-2n/k, ... Sum = k*n - (n/k)*(k(k-1)/2) ≈ k*n - n*k/2 = n*k/2. So 36000*3999/2 ≈ 7.2*10^7. ~10ms. Fine.

Let's bump to n=6000 fields for more work: length ~54000, k=5999, cost ~54000*5999/2 = 1.6*10^8 → ~20-40ms. Good.

I'll use n around 5000-8000 for colon/equals cases.

Actually let me be careful about total build time and memory. All fine.

Let me set:
- case1: 6000 fields.
- case2: 6000 fields, esc_ratio 0.4.
- case3: 5000 kv pairs (→ ~10000 separators, length ~5000*17=85000). Cost 85000*10000/2=4.25*10^8 → ~50-100ms. Hmm maybe too much. Let's use 3000 pairs → length ~51000, k=5999, cost ~1.5*10^8. OK.
- case4: same as 3 but include_empty=False. Could reuse the string; but we want distinct work. Actually case 3 and 4 with same string but different flag — the work is nearly identical except empty handling. That's fine, different path. But maybe make lengths different.

Hmm, the harness keeps the 4 that do the most work. We want at least 4 substantial.

Let me finalize sizes conservatively so nothing exceeds 1s.

I'll write a helper that builds a string of given target length with separators.

Let me just write explicit generators.

```python
import random
import string as _string
from dxpy.utils.resolver import split_unescaped

_AL = _string.ascii_letters + _string.digits

def _tok(rng, lo=4, hi=12):
    return ''.join(rng.choice(_AL) for _ in range(rng.randint(lo, hi)))

def _join_fields(fields, sep):
    return sep.join(fields)
```

Case 1:
```python
def _colon_plain(n, seed):
    rng = random.Random(seed)
    return ':'.join(_tok(rng) for _ in range(n))
```

Case 2:
```python
def _colon_escaped(n, seed, esc_ratio):
    rng = random.Random(seed)
    fields = []
    for _ in range(n):
        t = _tok(rng)
        if rng.random() < esc_ratio:
            i = rng.randrange(len(t) + 1)
            t = t[:i] + '\\:' + t[i:]
        fields.append(t)
    return ':'.join(fields)
```

Case 3/4:
```python
def _kv(n, seed):
    rng = random.Random(seed)
    return '='.join(_tok(rng) + '=' + _tok(rng) for _ in range(n))
```
Wait that joins pairs with '=' giving 2n-1 '='. Fine.

Hmm, actually for parsers.py realism, keyeqval like "key=value". Let me just do `'='.join(_tok(rng) for _ in range(2*n))`? Simpler: generate 2n tokens joined by '='. That's the same as above roughly.

Case 5 spaces:
```python
def _spaces(n, seed, esc_ratio):
    rng = random.Random(seed)
    words = []
    for _ in range(n):
        t = _tok(rng, 2, 10)
        if rng.random() < esc_ratio:
            i = rng.randrange(len(t)+1)
            t = t[:i] + '\\ ' + t[i:]
        words.append(t)
    return ' '.join(words)
```

Case 6 dense:
```python
def _dense(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        parts.append(_tok(rng, 1, 4))
        parts.append(':' * rng.randint(1, 4))
    return ''.join(parts)
```
This gives many colons. With include_empty_strings=True.

Hmm, but consecutive colons: after splitting, the algorithm finds each colon. Fine.

Case 7 backslash heavy:
```python
def _backslash(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        parts.append(_tok(rng, 3, 8))
        parts.append('\\' * rng.randint(1, 60))
        parts.append(':')
    parts.append(_tok(rng))
    return ''.join(parts)
```
Runs of backslashes up to 60, n=3000 → 180k backslashes; inner loop total ~ sum k = 3000*30 = 90k. Fine. But wait, does the backslash counting actually run for each colon? Yes: rfind finds colon at p, then counts backslashes before it. If run is k, counts k. So 90k iterations of Python loop — ~10ms. Plus slicing.

But careful: the slicing dominates and is O(n*k/2). n length ≈ 3000*(5+30+1)=108000. k=3000. cost = 108000*3000/2 = 1.6*10^8. OK ~30ms.

Case 8 mixed:
Realistic-ish: build strings resembling dx paths with colons and escaped chars, include_empty_strings=True. Let's do:
```python
def _mixed(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        kind = rng.random()
        if kind < 0.3:
            parts.append('project-' + _tok(rng, 8, 12))
        elif kind < 0.6:
            parts.append('folder' + str(rng.randint(0,999)) + '/' + _tok(rng, 3, 8))
        else:
            parts.append(_tok(rng, 2, 6) + '\\:' + _tok(rng, 2, 6))
        parts.append(':')
    return ''.join(parts)
```
Hmm this ends with ':'. That's fine.

Actually let me reconsider — maybe use a fixed char per case as the repository does: ':' , '=', ' '. Good.

Now checks(): 2-3 small edge inputs.
- empty string: `split_unescaped(':', "")` → words? Let's trace: string="", pos=0, lastpos=0. Loop: pos>=0: get_last_pos_of_char(':', "") → pos=0, while pos>0 false, return -1. pos=-1 <0 exit loop. Then lastpos==0 and not include_empty → no append. words=[] reversed = []. Returns [].
- single char: ":" → string=":", pos=1,lastpos=1. loop: get_last_pos_of_char(':', ":[:1]"=":") → pos=1, string[:1].rfind(':')=0. num_backslashes: test_index=-1, 0. even → return 0. pos=0>=0. pos+1=1 == lastpos=1 and not include_empty → skip. lastpos=0. loop: get_last_pos_of_char(':', string[:0]="") → -1. pos=-1 exit. lastpos==0 → no append. words=[]. Returns [].

Hmm interesting.

- include_empty_strings=True with empty: returns ['']? Let's trace: string="", pos=0,lastpos=0. loop: get_last_pos → -1. exit. lastpos==0 but include_empty True → append string[:0]="" → words=[""]. reverse → [""]. Returns [""].

- None input would raise TypeError. Could include as edge check.

Let's do checks:
```python
def checks():
    return [
        ("empty", lambda: (':', "")),
        ("only-sep", lambda: (':', ":")),
        ("empty-included", lambda: (':', "", True)),
    ]
```
Wait, include_empty_strings is positional third arg. Yes signature `split_unescaped(char, string, include_empty_strings=False)`. So `lambda: (':', "", True)`.

Maybe also a None check but it raises — allowed. Let's add one with odd type? "an odd type" — e.g. None. But then it raises, and behavior compared. It's allowed for checks. But maybe keep it simple with 3.

Actually the instructions say checks may raise. Let's include a None case? Hmm, it might be fine but let's keep 3 safe ones plus maybe. I'll do 3.

Wait, but "only-sep" with include_empty... let's also consider a case with escaped char at start.

Let me finalize checks:
1. ("empty", lambda: (':', ""))
2. ("one-separator", lambda: (':', ":"))
3. ("empty-included", lambda: (':', "a::b", True))

Hmm "a::b" with include_empty True → ['a','','b'].

Actually let me include a None/odd-type one since they suggest it. But it raises TypeError inside get_last_pos_of_char (len(None)). Both original and modified would raise the same. Fine. But if the modified version handles it differently... risk. I'll skip None and use safe small ones. Actually instructions say "2 or 3 small edge inputs (empty, one element, None, an odd type)". They may raise. It's fine either way. I'll do 3 that don't raise, safer.

Hmm, but they want edge coverage. Let me do:
1. empty string
2. single char string that's the separator
3. include_empty_strings=True with empty string

Now cases: 8 measured. Let me write them.

```python
def cases():
    return [
        ("colon-plain", lambda: (':', _COLON_PLAIN)),
        ("colon-escaped", lambda: (':', _COLON_ESC)),
        ("equals-include-empty", lambda: ('=', _KV, True)),
        ("equals-no-empty", lambda: ('=', _KV2)),
        ("spaces-escaped", lambda: (' ', _SPACES)),
        ("dense-colons", lambda: (':', _DENSE, True)),
        ("backslash-runs", lambda: (':', _BACKSLASH)),
        ("mixed-include-empty", lambda: (':', _MIXED, True)),
    ]
```

Build all at module level.

Let me pick sizes:
- _COLON_PLAIN: 6000 tokens.
- _COLON_ESC: 6000 tokens, esc 0.4.
- _KV: 3000 pairs → 6000 tokens joined by '='. length ~ 6000*8=48000, k=5999.
- _KV2: 3500 pairs.
- _SPACES: 8000 words.
- _DENSE: 5000 groups.
- _BACKSLASH: 3000.
- _MIXED: 5000.

Memory: each string ~50-100KB. Trivial.

Let me double check the cost isn't too high. Worst: _DENSE with 5000 groups each 1-4 colons → ~12500 colons, length ~5000*(2.5+2.5)=25000. cost = 25000*12500/2 = 1.56*10^8. OK.

_SPACES: 8000 words avg 6 chars → length ~56000, k=7999. cost = 56000*7999/2=2.2*10^8 → ~30-60ms. OK.

_KV2: 3500 pairs → 7000 tokens, length ~56000, k=6999. cost ~2*10^8. OK.

All under 200ms presumably. Good.

Build time: generating ~50k random chars per case, 8 cases → 400k random choices. That's fast (<1s). Good.

Now, one concern: the function `split_unescaped` is called with `string` that has no mutation. Good.

Wait, one more: the function reads `get_last_pos_of_char` from the module — imported. Fine.

Let me double-check `_COLON_ESC` construction: fields contain '\\:' which is two chars backslash+colon. When joined with ':', the rfind finds the real ':' separators; escaped ones have 1 backslash before → odd → not split. But careful: a field ending with backslash followed by join ':' would create even backslashes → split. My tokens are alphanumeric plus inserted '\:', so fields never end with backslash (the '\:' insertion puts backslash then colon, so field could end with colon but not backslash). Actually if inserted at end: t = t + '\\:' → ends with ':'. Then join adds ':' → '::' with a backslash before first. Hmm: field ends with '...\:' then join ':' → '...\::'. The last ':' has preceding char ':' (not backslash) → unescaped, split. And the escaped one has 1 backslash → not split. Fine, no issue.

Let me also make sure `_DENSE` doesn't produce weirdness with include_empty=True. It's fine.

Now, potential issue: the modified version might behave differently on some inputs; we want the original to run without raising. All fine.

Let me also verify no separator case? Not included. Fine.

Let me write final code.

Actually, let me reconsider the `_AL` and token generation speed. `''.join(rng.choice(_AL) for _ in range(...))` — for 6000 tokens of ~8 chars = 48000 choices per case. Fine.

One more consideration: module-level code runs when the test module is imported, and WORKDIR isn't needed (no files). Good.

Let me write it.

```python
import random
import string as _string

from dxpy.utils.resolver import split_unescaped

_AL = _string.ascii_letters + _string.digits


def _tok(rng, lo=4, hi=12):
    return ''.join(rng.choice(_AL) for _ in range(rng.randint(lo, hi)))


def _colon_plain(n, seed):
    rng = random.Random(seed)
    return ':'.join(_tok(rng) for _ in range(n))


def _colon_escaped(n, seed, esc_ratio):
    rng = random.Random(seed)
    fields = []
    for _ in range(n):
        t = _tok(rng)
        if rng.random() < esc_ratio:
            i = rng.randrange(len(t) + 1)
            t = t[:i] + '\\:' + t[i:]
        fields.append(t)
    return ':'.join(fields)


def _kv(n, seed):
    rng = random.Random(seed)
    return '='.join(_tok(rng) for _ in range(2 * n))


def _spaces(n, seed, esc_ratio):
    rng = random.Random(seed)
    words = []
    for _ in range(n):
        t = _tok(rng, 2, 10)
        if rng.random() < esc_ratio:
            i = rng.randrange(len(t) + 1)
            t = t[:i] + '\\ ' + t[i:]
        words.append(t)
    return ' '.join(words)


def _dense(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        parts.append(_tok(rng, 1, 4))
        parts.append(':' * rng.randint(1, 4))
    parts.append(_tok(rng, 1, 4))
    return ''.join(parts)


def _backslash(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        parts.append(_tok(rng, 3, 8))
        parts.append('\\' * rng.randint(1, 60))
        parts.append(':')
    parts.append(_tok(rng, 3, 8))
    return ''.join(parts)


def _mixed(n, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        r = rng.random()
        if r < 0.3:
            parts.append('project-' + _tok(rng, 8, 12))
        elif r < 0.6:
            parts.append('folder' + str(rng.randint(0, 999)) + '/' + _tok(rng, 3, 8))
        else:
            parts.append(_tok(rng, 2, 6) + '\\:' + _tok(rng, 2, 6))
        parts.append(':')
    parts.append(_tok(rng, 2, 6))
    return ''.join(parts)


_COLON_PLAIN = _colon_plain(6000, 0)
_COLON_ESC = _colon_escaped(6000, 1, 0.4)
_KV = _kv(3000, 2)
_KV2 = _kv(3500, 3)
_SPACES = _spaces(8000, 4, 0.2)
_DENSE = _dense(5000, 5)
_BACKSLASH = _backslash(3000, 6)
_MIXED = _mixed(5000, 7)


def checks():
    return [
        ("empty", lambda: (':', "")),
        ("one-separator", lambda: (':', ":")),
        ("empty-included", lambda: (':', "", True)),
    ]


def cases():
    return [
        ("colon-plain", lambda: (':', _COLON_PLAIN)),
        ("colon-escaped", lambda: (':', _COLON_ESC)),
        ("equals-include-empty", lambda: ('=', _KV, True)),
        ("equals-no-empty", lambda: ('=', _KV2)),
        ("spaces-escaped", lambda: (' ', _SPACES)),
        ("dense-colons", lambda: (':', _DENSE, True)),
        ("backslash-runs", lambda: (':', _BACKSLASH)),
        ("mixed-include-empty", lambda: (':', _MIXED, True)),
    ]
```

Wait — one concern about `_backslash`: the string ends with a token, and the last part before it is ':' so fine. But runs of backslashes followed by ':' — the rfind finds the colon, counts backslashes. Even runs → split, odd → escaped. Both paths exercised. Good.

Also concern: in `_mixed`, parts end with ':' then final token appended. So string ends with token. Fine.

Now let me reconsider whether the work is enough / not too much. I'll trust estimates.

One more: the `string[:pos].rfind(char)` where char is a single char. Fine.

Potential issue: `_COLON_PLAIN` with 6000 tokens — average token length (4+12)/2=8 → length ~54000. k=5999. Cost ~1.6e8. Fine.

Let me also double check that the function returns under 100000 values. Number of output words = number of fields ≈ up to ~12500 for dense. Fine.

Input data values: strings under 1,000,000 chars. Fine.

I think this is good. Let me also consider adding a case with no separators for diversity — but I have 8 already. Fine.

Actually, wait: the harness runs all 8 and keeps the 4 doing the most work. We want at least 4 substantial. colon-plain, colon-escaped, equals-include-empty, equals-no-empty, spaces, dense, backslash, mixed — all substantial. Good.

Let me finalize.