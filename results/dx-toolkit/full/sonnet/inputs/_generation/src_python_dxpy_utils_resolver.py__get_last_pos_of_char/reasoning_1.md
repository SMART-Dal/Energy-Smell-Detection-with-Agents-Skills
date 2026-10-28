The function `get_last_pos_of_char(char, string)` — simple string scanning. The worst case is when the string is full of backslashes causing the inner loop to walk far, or many occurrences of char causing rfind to repeatedly fail... Actually the loop: pos = len(string); then rfind in string[:pos]. If found at pos, count backslashes before. If odd, loop again with pos = that position, so string[:pos] excludes it. So each iteration finds the previous occurrence. Worst case: many occurrences of char each preceded by odd backslashes → many iterations, and each iteration does a slice `string[:pos]` which is O(n) copy! So string[:pos].rfind is O(pos). With many occurrences, total O(n * k).

So a string with many occurrences of char, where most are escaped (odd backslashes), makes the function do O(n*k) work. E.g., char = '/', string = "\\/\\/\\/..." repeated many times.

Actually careful: if pos found and num_backslashes odd, we continue with pos = pos (the found position), then string[:pos] excludes it. Next rfind finds previous occurrence. So iterations = number of occurrences scanned until one is unescaped. Each rfind is O(pos) due to slicing plus rfind scanning. So O(n^2 / something) worst case.

Let's design inputs:
- Typical path strings: "/a/b/c" small.
- Long path with many slashes.
- Strings of escaped chars: '\\/' repeated.
- char not present: rfind returns -1 immediately — cheap.
- char at position 0.
- Huge string ~ 1MB with many occurrences.

Keep under 200ms per call. Let's estimate: n = 200_000 with occurrences every 2 chars ('\\/' repeated 100k times), each rfind is O(pos) → total ~ sum of positions ~ 100k*200k = 2e10 — too slow. Need smaller.

Let's target n=20_000 with occurrences every 2 chars → 10_000 iterations, average slice ~10_000 chars → 1e8 char copies... roughly 100ms in Python? Slicing is fast C memcpy. 1e8 bytes ≈ 0.05s. Plus rfind. Maybe ok. Let's use a few sizes.

Actually, better to have the escaped ones so it walks back a lot: each odd backslash means continue. If all occurrences are escaped, we walk through all of them.

Let me design:

1. typical short path: get_last_pos_of_char('/', "/home/user/data/file.txt") — trivial but realistic.
2. long path with many unescaped slashes → first rfind finds last one, returns quickly. But slice of 100k is fine.
3. escaped slashes: '\\/' repeated n times, char '/'. All odd backslashes → walks all. This is the heavy one.
4. mixed: random strings with slashes and backslashes.
5. char not found: string of 1MB 'a's, char '/'.
6. char ' ' on a long text.
7. colon paths like "project:folder:subfolder".
8. Double backslashes before char → even → returns immediately at last occurrence, but slice large.

We need exactly 8 cases, run on original, keep 4 doing most work.

Let's make sizes moderate so each call ~1ms-200ms.

Case: escaped slashes heavy: string = "\\/" * k. For k=5000, n=10000, iterations 5000, sum of positions ~ 5000*10000/... each rfind on string[:pos] where pos decreasing by 2 each time → total ~ 5000 * 5000 avg = 2.5e7 char scanned. Fast, ~10ms. Good. Maybe use k=20000 → n=40000, total ~ 4e8... 0.4s? Hmm. Let's use k=10000 → 1e8 → maybe 0.1s. Fine.

Let's include varied cases.

checks(): edge inputs:
- empty string, char '/': returns -1.
- single char string.
- char not present.
- None char maybe raises? get_last_pos_of_char(None, "abc") → string[:pos].rfind(None) raises TypeError. Could include but risky — checks may raise, that's fine. Let's keep simple: empty char? char="" → rfind("") returns pos... then backslash counting... returns pos. Fine.

Let me write:

```python
import random
from dxpy.utils.resolver import get_last_pos_of_char

def checks():
    return [
        ("empty-string", lambda: ('/', "")),
        ("single-char", lambda: ('/', "/")),
        ("char-absent", lambda: ('/', "abcdef")),
        ("none-char", lambda: (None, "abc")),
    ]
```

Maybe 3 checks. Fine, "2 or 3". Let's do 3.

cases(): build strings at module level.

