The function: `get_first_pos_of_char(char, string)`. Note the docstring is wrong—it actually finds the first unescaped occurrence? Let's read the code.

```
first_pos = -1
pos = len(string)
while pos > 0:
    pos = string[:pos].rfind(char)
    if pos == -1:
        return first_pos
    num_backslashes = 0
    test_index = pos - 1
    while test_index >= 0 and string[test_index] == '\\':
        num_backslashes += 1
        test_index -= 1
    if num_backslashes % 2 == 0:
        first_pos = pos
return first_pos
```

It repeatedly finds rfind from the end, and records the last position found with even backslashes... Actually it keeps going until pos == -1, so it iterates over all occurrences. first_pos ends up being the first (leftmost) occurrence with even backslashes... wait, no. It searches from the end backwards. Each time rfind finds an occurrence at pos. If unescaped, first_pos = pos. Then loop continues with pos > 0, string[:pos].rfind(char) finds the next occurrence to the left. So it keeps updating first_pos to the leftmost unescaped occurrence. So it returns the first unescaped occurrence. Note if pos == 0 found... string[:0] is empty, rfind returns -1, loop exits.

Worst case: many occurrences. Each iteration does string[:pos].rfind(char) — O(pos) string slice copy plus rfind. So for a string of length n with many occurrences, it's O(n^2). That's the stress: long strings with many occurrences of char.

Also the backslash counting: many backslashes before char.

So cases: 
- long string with many '*' occurrences
- long string with many '?' 
- long string with many '=' 
- string with many escaped occurrences (backslashes)
- char not present (fast: one rfind returns -1)
- char at position 0
- mixed

We need 8 cases, each ~1ms-200ms. Let's design.

Let's use strings of length maybe 20000-50000 with many occurrences. O(n^2) with n=50000 and occurrences every few chars → number of iterations ~ n/k, each slice of length ~pos. Total ~ sum of positions ~ n^2/(2k). With n=50000, k=5: 50000^2/10 = 2.5e8 char copies... that's maybe 0.1-0.5s. Too much maybe. Let's be careful.

Let's target ~10-100ms. With n=20000, occurrences every 4 chars: iterations 5000, each slice average 10000 → 5e7 char copies. C-level memcpy, fast, ~10-20ms. Plus rfind scanning. Probably fine.

Actually rfind scans the slice from the end, finds near the end quickly, so rfind cost is small. The slice copy dominates: O(pos) each. Sum ≈ n^2/(2k).

Let's compute: n=20000, k=4 → 20000^2/8 = 5e7 bytes copied → ~15ms. Good.

n=50000, k=4 → 3.1e8 → ~100ms. Borderline OK.

Let's make varied cases:

1. "many-stars": string of length 20000, '*' every ~5 chars, no backslashes. char='*'.
2. "many-questions": length 30000, '?' frequent.
3. "escaped": string with '\\' before '*', alternating escaped/unescaped. This triggers backslash counting loops.
4. "all-backslashes-then-star": lots of backslashes.
5. "no-char": char not present, long string → fast single rfind. Hmm, that's cheap. But we need 8 cases; the top-4 by work are kept. Cheap ones are fine as long as they run.

Actually the instructions say cases() gives 8 measured inputs, we run on original and keep 4 that do most work. So we should have 8 diverse, and ideally heavy ones. Let's make most heavy.

Let's think about worst case: char appears at every position? Then iterations = n, each slice length ~pos, sum = n^2/2. n=10000 → 5e7. Hmm.

Let's design various:

Case A: path-like strings (realistic! repository uses it on paths). E.g. a long glob path with many '*'. Realistic: "project-123:/folder/*/sub/*/..." Hmm.

Let's just do:

