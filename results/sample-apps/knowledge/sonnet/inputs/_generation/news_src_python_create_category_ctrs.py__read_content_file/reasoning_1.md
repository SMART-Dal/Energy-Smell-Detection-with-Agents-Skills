We need to write cases for `read_content_file(file_name, news_map)`. It reads a TSV file with 8 columns: news_id, category, subcategory, title, abstract, url, title_entities, abstract_entities. It populates news_map with news_id -> category.

Note: if file doesn't exist, it calls sys.exit(1) — that would raise SystemExit. For checks, we can include a missing file case which raises (allowed for checks).

Important: news_map is mutated (adds entries). So each thunk call must get a fresh dict, and the file must be re-read. The file is read each time, so file contents stay the same. But news_map accumulates — so we need a fresh dict per thunk call. Use `lambda: (_FILE, {})` — building a fresh dict each call is cheap.

Wait: but the function is timed; the dict creation happens in the thunk (before timing). Good.

File must be created under WORKDIR. Build files at module level.

Need realistic scale: the news dataset (Microsoft MIND) has ~65k train news and ~65k dev news. Each line has 8 tab-separated fields. Let's create files with varying sizes: e.g., 50k lines, 100k lines, etc. Need one call ~1ms-200ms. Reading a 50k-line TSV with csv.DictReader... each line ~200 bytes, 50k lines = ~10MB. That's maybe 100-200ms. Let's be careful. Let's do sizes: 5k, 20k, 50k, 100k lines. 100k lines maybe 300ms? Hmm. Let's estimate: csv.DictReader parsing ~ maybe 1-2 µs per line? Actually Python csv reading with DictReader is maybe 3-5 µs per line for 8 fields. 50k lines → ~200ms. That's borderline. Let's keep max around 50k lines and use varied content.

Actually let's be safe: 2k, 5k, 10k, 20k, 30k, 50k. We have 8 cases. Let's design diverse cases:

1. small typical file (2k lines)
2. medium (10k)
3. large (50k) with realistic MIND-like data
4. file with duplicate news_ids (later overwrite earlier) — common
5. file with empty category values / missing fields
6. file with long titles/abstracts (large text fields)
7. file with unicode / non-ASCII characters
8. file with many distinct categories

Also, since news_map accumulates across calls in the repository (both train and dev go into the same map), but here each call gets a fresh dict. That's fine.

Also note: the function prints. Printing to stdout many times (one print per call) — only 2 prints per call, fine.

Important: `os.path.exists(file_name)` — file exists.

Let's build generators.

Field list: news_id, category, subcategory, title, abstract, url, title_entities, abstract_entities. Title_entities and abstract_entities are JSON strings in MIND. We can just use simple JSON strings or empty.

For realism, category is like "news", subcategory like "sports". Actually MIND categories: "news", "sports", "finance", "lifestyle", "health", "travel", "foodanddrink", "entertainment", "autos", "video", "music", "weather", "movies", "middleeast", "northamerica", "tv". Let's use a set.

Let's write a helper to generate a file:

```python
def _write_news_file(path, n, seed, categories=None, max_text=..., unicode_frac=0.0, dup_frac=0.0):
    rng = random.Random(seed)
    ...
```

We should keep files under WORKDIR. Total data under 100MB. 50k lines * 300 bytes = 15MB. Fine.

Let's be careful about total build time under 10s. Writing ~150k lines total should be fast.

Let me write the code.

```python
import random
import json
import os
from create_category_ctrs import read_content_file

WORKDIR  # provided

_CATEGORIES = ["news", "sports", "finance", "lifestyle", "health", "travel",
               "foodanddrink", "entertainment", "autos", "video", "music",
               "weather", "movies", "middleeast", "northamerica", "tv"]

def _write_news_file(path, n, seed, *, n_categories=16, max_words=12,
                     unicode_frac=0.0, dup_frac=0.0, empty_frac=0.0):
    rng = random.Random(seed)
    cats = _CATEGORIES[:n_categories]
    lines = []
    for i in range(n):
        if dup_frac and rng.random() < dup_frac:
            news_id = "N{}".format(rng.randrange(max(1, i)))
        else:
            news_id = "N{}".format(i)
        cat = rng.choice(cats)
        sub = rng.choice(cats)
        if empty_frac and rng.random() < empty_frac:
            cat = ""
        title = _text(rng, max_words, unicode_frac)
        abstract = _text(rng, max_words * 2, unicode_frac)
        url = "https://example.com/{}".format(news_id)
        te = "[]"
        ae = "[]"
        lines.append("\t".join([news_id, cat, sub, title, abstract, url, te, ae]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

Wait, need `_text` helper. Let me define words.

Actually, let's simplify: use a word pool.

```python
_WORDS = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "news",
          "report", "market", "team", "win", "game", "season", "player", "city",
          "government", "election", "health", "study", "research", "company",
          "stock", "price", "travel", "hotel", "food", "recipe", "music", "film",
          "actor", "weather", "storm", "rain", "snow", "sun", "cloud", "video"]

