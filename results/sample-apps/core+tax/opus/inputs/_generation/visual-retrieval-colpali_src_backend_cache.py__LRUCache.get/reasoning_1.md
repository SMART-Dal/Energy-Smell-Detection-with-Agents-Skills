We need to write checks() and cases() for LRUCache.get. The function is simple: check key in OrderedDict, move_to_end, return value, else None.

We need 8 measured cases that do substantial work. The work is dict lookup + move_to_end. To make it substantial, we need a large OrderedDict with many keys, and keys that hit/miss. move_to_end is O(1) for the moved element but the dict needs to be large.

Important: the function mutates self.cache (move_to_end). So each call changes state. Since we repeat many times, the state carries over. We need each thunk call to build a fresh instance (or copy) so every call takes the same path. Building a large OrderedDict in the thunk each time might be expensive but setup isn't timed... but it says "keep a thunk cheap next to one call". Building a big OrderedDict of 1M entries each call could be slow relative to the measured call. Better: build the OrderedDict once at module level, and have the thunk return a copy? Copying an OrderedDict of 1M entries is also expensive (O(n)). Hmm.

Alternative: the function under test is fast (microseconds). To make it ~1ms-200ms, we'd need a huge dict... Actually move_to_end is O(1). A single get on a dict of 1M entries is maybe ~100ns. To reach 1ms we'd need ~10000 calls. But the task says one call of the function under test. So we cannot loop inside. So the maximum work per call is one lookup + one move_to_end. That's inherently fast.

Hmm. But the instructions say "One call should take roughly 1 ms to 200 ms on the original." That's impossible for this function unless... well, maybe the comparison is between original and modified, and the measurement is energy over many repetitions. The measured call is one call per repetition, repeated many times. So a single call being fast is fine; the harness repeats it many times. The "roughly 1ms to 200ms" is a guideline; for such a trivial function it's impossible. We should just make the dict as large as reasonable to maximize work per call, and vary hits/misses.

Actually, maybe we can make the key comparison expensive: keys could be large objects with expensive __hash__ or __eq__. But that's artificial. The repository likely uses string keys (image ids?). We don't know exactly. The class is a generic LRU cache. Let's use string keys.

To make each call do more work, we could use a large OrderedDict (e.g., 1,000,000 entries). move_to_end on a large OrderedDict is still O(1) — it just relinks. So the work is dominated by hashing the key and dict lookup. Hashing a long string could be costly. We could use long string keys (e.g., 10KB each) so hashing takes time. But hashing is cached in the string object after first computation, so repeated calls with the same string would be fast after the first. Unless the key is a fresh string each time. But we need the same key to be in the dict... we can store the key objects in the dict and pass the same object. Hash is cached on the object. So no.

Hmm, but the key could be a tuple or custom object without hash caching. But we should stay realistic.

Realistically, this function is just fast. The task is a benchmark; maybe the modified version is slower/faster. We just need 8 diverse cases. Let's focus on diversity: different sizes, hit/miss ratios, key types (strings, ints, tuples), and different positions (front, middle, back of LRU order).

Since move_to_end mutates, if we pass the same instance across repetitions, the order changes but the function still works. The concern is "every call takes the same path". For a hit, the path is: move_to_end + return. For a miss, return None. The order of the dict changes on hits. But the path is the same (hit vs miss). However, the state after many calls could differ in a way that affects timing? Not really. But to be safe, we could rebuild the instance each thunk call. Building a fresh OrderedDict of N entries per call is O(N) setup, not timed, but the thunk runs before timing... The instructions say thunks run before timing starts; only the call is timed. But if the thunk is expensive, it doesn't affect the measured time, but it does affect total runtime. The harness probably runs many iterations; a heavy thunk would slow things down. The guidance: "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy if the function changes it". Here the function changes the OrderedDict order. So we should return a copy. Copying an OrderedDict of 1M entries is ~50ms. That's not cheap. Maybe use smaller dicts, like 10,000 entries. Copy is ~0.5ms. The call itself is ~1µs. That's a 500x overhead. Hmm.

Alternatively, we can make the thunk return the same instance but with a key that is always a miss (so no mutation) — but misses don't exercise move_to_end. For hits, we could use a fresh instance built once and... no, mutation accumulates.

Wait: move_to_end changes order but doesn't change membership. If we always call get on the same key, after the first call it's at the end; subsequent calls move it to end again (no-op effectively). The path is the same. The timing might be identical. So we could just reuse the same instance and same key. The state changes only in order, but the operation is the same. The concern about "same work on every call" is more about caches that grow, or functions that record seen keys. Here, the only state change is ordering. If we always query the same key, the work is constant. If we query different keys each time, the position varies, but move_to_end is O(1) regardless of position. So it's fine.

But the harness compares outputs. The output is the value returned. If we reuse the instance and query a hit key, output is the value. Constant. Good.

