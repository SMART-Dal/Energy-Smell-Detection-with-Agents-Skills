The problem: the function is very cheap, so each call takes almost no time, meaning the harness runs millions of calls. The issue is that building fresh arguments per call (the `_copy` of a large cache) is expensive relative to the call itself.

Key insight: The function `get` does `move_to_end` which mutates the cache. So we can't reuse the same cache across calls without changing state... but actually, does it matter? The harness compares outputs. `move_to_end` on a hit moves the key to the end. If we call repeatedly with the same key on the same instance, the first call moves it to end, subsequent calls it's already at end — output is the same value. So actually the state changes only once.

But the rule says "Same work on every call". Hmm. Actually the concern is that the timing should be consistent. For a hit at the end, move_to_end is cheap. For a hit at the front, the first call moves it to end, then it's cheap after.

But more importantly, the harness's problem is the argument building cost per call. The `_copy` builds a new OrderedDict each call — that's O(n), expensive.

We need arguments that are cheap to build but make one call do substantial work.

Wait — the function is just dict lookup + move_to_end. It's inherently O(1) (move_to_end on OrderedDict is O(1)). So one call can never do much work. The only way to make a call do more work is... the `key in self.cache` and `self.cache[key]` are O(1) hash operations. Hashing a long string is O(len). So long keys make the call do more work — that's why long-string-keys-hit passed.

So we need long keys to make each call expensive. But building long keys is expensive too. Hmm, but the long-string case passed because the key building was precomputed (module level) and the thunk just returns the instance copy... wait no, `_copy(_LONG)` builds an OrderedDict of 20 entries with 2MB keys each = 40MB copy per call. But it passed with 241k... no wait it says long-string-keys-hit: ok.

Hmm, actually let me reconsider. The copy is the issue. Let me think about what's cheap.

The real issue: the harness runs enough calls to fill a time window, and each call gets fresh arguments (the thunk is called each time). The cost of building arguments per call must be comparable/bounded.

So the thunk must be cheap. Instead of copying the whole cache, we could... use a small cache but with expensive keys.

Actually wait — for the copy, the cost is O(n) per call. For long strings, copy is O(n * len). But the long case passed? That's odd. Let me re-read.

"long-string-keys-hit: ok" — maybe because the call itself (hashing a 2MB string) is expensive enough that few calls happen, so total argument building is bounded. Hashing 2MB string ~ maybe 1ms. So ~thousands of calls in a window.

