Let me analyze the function under test.

`create_coding_name_dframe(self, coding, coding_name_value, is_hierarchical)`.

It's an instance method. The instance is `DXDatasetDictionary`. But constructing DXDatasetDictionary requires a descriptor and calls load_data_dictionary, load_coding_dictionary, load_entity_dictionary — which may need network/dxpy. Actually the test uses patch.object to avoid. But we can't use mocks.

However, the method only uses `self`... let me check. Actually it doesn't use `self` at all! It only uses `coding`, `coding_name_value`, `is_hierarchical`, `pd`, `CODING_PAGINATED_KEY`. So we can create the instance without calling `__init__`? Hmm, but the instructions say "a method is called as a plain function: the thunk builds the instance and passes it as the first argument". We could use `object.__new__(DXDatasetDictionary)` to build an instance without running `__init__`. That's not a mock — it's a real instance of the class, just not initialized. Hmm, is that acceptable? It's a legitimate way to build an instance. The instructions warn against mocks and subclasses overriding methods. `object.__new__` is fine — it's a real DXDatasetDictionary instance.

Actually, could we construct DXDatasetDictionary properly? It needs a descriptor. `DXDatasetDescriptor.__init__(self, dxfile, **kwargs)` — needs a dxfile. That would need network. So no.

But wait — the function doesn't use self, so an uninitialized instance works. Let me be careful: is there any attribute access on self? Reviewing the code... no. Only local variables. Good.

So the thunk: `lambda: (DXDatasetDictionary.__new__(DXDatasetDictionary), coding, coding_name_value, is_hierarchical)`.

Hmm, but `object.__new__` on a class... `DXDatasetDictionary.__new__(DXDatasetDictionary)` works.

Now the coding shape. Two branches: hierarchical and non-hierarchical.

Hierarchical: coding has "display" (list of nodes; nodes are either dict {code: [children]} or terminal code strings), "codes_to_meanings" dict, "codes_to_concepts" dict (optional).

Non-hierarchical: coding has "codes_to_meanings" dict, optional "display" list, optional "codes_to_concepts".

Paginated: coding.get(CODING_PAGINATED_KEY) truthy → drop display_order.

Output: DataFrame with columns code, parent_code (hierarchical), meaning, concept, display_order, coding_name.

Now let's design 8 cases with substantial work. Let's aim for ~1ms-200ms each. Creating a DataFrame with e.g. 50k rows is a decent workload. The non-hierarchical branch uses `display.index(c)` for each code — that's O(n*m) — very slow if display is large! `display.index` is O(len(display)) per code. So if codes and display are both large, that's quadratic. With 20k codes and 20k display, that's 4*10^8 operations — way too slow (>1s). So we need to be careful with non-hierarchical cases with display present.

Actually for the non-hierarchical branch, `c in display` is also O(n). So each code is O(n). With n codes and n display, O(n^2). Keep small: e.g. 2000 codes and 2000 display → 4*10^6 index operations, plus building. Might be ~ tens of ms. Let's test mentally: Python list.index on 2000 elements ~ maybe 100ns per comparison... 4M comparisons ~ 0.4s worst case. Hmm, that could be too slow. But typically the code is found early? If display contains the code, index finds it at some position. Average position n/2. So 2000*1000 = 2M comparisons ~ maybe 0.1-0.2s. Borderline.

Let's use smaller: 1000 codes with 1000 display → 1M comparisons ~ 0.05s. Fine.

Alternatively, make display small or absent. If display absent, `display = []`, and `c in []` is fast. So non-hierarchical without display is fast.

Let's design cases:

1. Hierarchical large: display tree with many nodes, e.g. 20000 codes. Build nested structure. codes_to_meanings for all, codes_to_concepts partial.

2. Hierarchical with deep nesting (recursion depth) — the recursive generator. Deep nesting could hit recursion limit. Keep depth modest (~50-100).

3. Hierarchical with concepts missing for many codes (None).

4. Non-hierarchical large, no display: 50000 codes → codes_to_meanings dict of 50k, display empty. display_order all None. That's fast-ish: building 50k lists. DataFrame construction of 50k rows ~ maybe 10-30ms.

Wait, if display is empty, `"display_order"` is in dcols (list of None), then pd.array([None]*n, dtype="Int64") → all NA. Then DataFrame. Fine.

5. Non-hierarchical with display: 1000 codes, display = shuffled list of those codes, some codes not in display → None. Quadratic but manageable.