However, there's a subtlety: the harness may check that arguments are unchanged. The instance is passed as first argument (self). The function mutates self.cache. So the argument changes. The instructions say "Its arguments are rendered before and after each call to see whether it changed them". If it changes, that's fine? It says "keep each input's data under about 1,000,000 values". It doesn't forbid mutation, just says to use a copy if the function changes it. Actually: "or a copy (list(data), dict(data)) if the function changes it (adds to a dict, sorts or fills a list in place)". So we should give a copy so the original data isn't changed, presumably so the next call gets the same starting state. If we reuse the same instance, the state evolves, but as argued, the work is the same. But to be safe and to have deterministic outputs, we could build a fresh instance per thunk call. But building a large OrderedDict is expensive.

Compromise: use moderate sizes (e.g., 10,000 - 200,000 entries) and build a fresh instance in each thunk by copying a pre-built template. Copying 200k entries is ~10ms. The call is ~1µs. That's 10,000x overhead. The harness might run 1000 iterations -> 10 seconds just for setup. That's probably acceptable? The task says building all inputs under 10s. That's for building all inputs once, not per iteration. Hmm, "Generate stressful inputs... building all inputs under about 10 s." That's the initial construction. The thunks run many times. If thunk is 10ms and call is 1µs, the measurement is dominated by setup, but timing only measures the call. However, the harness may have a time budget. Let's keep thunks reasonably cheap.

Alternative approach: make the function itself do more work by having the key be a custom object with expensive __hash__ and __eq__. But that's not realistic and might be considered "mocking" or artificial. The instructions say "Generate stressful inputs: complex, time-consuming, as diverse as possible." For a cache get, the stress is the size of the cache and the hashability of keys. In the repository, keys are likely strings (e.g., image IDs, query strings). Let's use strings of varying lengths.

We can make the key a long string (e.g., 100KB) so hashing takes time. But Python caches the hash on the string object. If we pass the same string object each call, hash is cached. If we pass a new equal string each call, hash is recomputed. But then the key in the dict is a different object; dict lookup uses hash and eq. If we pass a new string each time, it hashes the new string (costly) and compares to the stored key. That would make each call do real work: hashing a large string. But is that realistic? Maybe keys are long documents? Unlikely for a cache key.

Given the function is trivial, perhaps the benchmark just expects small variations. Let's not overthink. We'll create 8 cases with different sizes and hit/miss patterns.

We need exactly 8 measured inputs. We run them on original, keep 4 that do most work. So we should make some cases heavier than others.

Let's design:

- `_build_cache(n, seed)`: returns an LRUCache with n entries, keys are strings like f"key{i}", values are random ints or strings.
- Cases:
  1. Small cache, hit on most recently used (front? actually move_to_end moves to end; LRU usually front is least recently used, end is most recently used). Hit on a key that's already at the end (move_to_end no-op).
  2. Medium cache, hit on a key at the front (move_to_end moves it to end).
  3. Large cache, hit on a key in the middle.
  4. Miss on a large cache.
  5. Miss on a small cache.
  6. Hit with integer keys.
  7. Hit with tuple keys.
  8. Hit with long string keys.

But note: the function only does `if key in self.cache` then `move_to_end` then `return self.cache[key]`. Actually it does two lookups: `key in self.cache` and `self.cache[key]`. So it's two hash lookups plus move_to_end. For a miss, one lookup.

To maximize work, use a large cache and a hit. The work is dominated by hashing the key (if not cached) and the two dict lookups. Dict lookup is O(1) but with large dicts there may be more collisions. We can't control that easily.

Let's just make caches of sizes: 10, 1000, 100_000, 1_000_000. The 1M case might take ~50MB? Each entry: key string ~10 bytes + overhead ~50 bytes, value int ~28 bytes, dict entry ~100 bytes. 1M entries ~150MB. Too much. Keep under 100MB. So max maybe 300k entries. Let's use up to 200k.

Actually, we can use a single large cache and different keys for hits/misses. But each case needs its own instance? We can share a module-level template and copy it. Copying 200k entries is ~10ms. The thunk would do that copy. Then the call is fast. The harness runs the thunk before each call. If it runs 1000 times, that's 10 seconds. Might be okay.

Alternatively, we can avoid copying by making the function not mutate the cache in a way that affects subsequent calls. If we always query the same key, the state after the first call is stable (key at end). So we can reuse the same instance. The output is the same. The argument changes (order), but the harness might tolerate that. The instruction says "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over...". Here the cache is inside the argument (self). It says "if the function changes it (adds to a dict, sorts or fills a list in place)" use a copy. So they want us to avoid mutation affecting the next call. But if we query the same key, the mutation is idempotent after the first call. So it's effectively the same. I think it's fine.

But to be safe and correct, let's build a fresh instance per thunk call. To keep it cheap, use moderate sizes. For the "large" cases, maybe 50k entries. Copying 50k is ~2ms. That's acceptable.

Wait, we could also make the thunk return a new LRUCache that shares the same cache? No, then mutation affects the shared dict.

Actually, we can use `copy.deepcopy`? No, OrderedDict copy is shallow but creates a new OrderedDict. `OrderedDict(template.cache)` is a shallow copy. That's O(n). For 50k, it's fast.

Let's design the cases with varying sizes and key types. We'll use `random.Random(0)` for value generation.