_UNI = ["café", "naïve", "北京", "東京", "München", "Αθήνα", "Москва", "emoji😀"]
```

`_text(rng, n, unicode_frac)` returns " ".join of n words, where with probability unicode_frac each word is from _UNI.

Now build files at module level:

```python
_FILES = {}

def _build():
    d = WORKDIR
    _write_news_file(d / "news_small.tsv", 2_000, 0)
    ...
```

But careful: WORKDIR is defined by the harness. It's a pathlib.Path. Fine.

We need 8 cases. Let's design:

1. "typical-2k": 2,000 lines, standard.
2. "medium-10k": 10,000 lines.
3. "large-50k": 50,000 lines.
4. "duplicates": 20,000 lines with 50% duplicate news_ids.
5. "unicode": 10,000 lines with unicode_frac=0.5.
6. "long-text": 5,000 lines with max_words=200 (long titles/abstracts) — this makes each line big.
7. "empty-fields": 15,000 lines with empty_frac=0.3 (empty category).
8. "many-categories": 20,000 lines with n_categories=16 — actually all use 16. Hmm, maybe make one with 2 categories and one with 16? The category value is just a string, doesn't affect work much. Let's instead vary: one file with a single category, one with many. Or use different subcategory distributions.

Actually the work is dominated by parsing lines and dict insertion. Diversity in content matters less, but we should still vary sizes and structures. Let's also include a case with very long news_id? Not needed.

Let me reconsider: the "work" is reading and parsing. The 4 kept are the ones doing most work — likely the largest files. That's fine.

Let's make sure each case is distinct enough.

Cases:
1. "typical-2k" — 2k lines, standard, 16 cats.
2. "medium-10k" — 10k lines.
3. "large-50k" — 50k lines.
4. "duplicates-20k" — 20k lines, 50% dup ids.
5. "unicode-10k" — 10k lines, unicode_frac=0.6.
6. "long-text-5k" — 5k lines, max_words=150.
7. "empty-cat-15k" — 15k lines, empty_frac=0.35.
8. "wide-cats-25k" — 25k lines with 16 categories and random subcategory.

Hmm, but 50k lines might exceed 200ms? Let's estimate more carefully. csv.DictReader: for each row it creates a dict with 8 keys. That's maybe ~2-3 µs per row minimum in CPython... Actually let's benchmark mentally: reading a 10MB CSV with DictReader in Python takes roughly 0.5-1 second. Hmm, that's concerning. Let me think.

Typical CSV read speed in Python: `csv.reader` can do ~1M rows/sec for simple rows? Actually more like 200k-500k rows/sec for simple rows of a few fields. With DictReader (creates dict per row), maybe 100k-200k rows/sec. So 50k rows → 0.25-0.5s. That's over the 200ms limit.

Hmm. Let's be more conservative: max 20k lines? 20k rows → ~0.1-0.2s. Still borderline.

Let me think about actual numbers. A quick reference: reading a 100k-line CSV with csv.DictReader takes about 0.3-0.5s in CPython. So 50k → 0.15-0.25s. 20k → 0.06-0.1s.

Also the line length matters — the parsing of fields with quotes etc. Our fields are simple (no quotes, no commas since tab-delimited). So parsing is fast.

Actually since delimiter is tab, and fields are simple, csv module should be fast. Let's estimate ~1.5 µs per row → 50k rows = 75ms. Plus dict insertion. Probably fine.

I'll go with max 50k lines but keep line content moderate (short text). Actually long-text case with 5k lines and 150 words per title/abstract... each line ~2KB, 5k lines = 10MB. The csv parsing of long fields is more expensive. 5k rows with 2KB each... maybe 50-100ms. Fine.

Let's also consider: the function prints "Reading news data from ..." and that's it. Two prints per call.

Now, the news_map dict: after each call it has up to n entries. That's fine, under 100k values. For 50k lines, 50k entries. Output compared in full — 50k values. Hmm, "keep what it returns (and anything it writes) under about 100 000 values". The dict has 50k entries — that's under 100k. But the comparison is on the dict. 50k entries might be heavy for comparison but should be OK. Actually the return value is None (function returns None). But the arguments are rendered before and after each call to see whether it changed them — so the news_map dict (50k entries) gets rendered. That's 1M value limit for arguments. 50k entries * 2 (key+value) = 100k values. Under 1M. OK.

But rendering a 50k-entry dict each call, many times... that's outside timing though. Fine.

Hmm, but maybe reduce to be safe. Let's use max 40k.

Actually let's just be reasonable: sizes 2k, 8k, 20k, 40k, 15k, 12k, 25k, 5k. Total build ~127k lines.

Let me reconsider the "one call takes roughly 1 ms to 200 ms". 2k lines might be ~3-5ms. Good.

Now checks():
- missing file → sys.exit(1) raises SystemExit. Allowed (checks may raise).
- empty file (0 lines) → news_map stays empty.
- file with only header? No header since fieldnames given. A file with one line where category is empty.
- Maybe a file with a line missing some fields (fewer tabs) → csv.DictReader fills with None. Actually with fieldnames and a row with fewer fields, the missing values are None. Then `line["category"]` would be None → news_map[news_id] = None. That works.

Let's do checks:
1. "missing-file" → (path that doesn't exist, {}). Raises SystemExit.
2. "empty-file" → (empty file, {}). Returns None, news_map empty.
3. "blank-category" → (file with one line with empty category, {}).

Wait, but the empty file: csv.DictReader over empty file yields no rows. Fine.

Careful: for the missing file, the function calls sys.exit(1) which raises SystemExit. The harness compares behaviour between original and modified — both would raise SystemExit. Fine.

But note: sys.exit also prints to stderr. Fine.

Now, one issue: files are created at module level. But the checks' "missing file" path must not exist. Use WORKDIR / "does_not_exist.tsv".

Now, the thunks: `lambda: (str(_FILE), {})`. The function takes file_name as string. os.path.exists accepts Path too, but let's pass str.

Actually, io.open with a Path works fine. But let's pass str for safety.

Each thunk call builds a fresh dict. Good — no accumulation.

Wait: but building a fresh dict each call means the function does the same work each time. Yes.

But there's a subtlety: the file is read from disk each call. Disk caching makes it fast. Fine.

Let me now write the code.

```python
import random
import json
import os
from create_category_ctrs import read_content_file

