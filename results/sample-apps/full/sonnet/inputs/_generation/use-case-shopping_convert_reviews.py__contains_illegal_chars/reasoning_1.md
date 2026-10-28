We need write inputs. Function simple dict membership checks. Need 8 measured cases substantial work? But function itself is trivial; work is only substring search on three strings. Need realistic large strings from reviews. We can make large text fields, with illegal char at various positions, reviewer_name/title small. The function's work is `in` on strings. To make 1ms-200ms, need strings large enough. Python substring search fast (~GB/s), so 1ms ~ few MB. But memory under 100MB and 8 cases each maybe large. We can make text up to maybe 5-20 MB? But arguments rendered before/after each call to see if changed — "keep each input's data under about 1 000 000 values" — strings are values? A string counts as one value? Probably okay but rendering large string might be heavy. Better moderate: text of ~1-5 MB. 1MB search ~0.1ms. To get ~1ms need ~10MB. But 8 cases * 10MB = 80MB, under 100MB. Could do varied sizes 1-8MB. Need distinct paths: illegal in reviewer_name (early return), in title, in text at start/middle/end, absent (full scan all three). Realistic review text.

We should generate with random.Random(0) fixed. Build strings in module-level code once. Thunks return dict copies? Function doesn't mutate, so can return same dict. But rendering args before/after maybe fine.

Need checks: 2-3 small edge inputs: empty fields? Function expects keys, missing key raises KeyError. Could include empty strings, illegal in name, illegal in text. These may raise but should not? "may raise" okay. But original function must run? Checks only for identical behaviour, may raise. Include missing key maybe.

Cases: exactly 8. Need realistic scale. Use random words from alphabet excluding \u001a. Generate text with random characters/words. To make search worst-case absent, full scan. Include illegal char at positions. Since function returns early, if in reviewer_name only scans small name. For diversity include:
1. illegal in reviewer_name (early)
2. illegal in title (after name)
3. illegal at start of text
4. illegal near middle of large text
5. illegal at end of large text
6. no illegal, huge text (full scan)
7. no illegal, medium text with many near-matches? The char is distinct; no near matches.
8. illegal in text with large reviewer_name? Hmm reviewer_name could be large too.

But "each case should make function do substantial and different work": use varying sizes and positions. The function is O(n) scanning. We can make text sizes 2MB, 5MB, 8MB etc. But build all under 10s. Generating random strings of 8MB with random.Random choice per char slow. Use `''.join(rng.choice(alphabet) for _ in range(n))` for 8M ~ several seconds maybe too slow. Use `rng.choices(alphabet, k=n)` returns list of chars, join; faster. Or generate by repeating random words. But avoid uniformity/patterns. Use `rng.choices` with alphabet of letters/space/punct, k=n. For 8M, memory list of 8M refs ~64MB plus string 8MB, might be high. Could build via `rng.randbytes(n)` mapping? Simpler: use `''.join(rng.choices(...))` might be okay but memory. Better generate words: `' '.join(rng.choices(WORDS, k=n_words))` where WORDS list of common words. This yields realistic review text. For 8MB, n_words ~1.3M, list of 1.3M refs ~10MB, string 8MB. Fine. But building all cases total maybe 40MB strings. Under 100MB. Time: rng.choices 1.3M ~0.1s. Good.

Need insert illegal char at position. For middle, text = base[:pos] + '\u001a' + base[pos:]. This creates new string. Fine.

Let's define helper `_review_text(n_words, seed)` returns ' '.join(rng.choices(_WORDS, k=n_words)). Use a vocabulary of realistic words. Could include punctuation? Not necessary.

Fields dict has reviewer_name, title, text. Also maybe other keys? Function only reads three. The repo passes fields with those keys plus upvotes etc. We can include extra keys? Not needed. But to be realistic include upvotes/downvotes maybe. Not used. Fine.

Need ensure no illegal char in base. Vocabulary excludes \u001a.

Sizes: 1 word ~6 chars. To get 8MB need ~1.3M words. That's a lot but okay. But "keep each input's data under about 1 000 000 values" — words maybe values? It says values, likely list elements. 1.3M words might exceed. Better keep under 1M words. 8MB with 7 chars avg ~1.1M words. Maybe use 5MB max ~700k words. That's fine. But then function time ~0.5ms, maybe below 1ms. Could use longer words or characters. We can make text by `rng.choices` over characters? Hmm.