Keys: strings `f"k{i}"`, integers `i`, tuples `(i, i%10)`, long strings `f"k{i}" * 100` (but that's huge; hashing long strings is costly). Actually, if we use long strings, hashing takes time. But Python caches hash on the string object. If we store the key object in the dict and pass the same object, hash is cached. If we pass a different but equal string, hash is recomputed. To force recomputation, we could create a new string each thunk call. But then the dict lookup will hash the new string. That's realistic if keys are constructed on the fly (e.g., query + filters). Let's do that for one case: long string keys, and the thunk creates a new string equal to the stored key. That makes each call hash a long string, doing real work.

But careful: the thunk returns the arguments. If the thunk creates a new string each time, the key is different object but equal. The function will find it in the cache. The output is the value. Good.

Let's plan 8 cases:

1. "tiny-hit" - cache size 10, hit on existing key. Very fast.
2. "small-miss" - cache size 10, miss.
3. "medium-hit-front" - cache size 10_000, hit on the first key (least recently used). move_to_end moves it to end.
4. "medium-hit-back" - cache size 10_000, hit on the last key. move_to_end no-op.
5. "large-hit-middle" - cache size 100_000, hit on a middle key.
6. "large-miss" - cache size 100_000, miss.
7. "int-keys-hit" - cache size 50_000, integer keys, hit.
8. "long-string-keys-hit" - cache size 20_000, keys are long strings (e.g., 10_000 chars). Hit with a freshly constructed equal string (so hashing is recomputed).

For case 8, building 20k long strings of 10k chars each = 200MB. Too much. Let's use 1000 chars * 5000 keys = 5MB. That's fine. Hashing a 1000-char string takes ~1µs? Actually Python's string hash is fast, maybe 100ns per 1000 chars. So 1µs. Not huge. But with 5000 keys, the dict is small. The work is hashing. Let's use 100_000-char strings? Then building 1000 keys = 100MB. Too much. Let's use 10_000-char strings, 2000 keys = 20MB. Hashing 10k chars ~1µs. That's okay.

Actually, to make the call take ~1ms, we'd need hashing a 10MB string. That's 10MB per key, impossible for many keys. So we can't reach 1ms. That's fine; the guideline is a guideline.

Maybe we can make the key a custom object with a slow __hash__? But that's not realistic.

Let's just make the cache as large as memory allows. 200k entries with short string keys: each entry ~100 bytes, total 20MB. That's fine. 200k entries. Copying 200k OrderedDict is ~10ms. The call is ~1µs. The thunk overhead is 10,000x. If the harness runs 100 iterations, that's 1 second setup. Acceptable.

But wait: the harness times only the call. So the measured time is ~1µs. The energy measurement might be dominated by the call. The setup energy is not counted. So it's fine if setup is heavy. The only risk is the harness timing out. Let's keep setup reasonable: max 100k entries.

Let's decide sizes:
- tiny: 10
- small: 100
- medium: 10_000
- large: 100_000

For each case, we need a fresh instance per thunk call to avoid mutation affecting the next call. We'll build a template at module level, and the thunk does `LRUCache(max_size=...)` and then `inst.cache = OrderedDict(template.cache)`? But we need to import OrderedDict. The module already imports it. We can use `from collections import OrderedDict`. Or we can just build the cache from scratch in the thunk? Building 100k entries from scratch each call is O(n) and involves creating strings, which is slower than copying. Copying is faster.

Actually, we can create the LRUCache instance once and then in the thunk do `copy.copy(inst)`? No, copy.copy on an object with an OrderedDict attribute copies the reference, so mutation affects the original. We need a deep copy of the cache. `OrderedDict(inst.cache)` is a shallow copy of the dict, which is what we want. The keys and values are shared, which is fine since they're immutable.

So module-level: build a template LRUCache with n entries. Then thunk: `inst = LRUCache(); inst.cache = OrderedDict(template.cache); inst.max_size = template.max_size; return (inst, key)`.

But we need the key to be a specific object. For hits, the key must be present in the copy. Since the copy shares the same key objects, passing the same key object works. For misses, any key not in the dict.

However, for case 8 (long strings), we want a freshly constructed equal string. So the thunk will do `key = "x" * 10000` (or something) and the template has that key. But if we construct a new string each time, it's equal but not identical. The dict lookup will hash it. Good.

Let's write the code.

First, import:
```python
import random
from collections import OrderedDict
from backend.cache import LRUCache
```

We need to be careful: the repository path might not be on sys.path. The task says "Import the repository's modules exactly as shown in the task." It shows `from backend.cache import LRUCache`. So we just do that. The harness presumably sets up sys.path.

Now, module-level setup:

```python
def _make_cache(n, key_func, value_func):
    cache = LRUCache(max_size=n)
    for i in range(n):
        cache.cache[key_func(i)] = value_func(i)
    return cache
```

But we need different key types. Let's define builders.

For strings: `key_func = lambda i: f"key{i}"`
For ints: `key_func = lambda i: i`
For tuples: `key_func = lambda i: (i, i % 10)`
For long strings: `key_func = lambda i: f"longkey{i}_" + "x" * 10000` — but that's 10000 chars per key, 1000 keys = 10MB. Fine.

We'll create templates at module level:

```python
_rng = random.Random(0)

def _build_str_cache(n):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[f"key{i}"] = _rng.randint(0, 10**9)
    return c

def _build_int_cache(n):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[i] = _rng.randint(0, 10**9)
    return c

def _build_tuple_cache(n):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[(i, i % 10)] = _rng.randint(0, 10**9)
    return c

def _build_long_cache(n, length=10000):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[f"longkey{i}_" + "x" * length] = _rng.randint(0, 10**9)
    return c
```

Wait, values are random ints. The function returns the value. The output is compared. Since we use the same template, the values are fixed. Good.

Now cases. We need exactly 8. Each case is a (label, thunk). The thunk returns a tuple of args for `LRUCache.get(instance, key)`. So `lambda: (inst, key)`.

We need to build a fresh instance per thunk call. We'll define a helper:

```python
def _copy_cache(template):
    inst = LRUCache(max_size=template.max_size)
    inst.cache = OrderedDict(template.cache)
    return inst
```

Then in each thunk:
```python
lambda: (_copy_cache(_TEMPLATE_MEDIUM), "key5000")
```

But for long strings, we want a fresh key string:
```python
lambda: (_copy_cache(_TEMPLATE_LONG), "longkey500_" + "x" * 10000)
```

Wait, the template stores the key as `f"longkey{i}_" + "x" * length`. So the key is a specific string. We can reconstruct it exactly. Let's make sure the reconstruction matches. We'll define a function `_long_key(i, length=10000)`.

Now, sizes:
- tiny: 10
- small: 100
- medium: 10_000
- large: 100_000
- long: 1_000 (with 10k chars each = 10MB)

Let's list 8 cases:

1. "tiny-hit": template tiny, key "key5" (present)
2. "tiny-miss": template tiny, key "missing"
3. "medium-hit-front": template medium (10k), key "key0" (first inserted, so at front? OrderedDict order is insertion order. move_to_end moves to end. So "key0" is at the beginning. Hit on it moves it to end.)
4. "medium-hit-back": template medium, key "key9999" (last inserted, at end). move_to_end no-op.
5. "large-hit-middle": template large (100k), key "key50000"
6. "large-miss": template large, key "notfound"
7. "int-keys-hit": template int (50k), key 25000
8. "long-string-keys-hit": template long (1000), key reconstructed long string for index 500.

We need to ensure each case runs without raising. For misses, the key is not in the cache, returns None. That's fine.

Now, checks(): 2-3 small edge inputs. These are not measured. They may raise. We can include:
- empty cache, get a key -> returns None.
- cache with one entry, get that entry.
- get with None key? The function does `if key in self.cache`. If key is None, it checks if None is in the dict. That's fine. But if the dict contains None? Not typical. We can do a check with None key on a cache that has None as a key? Actually, `None in OrderedDict` works. Let's just do:
  - ("empty", lambda: (LRUCache(), "anything"))
  - ("single-hit", lambda: (LRUCache with one entry, that entry))
  - ("none-key", lambda: (LRUCache with None key, None))

But building an LRUCache with an entry in the thunk is fine. For checks, we don't need to copy since they run once.

Wait, the checks are run on both original and modified to compare behavior. They may raise. So we can include an odd type like a list as key? But lists are unhashable, so `key in self.cache` would raise TypeError. That's a valid edge case. Let's include one that raises: `lambda: (LRUCache(), [1,2,3])`. That will raise TypeError: unhashable type. That's fine for checks.

But the instructions: "checks(): 2 or 3 small edge inputs (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise." So we can have 3.

Let's define checks:

```python
def checks():
    return [
        ("empty-cache", lambda: (LRUCache(), "missing")),
        ("single-entry", lambda: (_make_single(), "only")),
        ("unhashable-key", lambda: (LRUCache(), [1, 2, 3])),
    ]
```

Where `_make_single` returns an LRUCache with one entry.

Now, we need to make sure the thunks are cheap. `_copy_cache` creates a new LRUCache and copies the OrderedDict. For 100k entries, copying is ~5-10ms. That's acceptable. But the harness might run many iterations. Let's think: if the harness runs 1000 iterations per case, 8 cases = 8000 thunk calls. For the large case, 100k copy * 1000 = 100 million dict entries copied. That could take 10 seconds. Might be okay. But we can reduce the large size to 50k. The task says "roughly 1 ms to 200 ms". Our call is microseconds. The measurement is energy over many repetitions. The thunk overhead is not measured. So we want the call to be as heavy as possible. But the call is inherently light. To make the call heavier, we need a bigger dict or more expensive hashing. But the call is O(1) regardless of dict size. The only thing that increases with dict size is cache misses (collisions). So a 100k dict might have slightly more collisions than a 10k dict, but not much. The main cost is hashing the key. For short strings, hashing is fast. For long strings, hashing is slow. So case 8 (long strings) will be the heaviest call. Let's make the long strings longer, e.g., 100k chars, and fewer keys (e.g., 100 keys) to keep memory under 100MB. 100 keys * 100k chars = 10MB. Hashing 100k chars takes ~10µs? Actually, Python's string hash is very fast, maybe 1ns per byte? Let's check: hashing a 1MB string takes about 0.5ms? Actually, Python's string hash uses SipHash, which is quite fast. For 100k chars, maybe 10µs. That's still far from 1ms. To reach 1ms, we'd need 10MB string. 10MB * 10 keys = 100MB. That's at the limit. Hashing a 10MB string might take ~1ms. Let's do that: 10 keys, each 10MB long? That's 100MB just for keys. Plus overhead. Might exceed 100MB. The limit is "under about 100 MB". So we could do 5 keys of 10MB = 50MB. Hashing 10MB might take ~1ms. That would make the call substantial. But building 5 keys of 10MB each is 50MB, and copying the dict is cheap (5 entries). The thunk would need to reconstruct the 10MB key each time? That would be expensive (allocating 10MB per thunk call). That's too heavy for the thunk. We could store the key in the template and pass the same object. But then hash is cached. To force rehash, we need a new object. Allocating 10MB per thunk call is 10MB * iterations, too much.

Alternative: use a custom key class with a slow __hash__ and __eq__. But that's artificial and might be considered mocking? It's not mocking, it's just a custom object. The function works with any hashable key. The repository likely uses strings, but a custom object is a valid input. However, the instructions say "Generate stressful inputs: complex, time-consuming, as diverse as possible." A custom key with a slow hash is a legitimate way to stress the cache. But it might be seen as unrealistic. Let's stick to strings.

Given the constraints, we'll just make the long string case with 1000-char strings and 10k keys? 10k * 1000 = 10MB. Hashing 1000 chars is ~1µs. Not heavy. But it's the heaviest among our cases.

Actually, we can make the key hashing expensive by using a string that is not cached? No, Python caches hash per string object. If we pass the same string object, hash is cached. If we pass a new equal string, hash is computed. The thunk can create a new string each time. For 1000-char strings, creating a new string is fast (~1µs). So the call does hashing (~1µs) plus dict lookup. That's still ~2µs. To make it 1ms, we need 1MB strings. Creating a 1MB string per thunk call is 1MB allocation, which is maybe 0.1ms. That's acceptable for thunk overhead. 100 iterations -> 10MB allocations, fine. Let's do 1MB strings, 100 keys = 100MB. That's at the limit. Let's do 500KB strings, 100 keys = 50MB. Hashing 500KB might take ~50µs. Still not 1ms. Hmm.

Maybe we don't need to hit 1ms. The guideline is "roughly 1 ms to 200 ms". For a trivial function, it's impossible. The harness probably tolerates it. The important thing is to have diverse cases.

Let's finalize with reasonable sizes:
- tiny: 10
- small: 100
- medium: 10_000
- large: 100_000
- long: 1_000 keys of 10_000 chars each (10MB)

We'll make the long case use a freshly constructed key string each thunk call, so hashing is recomputed. The string length 10_000. That's 10KB. Hashing 10KB is maybe 1-2µs. Not huge, but it's the heaviest.

Actually, we can make the long case have 100_000-char strings and 100 keys = 10MB. Hashing 100KB is ~10µs. That's better. Let's do 100 keys of 100_000 chars = 10MB. The thunk constructs a new 100KB string each call. That's 100KB allocation per call, which is fine.

Let's set:
- long: n=100, key_length=100_000

Then the call does: hash a 100KB string (~10µs), dict lookup on 100 entries, move_to_end. That's the heaviest.

For other cases, we can use larger dicts to increase collision chance. But dict lookup is O(1) regardless. The main cost is hashing. For short strings, hashing is fast. So the large dict cases will be fast. That's fine.

Now, we need to ensure the thunk copies the cache. For the long case, the cache has 100 entries, so copying is trivial. The thunk also constructs the key string. So the thunk does: copy 100-entry dict, construct 100KB string. That's cheap.

For the large case (100k entries), copying is the expensive part. But that's setup, not measured.

Let's write the code.

We need to define the templates at module level. We'll use `random.Random(0)` for values.

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)