6. Paginated hierarchical: CODING_PAGINATED_KEY set → display_order popped.

7. Paginated non-hierarchical.

8. Mixed: codes_to_concepts ordered differently, omitting codes.

Also "codes_to_meanings" values — strings.

Let me think about the hierarchical display format. From the code:

```
for node in nodes:
    if isinstance(node, dict):
        next_parent_code, child_nodes = next(iter(node.items()))
        yield next_parent_code, parent_code, displ_ord
        recurse(child_nodes, next_parent_code)
    else:
        yield (node, parent_code, displ_ord)
```

So display is a list where each element is either a code string (terminal) or a dict mapping a code to a list of children.

Let's build a tree. A helper to generate.

Let me write a builder that creates a random hierarchy.

```python
def _build_display(rng, n_nodes):
    # returns (display_list, all_codes)
```

Simplest: create a root list with several top-level dicts and terminals.

Let me generate: top-level has `k` items; each item either terminal or dict with children. Recursively.

I'll write:

```python
def _make_tree(rng, count):
    """Return (nodes, codes) building a hierarchy with `count` total codes."""
    nodes = []
    codes = []
    # distribute
    ...
```

Let me do a recursive function that consumes a budget.

```python
def _make_nodes(rng, budget):
    nodes = []
    while budget > 0:
        # decide terminal or internal
        if budget == 1 or rng.random() < 0.5:
            code = "c%d" % _code_counter()  # need unique codes
            nodes.append(code)
            budget -= 1
        else:
            # internal with children
            children_budget = rng.randint(1, max(1, budget - 1))
            child_nodes, child_codes = _make_nodes(rng, children_budget)
            code = next_code()
            nodes.append({code: child_nodes})
            budget -= 1 + children_budget
    return nodes
```

Hmm, budget bookkeeping. Let me simplify: use a global counter for unique codes and a recursive builder with max depth.

Actually simpler approach: build a random tree with a fixed number of nodes using a stack.

Let me write:

```python
def _make_hierarchy(rng, n_codes, max_children=8):
    codes = ["code_%d" % i for i in range(n_codes)]
    rng.shuffle(codes)
    idx = 0
    def build(n):
        nonlocal idx
        nodes = []
        while n > 0:
            if n == 1 or rng.random() < 0.4:
                nodes.append(codes[idx]); idx += 1; n -= 1
            else:
                c = codes[idx]; idx += 1
                child_n = rng.randint(1, min(max_children, n - 1))
                children = build(child_n)
                nodes.append({c: children})
                n -= 1 + child_n
        return nodes
    nodes = build(n_codes)
    return nodes, codes
```

Wait recursion: `build(child_n)` consumes child_n + ... but it might consume less than requested? The while loop runs while n>0 and always decreases n by at least 1 each iteration. For internal: n -= 1 + child_n where child_n <= n-1, so n decreases by at least 1. It could exit with n > 0? No: the loop continues while n>0, and each iteration reduces n. But for internal case, n -= 1 + child_n; child_n = rng.randint(1, min(max_children, n-1)) so 1+child_n <= n. So n becomes >= 0. If n becomes 0, loop exits. If n>0 continues. So build(n) consumes exactly n codes. Good.

But careful with `idx`: total codes consumed = n. Good.

However recursion depth: with max_children=8 and n large, depth could be large-ish but bounded by log-ish. Actually worst case each internal has 1 child → depth = n. With random, unlikely but possible. Let's cap depth by passing depth param. Simpler: use max_children and probabilistic; depth ~ log_2. Fine for n=20000? Depth maybe ~20-30. OK.

Actually to be safe, let me limit recursion depth explicitly.

Let me just do a breadth-first construction to control depth. Hmm, but display is a nested list; BFS construction is doable.

Alternative: build a tree where depth is limited. Let me do:

```python
def _make_hierarchy(rng, n_codes, max_depth=6, max_children=10):
    codes = ["code_%d" % i for i in range(n_codes)]
    rng.shuffle(codes)
    idx = [0]
    def build(n, depth):
        nodes = []
        while n > 0:
            take_terminal = (n == 1) or depth >= max_depth or rng.random() < 0.35
            if take_terminal:
                nodes.append(codes[idx[0]]); idx[0] += 1; n -= 1
            else:
                c = codes[idx[0]]; idx[0] += 1
                child_n = rng.randint(1, min(max_children, n - 1))
                children = build(child_n, depth + 1)
                nodes.append({c: children})
                n -= 1 + child_n
        return nodes
    return build(n_codes, 0), codes
```

