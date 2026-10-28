The function takes an iterable of (k, v) pairs and builds a dict, raising on duplicate keys. It's used as object_pairs_hook for json.loads.

Cases: 8 measured inputs. Need substantial work — lists of pairs. To make it work hard, large lists of pairs with unique keys and varied key types. Also cases that raise? No — cases must run to completion without raising. So all cases must have unique keys. But we want diverse paths: all-unique keys, string keys, int keys, tuple keys, mixed types, unhashable? no.

Let's build lists of pairs. Up to 1,000,000 values limit for args. Each pair is 2 values, so a list of 500k pairs = 1M values. Keep under. Let's use up to ~200k pairs to be safe (400k values).

Work per call: dict insertion of ~200k items → maybe 20-50 ms. Good.

Cases:
1. Many unique string keys, random.
2. Many unique int keys.
3. Mixed key types (int, str, tuple, frozenset, None, bool).
4. Keys with hash collisions? Hard to force. Could use strings designed to collide in Python's hash? That's tricky and version-dependent.
5. Large values (long strings) — memory heavy but work is insertion.
6. Nested tuples as keys.
7. Ordered pairs from json-like structure.
8. Keys that are floats, bytes, etc.

Also cases should differ in size and distribution. Let's make 8.

Also note the function iterates `for k, v in ordered_pairs` — pairs must be 2-element sequences. Use tuples.

Ensure no duplicates. Use rng with seed.

For string keys, use f"k{i}" unique — but "avoid uniformity or patterns that a simple trick could exploit". Since we need unique keys, use random strings.

Let's generate random strings of random lengths.

Case sizes: vary 50k, 100k, 200k.

Also we could include a case with many duplicate-free but with keys that are equal by hash... not needed.

Note: the function returns dict with same number of items; output comparison under 100k values? "keep what it returns under about 100 000 values". Hmm, a dict of 200k items returns 200k values — that exceeds 100k! Careful. The output is compared in full. So keep outputs under 100k values.

So limit to ~50k pairs per case → dict of 50k items = 50k values. That's fine. But then work per call is smaller. 50k insertions ~ 5 ms. Acceptable (1ms-200ms).

Actually "about 100 000 values" — 50k dict entries is 50k values. Let's use up to 90k pairs. Hmm, but the args also: 90k pairs = 180k values, under 1M. Fine.

Let's use sizes 20k, 50k, 80k, 90k etc.

Actually let's be a bit conservative: max 90k pairs.

Let me design:

- case A: 90k unique short string keys, int values.
- case B: 90k unique int keys (random large ints), string values.
- case C: 60k tuple keys (pairs of ints), varied.
- case D: 80k mixed-type keys: ints, strings, floats, bytes, None, bool, frozenset, tuple.
- case E: 50k keys with long string values (values heavy) - work is still insertion.
- case F: 90k keys generated as random strings of varying length (longer strings, more hashing work).
- case G: 70k nested structure pairs where keys are tuples of strings.
- case H: pairs given as lists (not tuples) — the function unpacks k, v; lists work. Also could be a generator? A generator would be consumed... but the args are rendered before/after each call — a generator would be exhausted after first call, so subsequent calls get nothing. Avoid generators. Use lists of lists.

Also the outer container: could be a list of 2-lists.

Careful: "Its arguments are rendered before and after each call to see whether it changed them" — rendering a 90k list is fine.

Let me write helper functions.

For mixed types, need to ensure no duplicates across types. E.g. True and 1 collide (hash equal, equal). 1 and 1.0 collide. So be careful: avoid mixing bools with ints, ints with floats. Use distinct ranges.

Let's define:

def _str_keys(n, seed, minlen=8, maxlen=16): returns list of (key, value) tuples.

Actually simpler: build pairs directly.

Case D mixed: use:
- strings f"s{i}"
- ints i (but strings distinct from ints, fine)
- floats: use i + 0.5 (distinct from ints since not equal)
- bytes: b"b%d" % i
- None (only one)
- frozenset([i]) 
- tuples (i, "x")
Careful: float 1.5 vs int? no collision. bytes vs str distinct. frozenset vs tuple distinct. None unique.

But wait, tuple (i, "x") and frozenset not equal. Fine.

Just need uniqueness — since each type family uses distinct i and types differ, no duplicates.

Let me write:

```python
import random

def _pairs_strings(n, seed, minlen=6, maxlen=20):
    rng = random.Random(seed)
    out = []
    seen = set()
    while len(out) < n:
        L = rng.randint(minlen, maxlen)
        s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(L))
        if s in seen:
            continue
        seen.add(s)
        out.append((s, rng.randint(0, 10**9)))
    return out
```

Hmm, generating 90k random strings char by char might be slow-ish but fine (setup under 10s). Actually 90k * 13 chars = ~1.2M rng.choice calls. That's maybe 1 second. OK.