def _build_cache(n, key_func):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[key_func(i)] = _rng.randint(0, 10**9)
    return c

_TINY = _build_cache(10, lambda i: f"key{i}")
_SMALL = _build_cache(100, lambda i: f"key{i}")
_MEDIUM = _build_cache(10_000, lambda i: f"key{i}")
_LARGE = _build_cache(100_000, lambda i: f"key{i}")
_INT = _build_cache(50_000, lambda i: i)
_TUPLE = _build_cache(50_000, lambda i: (i, i % 10))

_LONG_LEN = 100_000
def _long_key(i):
    return f"longkey{i}_" + "x" * _LONG_LEN
_LONG = _build_cache(100, _long_key)

def _copy(template):
    inst = LRUCache(max_size=template.max_size)
    inst.cache = OrderedDict(template.cache)
    return inst

def checks():
    single = LRUCache(max_size=1)
    single.cache["only"] = 42
    return [
        ("empty-cache", lambda: (LRUCache(), "missing")),
        ("single-entry", lambda: (single, "only")),
        ("unhashable-key", lambda: (LRUCache(), [1, 2, 3])),
    ]

def cases():
    return [
        ("tiny-hit", lambda: (_copy(_TINY), "key5")),
        ("tiny-miss", lambda: (_copy(_TINY), "missing")),
        ("medium-hit-front", lambda: (_copy(_MEDIUM), "key0")),
        ("medium-hit-back", lambda: (_copy(_MEDIUM), "key9999")),
        ("large-hit-middle", lambda: (_copy(_LARGE), "key50000")),
        ("large-miss", lambda: (_copy(_LARGE), "notfound")),
        ("int-keys-hit", lambda: (_copy(_INT), 25000)),
        ("long-string-keys-hit", lambda: (_copy(_LONG), _long_key(50))),
    ]