Good.

Now codes_to_meanings: dict code -> meaning string.

codes_to_concepts: partial dict, some codes → concept id.

Now the output size: for 20000 codes, DataFrame has 20000 rows × 6 cols = 120k values. The instruction says keep what it returns under ~100,000 values. Hmm, 20000 rows × 6 columns = 120,000 values. Slightly over. Let's use 15000 codes → 90,000 values. OK.

Actually "under about 100 000 values" — approximate. Let's use 12000 → 72000. Safe.

For non-hierarchical, 5 columns (code, meaning, concept, display_order, coding_name). 20000 × 5 = 100000. Let's use 15000 → 75000.

Now timing: DataFrame construction of 15k rows with 6 columns — maybe 5-15 ms. That's fine, above 1ms.

But to make it more substantial, we could go bigger. Let's aim ~50k rows? 50k×6=300k values — over the limit. Hmm. The limit is on returned values. So cap at ~16k rows for 6 columns.

Hmm, but they say "One call should take roughly 1 ms to 200 ms". 15k rows should be ~10ms. Fine.

Actually, the hierarchical branch does `coding["codes_to_meanings"][c] for c in all_codes` — dict lookups, fast. The main cost is DataFrame construction and pd.array.

Let's think about what makes different work:
- hierarchical vs non-hierarchical
- paginated vs not (pop display_order, skip pd.array)
- display present vs absent in non-hierarchical
- large vs small
- concepts present vs absent

Let me now design 8 cases:

1. `hier-large`: hierarchical, 15000 codes, deep-ish tree, concepts for ~half.
2. `hier-wide`: hierarchical, 15000 codes, wide tree (many children per node).
3. `hier-paginated`: hierarchical, 12000 codes, paginated=True.
4. `hier-no-concepts`: hierarchical, 12000 codes, codes_to_concepts empty.
5. `flat-large`: non-hierarchical, 15000 codes, no display.
6. `flat-display`: non-hierarchical, 1200 codes with display list of 1200 (shuffled), some codes missing from display.
7. `flat-paginated`: non-hierarchical, 15000 codes, no display, paginated.
8. `flat-concepts-misaligned`: non-hierarchical, 15000 codes, codes_to_concepts ordered differently and partially omitting.

Hmm case 6 is small (1200 codes) — work is quadratic: 1200*600 avg = 720k comparisons. That may be ~30-70ms. Good, that's substantial and different.

Actually let me reconsider: `display.index(c)` — display is a list of 1200 strings. `.index` does `==` comparisons. String comparison of short strings is fast. 1200*600 = 720k → maybe 20ms. Fine.

Let's make it a bit bigger: 2000 codes, display 2000. 2000*1000=2M → ~60ms. But output: 2000×5=10000 values. Fine. Input values: codes_to_meanings 2000 + display 2000. Fine.

Hmm but risk of exceeding 1s? 2M string comparisons ~ 0.1-0.2s. Should be OK. Let's use 1500 to be safe. Actually let's just use 2000; it's fine.

Wait, also `c in display` is O(n) then `.index(c)` O(n) — double. So 2*2M = 4M comparisons. ~0.2-0.4s. Hmm, that might approach 1s? Probably not. Let me use 1500 codes → 1500*750*2 = 2.25M → ~0.15s. Safe.

Actually, we want each case 1ms-200ms. 0.15s = 150ms is within. But it's the max. Let me use 1200 to be safer: 1200*600*2 = 1.44M → ~0.1s. Good.

Hmm, but actually maybe the string comparisons are slower. Let's use 1000: 1000*500*2 = 1M → ~0.07s. Fine.

Let me just pick 1500 and hope. Actually, let me be conservative: 1000 codes with 1000 display.

Hmm, but I want diversity in sizes. Fine.

Let me reconsider: maybe make display large but codes small? The work is len(codes)*len(display). To keep the quadratic, use codes=1000, display=5000 → 5M. Eh. Let's keep it simple.

Now, checks(): 2-3 small edge inputs.
- empty coding non-hierarchical: `{}`? Then `coding["codes_to_meanings"]` → KeyError. That raises. But checks may raise. Hmm, but better to have one that runs: `{"codes_to_meanings": {}}` → codes=[], display_order=[], pd.array([], dtype Int64), coding_name=[]. DataFrame empty. Then `dcols["coding_name"] = [name]*0 = []`. Works. Actually `zip(*unpack_hierarchy(...))` with empty display for hierarchical → `zip(*[])` → error? `zip(*[])` raises TypeError: not enough arguments for format... Actually `zip(*[])` = `zip()` which yields nothing, and unpacking into 3 variables raises ValueError. So empty hierarchical display raises. Good as an edge case.

