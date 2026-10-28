Let me think about this task.

The function `TrainDataset.__getitem__` reads from `self.queries`, `self.queries_ids`, `self.documents`. It mutates `query["positives"]` and `query["negatives"]` by popping the first element and appending it back — so the list is rotated. This means repeated calls on the same instance rotate the list, which is fine — it stays the same size, same elements. But the returned value depends on the order! Since we compare outputs after every call, we need... wait, the outputs are compared between the original function and the modified version on the same inputs. Each call gets the arguments of its own thunk call. If the thunk returns the same instance each time, the rotation state carries over between calls. But both original and modified are run on the same sequence, so as long as they rotate the same way, outputs match. Actually the comparison is between original and modified for each call — presumably they run each input many times on both, and compare.

Hmm, but careful: "Same work on every call". If the list rotates, each call does the same work (pop 0, append). The output differs across calls but that's the same for both versions. Actually to be safe, we could construct the instance fresh in each thunk. But building the dataset reads files and is expensive... Actually the dataset __init__ reads files, that's setup and it's fine (not timed). But building it in the thunk each call would be slow-ish but it's not timed. However thunks run before timing each iteration; building a large dataset each time might be slow. Let's build once at module level and return the same instance — the rotation is deterministic and identical for both versions.

Wait, but there's a subtlety: the rotation changes the state, so call 1 and call 2 return different outputs. The measurement harness compares original vs modified per call presumably by running them in lockstep or by running the original on the inputs, then modified. Either way, as long as the sequence of states is deterministic, both produce the same sequence. Actually, careful: if they run original many times in a row, then modified many times in a row, the state after original's N runs is rotated by N... and modified starts from the rotated state. Hmm, that could cause a mismatch if the harness doesn't reset.

To be safe, we should make the thunk reset the query lists to their original order before each call. That's cheap: for the query being accessed, we know which one. Actually simpler: create a fresh copy of the instance's queries... hmm.

Actually the cleanest: each thunk builds a fresh `TrainDataset`? That's reading files every call. Could be ok if files are small but for realistic scale (thousands of queries) it might be ~ tens of ms, and repeated many times → setup dominates but not timed, just wall-clock of the whole test. Might be acceptable but risky.

Alternative: build one instance at module level, and in each thunk, reset the state so that each call sees the same starting state. We can reset by restoring the original positives/negatives lists. We could precompute a deep copy of the queries dict and assign `instance.queries = copy.deepcopy(original)`? That's copying a dict of thousands of queries each call — expensive but not timed... but it's per-call overhead in wall clock. For 8 cases × many repetitions, deepcopy of large dict could be slow. Hmm.

Better: since the function only mutates the specific query it accesses (rotates its positives and negatives by one), and we control `item`, we can just rotate back after. But the thunk doesn't know what happened... Actually we can compute: for item i, the query is queries[queries_ids[i]]. Before the call, we could save that query's positives/negatives, and after the call restore them. But the thunk returns args; the call happens after. So we can't restore after within the thunk.

Option: In the thunk, before returning, ensure the query for that item is in its "canonical" state. We can do: restore the list order for that specific query. Since the function rotates by exactly one each call, if we always reset to canonical before each call, the state is deterministic.