```

Wait, for the long-string case, the thunk calls `_long_key(50)` which constructs a new 100KB string each time. That's good. But the template `_LONG` has a key that is exactly `_long_key(50)`? Yes, because `_build_cache` used `_long_key(i)` for i=50. So the key in the cache is a string equal to `_long_key(50)`. The new string is equal, so `key in self.cache` will find it. Good.

But note: `_long_key(50)` is called in the thunk, which runs before timing. So the string is constructed before the timed call. The timed call then hashes it (since it's a new string, hash not cached). Good.

Now, check the sizes and memory. `_LARGE` has 100k entries. Each entry: key string ~10 chars, value int. OrderedDict overhead. 100k * ~150 bytes = 15MB. Fine. `_INT` 50k ints. `_TUPLE` 50k tuples. `_LONG` 100 entries of 100KB strings = 10MB. Total memory maybe 50MB. Under 100MB.

But wait: `_build_cache` for `_LARGE` uses `f"key{i}"` for i up to 100k. That's fine.

Now, the thunk copies the template. For `_LARGE`, copying 100k entries takes maybe 5-10ms. The harness will run this many times. If it runs 1000 iterations, that's 10 seconds per case. 8 cases -> 80 seconds. Might be too slow. We can reduce the large size to 50k. Or we can avoid copying by reusing the same instance and always querying the same key. Let's reconsider.

The function mutates the cache order. If we always query the same key, the first call moves it to end. Subsequent calls: it's already at end, move_to_end is a no-op (or it moves it to end again, which is O(1) and doesn't change order). The state is stable. The output is the same. The argument (the instance) is mutated only in the first call. But the harness compares arguments before and after each call. The first call changes the order; subsequent calls don't. So the argument rendering would show a change on the first call, but then it's stable. The harness might detect that the argument changed and flag it? The instructions say "Its arguments are rendered before and after each call to see whether it changed them". It doesn't say it's forbidden to change, just that it's checked. If it changes, it's fine as long as the function works. But they recommend using a copy if the function changes it, to ensure every call takes the same path. If we reuse the same instance and always query the same key, every call after the first takes the exact same path (key at end, move_to_end no-op). So it's fine. The only difference is the first call vs subsequent. But the harness likely runs many iterations and discards warmup? Not sure. To be safe, we can do a warmup in the thunk? No, the thunk runs before each call. We could have the thunk call `inst.cache.move_to_end(key)` to normalize the state before returning? That would be extra work in the thunk, not timed. But then the function under test would see the key already at end, so move_to_end is a no-op. That changes the work! The original function's work includes move_to_end. If we pre-move it, the function does less work. That's not fair. We want the function to do the move_to_end. So we should not pre-move.

If we reuse the same instance and query different keys each time, the state evolves unpredictably. So we must copy.

Given the performance concern, let's reduce the large size to 50k. 50k copy is ~2-3ms. 1000 iterations = 3 seconds. Acceptable. Let's use 50k for large, 10k for medium.

Actually, the task says "One call should take roughly 1 ms to 200 ms". Our calls are microseconds. The harness might run many iterations to get a measurable energy difference. The setup time is not measured, but it affects total runtime. If the thunk is 3ms and the call is 1µs, the harness spends 99.9% of time in setup. That's inefficient but probably okay. However, if the harness has a timeout, it might be an issue. Let's keep thunks as cheap as possible. We can build the cache in the thunk from scratch? That's even slower. Copying is faster.

Alternatively, we can use a single global instance and reset it in the thunk by restoring the original order. But restoring order is O(n) anyway.

What if we use a smaller cache but make the key hashing expensive? That makes the call heavier without heavy setup. For example, use a cache of 1000 entries, but keys are 1MB strings. Then the call hashes a 1MB string (expensive), and the setup is just copying 1000 entries (cheap) plus constructing the 1MB key (cheap). That's a great idea! The call does substantial work (hashing 1MB), while the thunk is cheap. Let's do that for the heavy case.

Let's design cases with varying key lengths to vary the hashing cost. This directly stresses the `key in self.cache` and `self.cache[key]` lookups.

So:
- Case 1: tiny cache, short keys, hit.
- Case 2: tiny cache, short keys, miss.
- Case 3: medium cache (10k), short keys, hit front.
- Case 4: medium cache (10k), short keys, hit back.
- Case 5: large cache (50k), short keys, hit middle.
- Case 6: large cache (50k), short keys, miss.
- Case 7: int keys, medium cache (10k), hit.
- Case 8: long string keys (100KB), small cache (100), hit with fresh key.

For case 8, the thunk constructs a 100KB string. That's ~0.1ms. The call hashes it, ~10µs. Not 1ms, but the heaviest.

We can increase to 1MB string, 100 entries = 100MB. That's at the limit. Let's do 500KB, 100 entries = 50MB. Hashing 500KB might take ~50µs. Still not 1ms. To reach 1ms, we need ~10MB string. 10MB * 10 entries = 100MB. That's exactly the limit. Let's do 10 entries of 10MB = 100MB. Hashing a 10MB string: Python's hash is SipHash, which processes 8 bytes per iteration. 10MB / 8 = 1.25M iterations. At ~1ns per iteration, that's 1.25ms. So yes, ~1ms. That would make the call take ~1ms! And the thunk would construct a 10MB string each time. Constructing a 10MB string by `"x" * 10_000_000` is fast (memset), maybe 1ms. So the thunk is ~1ms, the call is ~1ms. That's balanced. But 10 entries of 10MB is 100MB. The limit is "under about 100 MB". So 10MB * 10 = 100MB, plus overhead, might exceed. Let's do 5 entries of 10MB = 50MB. That's safe. The call hashes a 10MB string, ~1ms. The thunk constructs it, ~1ms. That's perfect! The cache has only 5 entries, so copying is trivial.

Let's do that for the long-string case. But wait: the function does `key in self.cache` and then `self.cache[key]`. That's two hash lookups. But Python caches the hash on the string object after the first hash. So the first lookup computes the hash and caches it. The second lookup uses the cached hash. So the hashing cost is paid once per call. That's fine.

So case 8: cache size 5, keys are 10MB strings. The thunk constructs a new 10MB string equal to one of the keys. The call hashes it (~1ms) and finds it. That's a heavy call.

Let's adjust the long case:
- `_LONG_LEN = 10_000_000` (10MB)
- `_LONG_N = 5`
- `_LONG = _build_cache(_LONG_N, _long_key)`

But `_build_cache` uses `_rng.randint` for values. That's fine. Building 5 keys of 10MB each takes 50MB. The thunk does `_long_key(2)` which constructs a new 10MB string. That's 10MB allocation per thunk call. If the harness runs 100 iterations, that's 1GB of allocations, but garbage collected. Might be okay. But 10MB allocation per call is ~1ms. The call is ~1ms. So total ~2ms per iteration. 1000 iterations = 2 seconds. Acceptable.

However, we must ensure the key is exactly equal. `_long_key(i)` returns `f"longkey{i}_" + "x" * _LONG_LEN`. The template stores that. The thunk calls `_long_key(2)`. They are equal. Good.

Now, for the other cases, we can keep them moderate. Let's set:
- tiny: 10
- small: 100
- medium: 10_000
- large: 50_000

Copying 50k is ~2ms. The call is ~1µs. The thunk overhead is 2000x. That's a bit high but okay. We can reduce large to 20k. Let's use 20k for large, 5k for medium. That reduces setup time. The call is O(1) anyway, so dict size doesn't affect call time much (only collision probability). So we don't need huge dicts for the call to be heavy. The heavy call is the long string one. So we can make the other cases small. But the task says "Generate stressful inputs: complex, time-consuming, as diverse as possible." We should have some large dicts to test the cache's behavior with many entries. But since the function is O(1), the dict size doesn't matter for the call. The only thing that matters is the hash and the move_to_end. move_to_end is O(1) regardless of dict size. So large dicts don't stress the function more than small dicts, except for cache effects (CPU cache misses). A 50k dict might have more cache misses than a 10-entry dict. That could make the call slightly slower. So there is some effect. Let's keep a large dict case (50k) to stress memory access patterns.

Let's finalize sizes:
- tiny: 10
- small: 100
- medium: 5_000
- large: 50_000
- int: 10_000
- long: 5 entries of 10MB

Now, for the long case, the thunk constructs a 10MB string. That's a lot of work in the thunk. But it's not timed. The harness might run the thunk many times. 10MB allocation per call could be slow. Let's reduce to 1MB strings and 50 entries? 1MB * 50 = 50MB. Hashing 1MB is ~0.1ms. That's still substantial. The thunk constructs a 1MB string, ~0.1ms. That's more balanced. Let's do 1MB strings, 50 entries. That's 50MB. The call hashes 1MB, ~0.1ms. The thunk constructs 1MB, ~0.1ms. Good.

Actually, we want the call to be as heavy as possible. 10MB is better. But memory limit. Let's do 5 entries of 10MB = 50MB. The thunk constructs 10MB string. That's 10MB allocation per call. If the harness runs 1000 iterations, 10GB of allocations. That might be slow but probably okay. Let's compromise: 2MB strings, 20 entries = 40MB. Hashing 2MB ~0.2ms. Thunk constructs 2MB ~0.2ms. That's reasonable.

Let's set `_LONG_LEN = 2_000_000` (2MB), `_LONG_N = 20`. Total 40MB.

Now, let's write the final code.

We need to import `OrderedDict` for the copy. The module already imports it. We can import it in our code.

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)

def _build_cache(n, key_func):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[key_func(i)] = _rng.randint(0, 10**9)
    return c

_TINY = _build_cache(10, lambda i: f"key{i}")
_SMALL = _build_cache(100, lambda i: f"key{i}")
_MEDIUM = _build_cache(5_000, lambda i: f"key{i}")
_LARGE = _build_cache(50_000, lambda i: f"key{i}")
_INT = _build_cache(10_000, lambda i: i)
_TUPLE = _build_cache(10_000, lambda i: (i, i % 10))

_LONG_LEN = 2_000_000
_LONG_N = 20
def _long_key(i):
    return f"longkey{i}_" + "x" * _LONG_LEN
_LONG = _build_cache(_LONG_N, _long_key)

def _copy(template):
    inst = LRUCache(max_size=template.max_size)
    inst.cache = OrderedDict(template.cache)
    return inst

def checks():
    single = LRUCache(max_size=1)
    single.cache["only"] = 42
    return [
        ("empty-cache", lambda: (LRUCache(), "missing")),
        ("single-entry", lambda: (single, "only")),
        ("unhashable-key", lambda: (LRUCache(), [1, 2, 3])),
    ]

def cases():
    return [
        ("tiny-hit", lambda: (_copy(_TINY), "key5")),
        ("tiny-miss", lambda: (_copy(_TINY), "missing")),
        ("medium-hit-front", lambda: (_copy(_MEDIUM), "key0")),
        ("medium-hit-back", lambda: (_copy(_MEDIUM), "key4999")),
        ("large-hit-middle", lambda: (_copy(_LARGE), "key25000")),
        ("large-miss", lambda: (_copy(_LARGE), "notfound")),
        ("int-keys-hit", lambda: (_copy(_INT), 5000)),
        ("long-string-keys-hit", lambda: (_copy(_LONG), _long_key(10))),
    ]
```