Actually Python substring search for absent char in 5MB string is maybe 0.5ms. The requirement "roughly 1 ms to 200 ms" but not strict? We should aim at least ~1ms. Could use 10MB text but under 1M values? A string is one value. The "values" likely means elements in lists/dicts. A single string of 10MB is one value. But rendering args might output huge string? The harness renders before/after to see mutation; might be expensive but not timed. They said keep each input's data under about 1,000,000 values. A string of 10M chars is one value but could be heavy. To be safe, use text up to ~8MB. 8 cases with varying sizes: 1MB, 2MB, 4MB, 6MB, 8MB, 8MB, 6MB, 4MB total ~39MB. Good.

But generating 8MB via words: 8MB / 6 = 1.3M words, exceeding 1M. Use longer words average 10 chars: 800k words for 8MB. Vocabulary of longer words. Or generate with `rng.choices` from a list of 1000 long words. Average length maybe 8-9. 8MB ~900k words. Fine. We can set vocabulary with lengths 5-12. Average ~8.5. 8MB ~940k. Good.

Alternatively generate text with `rng.choices(_ALPHABET, k=n_chars)` but list of chars n=8M is 8M values, too many. Words better.

Let's craft vocabulary: common English words plus some longer. Use a fixed list of ~200 words. `rng.choices` with k=n_words.

Define `_make_text(n_words, seed)`.

For each case, build base text with n_words. Then insert illegal at index if needed. For absent, no insert.

Need illegal in reviewer_name: reviewer_name could be long? Realistic reviewer names short. But to make work substantial, maybe make reviewer_name 100k chars? But then early return after scanning 100k. That's small. Could make reviewer_name huge (1MB) with illegal at end to force scan. But realistic? Reviewer names aren't huge. However task says stressful inputs, diverse. We can include a case with large reviewer_name. But function checks reviewer_name first; if illegal at end, scans 1MB then returns. That's work. But real repo reviewer names are short. Still okay for stress. But "real workload kind of data this function gets" — reviews. Reviewer name short. Better keep reviewer_name small and rely on text.

Cases:
1. illegal in reviewer_name (early return) with large text but not scanned. Work small. But maybe still one of 8; they keep 4 most work. We need 8, they select 4. So include some low work cases; okay. But we want 4 substantial. We'll make at least 5 heavy.

Let's design 8:
- "illegal-name": reviewer_name contains \u001a, text 2MB (not scanned)
- "illegal-title": title contains \u001a, text 4MB (not scanned)
- "illegal-text-start": text 6MB, illegal at start (scans 0? `in` finds at start quickly)
- "illegal-text-middle": text 8MB, illegal at middle (scans 4MB)
- "illegal-text-end": text 8MB, illegal at end (scans 8MB)
- "clean-large": text 8MB no illegal, all three scanned (8MB)
- "clean-medium": text 4MB no illegal
- "clean-small": text 1MB no illegal

But note for illegal-text-end, `in` scans entire string then finds at last char. That's max work. Clean-large also scans entire text. So heavy cases: 8MB end, 8MB clean, 8MB middle, 6MB start? Start is fast. Need 4 most work: clean-large (8MB), illegal-end (8MB), illegal-middle (4MB scan), clean-medium (4MB). Good.

But generating 8MB text twice (clean-large and illegal-end) plus 8MB middle (another 8MB) total 24MB for those, plus 6MB, 4MB, 4MB, 2MB, 1MB = 41MB. Under 100MB. But we can share base text? If we generate one 8MB base and use it for multiple cases with different insertions, each insertion creates a new string. We can build base once and derive. But thunks need distinct dicts. We can build base texts at module level once per size. For same size, reuse base string. Inserting creates new string. For clean-large, use base8 directly. For illegal-end, base8[: -1] + '\u001a'? Actually insert at end: base8 + '\u001a'. That creates new 8MB string. For middle: base8[:4M] + '\u001a' + base8[4M:] creates new 8MB. So memory: base8 (8MB) + end (8MB) + middle (8MB) = 24MB. Plus base6, base4, base2, base1 ~13MB. Total ~37MB. Fine.

But building base8 with 8MB string: `' '.join(rng.choices(_WORDS, k=n_words))` creates list of n_words refs (~8MB? Actually 1M refs * 8 bytes = 8MB) plus string 8MB. During join, peak ~16MB. Fine. Time maybe 0.5s per 8MB? Let's estimate rng.choices 1M ~0.1s, join ~0.05s. Good.

Need fixed seed. Use random.Random(0) for each text? If we use same rng sequentially, fine. But for reproducibility, use `random.Random(seed)` per helper.

Let's compute n_words for target chars. We can just specify n_words. Average word length including space ~ maybe 7. So 8MB -> ~1.14M words. That's >1M values if words counted. To stay under 1M, use longer words average 10. Let's create vocabulary of longer words (e.g., 8-14 letters) to get average ~10. Then 8MB -> 800k words. Good. Use words like "extraordinary", "responsibility", etc. But realistic review text can have long words. We'll include a list of 100 words with lengths 6-14. Average maybe 9. 8MB -> 890k. Good.