```python
_rng = random.Random(0)

# realistic long path
_long_path = "/" + "/".join(f"dir{i}_{_rng.randrange(10**6)}" for i in range(2000)) + "/file.txt"

# escaped slashes
_escaped = "\\/" * 10000

# mixed random
def _mixed(n, seed):
    rng = random.Random(seed)
    chars = []
    for _ in range(n):
        r = rng.random()
        if r < 0.3:
            chars.append('/')
        elif r < 0.5:
            chars.append('\\')
        else:
            chars.append(rng.choice('abcdefgh'))
    return ''.join(chars)

_mixed_str = _mixed(50000, 1)
_no_char = 'a' * 200000
```

Wait, for mixed: with unescaped slash most likely found at last occurrence quickly... need many escaped. Actually the heavy part is when the last occurrence is escaped and we walk back. In random mixed, last occurrence of '/' likely unescaped → quick. But the slicing string[:pos] with pos = n is one copy of 50000 — cheap. So that's a light case. Still fine to include for diversity but not heavy.

To make heavy: force the last slash escaped by odd backslashes. E.g., ensure string ends with "\\/" and many earlier slashes escaped too.

Let's create a case: string = ('x/' * 5000) + ... hmm.

Design heavy case A: many escaped slashes: "\\/"*k → each slash preceded by exactly 1 backslash → odd → all escaped → walks all k occurrences. Good.

Design heavy case B: slashes separated by long filler: ("/" + "a"*100) repeated k, last one escaped. Actually to force walking many: make the last slash escaped, and the previous slashes also escaped. Simplest: prefix each slash with a single backslash.

Alternative: string = ("ab" + "\\/" ) ... eh.

Let's do variants:
- escaped_1: "\\/" * 8000
- escaped_2: "\\" + "/"*... no, "//" would be even? "\\//" — the slash at index 1 preceded by one backslash → odd escaped. Hmm.

Let's do "x\\/" repeated: 'x','\\','/' → slash escaped. Each iteration walks back 2 chars. Fine, similar cost.

- Case with long runs between slashes: ("a"*50 + "\\/") * 2000 → n = 2000*52 = 104000. Each rfind scans string[:pos] which is O(pos). Sum over 2000 iterations with pos decreasing by 52 → avg 52000 → total 1e8 char scanning. ~0.05-0.1s. Good heavy case.

- Case where char is ':' with many colons unescaped → quick (first rfind). Not heavy.

- Case with char not present in huge string → one rfind O(n). Cheap.

- Case with even backslashes: "\\\\/" i.e. two backslashes then slash → even → returns immediately. Slice cost O(n).

Let me also include a case with backslashes only, char '/' not found → rfind returns -1 quickly.

Let's define 8 cases:

1. short-path: "/home/user/data/file.txt" (realistic small)
2. long-path: _long_path with many unescaped slashes (first rfind returns) — heavy due to slicing? n=~2000*10=20000, cheap.
3. escaped-all: "\\/" * 8000
4. long-gaps-escaped: ("a"*50 + "\\/") * 2000
5. mixed-random: _mixed(50000,1)
6. no-occurrence: "a"*300000
7. double-backslash: "\\\\" pattern with "/" at end... 
8. colons: "project:" + ":"*... realistic colon path.

Let me think about which 4 do the most work: 3, 4, 5?, 6? Case 6 is one rfind over 300000 chars — fast C. Case 5: last slash probably unescaped → one slice of 50000 + rfind. Fast. Hmm.

The heaviest are 3 and 4. Need more heavy ones to have a good spread. Let's add:

- escaped with two backslashes per slash? "\\\\/" = 3 backslashes + slash → odd (3) → escaped, walk back 3. That works too.

- Deep walk: "\\" + "/" repeated? "\\/" already.

Let me create a case where slash appears very frequently and all escaped with long tail: 

Case: string = "\\/" * 15000 → n=30000, iterations 15000, sum positions ~ 15000*30000/2 ≈ 2.25e8 → maybe 0.2-0.3s. Risky. Use 10000.

Case 4: gaps 50: heavy.

Another heavy: slash preceded by 1 backslash but separated by random-length filler:
"".join("a"*rng.randint(0,30) + "\\/" for _ in range(3000)) → n ≈ 3000*(15+2)=51000, iterations 3000, sum ~ 3000*25500 ≈ 7.6e7. Good.