So the strategy: make the key expensive to hash (long string), so each call does real work. But building the key must be cheap — we can reuse the same long string object across calls (it's immutable, no need to copy).

But the cache copy is the problem. We need to avoid copying the cache. Can we reuse the same cache instance across calls? The function mutates via move_to_end. If the key is already at the end, move_to_end is a no-op-ish but still O(1). Actually move_to_end always does work but O(1).

The rule about "same work every call": if we use a cache where the target key is at the end, then every call does the same work (dict lookup + move_to_end on already-last element). That's fine and consistent.

But wait, does the harness compare outputs? `get` returns the value. Same value each time. The cache state: after first call key is at end. If it started at end, state unchanged. So consistent.

But is reusing the same instance "cheating"? The rule says if the function changes its arguments, use a copy. Here the argument is the instance (self). The function changes self.cache order. If we ensure the key is already at the end, no change. Hmm, but that's fragile.

Alternative: make the cache small so copying is cheap, but key long so call is expensive.

Let's think: copy of cache with n entries. If n is small (say 3), copy is cheap. Key long (say 1MB). Then call hashes 1MB string. Building the cache copy: 3 entries, one with 1MB key — but copying an OrderedDict copies references to keys, not the strings themselves! Strings are immutable and shared. So copying a dict of 3 entries where keys are large strings is O(3) pointer copies. Cheap!

Wait, that changes everything. `OrderedDict(template.cache)` copies references. So copying is O(n) in number of entries, not in key size. So for medium cache of 10,000 entries, copy is 10,000 pointer copies — that's not huge but per call it's significant.

So the fix: keep the number of entries small, but make the key hashing expensive.

But then the "work" of the call is dominated by hashing the key. Good.

Let me design:
- Cache with a few entries (e.g., 3-10), one key being a very long string (e.g., 1-5 MB).
- Thunk returns (copy_of_cache, long_key). Copy is cheap (few entries).
- Call hashes long key: O(len).

Actually, even simpler: we don't even need to copy if the key is at the end. But copying a small dict is cheap anyway.

Hmm, but there's a subtlety: the harness measures "each of the N calls gets fresh arguments". The thunk is called each time. If the thunk does a copy of a small dict, that's cheap. Good.

But wait, the reported issue for medium-hit: "building them would take 559.3 GB". That's because the copy of 10,000 entries times 749,558 calls. So yes, number of entries matters.

So: use small caches with long keys.

But how much work does one call do? Hashing a 5MB string: Python's string hash is cached! Once a string's hash is computed, it's stored in the string object. So if we reuse the same string object, the hash is computed once and cached. Then subsequent lookups are O(1)!

Hmm. That's a problem. So reusing the same long string means the hash is cached after the first call.

To force re-hashing, we need a new string object each call. But building a new 5MB string each call is expensive (memcpy).

Alternatively use a key type whose hash isn't cached... but keys are strings typically.

Hmm. Actually, wait. Let's reconsider. The `long-string-keys-hit` case passed. Why? Because the thunk does `_copy(_LONG)` which copies 20 entries, and the key is `_long_key(10)` — a fresh 2MB string built each call! Building a 2MB string each call is expensive (~memcpy 2MB). So the argument building dominates and the harness saw the call as... hmm, but it passed.

Actually the harness's concern is total argument-building time/space vs the time window. If building args is expensive, fewer calls fit, so total is bounded. The "long-string" passed because... maybe building a 2MB string is slow enough that the number of calls is small, keeping total memory bounded.

Wait but `_long_key(10)` builds a fresh 2MB string every call. That's ~2MB allocation per call. Over many calls that's a lot of allocation. But the harness said ok. Maybe because the call (hashing 2MB) is also slow, so few calls.

Hmm, let me reconsider the metric. "each of the 1,964,761 calls in a window gets fresh arguments, and building them would take about 12.2s". So they compute: number of calls in a time window × cost of building args. For tiny-hit, the call is fast so many calls happen, and building args (copy of 10-entry dict) × 1.96M = 12.2s. So the copy of 10 entries is ~6µs.

For medium: copy of 10,000 entries × 749,558 = huge.

So the fix is to reduce the number of entries AND/OR increase the per-call work so fewer calls happen.

The cleanest: make the key expensive to hash so the call itself is slow, reducing call count. But hash caching...

Option: use a key that's a long string but built fresh each call. Then hashing is fresh each call (no cache). Building the string each call is the argument cost. Hmm, but that's the same problem.

Actually, let's think about what makes a call slow without expensive argument building:
- `key in self.cache`: hash the key. If hash cached, O(1).
- `self.cache.move_to_end(key)`: O(1).
- `self.cache[key]`: O(1).

So with cached hash, the call is truly O(1) and fast. No way to make it slow without expensive args.

Therefore, to make the call do more work, the key must be a fresh object each call (so hashing happens), OR the hash must not be cached.

Hmm, but wait: does `move_to_end` require a hash? It uses the key to find the node. It calls `self.__map[key]` — hash lookup. So each of `in`, `move_to_end`, `[]` does a hash lookup. If hash cached, each is O(1). Three hash lookups.

So the call is ~3 dict lookups. Very fast.

To slow it down: fresh long string key each call → hash computed each call (O(len)) but also the arg building includes creating the string.

Hmm, creating a long string: `"x" * N` is O(N) memcpy. Hashing is O(N). So both are O(N). The call does O(N) work (hashing), args building does O(N) (string creation). Ratio roughly 1:1 or so. The harness wants arg building to be cheap relative to the call.

Can we make a key whose hashing is expensive but construction is cheap? 

Idea: use a string that already exists but... hash cached.

Idea: use a custom object with a slow `__hash__`? But we can't define arbitrary classes? Actually we can — the rule says no mocking repository classes, but defining our own key class is fine? Hmm, "No mocks". A custom hashable class isn't a mock. But would the repository pass such keys? Realistically keys are strings. But the task says "build real inputs". Hmm.

Actually, let me reconsider. Maybe there's a simpler approach: the harness's limit is about argument building cost. We can make the thunk cheap by reusing the cache and key, but the state changes...

Let me reconsider: what if we DON'T copy the cache, just reuse the same instance? The function mutates it (move_to_end). But if the key is already last, no change. Let's make the cache such that the queried key is at the end. Then every call: key in cache (yes), move_to_end(key) (already last, still does the operation but result same), return value. State unchanged. So we can reuse the same instance! Thunk is just `(instance, key)` — nearly free.

But is that "cheating"? The rule: "Anything the function changes outside its arguments ... carries over". Here the function changes its argument (self). We should provide a copy if it changes. But if the key is at the end, it doesn't change. Still, to be safe and honest, we could copy a small cache.

Hmm, but the harness measures the thunk cost. If the thunk is `(instance, key)` with no copy, cost is ~0. Then many calls happen, but each call is fast, total time window bounded... Actually the concern is arg building cost per call. If it's ~0, fine.

But the harness might complain "one call does too little work". The limit is: "one call should take roughly 1ms to 200ms". If a call takes nanoseconds, the harness runs millions of calls. The reported error is about building args taking too long in total. If thunk is free, no problem? But maybe there's also a minimum work requirement.

Hmm, actually re-reading: the errors all say "one call does too little work for arguments that size; give it arguments that are cheaper to build, or on which one call does more of the work". So they want either cheaper args or more work per call.

The simplest: cheaper args. Reuse instances without copying.

But we need 8 distinct cases. Let's make cases that differ in the cache content/position but keep the thunk cheap.

Wait, but if we reuse the same instance across calls and the function moves the key to end, then the position changes after first call. To keep "same work every call", we want the key already at end. But for a "hit at front" case, the first call moves it to end, then it's cheap. The output (value) stays the same, so the harness's output comparison is fine. But the timing would differ between first call and rest — the harness times many calls and averages, so first call is negligible.

Actually, is it a problem that the function changes state? The rule says provide a copy if it changes the argument. But this rule is about "same work on every call" — if state carries over, later calls do different work. For a hit-at-front moving to end, subsequent calls are hit-at-end. Different work. That violates "same work on every call".

Hmm. But practically, the difference is tiny. And the harness only cares about timing consistency and output equality.

Let me think about what's the most robust: make the thunk cheap AND keep work constant.

Approach: use a fresh copy but of a SMALL cache (few entries), with the key being a long string whose hash is NOT cached. But hash caching is the issue.

Alternative: use a small cache and a key that's a fresh long string each call. Then:
- arg cost: create long string O(N) + copy small dict O(k).
- call cost: hash long string O(N) (3 times? no, hash computed once per string object, cached after first hash within the call).

Actually within one call, the string is hashed once (first `in`), then cached, then `move_to_end` and `[]` use cached hash. So call cost ~ O(N) for one hash + 3 lookups.

Arg cost ~ O(N) for string creation.
Ratio ~1:1. The harness wants arg building to not dominate. Hmm.

Actually wait, let me reconsider the reported numbers. For long-string-keys-hit it passed. There the thunk built a fresh 2MB string each call AND copied a 20-entry dict. And it passed. So maybe the threshold is lenient.

Actually the reason it passed: the call hashes a 2MB string, which takes maybe ~1ms? No, hashing 2MB is fast, ~0.2ms maybe. Hmm. Actually Python's string hash for 2MB... siphash processes ~1 byte/cycle? Actually ~1-2 GB/s. 2MB → ~1-2ms. So call ~1-2ms. That's in the desired range! So few calls happen (say 1000 in a 2s window), and arg building 1000 × 2MB = 2GB... hmm that's near the 4.3GB limit but passed.

OK so the winning formula: make the call take ~1ms by hashing a fresh long string. But fresh string each call costs the same as hashing. Hmm.

Wait, but actually maybe the hash IS cached even for fresh strings? No, fresh string = new object = no cached hash.

Hmm, but actually — if we reuse the SAME long string object, the hash gets cached after the first call. Then all subsequent calls are O(1) fast. Then many calls happen, but the thunk is cheap (no string creation). So total arg building is cheap! That might actually pass!

Let me reconsider: the harness error for tiny-hit was that arg building (copy of 10-entry dict) × 1.96M calls = 12.2s. If instead the thunk is free (reuse instance + reuse key), then arg building ≈ 0, no problem. And the call is fast, so many calls, but that's fine — the harness just runs many fast calls.

But wait, is there a minimum? The harness says "one call should take roughly 1 ms to 200 ms on the original". If a call is 1µs, the harness runs ~1M calls. That's fine as long as arg building is free. But the harness might have a max call count. The errors mention counts like 1.96M, 2.9M. So they allow millions of calls. The issue was only arg building.

Hmm, but actually re-reading the error: "each of the 1,964,761 calls in a window gets fresh arguments, and building them would take about 12.2s (limit 10s)". So the limit is on total arg building time (10s) and total memory (4.3GB). If the thunk is free, both are ~0.

So the simplest fix: make thunks nearly free. Reuse instances and keys.

But we must ensure "same work on every call". If we reuse an instance and the key is at the end, work is constant. If key is in the middle, first call moves to end, then constant but different from first.

To be safe, let's make each case's key be at the END of the cache (so move_to_end is a no-op in terms of result). Actually move_to_end still executes but the dict state is unchanged. And the work is constant.

But then all cases are "hit at end" — not diverse. Hmm. We want diverse paths: hit, miss, different sizes.

For a miss, the function returns None without changing state. So a miss case reuses the instance fine, constant work.

For a hit, we want it to be at the end to avoid state change. Or we accept state change.

Hmm, but diversity: we could have hits at different positions, but then state changes. Let's think: does the harness detect state change? It renders args before and after each call. If the cache order changes, the rendered args differ → it might complain the function mutates args and we should copy. Actually the rule says the harness renders args before/after to see if changed. If changed, presumably it's fine as long as we handle it (copy). But if we don't copy, the harness might flag it.

Hmm, actually re-reading rule 6: "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy ... if the function changes it". So the harness expects that if the function changes the arg, we copy. But it doesn't say it errors. The rendering is to detect changes.

I think the safest is: for hit cases, place the key at the end so no change. For miss cases, no change. Then no copy needed, thunk is free.

But wait — if the key is at the end and we call get, move_to_end(key) — does it change the OrderedDict? It removes and re-appends; the resulting order is the same. So `OrderedDict` internal state: the linked list is rebuilt but order identical. The rendered representation is the same. So no detected change. 

But actually, does calling move_to_end on the last element allocate/change anything observable? The repr is the same. Good.

Now, but if we reuse the same instance across all calls for a case, and the key is at end, work is constant. 

But hold on — will the harness's "rendered args before and after" comparison be expensive? It renders the cache (e.g., 10,000 entries) each call. That's part of the harness overhead, not ours. Hmm, but that could be a problem for large caches. Actually the harness renders args to compare. If the cache has 10,000 entries, rendering is expensive per call. That might blow up the harness. Hmm, but that's the harness's business; the reported errors were about "building them" (the thunk). Actually "building them would take 559.3 GB" — that's the thunk's copy.

Hmm, but if we reuse a large instance, the harness still renders it every call for comparison. That could be slow but maybe not counted against us. Risky.

Let me keep caches small-ish (a few hundred to a few thousand entries) to keep rendering cheap, and make the call do work via long keys.

Actually, let's reconsider the whole thing. The function is O(1). The only way to make a call take ~1ms is a long key with fresh hashing. But fresh string creation costs ~ same as hashing.

Unless... we can create a long string cheaply and still force hashing. Hmm.

Alternative: use a key that is a large tuple? Hashing a tuple hashes each element. If elements are ints, hashing is fast. Not helpful.

Alternative: a string whose hash is expensive but that we can create cheaply? Creation is memcpy, hashing is siphash — both O(n). Similar cost. 

Hmm, but maybe the harness's metric: total arg building time across the window < 10s. If call takes 1ms and window is ~2s, ~2000 calls. Arg building 2000 × (string creation ~0.5ms) = 1s < 10s. That passes! And memory: 2000 × 2MB = 4GB... near limit. Use smaller strings.

Wait, the long-string case passed with 2MB strings. Let me just mimic that but tune.

Actually, let me reconsider: the long-string case had a 20-entry cache and a 2MB key built fresh each call. It passed. So that's a working pattern. Let me build cases around that: fresh long key each call, small cache.

But then all cases would be similar. We need 8 diverse cases. Diversity can come from: cache size, key position (front/middle/end), hit vs miss, key length, key type.

But if the key is fresh each call, it won't be in the cache unless we insert it. Hmm! Right — if we build a fresh key each call, it's a different object, but `in` uses equality not identity. So a fresh string equal to a stored key will match. So we can store "key10" and pass a fresh equal string. Good. And the hash is computed fresh (since new object). 

So: store a long string key in the cache, and each call pass a freshly-created equal long string. The `in` check hashes the fresh string (O(n)), finds match, move_to_end, return. 

For a miss: pass a fresh long string that's not in the cache. Hash O(n), no match, return None. Constant.

This gives work ~O(key length) per call.

Now, the concern: building the fresh long string each call costs ~O(n). To keep total under 10s, keep n moderate and call count moderate.

Let me pick key length ~ 1MB. Hashing 1MB ~ 0.5ms, creation ~0.3ms. Call ~0.5ms. Window maybe 1-2s → ~2000-4000 calls. Arg building 4000 × 0.3ms = 1.2s. OK.

Hmm, but actually the harness might run a fixed number of calls or a fixed time. The reported counts suggest a fixed time window (they say "in a window"). 

Let me be conservative: use key length ~ 200KB to 1MB, and small caches.

Actually, wait. Let me reconsider whether the hash is really the dominant cost. Let me just design robustly.

Alternative simpler robust approach: make the thunk free by reusing instances, and accept that calls are fast. The harness's problem was purely arg building. If thunk is free, no arg building cost. Let's check: for tiny-hit, thunk was `_copy(_TINY)` → copy of 10-entry dict, ~6µs × 1.96M = 12s. If thunk were `(_TINY, "key5")` → ~0.1µs. Then 1.96M × 0.1µs = 0.2s. Fine!

But then the call is fast (~0.2µs). The harness might run even more calls. But arg building stays cheap. Memory: reusing the same instance → no new memory. 

But the state-change issue: for tiny-hit with key5 in a 10-entry cache, key5 is not at the end, so first call moves it to end. Subsequent calls: key5 at end, no change. So only first call differs. The harness times many calls; the first is negligible. Output is same. 

But the harness renders args before/after each call. Before call 1: order [0..9]. After: [0,1,2,3,4,6,7,8,9,5]. Detected change! The harness might then... hmm, does it error? The rule says we should copy if changed. If we don't, maybe the harness still works but the "same work" is violated.

I think it's safer to avoid state changes: put the key at the end.

But then diversity is limited. We can still have:
1. hit at end, small cache
2. miss, small cache
3. hit at end, medium cache
4. miss, medium cache
5. hit at end, large cache
6. hit at end, int keys
7. hit at end, long string keys
8. miss, long string keys

Hmm, but "hit at end" all do the same work (one lookup + move_to_end). Not diverse in path. But the function only has 2 paths (hit/miss). Diversity in size and key type.

Actually, maybe better to just accept the copy for small caches. Copy of a small cache (say 100 entries) is cheap (~1µs). × many calls... if call is fast, many calls. Hmm.

Let me combine: use long keys (fresh each call) to make calls slow, so few calls, so even moderate copies are fine. And use copies for correctness.

Let me design:

For each hit case: cache contains a long key (say L bytes) at some position. Thunk: copy the cache (small, e.g., 5-50 entries) and create a fresh long string equal to the stored key. Call: hash fresh string O(L), match, move_to_end, return.

Wait, but if the stored key is at position p and we move to end, the copy is fresh each call so no carryover. Good, constant work.

For miss case: thunk creates fresh long string not in cache; copy cache.

The copy cost: number of entries × pointer. Keep entries small (≤ 100). Copy ~1-2µs. Call ~0.5ms. Ratio fine.

Actually, do we even need to copy? If we copy, the move_to_end state change is contained. Good, correct.

Let me now think about the fresh long string creation. `stored_key` is a long string. To create a fresh equal string each call: `str(stored_key)`? That returns the same object for str (str(x) returns x if x is str). Need a real copy: `stored_key[:]`? For str, slicing returns the same object if full slice? Actually `s[:]` returns the same object for str (immutable optimization). Hmm. `stored_key + ""`? Also may return same object. `"".join([stored_key])`? Returns same object maybe. 

To force a new object: `(stored_key + "x")[:-1]`? That creates a new string of same content. Or `stored_key.encode().decode()` — creates new. Or `bytearray`... 

Simplest: `stored_key * 1`? For strings, `s * 1` returns a new object? Let me think. Actually `s * 1` might return s itself. Hmm, CPython: `string_repeat` with n=1 returns the original? I believe it returns a new reference to the same object for n==1? Not sure.

Safest: `stored_key.encode().decode()` — definitely new object, but costs encode+decode (2× memcpy). Or `stored_key[:len(stored_key)]` — full slice, returns same object. 

Hmm. `str(stored_key)` same object. 

What about building the string from a template each time: `_PREFIX + _SUFFIX` where prefix+suffix creates new. But if we store the key as prefix+suffix, then each call does `_PREFIX + _SUFFIX` → new string O(L). That's clean!

So: `_LONG_A = "x" * (L//2)`, `_LONG_B = "y" * (L - L//2)`, stored key = `_LONG_A + _LONG_B`. Each call: `_LONG_A + _LONG_B` creates a fresh string equal to stored key. 

But concatenation of two strings creates a new object, O(L). Good. And hashing it is O(L). 

Actually, even simpler: use `bytes`? No, keys are strings.

OK let me also reconsider: maybe the harness's notion of "fresh arguments" is that the thunk returns new objects. If our thunk returns the same instance object (not copied), the harness might consider it not fresh but that's fine. The issue is just cost.

Let me just go with the copy + fresh long string approach.

Let me now pick parameters. The limit: total arg building < 10s, memory < 4.3GB. And call time 1-200ms ideally (or at least enough work).

Let me estimate: L = 1MB. Hash ~0.5ms, concat ~0.3ms. Call ~0.5ms. Window: unknown, but say the harness runs for ~1-2s → ~2000-4000 calls. Arg building: 4000 × (0.3ms + copy) ≈ 1.2s. Memory: 4000 × 1MB (fresh strings, but they're discarded after each call... the harness might keep them?) Hmm, "building them would take X GB" suggests they accumulate. If they keep all fresh args, 4000 × 1MB = 4GB. Near limit!

Hmm. That's risky. Let me use smaller L, like 100KB. Then 4000 × 100KB = 400MB. Safe. But call time ~0.05ms = 50µs, still > 1µs. Call count would be higher though (~20,000 in 1s?). Then arg building 20,000 × 0.03ms = 0.6s, memory 20,000 × 100KB = 2GB. Hmm.

The scaling: call time ∝ L, arg building per call ∝ L (string) + O(entries). Number of calls ∝ 1/L. So total arg building ∝ (1/L) × L = constant! And total memory ∝ (1/L) × L = constant. Interesting. So it doesn't matter much what L is, as long as the ratio of arg-cost to call-cost is small.

Arg cost = string concat (O(L)) + copy (O(entries)). Call cost = hash (O(L)) + lookups. So arg/call ratio ≈ 1 (concat vs hash). That's the problem — arg building is comparable to call cost, so total arg building ≈ total call time ≈ window length. If window is 1-2s, arg building ~1-2s < 10s. OK actually fine!

Wait, the reported failures: tiny-hit copy was 6µs while call was ~0.2µs → ratio 30. That's why it failed. With long keys, ratio ~1-2, so total arg building ~2-4s < 10s. And memory: total fresh strings = window/L × L = window_bytes... hmm, window is time not bytes. Let me redo.

Number of calls N ≈ T_window / T_call. T_call ∝ L. So N ∝ 1/L. Memory = N × L = T_window × (L/T_call) = T_window × const. Since T_call ∝ L, L/T_call is constant. So memory ∝ T_window. For T_window ~2s and hash rate ~2GB/s, memory ~ 2s × 2GB/s = 4GB. Hmm, borderline.

Hmm, that's because hashing processes ~2GB/s and the window is 2s, so ~4GB of strings get hashed. If the harness keeps them all, 4GB. Near limit.

To reduce memory: make the call slower per byte. E.g., use move_to_end which... no. Or make the key hashing slow but memory small? Can't.

Alternatively, reduce the window? We can't control it.

Hmm. Alternatively, make the call do work that's not proportional to key size, so memory (key size) is small but call is slow. But the function is O(1) with cached hash.

Wait — what if we make the cache large so move_to_end... no, still O(1).

Hmm. What if the key is a large object with expensive equality? E.g., a tuple of many elements where hash is cached? No.

Actually, here's an idea: make the key a string, but make the CALL do more hashing by... no.

Alternatively, accept that memory might approach the limit and use a moderate L. The long-string case with 2MB passed. So maybe the memory accounting isn't as I fear. Let me just use L ~ 500KB-1MB and see.

Actually, the reported "long-string-keys-hit: ok" used 2MB keys and 20-entry cache. Let me just replicate that pattern with variations.

Hmm, but wait: in that case, the thunk did `_copy(_LONG)` (copy 20 entries) and `_long_key(10)` (fresh 2MB string via f-string + "x"*2M). The f-string `f"longkey{i}_" + "x" * _LONG_LEN` creates a new 2MB string each call. And it passed. Good.

So let me build all cases with fresh long strings. Let me vary:
- L: 100KB, 500KB, 1MB, 2MB
- hit vs miss
- cache size: small (5), medium (100)
- key types: string, maybe bytes? Keys could be bytes. `bytes` is hashable. Hmm, but repository uses string keys probably.
- position: front/middle/end (with copy, position doesn't matter for correctness; the copy resets each call).

Let me write 8 cases:

1. "hit-end-small": cache 5 entries, target key at end, L=500KB. 
2. "hit-front-small": cache 5 entries, target at front, L=500KB. (move_to_end does more? still O(1))
3. "miss-small": cache 5 entries, fresh key not present, L=500KB.
4. "hit-medium": cache 100 entries, target, L=1MB.
5. "miss-medium": cache 100 entries, L=1MB.
6. "hit-int-keys": cache with int keys, target int. But int hashing is O(1)! So call is fast. Arg building: copy small cache, cheap. Hmm, but then many calls and copy cost × many... copy of 100 entries ~2µs, call ~0.2µs, ratio 10 → might fail. Use small cache (5 entries) → copy ~0.3µs, ratio ~1.5. Hmm borderline.

Hmm, for int keys we can't make the call slow. So the call is ~0.3µs (3 lookups). Arg building must be < ~0.3µs × (10s/2s) = 1.5µs. A copy of a 5-entry OrderedDict: OrderedDict() + 5 inserts ~ 1µs. Borderline. A copy of a 2-entry: ~0.5µs. OK use tiny caches for int keys.

Actually, maybe avoid int keys to reduce risk. But diversity... The task says "different paths through its code". The function has hit/miss paths. Key type diversity is nice but risky.

Alternatively, for int-key cases, don't copy — reuse instance with key at end (no state change). Then thunk is free. 

Actually, that's a great idea for ALL cases: reuse instance, key at end. Thunk free. No arg building cost. Let me reconsider.

If thunk is free, the harness's arg building cost is ~0. The only concern is the harness rendering args for comparison each call. If the cache is small (e.g., 5 entries), rendering is cheap. And the call is fast, so many calls, but each is cheap.

But the harness might complain "one call does too little work". The errors we got were specifically about arg building, not call work. Let me re-read: "one call does too little work for arguments that size; give it arguments that are cheaper to build, or on which one call does more of the work". So the fix suggested is cheaper args. So free thunk should work.

But wait — if the call is super fast and thunk is free, why did the harness include a "window"? It runs calls until some time budget. With free thunk and fast call, it runs millions. Each call is timed; total time is the window. Fine.

Hmm, but there's a subtlety: the harness renders args before and after each call to detect mutation. If the cache is reused and the key is at the end, no mutation, so before==after. Rendering a 5-entry dict is cheap. Good.

But if we reuse the instance and the key is NOT at the end, first call mutates. Then before != after for call 1. The harness might flag it. To be safe, key at end.

But then all hits are at end — same work. Is that OK? The function's hit path: `key in cache` (True), `move_to_end`, `cache[key]`. Whether key is at end or not, the code path is identical. The work is identical (move_to_end is O(1) regardless of position). So "hit at end" vs "hit at front" is the same code path and same work. So no diversity loss from the function's perspective!

So I can just use key at end for all hits, and it's representative.

Hmm, but is it "avoiding uniformity"? The rule says avoid patterns a simple trick could exploit. But here it's about input diversity. Eh.

Actually, let me reconsider: maybe better to copy small caches and use long keys, combining both. Let me just do the robust free-thunk approach with moderate caches and some long keys.

Wait, but if thunk is free and call is fast, the harness runs millions of calls. The harness also renders args each call. If cache is large (10,000 entries), rendering is expensive per call → harness overhead huge. So keep caches small.

But then the "work" is tiny. Is that acceptable? The function IS tiny. The harness wants 1-200ms per call ideally, but for such a function it's impossible without long keys.

Hmm, I'm torn. Let me think about what maximizes success probability.

The failures were all about arg building cost. The safest fix: make thunk as cheap as possible. Reuse instances, no copies, no fresh objects.

But then calls are ~0.3µs. The harness will run maybe 5-10M calls in a window. Each call involves the harness's timing overhead (perf_counter calls), which might dominate. But that's the harness's issue.

Actually, wait — the harness reported "1,964,761 calls in a window". So the window contains ~2M calls. If thunk is free, maybe 3-5M calls. Fine.

Let me go with: reuse instances, key at end for hits, miss for misses. Small to medium caches. Vary cache size and key type for diversity.

But hold on: for a hit at end, `move_to_end` — does it actually modify the OrderedDict even if already at end? Let me think about CPython's implementation: `move_to_end` finds the node and moves it to the end of the linked list. If it's already at the end, it still detaches and reattaches. The resulting order is identical. So the repr is identical. But the internal state (the linked list) is rebuilt — no observable difference. So before==after. Good.

Actually, hmm, does it update `self.__map`? No, only the linked list pointers. So repr same.

OK. But is there any chance the harness considers "the function changed the arguments" based on object identity or something? Unlikely.

Let me also consider: maybe the harness checks that outputs are equal across calls. get returns the value — same each time. Good.

Alright, but I worry the harness might reject "too little work" in some other check. The error text says the issue is arg building. Let me hedge: use long keys for SOME cases to make calls slower, and reuse instances (no copy) so arg building is still free.

For a hit with a long key: store the long key, pass the SAME long string object each call. Hash cached after first call → subsequent calls O(1) fast. So no benefit. To force rehash, need fresh string → arg cost.

Hmm. So long keys don't help unless fresh, which costs args.

OK here's another thought: what if we make the call slow via a large cache and a key... no, O(1).

The function is fundamentally O(1). So the only lever is hash cost of a fresh key. And that's balanced by arg cost.

Given the reported long-string case passed, let me use that pattern for a few cases and free-thunk for others. Mix.

Let me design 8 cases:

Use a mix:
- Cases with fresh long keys (call ~O(L)), small cache copy. 
- Cases with reused instance, key at end, small cache (call fast, thunk free).

Actually, mixing risks: the fresh-long-key cases might fail if memory is tight. The long-string case passed with 2MB. Let me use smaller, 200KB-500KB.

Hmm, let me reconsider the memory. The harness said for long-string "ok" — so with 2MB keys it was fine. Let me just use 1MB keys for the long cases.

Let me define a helper to build a cache and a "key factory".

Plan:

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)

def _make_cache(n, key_of):
    c = LRUCache(max_size=max(n, 1))
    for i in range(n):
        c.cache[key_of(i)] = _rng.randint(0, 10**9)
    return c
```

For long-key cases, I need a stored key and a way to produce a fresh equal key cheaply. Use two halves:

```python
_HALF = "a" * 500_000
_OTHER = "b" * 500_000
```

stored key = _HALF + _OTHER (1MB). fresh key each call = _HALF + _OTHER (new object).

But if the cache has multiple entries, we need other keys too. Let's make the long key the last entry.

Let me build:

Case A "hit-long-small": cache with 5 short entries + the long key at end. Thunk: copy cache + fresh long key. Wait, copying includes the long key reference (cheap, pointer). Fresh long key = _HALF + _OTHER.

Call: hash fresh key O(1MB), match, move_to_end, return.

Case B "miss-long-small": cache with 5 short entries. Thunk: copy + fresh long key (not present). Call: hash O(1MB), no match, return None.

Case C "hit-short-reuse": cache with 5 short entries, key at end. Thunk: (cache, key) reuse. Call fast.

Hmm, but if I reuse the same instance across cases... each case has its own instance. Fine.

Let me think about whether reusing an instance across calls causes issues with the harness's "fresh arguments" expectation. The harness calls the thunk each time; the thunk returns the same objects. The harness then calls the function. It compares outputs. Should be fine.

Actually, wait. There's a risk: the harness might run the original and modified functions on the same thunk results. If the original mutates the shared instance, the modified sees mutated state. But for key-at-end, no mutation. For miss, no mutation. So fine.

But if the harness runs original first (many times) then modified, the instance state is unchanged. Good.

Hmm, but actually the harness runs each input many times in a row for the original, then presumably resets for modified by re-calling thunks. If thunks return the same shared instance, and the function doesn't mutate, fine.

OK let me also worry: for the long-key hit case, if I reuse the instance but pass a fresh key each call, the cache is mutated (move_to_end moves the fresh key... but the fresh key equals the stored key, and move_to_end uses the stored key's node). Since stored key is at end, no change. Good. So actually for the long-key hit case, I could also reuse the instance (no copy)! Because the key is at end. Then thunk = fresh long key only. Arg cost = 1MB concat. Call = 1MB hash. Ratio 1.

Hmm, but do I need the copy? No, if key at end. Let me drop the copy to reduce arg cost. 

But wait, for a hit where the key is NOT at end, the first call moves it to end. To keep constant work, put at end. So no copy needed.

For miss, no mutation, no copy needed.

So actually, NO copies needed at all if we position keys at end for hits! Thunk cost = just the fresh key (for long cases) or free (for short cases).

Great, that simplifies.

Now diversity: 
- hit/miss
- long key (fresh, expensive) / short key (cached hash, cheap)
- cache size small/large
- key type int/str

Let me write 8:

1. "short-hit-small": 5-entry cache, short str key at end, reuse. Thunk free.
2. "short-miss-small": 5-entry cache, short str key not present, reuse. Thunk free.
3. "short-hit-large": 1000-entry cache, short key at end, reuse. Thunk free.
4. "short-miss-large": 1000-entry cache, short key not present, reuse. Thunk free.
5. "int-hit": 100-entry cache, int key at end, reuse. Thunk free.
6. "int-miss": 100-entry cache, int key not present, reuse. Thunk free.
7. "long-hit": 5-entry cache with 1MB key at end, fresh 1MB key each call. Thunk = concat.
8. "long-miss": 5-entry cache, fresh 1MB key not present. Thunk = concat.

Hmm, but cases 1-6 have free thunks and fast calls. The harness runs millions of calls. Is that a problem? The harness's per-call overhead (rendering args, timing) might be large. Rendering a 1000-entry cache each call × millions = huge. That could blow up the harness's own budget. Hmm.

Actually the harness renders args "before and after each call to see whether it changed them". For a 1000-entry cache, rendering is ~50µs. × millions = way too much. So the harness would be slow. But is that counted? The error messages were about "building them" (thunk). Rendering might be separate. Risky though.

Let me keep caches small (≤ 50 entries) to keep rendering cheap.

But then "large cache" diversity is lost. Eh, the function doesn't care about cache size for work. But diversity is requested. Let me use up to a few hundred.

Hmm, actually, let me reconsider. Maybe the harness is smart: it renders args once? No, "before and after each call".

To be safe, keep caches small: 5, 20, 100.

Let me reconsider the whole approach once more. The reported failures: all cases had thunks that copied the cache (O(entries)) plus in some cases built long keys. The successful case built a 2MB key AND copied 20 entries, and passed. So the harness tolerates the 2MB key build. The failures were because the call was too fast relative to arg build (copy dominated).

So the fix: reduce copy cost (fewer entries or no copy) and/or increase call cost (long fresh keys).

I'll go with: no copies (keys at end), moderate caches, mix of short and long keys.

Let me finalize:

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)

def _cache(n, key_of):
    c = LRUCache(max_size=max(n, 1))
    for i in range(n):
        c.cache[key_of(i)] = _rng.randint(0, 10**9)
    return c

# short-key caches, target key is the LAST entry (so move_to_end is a no-op)
_SMALL = _cache(5, lambda i: f"k{i}")
_SMALL_TARGET = "k4"

_MED = _cache(100, lambda i: f"k{i}")
_MED_TARGET = "k99"

_INT = _cache(50, lambda i: i)
_INT_TARGET = 49

# long-key cache: last entry is a long string
_HALF = "a" * 500_000
_OTHER = "b" * 500_000
_LONG_KEY = _HALF + _OTHER

_LONG_CACHE = LRUCache(max_size=5)
for i in range(4):
    _LONG_CACHE.cache[f"k{i}"] = _rng.randint(0, 10**9)
_LONG_CACHE.cache[_LONG_KEY] = _rng.randint(0, 10**9)

_LONG_MISS_CACHE = _cache(4, lambda i: f"m{i}")
```

Wait, for the long hit, the target key is at end. Good. For the long miss, the fresh key isn't present.

Thunks:
- short hit small: `lambda: (_SMALL, _SMALL_TARGET)` — reuse.
- short miss small: `lambda: (_SMALL, "nothere")`.
- short hit med: `lambda: (_MED, _MED_TARGET)`.
- short miss med: `lambda: (_MED, "nothere")`.
- int hit: `lambda: (_INT, _INT_TARGET)`.
- int miss: `lambda: (_INT, -1)`.
- long hit: `lambda: (_LONG_CACHE, _HALF + _OTHER)`.
- long miss: `lambda: (_LONG_MISS_CACHE, _HALF + _OTHER)`.

Hmm, for the long miss, the fresh key equals _LONG_KEY which is NOT in _LONG_MISS_CACHE. Good, miss.

But wait: for long miss, `_HALF + _OTHER` is a 1MB string. Hash O(1MB). Good.

For long hit, the fresh key equals _LONG_KEY which IS in _LONG_CACHE (at end). Good.

Concern: `_HALF + _OTHER` — does Python optimize this to return a cached object? No, string concatenation creates a new string (unless one is empty). Good.

Now, "same work every call": for long hit, the fresh key is at end (equal to stored key which is at end), so move_to_end no-op. Good. For repeated calls, cache unchanged.

For short hits, key at end. Good.

Now the checks():
```python
def checks():
    return [
        ("empty", lambda: (LRUCache(), "x")),
        ("single-hit", lambda: (_one, "only")),
        ("unhashable", lambda: (LRUCache(), [1, 2])),
    ]
```
where `_one` is a 1-entry cache.

Now, is there a risk the harness complains about the free-thunk cases doing "too little work"? The call is ~0.3µs. The harness window would contain ~5-10M calls. Arg building ~0. Should pass.

Hmm, but actually, wait. Let me reconsider: does the harness's "building them would take X" account for the thunk returning the SAME object? If the thunk returns `(_SMALL, _SMALL_TARGET)`, building the tuple is cheap (~0.1µs). × 5M = 0.5s. Fine.

Memory: the tuple is small, reused objects. Fine.

OK. But I'm slightly worried about the "one call does too little work" aspect. Let me make the short cases have slightly more work by... no, can't.

Alternatively, I could make ALL cases use long fresh keys, making calls ~0.5ms, so fewer calls, and arg building ~ concat cost. Ratio ~1. Total arg time ~ window ~ 1-2s < 10s. Memory: window × hash_rate ~ 2s × 2GB/s = 4GB. Borderline but the 2MB case passed.

Hmm, risky. Let me mix: half free-thunk fast cases, half long-key cases. If the long ones fail, the free ones should pass, giving ≥4.

Actually, the requirement is ≥4 usable. Let me make 6 free-thunk cases and 2 long-key cases, so even if long ones fail, 6 pass.

But are free-thunk cases definitely usable? The failures were about arg building. Free thunks have ~0 arg building. So they should pass. Unless the harness rejects them for another reason.

Hmm, let me reconsider: maybe the harness also has a minimum on call work to avoid noise. The error "one call does too little work" suggests they want more work per call. But the suggested fix is "cheaper arguments", implying that if args are cheap, little work per call is OK.

Actually re-reading: "one call does too little work for arguments that size; give it arguments that are cheaper to build, or on which one call does more of the work". So the problem is the RATIO of arg-build to call-work. Cheaper args fixes it. So free args → fixed.

OK, I'm fairly confident. Let me make most cases free-thunk.

But diversity: with free thunks, all cases are "fast call". The harness keeps the 4 that "do the most work". If all do similar work, it keeps 4 arbitrary. Fine, as long as they're usable.

Hmm, but "keep the 4 that do the most work" — if all do ~0 work, it keeps 4. Fine.

Let me add the long-key cases to have some that do more work (so they're likely kept and representative).

Let me finalize with 8 cases:

1. "hit-small-short" — free thunk, 5-entry cache, key at end.
2. "miss-small-short" — free thunk, 5-entry cache, miss.
3. "hit-medium-short" — free thunk, 100-entry cache, key at end.
4. "miss-medium-short" — free thunk, 100-entry cache, miss.
5. "hit-int" — free thunk, 50-entry int cache, int key at end.
6. "miss-int" — free thunk, 50-entry int cache, int miss.
7. "hit-long" — fresh 1MB key, 5-entry cache with long key at end.
8. "miss-long" — fresh 1MB key, 4-entry cache, miss.

Wait, for case 7, the cache contains the long key at end. The thunk builds a fresh equal 1MB key. Call hashes it. Good.

Hmm, one concern for case 7: the cache `_LONG_CACHE` has the long key stored. The harness renders the cache before/after each call — rendering a 1MB key string! That's expensive (repr of 1MB string). × many calls → huge. Hmm. The repr of a 1MB string is 1MB. Rendering it each call × 2000 calls = 2GB of string ops. Might be slow but maybe tolerable.

Actually, the harness renders args to compare. For case 7, args = (cache, key). cache repr includes the 1MB key → 1MB repr. key repr → 1MB. So ~2MB per call × 2000 = 4GB. Hmm. That might exceed. But the original long-string case had a 2MB key and passed, so rendering must be handled or not counted. Actually the original had the key in the cache too (20 entries with 2MB keys? No — `_build_cache(_LONG_N, _long_key)` builds 20 entries each with a 2MB key!). So 20 × 2MB = 40MB repr per call. And it passed. So rendering is either not done or cheap enough. OK, so my concern is unfounded. Good.

Actually wait, that means the harness's rendering might be the dominant cost but it passed, so it's fine.

Hmm, but actually if rendering 40MB per call × 2000 calls = 80GB, that can't be. So maybe the harness doesn't render large args, or the long case had very few calls. Let me not worry.

Actually, let me reconsider: maybe the harness renders args only ONCE (before and after a single call) or uses a hash. Whatever.

Let me reduce risk by making the long-key cache small and the key moderate (500KB).

Actually, let me reconsider using the long key in the cache at all. For the hit case, the key must be in the cache. So yes.

Alternatively, make the hit case use a SHORT stored key but... no, then hash is cached.

Hmm, what if the stored key is short but we pass a long key that hashes to the same bucket? No, equality fails.

OK, long key must be stored.

Let me just go with it.

Let me reconsider the sizes. Let me use 300KB halves → 600KB key. Or keep 500KB → 1MB.

I'll use 250_000 each → 500KB key. Safer on memory.

Let me write the final code.

Actually, one more consideration: the rule says "Generate stressful inputs: complex, time-consuming, as diverse as possible." and "Each case should make the function do substantial and different work". My free-thunk cases do minimal work. But the function is minimal. I'll add diversity via cache size and key types.

Also, I should make sure the hits are at the end so no mutation. But the harness might want the function to actually do move_to_end meaningfully. Eh.

Hmm, actually, let me reconsider: is it better to put the target key at the FRONT and copy a small cache? Then move_to_end does real work (moving from front to back). But copy cost... For a 5-entry cache, copy ~0.5µs, call ~0.3µs, ratio ~1.7. Might pass. And the function does "more work" (real move). 

But then the harness renders args before/after and sees a change → might complain? The rule says copy if it changes. We do copy. So each call gets a fresh copy, and the change is contained. Fine.

Hmm, but with a copy, the thunk cost is O(entries). For 100 entries, ~2µs, call ~0.3µs → ratio 7. Might fail. So keep copies tiny (≤5 entries) or avoid.

Let me mix: some cases with tiny copies and front keys (real move), some with reuse and end keys.

Actually, you know what, let me keep it simple and robust. The main goal: pass ≥4. Let me make all 8 with free or near-free thunks.

Decision: 
- 6 cases reuse instances with keys at end (free thunk).
- 2 cases use fresh long keys (moderate thunk).

Let me also add a tiny-copy case to show diversity? No, keep it simple.

Hmm, let me reconsider once more. Actually there's a subtle issue with reusing the instance and key at end: `move_to_end` on the last element. Let me verify CPython doesn't do something weird. In `OrderedDict.move_to_end`, if last=True (default), it does `self.__map[key]` to get the link, then `link_prev, link_next = link[0], link[1]`... it unlinks and appends. The order stays the same. So repr unchanged. Good.

But it does allocate? No. Good.

Alright, writing final code.

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)


def _build(n, key_of):
    c = LRUCache(max_size=max(n, 1))
    for i in range(n):
        c.cache[key_of(i)] = _rng.randint(0, 10 ** 9)
    return c


# small string-keyed cache; queried key is the last entry (move_to_end is a no-op)
_SMALL = _build(5, lambda i: f"k{i}")
_SMALL_HIT = "k4"
_SMALL_MISS = "absent"

# medium string-keyed cache
_MED = _build(120, lambda i: f"key-{i}")
_MED_HIT = "key-119"
_MED_MISS = "nope"

# integer-keyed cache
_INT = _build(64, lambda i: i * 7 + 1)
_INT_HIT = 63 * 7 + 1
_INT_MISS = -12345

# long-key cache: last entry is a long string
_HALF_A = "a" * 250_000
_HALF_B = "b" * 250_000
_LONG_KEY = _HALF_A + _HALF_B

_LONG = LRUCache(max_size=5)
for i in range(4):
    _LONG.cache[f"L{i}"] = _rng.randint(0, 10 ** 9)
_LONG.cache[_LONG_KEY] = _rng.randint(0, 10 ** 9)

_LONG_MISS = _build(4, lambda i: f"M{i}")
```

Wait, `_INT_HIT = 63*7+1 = 442`. And `_build(64, ...)` creates keys 1, 8, 15, ..., 442. Last is 442. Good.

Thunks:
- small hit: `lambda: (_SMALL, _SMALL_HIT)`
- small miss: `lambda: (_SMALL, _SMALL_MISS)`
- med hit: `lambda: (_MED, _MED_HIT)`
- med miss: `lambda: (_MED, _MED_MISS)`
- int hit: `lambda: (_INT, _INT_HIT)`
- int miss: `lambda: (_INT, _INT_MISS)`
- long hit: `lambda: (_LONG, _HALF_A + _HALF_B)`
- long miss: `lambda: (_LONG_MISS, _HALF_A + _HALF_B)`

Checks:
```python
_ONE = LRUCache(max_size=1)
_ONE.cache["only"] = 7

def checks():
    return [
        ("empty", lambda: (LRUCache(), "x")),
        ("single-hit", lambda: (_ONE, "only")),
        ("unhashable", lambda: (LRUCache(), [1, 2, 3])),
    ]
```

Hmm, "unhashable" will raise TypeError — checks may raise, that's allowed.

Now, wait: for the long hit case, the cache `_LONG` is reused across calls. The fresh key is at end (equal to stored). move_to_end no-op. So cache unchanged. Good.

But for the long miss, `_LONG_MISS` reused, no mutation. Good.

One concern: the harness might run the original and modified functions with the SAME thunk results (same instance). Since no mutation, fine.

Another concern: does reusing the instance across the many calls of the SAME case cause any drift? No mutation → no drift.

I think this is good. Let me also double check the "long hit" thunk: `_HALF_A + _HALF_B` creates a 500KB string each call. Cost ~0.1ms? Actually concatenating two 250KB strings: memcpy 500KB ~ 0.05ms. Hash 500KB ~ 0.25ms. So call ~0.25ms, arg ~0.05ms. Ratio 0.2. 

Number of calls in window: if window ~1s, ~4000 calls. Arg building 4000 × 0.05ms = 0.2s. Memory 4000 × 500KB = 2GB. Hmm, borderline. If window is 2s, 4GB. Risky.

Let me reduce to 100KB halves → 200KB key. Then call ~0.1ms, ~10000 calls in 1s, arg 10000×0.02ms=0.2s, memory 10000×200KB=2GB. Same. Hmm, memory scales with window regardless.

The memory is window_time × (bytes/hash_time). Hash rate ~2GB/s. Window ~1-2s → 2-4GB. Near limit 4.3GB.

Hmm. To reduce, make the call slower per byte. Can I? The call hashes once. What if the key appears... no.

What if I use a key type whose hash is slower per byte? E.g., a string with non-ASCII? No.

What if the call does more hashing? `key in self.cache` hashes once. Then `move_to_end` and `[]` use cached hash. So one hash per call.

Hmm, what if the key is NOT in the cache (miss)? Then `key in self.cache` hashes once, no match, return. One hash. Same.

So one hash per call, memory ∝ window × hash_rate.

To reduce memory below 4.3GB with window 2s, need hash_rate < 2GB/s. Python's siphash is maybe ~1-2 GB/s. Borderline.

Alternatively, make the window shorter — can't control.

Hmm, but the original long-string case with 2MB passed. So maybe the harness's window for slow calls is short (it stops after enough calls). Or the memory accounting is different. Let me not over-worry and use 200KB keys.

Actually, let me reconsider: maybe the harness's "memory" is peak memory, not accumulated. If the fresh strings are garbage-collected after each call, peak memory is small! The phrase "building them would take 2,063.8 GB" suggests they sum it, but maybe it's an estimate of total allocation, not peak. If it's total allocation, then it's a throughput concern. Hmm.

For the failing cases, "building them would take 559.3 GB" — that's total allocation across calls (copy of 10,000 entries × 749,558 calls × ~80 bytes ≈ 600GB). So it's total allocation. And the limit 4.3GB is presumably total allocation budget? That seems small for total. Actually 4.3GB total allocation over a window is tiny. Hmm.

Wait, maybe 4.3GB is the peak memory limit. And "building them would take 559.3 GB" is the total memory if all kept. Confusing.

Let me re-read: "each of the 749,558 calls in a window gets fresh arguments, and building them would take 559.3 GB (limit 4.3 GB)". So they estimate building all the fresh args takes 559GB, exceeding a 4.3GB limit. This suggests they'd keep them? Or it's total allocation. Either way, our long-key cases allocate ~window × hash_rate bytes.

For the passing long-string case, it allocated 2MB per call × N calls. If N ~ 2000, that's 4GB. It passed, so limit is around there or the accounting differs.

To be safe, let me make the long-key cases allocate less: use 100KB keys (200KB total). Then N ~ 10000, total 2GB. Hmm same.

The fundamental issue: total allocation = window_time × (allocation_rate). Allocation rate for building a string = 1/concatenation_time. Concatenation ~ memcpy ~ 10GB/s. So allocation rate ~10GB/s → 2s window = 20GB! That's over.

Hmm wait, but the string is allocated once per call, and the call takes hash_time. Number of calls = window/hash_time. Total bytes = calls × key_size = window × key_size / hash_time = window × hash_rate. Hash rate ~2GB/s → 2s × 2GB/s = 4GB. OK.

So it's ~4GB, borderline. The passing case suggests it's OK. Let me use a slightly smaller key to be safe, like 150KB. Then total ~3GB.

Hmm, but smaller key → faster call → more calls → same total. It's invariant! Total = window × hash_rate regardless of key size. So key size doesn't matter for total allocation. Only the window and hash rate matter.

So the long-key approach inherently allocates ~window × 2GB/s. If window is 2s, 4GB. If 1s, 2GB. The passing case implies window is short enough or the limit is lenient.

Given the passing case, I'll include 2 long-key cases with moderate keys. If they fail, I still have 6 free-thunk cases.

Hmm, but actually if the 6 free-thunk cases all pass, I'm fine. Let me make sure they pass. Their thunk cost is ~0.1µs (tuple creation). Total arg building = calls × 0.1µs. Calls = window / call_time. Call time ~0.3µs → calls ~ 3M for 1s window. Total arg = 3M × 0.1µs = 0.3s < 10s. Memory: reusing objects, so ~0. 

So free-thunk cases should definitely pass.

But wait — will the harness consider them "too little work"? The call is 0.3µs. Hmm. The harness might have a minimum. But the error text focuses on the ratio. Let me trust it.

Actually, hmm, let me reconsider. If the call is 0.3µs and the harness's own per-call overhead (timing, rendering) is say 1µs, then the harness sees 1.3µs per call and runs ~1M calls. The rendering of a 120-entry cache each call: ~10µs. That dominates! So the harness would be slow, but it's the harness's cost, not ours. Would the harness count it? The error says "building them" — that's the thunk. Rendering is separate. Probably fine.

But to reduce rendering cost, keep caches small. Let me use ≤ 120 entries. Actually, let me use smaller: 5, 50, 20. Hmm, diversity.

Actually, rendering a 120-entry OrderedDict: repr of 120 items ~ maybe 5µs. × 1M calls = 5s. That's harness overhead. Might slow the harness but not fail our metric. Eh.

Let me keep caches modest: 5, 40, 16.

Hmm, I realize I'm overthinking. Let me just write it.

Let me reconsider the "large cache" diversity. Since the function is O(1), cache size doesn't change work. But the task wants realistic scale. The repository uses max_size=20 by default. So caches of size ~20 are realistic! Let me use sizes around 20.

Actually the default max_size=20. So realistic caches are small. Good — use sizes like 5, 20, 50.

Final cases:
1. "hit-typical" — 20-entry cache, key at end. Free thunk.
2. "miss-typical" — 20-entry cache, miss. Free thunk.
3. "hit-small" — 5-entry cache, key at end. Free thunk.
4. "miss-small" — 5-entry cache, miss. Free thunk.
5. "hit-large" — 100-entry cache, key at end. Free thunk.
6. "hit-int" — 50-entry int cache, key at end. Free thunk.
7. "hit-long-key" — 5-entry cache with 200KB key at end, fresh key. 
8. "miss-long-key" — 4-entry cache, fresh 200KB key, miss.

Hmm, cases 7,8 have expensive calls. Cases 1-6 cheap.

Wait, I want the 4 kept to be diverse. The harness keeps the 4 doing most work → likely 7,8 and maybe 5,6. Fine.

Let me write it.

Actually, let me reconsider case 7/8 key size. Let me use 250KB halves = 500KB. Or smaller, 100KB halves = 200KB. I'll use 200KB total (100KB each).

Hmm, actually, let me reconsider: does the harness's total-allocation concern apply to the tuple creation too? For free cases, the tuple `(_SMALL, "k4")` is created each call. That's ~56 bytes × 3M calls = 168MB. Fine.

OK writing.

One more: for the long hit, the stored key in the cache is `_LONG_KEY = _HALF_A + _HALF_B`. The fresh key is `_HALF_A + _HALF_B` (new object, equal). Good.

But careful: for the long MISS case, the fresh key `_HALF_A + _HALF_B` equals `_LONG_KEY`, which is NOT in `_LONG_MISS`. So miss. Good. But note `_LONG_KEY` is in `_LONG` (the hit cache). Different cache objects. Fine.

Let me write the code now.

Also need `WORKDIR`? No files. Good.

Let me double check imports: `from backend.cache import LRUCache`. The module imports `from collections import OrderedDict`. Our import of backend.cache requires the path `visual-retrieval-colpali/src` on sys.path. The task says import as shown. Presumably the harness sets it up. Good.

Let me write.

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)


def _build(n, key_of):
    c = LRUCache(max_size=max(n, 1))
    for i in range(n):
        c.cache[key_of(i)] = _rng.randint(0, 10 ** 9)
    return c


_SMALL = _build(5, lambda i: f"s{i}")
_SMALL_HIT = "s4"
_SMALL_MISS = "s-missing"

_TYP = _build(20, lambda i: f"t{i}")
_TYP_HIT = "t19"
_TYP_MISS = "t-missing"

_BIG = _build(120, lambda i: f"b{i}")
_BIG_HIT = "b119"
_BIG_MISS = "b-missing"

_INT = _build(50, lambda i: i * 3 + 2)
_INT_HIT = 49 * 3 + 2
_INT_MISS = -999

_HALF_A = "a" * 100_000
_HALF_B = "b" * 100_000
_LONG_KEY = _HALF_A + _HALF_B

_LONG = LRUCache(max_size=5)
for i in range(4):
    _LONG.cache[f"L{i}"] = _rng.randint(0, 10 ** 9)
_LONG.cache[_LONG_KEY] = _rng.randint(0, 10 ** 9)

_LONG_MISS = _build(4, lambda i: f"M{i}")

_ONE = LRUCache(max_size=1)
_ONE.cache["only"] = 7


def checks():
    return [
        ("empty", lambda: (LRUCache(), "x")),
        ("single-hit", lambda: (_ONE, "only")),
        ("unhashable", lambda: (LRUCache(), [1, 2, 3])),
    ]


def cases():
    return [
        ("hit-typical", lambda: (_TYP, _TYP_HIT)),
        ("miss-typical", lambda: (_TYP, _TYP_MISS)),
        ("hit-small", lambda: (_SMALL, _SMALL_HIT)),
        ("miss-small", lambda: (_SMALL, _SMALL_MISS)),
        ("hit-large", lambda: (_BIG, _BIG_HIT)),
        ("miss-large", lambda: (_BIG, _BIG_MISS)),
        ("hit-int-keys", lambda: (_INT, _INT_HIT)),
        ("hit-long-key", lambda: (_LONG, _HALF_A + _HALF_B)),
    ]
```

Hmm, that's 8 but I dropped the long miss. Let me include long miss instead of one. Let me pick 8:

1. hit-typical (20, str)
2. miss-typical (20, str)
3. hit-small (5, str)
4. miss-large (120, str)
5. hit-large (120, str)
6. hit-int-keys (50, int)
7. hit-long-key
8. miss-long-key

That's 8. Good, diverse.

Wait, but the harness keeps the 4 doing most work. The long ones do most. Then typical ones. Fine.

Hmm, I worry the free-thunk cases might be flagged as "too little work" and dropped, leaving only 2 long ones → fail. Let me add more long cases to be safe? But long cases risk memory.

Alternatively, make ALL cases have some work. Hmm.

Let me reconsider: the harness keeps 4 of 8 that "do the most work". If 6 free cases do ~0 work, the 2 long cases do most, kept. Then only 2 usable → fail (need ≥4).

Wait, "Only 1 of the 8 measured inputs can be used; we need at least 4." So they need ≥4 usable. If only 2 do work and are kept, that's <4. So I need ≥4 cases that are usable AND do substantial work.

Hmm! So the free-thunk cases might be dropped for doing too little work. So I need at least 4 cases with substantial work.

So I should make ≥4 cases do substantial work. Substantial work = long fresh keys (only way). So make ≥4 long-key cases. But memory risk.

Hmm. Let me reconsider. Are free-thunk cases "usable"? The harness's criterion for keeping: "the 4 that do the most work". If free cases do ~0 work, they're not kept. So I need ≥4 cases with real work.

So let me make 5-6 long-key cases, each with distinct characteristics.

But the memory concern... The passing long-string case used 2MB keys. So 2MB is OK. Let me use ~500KB-1MB keys for the long cases.

Let me design 6 long-key cases + 2 others (maybe the others also get work via moderate keys).

Long-key cases with diversity:
- L1: hit, 500KB key at end, small cache (5).
- L2: miss, 500KB key, small cache (5).
- L3: hit, 1MB key at end, medium cache (20).
- L4: miss, 1MB key, medium cache (20).
- L5: hit, 300KB key at end, large cache (100).
- L6: hit, 500KB key at front (with copy? no, key at front → mutation). Hmm, for hit at front, first call moves to end. To keep constant work, either copy (cost) or accept drift.

Hmm, for hit at front without copy: call 1 hashes fresh key (O(L)), moves to end. Call 2: fresh key equal to stored, now at end, hashes O(L), move_to_end no-op. So after call 1, constant. Only call 1 differs. Negligible. And output same. But the harness renders before/after: call 1 changes order. Might be flagged. But only once. Probably fine.

Actually, let me avoid front hits to be safe. Use end hits.

- L6: hit with int... no, int hashes are O(1).

Hmm. Let me think of other diversity:
- Different key lengths (300KB, 500KB, 1MB).
- Different cache sizes (5, 20, 100).
- hit vs miss.
- Maybe a key that's a concatenation of many small pieces (different hash path? no).

Let me do:
1. hit, 300KB key, cache 5.
2. miss, 300KB key, cache 5.
3. hit, 600KB key, cache 20.
4. miss, 600KB key, cache 20.
5. hit, 1MB key, cache 100.
6. miss, 1MB key, cache 100.

Plus 2 more:
7. hit, 600KB key, cache 5, but key at... hmm same.
8. Maybe a "repeated" case: hit with a key that's a long string of a single char (different hash distribution? no).

Hmm, 6 long cases is enough (need ≥4). Let me add 2 non-long for diversity but they might be dropped.

Actually, let me make all 8 long-ish to maximize kept count.

Wait, but if all 8 are long and all pass, great. If memory fails for the 1MB ones, the 300KB ones still pass. Let me use a range of sizes.

Let me reconsider memory for 300KB key: total allocation = window × hash_rate ~ 2s × 2GB/s = 4GB. Same regardless of key size! So all long cases have similar total allocation. Hmm.

Unless the window is determined by number of calls (fixed count) rather than time. If fixed count N, total allocation = N × key_size. Then smaller keys → less memory. But the errors mention "calls in a window" suggesting time-based.

Ugh. Let me just use moderate keys (200-500KB) and hope.

Actually, let me reconsider the passing case: 2MB keys passed. So the harness's total allocation for that was acceptable. If it's time-based at ~2GB/s, 2MB keys → 4GB. Passed. So limit ~4.3GB is right at the edge, and it passed. So maybe hash rate is lower or window shorter.

Let me use 500KB keys to be safer (half the 2MB case). Hmm, but time-based total is independent of key size. So 500KB → same 4GB. No help.

If count-based, 500KB → 1/4 of 2MB case's memory. Help.

I'll use 400KB keys. Compromise.

Hmm, actually, let me reconsider: maybe I can make the call do more work per byte, reducing the number of calls and thus total allocation. 

Idea: make the key a string, but the cache lookup involves string comparison too? No, hash match then identity/equality check. For a fresh equal string, after hash match, Python checks equality: `key == stored_key`. String equality is O(1) if identity differs but... actually CPython's string equality first checks length, then memcmp. So it's O(L) too! So the call does hash O(L) + equality O(L) = 2× O(L). Hmm, actually for a dict lookup with a hash collision (same hash, different object), it does the equality check. So yes, ~2× work.

Wait, but hash is cached after first computation. Within one call: `key in self.cache` → hash (O(L)) + equality (O(L)). Then `move_to_end` → hash (cached, O(1)) + equality (O(L))? Actually move_to_end looks up `self.__map[key]` which does hash + equality. Then `self.cache[key]` → hash + equality. So 3 equality checks of O(L) each! Total ~3L memcmp + 1L hash = 4L work.

Hmm interesting. So the call does ~4× O(L). And arg building (concat) does ~1× O(L). Ratio 4. 

So total allocation = window × (allocation_rate). Allocation rate = 1/concat_time = 1/(L/memcpy_rate) ... total bytes = calls × L = window/call_time × L = window × L/(4L/memcpy_rate) = window × memcpy_rate/4. memcpy ~10GB/s → 2.5GB/s → 2s window = 5GB. Hmm.

OK whatever. Let me just try and use moderate keys.

Actually, maybe I'm overanalyzing. The original long case passed. Let me replicate its structure closely but with variety, and use similar key sizes (up to 2MB). Since it passed, similar should pass.

Let me use key sizes around 500KB-1MB.

Final design (8 cases, all with fresh long keys):

1. "hit-500k-small": 5-entry cache, 500KB key at end.
2. "miss-500k-small": 5-entry cache, 500KB fresh key miss.
3. "hit-500k-medium": 20-entry cache, 500KB key at end.
4. "miss-500k-medium": 20-entry cache, 500KB miss.
5. "hit-1m-large": 100-entry cache, 1MB key at end.
6. "miss-1m-large": 100-entry cache, 1MB miss.
7. "hit-250k-small": 5-entry cache, 250KB key at end.
8. "hit-2m-small": 5-entry cache, 2MB key at end.

Hmm, for the miss with 1MB: the cache has 100 short entries, fresh 1MB key not present.

Let me define a helper to make a long key from two halves.

```python
def _mk_halves(n):
    return "a" * n, "b" * n
```

Store key = a+b.

Let me write:

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)


def _build(n, key_of):
    c = LRUCache(max_size=max(n, 1))
    for i in range(n):
        c.cache[key_of(i)] = _rng.randint(0, 10 ** 9)
    return c


def _long_cache(n_short, half_len, seed):
    a = "a" * half_len
    b = "b" * half_len
    c = LRUCache(max_size=n_short + 1)
    rng = random.Random(seed)
    for i in range(n_short):
        c.cache[f"L{seed}_{i}"] = rng.randint(0, 10 ** 9)
    c.cache[a + b] = rng.randint(0, 10 ** 9)
    return a, b, c
```

Hmm, simpler to just define constants.

Let me write explicit:

```python
_A_500 = "a" * 250_000
_B_500 = "b" * 250_000
_KEY_500 = _A_500 + _B_500

_A_250 = "a" * 125_000
_B_250 = "b" * 125_000
_KEY_250 = _A_250 + _B_250

_A_1M = "a" * 500_000
_B_1M = "b" * 500_000
_KEY_1M = _A_1M + _B_1M

_A_2M = "a" * 1_000_000
_B_2M = "b" * 1_000_000
_KEY_2M = _A_2M + _B_2M
```

Caches:

```python
def _with_long(n_short, tag, long_key, seed):
    c = LRUCache(max_size=n_short + 1)
    rng = random.Random(seed)
    for i in range(n_short):
        c.cache[f"{tag}{i}"] = rng.randint(0, 10 ** 9)
    c.cache[long_key] = rng.randint(0, 10 ** 9)
    return c

_C5_500 = _with_long(4, "p", _KEY_500, 1)
_C5_250 = _with_long(4, "q", _KEY_250, 2)
_C5_2M = _with_long(4, "r", _KEY_2M, 3)
_C20_500 = _with_long(19, "s", _KEY_500, 4)
_C100_1M = _with_long(99, "t", _KEY_1M, 5)

_MISS5 = _build(5, lambda i: f"m{i}")
_MISS20 = _build(20, lambda i: f"n{i}")
_MISS100 = _build(100, lambda i: f"o{i}")
```

Cases:

```python
def cases():
    return [
        ("hit-250k-small", lambda: (_C5_250, _A_250 + _B_250)),
        ("hit-500k-small", lambda: (_C5_500, _A_500 + _B_500)),
        ("miss-500k-small", lambda: (_MISS5, _A_500 + _B_500)),
        ("hit-500k-medium", lambda: (_C20_500, _A_500 + _B_500)),
        ("miss-500k-medium", lambda: (_MISS20, _A_500 + _B_500)),
        ("hit-1m-large", lambda: (_C100_1M, _A_1M + _B_1M)),
        ("miss-1m-large", lambda: (_MISS100, _A_1M + _B_1M)),
        ("hit-2m-small", lambda: (_C5_2M, _A_2M + _B_2M)),
    ]
```

Wait, for miss-500k-small: `_MISS5` has keys m0..m4 (short). Fresh key `_A_500 + _B_500` = `_KEY_500`, not in `_MISS5`. Miss. Good.

For hit-500k-medium: `_C20_500` contains `_KEY_500` at end. Fresh key equal. Hit. Good.

For miss-1m-large: `_MISS100` short keys. Fresh `_KEY_1M` not present. Miss. Good.

For hit-2m-small: `_C5_2M` contains `_KEY_2M`. Hit.

Hmm, but note: `_A_500 + _B_500` is computed in the thunk each call. But `_KEY_500` is the stored key. Equal. Good.

Now, concern: the thunk `_A_500 + _B_500` creates a new 500KB string. But CPython might cache the concatenation? No.

Another concern: `_A_500 + _B_500` — since `_A_500` and `_B_500` are module-level constants, and the result is a new string each time. Good.

Now, is there a risk that the harness's rendering of the cache (which contains a 2MB key) is too slow? The original case had 20 entries with 2MB keys (40MB) and passed. Mine has 1 entry with 2MB key (2MB). Better.

Wait, actually the original `_LONG = _build_cache(_LONG_N, _long_key)` with `_LONG_N=20` and `_long_key` returns `f"longkey{i}_" + "x"*2_000_000`. So 20 distinct 2MB keys = 40MB. And it passed. So rendering 40MB is fine. Mine is much less.

OK good.

Now, checks:

```python
_ONE = LRUCache(max_size=1)
_ONE.cache["only"] = 7

def checks():
    return [
        ("empty", lambda: (LRUCache(), "x")),
        ("single-hit", lambda: (_ONE, "only")),
        ("unhashable", lambda: (LRUCache(), [1, 2, 3])),
    ]
```

Now let me reconsider: are 8 long cases all going to be "usable"? They all do substantial work. So ≥4 kept. 

But memory: 8 cases, each allocating ~window × hash_rate. If run sequentially, peak is one case at a time. Total per case ~4GB. Hmm, if the limit is total across all cases, 8 × 4GB = 32GB > 4.3GB. But the limit is probably per case. The original had 8 cases too and only 1 passed. So per-case.

Hmm, wait, actually the original 7 failed for arg-building-time/memory, 1 passed. So per-case limit.

Let me reduce key sizes to lower per-case allocation. Use 250KB max? But then calls are faster, more calls, same total. Argh.

OK, the total is invariant. So it doesn't matter. Let me just use moderate sizes and hope the harness's window is short.

Actually, let me reconsider: maybe the harness's window is a fixed NUMBER of calls (like 1000 or 10000), not time. The errors say "1,964,761 calls in a window" — that's a lot, suggesting time-based (they ran until a time budget). For the long case, fewer calls.

If time-based with budget ~1s: total allocation ~1s × hash_rate. If hash_rate ~2GB/s, 2GB. OK.

The 2MB passing case: if it ran ~1s, ~2000 calls × 2MB = 4GB. Passed. So limit ~4.3GB. Consistent.

So my 500KB cases: ~1s / (call_time). call_time for 500KB ~ 4×500KB / 10GB/s = 0.2ms. Calls ~5000. Total 5000 × 500KB = 2.5GB. OK.

1MB cases: call_time ~0.4ms, calls ~2500, total 2.5GB. Same.

2MB case: call_time ~0.8ms, calls ~1250, total 2.5GB. Same.

All ~2.5GB. Under 4.3GB. 

But wait, the original 2MB case passed at ~4GB? Maybe its window was shorter. Anyway, ~2.5GB should be safe.

Hmm, but actually my estimate of hash_rate might be off. Let me use 250KB keys to be extra safe? No, invariant. OK.

Let me just go with sizes 250KB, 500KB, 1MB, 2MB.

Actually, to be safe, let me cap at 1MB max and use mostly 250-500KB.

Let me finalize:

1. hit-250k-small
2. hit-500k-small
3. miss-500k-small
4. hit-500k-medium
5. miss-500k-medium
6. hit-1m-large
7. miss-1m-large
8. hit-2m-small

Drop 2MB? Keep it as the original passed with 2MB. Keep.

Hmm, actually let me drop the 2MB to reduce risk and use a different diversity: maybe a case where the key is at the FRONT (with a copy). Or a case with int keys but... no work.

Let me replace hit-2m-small with a "hit-500k-front" using a small copy:

`lambda: (_copy(C5_500_front), _A_500 + _B_500)` where the key is at the front. Copy of 5 entries ~0.5µs, call ~0.2ms. Ratio tiny. Fine. And it exercises the real move_to_end (front→back).

Hmm, but the copy is fresh each call, so the key is always at front. Good, constant work.

Let me add that.

Actually, let me keep it simple: 8 long cases with variety in size and hit/miss. Let me finalize.

Let me write the code cleanly.

```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)


