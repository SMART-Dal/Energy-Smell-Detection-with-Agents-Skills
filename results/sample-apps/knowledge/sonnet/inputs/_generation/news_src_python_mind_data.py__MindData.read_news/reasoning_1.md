Let me think about this carefully.

The function `read_news(self, news_file)` reads a tab-separated news file line by line. It calls `self.add_entities`, `self.lookup_news_index`, `self.lookup_category_index`, `self.lookup_subcategory_index`, `self.lookup_entity_index`.

I need to construct a `MindData` instance. But the constructor reads files and calls `read_data` and `read_news`. The task says: "the thunk builds the instance and passes it as the first argument". But building via the constructor requires impression files and news files. That's actually fine - I can create those files under WORKDIR. But the constructor calls `read_news` on train and valid news files, which would populate `news_content`. That's fine but adds work in the thunk (not timed).

Alternatively, I could construct the instance without calling `__init__`... but that's not allowed? Actually the rule says "no subclass that overrides a method". Using `MindData.__new__(MindData)` and setting fields manually is "setting data (an object's fields) to build an input is fine". Hmm, that might be simpler and more controlled.

But wait - the lookup methods are elided. I need to know what they do. They're not shown. `lookup_news_index(news_id)` presumably does something like `lookup_index(news_id, self.news_map)` which assigns a new index if not present. Since bodies are elided, I must rely on the real repository code. Hmm, but the task says "Everything you can know about the repository is in the task: do not try to recall its code from memory".

This is tricky. The lookup methods are elided, so I don't know their exact behavior. But I can still build inputs that work regardless: the functions presumably use `self.news_map`, `self.cat_map`, `self.sub_cat_map`, `self.entity_map`, and `self.news_content`. Setting these as empty dicts (as `__init__` does) should be safe.

Actually, the safest approach: build the instance through the real `__init__` with real files. That way whatever the lookup methods do, they work. The constructor requires:
- train_news_file, train_impressions_file, valid_news_file, valid_impressions_file

`read_data(impressions_file, impression_list)` - reads impressions file. I don't know its format exactly, but from MIND dataset, impressions.tsv lines are like: `impression_id \t user_id \t timestamp \t history \t impressions`. Hmm, but the exact parse is elided.

Actually I could make the impression files empty! `read_data` with an empty file would just do nothing (loop over no lines). That should work. Then `read_news` is called on train and valid news files - I can make those empty too, or minimal.

Then after construction, I call `read_news` with my actual test file. That's clean and uses only the real constructor.

But wait - `read_data` might do something with an empty file... it should be fine. Let me consider: it opens file, iterates lines. Empty -> no iterations. Should be safe.

Hmm, but does `read_data` check `os.path.exists`? Possibly. I'll create the files anyway.

Also `read_news` in the constructor: if the news file doesn't exist, it calls `sys.exit(1)`. So I must create the files.

OK so plan:
- Module level: create impression files (empty) and news files (empty) under WORKDIR.
- Build a MindData instance at module level? But the instance accumulates state across calls. `read_news` adds to `self.news_content` and to the maps. Since the call is repeated many times with the same arguments, `news_content` would grow and the maps would grow. That changes behavior across calls (though output comparison... hmm, the function returns None). Actually the function returns nothing. The comparison is on the return value and the arguments (the file path string, unchanged). So repeated calls would just keep re-adding the same entries - idempotent-ish since same doc_ids map to same indices.

Wait, but the task says "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys". Here `self.news_content` and maps are on the instance, which is passed as an argument. Hmm, the instance is an argument to the function (self). The arguments are rendered before and after each call to see whether it changed them. So the instance's state change would be detected... but that's the same for original and modified, so it's fine? Actually "Its arguments are rendered before and after each call to see whether it changed them" - this is about detecting mutation. But since we compare original vs modified, as long as both mutate identically, fine.

Hmm, but actually re-adding the same doc_ids: `lookup_news_index` might do `if news_id not in self.news_map: self.news_map[news_id] = len(...)`. So repeated calls with same file are idempotent. Good, consistent work each call.

But to be safe and give "each thunk call new keys", I could build a new instance for each call. But building an instance is expensive (constructor). Hmm. Actually the constructor reads the (empty) files, which is cheap. So building a fresh instance per thunk call is fine and cheap!

Actually wait, but the instance must be built in the thunk. Let me have each thunk build a fresh MindData instance plus return the news file. That's clean: every call starts from a fresh instance, so state is identical. But building the instance each time costs time in the thunk (not timed). Good.

Hmm, but there's a subtlety: the constructor calls `read_news` on train and valid news files. If those are empty, fine.

Actually, is there an issue: `read_news` prints stuff. Printing is fine.

Now, the news file format. Each line: doc_id, category, subcategory, title, abstract, url, title_entities (JSON), abstract_entities (JSON). Tab-separated.

The function: `title_entities = json.loads(news_data[6]) if len(news_data) > 6 else []`. So lines can have 6 fields (no entities) or 8 fields.

`add_entities(entity_ids, title_entities)` - elided. Presumably it extracts entity ids from the entities list and appends to entity_ids. It's called with the parsed JSON (a list of dicts with keys like "Label", "Type", "WikidataId", "Confidence", "SurfaceForms"). Then `entity_ids.extend([""] * entities_to_keep)` (2 empties). Then `entity_index` = first 2 entity ids looked up.

So entity_ids after add_entities has some entities, then two empty strings. `entity_ids[:2]` takes the first 2. If title+abstract have >= 2 entities, we get real entity ids. Otherwise we get some empties.

I don't know exactly what `add_entities` does but I can create realistic entity JSON: list of dicts with "WikidataId" key. Since add_entities is elided, I'll just produce realistic MIND entity JSON.

Actually, let me think: MIND news.tsv format:
```
N55528	finance	newscategory	title	abstract	url	[{"Label": "...", "Type": "P", "WikidataId": "Q...", "Confidence": 1.0, "SurfaceForms": [...]}, ...]
```
Yes. So title_entities and abstract_entities are JSON arrays of entity dicts.

`add_entities(entity_ids, entities)`: probably iterates entities and appends `entity["WikidataId"]` if present, maybe with a limit. Something like:

```python
def add_entities(self, entity_ids, entities):
    if len(entity_ids) >= 2: return
    for entity in entities:
        entity_ids.append(entity["WikidataId"])
```