1. `("*", many_stars)`: n=20000, '*' every 4 chars.
2. `("?", many_qs)`: n=20000, '?' every 4 chars.
3. `("=", many_eqs)`: n=30000, '=' every 6 chars (like key=val repeated).
4. `(":", long_path)`: colon appears many times.
5. escaped stars: pattern `\\*` repeated — every star escaped, so no unescaped found; loop runs over all n/2 occurrences. Also backslash counting.
6. mixed escaped: half escaped, half not.
7. many backslashes before a star: e.g. '\\\\...' 
8. char not present at all: long string, single rfind → very fast. Include as a diverse "miss" case.
9. char at very end.

Let's produce 8:

- "stars-dense": n=20000, '*' every 4 chars, no escapes.
- "questions-dense": n=20000.
- "equals-dense": n=30000.
- "colons-path": realistic path string with many colons... maybe just many ':'.
- "escaped-stars": every '*' preceded by single backslash → all escaped, loop iterates over all occurrences.
- "mixed-escapes": random mix of 0-3 backslashes before stars.
- "long-backslash-run": string of many backslashes then '*'.
- "miss": long string without char.

Hmm, but "miss" is very fast, and "long-backslash-run" — the backslash counting loop is O(number of backslashes) each occurrence, but if only one star at the end after 20000 backslashes, the counting loop runs 20000 steps in Python — that's ~ms. Actually Python-level loop 20000 iterations ≈ 1-2 ms. Fine.

Let's also consider: the outer while loop condition is `pos > 0`. If char found at pos 0, then first_pos=0, then loop: pos=0 → exit. Fine.

Let's think about timing more carefully. The inner backslash loop is Python-level, so it's slower per char than the slice copy. If we have many occurrences each preceded by a backslash, that's a lot of Python iterations.

E.g. escaped-stars: pattern "\\*" repeated 10000 times → string length 20000, 10000 occurrences, each with 1 backslash → 10000 Python iterations + 10000 slice copies averaging 10000 chars → 1e8 byte copies. That's maybe 30-50ms. OK.

Let's cap sizes so nothing exceeds ~200ms.

Let me estimate: slice copy of average L bytes is memcpy ~ 1e9 bytes/sec? Actually Python bytes/str slicing is quite fast, maybe 1-5 GB/s. Sum 1e8 → 20-100ms. Hmm, risky. Let's use smaller.

Let's target sums around 2e7-5e7 bytes.

For n=20000 with occurrence every 4: iterations 5000, average slice 10000 → 5e7. Probably ~20-50ms. Acceptable.

Let me reduce to be safe: n=15000, every 4 → 3750 iterations, avg 7500 → 2.8e7. ~10-30ms.

Hmm, but we want the top-4 to be heavy. Fine, all around similar.

Actually since only 4 heaviest are kept, and each must be ≥1ms, we're fine.

Let me build strings using random.Random(0) but with controlled structure.

Design generation helper:

```python
def _dense(n, char, gap, seed):
    rng = random.Random(seed)
    parts = []
    while total < n: append random filler of length gap-1 then char
```

Simpler: build a list of tokens and join.

Let me write:

```python
def _dense(char, gap, length, seed):
    rng = random.Random(seed)
    out = []
    total = 0
    alphabet = "abcXYZ019._-/\\"
    while total < length:
        filler = "".join(rng.choice(alphabet) for _ in range(gap - 1))
        out.append(filler)
        out.append(char)
        total += gap
    return "".join(out)[:length]  # careful truncation may cut char
```

Hmm truncation could remove the last char, that's fine.

Actually careful: filler uses alphabet that might contain the char. Let's exclude char from alphabet. Use a fixed alphabet without '*', '?', '=', ':'.

Let's just make filler = "abc" repeated deterministically? Instructions say avoid uniformity that a simple trick could exploit. But the function does no trick; it's a straightforward loop. Still, use random filler for realism.

Let me define alphabet per case excluding the char.

Escaped case: build pattern `\\` + char repeated.

Mixed escapes: for each occurrence, prepend rng.randint(0,3) backslashes.

But careful: with an odd number of backslashes, char is escaped; even → unescaped. The function counts backslashes immediately preceding. If filler contains backslashes, that also matters. Let's keep filler free of backslashes for escape cases.