def _build(n, key_of, seed=0):
    c = LRUCache(max_size=max(n, 1))
    rng = random.Random(seed)
    for i in range(n):
        c.cache[key_of(i)] = rng.randint(0, 10 ** 9)
    return c


def _halves(n):
    return "a" * n, "b" * n


_A250, _B250 = _halves(125_000)
_A500, _B500 = _halves(250_000)
_A1M, _B1M = _halves(500_000)
_A2M, _B2M = _halves(1_000_000)

_KEY250 = _A250 + _B250
_KEY500 = _A500 + _B500
_KEY1M = _A1M + _B1M
_KEY2M = _A2M + _B2M


def _cache_with_long(n_short, tag, long_key, seed):
    c = LRUCache(max_size=n_short + 1)
    rng = random.Random(seed)
    for i in range(n_short):
        c.cache[f"{tag}{i}"] = rng.randint(0, 10 ** 9)
    c.cache[long_key] = rng.randint(0, 10 ** 9)
    return c


_C5_250 = _cache_with_long(4, "p", _KEY250, 1)
_C5_500 = _cache_with_long(4, "q", _KEY500, 2)
_C20_500 = _cache_with_long(19, "r", _KEY500, 3)
_C100_1M = _cache_with_long(99, "s", _KEY1M, 4)
_C5_2M = _cache_with_long(4, "t", _KEY2M, 5)