I don't know. But it doesn't matter much - I just supply realistic data.

Now the key constraint: "keep what it returns ... under about 100 000 values" - it returns None. "Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values." The arguments are the instance and the file path. The instance is huge (news_content grows to number of lines). So keep the number of lines times fields under ~1M values. Each line adds one dict to news_content. So maybe up to ~50k-100k lines is fine. Let's keep lines around 20k-60k.

Hmm, rendering the instance: `self.news_content` has one entry per line, each a dict of 4 keys with a list of 2. So per line ~ 1 + 4 + 2 = 7 values. 60k lines -> 420k values. Plus maps. OK.

But wait, the constructor also adds to news_content? Only if news files non-empty. I'll keep them empty so only the measured call populates.

Actually, but I want each thunk to build a fresh instance. Then the instance only gets populated by the measured call. Good.

Let me decide on the number of lines. One call should take 1ms-200ms. Reading and parsing 20k lines with JSON parsing... probably ~100-200ms. Let's aim for varying sizes: 5k, 10k, 20k, 40k, etc. Let me estimate: json.loads on small arrays is fast. Per line maybe 10-30 microseconds. 20k lines -> 0.2-0.6s. Hmm, might exceed 200ms. Let me use smaller: 2k-15k lines.

Actually the pruning keeps the 4 that do the most work, so I want a range. Let's do sizes like 1k, 3k, 6k, 10k, 15k, 20k, 30k, 40k. But if one call > 1s it's dropped. Let me be conservative: max ~20k lines.

Hmm, let me reconsider. Actually the JSON parsing of entities is the expensive part. Let me include some lines with many entities and some with none (6-field lines) to vary.

Let me design 8 cases:
1. Small plain: 2000 lines, 6 fields (no entities).
2. Medium with entities: 5000 lines, 8 fields with few entities.
3. Many entities: 3000 lines with many entities each (10-20 entities).
4. Large: 15000 lines mixed.
5. Duplicate doc_ids/categories: 8000 lines with heavy duplicates.
6. All distinct categories/subcategories: 6000 lines.
7. Mixed field counts: 10000 lines randomly 6, 7, or 8 fields.
8. Large with long titles/abstracts: 8000 lines.

Wait, but `add_entities` behavior with many entities - if it caps at 2, extra entities don't matter. If it doesn't cap, then entity_ids grows large and `entity_ids[:2]` takes first 2. So many entities mostly affect parse cost.

Let me think about the "distinct labels" requirement and 8 cases.

Now, checks(): 2-3 small edge inputs.
- Empty file (0 lines).
- File with one line, 6 fields (no entities).
- File with one line, 8 fields.

These may raise. Empty file: read_news with empty file -> no iterations, returns None. Fine.

Now, the file must exist. For checks, create small files.

Where to create files: module level under WORKDIR, or in thunk. Since the function only reads, and the file content is fixed, I can create files at module level. But the thunk returns the path. The instance must be built per thunk.

Wait — building the instance per thunk: the constructor reads train/valid news and impressions files. I need those files too. Let me create them empty (or with a few lines) at module level.

But careful: if the constructor's `read_news` on empty file works fine. And `read_data` on empty file works fine. Let me verify `read_data` doesn't require content. Elided, but likely:

```python
def read_data(self, impressions_file, impression_list):
    if not os.path.exists(impressions_file): ...
    with io.open(...) as f:
        for line in f:
            ...
```
Empty -> nothing. Fine.

Hmm, but there's a risk: maybe `read_data` calls `sys.exit` if file missing. We create the file, so fine.

Now, building the instance per thunk: how expensive? Constructor does file existence checks and opens 4 files. Cheap. Good.

But actually — is it necessary to build per thunk? The concern is state accumulation. If the same instance is reused, `news_content` gets overwritten with the same keys each time (same doc_ids -> same indices). Map lookups: same keys, no growth. So it's actually idempotent. But to be safe and clean, build fresh per thunk. That's allowed since setup isn't timed.

Hmm wait, but there's a subtlety: the maps start empty in a fresh instance. In a reused instance they'd be populated. Either way the work per call is similar. Fresh is cleaner. Let's do fresh.

But building fresh instance means the constructor reads files each thunk call — but that's not timed. Fine.

Actually, hmm, one concern: does `MindData.__init__` do anything expensive like torch stuff? No, it just reads data. Fine.

Let me now write the entity JSON generator.

```python
def _entity_json(rng, n):
    ents = []
    for _ in range(n):
        ents.append({
            "Label": f"label{rng.randrange(1000)}",
            "Type": rng.choice(["P", "O", "T"]),
            "WikidataId": f"Q{rng.randrange(100000)}",
            "Confidence": round(rng.random(), 3),
            "SurfaceForms": [f"sf{rng.randrange(100)}"],
        })
    return json.dumps(ents)
```

And a line builder:

```python
def _make_line(rng, doc_id, category, subcategory, n_title_ents, n_abs_ents, with_entities=True):
    title = ...
    abstract = ...
    url = ...
    if with_entities:
        fields = [doc_id, category, subcategory, title, abstract, url,
                  _entity_json(rng, n_title_ents), _entity_json(rng, n_abs_ents)]
    else:
        fields = [doc_id, category, subcategory, title, abstract, url]
    return "\t".join(fields)
```

Careful: titles/abstracts must not contain tabs or newlines. Use simple text.

Now, the function reads lines and splits by "\t". Note `line` includes trailing "\n". The last field (abstract_entities JSON) would have a trailing "\n" — json.loads handles trailing whitespace fine. Actually for 6-field lines, url has trailing newline; url is just stored... no, url isn't used. Actually url is parsed but never used! Look: `url = news_data[5]` then never used. Fine.

Wait, actually if a line has only 6 fields and the last field is url with "\n", fine. If 8 fields, the 8th is JSON with "\n", json.loads handles it.

Hmm, but what if a line has 7 fields? `len(news_data) > 6` true -> json.loads(news_data[6]); `len > 7` false -> abstract_entities = []. So 7-field lines: title_entities parsed, abstract_entities empty. That's a valid edge. Include in mixed case.

Now categories and subcategories: realistic MIND has categories like "news", "sports", "finance", "lifestyle", "health", "travel", "autos", "entertainment", "foodanddrink", "movies", "music", "weather", "video", "kids". Subcategories are more specific.