Wait, for `_MEDIUM`, n=5000, keys are "key0" to "key4999". So "key4999" is the last. Good.

For `_INT`, n=10000, key 5000 is present.

For `_LONG`, n=20, keys are `_long_key(0)` to `_long_key(19)`. `_long_key(10)` is present.

Now, check `checks()`: `single` is built at module level? No, inside `checks()`. That's fine. The thunk returns `(single, "only")`. The function will do `if "only" in single.cache: move_to_end("only"); return single.cache["only"]`. It will mutate `single` by moving "only" to end. But since it's already the only entry, it's a no-op. So no issue. The unhashable key case will raise TypeError. That's expected.

One more thing: the function under test is called as `LRUCache.get(instance, key)`. Our thunks return `(instance, key)`. So the harness will call `LRUCache.get(*args)`. That matches.

Now, verify that the thunks are cheap. `_copy(_LARGE)` copies 50k entries. That's maybe 2-3ms. The call is ~1µs. So the thunk is 2000x the call. The harness might run many iterations. If it runs 1000 iterations, that's 2-3 seconds for that case. 8 cases, maybe 5 seconds total. Acceptable.

But we can optimize `_copy` by using `OrderedDict(template.cache)` which is a C-level copy, very fast. For 50k entries, it's probably <1ms. Let's keep it.