Alternatively generate text by repeating random sentences? But pattern. Use rng.choices from word list.

Let's define `_WORDS = ["excellent", "wonderful", "disappointing", ...]` maybe 50 words. Average length ~9. 8MB / 10 = 800k words. Good.

We can also add punctuation to words? Not necessary.

Let's write helper:

```python
_WORDS = [
    "excellent", "wonderful", "disappointing", "recommend", "purchase",
    "quality", "delivery", "customer", "service", "product",
    "experience", "fantastic", "terrible", "average", "satisfied",
    "refund", "shipping", "packaging", "description", "material",
    "comfortable", "beautiful", "expensive", "worthwhile", "unfortunately",
    "absolutely", "completely", "different", "expectation", "recommended",
    "improvement", "considering", "nevertheless", "understanding", "particularly",
]
```
Average length maybe 9.5. 8MB -> 800k. Good.

`_make_text(n_words, seed)`:
```python
def _make_text(n_words, seed):
    rng = random.Random(seed)
    return " ".join(rng.choices(_WORDS, k=n_words))
```

We need base texts. Use module-level:
```python
_BASE_8M = _make_text(800_000, 1)  # ~8MB
_BASE_6M = _make_text(600_000, 2)
_BASE_4M = _make_text(400_000, 3)
_BASE_2M = _make_text(200_000, 4)
_BASE_1M = _make_text(100_000, 5)
```
But actual size depends on word lengths. 800k * ~10 = 8MB. Good.

Now build cases. Need dicts. For each case, create dict with reviewer_name, title, text. Use small reviewer_name/title except illegal-name/title.

```python
def _fields(text, reviewer_name="John Doe", title="A review"):
    return {"reviewer_name": reviewer_name, "title": title, "text": text}
```

For illegal-name: reviewer_name = "John\u001aDoe", text=_BASE_2M.
For illegal-title: title = "Great\u001aproduct", text=_BASE_4M.
For illegal-text-start: text = "\u001a" + _BASE_6M
For illegal-text-middle: mid = len(_BASE_8M)//2; text = _BASE_8M[:mid] + "\u001a" + _BASE_8M[mid:]
For illegal-text-end: text = _BASE_8M + "\u001a"
For clean-large: text = _BASE_8M
For clean-medium: text = _BASE_4M
For clean-small: text = _BASE_1M

But note for illegal-text-middle, the `in` search scans from start to mid. For illegal-text-end, scans entire. For clean-large, scans entire. For clean-medium, scans entire 4MB. These are heavy.

Thunks return `(fields_dict,)`. Function doesn't mutate, so same dict can be reused. But to be safe, return dict copy? Copying dict is cheap but strings shared. The function only reads. No need. However harness renders args before/after; same dict fine. We can return the same dict each thunk call. But if function doesn't mutate, okay. It doesn't. So use module-level dicts.

But wait: "Anything the function changes outside its arguments carries over... if it caches..." It doesn't. Fine.

Checks: 2-3 small edge inputs:
- empty strings: `{"reviewer_name": "", "title": "", "text": ""}` -> False
- illegal in name: `{"reviewer_name": "\u001a", "title": "", "text": ""}` -> True
- missing key: `{"reviewer_name": "", "title": ""}` -> KeyError. This may raise. They said may raise. But maybe better not to include missing key? It's an odd type edge. Could include `None`? `None in fields["reviewer_name"]` would TypeError. But fields must be dict. We can include a case with missing key to test error behavior. It's allowed. But "Every case must run to completion on the original function without raising" applies to cases(), not checks(). Checks may raise. So include missing key.

Need import `from convert_reviews import contains_illegal_chars` exactly? The task says import as `from convert_reviews import contains_illegal_chars`. We should do that. The module is in `use-case-shopping/convert_reviews.py`. But our code runs in some environment where that module is importable? The task says import exactly as shown. So use `from convert_reviews import contains_illegal_chars`. But we don't actually call the function; we just need to import? The harness will use the function. The example imports module. We should import to ensure module loaded. But we don't need to reference it. However the instructions say import the repository's modules exactly as shown. So include `from convert_reviews import contains_illegal_chars`. It may be unused but fine.

Need ensure no `WORKDIR` usage since no files.

Let's write code. Use `random` module. Module-level generation might take some time but under 10s. Let's estimate: 800k choices * 5 bases = 2.1M choices total. rng.choices is fast. Join 2.1M words ~ maybe 0.5s. Good.