_CATEGORIES = ["news", "sports", "finance", "lifestyle", "health", "travel",
               "foodanddrink", "entertainment", "autos", "video", "music",
               "weather", "movies", "middleeast", "northamerica", "tv"]

_WORDS = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
          "report", "market", "team", "win", "game", "season", "player",
          "city", "government", "election", "health", "study", "research",
          "company", "stock", "price", "travel", "hotel", "food", "recipe",
          "music", "film", "actor", "weather", "storm", "rain", "snow",
          "sun", "cloud", "video", "news", "world", "local", "state"]

_UNI = ["café", "naïve", "北京", "東京", "München", "Αθήνα", "Москва", "emoji😀", "São"]


def _text(rng, n_words, unicode_frac):
    parts = []
    for _ in range(n_words):
        if unicode_frac and rng.random() < unicode_frac:
            parts.append(rng.choice(_UNI))
        else:
            parts.append(rng.choice(_WORDS))
    return " ".join(parts)


def _write_news_file(path, n, seed, *, n_categories=16, max_words=12,
                     unicode_frac=0.0, dup_frac=0.0, empty_cat_frac=0.0):
    rng = random.Random(seed)
    cats = _CATEGORIES[:n_categories]
    out = []
    for i in range(n):
        if dup_frac and i > 0 and rng.random() < dup_frac:
            news_id = "N{}".format(rng.randrange(i))
        else:
            news_id = "N{}".format(i)
        cat = rng.choice(cats)
        sub = rng.choice(cats)
        if empty_cat_frac and rng.random() < empty_cat_frac:
            cat = ""
        title = _text(rng, max(1, int(max_words * rng.uniform(0.5, 1.5))), unicode_frac)
        abstract = _text(rng, max(1, int(max_words * 2 * rng.uniform(0.5, 1.5))), unicode_frac)
        url = "https://example.com/{}/{}".format(cat or "x", news_id)
        out.append("\t".join([news_id, cat, sub, title, abstract, url, "[]", "[]"]))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