Let's write the code.

```python
import random
from dxpy.utils.resolver import get_first_pos_of_char

_FILLER = "abcdefghijklmnopqrstuvwxyz0123456789._-/:@"

def _dense(char, gap, length, seed, alphabet=_FILLER):
    rng = random.Random(seed)
    alpha = alphabet.replace(char, "")
    out = []
    total = 0
    while total < length:
        out.append("".join(rng.choice(alpha) for _ in range(gap - 1)))
        out.append(char)
        total += gap
    return "".join(out)
```

gap=4, length=15000 → ~3750 occurrences, string length ~15000.

Case 1: char='*', gap=4, length=15000.
Case 2: char='?', gap=5, length=20000.
Case 3: char='=', gap=6, length=30000 (like key=value pairs). Hmm length 30000 gap 6 → 5000 occurrences, avg slice 15000 → 7.5e7. Might be 30ms. Reduce to 20000 → 5e7.

Let's do:
- stars: 15000, gap 4
- questions: 18000, gap 5
- equals: 24000, gap 6
- colon path: 20000, gap 8

Escaped stars: pattern "\\*" * 8000 → length 16000, 8000 occurrences all escaped. Each iteration: slice copy avg 8000 → 6.4e7, plus 8000 Python backslash checks. Maybe 30-60ms. OK, reduce to 6000 repetitions → length 12000, 6000 occurrences, sum 3.6e7.

Mixed escapes: 5000 occurrences with random 0-3 backslashes.

Long backslash run: single star preceded by 30000 backslashes... The inner loop is Python-level, 30000 iterations ~3ms. Plus rfind. Actually rfind scanning: string[:pos].rfind('*') where pos = len(string). The slice is 30001 chars, rfind scans from end, finds '*' at index 30000 immediately. Then backslash loop 30000 iterations. Then pos=30000, next rfind on string[:30000] which is all backslashes → -1, return. Total ~3ms. OK but small. Let's make it 50000 backslashes → 5ms. Hmm.

Better: many stars each preceded by long backslash runs? That could blow up. Let's do: alternating runs of 50 backslashes then a star, repeated 500 times → 500 occurrences, each with 50 backslash iterations = 25000 Python iterations, plus slice copies sum ~ (25000)^2/2... wait string length = 500*51 = 25500, sum of slice lengths ≈ 25500^2/2 = 3.2e8. Too much.

Let's keep it simpler. Maybe drop the long-backslash-run case and use other diverse cases.

Alternative diverse cases:
- char at position 0 only: string starts with char. Then first iteration finds pos=0, first_pos=0, loop exits (pos=0). Very fast though.
- char absent: fast.
- string with many backslashes but no char: fast.
- realistic glob path.

We need 8; some can be fast. The requirement is each ≥1ms ideally ("roughly 1ms to 200ms"). Hmm, "One call should take roughly 1 ms to 200 ms on the original." So all 8 should be ≥ ~1ms. Fast cases like "miss" would be microseconds. Let's avoid super-fast ones, or make them heavy enough.

A "miss" case with a very long string (e.g. 200000 chars) — rfind scans 200000 chars, maybe 0.1ms. Still fast. Hmm. Actually rfind in C on 200k chars is very fast (~50µs). So misses are inherently fast. Skip.

Let's make all 8 heavy-ish:

1. stars dense (gap 4, len 15000)
2. questions dense (gap 5, len 18000)
3. equals dense (gap 6, len 24000)
4. colons dense (gap 7, len 21000)
5. escaped stars all escaped (6000 pairs)
6. mixed escapes (5000 occurrences, 0-3 backslashes)
7. mostly-escaped with occasional unescaped (10000 pairs, 10% unescaped)
8. char at very end with long prefix of other chars + many occurrences of other char... hmm.

Alternative 8: dense with gap 2 (occurrences almost everywhere) on a shorter string, e.g. length 8000 gap 2 → 4000 occurrences, sum 1.6e7. That's a different distribution.