_MISS5 = _build(5, lambda i: f"m{i}", 6)
_MISS20 = _build(20, lambda i: f"n{i}", 7)
_MISS100 = _build(100, lambda i: f"o{i}", 8)

_ONE = LRUCache(max_size=1)
_ONE.cache["only"] = 7


def checks():
    return [
        ("empty", lambda: (LRUCache(), "x")),
        ("single-hit", lambda: (_ONE, "only")),
        ("unhashable", lambda: (LRUCache(), [1, 2, 3])),
    ]


def cases():
    return [
        ("hit-250k-small", lambda: (_C5_250, _A250 + _B250)),
        ("hit-500k-small", lambda: (_C5_500, _A500 + _B500)),
        ("miss-500k-small", lambda: (_MISS5, _A500 + _B500)),
        ("hit-500k-medium", lambda: (_C20_500, _A500 + _B500)),
        ("miss-500k-medium", lambda: (_MISS20, _A500 + _B500)),
        ("hit-1m-large", lambda: (_C100_1M, _A1M + _B1M)),
        ("miss-1m-large", lambda: (_MISS100, _A1M + _B1M)),
        ("hit-2m-small", lambda: (_C5_2M, _A2M + _B2M)),
    ]
```

Wait, there's a bug: `_KEY500` is used in both `_C5_500` and `_C20_500`. That's fine (same key in different caches).

But careful: `_A500 + _B500` equals `_KEY500`. In `_C5_500`, `_KEY500` is at end. Hit. Good.

Now, the miss cases: `_MISS5` has keys m0..m4. `_KEY500` not present. Miss. Good.

Hmm, one issue: for the miss cases, the fresh key `_A500 + _B500` is a long string. Hash O(500KB). Good.

Now, is there any issue with `max_size`? The function doesn't use max_size. Fine.

Let me double-check `_build` default seed param — I pass seed. Fine.

Now let me reconsider whether the harness might complain about the thunks creating new large strings each call (arg building). The thunk cost = concat ~ 500KB memcpy ~ 0.05ms. Call cost ~ 0.2ms. Ratio 0.25. Total arg building = 0.25 × total call time = 0.25 × window ~ 0.25s. Under 10s. 

Memory: 500KB per call × 5000 calls = 2.5GB. Under 4.3GB. OK.

I think this is good. Let me also double check: does `_A500 + _B500` return a new object? Yes, string concatenation of two non-empty strings creates a new string.

But wait — CPython has a peephole optimizer for constant folding at compile time. `_A500 + _B500` where both are module globals (not constants) — no folding. Good.

Actually, hold on: could CPython's string concatenation be optimized with `PyUnicode_Concat` returning a cached/interned result? No.

OK. Also, is the hash of the fresh string computed? Yes, new object → no cached hash → computed on first lookup.

Great.

One more: the harness compares outputs. `get` returns the stored value (an int). Same each call. Good.

For miss, returns None. Good.

Let me also make sure the checks don't crash the harness setup. "unhashable" raises TypeError when called — allowed for checks.

Actually, wait: `key in self.cache` with an unhashable list raises TypeError. Good, that's the edge case.

Let me finalize. I'll clean up the code.

Actually, let me reconsider the number of distinct long keys and memory during SETUP. Module-level: we create `_KEY250, _KEY500, _KEY1M, _KEY2M` plus halves. Total ~ 2×(125K+250K+500K+1M) = ~3.75MB. Plus caches store them (references). Fine.

Setup time: creating these strings is fast. Fine.

OK, writing final answer.

Hmm, one last thought: should I worry that all 8 cases are "long key" and thus similar, and the harness might dedupe? No, labels are distinct.

Also, the task says "different paths through its code, sizes, data distributions". Hit vs miss is the main path difference. Sizes vary. Good enough.

Let me write it out.