Simpler: use uuid-like or f"{rng.getrandbits(64):016x}" plus random length padding. Let's do:

```python
def _rand_str(rng, minlen, maxlen):
    L = rng.randint(minlen, maxlen)
    return "".join(rng.choice(_ALPHABET) for _ in range(L))
```

Fine.

For int keys: rng.randrange(0, 2**63) unique.

Let me write the cases:

```python
_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def _str_pairs(n, seed, minlen=6, maxlen=18):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        s = "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(minlen, maxlen)))
        if s in seen:
            continue
        seen.add(s)
        out.append((s, rng.randrange(10**9)))
    return out

def _int_pairs(n, seed):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        k = rng.randrange(-2**62, 2**62)
        if k in seen:
            continue
        seen.add(k)
        out.append((k, "v%d" % rng.randrange(10**9)))
    return out

def _tuple_pairs(n, seed, width=3):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        k = tuple(rng.randrange(10**6) for _ in range(width))
        if k in seen:
            continue
        seen.add(k)
        out.append((k, rng.random()))
    return out

def _mixed_pairs(n, seed):
    rng = random.Random(seed)
    out = []
    count = 0
    i = 0
    families = 7
    per = n // families + 1
    # strings
    seen = set()
    for j in range(per):
        s = "s%d_%s" % (j, "".join(rng.choice(_ALPHABET) for _ in range(8)))
        if s in seen: continue
        seen.add(s)
        out.append((s, j))
    # ints
    for j in range(per):
        out.append((rng.randrange(2**62), j))
    # floats (non-integral)
    for j in range(per):
        out.append((rng.random() * 10**9 + 0.5, j))
    # bytes
    for j in range(per):
        out.append((b"b%d" % j, j))
    # tuples of strings
    for j in range(per):
        out.append(((str(j), str(j*7)), j))
    # frozensets
    for j in range(per):
        out.append((frozenset((j, j+1)), j))
    # None + bools? bools collide with ints 0/1. Use True/False only if no 0/1 ints... risky.
    out.append((None, "none"))
    return out[:n]
```

Hmm floats: rng.random()*1e9 + 0.5 is non-integral, so distinct from ints. But could two floats collide? Very unlikely; and to be safe use j-based: float(j) + 0.5 — distinct from each other and from ints. Yes, use float(j) + 0.5.

frozenset((j, j+1)) for j in range(per) — distinct sets? frozenset({0,1}) vs {1,2} distinct. Yes.

Tuples (str(j), str(j*7)) distinct.

Bytes b"b%d" distinct.

So all unique. Good.

Now the outer container as list of lists case: convert pairs to lists.

Also a case where the pairs are a large list of 2-element lists.

Also case where values are large strings (long values) — memory: 50k * 1KB = 50MB. Too much maybe. Use 20k * 200 chars = 4MB. Work is less though. Skip; instead vary key length.

Let's think about which 4 cases do most work — the harness keeps 4. All similar sized so fine.

Let's finalize 8 cases:

1. "strings-90k" — 90k random string keys, int values.
2. "ints-90k" — 90k random int keys.
3. "tuples-60k" — 60k tuple keys width 3.
4. "mixed-70k" — mixed types.
5. "lists-90k" — pairs as lists, string keys.
6. "longkeys-50k" — long string keys (60-120 chars) → more hashing work.
7. "small-20k" — smaller, quick.
8. "nested-tuples-50k" — tuple keys of width 5 with mixed element types.

Need to ensure the thunk returns the args fresh each time? The function doesn't modify the input. It only reads. So we can reuse the same list. But rendering before/after — unchanged, fine. Reusing is fine and cheap.

Actually careful: the function builds a new dict each time; input unchanged. Good.

Let's compute memory: 90k pairs of tuples: each tuple ~56 bytes + list pointers 8*90k... about 90k*(56+8) ≈ 6MB plus strings. Fine.

Now checks(): small edge inputs, may raise.
- empty: ([],)
- single pair: ([("a", 1)],)
- duplicate: ([("a",1),("a",2)],) — raises ValueError. Good, checking identical behaviour (both raise).
- maybe None: (None,) raises TypeError. Include? "2 or 3 small edge inputs". Let's do 3: empty, single, duplicate.

Actually the duplicate case raising — that's fine, checks may raise.

Let me also consider: pairs with wrong arity, e.g. [("a",)] → ValueError from unpacking. Could add but limit to 3.

Write code.

One thing: the module import — `from dxpy.utils import _dict_raise_on_duplicates`. Need `import dxpy.utils`? The instruction says import exactly as shown. I'll do `from dxpy.utils import _dict_raise_on_duplicates`. But does importing dxpy.utils work standalone? It imports dateutil, .. compat etc. Presumably environment has it. We'll just do it.