Or: a realistic path string from the repo: "project-xxxx:/folder1/subfolder2/.../*" — but the function is called with '*' or '?' or ':' or '='. Let's make case 4 realistic: a long path-like string with many ':' ... actually paths have few colons. Realistic usage: `_is_glob(path)` on a glob path. Let's construct a long glob pattern with many '*' and '?'.

Let me just do 8 diverse:

1. "stars-dense": gap 3, len 12000, char '*'.
2. "questions-dense": gap 4, len 16000, char '?'.
3. "equals-dense": gap 5, len 20000, char '='.
4. "colons-dense": gap 6, len 24000, char ':'.
5. "escaped-stars": "\\*" * 7000.
6. "mixed-escapes": 5000 occurrences with 0-3 backslashes.
7. "mostly-escaped": 8000 occurrences, 90% escaped (odd backslashes 1 or 3), 10% unescaped.
8. "glob-path": realistic long glob path with '*' and '?' at various places, searching '*'.

Let's estimate case 1: gap 3, len 12000 → 4000 occurrences, sum of slice lengths ≈ 12000^2/(2*3) = 2.4e7. ~10-30ms. Good.

Case 4: gap 6, len 24000 → 4000 occ, sum ≈ 24000^2/12 = 4.8e7. ~20-60ms.

Case 5: "\\*"*7000 → len 14000, 7000 occ, sum ≈ 14000^2/2 = 9.8e7. That's maybe 50-150ms. Plus 7000 Python iterations. Hmm, borderline. Let's use 4000 reps → len 8000, sum 3.2e7. Good.

Case 6: 5000 occurrences, each with filler of ~3 chars + backslashes. Let's build: for each occurrence, rng.randint(0,3) backslashes + a few filler chars + '*'. Length ~ 5000*5 = 25000, sum ≈ 25000^2/2 = 3.1e8. Too much! Because occurrences are dense relative to length.

Wait, sum of slice lengths = sum over occurrences of position ≈ n^2/(2*gap) where gap = average spacing. With n=25000 and gap 5, sum = 6.25e8/... let me compute: n^2/(2*gap) = 625e6/10 = 6.25e7. Right, I miscalculated. n^2 = 6.25e8, /10 = 6.25e7. OK fine.

Let me redo case 5: n=8000, gap=2, sum = 64000000/4 = 1.6e7. Good.

Case 1: n=12000, gap 3 → 144e6/6 = 2.4e7. Good.
Case 4: n=24000, gap 6 → 576e6/12 = 4.8e7. OK.

So the general formula sum ≈ n^2/(2*gap). Good.

Let's target sums 2e7-6e7 for each.

Case 2: n=16000, gap 4 → 256e6/8 = 3.2e7. Good.
Case 3: n=20000, gap 5 → 4e8/10 = 4e7. Good.

Case 7: mostly escaped, n=20000, gap 5 → 4e7, plus 8000 Python iterations. Good.

Case 8: glob path. Let's build a realistic path with maybe 100 segments each containing globs. That's short. Hmm, need it heavy. Let's make a long path: repeat "folder{i}/*/sub?/file{i}" many times. Let's just generate a long string with '*' and '?' scattered, gap ~6, length 20000 → sum 3.3e7.

Actually let's make case 8 use char='?' on a path with both. Fine.

Now, the function might be called with bytes? No, strings.

checks(): 2-3 small edge inputs:
- empty string: get_first_pos_of_char('*', '') → pos=0, while pos>0 false, return -1.
- char not in string.
- char at position 0.
- escaped only.

Let's do:
- ("empty-string", lambda: ('*', ""))
- ("single-char-match", lambda: ('*', "*"))
- ("escaped-only", lambda: ('*', "\\\\*"))  # i.e. '\\*' one backslash + star → returns -1

Wait careful with escaping in Python source: to get string `\*` (backslash + star) write "\\*".