Now, the long case: `_copy(_LONG)` copies 20 entries (fast). `_long_key(10)` constructs a 2MB string. That's ~0.2ms. The call hashes it, ~0.2ms. So thunk and call are comparable. Good.

We should also consider that the harness might run the thunk once and then call the function many times? No, the instructions say: "We run the original function and a modified version of it on your inputs, each input many times in a row". And "The thunk returns the arguments; it never calls the function under test. We call the function with them, and time only that call." It sounds like for each iteration, the thunk is called to get the arguments, then the function is called. So the thunk runs every time. That's why they say "keep a thunk cheap next to one call".

Our thunks are reasonably cheap for the small cases, but the large case has a 50k copy. That's the most expensive. We could reduce the large case to 20k to make it cheaper. Let's do 20k for large, 5k for medium. That reduces copy time to ~0.5ms. The call is still O(1). The cache effects are less, but still some. Let's use 20k.

Actually, the task says "Use realistic scale and complexity". The repository is a visual retrieval app. The cache might store image embeddings or search results. The max_size default is 20. So the cache is typically small! The default max_size is 20. So in the repository, the cache is small. The function is called with a cache of size at most 20. So large caches are not realistic. The task says "the kind of data this function gets in this repository (see where the repository calls it)". The repository calls it... we don't have the call sites. But the class default is max_size=20. So realistic caches are small. But the instructions say "Generate stressful inputs: complex, time-consuming, as diverse as possible." So we can go beyond the default to stress it. But maybe we should stay somewhat realistic. A cache of 50k is not realistic for this app. But the benchmark wants to stress the function. I think it's fine to have large caches to stress the dict lookup.

However, the instructions also say "Avoid uniformity or patterns... unless that pattern is what the repository really passes." The repository likely passes small caches. But we can still test large ones for stress. I'll keep a mix: some small (realistic), some large (stress).

Let's finalize with:
- tiny: 10
- small: 100
- medium: 10_000
- large: 50_000
- int: 10_000
- long: 20 entries of 2MB

I'll keep medium 10k and large 50k. The copy time for 50k is maybe 2ms. That's acceptable.

Let's write the final code.

One more check: the function `get` does `if key in self.cache: self.cache.move_to_end(key); return self.cache[key]`. For a miss, it returns None. Our miss cases return None. The output comparison will check that. Good.

Now, ensure no module-level code is timed. The templates are built at import time. That's fine.

Let's produce the final answer.