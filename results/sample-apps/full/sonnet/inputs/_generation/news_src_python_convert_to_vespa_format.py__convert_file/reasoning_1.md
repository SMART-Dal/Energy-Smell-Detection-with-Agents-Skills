Let me analyze this function.

`convert_file(output, file_name, docids, click_map)`:
- checks os.path.exists(file_name); if not, prints and sys.exit(1)
- opens file, reads TSV with DictReader, fieldnames = [news_id, category, subcategory, title, abstract, url, title_entities, abstract_entities]
- For each line: if news_id in docids: continue; if len(docids) > 0: output.write(",\n"); docid = news_id; docids.add(docid)
- clicks = click_map[docid]["clicks"]; impressions = click_map[docid]["impressions"]
- build doc dict, json.dump

So input needs: a TSV file under WORKDIR, an output stream (io.StringIO), a docids set, and a click_map dict.

Note: docids is mutated - each call adds docids. Since we call the function many times, the docids set carries over. But the thunk returns the arguments. If the thunk returns the same docids set, after the first call, subsequent calls will skip everything. That would break "same work on every call". So we need fresh docids each call. But also the output stream needs to be fresh, since output is written to.

Actually the thunk returns a new set each call - but that's cheap. The output: we need a fresh output each call. Using io.StringIO() in the thunk is cheap. But if the output accumulates... each thunk call creates a new StringIO so it's fine.

Wait, but the output is only written; the function doesn't read it. So a fresh StringIO per call is fine and cheap.

The click_map: contains all docids with clicks/impressions. It's read-only, so build once at module level.

file_name: the TSV file, read-only, build once.

docids: fresh empty set per call. But wait - the function checks `if line["news_id"] in docids: continue`. With a fresh empty set, no lines skipped. Good.

Hmm but for "hit and miss ratios" we could pass a docids pre-populated. But careful: if docids is non-empty at start, the function writes ",\n" before the first written doc. That's fine.

Let me think about sizes. One call should be ~1ms-200ms. Reading a TSV with csv.DictReader and json.dump per line. Let's use a few thousand lines.