Also a case where the answer is -1 but there are many backslashes: string = "\\"*100000, char='/' → rfind returns -1 immediately. Cheap.

Let's just include diverse ones; the harness picks top 4.

Let me also consider char=' ' on a long text with spaces escaped.

Fine. Let me write final code.

Module-level building: need to be careful about time (<10s). All fine.

Memory: strings up to ~300KB, fine.

Let me write:

```python
import random
from dxpy.utils.resolver import get_last_pos_of_char


def _rand_str(n, seed, alphabet):
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(n))


_long_path = "/" + "/".join(
    "dir%d_%s" % (i, _rand_str(6, i, "abcdefghijklmnop")) for i in range(1500)
) + "/file.txt"

_escaped_all = "\\/" * 9000

_gapped_escaped = "".join("a" * 50 + "\\/" for _ in range(2000))

_rng2 = random.Random(0)
_gapped_random = "".join("a" * _rng2.randint(0, 30) + "\\/" for _ in range(3000))

_mixed = _rand_str(60000, 1, "abcde/\\")  # hmm random choice from alphabet

_no_occ = "a" * 300000

_backslashes = "\\" * 120000

_colon_path = "project-abc:" + ":".join(...)
```

Wait _mixed with alphabet "abcde/\\": the last slash might be escaped. Fine.

Also case: char ' ' with text: " ".join(...) with escaped spaces? Let's just do a text with spaces.

Let's finalize 8 cases:

1. "typical-path": ('/', "/home/user/data/file.txt")
2. "long-unescaped-path": ('/', _long_path)
3. "all-escaped-slashes": ('/', _escaped_all)
4. "gapped-escaped": ('/', _gapped_escaped)
5. "gapped-random-escaped": ('/', _gapped_random)
6. "mixed-random": ('/', _mixed)
7. "no-occurrence": ('/', _no_occ)
8. "many-colons": (':', _colon_path)

_colon_path: e.g. "proj:" + ":".join("f%d"%i for i in range(5000)) → last colon unescaped → quick. To make it walk, escape each colon: "\\:" repeated. Let's do "proj" + "\\:"*5000. That walks all. Good — diverse char.

Actually let's make case 8: (' ', text) with escaped spaces? Let's do colon escaped, that's realistic-ish for resolver (paths with colons escaped? maybe). Fine.

Let me finalize.

For _mixed, let's ensure a decent number of slashes: alphabet "abcde" plus '/' and '\\' with weighting. Use rng.choice over a list with more slashes: "abcde//\\\\" — hmm. Simpler: use random.random.

Let me write _mixed properly:

```python
def _mixed(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.25:
            out.append('/')
        elif r < 0.45:
            out.append('\\')
        else:
            out.append(rng.choice('abcdefgh'))
    return ''.join(out)
```

n=60000 → ~15000 slashes, ~12000 backslashes. The last slash: 50% chance unescaped? Actually if preceded by backslash... The scan: last slash at some pos, count backslashes before it (0 or 1 or 2...). Likely returns quickly. It's a light case but diverse. Fine.

To guarantee at least one heavy random case, add explicit ending: _mixed ends with "\\/" appended → forces walking at least one step. Eh.

Actually let's make one case designed to walk a lot with random: force each slash escaped by preceding with exactly one backslash at random-ish positions... the gapped_random covers that.

Good enough. The harness keeps 4 heaviest; we have at least 3-4 heavy.

Let me double-check heavy cases' runtimes roughly.

Case 3: "\\/" * 9000 → n=18000. Iterations: 9000 (each slash escaped). Each iteration: pos = string[:pos].rfind('/'). string[:pos] creates a copy of length pos. pos goes 18000, 17998, ... So total copied ≈ 9000 * 9000 = 8.1e7 bytes. Plus rfind scan similar. ~0.1s. Fine.

Case 4: gapped_escaped: "a"*50 + "\\/" repeated 2000 → n=2000*52=104000. Positions of slashes: 52k-1, ... decreasing by 52. 2000 iterations, avg pos 52000 → total copy 1.04e8. rfind scans from end of slice backward — it finds at the very end quickly actually! rfind scans from the right, so it finds the slash at the last position immediately, no scanning. But the slice copy is O(pos). So total ~1e8 bytes copy → ~0.05s. Plus 2000 iterations overhead. OK ~0.1s.