Checks:
- ("empty-flat", lambda: (inst, {"codes_to_meanings": {}}, "c", False))
- ("empty-hier", lambda: (inst, {"display": [], "codes_to_meanings": {}}, "c", True)) — raises ValueError
- ("single", lambda: (inst, {"codes_to_meanings": {"a": "A"}}, "c", False))

Actually the third duplicates a case. Fine, checks aren't measured.

Hmm, but checks must run — "checked only for identical behaviour, never measured. These may raise." So raising is fine.

Now let's think about the instance. `DXDatasetDictionary.__new__(DXDatasetDictionary)`.

But wait — importing `from dxpy.cli.dataset_utilities import DXDatasetDictionary` will import the whole module, which imports dxpy, DXRecord, etc. That should be importable? dxpy is a local package. The module imports `dxpy` and various submodules. It might do network at import? Unlikely. But `from ..bindings.dxfile import DXFile` — DXFile class body has `_http_threadpool = dxpy.utils.get_futures_threadpool(...)` at class definition time. That creates a threadpool — should be fine, no network.

Also `dxpy` import itself: `import dxpy` — the top-level package. Should be fine.

Let me check: does importing dataset_utilities require anything special? It imports `from ..utils.resolver import ...` etc. Probably fine.

We need `pd` — pandas. The function uses `pd`. It's imported in the module presumably as `import pandas as pd`. We don't need to import pandas ourselves, but we might for nothing. Actually we don't need it.

Now, the thunk builds instance and passes it. Since the function doesn't mutate the instance, we can reuse a single instance across all thunks. Create it at module level? But module-level code runs at import; `DXDatasetDictionary.__new__` is cheap. Let's create `_INSTANCE = DXDatasetDictionary.__new__(DXDatasetDictionary)` at module level. Actually better to create in thunk to be safe? Module-level is allowed ("everything that builds data, objects or files goes in the thunk or in module-level code").

Hmm, but does `__new__` work? `object.__new__(DXDatasetDictionary)`. Yes.

Wait, is there any chance the class defines `__new__`? Not shown. Fine.

Alternatively, we could avoid the instance issue entirely by... no, we must pass an instance.

Now let's think: does the function modify `coding`? It reads `coding.get(...)`, `coding["display"]`, `coding["codes_to_meanings"]`. No mutation. So we can reuse the same coding dict across calls. Good — build once at module level.

But careful: `dcols` is local. No mutation of inputs. Good.

However, `pd.array(dcols["display_order"], dtype="Int64")` — creates new. Fine.

So thunks can just return the same prebuilt objects.

Let me now write the code.

```python
import random
from dxpy.cli.dataset_utilities import DXDatasetDictionary

_INSTANCE = DXDatasetDictionary.__new__(DXDatasetDictionary)
```

Hmm, `DXDatasetDictionary.__new__(DXDatasetDictionary)` — calling `__new__` on the class. Actually `object.__new__` is what's inherited. `DXDatasetDictionary.__new__(DXDatasetDictionary)` works.

Now builders.

```python
def _make_hierarchy(rng, n_codes, max_depth=6, max_children=10):
    codes = ["code_%d" % i for i in range(n_codes)]
    rng.shuffle(codes)
    idx = [0]
    def build(n, depth):
        nodes = []
        while n > 0:
            if n == 1 or depth >= max_depth or rng.random() < 0.35:
                nodes.append(codes[idx[0]]); idx[0] += 1; n -= 1
            else:
                c = codes[idx[0]]; idx[0] += 1
                child_n = rng.randint(1, min(max_children, n - 1))
                children = build(child_n, depth + 1)
                nodes.append({c: children})
                n -= 1 + child_n
        return nodes
    return build(n_codes, 0), codes
```

Wait, there's a bug: when depth >= max_depth, we take terminal — good. But `n == 1` terminal. Good.

Hmm, but `rng.random() < 0.35` — with max_children=10, an internal node consumes 1+child_n up to 11. Fine.

Then meanings:

```python
def _meanings(codes, rng, prefix="Meaning"):
    return {c: "%s for %s" % (prefix, c) for c in codes}
```