```

Now build files:

```python
_F_TYPICAL = WORKDIR / "news_typical.tsv"
_F_MEDIUM = WORKDIR / "news_medium.tsv"
_F_LARGE = WORKDIR / "news_large.tsv"
_F_DUP = WORKDIR / "news_dup.tsv"
_F_UNI = WORKDIR / "news_uni.tsv"
_F_LONG = WORKDIR / "news_long.tsv"
_F_EMPTY = WORKDIR / "news_empty_cat.tsv"
_F_WIDE = WORKDIR / "news_wide.tsv"
_F_ONE = WORKDIR / "news_one.tsv"
_F_BLANK = WORKDIR / "news_blank.tsv"
_F_EMPTYFILE = WORKDIR / "news_empty_file.tsv"

_write_news_file(_F_TYPICAL, 2_000, 0)
_write_news_file(_F_MEDIUM, 8_000, 1)
_write_news_file(_F_LARGE, 40_000, 2)
_write_news_file(_F_DUP, 20_000, 3, dup_frac=0.5)
_write_news_file(_F_UNI, 12_000, 4, unicode_frac=0.6)
_write_news_file(_F_LONG, 5_000, 5, max_words=150)
_write_news_file(_F_EMPTY, 15_000, 6, empty_cat_frac=0.35)
_write_news_file(_F_WIDE, 25_000, 7, n_categories=16)
_write_news_file(_F_ONE, 1, 8, n_categories=1)
_write_news_file(_F_BLANK, 1, 9, empty_cat_frac=1.0)
_F_EMPTYFILE.write_text("", encoding="utf-8")
```

Wait, empty_cat_frac=1.0 with n=1 → cat = "". Good.

Hmm, for _F_BLANK, the check: category is empty string "". news_map["N0"] = "". Fine.

Now the cases:

```python
def cases():
    return [
        ("typical-2k",   lambda: (str(_F_TYPICAL), {})),
        ("medium-8k",    lambda: (str(_F_MEDIUM), {})),
        ("large-40k",    lambda: (str(_F_LARGE), {})),
        ("duplicates-20k", lambda: (str(_F_DUP), {})),
        ("unicode-12k",  lambda: (str(_F_UNI), {})),
        ("long-text-5k", lambda: (str(_F_LONG), {})),
        ("empty-cat-15k", lambda: (str(_F_EMPTY), {})),
        ("wide-25k",     lambda: (str(_F_WIDE), {})),
    ]
```

That's 8.

checks:

```python
def checks():
    return [
        ("missing-file", lambda: (str(WORKDIR / "nope.tsv"), {})),
        ("empty-file",   lambda: (str(_F_EMPTYFILE), {})),
        ("blank-category", lambda: (str(_F_BLANK), {})),
    ]
```

Wait — the missing file check raises SystemExit. The harness compares behaviour; both original and modified raise. OK.

Hmm, but does the harness accept a check that raises? "These may raise." Yes.

One concern: building files at module level takes time. 128k lines total with text generation. Each line generates ~36 words. That's ~4.6M random choices. Should take a few seconds in Python. Let's estimate: rng.choice per word ~0.3µs? Actually more like 0.5µs. 4.6M * 0.5µs = 2.3s. Plus writing. Should be under 10s. But the long-text case: 5000 lines * (150*1.5 + 300*1.5) ≈ 5000 * 675 = 3.4M words. Hmm, that's a lot. Let me reduce max_words for long-text to 80. Then 5000 * (80*1.5 + 160*1.5) = 5000*360 = 1.8M words. Still significant but OK.

Actually, let me reduce the per-word generation cost by using a simpler approach: generate a word list once and sample. But rng.choice is fine.

Let me reduce overall: total words across all files. Let's compute roughly:
- typical 2k * 36 = 72k
- medium 8k * 36 = 288k
- large 40k * 36 = 1.44M
- dup 20k * 36 = 720k
- uni 12k * 36 = 432k
- long 5k * 360 = 1.8M
- empty 15k * 36 = 540k
- wide 25k * 36 = 900k
Total ≈ 6.2M words. At ~0.4µs each → 2.5s. Plus string join and file writing. Probably ~4-5s total. Acceptable but close. Let's trim: reduce large to 30k, wide to 20k, uni to 10k, empty to 12k, dup to 15k.

New totals:
- typical 2k*36=72k
- medium 8k*36=288k
- large 30k*36=1.08M
- dup 15k*36=540k
- uni 10k*36=360k
- long 5k*360=1.8M (reduce max_words to 80 → 5k*180=900k)
- empty 12k*36=432k
- wide 20k*36=720k
Total ≈ 4.4M words → ~2s. Good.

Let me set long-text max_words=80.

Also, file sizes: large 30k lines * ~250 bytes = 7.5MB. Fine.

Now, timing per call: 30k lines. If ~1.5µs/row → 45ms. Good, within range.

Actually let me reconsider whether 40k would be too slow. 30k is safer.

Let me also double check: the function uses `io.open(file_name, "r", encoding="utf-8")`. Our files are written with encoding utf-8. Good.

Now about the news_map being fresh: `{}` literal in the lambda creates a new dict each call. Good.

One more thing: the function prints. That's fine.

Let me also make sure `json` import isn't needed — I imported json but don't use it. Remove.

Also `os` not needed. Remove.

Final code:

```python
import random