Let me create lists.

Now, the entity ids: WikidataId like "Q12345". For duplicates across lines, reuse a pool.

Let me now think about sizes and time. Let me just pick moderate sizes and trust. Actually I should be careful: the timing budget is 1ms-200ms per call. Let me estimate more carefully.

Per line work: split, 6 index accesses, 2 json.loads (if 8 fields), add_entities twice, extend, then dict construction with 3 lookups + list comp of 2 lookups. That's maybe 5-20 µs for small entities. For 10k lines -> 50-200ms.

JSON parsing of a 10-entity array: maybe 5-10µs. Two per line -> 10-20µs. So 10k lines with entities -> 100-300ms. Hmm.

Let me keep entity counts modest: 0-5 entities typically.

Let me set sizes:
1. 3000 lines, no entities (6 fields).
2. 8000 lines, 1-3 entities each.
3. 4000 lines, many entities (5-15).
4. 20000 lines, mixed 6/7/8 fields, few entities.
5. 10000 lines, heavy duplicates.
6. 12000 lines, all distinct categories/subcategories.
7. 6000 lines, long titles/abstracts.
8. 16000 lines, mixed.

Hmm, 20000 lines might be ~200-400ms. Risky. Let me cap at 12000 for the largest. Actually the pruning drops inputs > 1s, and keeps the 4 with most work. So even if some are 300ms, that's fine as long as < 1s. The instruction says "One call should take roughly 1 ms to 200 ms on the original." Let me aim for that but it's a soft guideline. I'll keep sizes moderate.

Let me use: 2000, 5000, 3000, 10000, 6000, 8000, 4000, 12000. Hmm, let me just pick reasonable values.

Actually, let me reconsider the per-line cost. Python string split and dict ops are fast. Let me estimate ~10µs/line average. 10000 lines -> 100ms. Good. So sizes up to ~10000 are safe (~100ms). Let me use max 12000.

Let me finalize:

cases:
1. ("no-entities", 2000 lines, 6 fields)
2. ("few-entities", 5000 lines, 1-3 title + 0-2 abstract)
3. ("many-entities", 2500 lines, 5-15 each)
4. ("mixed-fields", 8000 lines, random 6/7/8)
5. ("duplicates", 6000 lines, small pool of doc_ids/categories)
6. ("all-distinct", 7000 lines, unique categories/subcategories)
7. ("long-text", 4000 lines, long titles/abstracts, few entities)
8. ("large-mixed", 10000 lines, everything mixed)

Now the instance. Building fresh per thunk.

Let me write a helper `_new_mind()` that builds a MindData with empty files.

```python
_EMPTY_IMPR = WORKDIR / "empty_impressions.tsv"
_EMPTY_NEWS = WORKDIR / "empty_news.tsv"
_EMPTY_IMPR.write_text("")
_EMPTY_NEWS.write_text("")

def _new_mind():
    return MindData(str(_EMPTY_NEWS), str(_EMPTY_IMPR), str(_EMPTY_NEWS), str(_EMPTY_IMPR))
```

Wait, but the constructor signature: `__init__(self, train_news_file, train_impressions_file, valid_news_file, valid_impressions_file)`. Order: train_news, train_impressions, valid_news, valid_impressions. So `MindData(train_news, train_impr, valid_news, valid_impr)`.

Hmm, `read_data(impressions_file, impression_list)` is called with train_impressions_file and valid_impressions_file. Empty files -> nothing.

But wait: does `read_data` require the file to exist? It might check and sys.exit. We create it. Good.

Now, one concern: what if `read_data` on empty file throws because it expects at least a header? Unlikely. Let's assume fine.

Alternatively, to be extra safe, I could bypass `__init__` using `__new__` and set the fields directly. That avoids any dependency on `read_data`'s format. The rule: "Setting data (a module's configuration, an object's fields) to build an input is fine." So:

```python
def _new_mind():
    m = MindData.__new__(MindData)
    m.user_map = {}
    m.news_map = {}
    m.cat_map = {}
    m.sub_cat_map = {}
    m.entity_map = {}
    m.news_content = {}
    m.train_impressions = []
    m.valid_impressions = []
    return m
```

This is cleaner and avoids file format issues. But it relies on knowing the field names from `__init__`, which are shown. And the lookup methods presumably use these maps. This is "setting an object's fields to build an input" — allowed.

Hmm, but is `MindData.__new__(MindData)` considered a mock? No, it's the real class, just not calling init. I think it's fine. But the instructions say "the thunk builds the instance and passes it as the first argument". Building via __new__ is building the instance.

Which is safer? Using the real constructor is more faithful ("Prepare the way the repository's own callers do"). The repository callers do `MindData(train_news_file, ...)`. But they pass real files. Using empty files is a deviation but reasonable.

Risk with real constructor: `read_data` format unknown, might fail on empty file. Risk with __new__: lookup methods might use fields I didn't set (but __init__ shows all fields).

Actually, the lookup methods might reference something else. Let me look: `lookup_index(self, id, map)` — takes a map. `lookup_news_index(self, news_id)` probably calls `self.lookup_index(news_id, self.news_map)`. So it uses self.news_map. Similarly others. And `add_entities` uses nothing from self probably (just entity_ids and entities). Hmm, or it might use self.entity_map? No, it just appends ids to entity_ids.

I think __new__ approach is safe. But let me go with the real constructor with empty files, since it's more faithful and the empty-file case is very likely fine. Hmm.

Actually, let me reconsider: there's a real risk `read_data` on an empty file does something like `line.split("\t")` and then indexes — but with no lines, no iterations. So safe. The only risk is if read_data has code before the loop that fails. E.g., it might open the file and read a header line. Unlikely for MIND.

I'll go with the real constructor. Actually, you know what, let me hedge: I'll use the real constructor but with small valid-ish files? No, empty is simplest.

Hmm, actually let me reconsider once more. If `read_data` reads impressions and there's a header line expected... MIND impressions.tsv has no header. So fine.

Decision: use real constructor with empty impression files and empty news files.

Wait, but there's another issue: the constructor calls `read_news` on the empty news files, which prints "Reading data from ...". Fine.

Now, the thunk:

```python
def _case(path):
    return lambda: (MindData(str(_EMPTY_NEWS), str(_EMPTY_IMPR), str(_EMPTY_NEWS), str(_EMPTY_IMPR)), str(path))
```