Concepts:

```python
def _concepts(codes, rng, ratio, offset=0):
    return {c: "concept_%d" % (i + offset) for i, c in enumerate(codes) if rng.random() < ratio}
```

Now cases.

Case 1: hierarchical large.
```python
_rng = random.Random(0)
_disp1, _codes1 = _make_hierarchy(_rng, 15000, max_depth=6, max_children=10)
_coding1 = {
    "display": _disp1,
    "codes_to_meanings": {c: "Meaning of %s" % c for c in _codes1},
    "codes_to_concepts": {c: "concept_%d" % i for i, c in enumerate(_codes1) if _rng.random() < 0.5},
}
```

Case 2: hierarchical wide.
```python
_disp2, _codes2 = _make_hierarchy(_rng, 15000, max_depth=3, max_children=40)
```
Hmm max_children=40 with max_depth=3 → up to 40^3 = 64000 > 15000, fine.

Case 3: hierarchical paginated.
```python
_disp3, _codes3 = _make_hierarchy(_rng, 12000, max_depth=5, max_children=12)
_coding3 = {..., CODING_PAGINATED_KEY: True}
```
Need CODING_PAGINATED_KEY = "_dx_paginated". I can import it or hardcode. Import it: `from dxpy.cli.dataset_utilities import CODING_PAGINATED_KEY`. Or just use "_dx_paginated". Let's import to be safe. Actually the key value is given in the task: `CODING_PAGINATED_KEY = "_dx_paginated"`. Import it.

Case 4: hierarchical no concepts.
```python
_disp4, _codes4 = _make_hierarchy(_rng, 12000, max_depth=8, max_children=6)
_coding4 = {"display": _disp4, "codes_to_meanings": {...}, "codes_to_concepts": {}}
```

Case 5: flat large no display.
```python
_codes5 = ["fcode_%d" % i for i in range(15000)]
_coding5 = {"codes_to_meanings": {c: "m %s" % c for c in _codes5}}
```
Note: no "display" key → `coding.get("display") or []` → []. display_order = [None]*15000. Then pd.array Int64 all NA.

Hmm wait — is that realistic? The repository's non-hierarchical coding usually has display. But it's fine as a case.

Actually, maybe more realistic: flat coding without display happens when paginated. Let's keep it.

Case 6: flat with display (quadratic).
```python
_codes6 = ["dcode_%d" % i for i in range(1000)]
_display6 = list(_codes6)
_rng.shuffle(_display6)
# remove some from display so they're None
_display6 = _display6[:900]
_coding6 = {"codes_to_meanings": {...}, "display": _display6, "codes_to_concepts": {...}}
```
Then 100 codes not in display → None. Work: 1000 codes × (search in 900) ×2.

Case 7: flat paginated large.
```python
_codes7 = ["pcode_%d" % i for i in range(15000)]
_coding7 = {"codes_to_meanings": {...}, "display": list(_codes7), CODING_PAGINATED_KEY: True}
```
Wait, with display present and paginated, the quadratic still happens before popping. 15000×15000 = 2.25*10^8 → too slow! So don't include display here. Use no display: `_coding7 = {"codes_to_meanings": {...}, CODING_PAGINATED_KEY: True}`. Then display_order computed as all None (fast), then popped. Good.

Hmm, but paginated is meant for a coding split across pages — no display. Realistic.

Case 8: flat concepts misaligned.
```python
_codes8 = ["mcode_%d" % i for i in range(15000)]
_meanings8 = {c: "m" for c in _codes8}
_concepts8 = {c: "concept_%d" % i for i, c in enumerate(reversed(_codes8)) if i % 3 == 0}
_coding8 = {"codes_to_meanings": _meanings8, "codes_to_concepts": _concepts8}
```
No display. Good.

Hmm, cases 5, 7, 8 are all "flat no display large" which is similar work. Let's diversify.

Let me reconsider. Maybe make case 5 flat with display but small codes and large display? The quadratic...

Alternative: flat with display where all codes are in display and display is the same order → `.index` finds quickly? No, still O(n) per code from the start... Actually if code is at position i, index scans i elements. Total = sum i = n^2/2. Still quadratic.

OK, so flat-with-display is inherently quadratic. Keep it small (case 6).

Let's diversify the large flat cases by size and concepts.

Case 5: flat, 15000 codes, no display, no concepts.
Case 7: flat, 15000 codes, paginated, with display absent. Work similar to 5 but skips pd.array. Slightly different.
Case 8: flat, 15000 codes, concepts misaligned, no display.