Simplest robust approach: make the thunk set `instance.queries[qid]["positives"] = list(canonical_pos[qid])` and same for negatives, where qid is the item's query. That's a cheap O(len of that query's positives) copy — typically small (a few). Actually could be just 1-3 elements. That's cheap and resets state.

But actually, is resetting even needed? Let's think about the harness: "We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs." So each input (thunk) is run many times. For each input, original run many times, modified run many times, outputs compared. If they compare outputs across the runs, both would rotate identically IF they each start from the same state. But original runs first and rotates the state, then modified starts from rotated state → outputs differ. So yes, we need reset per call.

Hmm, but actually maybe the harness does a fresh copy... no, we can't rely on it. Let's just reset.

Actually, even simpler and safest: give each case its own instance built at module level, and have the thunk return `(instance, item)` after resetting the relevant query's lists. Let's do the reset.

But wait — a subtle issue: the reset itself modifies the instance before the call, and "its arguments are rendered before and after each call to see whether it changed them". The argument is the instance; rendering it fully might be expensive (it has a documents dict of thousands). Hmm, "keep each input's data under about 1 000 000 values". Rendering the instance's repr... Dataset doesn't define __repr__, so repr is default object repr — cheap! Actually rendering probably means some canonical serialization; for a custom object it may use repr. Fine.

Actually, hmm — "its arguments are rendered before and after each call to see whether it changed them" — the instance will change (queries lists rotate). That's expected and fine as long as it's the same for both versions. The comparison is between original and modified, so both change the same way. Good.

Now, about scale. The real workload: each __getitem__ does a dict lookup, pops, index, append — very cheap, O(1). One call takes microseconds, way under 1ms. The task wants 1ms-200ms per call ideally. We can't make it slower without changing the function's complexity. Hmm. But we must produce realistic inputs. The function is O(1). To get to ~1ms we'd need... it's just dict operations. Hard.

But the instructions say "One call should take roughly 1 ms to 200 ms". With O(1) operations this is impossible without huge... Actually, dict lookups on huge dicts are still O(1). The only cost scaling is hashing the key. Not enough.

Hmm. Maybe we can make the documents dict huge? No, lookup is O(1).

Actually, maybe we accept that the call is fast (microseconds). The instructions say "roughly 1 ms to 200 ms" but that's a guideline. Since we can't change the function, we just do the realistic thing. The measured work will be tiny. Let me just build realistic data.

Hmm, but then "keep the 4 that do the most work" — all do similar work. Whatever.

Wait — maybe there's a way: `self.queries_ids[item]` is a list index, `self.queries[...]` dict. All O(1). The pop(0) on a list of length 1 is O(1). If positives list is huge, pop(0) is O(n). But realistically positives lists are small (a few). We could make positives lists large to add work, but that's not realistic. Hmm, actually could be — some queries might have many positives? Not typical for training data.

Actually, pop(0) and append: if we make the positives list large (say 10000), pop(0) is O(n) = 10000 element shifts. That would be ~ tens of microseconds. Still not 1ms. With 1e6 elements, pop(0) is ~1ms. But that's unrealistic and the instruction warns against patterns. Hmm.

I think the honest approach: build a realistic dataset. The function is trivially fast. I'll make the data reasonably large so lookups involve large dicts (though O(1)). Let's not overthink; just produce 8 diverse cases with realistic data and varied item indices, varied positives/negatives lengths.

Actually, let me reconsider: to make it do "substantial work", maybe use large positives/negatives lists. In real training data from this repo (embedder auto training), each query has a positives list and negatives list. Often positives is 1, negatives could be a list. Let me keep them small-ish but varied: some queries with 1 positive, some with many negatives.

Given pop(0) shifts the list, having a large list makes it slower. Let's use varied sizes: e.g., positives list length 1-50, negatives length 1-100. That gives a bit of work but still tiny.

I'll just go with realistic scale. The 8 cases differ by: number of queries, number of documents, item index position (first, middle, last), positives/negatives lengths, and maybe a large case.

Let me design the data format:
- documents file: one JSON per line, `{"doc_id": ..., "text": ...}`.
- queries file: one JSON per line, `{"query_id": ..., "query": ..., "positives": [...], "negatives": [...]}`.

Wait, but the function does `self.queries[self.queries_ids[item]]`. queries_ids = list(self.queries.keys()). So item is an integer index into that list.

For the reset approach: I need to know the query id for a given item. Since queries_ids order = insertion order = file order, I can compute it. I'll build the instance and keep a reference to the original positives/negatives per query.

Actually, let me simplify: the reset. For each case, I'll precompute the instance and the canonical positives/negatives for the target query, then thunk does:

```python
def thunk():
    q = inst.queries[qid]
    q["positives"][:] = canon_pos
    q["negatives"][:] = canon_neg
    return (inst, item)
```

Hmm, but that mutates before the call, so the "before" render vs "after" render shows a change... same for both versions. Fine.

Actually wait — is it necessary? Let me reconsider. The rotation: pop(0) then append. So the list order rotates. After k calls, the list is rotated by k. The output at call k is determined by the rotated state. If original does calls 1..N then modified does calls 1..N starting from state after N rotations, outputs differ (rotated by N). Unless N is a multiple of the list length! If list length is L and N ≡ 0 mod L, then state returns to original. Not controllable.

So yes, reset is needed for safety. But hmm, does the harness actually compare per-call outputs, or aggregate? "compare their energy use and their outputs" — likely per call or per input. To be safe, reset.

Actually, an even simpler approach that avoids state issues: create the TrainDataset instance fresh in every thunk? The __init__ reads files with readlines and json.loads. For a dataset of, say, 5000 queries and 5000 docs, that's maybe 20ms per thunk call. Since thunks run before each timed call, and there are many repetitions... could be slow but acceptable? Risky if they run thousands of reps.

Let me do the reset approach — cleaner and cheap.

Hmm, but actually there's another consideration: does resetting count as "the function changes outside its arguments"? We're setting data, which is allowed. Good.

Let me also consider: the function reads `self.queries_ids` (a list), `self.queries` (dict), `self.documents` (dict). It doesn't read module globals. InputExample is from sentence_transformers — need it available. The task says import from train; train imports sentence_transformers. Is sentence_transformers installed? The task says "packages the repository already imports" — so presumably yes in the test environment. I'll trust it.

But importing `train` will import sentence_transformers, torch, etc. That might be heavy but fine. Actually, is torch available? If not, the import fails and we can't run. The task implies it's available since the repo uses it. I'll assume so.

Hmm, actually the instruction: "If the function cannot run here at all -- it needs network access, a remote service, credentials, special hardware, or a library that is not available". sentence_transformers is a library; if not available we'd have to say CANNOT RUN. But we're told to import it as shown. I'll assume it's available.

Now the returned InputExample — comparison. InputExample has `texts` attribute. Fine.

Let's write the files under WORKDIR.

Now build the data. Let me write helper:

```python
import json, random
from train import TrainDataset

def _make_data(n_docs, n_queries, doc_text_len, pos_len, neg_len, seed, outdir):
    rng = random.Random(seed)
    docs_path = outdir / "documents.jsonl"
    queries_path = outdir / "queries.jsonl"
    ...
```

Wait, but building files: "create them under WORKDIR". And "Generate stressful inputs". Each case can share the same files? The instance is what matters. But different cases should differ in data distribution. I'll create separate files per case.

Actually building files at module level for 8 cases with large data — keep under 10s total. Fine.

Let me define a function that creates the files and returns paths, then a thunk builds the TrainDataset (or we build at module level).

Let's decide sizes: documents ~ 20,000; queries ~ 20,000. Each line has text of ~200 chars. That's ~4MB per file, fine.

Actually to make cases "diverse", vary:
1. small dataset, item in middle
2. large documents, small queries
3. query with many positives (long list)
4. query with many negatives
5. item = 0 (first)
6. item = last
7. duplicate texts / repeated docs
8. large overall

Hmm, but honestly the function work is dominated by pop(0) on positives/negatives. So to create diverse "work", vary the lengths of positives/negatives lists.

Let me make it so that cases with large positives lists give more work.

Let me design: For each case, I build one instance with queries where the target query has a specific positives/negatives length.

But the instance is built from files. To have varied positives lengths per query, I can just set them in the file.

Simpler: I'll generate the files such that each query has positives of length p_i and negatives of length n_i, varied.

Let me write:

```python
def _build_dataset(dirpath, n_docs, n_queries, seed, pos_lens=None, neg_lens=None, text_size=200):
    rng = random.Random(seed)
    docs_path = dirpath / "documents.jsonl"
    queries_path = dirpath / "queries.jsonl"
    with open(docs_path, "w") as f:
        for i in range(n_docs):
            doc = {"doc_id": f"d{i}", "text": " ".join(rng.choice(WORDS) for _ in range(text_size))}
            f.write(json.dumps(doc) + "\n")
    with open(queries_path, "w") as f:
        for i in range(n_queries):
            p = pos_lens(i) if pos_lens else 1
            n = neg_lens(i) if neg_lens else 1
            query = {
                "query_id": f"q{i}",
                "query": " ".join(...),
                "positives": [f"d{rng.randrange(n_docs)}" for _ in range(p)],
                "negatives": [f"d{rng.randrange(n_docs)}" for _ in range(n)],
            }
            f.write(json.dumps(query) + "\n")
    return docs_path, queries_path
```

Then instance = TrainDataset(docs_path, queries_path) at module level.

For the reset, I need the canonical positives/negatives for the target item. I can read from the instance's queries before any call. Let's store for each case: (instance, item, qid, canon_pos, canon_neg).

qid = instance.queries_ids[item].

Then thunk:
```python
def make_thunk(inst, item):
    qid = inst.queries_ids[item]
    q = inst.queries[qid]
    canon_pos = list(q["positives"])
    canon_neg = list(q["negatives"])
    def thunk():
        q["positives"][:] = canon_pos
        q["negatives"][:] = canon_neg
        return (inst, item)
    return thunk
```

Wait, but `q` closure references the query dict. Fine.

Hmm, but there's a subtlety: `q["positives"][:] = canon_pos` — this replaces contents in place, keeping the same list object. Good.

Now, the function's returned value depends on canon order, so deterministic. 

But wait: the item might index into a query whose positives list has duplicates etc. Fine.

Now, one more issue: the function returns InputExample(texts=[...]). The docs' texts. Fine.

Now — item index: queries_ids is a list of query ids in insertion order. Item must be in range [0, len(queries_ids)). Choose item values like 0, n//2, n-1.

Let me now think about "checks()" — small edge inputs, may raise. E.g., empty dataset (no documents, no queries) → item 0 → IndexError. Or item out of range. But checks are "checked only for identical behaviour". They may raise. So:
- empty queries file, item 0 → IndexError.
- one query, one doc, item 0 → works.
- item = -1 (negative index) → works (last element).

But careful: checks build instances too — need files. I can reuse module-level built files or build tiny ones.

Actually, checks with empty queries: TrainDataset requires the files to exist. Create empty files. Fine.

Let me write checks:
1. ("empty-queries", instance with 0 queries, item 0) → IndexError.
2. ("single", instance with 1 query, 1 positive, 1 negative, item 0).
3. ("negative-index", item -1).

For the negative index case with a dataset that has queries.

Let me keep it simple: build a tiny dataset at module level for checks.

Now, potential problem: the `checks()` thunks also need reset. For single element, reset is trivial.

Let me now also consider: does the harness call `TrainDataset.__getitem__(instance, item)` — yes, method called as plain function with instance first.

Now about the size of positives/negatives lists to make work "substantial". pop(0) on a list of length L is O(L). Let's make some cases with L up to maybe 5000? That's 5000 pointer moves ~ few microseconds. Still tiny. Honestly the function is O(1)-ish. Let's just do realistic: positives typically 1, negatives maybe up to a few. I'll vary: some cases with positives length 1, some with 10, some with 100, negatives similar.

Hmm, but "complex, time-consuming" and "One call should take roughly 1 ms to 200 ms". Since impossible, I'll maximize where reasonable: make negatives lists longer (e.g., up to 2000) for some cases. Realistic? In embedding training, hard negatives per query are usually < 100. 2000 is unrealistic. But it does make the pop(0) do work. I'll use moderate values like up to 1000 for one case to add variety. Hmm, but that changes semantics of realistic data.

Let me not over-engineer. I'll use positives lengths like [1, 1, 2, 5, 1, 3, 10, 1] and negatives like [1, 2, 5, 1, 20, 50, 1, 100]. The work is dominated by dict lookups and list ops, all fast.

Hmm, wait. Actually, maybe I should reconsider making the data large so that the "rendering before/after" is heavy... no, that's not the measured function.

OK let me just write it. The key deliverable is correct, runnable code.

One concern: `TrainDataset.__init__` reads all lines with readlines() and json.loads. For 20000 docs + 20000 queries that's fine (~0.1s).

Memory: 8 cases × (20000 docs with 200-char text + 20000 queries) ≈ 8 × ~10MB = 80MB. Under 100MB? Maybe tight. Let me reduce: use 5000-15000 docs/queries per case, and shorter texts. Actually the task says "Keep the data in memory under about 100 MB". Let me use modest sizes: n_docs ~ 8000, n_queries ~ 8000, text of ~50 words (~300 chars). Each doc dict in memory ~ maybe 500 bytes + text 300 bytes. 8000 × 800 = 6.4MB per case. 8 cases = 51MB. Plus queries similar. Hmm.

Let me reduce to ~4000-6000 each. Total maybe 40MB. Fine.

Actually, do we even need documents to be huge? The lookup is O(1). The main point is realism. Let's use n_docs = 5000, n_queries = 5000 for most cases, varying.

Actually, I want diverse "work". Let me think about what varies the function's cost:
- Length of positives list (pop(0) shift).
- Length of negatives list (pop(0) shift).
- Hash cost of keys (string length) — negligible.

So the meaningful variation is list lengths. Let's vary those a lot: one case with positives length 1, one with 100, one with 2000; negatives similar. That gives real differences in work (2000-element list shift).

Also `self.documents[pos_id]` — dict lookup with string key; the doc_id strings could be long. Negligible.

I'll design 8 cases:

1. "typical": 5000 docs, 5000 queries, all pos len 1, neg len 1, item = middle.
2. "first-item": same data, item 0.
3. "last-item": item = n-1.
4. "many-negatives": target query has 2000 negatives, others 1. item targeting that query.
5. "many-positives": target query has 1000 positives.
6. "many-positives-negatives": target 500 pos + 500 neg.
7. "large-corpus": 20000 docs, 20000 queries, pos 1, neg 1.
8. "long-ids": doc ids long strings, many duplicates in positives? Hmm.

Actually to have the target query have a special length, I can set it per query in the generator via a function of index.

Let me restructure: generate queries with a `pos_len` and `neg_len` function. For case 4, make query at index `item` have 2000 negatives.

Simpler: I'll generate all queries with uniform pos_len/neg_len per case, except allow one special index. Actually simplest: just make ALL queries in a case have the same lengths. E.g., case "many-negatives" → all queries have 2000 negatives. That's unrealistic but simple, and the function does 2000-element pop each call. That gives the most work.

Hmm, but then the file would be huge: 5000 queries × 2000 negatives = 10M values → exceeds "under 1,000,000 values" for input rendering! Each input's data under ~1,000,000 values. So 5000 × 2000 = 10M > 1M. Too big.

So: if negatives length is 2000, number of queries must be ≤ 500. Let's do 200 queries × 2000 negatives = 400k values. OK.

But then rendering the instance (which includes all queries) — 400k values. Under 1M. OK. But it's rendered before and after every call, 400k values... that could be slow but not our concern? It might blow up the harness. Hmm. "keep each input's data under about 1,000,000 values" — so 400k is fine.

But rendering 400k values twice per call × many reps = heavy. Let's be conservative: keep each input under ~100k values maybe. Hmm.

Let me reconsider: total values per input = n_docs (each doc has doc_id + text = 2 values) + n_queries (each has query_id, query, positives list, negatives list). If positives/negatives are length ~1-10, then per query ~ 6 values. So 5000 queries × 6 = 30k. Plus 5000 docs × 2 = 10k. Total 40k. Fine.

For the "many-negatives" case: 200 queries × (2 + 2000) ≈ 400k. Plus docs. That's within 1M but heavy. Let's use 100 queries × 1000 negatives = 100k values. Good.

Let me set:
- Case with big negatives: 200 queries, neg_len 500 → 100k values.
- Case with big positives: 200 queries, pos_len 500 → 100k.

Hmm, pop(0) on 500-element list: ~500 shifts, nanoseconds. Tiny.

Honestly the whole thing is microseconds. Fine.

Let me now also reconsider whether we even need the documents to be large. The lookup `self.documents[pos_id]` is O(1). So doc count doesn't affect per-call time much. But realism: the repo has documents and queries files. I'll keep docs moderate.

Let me finalize a design that's simple and robust:

Module-level helper builds a dataset directory and returns (instance, item, reset info).

Actually, let me just write a function `_make_case(name, n_docs, n_queries, pos_len, neg_len, item, seed)` that:
- creates files under WORKDIR/name
- builds TrainDataset
- returns instance, item
and separately a `_reset_for(inst, item)` returning a thunk.

But different cases need different item positions. For "first", item=0; "middle", item=n//2; "last", item=n-1.

Also, we might want the item to select a query with specific structure. With uniform lengths, item doesn't matter much except index lookup position (list index O(1)). Fine.

Let me now write the code.

```python
import json
import random
from pathlib import Path

from train import TrainDataset

_WORDS = ["alpha", "beta", ...]  # word list

def _text(rng, n):
    return " ".join(rng.choice(_WORDS) for _ in range(n))

def _build(name, n_docs, n_queries, pos_len, neg_len, seed, doc_text_words=20, query_text_words=8):
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    docs_path = d / "documents.jsonl"
    queries_path = d / "queries.jsonl"
    rng = random.Random(seed)
    with open(docs_path, "w") as f:
        for i in range(n_docs):
            doc = {"doc_id": f"doc-{i}", "text": _text(rng, doc_text_words)}
            f.write(json.dumps(doc) + "\n")
    with open(queries_path, "w") as f:
        for i in range(n_queries):
            query = {
                "query_id": f"query-{i}",
                "query": _text(rng, query_text_words),
                "positives": [f"doc-{rng.randrange(n_docs)}" for _ in range(pos_len)],
                "negatives": [f"doc-{rng.randrange(n_docs)}" for _ in range(neg_len)],
            }
            f.write(json.dumps(query) + "\n")
    return TrainDataset(str(docs_path), str(queries_path))
```

Wait, `_build` returns instance. Then thunk needs reset info.

Let me define:

```python
def _thunk_for(inst, item):
    qid = inst.queries_ids[item]
    q = inst.queries[qid]
    canon_pos = list(q["positives"])
    canon_neg = list(q["negatives"])
    def thunk():
        q["positives"][:] = canon_pos
        q["negatives"][:] = canon_neg
        return (inst, item)
    return thunk
```

Now cases:

```python
def cases():
    out = []
    # 1 typical
    inst = _build("typical", 5000, 5000, 1, 1, 0)
    out.append(("typical-mid", _thunk_for(inst, 2500)))
    # 2 first item
    out.append(("first-item", _thunk_for(inst, 0)))
    # 3 last item
    out.append(("last-item", _thunk_for(inst, len(inst.queries_ids) - 1)))
    ...
```

Hmm, sharing `inst` across cases 1-3: they mutate the same instance but each thunk resets its own query. Different items → different queries → independent. OK. But case 1 and 2 share instance, no conflict. Fine.

Actually, to be safe and independent, maybe separate instances. But sharing is fine.

Let me define 8 distinct cases:

1. "typical": 5000 docs/queries, pos 1, neg 1, item mid.
2. "first-item": same instance, item 0.
3. "last-item": item last.
4. "long-negatives": 300 docs, 300 queries, pos 1, neg 1000, item mid.
5. "long-positives": 300 docs, 300 queries, pos 1000, neg 1, item mid.
6. "balanced-long": 500 docs, 500 queries, pos 200, neg 200, item mid.
7. "large-corpus": 30000 docs, 30000 queries, pos 1, neg 1, item mid.
8. "duplicate-negatives": 1000 docs, 1000 queries, pos 1, neg 50 with duplicates, item mid.

Hmm, case 7 with 30000 docs/queries — memory: 30000 docs × (doc_id ~10 chars + text ~150 chars) ≈ 30000 × 200 = 6MB. queries 30000 × ~200 = 6MB. Total 12MB. OK. Building takes maybe 0.5s. Fine.

Wait, "large-corpus" per-call time is still O(1). No difference. But realism.

Actually, maybe make case 7 use longer doc texts to stress JSON parsing? No, parsing is in __init__ (setup). Per-call, text isn't touched except being put in the returned InputExample. The returned value has references to strings, no copy. So cheap.

Alright.

Let me reconsider whether the returned InputExample could be large. It contains 3 strings. Fine, well under 100k values.

Now checks():

```python
def checks():
    # empty dataset
    inst_empty = _build("empty", 1, 0, 0, 0, 0)
    # wait, _build with n_queries=0 writes empty queries file
    ...
```

Hmm, `_build` with n_queries=0 → queries_ids empty → item 0 → IndexError. Good, that's a check that raises.

But `_thunk_for` would fail because inst.queries_ids[0] raises. So build the thunk manually for that:

```python
def checks():
    inst_empty = _build("check-empty", 2, 0, 0, 0, 1)
    inst_single = _build("check-single", 3, 1, 1, 1, 2)
    inst_multi = _build("check-multi", 5, 3, 2, 3, 3)
    return [
        ("empty-queries", lambda: (inst_empty, 0)),
        ("single", _thunk_for(inst_single, 0)),
        ("negative-index", _thunk_for(inst_multi, -1)),
    ]
```

Wait, `_thunk_for(inst_empty, 0)` raises during checks() construction. So use lambda returning (inst_empty, 0) — the error occurs when the function is called. Good.

Actually for "single", _thunk_for works (item 0 valid).

For "negative-index", item -1 → queries_ids[-1] = last query. Works.

Now, one concern: the empty dataset instance has n_docs=2 but n_queries=0. `_build` writes 0 queries. TrainDataset init: `self.queries_ids = list(self.queries.keys())` = []. Then __getitem__(inst, 0) → self.queries[self.queries_ids[0]] → IndexError. Good.

Now `_build` signature with pos_len/neg_len unused when n_queries=0. Fine.

Now about the reset: `q["positives"][:] = canon_pos`. If canon_pos is empty (pos_len=0)? For checks single, pos_len=1. For cases, all ≥1. But if a query had empty positives, `pop(0)` raises IndexError. The function would raise. Not in our cases. Fine.

Hmm, actually for checks, the "empty-queries" case raises at `self.queries_ids[item]` before any mutation. Fine.

Now let me double check `TrainDataset.__init__` signature: `__init__(self, documents: str, queries: str)` where documents is a path. So `TrainDataset(str(docs_path), str(queries_path))`.

Now the import: `from train import TrainDataset`. The module is at `examples/embedder-auto-training-evaluation/training-evaluation/train.py`. The task says import it as `from train import TrainDataset`. So presumably sys.path includes that dir. OK.

But wait — importing `train` will run `from sentence_transformers import ...` and `import torch`. Heavy but OK. And there's `def main()` at module level but not called. Good, no side effects.

Now let me also double-check: does `train.py` have module-level code that runs? The header shows only imports and function defs. Good.

Now, memory: 8 cases, each builds its own instance. Case 7 is 30000+30000. Others smaller. Total maybe 30-40MB. Should be OK.

Actually, let me reconsider case 4 "long-negatives": 300 queries × 1000 negatives = 300k negative values. Plus rendering... "keep each input's data under about 1,000,000 values". 300k is fine. But rendering the instance before/after each call = serializing 300k values twice per call. If reps are many, that's slow. Hmm. Let me reduce to 200 queries × 500 negatives = 100k. Better.

Similarly case 5: 200 queries × 500 positives = 100k.

Case 6: 500 queries × 200 pos + 200 neg = 500 × 400 = 200k. Reduce to 300 queries × 150+150 = 90k.

OK.

Actually, hold on. Let me reconsider the whole "reset" necessity more carefully, because it adds complexity and the mutation. Let me re-read: "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next... give every thunk call new keys... so every call takes the same path."

Here the function changes its argument (the instance). The guidance about copies: "have the thunk return it -- or a copy (`list(data)`, `dict(data)`) if the function changes it (adds to a dict, sorts or fills a list in place)."

So the intended approach is to return a copy of the mutated data! But here the argument is the instance, and copying the whole instance (with all documents/queries) each call is expensive... but not timed. Hmm. Actually copying the instance's queries dict deeply would be needed since it mutates nested lists. A shallow copy of the instance via copy.copy wouldn't isolate the nested query dicts. Need deepcopy → expensive but not timed.

Hmm. Alternatively, the reset approach is equivalent and cheap.

But wait — will the harness compare the instance's state? "Its arguments are rendered before and after each call to see whether it changed them". If we return the same instance each call and it mutates, the render changes. Both versions do the same, so comparison passes.

But there's a subtle risk: if the harness runs original N times, then modified N times, the "before" state for modified's first call is the state after original's N calls. If we reset in the thunk, then modified's first call starts from canonical. Original's first call also starts from canonical. So outputs match. Good — reset solves it.

Without reset, original's calls rotate; modified starts rotated → mismatch. So reset is important. 

Alternatively deepcopy the instance in the thunk. Let's just do reset — cheaper and clean.

Hmm, but actually, is the reset semantically "cheating"? No, it's just restoring data before the call, which is allowed ("Setting data ... to build an input is fine").

But wait, there's another subtlety: the reset sets the list contents, but the function also reads `self.queries` and `self.documents` which don't change. Fine.

Let me also make sure the thunk's reset happens before the timed call. Yes: "Thunks run before the timing starts".

Now, one more: the thunk returns `(inst, item)`. The harness calls `TrainDataset.__getitem__(inst, item)`. Good.

Let me write the final code.

Also need `random.Random(0)` fixed seed — I use rng = random.Random(seed) with fixed seeds. Good.

Let me write word list. Use a simple deterministic set.

Let me write:

```python
import json
import random

from train import TrainDataset

_WORDS = [
    "retrieval", "embedding", "sentence", "vector", "search", "model",
    "training", "evaluation", "document", "passage", "question", "answer",
    "neural", "network", "transformer", "encoder", "corpus", "index",
    "similarity", "distance", "query", "context", "token", "attention",
]


def _make_text(rng, n_words):
    return " ".join(rng.choice(_WORDS) for _ in range(n_words))


def _build_dataset(name, n_docs, n_queries, pos_len, neg_len, seed,
                   doc_words=30, query_words=10):
    folder = WORKDIR / name
    folder.mkdir(parents=True, exist_ok=True)
    docs_path = folder / "documents.jsonl"
    queries_path = folder / "queries.jsonl"
    rng = random.Random(seed)
    with open(docs_path, "w") as fh:
        for i in range(n_docs):
            doc = {"doc_id": f"doc-{i}", "text": _make_text(rng, doc_words)}
            fh.write(json.dumps(doc) + "\n")
    with open(queries_path, "w") as fh:
        for i in range(n_queries):
            query = {
                "query_id": f"query-{i}",
                "query": _make_text(rng, query_words),
                "positives": [f"doc-{rng.randrange(n_docs)}" for _ in range(pos_len)],
                "negatives": [f"doc-{rng.randrange(n_docs)}" for _ in range(neg_len)],
            }
            fh.write(json.dumps(query) + "\n")
    return TrainDataset(str(docs_path), str(queries_path))
```

Wait — n_docs could be 0? For checks empty we use n_docs=2. randrange(n_docs) with n_docs>0. Fine.

For the empty-queries check, n_docs=2, n_queries=0 → no randrange calls for positives. Good.

But if n_queries=0 and n_docs=2, fine.

Now `_thunk_for`:

```python
def _thunk_for(dataset, item):
    qid = dataset.queries_ids[item]
    query = dataset.queries[qid]
    original_positives = list(query["positives"])
    original_negatives = list(query["negatives"])

    def thunk():
        query["positives"][:] = original_positives
        query["negatives"][:] = original_negatives
        return (dataset, item)

    return thunk
```

Now cases. Let me carefully build.

```python
def cases():
    typical = _build_dataset("case-typical", 5000, 5000, 1, 1, 0)
    first = _build_dataset("case-first", 4000, 4000, 1, 1, 1)
    last = _build_dataset("case-last", 4000, 4000, 1, 1, 2)
    many_neg = _build_dataset("case-many-neg", 500, 200, 1, 500, 3)
    many_pos = _build_dataset("case-many-pos", 500, 200, 500, 1, 4)
    balanced = _build_dataset("case-balanced", 1000, 300, 150, 150, 5)
    large = _build_dataset("case-large", 30000, 30000, 1, 1, 6)
    dup_neg = _build_dataset("case-dup-neg", 2000, 1500, 1, 30, 7)
    ...
```

Hmm, for `first` and `last`, they're separate instances — no need to share. But then typical/first/last are similar work. That's fine; they differ by item position.

Wait, but `large` with 30000 docs and 30000 queries: building takes maybe 1s. Total build time for all cases must be under 10s. Let's estimate: case-large 30000 docs × 30 words ≈ 900k word picks + 30000 queries. Python: ~1-2s. Others smaller. Total maybe 4s. OK.

Memory: case-large: 30000 docs each ~30 words (~200 chars) → ~30000 × (dict overhead ~ 200 + strings 250) ≈ 13MB. queries 30000 × (query text + lists of 1+1) ≈ 30000 × 300 = 9MB. Total ~22MB for large. Others ~5MB each. Total maybe 40MB. OK.

Now thunks:

```python
    return [
        ("typical-mid", _thunk_for(typical, 2500)),
        ("first-index", _thunk_for(first, 0)),
        ("last-index", _thunk_for(last, len(last.queries_ids) - 1)),
        ("long-negatives", _thunk_for(many_neg, 100)),
        ("long-positives", _thunk_for(many_pos, 100)),
        ("balanced-long", _thunk_for(balanced, 150)),
        ("large-corpus", _thunk_for(large, 15000)),
        ("duplicate-negatives", _thunk_for(dup_neg, 750)),
    ]
```

For `first` item 0 and `last` item n-1 — both valid.

For many_neg: 200 queries, item 100 valid.
many_pos: 200 queries, item 100.
balanced: 300 queries, item 150.
large: 30000 queries, item 15000.
dup_neg: 1500 queries, item 750.

Good, 8 cases.

Now checks:

```python
def checks():
    empty = _build_dataset("check-empty", 3, 0, 0, 0, 10)
    single = _build_dataset("check-single", 4, 1, 1, 1, 11)
    multi = _build_dataset("check-multi", 6, 3, 2, 3, 12)
    return [
        ("empty-queries", lambda: (empty, 0)),
        ("single-item", _thunk_for(single, 0)),
        ("negative-index", _thunk_for(multi, -1)),
    ]
```

Wait, `_thunk_for(single, 0)` — single has 1 query, item 0 valid. Its positives has 1 element. The function pops it, appends it. Fine.

`_thunk_for(multi, -1)` — item -1 → queries_ids[-1] = "query-2". Valid. pos_len 2, neg_len 3.

Now, "empty-queries" thunk returns (empty, 0) without reset (no query). Calling the function raises IndexError. The task says checks may raise. But does the harness expect it to raise on both original and modified identically? Yes, identical behaviour. Good.

Hmm, one issue: `_build_dataset("check-empty", 3, 0, 0, 0, 10)` — pos_len=0, neg_len=0 but n_queries=0 so unused. Fine.

Now, potential issue: `WORKDIR` — provided, don't define. Use it directly at module level in `_build_dataset` (called at module level? No — `_build_dataset` is called inside `cases()` and `checks()`, which are called by the harness). Actually the task says files can be created "in module-level code or in the thunk". Since cases() is called before timing, building inside cases() is fine (it's setup). Actually, is cases() itself part of setup? Yes — "Thunks run before the timing starts". The cases() function returns thunks; building data inside cases() happens when cases() is called, which is setup. Good.