Hmm but wait: after finding slash at pos, we check backslashes. Slash at index pos, preceded by "\\" at pos-1, pos-2? "a"*50 + "\\/" → positions: a(0..49), \(50), /(51). So slash at 51, backslash at 50, char at 49 is 'a' → count=1 odd → continue. Next iteration pos=51, string[:51] ends at index 50, rfind('/') → finds nothing before → returns -1? Wait, string[:51] = indices 0..50, which includes 'a'*50 + '\\' — no slash. So rfind returns -1 → function returns -1!

Oops. The loop: pos = string[:pos].rfind(char). If we set pos=51, then string[:51] excludes index 51 (the slash). Next rfind finds the previous slash at... the previous slash is at index 51-52 = -1? No: pattern repeats every 52. First slash at 51, next at 103, etc. So going down: 51, then string[:51] has no slash → -1 → return -1.

Hmm, that means the function returns -1 even though there are slashes? Wait no: the loop starts with pos = len(string), rfind finds the LAST slash at index n-1? Let's see: last block is "a"*50+"\\/", last char is '/' at n-1. So first rfind finds n-1. Backslash at n-2, odd → continue. pos = n-1. string[:n-1] = everything except last char. rfind finds previous slash at n-1-52 = n-53. Backslash at n-54 → odd → continue. Etc. So it walks all 2000 slashes. Then eventually pos = 51, string[:51] no slash → -1 → return -1. Good, that's the walk. My mistake earlier.

So case 4 walks 2000 iterations, each with slice of avg ~52000 → 1e8. Good.

Case 5: gapped_random, 3000 iterations, avg gap 15 → n≈51000, slices avg 25500 → 7.6e7. Good.

Case 3: 9000 iterations of slices avg 9000 → 8.1e7. Good.

So the top 4 heavy: 3, 4, 5, and maybe 8 (colon escaped 5000 → slices avg 5000... n=10000, 5000 iterations avg 5000 = 2.5e7). Or 2 (long path: n≈1500*11=16500, one slice + rfind → cheap). Or 6.

Anyway fine.

Case 8: "proj" + "\\:"*5000 → char ':' → n=10004, 5000 iterations, slices avg 5000 → 2.5e7. Similar to case 3? Slightly less.

Alright.

One concern: repeated calls — the function doesn't modify inputs, so returning the same string each time is fine.

Check outputs: return int. Fine.

Now checks(): 3 small edge inputs. Include one that raises? "none-char": (None, "abc") → string[:3].rfind(None) raises TypeError. Both original and modified should raise same. That's allowed ("These may raise"). But careful: the harness compares behaviour; if modified version handles None differently it'd differ, but that's the point. Include it. Actually risk: if modified version raises a different exception... unlikely to matter for our score. Keep it safe maybe. I'll include it — spec says odd types allowed.

Hmm, but if the modified version is expected to behave identically, an exception is fine. Let's include.

Let me write final code.

Also note: importing the module requires dxpy etc. Presumably available in the environment.

Final:

```python
import random

from dxpy.utils.resolver import get_last_pos_of_char


def _mixed(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.25:
            out.append('/')
        elif r < 0.45:
            out.append('\\')
        else:
            out.append(rng.choice('abcdefgh'))
    return ''.join(out)


_rng = random.Random(0)

_LONG_PATH = "/" + "/".join(
    "dir%d_%s" % (i, "".join(_rng.choice("abcdefghijklmnop") for _ in range(6)))
    for i in range(1500)
) + "/file.txt"

_ESCAPED_ALL = "\\/" * 9000

_GAPPED_ESCAPED = "".join("a" * 50 + "\\/" for _ in range(2000))

_grng = random.Random(7)
_GAPPED_RANDOM = "".join("a" * _grng.randint(0, 30) + "\\/" for _ in range(3000))

_MIXED = _mixed(60000, 1)

_NO_OCC = "a" * 300000

_COLON_ESCAPED = "proj" + "\\:" * 5000

_SHORT_PATH = "/home/user/data/file.txt"
```

Wait _rng.choice in a generator expression at module level — fine.

Cases list.

Also maybe add a case with char ' ' over a sentence with escaped spaces — skip, 8 already.

Let me count cases: short-path, long-path, escaped-all, gapped-escaped, gapped-random, mixed, no-occurrence, colon-escaped = 8. 

Write it out.