Wait, `read_news(self, news_file)` — so args are (instance, news_file). Thunk returns `(_new_mind(), str(path))`. Good.

Now let me write the data generation.

Let me write a function to generate a news file:

```python
def _gen_news(path, n, seed, *, entity_range=(0,0), field_modes=None, dup_pool=None, long_text=False):
    rng = random.Random(seed)
    lines = []
    ...
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

Hmm, careful with encoding. The function opens with encoding="utf-8". Write with utf-8.

Let me make it flexible.

Categories and subcategories:

```python
_CATEGORIES = ["news", "sports", "finance", "lifestyle", "health", "travel", "autos", "entertainment", "foodanddrink", "movies", "music", "weather", "video", "kids"]
_SUBCATS = ["newscategory", "football", "nfl", "basketball", "mlb", "nba", "soccer", "golf", "tennis", "movies", "tv", "music", "celebrities", "health", "medical", "travel", "food", "recipes", "autos", "weather"]
```

Entity pool for duplicates.

Let me write:

```python
def _entities_json(rng, count, pool):
    ents = []
    for _ in range(count):
        qid = pool[rng.randrange(len(pool))]
        ents.append({
            "Label": "entity" + qid,
            "Type": rng.choice(["P", "O", "T"]),
            "WikidataId": qid,
            "Confidence": round(rng.uniform(0.5, 1.0), 3),
            "SurfaceForms": ["sf" + str(rng.randrange(50))],
        })
    return json.dumps(ents)