from create_category_ctrs import read_content_file
```

Wait, do we need to import the function? The harness imports it? The task says "Import it as `from create_category_ctrs import read_content_file`." So we should include that import. Yes.

Let me write final.

Actually, one concern about `_text` with `int(max_words * rng.uniform(0.5, 1.5))` — for max_words=12, this gives 6-18 words. Fine.

Also for the unicode case, the file is written with encoding utf-8. Good.

Let me also make sure that the news_id in dup case: `rng.randrange(i)` where i>0. Good.

Now, potential issue: the function's `news_map` argument is rendered before and after. For the large case, 30k entries. Fine.

Another consideration: the harness keeps all 8 cases' data in memory. Total lines ~112k, each with ~36 words. That's ~4M words in memory as strings? No — the files are on disk; the thunks only hold the file path and an empty dict. So memory is fine. The files on disk total maybe 30MB.

Wait, but the harness says "keep the data in memory under about 100 MB" — files on disk are fine.

Hmm, but actually there's a subtlety: the thunk returns `(str(_F), {})`. The dict is empty. The function fills it. After the call, the dict has 30k entries. That's the argument. Fine.

Let me write it out.

One more: should I worry that `read_content_file` might be called with a Path? No, str is fine.

Let me finalize.

Actually, let me reconsider the "long-text" case. With max_words=80, title ~40-120 words, abstract ~80-240 words. Each line ~1-2KB. 5k lines = 5-10MB. Parsing 5k rows with large fields. The csv module handles it. Time maybe 30-60ms. Good.

Also for diversity, maybe make one case have a very small number of categories (2) to create many duplicate category values. But that doesn't change work. It's fine.

Let me also add a case with no duplicates but with ids that are long strings? Not needed.

Final answer.

Let me write the code carefully.

```python
import random

from create_category_ctrs import read_content_file

_CATEGORIES = [
    "news", "sports", "finance", "lifestyle", "health", "travel",
    "foodanddrink", "entertainment", "autos", "video", "music",
    "weather", "movies", "middleeast", "northamerica", "tv",
]

_WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
    "report", "market", "team", "win", "game", "season", "player",
    "city", "government", "election", "health", "study", "research",
    "company", "stock", "price", "travel", "hotel", "food", "recipe",
    "music", "film", "actor", "weather", "storm", "rain", "snow",
    "sun", "cloud", "video", "news", "world", "local", "state",
]

_UNI = ["café", "naïve", "北京", "東京", "München", "Αθήνα", "Москва", "emoji😀", "São"]


def _text(rng, n_words, unicode_frac):
    parts = []
    for _ in range(n_words):
        if unicode_frac and rng.random() < unicode_frac:
            parts.append(rng.choice(_UNI))
        else:
            parts.append(rng.choice(_WORDS))
    return " ".join(parts)


def _write_news_file(path, n, seed, *, n_categories=16, max_words=12,
                     unicode_frac=0.0, dup_frac=0.0, empty_cat_frac=0.0):
    rng = random.Random(seed)
    cats = _CATEGORIES[:n_categories]
    out = []
    for i in range(n):
        if dup_frac and i > 0 and rng.random() < dup_frac:
            news_id = "N{}".format(rng.randrange(i))
        else:
            news_id = "N{}".format(i)
        cat = rng.choice(cats)
        sub = rng.choice(cats)
        if empty_cat_frac and rng.random() < empty_cat_frac:
            cat = ""
        title = _text(rng, max(1, int(max_words * rng.uniform(0.5, 1.5))), unicode_frac)
        abstract = _text(rng, max(1, int(max_words * 2 * rng.uniform(0.5, 1.5))), unicode_frac)
        url = "https://example.com/{}/{}".format(cat or "x", news_id)
        out.append("\t".join([news_id, cat, sub, title, abstract, url, "[]", "[]"]))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