But memory: base8 8MB, base6 6MB, base4 4MB, base2 2MB, base1 1MB = 21MB. Derived strings: middle 8MB, end 8MB, start 6MB = 22MB. Total ~43MB. Plus lists during generation freed. Good.

We need be careful with `_BASE_8M` etc. at module level. The harness may import our module multiple times? No.

Let's produce final answer with code block only.

Double-check function: `contains_illegal_chars(fields)` checks `"\u001a" in fields["reviewer_name"]`, etc. Our dicts have keys. Good.

One subtlety: For illegal-text-middle, if `_BASE_8M` length is L, mid = L//2. Inserting char at mid. The `in` search for `\u001a` will scan from start to mid. Good.

For illegal-text-end, text = _BASE_8M + "\u001a". `in` scans entire base then finds at last char. Good.

For clean-large, text = _BASE_8M. `in` scans entire, returns False. Then title and reviewer_name small. So full scan.

For clean-medium, 4MB full scan.

For illegal-text-start, `in` finds at index 0 immediately. So work small. But still one of 8.

We need exactly 8 measured inputs. Yes.

Let's write checks:

```python
def checks():
    return [
        ("empty", lambda: ({"reviewer_name": "", "title": "", "text": ""},)),
        ("illegal-name", lambda: ({"reviewer_name": "\u001a", "title": "", "text": ""},)),
        ("missing-key", lambda: ({"reviewer_name": "", "title": ""},)),
    ]
```

Missing key will raise KeyError on original. That's fine for checks.

Now cases:

```python
def cases():
    return [
        ("illegal-name", lambda: ({"reviewer_name": "John\u001aDoe", "title": "A review", "text": _BASE_2M},)),
        ("illegal-title", lambda: ({"reviewer_name": "John Doe", "title": "Great\u001aproduct", "text": _BASE_4M},)),
        ("illegal-text-start", lambda: ({"reviewer_name": "John Doe", "title": "A review", "text": "\u001a" + _BASE_6M},)),
        ("illegal-text-middle", lambda: ({"reviewer_name": "John Doe", "title": "A review", "text": _TEXT_MIDDLE},)),
        ("illegal-text-end", lambda: ({"reviewer_name": "John Doe", "title": "A review", "text": _TEXT_END},)),
        ("clean-large", lambda: ({"reviewer_name": "John Doe", "title": "A review", "text": _BASE_8M},)),
        ("clean-medium", lambda: ({"reviewer_name": "John Doe", "title": "A review", "text": _BASE_4M},)),
        ("clean-small", lambda: ({"reviewer_name": "John Doe", "title": "A review", "text": _BASE_1M},)),
    ]
```

But we should build `_TEXT_MIDDLE` and `_TEXT_END` at module level to avoid rebuilding each thunk call. Yes.

```python
_MID = len(_BASE_8M) // 2
_TEXT_MIDDLE = _BASE_8M[:_MID] + "\u001a" + _BASE_8M[_MID:]
_TEXT_END = _BASE_8M + "\u001a"
```

Also `_TEXT_START` maybe `"\u001a" + _BASE_6M` can be built in thunk? It's cheap (concatenation 6MB) but repeated each call? Thunk runs before timing, so not timed. But building 6MB string each thunk call is expensive (but not timed). However it might be called many times? The harness runs each thunk many times? "each input many times in a row" - thunks run before each timing? Actually they run thunks to get args, then time call. They may call thunk many times. So thunk should be cheap. Building 6MB string each thunk call is wasteful. Better build once at module level and return it. So define `_TEXT_START = "\u001a" + _BASE_6M` at module level. Similarly all text variants module-level.

Also dicts: create module-level dicts? But if function doesn't mutate, can reuse same dict. But to be safe if harness checks mutation, it compares before/after; same dict unchanged. So we can create module-level dicts and thunks return them. That's cheapest. But note: if the function mutated the dict, it would carry over. It doesn't. So fine.

Let's create `_CASE_FIELDS` list? Simpler: define dicts at module level.

```python
_F_ILLEGAL_NAME = {"reviewer_name": "John\u001aDoe", "title": "A review", "text": _BASE_2M}
...
```

Then thunks `lambda: (_F_ILLEGAL_NAME,)`.

But careful: if the function mutated the dict, subsequent calls would see mutation. It doesn't. Good.

Let's write final code.

Need to ensure `_BASE_8M` etc. are generated with fixed seed. Use `random.Random(seed)` inside `_make_text`. The module-level `random` imported. Good.

Potential issue: `rng.choices(_WORDS, k=n_words)` returns list of strings, `" ".join` works. Good.

Let's output.