Also maybe a None char? The function would raise TypeError on rfind(None)? Actually string.rfind(None) raises TypeError. That's an odd type case. But checks may raise. Let's include ("none-char", lambda: (None, "abc")) — raises TypeError. Hmm, "checked only for identical behaviour" — both original and modified would raise the same. Probably fine. But to be safe, keep checks simple and non-raising except maybe one. Let's include the None one; it's an odd type as suggested.

Actually the instruction says "These may raise." So fine.

Now the thunks: the function doesn't modify its arguments (strings immutable). So we can just return the prebuilt strings.

Let me write the code.

```python
import random

from dxpy.utils.resolver import get_first_pos_of_char

_FILLER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"


def _dense(char, gap, length, seed):
    rng = random.Random(seed)
    alpha = _FILLER
    out = []
    total = 0
    while total < length:
        out.append("".join(rng.choice(alpha) for _ in range(gap - 1)))
        out.append(char)
        total += gap
    return "".join(out)
```

Note: `_FILLER` doesn't contain '*', '?', '=', ':' so fine.

For escaped cases:

```python
def _escaped(char, reps, seed, unescaped_frac=0.0):
    rng = random.Random(seed)
    out = []
    for i in range(reps):
        if rng.random() < unescaped_frac:
            n_bs = rng.choice([0, 2])
        else:
            n_bs = rng.choice([1, 3])
        out.append("\\" * n_bs)
        out.append("".join(rng.choice(_FILLER) for _ in range(3)))
        out.append(char)
    return "".join(out)
```

Careful: filler chars must not be backslash or char. _FILLER has no backslash. Good.

Hmm but if filler is between backslashes and char, then the backslashes aren't immediately before char → char is unescaped. Oops! I need backslashes immediately before char. So order: filler, then backslashes, then char.

```python
        out.append("".join(rng.choice(_FILLER) for _ in range(3)))
        out.append("\\" * n_bs)
        out.append(char)
```

Good.

Case 5: all escaped: unescaped_frac=0.0, n_bs in {1,3}. reps=4000 → length ≈ 4000*(3+1+1)=20000. sum ≈ 20000^2/(2*5) = 4e7. Hmm, gap = 5. OK.

Wait, but with all escaped, the function iterates over all occurrences (since first_pos stays -1). Yes.

Case 7: mostly escaped, unescaped_frac=0.1, reps=4000.

Case 6: mixed random 0-3 backslashes → unescaped_frac irrelevant; use a different generator: n_bs = rng.randint(0,3). Let's just make a separate function or parameter.

Let me simplify: one function `_escaped(char, reps, seed, choices)` where choices is a list of backslash counts to sample from.

Case 6: choices = [0,1,2,3], reps 4000.
Case 5: choices = [1,3], reps 4000.
Case 7: choices = [1,1,1,1,1,1,1,1,1,0] weighted... simpler: use random with weights.

I'll write:

```python
def _escaped(char, reps, seed, weights):
    # weights: dict n_bs -> weight
    rng = random.Random(seed)
    choices = []
    for k, w in weights.items():
        choices.extend([k] * w)
    out = []
    for _ in range(reps):
        out.append("".join(rng.choice(_FILLER) for _ in range(3)))
        out.append("\\" * rng.choice(choices))
        out.append(char)
    return "".join(out)
```

Case 5: {1:1, 3:1}
Case 6: {0:1, 1:1, 2:1, 3:1}
Case 7: {0:1, 1:9}  (mostly escaped)

Case 8: glob path.

```python
def _glob_path(seed, segments=400):
    rng = random.Random(seed)
    parts = []
    for i in range(segments):
        parts.append("folder%d" % i)
        parts.append(rng.choice(["*", "sub?", "data*", "*.txt", "?x", "run"]))
    return "/".join(parts)
```

Hmm, with segments=400, length ≈ 400*(10+5) = 6000, occurrences of '*' maybe 200 → sum of slices ≈ 6000^2/(2*30) = 6e5. Too small. Need more.