Hmm, but is it safer to build at module level? The instructions say setup can be in module-level code or in the thunk. cases() body is neither exactly... but it's called to produce the thunks, before timing. I think it's fine — the example does `_rows(...)` inside `cases()`? No, the example calls `_rows(2000,4,0)` inside the lambda (thunk). Hmm. Actually in the first example, `_rows` is called inside the thunk: `lambda: (_rows(2_000, 4, 0),)`. In the second example, `Index(_VOCAB)` is inside the thunk too.

Hmm. So building data inside cases() body (not in thunk) — is that acceptable? The data would be built once when cases() is called, then reused across thunk calls. That's exactly what we want for expensive setup. The instruction says "build large data once, in module-level code, and have the thunk return it". So module-level is the suggested place. cases() body runs at setup time too (cases() is called before timing). I think it's fine and equivalent.

But to be safe and match guidance, maybe build at module level. But module-level building of 8 datasets with heavy work might be slow at import... but that's setup. However, module-level code runs even if checks() is called without cases()? Both are needed. Module-level building always runs. That's fine.

Actually, there's a risk: if module import fails... no.

I'll build inside cases()/checks() — it's cleaner and only runs when needed. The harness calls cases() once. Good.

Hmm, but wait: could the harness call cases() multiple times (e.g., once to get the list, and maybe again)? If called multiple times, each call rebuilds datasets → new instances → different items but same data. Fine, just slower.