These are similar in cost. The harness keeps the 4 that do the most work. That's fine; we just need 8 distinct cases.

Hmm, but "Each case should make the function do substantial and different work: different paths through its code". The paginated path is different. The concepts path is different data.

Let me add more variety:
- A hierarchical case where concepts are ordered differently.
- A flat case with display but small.

Let me restructure to 8:

1. hier-large (15000, concepts half)
2. hier-wide (15000, max_children 40, depth 3)
3. hier-deep (8000, max_depth 12, max_children 3)
4. hier-paginated (12000)
5. hier-empty-concepts (12000)
6. flat-large-no-display (15000)
7. flat-with-display (1000 codes, 900 display)
8. flat-paginated (15000)

That's 8. Good.

Hmm, maybe replace one with a flat case where display is present and codes are all in display in the same order — but that's still quadratic. Skip.

Actually, let's include a flat case with small display to test the `display.index` path more moderately. Case 7 covers it.

Let me now also double check the hierarchical `zip(*unpack_hierarchy(...))` — if display is non-empty, fine.

One concern: `all_codes, parents, displ_ord = zip(...)` — all_codes is a tuple. Then `len(dcols["code"])` works. Fine.

`"display_order": displ_ord` — displ_ord is a tuple of ints. pd.array with Int64. Fine.

Now, about `codes_to_meanings` — for hierarchical, `coding["codes_to_meanings"][c]` for each code. Must contain all codes. Yes.

For `codes_to_concepts.get(c)` — may be None. Fine.

Now let me write the module.

Also need to be careful: `_rng` used across builders — deterministic since seeded. Good.

Let me also double check `_make_hierarchy` recursion: `build(n, depth)` where n is total codes for this subtree. The while loop: for internal, `child_n = rng.randint(1, min(max_children, n-1))`. If n-1 >= 1, min is >= 1. Good. `n -= 1 + child_n` → n >= 0.

But wait: after `n -= 1 + child_n`, n could be 0, loop exits. Good.

Total codes consumed from `codes` list = n_codes exactly? Each iteration consumes 1 code (either terminal or internal) plus child_n codes consumed by recursion. So total = n. Yes. idx[0] ends at n_codes. Good.

But what if `n_codes` is such that... fine.

Potential issue: recursion depth with max_depth=12 and max_children=3: depth ≤ 12. Fine.

For max_depth=6, max_children=10: depth ≤ 6. Fine.

Now the `codes` list is shuffled so the mapping code→position is random. Good.

Let me write the final code.

```python
import random

from dxpy.cli.dataset_utilities import DXDatasetDictionary, CODING_PAGINATED_KEY

_INSTANCE = DXDatasetDictionary.__new__(DXDatasetDictionary)


def _make_hierarchy(rng, n_codes, max_depth=6, max_children=10):
    codes = ["code_%d" % i for i in range(n_codes)]
    rng.shuffle(codes)
    idx = [0]

    def build(n, depth):
        nodes = []
        while n > 0:
            if n == 1 or depth >= max_depth or rng.random() < 0.35:
                nodes.append(codes[idx[0]])
                idx[0] += 1
                n -= 1
            else:
                c = codes[idx[0]]
                idx[0] += 1
                child_n = rng.randint(1, min(max_children, n - 1))
                children = build(child_n, depth + 1)
                nodes.append({c: children})
                n -= 1 + child_n
        return nodes

    return build(n_codes, 0), codes


def _meanings(codes, tag):
    return {c: "%s meaning for %s" % (tag, c) for c in codes}


def _concepts(codes, rng, ratio, tag="concept"):
    return {c: "%s_%d" % (tag, i) for i, c in enumerate(codes) if rng.random() < ratio}
```

Then build the cases at module level.