Let's increase: segments=4000 → length 60000, occurrences ~2000, sum ≈ 60000^2/(2*30) = 6e7. Good. But length 60000 with gap 30 → 2000 occurrences. sum = n^2/(2*gap) = 3.6e9/60 = 6e7. Good, ~30-60ms.

Hmm, but building 4000 segments with random is fine.

Actually let's make it simpler and keep the glob case with '*' at ~every 8 chars. Let's just do a dense-ish glob: parts alternate "seg" and "*" mostly.

I'll do: for i in range(3000): append "f%d" % i, then rng.choice(["*","*","?","x","*"]). Length ~ 3000*8 = 24000, occurrences ~ 2400, gap ~10, sum ≈ 24000^2/20 = 2.9e7. Good.

Now the char for case 8 is '*'.

Let me now finalize the 8 cases:

1. ("stars-dense", lambda: ('*', _STARS))
2. ("questions-dense", lambda: ('?', _QUESTIONS))
3. ("equals-dense", lambda: ('=', _EQUALS))
4. ("colons-dense", lambda: (':', _COLONS))
5. ("all-escaped-stars", lambda: ('*', _ALL_ESCAPED))
6. ("mixed-escapes", lambda: ('*', _MIXED))
7. ("mostly-escaped", lambda: ('*', _MOSTLY_ESCAPED))
8. ("glob-path", lambda: ('*', _GLOB))

All built at module level.

Let me double check `_dense` length and gap: gap=3, length=12000 → 4000 iterations. Building 4000*2 chars via rng.choice - fine.

Wait, `rng.choice(alpha)` where alpha is a 64-char string - fine.

Now check the function's behavior on these to make sure no errors. Strings are str, char is str. Fine.

One concern: `string[:pos].rfind(char)` where char is a single char — fine.

Now let me verify timing isn't too extreme. Case 4: n=24000, gap 6, sum=4.8e7 bytes copied. Python string slicing creates a new str object: allocation + memcpy. 4.8e7 bytes total across 4000 slices of avg 12000 chars. Each slice allocation ~12KB. 4000 allocations. Should be maybe 20-50ms. Acceptable.

Case 8: n=24000, gap ~10, 2400 occurrences, sum 2.9e7. Fine.

Hmm, wait: in case 8 the string contains '?' too, but char is '*', so only '*' matters. Good.

Let me also double check case 5: n = 4000*(3+1+1) = 20000, occurrences 4000, gap 5, sum = 4e8/10 = 4e7. Plus 4000 Python backslash-count iterations (each 1-3). Fine.

Alright.

Actually, one more consideration: the loop `while pos > 0` — after finding at pos p and setting first_pos, next iteration slices string[:p]. If p becomes 0 after finding char at 0... loop condition pos>0 fails. Fine.

Also note: the function returns the FIRST unescaped occurrence. Let's sanity check with "\\*" (backslash star): pos=2, string[:2].rfind('*') = -1 → return -1. Good.

Now checks:

```python
def checks():
    return [
        ("empty-string", lambda: ('*', "")),
        ("char-at-start", lambda: ('*', "*abcdef")),
        ("escaped-only", lambda: ('*', "\\\\*")),
    ]
```

Hmm "escaped-only" — string is `\*` (one backslash, star). Python literal "\\\\*" is two chars backslash... wait: "\\\\*" in source = `\\*` (two backslashes then star). That's even → unescaped → returns 0. Let me use "\\*" in source = `\*` (one backslash + star) → returns -1. Good.

Let me use raw strings to be clear: r"\*" → backslash + star. Yes.

And char-at-start: ('*', "*abc") → pos=4, string[:4].rfind('*')=0, backslashes 0, first_pos=0, pos=0 → exit → return 0. Good.

Also maybe a None-char case: (None, "abc") → raises TypeError. Include? "an odd type". Let's include it as a 3rd... but we already have 3. Let's have 3 checks: empty, char-at-start, escaped-only. Maybe add None as 4th? Instructions say 2 or 3. Keep 3.