_F_TYPICAL = WORKDIR / "news_typical.tsv"
_F_MEDIUM = WORKDIR / "news_medium.tsv"
_F_LARGE = WORKDIR / "news_large.tsv"
_F_DUP = WORKDIR / "news_dup.tsv"
_F_UNI = WORKDIR / "news_uni.tsv"
_F_LONG = WORKDIR / "news_long.tsv"
_F_EMPTY = WORKDIR / "news_empty_cat.tsv"
_F_WIDE = WORKDIR / "news_wide.tsv"
_F_BLANK = WORKDIR / "news_blank_cat.tsv"
_F_EMPTYFILE = WORKDIR / "news_empty_file.tsv"

_write_news_file(_F_TYPICAL, 2_000, 0)
_write_news_file(_F_MEDIUM, 8_000, 1)
_write_news_file(_F_LARGE, 30_000, 2)
_write_news_file(_F_DUP, 15_000, 3, dup_frac=0.5)
_write_news_file(_F_UNI, 10_000, 4, unicode_frac=0.6)
_write_news_file(_F_LONG, 5_000, 5, max_words=80)
_write_news_file(_F_EMPTY, 12_000, 6, empty_cat_frac=0.35)
_write_news_file(_F_WIDE, 20_000, 7, n_categories=16)
_write_news_file(_F_BLANK, 1, 8, empty_cat_frac=1.0)
_F_EMPTYFILE.write_text("", encoding="utf-8")


def checks():
    return [
        ("missing-file", lambda: (str(WORKDIR / "does_not_exist.tsv"), {})),
        ("empty-file", lambda: (str(_F_EMPTYFILE), {})),
        ("blank-category", lambda: (str(_F_BLANK), {})),
    ]


def cases():
    return [
        ("typical-2k", lambda: (str(_F_TYPICAL), {})),
        ("medium-8k", lambda: (str(_F_MEDIUM), {})),
        ("large-30k", lambda: (str(_F_LARGE), {})),
        ("duplicates-15k", lambda: (str(_F_DUP), {})),
        ("unicode-10k", lambda: (str(_F_UNI), {})),
        ("long-text-5k", lambda: (str(_F_LONG), {})),
        ("empty-cat-12k", lambda: (str(_F_EMPTY), {})),
        ("wide-20k", lambda: (str(_F_WIDE), {})),
    ]
```

Wait, `_F_WIDE` with n_categories=16 is the same as default. Let me make it distinct: maybe n_categories=2 for a "narrow" case, or use different structure. Actually, let's make _F_WIDE use n_categories=16 but with a different seed and size. It's fine, but let's differentiate more: make it have very long news_ids? Or make it have no subcategory variety. Hmm.

Actually, let's make the last case "single-category" with n_categories=1 and larger size (25k). That creates a file where all categories are the same — realistic for a small dataset. But the work is the same.

Alternatively, make one case with a huge number of distinct news_ids and short lines (minimal text) to stress dict insertion. Let's do max_words=2 for that one, 25k lines. That's a "minimal-text" case. Hmm.

Let me just keep _F_WIDE as 20k with 16 categories, and it's fine. The diversity across cases is already good.

Actually, to make the last case more distinct, let's use max_words=3 (very short). Rename to "short-text-20k". That stresses the dict insertion relative to parsing.

Let me do that: `_write_news_file(_F_WIDE, 20_000, 7, max_words=3)`.

Hmm but then it's similar to typical. Whatever. Let's keep it.

Actually, let me reconsider: the "4 that do the most work" are kept. So the large ones matter. Fine.

One more thought: should the empty-file check be a case? No, it's in checks.

I think this is good. Let me also double check the `_write_news_file` for `_F_BLANK` with n=1, empty_cat_frac=1.0: rng.random() < 1.0 is always True (random() returns [0,1)), so cat = "". Good.

And for _F_EMPTY, empty_cat_frac=0.35.

Now, potential issue: the function's `print` statements. With many calls, lots of output. But the harness presumably captures it. Fine.

I'm confident. Write final.

Actually, one thing: `WORKDIR` is provided. We use it at module level. Good.

Also, the thunks return `(str(_F_TYPICAL), {})`. The function signature is `read_content_file(file_name, news_map)`. Positional args. Good.

Final answer.