```

Now the main generator:

```python
def _make_news_file(path, n_lines, seed, ent_lo, ent_hi, field_mode, doc_pool, cat_pool, sub_pool, text_len):
    rng = random.Random(seed)
    ent_pool = ["Q" + str(i) for i in range(500)]
    lines = []
    for i in range(n_lines):
        if doc_pool is None:
            doc_id = "N" + str(100000 + i)
        else:
            doc_id = doc_pool[rng.randrange(len(doc_pool))]
        category = cat_pool[rng.randrange(len(cat_pool))]
        subcategory = sub_pool[rng.randrange(len(sub_pool))]
        title = " ".join("t" + str(rng.randrange(1000)) for _ in range(text_len))
        abstract = " ".join("a" + str(rng.randrange(1000)) for _ in range(text_len))
        url = "http://example.com/" + str(i)
        n_title = rng.randint(ent_lo, ent_hi)
        n_abs = rng.randint(ent_lo, ent_hi)
        if field_mode == "none":
            lines.append("\t".join([doc_id, category, subcategory, title, abstract, url]))
        elif field_mode == "title_only":
            lines.append("\t".join([doc_id, category, subcategory, title, abstract, url, _entities_json(rng, n_title, ent_pool)]))
        elif field_mode == "mixed":
            r = rng.random()
            if r < 0.34:
                lines.append("\t".join([doc_id, category, subcategory, title, abstract, url]))
            elif r < 0.67:
                lines.append("\t".join([doc_id, category, subcategory, title, abstract, url, _entities_json(rng, n_title, ent_pool)]))
            else:
                lines.append("\t".join([doc_id, category, subcategory, title, abstract, url, _entities_json(rng, n_title, ent_pool), _entities_json(rng, n_abs, ent_pool)]))
        else:  # "both"
            lines.append("\t".join([doc_id, category, subcategory, title, abstract, url, _entities_json(rng, n_title, ent_pool), _entities_json(rng, n_abs, ent_pool)]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

Note: MIND uses spaces in titles, and the fields are tab-separated. Good.

Now the cases. Let me define module-level file paths and generate them.

Let me pick sizes carefully. I'll go:

1. no-entities: 2000 lines, field_mode="none", text_len=8
2. few-entities: 5000 lines, field_mode="both", ent 1-3, text_len=10
3. many-entities: 2500 lines, field_mode="both", ent 6-15, text_len=8
4. mixed-fields: 8000 lines, field_mode="mixed", ent 0-4, text_len=10
5. duplicates: 6000 lines, field_mode="both", doc_pool of 200, cat_pool of 5, sub_pool of 8, ent 1-3
6. all-distinct: 7000 lines, field_mode="both", unique categories? Hmm, categories are from a fixed list. To make "all distinct" I'd need many categories. Let me instead use unique doc_ids and unique subcategories generated per line.
7. long-text: 4000 lines, text_len=60, ent 1-2
8. large-mixed: 10000 lines, field_mode="mixed", ent 0-5

For case 6 (all distinct), let me generate subcategories per line as "sub{i}" and categories from a larger generated list. Actually categories in real data are limited. Let me just make doc_ids unique and subcategories unique. Hmm, "all distinct" — I'll create a variant where category = "cat" + str(i % 1000) to have many distinct categories. That stresses the cat_map growth.

Actually, let me make case 6 stress distinct keys: doc_id unique, category from 1000 values, subcategory from 2000 values, entities from a large pool. This makes the maps grow a lot — good stress.

Hmm, but map growth is per-instance, and each thunk builds a fresh instance, so the maps grow during the measured call. That's real work.

Let me restructure the generator to accept explicit pools/lists.

Let me simplify: write a generator that takes a function for doc_id, category, subcategory.

Actually let me just write separate small generators inline in cases? That's a lot of code. Let me make a flexible generator.

I'll write:

```python
def _gen(path, n, seed, *, mode="both", ent_lo=1, ent_hi=3, text_len=8,
         doc_ids=None, categories=None, subcategories=None, ent_pool_size=500):
    rng = random.Random(seed)
    ent_pool = ["Q" + str(i) for i in range(ent_pool_size)]
    lines = []
    for i in range(n):
        doc_id = doc_ids[i] if doc_ids is not None else "N" + str(100000 + i)
        category = categories[i % len(categories)] if categories is not None else _CATEGORIES[i % len(_CATEGORIES)]
        subcategory = subcategories[i % len(subcategories)] if subcategories is not None else _SUBCATS[i % len(_SUBCATS)]
        ...
```

Hmm, using i % len for categories gives a pattern. For realism, random choice is better. Let me use rng.choice for the default, and for distinct cases pass lists and use i.

Let me just handle it with flags. Let me write:

```python
def _gen(path, n, seed, mode="both", ent_lo=1, ent_hi=3, text_len=8,
         n_doc=0, n_cat=0, n_sub=0, ent_pool_size=500):
    """n_doc/n_cat/n_sub: 0 => unique per line; >0 => random from that many distinct values."""
    rng = random.Random(seed)
    ent_pool = ["Q" + str(i) for i in range(ent_pool_size)]
    lines = []
    for i in range(n):
        if n_doc == 0:
            doc_id = "N" + str(100000 + i)
        else:
            doc_id = "N" + str(100000 + rng.randrange(n_doc))
        if n_cat == 0:
            category = _CATEGORIES[rng.randrange(len(_CATEGORIES))]
        else:
            category = "cat" + str(rng.randrange(n_cat))
        if n_sub == 0:
            subcategory = _SUBCATS[rng.randrange(len(_SUBCATS))]
        else:
            subcategory = "sub" + str(rng.randrange(n_sub))
        ...
```

Hmm, but for case "all-distinct" I want many distinct categories, so n_cat large (e.g., 5000) with n=7000 lines -> mostly distinct. Good.

Actually the default (n_cat=0) uses the fixed 14 categories — realistic. Let me set:

- case 1: n_doc=0 (unique), n_cat=0, n_sub=0, mode="none"
- case 2: n_doc=0, n_cat=0, n_sub=0, mode="both", ent 1-3
- case 3: n_doc=0, n_cat=0, n_sub=0, mode="both", ent 6-15
- case 4: mode="mixed", ent 0-4
- case 5: n_doc=200, n_cat=5, n_sub=8, mode="both" (duplicates)
- case 6: n_doc=0, n_cat=5000, n_sub=6000, mode="both" (distinct)
- case 7: mode="both", ent 1-2, text_len=60
- case 8: mode="mixed", ent 0-5, n_doc=0

Wait, but n_doc=0 means unique doc_ids — that's fine and realistic (each news item unique). For duplicates case, n_doc=200.

Hmm, but the default category selection `_CATEGORIES[rng.randrange(len)]` gives random from 14. Good.

For "distinct" case with n_cat=5000, categories are "cat0".."cat4999" — random selection, so ~ n*(1-...) distinct. Fine.

Now text_len: title of text_len words. For long-text, text_len=60 words each. That makes lines long but fine.

Now, sizes. Let me reconsider timing. I'll go with:

1. no-entities: n=2000, mode="none", text_len=8
2. few-entities: n=5000, mode="both", ent 1-3, text_len=10
3. many-entities: n=2500, mode="both", ent 6-15, text_len=8
4. mixed-fields: n=8000, mode="mixed", ent 0-4, text_len=10
5. duplicates: n=6000, n_doc=200, n_cat=5, n_sub=8, mode="both", ent 1-3
6. distinct: n=7000, n_cat=5000, n_sub=6000, mode="both", ent 1-3
7. long-text: n=4000, mode="both", ent 1-2, text_len=60
8. large-mixed: n=10000, mode="mixed", ent 0-5, text_len=10

Total lines generated: 2000+5000+2500+8000+6000+7000+4000+10000 = 44500 lines. Building under 10s — yes, fast.

Memory: each file maybe a few MB. Fine.

Now checks():
- empty file: 0 lines.
- one line, 6 fields.
- one line, 8 fields.

For empty file, `path.write_text("")`. read_news loops zero times. Returns None.

For the one-line files, generate with n=1.

Let me create these files at module level too.

Now, one thing: the function prints. Printing to stdout during timing — fine, but could be slow. It prints once per call ("Reading data from ..."). Negligible.

Now, about `sys.exit(1)` if file not found — our files exist.

Let me also double check: the function uses `io.open(news_file, "r", encoding="utf-8")`. Our files are utf-8. Good.

Now, potential issue: `json.loads(news_data[6])` where news_data[6] for a line without trailing newline... The last line: if I write "\n".join(lines) + "\n", every line ends with "\n". So news_data[7] would be the JSON + "\n". json.loads handles trailing whitespace. And for 6-field lines, news_data[5] = url + "\n". Fine.

But wait, `line.split("\t")` — if the abstract contains no tabs (we use spaces), fine.

Now, one more: `add_entities(entity_ids, title_entities)` where title_entities is a list of dicts. If add_entities expects dicts, fine. If it expects strings... Hmm. MIND entity JSON is list of dicts, and the function does json.loads. So add_entities must handle list of dicts. Good.

Actually, I realize I should double check: maybe `add_entities` expects the entities to be a list of dicts and does `entity["WikidataId"]`. Yes.

Now, what if add_entities raises on our data? E.g., if it accesses a key we didn't provide. We provide Label, Type, WikidataId, Confidence, SurfaceForms — the standard MIND keys. Should be fine.

Hmm, but if it only uses "WikidataId", extra keys are harmless.

Let me now also consider: does the function's output matter? It returns None. The comparison is on return value and argument rendering. Fine.

Now let me write the final code.

One concern: `MindData.__init__` requires 4 args. The thunk builds it. But if `read_data` on empty file fails... Let me reduce risk by using the `__new__` approach? Hmm.

Let me think about which is more robust. The instruction says "Prepare the way the repository's own callers do". The repository callers call the constructor with real files. Using empty files is a reasonable stand-in.

But I genuinely don't know read_data's body. If it does something like:

```python
def read_data(self, impressions_file, impression_list):
    if not os.path.exists(impressions_file):
        print(...)
        sys.exit(1)
    with io.open(impressions_file, "r", encoding="utf-8") as f:
        for line in f:
            ...
```

Empty file -> fine.

I'll go with the constructor. Actually, hmm, wait. There's a subtle risk: what if `read_data` is fine but the constructor's `read_news` on the empty news file... `os.path.exists` true, opens, loops zero times. Fine.

OK. But actually, there's another consideration: building the instance via constructor calls read_news twice on empty files — cheap. Good.

Hmm, but actually — I realize there might be an issue with using the same empty file for both train_news and valid_news. The constructor calls read_news(train_news_file) then read_news(valid_news_file). Both empty. Fine.

Let me go with constructor.

Actually, wait. Let me reconsider using `__new__` vs constructor once more, thinking about robustness of the *measured* call. The measured call is `read_news(instance, news_file)`. It uses `self.add_entities`, `self.lookup_*`, and `self.news_content`, `self.*_map`. Both approaches set these. The constructor approach additionally runs read_data which populates train_impressions/valid_impressions (empty). Doesn't matter.

I'll use the constructor for faithfulness.

Hmm, but one more risk: what if `MindData.__init__` or `read_data` prints a lot or is slow? Empty files -> negligible.

OK, final decision: constructor with empty files.

Actually, hold on. Let me reconsider: what if `read_data` requires the impressions file to have specific columns and crashes on empty? No, empty has no lines.

Fine.

Let me write the code.

```python
import json
import random

from mind_data import MindData

_CATEGORIES = [
    "news", "sports", "finance", "lifestyle", "health", "travel",
    "autos", "entertainment", "foodanddrink", "movies", "music",
    "weather", "video", "kids",
]
_SUBCATS = [
    "newscategory", "football", "nfl", "basketball", "mlb", "nba",
    "soccer", "golf", "tennis", "movies", "tv", "music",
    "celebrities", "health", "medical", "travel", "food", "recipes",
    "autos", "weather",
]

_EMPTY_IMPR = WORKDIR / "empty_impressions.tsv"
_EMPTY_NEWS = WORKDIR / "empty_news.tsv"
_EMPTY_IMPR.write_text("", encoding="utf-8")
_EMPTY_NEWS.write_text("", encoding="utf-8")


def _new_mind():
    return MindData(str(_EMPTY_NEWS), str(_EMPTY_IMPR),
                    str(_EMPTY_NEWS), str(_EMPTY_IMPR))


def _entities_json(rng, count, pool):
    ents = []
    for _ in range(count):
        qid = pool[rng.randrange(len(pool))]
        ents.append({
            "Label": "entity_" + qid,
            "Type": rng.choice(["P", "O", "T"]),
            "WikidataId": qid,
            "Confidence": round(rng.uniform(0.5, 1.0), 3),
            "SurfaceForms": ["surface_" + str(rng.randrange(50))],
        })
    return json.dumps(ents)


def _gen(path, n, seed, mode="both", ent_lo=1, ent_hi=3, text_len=8,
         n_doc=0, n_cat=0, n_sub=0, ent_pool_size=500):
    rng = random.Random(seed)
    pool = ["Q" + str(i) for i in range(ent_pool_size)]
    lines = []
    for i in range(n):
        if n_doc == 0:
            doc_id = "N" + str(100000 + i)
        else:
            doc_id = "N" + str(100000 + rng.randrange(n_doc))
        if n_cat == 0:
            category = _CATEGORIES[rng.randrange(len(_CATEGORIES))]
        else:
            category = "cat" + str(rng.randrange(n_cat))
        if n_sub == 0:
            subcategory = _SUBCATS[rng.randrange(len(_SUBCATS))]
        else:
            subcategory = "sub" + str(rng.randrange(n_sub))
        title = " ".join("t" + str(rng.randrange(1000)) for _ in range(text_len))
        abstract = " ".join("a" + str(rng.randrange(1000)) for _ in range(text_len))
        url = "http://example.com/news/" + str(i)
        base = [doc_id, category, subcategory, title, abstract, url]
        if mode == "none":
            lines.append("\t".join(base))
        elif mode == "title":
            lines.append("\t".join(base + [_entities_json(rng, rng.randint(ent_lo, ent_hi), pool)]))
        elif mode == "mixed":
            r = rng.random()
            if r < 0.34:
                lines.append("\t".join(base))
            elif r < 0.67:
                lines.append("\t".join(base + [_entities_json(rng, rng.randint(ent_lo, ent_hi), pool)]))
            else:
                lines.append("\t".join(base + [
                    _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
                    _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
                ]))
        else:  # both
            lines.append("\t".join(base + [
                _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
                _entities_json(rng, rng.randint(ent_lo, ent_hi), pool),
            ]))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path
```

Wait, for empty file (n=0), "\n".join([]) = "" and we add "" -> "". Good.

Now generate files:

```python
_F = {}
_F["noent"] = _gen(WORKDIR / "news_noent.tsv", 2000, 0, mode="none", text_len=8)
_F["fewent"] = _gen(WORKDIR / "news_fewent.tsv", 5000, 1, mode="both", ent_lo=1, ent_hi=3, text_len=10)
_F["manyent"] = _gen(WORKDIR / "news_manyent.tsv", 2500, 2, mode="both", ent_lo=6, ent_hi=15, text_len=8)
_F["mixed"] = _gen(WORKDIR / "news_mixed.tsv", 8000, 3, mode="mixed", ent_lo=0, ent_hi=4, text_len=10)
_F["dups"] = _gen(WORKDIR / "news_dups.tsv", 6000, 4, mode="both", ent_lo=1, ent_hi=3, text_len=10, n_doc=200, n_cat=5, n_sub=8)
_F["distinct"] = _gen(WORKDIR / "news_distinct.tsv", 7000, 5, mode="both", ent_lo=1, ent_hi=3, text_len=10, n_cat=5000, n_sub=6000)
_F["long"] = _gen(WORKDIR / "news_long.tsv", 4000, 6, mode="both", ent_lo=1, ent_hi=2, text_len=60)
_F["large"] = _gen(WORKDIR / "news_large.tsv", 10000, 7, mode="mixed", ent_lo=0, ent_hi=5, text_len=10)

_C = {}
_C["empty"] = _gen(WORKDIR / "news_empty.tsv", 0, 100, mode="none")
_C["one6"] = _gen(WORKDIR / "news_one6.tsv", 1, 101, mode="none", text_len=5)
_C["one8"] = _gen(WORKDIR / "news_one8.tsv", 1, 102, mode="both", ent_lo=2, ent_hi=2, text_len=5)
```

Then:

```python
def _mk(path):
    return lambda: (_new_mind(), str(path))


def checks():
    return [
        ("empty-file", _mk(_C["empty"])),
        ("single-line-6-fields", _mk(_C["one6"])),
        ("single-line-8-fields", _mk(_C["one8"])),
    ]


def cases():
    return [
        ("no-entities", _mk(_F["noent"])),
        ("few-entities", _mk(_F["fewent"])),
        ("many-entities", _mk(_F["manyent"])),
        ("mixed-field-counts", _mk(_F["mixed"])),
        ("duplicate-ids", _mk(_F["dups"])),
        ("all-distinct-keys", _mk(_F["distinct"])),
        ("long-text", _mk(_F["long"])),
        ("large-mixed", _mk(_F["large"])),
    ]
```

Wait — `_mk` returns a lambda that builds a fresh MindData each call. Good. But building MindData each thunk call: the constructor reads 2 empty files twice (read_data x2, read_news x2). Cheap.

Hmm, but actually there's a subtlety: the thunk is called before timing, and the returned args are used for the timed call. Building MindData in the thunk is not timed. Good.

But wait — "the call is repeated many times in a row, and every call gets the arguments of its own thunk call". So each repetition calls the thunk again? Or the thunk is called once and args reused? The instruction says "every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts". Hmm, ambiguous. I think thunks are called once per case before timing, and the args reused. But then a fresh MindData per case would be reused across repetitions, accumulating state.

Hmm. "every call gets the arguments of its own thunk call" — suggests each call gets fresh args from a thunk call. Let me re-read: "The call is repeated many times in a row, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts."

I think it means: the thunk is called, args built, then the function is called many times with those same args. "all built and kept in memory before the timing starts" — so args are built once and reused.

Hmm, but then "if it caches or records what it has seen, give every thunk call new keys" implies thunks might be called multiple times. Confusing.

Actually I think the setup: for each case, the thunk is called once to get args, then the function is called N times with those args. The phrase "every call gets the arguments of its own thunk call" might mean across different cases.

Hmm, "all built and kept in memory before the timing starts" strongly suggests args are built once and reused for all repetitions.

So if I build a fresh MindData in the thunk, it's built once and reused for all repetitions. Then state accumulates across repetitions! news_content gets re-populated with same keys (idempotent), maps don't grow (same keys). So work per call is roughly constant. Actually, re-assigning same dict entries is same work. So fine.

But wait: on the first call, maps are empty and get filled. On subsequent calls, maps already have the keys, so lookup_index finds them. Does that change work? If lookup_index is `if id not in map: map[id]=len(map); return map[id]`, then subsequent calls skip the insertion — slightly less work. But the difference is small. And it's the same for original and modified. So it's fine for comparison.

Hmm, but the instruction warns about this. To be safe, I'd want fresh keys per call. But I can't control the file content per call if args are built once.

Alternative: make the thunk build a fresh MindData AND... no, the file path is fixed.

Hmm. Actually, if the thunk is called once per case, then a fresh MindData is built once. Fine. If the thunk is called before each repetition, fresh MindData each time. Either way, using a fresh MindData in the thunk is the best I can do.

Actually, re-reading again: "every call gets the arguments of its own thunk call". I now think the thunk IS called for each repetition (each "call"). "all built and kept in memory before the timing starts" refers to the fact that thunk execution isn't timed.

Hmm, but "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy". This suggests the thunk returns the same big data (built at module level) each time. So the thunk is called per repetition but returns shared data.

OK so thunks are called per repetition, but the heavy data is shared. For our case, building MindData per repetition is cheap, so it's fine either way. 

So a fresh MindData per thunk call ensures no state carryover. 

Now, is building MindData per call cheap enough relative to the measured call? The measured call is ~50-200ms; building MindData reads 4 tiny files, ~microseconds. Fine.

Now let me reconsider the empty-file case for the constructor. Actually, I realize I should double-check: does `MindData.__init__` have any other requirements? It calls read_data twice and read_news twice. All with our empty files. Should be fine.

Hmm, one more thought: what if `read_data` uses `self.lookup_user_index` etc. and needs the file. Empty -> no lines -> no calls. Fine.

Let me also consider: maybe `read_data` on an empty impressions file is fine, but what if it does `f.readline()` expecting a header? Let me not worry.

Actually, to be safest, maybe I should just use `__new__` and set fields. That completely avoids read_data. Let me weigh:

- Constructor: faithful, but risk if read_data misbehaves on empty file.
- __new__: no risk from read_data, but relies on field names (which are explicitly shown in __init__).

The field names are given in the task. Setting them is explicitly allowed ("Setting data ... an object's fields ... is fine"). I'll use __new__ to be safe and fast. Hmm, but is it "building the instance"? Yes.

Hmm, but actually the instruction says "the thunk builds the instance and passes it as the first argument (a classmethod gets its class there...)". Using __new__ is building the instance.

But wait, there's a risk: the lookup methods might rely on something set in __init__ that I don't know about. But __init__ is fully shown (the body). It sets exactly those fields. So __new__ + those fields = same as a fresh __init__-constructed instance (minus the read_data/read_news effects, which with empty files are nil).

Actually with empty files, the constructor leaves maps empty and news_content empty — exactly what __new__ gives. So they're equivalent!

I'll use __new__ to avoid any read_data risk. Actually... hmm, let me use the constructor since it's more "real" and empty files should be fine. Ugh.

Let me think about what could go wrong with read_data on empty file. The most likely implementation:

```python
def read_data(self, impressions_file, impression_list):
    if not os.path.exists(impressions_file):
        print("{} not found.".format(impressions_file))
        sys.exit(1)
    print("Reading data from " + impressions_file)
    with io.open(impressions_file, "r", encoding="utf-8") as f:
        for line in f:
            ...
```

Empty -> fine.

I'm fairly confident. But __new__ is strictly safer. Let me go with __new__.

Hmm, but one concern with __new__: the task says "no subclass that overrides a method of a repository or library class". __new__ isn't a subclass. Fine.

Actually, let me reconsider. There's a philosophical point: the graders might check that we don't do anything weird. Using __new__ is a known pattern for building test fixtures. I think it's acceptable.

Hmm, but "Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk." The callers call the constructor. So maybe I should call the constructor.

OK let me just do the constructor with empty files. It's the most faithful. If read_data fails on empty... risk. But I'll take it. Actually no — let me hedge differently: I can call the constructor with empty files, and if that's a problem... I can't test.

Hmm. Let me think about what's more likely to be correct. The MIND reader `read_data` reads impressions.tsv. An empty file is a degenerate but valid input. Standard code handles it.

I'll go with the constructor. Final.

Hmm, wait, actually there's a real consideration: `read_data` might do `line.strip().split("\t")` and then unpack like `impression_id, user_id, timestamp, history, impressions = ...`. With no lines, no unpacking. Fine.

OK, constructor it is.

Hmm, but actually, let me reconsider one more time. What if `read_data` reads the file and expects a specific number of columns even for the header? No header in MIND.

Fine. Constructor.

Hmm, actually, you know what — let me just use __new__. It's guaranteed to work regardless of read_data's implementation, and it's explicitly allowed. The risk of read_data is small but nonzero, and I can't test. The __new__ approach has essentially zero risk.

Wait, but is there a risk that the lookup methods use `self.train_impressions` or something? No, they use the maps. And I set all fields from __init__.

Decision: __new__. Let me write it.

Actually, hmm, one more consideration. If I use __new__ and set the fields, that's fine. But what if `MindData` has `__slots__`? Then setting fields works if they're in slots. __init__ sets them, so they're in slots. Fine.

OK.

Let me finalize the code.

Actually, let me reconsider whether to use the constructor. The problem statement says the function under test is called as `MindData.read_news(instance, ...)`. The instance must be a MindData. Both approaches give a MindData.

I'll go with the constructor actually — no wait. Ugh. Let me just decide: __new__ with fields. Done. It's robust.

Hmm, but actually, if the graders inspect "did you build the instance realistically", __new__ might look odd but it's fine.

Let me write it with the constructor but... no. OK, final: I'll use the constructor with empty files, because it's the most faithful and empty files are very likely fine. If read_data fails, the whole thing fails. Hmm.

Let me think about probability. read_data on empty file: 95% fine. __new__: 99% fine (field names given). The difference is small. 

I'll go with the constructor. No — I keep flip-flopping. Let me use the constructor because it also exercises the real init path and is what callers do. Actually, the constructor's read_data with an empty file is a totally standard no-op. I'm confident.

FINAL: constructor with empty files.

Hmm, no. Let me think about this differently. The task explicitly says: "Setting data (a module's configuration, an object's fields) to build an input is fine." This hints that setting fields directly is an accepted pattern. And it avoids the unknown read_data.

But it also says "Prepare the way the repository's own callers do".

You know, both are defensible. Let me use the constructor, since the callers use it, and empty files should work.

Ugh, OK. Constructor. Moving on.

Wait, actually, I realize there might be an issue with the constructor: it calls `read_news` twice, which is fine, but it also might be slow if... no, empty files.

OK writing final code with constructor.

Hmm, actually, let me reconsider the risk more concretely. If `read_data` is:

```python
def read_data(self, impressions_file, impression_list):
    if not os.path.exists(impressions_file):
        print("{} not found.".format(impressions_file))
        sys.exit(1)
    print("Reading data from " + impressions_file)
    with io.open(impressions_file, "r", encoding="utf-8") as f:
        for line in f:
            impression = line.strip().split("\t")
            ...
```

Fine with empty.

OK. Constructor.

Now let me also double check the `_gen` for mode="none" with text_len: title/abstract are words. Fine.

Let me also ensure no tabs in generated text. Words are "t123" etc. Good.

Now, the labels must be distinct. Yes.

Let me write the final code.

One more: the function under test is `MindData.read_news`. We call it as `MindData.read_news(instance, news_file)`. The thunk returns `(instance, news_file_str)`. Good.

Let me also make sure `_mk` returns a lambda that doesn't capture loop variables incorrectly. It captures `path` as a parameter. Good.

Final code:

```python
import json
import random

from mind_data import MindData

_CATEGORIES = [...]
_SUBCATS = [...]

_EMPTY_IMPR = WORKDIR / "empty_impressions.tsv"
_EMPTY_NEWS = WORKDIR / "empty_news.tsv"
_EMPTY_IMPR.write_text("", encoding="utf-8")
_EMPTY_NEWS.write_text("", encoding="utf-8")


def _new_mind():
    return MindData(str(_EMPTY_NEWS), str(_EMPTY_IMPR),
                    str(_EMPTY_NEWS), str(_EMPTY_IMPR))
...
```

Wait, the constructor signature is `(train_news_file, train_impressions_file, valid_news_file, valid_impressions_file)`. So `MindData(train_news, train_impr, valid_news, valid_impr)`. I pass `(EMPTY_NEWS, EMPTY_IMPR, EMPTY_NEWS, EMPTY_IMPR)`. Good.

Now write everything.

Let me reconsider sizes once more for the 1-200ms target. Actually, I worry 10000 lines with entities might be >200ms. Let me reduce the largest to 8000. And the mixed one to 6000. Hmm.

Let me estimate: Python reading a file line by line + split + json.loads. Roughly:
- split: ~1µs
- 6 index ops: ~0.5µs
- 2 json.loads of small arrays: ~4µs
- add_entities x2: ~1µs
- dict construction with lookups: ~3µs
Total ~10µs/line. 10000 lines -> 100ms. OK, within budget.

For many-entities (6-15 each, 2 arrays): json.loads of 10-element array ~8µs, x2 = 16µs, plus rest ~5µs = 21µs/line. 2500 lines -> 52ms. OK.

For long-text (60 words): string ops bigger, maybe 15µs/line. 4000 -> 60ms.

OK all within 200ms. Good.

Let me finalize.

Actually, I want to double-check the entity JSON structure doesn't break add_entities. Since add_entities is elided, I'll use the standard MIND keys. If add_entities does `entity["WikidataId"]`, we're good. If it does something else... risk. But standard.

Hmm, what if add_entities expects entities to be a list of dicts where each has "WikidataId" and it appends `self.lookup_entity_index(...)`? No, it appends to entity_ids (a list of ids). Then the caller does the lookup. So add_entities appends raw ids.

Actually, re-reading the function: `self.add_entities(entity_ids, title_entities)` then `entity_ids.extend([""]*2)` then `entity_index: [self.lookup_entity_index(id) for id in entity_ids[:2]]`. So add_entities appends id strings. Good.

OK. Writing final.

Let me also handle: what if `add_entities` appends dicts instead of strings? Then lookup_entity_index(dict) would fail. But the code suggests strings. Fine.

Let me write it out.

Also need to be careful: `_gen` writes the file. For n=0, `"\n".join([])` is `""`, plus `""` = `""`. Good.

Final code below.

Actually, let me reconsider the "checks" — they should be small edge inputs. Empty file, single line 6 fields, single line 8 fields. Good. They may raise (ours won't).

Also, I should make sure the checks files are distinct from cases files. Yes.

Let me write.

def _mk(path):
    return lambda: (_new_mind(), str(path))

Good.

Let me finalize the whole thing.