Hmm, but "an odd type" is suggested. Let's swap: use None char instead of char-at-start? I'll keep 3: empty-string, escaped-only, none-char. Actually char-at-start is a nice edge. Let's do:

1. ("empty-string", lambda: ('*', ""))
2. ("escaped-only", lambda: ('*', r"\*"))
3. ("none-char", lambda: (None, "abc"))

That covers empty, escape, odd type. Good.

Wait, does (None, "abc") raise? `string[:pos].rfind(None)` → TypeError: must be str, not None. Yes raises. Both versions raise identically. Fine.

Now, the module import: `from dxpy.utils.resolver import get_first_pos_of_char`. The module imports dxpy, .describe, ..compat, ..cli, ..exceptions. Should be importable if the repo is installed. Presumably yes.

Let me write final code.

One thing: `_FILLER` must not contain the chars we search for. It contains letters, digits, "._-". Good, no '*', '?', '=', ':'.

Let me write it out.

```python
import random

from dxpy.utils.resolver import get_first_pos_of_char

_FILLER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"


def _dense(char, gap, length, seed):
    rng = random.Random(seed)
    out = []
    total = 0
    while total < length:
        out.append("".join(rng.choice(_FILLER) for _ in range(gap - 1)))
        out.append(char)
        total += gap
    return "".join(out)


def _escaped(char, reps, seed, weights):
    rng = random.Random(seed)
    pool = []
    for k, w in weights.items():
        pool.extend([k] * w)
    out = []
    for _ in range(reps):
        out.append("".join(rng.choice(_FILLER) for _ in range(3)))
        out.append("\\" * rng.choice(pool))
        out.append(char)
    return "".join(out)


def _glob_path(seed, segments):
    rng = random.Random(seed)
    parts = []
    for i in range(segments):
        parts.append("f%d" % i)
        parts.append(rng.choice(["*", "*", "?", "x", "*"]))
    return "/".join(parts)


_STARS = _dense("*", 3, 12000, 0)
_QUESTIONS = _dense("?", 4, 16000, 1)
_EQUALS = _dense("=", 5, 20000, 2)
_COLONS = _dense(":", 6, 24000, 3)
_ALL_ESCAPED = _escaped("*", 4000, 4, {1: 1, 3: 1})
_MIXED = _escaped("*", 4000, 5, {0: 1, 1: 1, 2: 1, 3: 1})
_MOSTLY_ESCAPED = _escaped("*", 4000, 6, {0: 1, 1: 9})
_GLOB = _glob_path(7, 3000)
```

Wait _GLOB length: segments 3000, each "f%d" (2-5 chars) + "/" + choice (1 char) → ~3000*8 = 24000. Occurrences of '*': choice picks '*' 3/5 of the time → 1800. gap ~13. sum ≈ 24000^2/26 = 2.2e7. Fine.

Hmm, but "?" also appears; char is '*' so irrelevant.

Now cases:

```python
def cases():
    return [
        ("stars-dense", lambda: ('*', _STARS)),
        ("questions-dense", lambda: ('?', _QUESTIONS)),
        ("equals-dense", lambda: ('=', _EQUALS)),
        ("colons-dense", lambda: (':', _COLONS)),
        ("all-escaped-stars", lambda: ('*', _ALL_ESCAPED)),
        ("mixed-escapes", lambda: ('*', _MIXED)),
        ("mostly-escaped", lambda: ('*', _MOSTLY_ESCAPED)),
        ("glob-path", lambda: ('*', _GLOB)),
    ]
```

Good. All heavy-ish.

Let me double check the `_dense` for gap 3: filler length 2 per occurrence. rng.choice for 2 chars * 4000 = 8000 calls. Fine.

Case 4: gap 6, length 24000 → 4000 occurrences, filler 5 chars each → 20000 rng.choice calls. Fine.

Total build time small.

One more: is the function's first arg named `char` and second `string`? Yes. We pass positionally.

Done. Write the final answer.