```python
_rng = random.Random(0)

# 1 hierarchical large
_disp1, _codes1 = _make_hierarchy(_rng, 15000, max_depth=6, max_children=10)
_coding1 = {
    "display": _disp1,
    "codes_to_meanings": _meanings(_codes1, "h1"),
    "codes_to_concepts": _concepts(_codes1, _rng, 0.5, "c1"),
}

# 2 hierarchical wide
_disp2, _codes2 = _make_hierarchy(_rng, 15000, max_depth=3, max_children=40)
_coding2 = {
    "display": _disp2,
    "codes_to_meanings": _meanings(_codes2, "h2"),
    "codes_to_concepts": _concepts(_codes2, _rng, 0.8, "c2"),
}

# 3 hierarchical deep
_disp3, _codes3 = _make_hierarchy(_rng, 8000, max_depth=12, max_children=3)
_coding3 = {
    "display": _disp3,
    "codes_to_meanings": _meanings(_codes3, "h3"),
    "codes_to_concepts": _concepts(_codes3, _rng, 0.2, "c3"),
}

# 4 hierarchical paginated
_disp4, _codes4 = _make_hierarchy(_rng, 12000, max_depth=5, max_children=12)
_coding4 = {
    "display": _disp4,
    "codes_to_meanings": _meanings(_codes4, "h4"),
    "codes_to_concepts": _concepts(_codes4, _rng, 0.5, "c4"),
    CODING_PAGINATED_KEY: True,
}

# 5 hierarchical empty concepts
_disp5, _codes5 = _make_hierarchy(_rng, 12000, max_depth=7, max_children=8)
_coding5 = {
    "display": _disp5,
    "codes_to_meanings": _meanings(_codes5, "h5"),
    "codes_to_concepts": {},
}

# 6 flat large no display
_codes6 = ["fcode_%d" % i for i in range(15000)]
_coding6 = {"codes_to_meanings": _meanings(_codes6, "f6")}

# 7 flat with display
_codes7 = ["dcode_%d" % i for i in range(1000)]
_display7 = list(_codes7)
_rng.shuffle(_display7)
_display7 = _display7[:900]
_coding7 = {
    "codes_to_meanings": _meanings(_codes7, "f7"),
    "display": _display7,
    "codes_to_concepts": _concepts(_codes7, _rng, 0.5, "c7"),
}

# 8 flat paginated
_codes8 = ["pcode_%d" % i for i in range(15000)]
_coding8 = {
    "codes_to_meanings": _meanings(_codes8, "f8"),
    CODING_PAGINATED_KEY: True,
}
```

Wait, case 8 paginated flat with no display: display_order computed as [None]*15000 via `int(display.index(c)+1) if c in display else None` — display is [] so `c in []` false → None. Fast. Then popped. Good.

Hmm, but case 6 and 8 differ only in the pop. Fine.

Now, one concern: `_concepts` uses `rng.random()` — deterministic given seed and call order. Since all module-level, order is fixed. Good.

Now the thunks:

```python
def cases():
    return [
        ("hier-large", lambda: (_INSTANCE, _coding1, "coding_one", True)),
        ("hier-wide", lambda: (_INSTANCE, _coding2, "coding_two", True)),
        ("hier-deep", lambda: (_INSTANCE, _coding3, "coding_three", True)),
        ("hier-paginated", lambda: (_INSTANCE, _coding4, "coding_four", True)),
        ("hier-no-concepts", lambda: (_INSTANCE, _coding5, "coding_five", True)),
        ("flat-large", lambda: (_INSTANCE, _coding6, "coding_six", False)),
        ("flat-with-display", lambda: (_INSTANCE, _coding7, "coding_seven", False)),
        ("flat-paginated", lambda: (_INSTANCE, _coding8, "coding_eight", False)),
    ]
```

Wait — the function signature is `create_coding_name_dframe(self, coding, coding_name_value, is_hierarchical)`. Called as `DXDatasetDictionary.create_coding_name_dframe(instance, coding, name, is_hierarchical)`. The harness calls `func(*args)` where args is the tuple. So `(instance, coding, name, is_hierarchical)`. Good.

checks():

```python
def checks():
    return [
        ("empty-flat", lambda: (_INSTANCE, {"codes_to_meanings": {}}, "empty", False)),
        ("empty-hier", lambda: (_INSTANCE, {"display": [], "codes_to_meanings": {}}, "empty_h", True)),
        ("single-flat", lambda: (_INSTANCE, {"codes_to_meanings": {"a": "A"}}, "one", False)),
    ]
```

The empty-hier will raise ValueError from `zip(*[])`. Actually let's verify: `unpack_hierarchy([], "", 0)` — it's a generator; iterating yields nothing. `zip(*gen)` → `zip()` with no args → iterating gives nothing → `a, b, c = zip()` → ValueError: not enough values to unpack (expected 3, got 0). Yes, raises.

Hmm, but is that desired? "These may raise." Fine. But maybe better to have checks that all run to completion? Not required. Actually the harness compares behaviour (including exceptions) between original and modified. Fine.