Also random: generate_random_date uses random.randint — the global random. That's fine, it's not timed-relevant (it is timed actually, it's inside the call). No seeding needed for correctness; output comparison is done on both original and modified — but if random isn't seeded, outputs differ between runs! The harness compares outputs of original and modified. If random is unseeded, the dates will differ between the two runs, causing mismatch.

Hmm. Actually the harness runs original and modified each with the same inputs, and compares outputs. The random state differs. We should seed the global random before each call... but the thunk runs before timing. Actually the thunk is where we can do setup. But random state: if the thunk calls random.seed(0), then each thunk call resets the seed. But the thunk returns args, then the call happens. So if every thunk seeds random with the same seed, each call gets the same sequence. That would make original and modified identical (assuming same number of randint calls). That's good.

But is seeding the global random allowed? It's setting state to build an input, kind of. Hmm, "No time-dependent or unseeded random behaviour." So we should seed. Let's seed inside the thunk: `random.seed(12345)`. That's setting the module's config, fine.

Actually wait — but does the harness compare outputs across original and modified? "We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their outputs." Yes. So deterministic output matters. Seed the global random in the thunk.

But note: the thunk seeds, then the function call runs and consumes random. Next thunk call seeds again. Good.

Now, generate_random_date is called once per written doc. If the modified version changes the number of randint calls... unlikely.

Let me write the module.

Setup at module level:
- Create TSV file(s) under WORKDIR.
- Build click_map.

The file format: TSV with columns news_id, category, subcategory, title, abstract, url, title_entities, abstract_entities. The function reads fields 0..5 (news_id..abstract) into doc fields, plus url? Wait include_fields = set(field_list[0:6]) = news_id, category, subcategory, title, abstract, url. Yes 6 fields including url.

title_entities and abstract_entities are not included in output but must be present in the TSV rows? Actually DictReader with fieldnames given will read all columns; if a row has fewer columns, missing keys become None. The function only accesses line[field] for include_fields. So title_entities/abstract_entities columns aren't accessed. But we can include them for realism.

click_map: dict docid -> {"clicks": int, "impressions": int}.

Let's design cases with varying:
- number of lines
- duplicate news_ids in file (so `continue` path triggered)
- pre-populated docids (hit ratio)
- different text lengths

But careful: docids must be fresh per call for same work. Pre-populated docids: we need a fresh set each thunk call with the same contents. Building a set of e.g. 500 elements per call is cheap.

Actually, to have the docids carry the same "skip" behavior each call, we build the set fresh in the thunk.

Hmm, but the output: with pre-populated docids, `len(docids) > 0` so every written doc gets preceded by ",\n". That's fine and deterministic.

Let me plan 8 cases:

1. Small-ish typical: 2000 lines, all unique, empty docids.
2. Large: 20000 lines.
3. With duplicates: file has repeated news_ids.
4. With pre-populated docids (50% hits).
5. Long text fields (large strings).
6. Many lines + duplicates + pre-populated.
7. Different distribution: short fields, many lines.
8. etc.

Let's keep the output under 100k values. Each doc is a dict with 9 fields; json output. For 20000 lines -> 20000 docs, output writes ~20000 json objects. The output is a StringIO - that's an "output" not a returned value. Hmm, "keep what it returns (and anything it writes) under about 100 000 values." The written output: 20000 json lines. Each is a JSON object. Counting values... 20000 * ~10 = 200k. Might be over. Let's keep max around 10000-15000 lines.

Actually the check is "about 100 000 values". Let's be conservative: max 8000 lines per call. 8000 * 9 fields ≈ 72k values. Hmm, borderline. Let's use up to 10000. Actually let's think: the number of "values" in the output. The output is a JSON-ish stream. Hard to say. Let's keep max lines at 10000 to be safe-ish. 10000 docs * 9 fields = 90000. OK.

Timing: 10000 lines with json.dump and csv reading — probably ~50-100ms. Fine.

Let me be careful about the file size: 10000 lines * ~200 bytes = 2MB. Fine.

Let me write helper to generate TSV content.

```python
import csv
import io
import os
import random
from pathlib import Path

from convert_to_vespa_format import convert_file

WORKDIR  # provided
```

Wait, WORKDIR is provided, do not define. But module-level code can use it.

Let me write:

```python
import io
import random
from convert_to_vespa_format import convert_file

_FIELDS = ["news_id", "category", "subcategory", "title", "abstract", "url", "title_entities", "abstract_entities"]

def _make_rows(n, seed, dup_ratio=0.0, text_len=40, categories=8):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        nid = f"N{i}"
        if rows and rng.random() < dup_ratio:
            nid = rows[rng.randrange(len(rows))][0]
        title = "t" * text_len  # hmm, uniform
        ...
```

Avoid uniformity: use random words. Let's generate words from a vocabulary.

Let me write a text generator: `" ".join(rng.choice(words) for _ in range(k))`.

Let's define a fixed vocabulary list.

Now build the TSV file per case. Each case needs its own file (different content) under WORKDIR.

```python
def _write_tsv(path, rows):
    with io.open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")
```

Rows must have 8 fields each, no tabs inside fields. Ensure text has no tabs.

click_map: for each unique news_id in the file, an entry. Build from rows.

Actually the function does `click_map[docid]["clicks"]` — KeyError if missing. So click_map must contain every docid that could be written. With duplicates, all docids present. With pre-populated docids, skipped ones need not be in click_map, but easier to include all.

Let's structure: a helper that builds everything for a case and returns a factory.

```python
def _build_case(name, rows, prepopulate=0, seed=0):
    path = WORKDIR / f"news_{name}.tsv"
    _write_tsv(path, rows)
    click_map = {}
    rng = random.Random(seed)
    for r in rows:
        click_map[r[0]] = {"clicks": rng.randint(0, 100), "impressions": rng.randint(0, 5000)}
    pre = [r[0] for r in rows[:prepopulate]]
    return path, click_map, pre
```

Then thunk:
```python
lambda: (io.StringIO(), path, set(pre), click_map)
```
And seed random inside the thunk? We need `random.seed(...)` before the call. The thunk is `lambda: (...)`. We can make a helper function:

```python
def _call(path, pre, click_map):
    random.seed(0)
    return (io.StringIO(), path, set(pre), click_map)
```

Wait but random.seed resets global. Good. Each thunk call seeds the same.

Hmm, but is resetting global random each call "same work on every call"? Yes.

But careful: the thunk runs before timing, and the function's random calls are timed. Seeding in thunk is fine.

Actually there's a subtlety: does seeding global random affect the modified version identically? The modified version presumably uses the same generate_random_date. Fine.

Now the "hits": with prepopulate, docids non-empty initially → the first written line is preceded by ",\n". Also the skipped lines aren't written.

Let me now think about what makes different work paths:
- `if line["news_id"] in docids: continue` — duplicates within file, and prepopulated.
- `if len(docids) > 0: output.write(",\n")` — triggered when docids non-empty.
- json.dump of various field sizes.

8 cases:

1. "baseline-2k": 2000 unique rows, no prepopulate.
2. "many-10k": 10000 unique rows.
3. "duplicates": 8000 rows with dup_ratio 0.5 (many repeats → lots of continue).
4. "prepopulated-half": 8000 rows, prepopulate 4000 (half skipped).
5. "long-text": 3000 rows with long titles/abstracts (text_len large).
6. "short-text-many": 12000 rows with very short text.
7. "wide-entities": rows with long title_entities/abstract_entities (though not included in output, they're parsed by csv — adds work). Actually DictReader parses all columns. Long entities add parsing work but not output. Good for diversity.
8. "all-skipped"? No, must do work. Maybe "mixed" with dup + prepopulate + varied lengths.

Let me also consider that docids passed as set - building set(pre) each call with 4000 elements is a bit of work but it's in the thunk, not timed. Fine.

But wait: "keep a thunk cheap next to one call". Building a 4000-element set each call is ~100µs, fine.

Output size: case 2 with 10000 rows → 10000 docs. Case 6 with 12000 rows → 12000 docs. Hmm, 12000*9 = 108k values. Slightly over. Let's cap at 10000.

Let me set:
1. baseline: 2000
2. large: 10000
3. duplicates: 8000 rows → maybe ~4000 unique written.
4. prepopulated: 9000 rows, 4500 prepopulated → 4500 written.
5. long-text: 3000 rows with text_len 400.
6. short-text: 10000 rows with text_len 5.
7. entities: 5000 rows with long entity strings.
8. mixed: 8000 rows with dup 0.3 and prepopulate 2000.

Timing estimate: json.dump of a doc with a few fields ~ few µs. 10000 docs ~ 50ms? Plus csv parsing. Probably 50-100ms. Good.

Now checks(): 2-3 small edge inputs.
- Empty file: file with no lines → loop does nothing. docids empty, output nothing.
- One row.
- Maybe: file not found → sys.exit(1) raises SystemExit. That's an edge case that raises. But sys.exit(1) — the harness says checks "may raise". Good. But careful: `print` and `sys.exit(1)`. Actually if the file doesn't exist, it exits. That's a valid edge check.

But hmm, sys.exit raises SystemExit which propagates. The harness compares behavior; both original and modified raise SystemExit. Fine.

Actually, is that safe? "These may raise." Yes.

Let's do checks:
- empty file
- single row
- missing file (SystemExit)

Wait, single row: with empty docids, len(docids)==0 so no ",\n". Writes one json.

Also None? Not applicable.

Now the tricky part: module-level setup. We create files at import time under WORKDIR. WORKDIR is available.

Let me be careful with the TSV: csv.DictReader with fieldnames and delimiter tab. Rows with exactly 8 columns. If a field is empty string, that's fine.

Note: if the text contains a newline, csv would break. Ensure no newlines.

Let me write text generation carefully with no tabs/newlines.

```python
_WORDS = [f"w{i}" for i in range(500)]
```
That's uniform-ish but random selection. Fine. Actually let's make varied-length words.

```python
def _text(rng, nwords):
    return " ".join(rng.choice(_WORDS) for _ in range(nwords))
```

_VOCAB with words of varying lengths.

For entities, generate JSON-ish strings like `[{"id": "x", "confidence": 0.5}]`. But it's read by csv only, not parsed. Just needs to be a string without tabs/newlines. We can make it long.

Now, one concern: the function uses `random.randint` for dates. If a case writes many docs, many randint calls. With seed reset each call, deterministic. Good.

But wait: the harness might run the function multiple times in a row per input; each thunk call re-seeds. Since each thunk returns args and then the call is timed, the sequence is: thunk1, call1, thunk2, call2, ... So each call starts from seed 0. 

But hold on — does the harness call the thunk once and reuse the args for multiple timed calls? "The call is repeated many times, and every call gets the arguments of its own thunk call". So thunk is called for each timed call. Good.

Now let me also double-check the docids mutation issue: docids is a fresh set each call, so no carryover.

The output StringIO: fresh each call.

click_map: shared, read-only.

file: read-only.

Good.

Now write the code.

```python
import io
import random

from convert_to_vespa_format import convert_file

_WORK = WORKDIR

_VOCAB = ["alpha", "beta", "gamma", ...]
```

Let me generate vocab programmatically at module level with a seeded rng.

```python
_rng = random.Random(12345)
_VOCAB = ["".join(_rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(_rng.randint(3, 12))) for _ in range(2000)]
```

Hmm, but that's module-level, fine.

Actually simpler: fixed list of a few hundred words generated.

Let me write:

```python
import io
import random

from convert_to_vespa_format import convert_file

_R = random.Random(0)
_VOCAB = ["".join(_R.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(_R.randint(3, 14)))
          for _ in range(3000)]


def _text(rng, nwords):
    return " ".join(rng.choice(_VOCAB) for _ in range(nwords))


def _entities(rng, n):
    return "[" + ",".join(
        '{"id": "%s", "confidence": %.3f}' % (rng.choice(_VOCAB), rng.random())
        for _ in range(n)
    ) + "]"


def _rows(n, seed, dup_ratio=0.0, title_words=6, abstract_words=25, n_entities=3):
    rng = random.Random(seed)
    rows = []
    seen = []
    for i in range(n):
        if seen and rng.random() < dup_ratio:
            nid = seen[rng.randrange(len(seen))]
        else:
            nid = "N%07d" % i
            seen.append(nid)
        cat = rng.choice(["sports", "business", "tech", "health", "music", "news", "travel", "food"])
        sub = rng.choice(["a", "b", "c", "d"])
        title = _text(rng, title_words)
        abstract = _text(rng, abstract_words)
        url = "https://example.com/%s" % rng.randrange(10**9)
        te = _entities(rng, n_entities)
        ae = _entities(rng, n_entities + rng.randint(0, 5))
        rows.append([nid, cat, sub, title, abstract, url, te, ae])
    return rows


def _write(path, rows):
    with io.open(str(path), "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r))
            f.write("\n")


def _click_map(rows, seed):
    rng = random.Random(seed)
    cm = {}
    for r in rows:
        cm[r[0]] = {"clicks": rng.randint(0, 200), "impressions": rng.randint(0, 20000)}
    return cm
```

Then build cases at module level:

```python
def _prepare(name, rows, prepopulate, seed):
    path = WORKDIR / ("news_%s.tsv" % name)
    _write(path, rows)
    cm = _click_map(rows, seed)
    pre = [r[0] for r in rows[:prepopulate]]
    return path, cm, pre


def _thunk(path, cm, pre):
    random.seed(987654321)
    return (io.StringIO(), str(path), set(pre), cm)
```

Wait, path as str? The function does io.open(file_name,...) and os.path.exists(file_name). pathlib.Path works with both. But `print("Reading news data from " + file_name)` — string concatenation with Path fails! `"..." + Path` raises TypeError. So file_name must be a str. Yes, use str(path).

Good catch.

Now define the 8 cases.

```python
_CASE_DEFS = []
```

Let me just inline.

```python
_b1_rows = _rows(2000, 1)
_b1 = _prepare("baseline", _b1_rows, 0, 101)
...
```

Hmm, storing rows also stores memory but that's fine. Actually we don't need to keep rows after preparing.

Let me write a function that returns the thunk.

```python
def _make(name, n, seed, dup_ratio=0.0, title_words=6, abstract_words=25,
          n_entities=3, prepopulate=0):
    rows = _rows(n, seed, dup_ratio, title_words, abstract_words, n_entities)
    path = WORKDIR / ("news_%s.tsv" % name)
    _write(path, rows)
    cm = _click_map(rows, seed + 1000)
    pre = [r[0] for r in rows[:prepopulate]]
    p = str(path)
    return lambda: (io.StringIO(), p, set(pre), cm)
```

But wait: `random.seed` needs to be called in the thunk. Add:

```python
def _make(...):
    ...
    def thunk():
        random.seed(4242)
        return (io.StringIO(), p, set(pre), cm)
    return thunk
```

Then cases() returns list of (label, thunk).

But note: the lambda/closure captures cm and pre. Each call to the thunk creates new set. Good.

Hmm, one issue: `pre` list order and set() — fine.

Also, does building the case at module level take under 10s? Generating 2000+10000+8000+9000+3000+10000+5000+8000 ≈ 55000 rows, each with abstract of 25 words → 55000*25 = 1.4M random choices. That's fine, maybe 1-2s. Writing files fine.

Memory: rows stored temporarily then freed. click_map for 10000 entries. Fine.

Let me reduce abstract_words a bit for large cases to keep it fast.

Now define the 8 cases:

1. ("baseline-2k", _make("baseline", 2000, 1))
2. ("large-10k", _make("large", 10000, 2))
3. ("duplicates", _make("dups", 8000, 3, dup_ratio=0.5))
4. ("prepopulated-half", _make("prepop", 9000, 4, prepopulate=4500))
5. ("long-text", _make("long", 3000, 5, title_words=60, abstract_words=300, n_entities=8))
6. ("short-text-10k", _make("short", 10000, 6, title_words=2, abstract_words=4, n_entities=0))
7. ("entity-heavy", _make("ents", 5000, 7, n_entities=40))
8. ("mixed", _make("mixed", 8000, 8, dup_ratio=0.3, prepopulate=2000, title_words=15, abstract_words=80))

Case 5: abstract 300 words → long lines. 3000 rows. Output docs with long abstract strings. That's a lot of characters but the value count is 3000*9 = 27000. Fine.

Case 6: 10000 rows, output 10000 docs → 90000 values. OK.

Case 7: entity strings with 40 entities each — long lines but not in output. 5000 rows.

Wait, case 7 n_entities=40, and ae has 40+randint(0,5). Each entity ~40 chars. So ~1600 chars per entity field. 5000 rows → 8MB file. Fine.

Hmm, but csv parsing of long fields adds work. Good.

Case 3 duplicates: 8000 rows with dup_ratio 0.5 → ~4000 unique written? Actually first row unique, then 50% chance dup. Roughly 4000 unique. Output 4000 docs.

Case 4: 9000 rows, prepopulate 4500 → 4500 skipped, 4500 written. Output 4500 docs.

Now the total output values per call: max 90000. OK.

Let's double check that duplicate news_ids: click_map built from rows covers all nids including duplicates. Good.

Edge: In case 3, if a duplicate nid appears, the second occurrence is skipped via `in docids`. Good.

Now checks():

```python
def checks():
    # empty file
    empty_path = WORKDIR / "news_empty.tsv"
    _write(empty_path, [])
    one_path = WORKDIR / "news_one.tsv"
    one_rows = _rows(1, 999)
    _write(one_path, one_rows)
    cm = _click_map(one_rows, 999)
    missing = str(WORKDIR / "news_missing_xyz.tsv")

    return [
        ("empty-file", lambda: (io.StringIO(), str(empty_path), set(), {})),
        ("single-row", lambda: (io.StringIO(), str(one_path), set(), cm)),
        ("missing-file", lambda: (io.StringIO(), missing, set(), {})),
    ]
```

For empty-file, click_map {} is fine since no lines.

Wait for empty file: `io.open` works, DictReader yields nothing. Good.

Missing file: os.path.exists false → print + sys.exit(1) → SystemExit. Good.

Hmm, but should I worry the harness treats SystemExit specially? "These may raise." OK.

One more consideration: the function signature is `convert_file(output, file_name, docids, click_map)`. The thunk returns positional args. Good.

Now the import: `from convert_to_vespa_format import convert_file`. The task says import as such. Since the file is at news/src/python/, presumably the harness sets up sys.path. We just do the import as instructed.

Let me also consider: the function prints stuff. That's fine (goes to stdout). Might be a lot of prints per call ("Reading news data from ..."). One print per call. Fine.

Now, is there any concern about `random.seed` in thunk affecting the file reading? No.

Actually wait, there's a subtle issue with seeding: the modified version might be compared with the original for identical outputs. If the modification changes how many times random is called (e.g., refactors), outputs would differ anyway. Not our problem.

But also: the harness compares outputs between original runs? No, between original and modified. And "runs each input many times in a row" — presumably checking determinism? If outputs differ across runs of the same function, that could be an issue. With seeding, deterministic. Good.

Let me finalize.

Actually, one thing: `random.seed(4242)` inside the thunk — but the thunk also builds `set(pre)`. Order doesn't matter.

Let me also double check `_write` with empty rows: creates empty file. Good.

Also `_entities` with n=0 returns "[]". Good.

Let me also ensure fields have no tab characters — vocabulary words are alphabetic, URLs no tabs, entity JSON no tabs. Good.

Let me write the final code.

One concern: `_rows` for case 5 with abstract_words=300 and 3000 rows = 900k random choices plus string joins. Might take a couple seconds. Fine.

Total random choices: let's estimate ~2M. Under 10s.

Let me also reduce: case 2 large 10000 rows with abstract_words 25 → 250k choices. case 6 10000 rows with 4 words. Fine.

Write it.

Actually for `_click_map`, iterating over rows and setting dict entries for duplicates repeatedly — fine.

Let me finalize the code.

```python
import io
import random

from convert_to_vespa_format import convert_file

_R = random.Random(0)
_VOCAB = [
    "".join(_R.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(_R.randint(3, 14)))
    for _ in range(3000)
]

_CATS = ["sports", "business", "technology", "health", "music", "news", "travel", "food", "science", "politics"]
_SUBS = ["a", "b", "c", "d", "e"]


def _text(rng, nwords):
    return " ".join(rng.choice(_VOCAB) for _ in range(nwords))


def _entities(rng, n):
    parts = []
    for _ in range(n):
        parts.append('{"id": "%s", "confidence": %.3f}' % (rng.choice(_VOCAB), rng.random()))
    return "[" + ", ".join(parts) + "]"


def _rows(n, seed, dup_ratio=0.0, title_words=6, abstract_words=25, n_entities=3):
    rng = random.Random(seed)
    rows = []
    unique = []
    for i in range(n):
        if unique and rng.random() < dup_ratio:
            nid = unique[rng.randrange(len(unique))]
        else:
            nid = "N%07d" % i
            unique.append(nid)
        row = [
            nid,
            rng.choice(_CATS),
            rng.choice(_SUBS),
            _text(rng, title_words),
            _text(rng, abstract_words),
            "https://example.com/%d" % rng.randrange(10 ** 9),
            _entities(rng, n_entities),
            _entities(rng, n_entities + rng.randint(0, 5)),
        ]
        rows.append(row)
    return rows


def _write(path, rows):
    with io.open(str(path), "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r))
            f.write("\n")


def _click_map(rows, seed):
    rng = random.Random(seed)
    cm = {}
    for r in rows:
        cm[r[0]] = {"clicks": rng.randint(0, 200), "impressions": rng.randint(0, 20000)}
    return cm


def _make(name, n, seed, dup_ratio=0.0, title_words=6, abstract_words=25,
          n_entities=3, prepopulate=0):
    rows = _rows(n, seed, dup_ratio, title_words, abstract_words, n_entities)
    path = str(WORKDIR / ("news_%s.tsv" % name))
    _write(path, rows)
    cm = _click_map(rows, seed + 1000)
    pre = [r[0] for r in rows[:prepopulate]]

    def thunk():
        random.seed(424242)
        return (io.StringIO(), path, set(pre), cm)

    return thunk
```

Wait — `_write` uses io.open with str path. Fine.

Now cases():

```python
def cases():
    return [
        ("baseline-2k", _make("baseline", 2000, 1)),
        ("large-10k", _make("large", 10000, 2)),
        ("duplicates", _make("dups", 8000, 3, dup_ratio=0.5)),
        ("prepopulated-half", _make("prepop", 9000, 4, prepopulate=4500)),
        ("long-text", _make("long", 3000, 5, title_words=60, abstract_words=300, n_entities=8)),
        ("short-text-10k", _make("short", 10000, 6, title_words=2, abstract_words=4, n_entities=0)),
        ("entity-heavy", _make("ents", 5000, 7, n_entities=40)),
        ("mixed", _make("mixed", 8000, 8, dup_ratio=0.3, prepopulate=2000, title_words=15, abstract_words=80)),
    ]
```

Note `_make` is called at cases() time, which is when the harness calls cases(). Is that "module-level or thunk"? The instruction says setup goes in thunk or module-level. cases() is called by the harness before timing; building data inside cases() body is effectively setup and not timed. I think that's fine — actually the example does `_rows(...)` inside lambdas in cases(), but also module-level. Hmm, in the example, `_rows(2000,4,0)` is inside the lambda (thunk), so it's built each thunk call. That's allowed but slow-ish.

To be safe, I could build everything at module level. But the harness may only call cases() once. Building in cases() body is fine since it's before timing. But is cases() called once? Probably. Actually safer to build at module level so it's definitely not timed and done once.

Hmm, but module-level code runs at import, which happens once. Let's build at module level. But then WORKDIR must be defined at import — yes it's provided.

Actually, the concern: "building all inputs under about 10 s" — module-level is fine.

But there's a subtlety: if the harness imports the module for the modified version too, module-level runs again. Fine.

I'll do module-level construction via a list of thunks built at module level. But cases() must return them. Let me define:

```python
_CASES = [ ... ]  # built at module level

def cases():
    return _CASES
```

But careful: returning the same list of thunks each time is fine.

Hmm, but the labels must be distinct. Yes.

Let me build at module level.

Actually, one risk: if cases() is called and the thunks are shared, and the harness calls cases() twice, same thunks. Fine.

I'll build at module level.

For checks, build at module level too? checks may be called; build files at module level. Let's build the check inputs at module level as well, but the thunks create fresh StringIO. The one-row click_map built at module level.

Let me write checks at module level:

```python
_EMPTY_PATH = str(WORKDIR / "news_empty.tsv")
_write(_EMPTY_PATH, [])
_ONE_ROWS = _rows(1, 999)
_ONE_PATH = str(WORKDIR / "news_one.tsv")
_write(_ONE_PATH, _ONE_ROWS)
_ONE_CM = _click_map(_ONE_ROWS, 999)
_MISSING_PATH = str(WORKDIR / "news_definitely_missing.tsv")
```

But _write takes path — pass str, io.open(str) works. Fine.

Now checks():

```python
def checks():
    return [
        ("empty-file", lambda: (io.StringIO(), _EMPTY_PATH, set(), {})),
        ("single-row", lambda: (io.StringIO(), _ONE_PATH, set(), _ONE_CM)),
        ("missing-file", lambda: (io.StringIO(), _MISSING_PATH, set(), {})),
    ]
```

Wait — for single-row, seeding random? The check compares behavior, not output equality across runs necessarily... Actually checks are "checked only for identical behaviour". If random unseeded, the date differs between original and modified runs → mismatch. Better to seed in the check thunk too.

Let me seed in check thunks:

```python
def _one_thunk():
    random.seed(1)
    return (io.StringIO(), _ONE_PATH, set(), _ONE_CM)
```

And for missing-file, no random used, but seed anyway for consistency.

Hmm, but for empty-file, no random. Fine.

Let me use a helper `_seed_thunk(args_factory)`... simpler to just define small functions.

Actually simpler: define a function `_mk(*args)` returning lambda that seeds then returns args:

```python
def _mk(args):
    def thunk():
        random.seed(7)
        return args
    return thunk
```

But args includes a fresh StringIO needed each call. For checks, each call gets same StringIO if we pass the object... Actually for checks, we want fresh StringIO too? The function writes to output. If reused, output accumulates but no error. For behavior comparison, using a fresh one is cleaner. Let's just use lambdas with io.StringIO().

OK let me finalize with explicit lambdas.

For cases, thunk creates fresh StringIO and fresh set.

Alright, writing final.

One more check: `_make` builds rows then discards. Memory OK.

Also `prepopulate` for mixed=2000 → set of 2000 built each thunk call. Fine.

Let me double check the file naming doesn't collide across the two module imports. Same names, overwritten. Fine.

Potential issue: WORKDIR might not exist? It's provided as a pathlib.Path presumably existing. I'll assume it exists. Could do WORKDIR.mkdir(exist_ok=True) but "do not define WORKDIR" — using it is fine. I'll not mkdir.

Final code.

Let me reconsider timing for the largest: 10000 rows. Reading 10000 lines with DictReader + json.dump 10000 docs. Rough estimate: DictReader ~1-2µs/row = 20ms; json.dump ~5-10µs = 100ms; plus dict building. So maybe 100-150ms. Under 200ms. Good.

Entity-heavy 5000 rows with 40 entities → long lines ~2000 chars; csv parsing maybe 5µs/row... fine.

Long-text 3000 rows with 300-word abstracts → each abstract ~1500 chars. json.dump of long strings. Fine.

OK.

Actually, let me reconsider: is 150ms too close to 200? The instruction says roughly 1ms-200ms. Fine.

Let me reduce large-10k to 8000 to be safer? Eh, 10000 should be fine. I'll keep but maybe use 9000. Let's keep 10000; if it's 200ms it's still within.

Hmm, to be safe let's use 8000 for large and short-text-10k → rename short-text-8k with 8000. Then output max 8000*9=72000 values. Safer.

Let me do:
- large: 8000
- short: 8000

Final.

Also, `_text` for short case with abstract_words=4, title_words=2.

Write it out.

One more: the `if len(docids) > 0` check — in prepopulated case, output starts with ",\n" before first doc. That's the same in both versions. Fine.

Also `docids.add(docid)` mutates the set — fresh set each call, so consistent.

Done. Write final answer.