Let me write the final code.

For long keys case, generate strings of length 60-120.

Let me write helper `_str_pairs(n, seed, minlen, maxlen)`.

For nested tuples width 5 with mixed element types: elements could be ints and strings and floats — need uniqueness of the tuple; random generation with collisions checked.

Let me just do width 4 with rng.randrange.

Final code:

```python
import random

_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _rand_str(rng, minlen, maxlen):
    n = rng.randint(minlen, maxlen)
    return "".join(rng.choice(_ALPHABET) for _ in range(n))


def _str_pairs(n, seed, minlen=6, maxlen=18):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        s = _rand_str(rng, minlen, maxlen)
        if s in seen:
            continue
        seen.add(s)
        out.append((s, rng.randrange(10 ** 9)))
    return out


def _int_pairs(n, seed):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        k = rng.randrange(-(2 ** 62), 2 ** 62)
        if k in seen:
            continue
        seen.add(k)
        out.append((k, "v%d" % rng.randrange(10 ** 9)))
    return out


def _tuple_pairs(n, seed, width):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        k = tuple(rng.randrange(10 ** 6) for _ in range(width))
        if k in seen:
            continue
        seen.add(k)
        out.append((k, rng.random()))
    return out


def _mixed_pairs(n, seed):
    rng = random.Random(seed)
    out = []
    per = n // 7 + 1
    for j in range(per):
        out.append(("s%d_" % j + _rand_str(rng, 4, 10), j))
    for j in range(per):
        out.append((rng.randrange(2 ** 62), j))
    for j in range(per):
        out.append((float(j) + 0.5, j))
    for j in range(per):
        out.append((b"b%d" % j, j))
    for j in range(per):
        out.append(((str(j), str(j * 7 + 1)), j))
    for j in range(per):
        out.append((frozenset((j, j + 1)), j))
    out.append((None, "none"))
    return out[:n]
```

Wait: "s%d_" % j + _rand_str could collide? Very unlikely; and if it does, duplicate key raises. Risky. Better make deterministic unique: "s%d" % j is unique. Use that plus random suffix but ensure uniqueness by including j. "s%d_%s" % (j, rand) — unique due to j prefix. Good.

Also floats float(j)+0.5 vs ints rng.randrange(2**62) — could an int equal a float? float(j)+0.5 is non-integral, so no. Good.

frozenset((j, j+1)) unique per j. Good.

Tuples of strings unique. Bytes unique. None unique.

But careful: tuple (str(j), str(j*7+1)) — could it equal a frozenset? No.

Also mixed case: "s%d_..." strings vs bytes distinct. Good.

Now the "lists" case: convert pairs to lists.

```python
_LIST_PAIRS = [list(p) for p in _str_pairs(90000, 5)]
```

Hmm, need to make sure the function doesn't modify them — it doesn't.

Let's define module-level data.

Case labels distinct.

Let me finalize sizes:
1. strings-90k: _str_pairs(90000, 11)
2. ints-90k: _int_pairs(90000, 12)
3. tuples-60k: _tuple_pairs(60000, 13, 3)
4. mixed-70k: _mixed_pairs(70000, 14)
5. lists-90k: list version of _str_pairs(90000, 15)
6. longkeys-50k: _str_pairs(50000, 16, 60, 120)
7. nested-tuples-50k: _tuple_pairs(50000, 17, 6)
8. small-20k: _str_pairs(20000, 18)

Check output sizes: dict entries = n, all ≤ 90k < 100k. Good.

Arg value counts: 90k pairs = 180k values < 1M. Good.

Timing: 90k insertions of strings ~ 15-30 ms. Good.

Building all: string generation 90k*~12 chars ~ 1M rng.choice calls per case, several cases → maybe 3-5s total. Acceptable but let's reduce by using faster generation. Alternative: generate random bytes and hex. Let's use `rng.getrandbits` based:

```python
def _rand_str(rng, minlen, maxlen):
    n = rng.randint(minlen, maxlen)
    return "".join(rng.choice(_ALPHABET) for _ in range(n))
```

1M choices ~ 0.3s. Fine. Total maybe 2s. OK.

Actually for longkeys case 50k * 90 chars = 4.5M choices ~ 1.5s. Acceptable but let's reduce longkeys to 40k. Fine, keep 50k.

Total under 10s hopefully. Let's be a bit careful: strings-90k ~1M, lists-90k ~1M, longkeys 4.5M, small 20k, mixed small. Total ~7M choices ~ 2-3 s. Plus dict building. OK.

Now checks:

```python
def checks():
    return [
        ("empty", lambda: ([],)),
        ("single", lambda: ([("only", 1)],)),
        ("duplicate", lambda: ([("a", 1), ("b", 2), ("a", 3)],)),
    ]
```

Good.

Write final.