But hmm, `empty-flat`: `codes_to_meanings` = {} → codes = []. display = [] . display_order = []. Then `pd.array([], dtype="Int64")` → empty Int64 array. Then `dcols["coding_name"] = []`. Then `pd.DataFrame({"code": [], "meaning": [], "concept": [], "display_order": Int64[], "coding_name": []})`. Works.

`single-flat`: codes = ["a"], display = [] → display_order = [None]. pd.array([None], dtype Int64). Works.

Good.

Now, one more consideration: does `pd` need to be imported? The module imports it. We don't use it directly.

Let me double-check the import path: `from dxpy.cli.dataset_utilities import DXDatasetDictionary`. The task says import it as such. Good.

Is `CODING_PAGINATED_KEY` importable from that module? It's defined at module level. Yes.

Now potential issue: importing `dxpy.cli.dataset_utilities` might be heavy or fail. The task says to import exactly as shown. Let's trust.

Actually, wait. The module does `import dxpy` and `from ..bindings import DXRecord`. Importing `dxpy.cli.dataset_utilities` triggers `dxpy/__init__.py` and `dxpy/cli/__init__.py`. Should be fine.

One risk: `from ..bindings.dxfile import DXFile` — class body creates a threadpool. Fine.

Now, memory: 15000 codes with meanings dict — fine. All under 100MB.

Let's also double check the hierarchical display size vs codes. `_make_hierarchy(15000)` returns display tree with 15000 code strings total (each terminal is a code, each internal dict key is a code). So `all_codes` has 15000 entries. Good.

Now, timing per call. Let's estimate DataFrame construction for 15000 rows × 6 cols. pandas DataFrame from dict of lists: ~ a few ms. Plus pd.array. Maybe 5-10ms. Good.

Hmm, is that enough "work"? 1ms minimum. Yes.

Actually, maybe I should increase sizes to make it more substantial, but the output limit (100k values) constrains. 15000×6 = 90000. OK.

For flat: 15000×5 = 75000. Good.

Let me reconsider case 7: 1000 codes × display 900. Work ~ 1000*900*2 = 1.8M string comparisons. Could be ~0.1-0.2s. Hmm, that might be the heaviest. It's under 1s. OK.

Actually, let me reduce to 800 codes and display 700 to be safe: 800*700*2 = 1.12M. ~0.07s. Fine. Let's use 1000/900 anyway; I think it's fine.

Hmm, string comparison in CPython for short strings: if the strings differ early, it's fast. "dcode_123" vs "dcode_456" — differ at first char after prefix. Actually they share prefix "dcode_" then digits. Comparison checks length first (equal), then memcmp. Fast. So ~50-100ns per comparison. 1.8M → 0.1-0.2s. OK, under 1s.

Let's go with 1000/900.

Actually, to be safer and still substantial, use 800 codes / 720 display: 800*720*2 = 1.15M → ~0.1s. Meh, similar. Keep 1000/900.

Hmm, I realize there might be an issue with `_display7 = _display7[:900]` — this keeps the first 900 of the shuffled list. So 100 codes (the last 100 in shuffled order) are not in display. Actually the codes not in display are `_display7[900:]` = last 100 of shuffled. Fine.

Now, `display.index(c)` for c in the first 900 of shuffled order — positions are the shuffled indices. Average ~450. Fine.

Let me finalize.

One more: should I worry that `_INSTANCE` created at module level might be mutated? The function doesn't touch self. Fine.

Actually, hmm — is `DXDatasetDictionary.__new__(DXDatasetDictionary)` going to work if the class inherits from object? Yes.

Let me write it out.

Also note: the harness renders arguments before and after the call to check for changes. Our coding dicts are large-ish but under 1M values. Fine.

Let me also consider: the `coding` dict is passed and the function does `coding.get(...)`. No mutation.

Final answer.

Wait, one thing: `_concepts` signature `_concepts(codes, rng, ratio, tag="concept")`. In case 1 I call `_concepts(_codes1, _rng, 0.5, "c1")`. Good.

Let me write the final code.

Actually, let me reconsider whether `DXDatasetDictionary.__new__` is safe. `object.__new__(cls)` — when called as `DXDatasetDictionary.__new__(DXDatasetDictionary)`, Python's `object.__new__` checks that `cls.__init__` is object's... no, that check is only when extra args are passed. With just cls, it's fine.

OK.

Also, maybe safer: build the instance in a helper that's called at module level.

Let me finalize.