Actually, there's a subtlety with `_thunk_for` closure and re-calling cases(): each call creates new closures over new instances. Fine.

Let me reconsider: is it a problem that the data files are written each time cases() is called? They're overwritten. Fine.

I'll go with building inside cases().

Hmm, one more consideration: "Prepare the way the repository's own callers do". The repo does `TrainDataset(args.documents, args.queries)`. We do the same with paths. Good.

Now, does the function need `InputExample` importable? It's imported in train.py. Good.

Let me double-check the returned value: `InputExample(texts=[{"query": ...}, {"doc": ...}, {"doc": ...}])`. Fine.

Now let me reconsider the "many negatives" case: pos_len=1, neg_len=500, n_queries=200. Each query has 500 negatives. Total negative values = 100k. Rendering... fine.

But the per-call work: pop(0) on 500-element list → 500 shifts. Still microseconds.

Alright, I'm fairly confident. Let me also think about whether `_thunk_for`'s reset correctly restores state given the function pops and appends. The function does pop(0) then append, so list rotates left by 1. Our reset sets list contents to original order. So each call starts from the same order. Deterministic. 

But note: `query["positives"][:] = original_positives` — this is a slice assignment, replacing all elements. It keeps the same list object (important since the function holds no long-lived reference... actually it does `query["positives"].pop(0)` which uses the list object from the dict, so identity doesn't matter, but keeping it is fine).

Now, the reset runs before the timed call — but does the harness time only the function call, or the thunk + call? "Thunks run before the timing starts; only the call of the function is timed." Good.

Now, potential issue: the harness "renders arguments before and after each call". The arguments are `(dataset, item)`. Rendering the dataset might be expensive. For case-large, rendering 30000 queries + 30000 docs... that's 60000 objects. If it's a repr-based render, Dataset has default repr (object id) → cheap. If it's a deep serialization, expensive. Hmm. The instruction says "Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1,000,000 values." So they do count values. case-large: 30000 docs × 2 + 30000 queries × ~6 = 60k + 180k = 240k. Under 1M. OK.

But rendering 240k values twice per call... if reps = 100, that's 48M value renders. Could be slow but presumably the harness handles it.

Hmm, let me reduce case-large to 20000 to be safe. 20000×2 + 20000×6 = 160k. Fine.

Actually let me keep it moderate: 15000 docs, 15000 queries.

Let me reconsider: does the instance's `__dict__` include `documents`, `queries`, `queries_ids`. Rendering would include all. 15000 docs × 2 + 15000 queries × (query_id, query, positives list, negatives list) → 15000×2 + 15000×4 = 90k values. Fine.

Now the duplicate-negatives case: 2000 docs, 1500 queries, neg_len 30 with duplicates. Total 1500×30 = 45k. Fine.

OK. Let me also vary doc text lengths for diversity.

Let me finalize.

One more thought: Should I worry that `TrainDataset.__init__` uses `file.readlines()` — reading the whole file. For 15000 lines that's fine.

Also: the documents file uses `doc_id` keys as `doc-{i}`, and queries reference `doc-{rng.randrange(n_docs)}`. Good.

Let me write the final code.

Also, I should double check: `random.Random(seed)` — seeds are fixed integers. Good, deterministic.

Potential issue: `_build_dataset` called multiple times with the same name would reuse folder; but names are distinct.

Let me write it out.

```python
import json
import random

from train import TrainDataset


_WORDS = [
    "retrieval", "embedding", "sentence", "vector", "search", "model",
    "training", "evaluation", "document", "passage", "question", "answer",
    "neural", "network", "transformer", "encoder", "corpus", "index",
    "similarity", "distance", "query", "context", "token", "attention",
    "language", "learning", "semantic", "ranking", "relevant", "candidate",
]


def _text(rng, n_words):
    return " ".join(rng.choice(_WORDS) for _ in range(n_words))


def _build_dataset(name, n_docs, n_queries, pos_len, neg_len, seed,
                   doc_words=30, query_words=10):
    folder = WORKDIR / name
    folder.mkdir(parents=True, exist_ok=True)
    docs_path = folder / "documents.jsonl"
    queries_path = folder / "queries.jsonl"

    rng = random.Random(seed)
    with open(docs_path, "w") as fh:
        for i in range(n_docs):
            fh.write(json.dumps({"doc_id": f"doc-{i}",
                                 "text": _text(rng, doc_words)}) + "\n")

    with open(queries_path, "w") as fh:
        for i in range(n_queries):
            query = {
                "query_id": f"query-{i}",
                "query": _text(rng, query_words),
                "positives": [f"doc-{rng.randrange(n_docs)}" for _ in range(pos_len)],
                "negatives": [f"doc-{rng.randrange(n_docs)}" for _ in range(neg_len)],
            }
            fh.write(json.dumps(query) + "\n")

    return TrainDataset(str(docs_path), str(queries_path))


def _thunk_for(dataset, item):
    query = dataset.queries[dataset.queries_ids[item]]
    original_positives = list(query["positives"])
    original_negatives = list(query["negatives"])

    def thunk():
        query["positives"][:] = original_positives
        query["negatives"][:] = original_negatives
        return (dataset, item)

    return thunk
```

Wait: for the empty dataset check, `_thunk_for` can't be used (item invalid). Use a plain lambda.

Now cases:

```python
def cases():
    typical = _build_dataset("case-typical", 6000, 6000, 1, 1, 0)
    first = _build_dataset("case-first", 5000, 5000, 1, 1, 1)
    last = _build_dataset("case-last", 5000, 5000, 1, 1, 2)
    many_neg = _build_dataset("case-many-neg", 800, 200, 1, 500, 3)
    many_pos = _build_dataset("case-many-pos", 800, 200, 500, 1, 4)
    balanced = _build_dataset("case-balanced", 1500, 400, 120, 120, 5)
    large = _build_dataset("case-large", 15000, 15000, 1, 1, 6)
    dup = _build_dataset("case-dup-neg", 3000, 2000, 1, 40, 7)

    return [
        ("typical-mid", _thunk_for(typical, 3000)),
        ("first-index", _thunk_for(first, 0)),
        ("last-index", _thunk_for(last, len(last.queries_ids) - 1)),
        ("long-negatives", _thunk_for(many_neg, 100)),
        ("long-positives", _thunk_for(many_pos, 100)),
        ("balanced-long", _thunk_for(balanced, 200)),
        ("large-corpus", _thunk_for(large, 7500)),
        ("duplicate-negatives", _thunk_for(dup, 1000)),
    ]
```

Note: `first` case item 0, `last` case item n-1. Distinct instances so no shared state issue.

Hmm, but for "duplicate-negatives", the negatives are drawn randomly from 3000 docs with neg_len 40 — duplicates likely. Good.

Now checks:

```python
def checks():
    empty = _build_dataset("check-empty", 3, 0, 0, 0, 10)
    single = _build_dataset("check-single", 4, 1, 1, 1, 11)
    multi = _build_dataset("check-multi", 6, 3, 2, 3, 12)

    return [
        ("empty-queries", lambda: (empty, 0)),
        ("single-item", _thunk_for(single, 0)),
        ("negative-index", _thunk_for(multi, -1)),
    ]
```

That's 3 checks. Good.

Wait, for "single-item": single has 1 query with positives=[doc-x], negatives=[doc-y]. The function works. Good.

For "negative-index": multi has 3 queries, item -1 → last query, pos_len 2, neg_len 3. Works.

I think this is good. Let me double check `_build_dataset` when n_queries=0: the queries file is empty; TrainDataset init reads empty → queries={} → queries_ids=[]. Good.

One concern: `_text(rng, doc_words)` with doc_words=30 and 6000 docs → 180k word picks. Fine.

Also for case-large 15000 docs × 30 words = 450k picks. Fine.

Total word picks across all: maybe 1.5M. Building time maybe 2-3s. Under 10s. OK.

Let me also ensure the queries' `positives` and `negatives` reference valid doc ids (0..n_docs-1). Yes.

Now — is there any chance the function mutates `self.documents`? No. Only the query's lists.

Final concern: The `query` closure in `_thunk_for` — for cases sharing an instance? Each case builds its own instance, so no cross-case interference. Good.

Actually wait, `first` and `last` are separate instances built with the same parameters but different seeds — fine.

Let me reconsider whether we should reset at all, given potential harness behavior. If the harness deep-copies inputs before each call (to compare before/after), then our reset is still fine. If it doesn't copy, reset is essential. Either way, reset is safe.

But hold on: if the harness copies the arguments before calling, then the copy it passes is a copy of our dataset — a deepcopy. Then the mutation happens on the copy, and our reset on the original wouldn't matter... but then each call gets a fresh copy from the original (unmutated, since we reset). Either way fine.

Hmm, but if the harness deep-copies, the deepcopy of a large dataset per call is expensive. Not our problem.

OK, writing final answer.

Actually, let me reconsider one thing: the harness says "each input many times in a row". If it deep-copies the args each time from our returned thunk result, and our thunk resets the original each time, then each copy is canonical → deterministic. Good.

I'm confident. Let me also add a guard: the returned tuple must be positional args. `(dataset, item)` → `TrainDataset.__getitem__(dataset, item)`. Correct.

Let me finalize.

One last thing: should I worry about `import train` failing because sentence_transformers isn't installed? The task explicitly says import it as `from train import TrainDataset`, implying it works. I'll go with it.

Write final.