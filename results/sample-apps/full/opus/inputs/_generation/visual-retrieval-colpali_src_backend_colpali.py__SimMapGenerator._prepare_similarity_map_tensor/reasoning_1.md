We need to write inputs for `_prepare_similarity_map_tensor`. The instance `SimMapGenerator` requires loading a model in `__init__` (load_model), which loads ColPali from HuggingFace — network access. That's a problem. But we can create the instance without calling `__init__`? The instructions say "A method is called as a plain function: the thunk builds the instance and passes it as the first argument". We can build an instance via `object.__new__(SimMapGenerator)` and set attributes `n_patch`, `processor`. Is that allowed? It's building the instance without running the constructor. The rule says no mocks/subclasses overriding methods. Using `object.__new__` and setting fields is "Setting data (a module's configuration, an object's fields) to build an input is fine." That's explicitly allowed.

The function reads `self.n_patch` and `self.processor` (via hasattr for image_seq_length). So we set `self.processor` to a simple object with `image_seq_length` attribute (or without, to hit the else branch). But wait, `self.processor` is expected to be a ColPaliProcessor; the function only does `hasattr(self.processor, "image_seq_length")`. We can set a simple namespace object. Is that a mock? It's setting an object's field to a plain object. Hmm, borderline. The rule: "no subclass that overrides a method of a repository or library class -- a subclass whose get returns canned data instead of making the request is a mock too." A simple object with an attribute is not a subclass overriding methods. The function only checks hasattr and reads the attribute. I think a small class or `types.SimpleNamespace` is acceptable. Alternatively, we could actually create a real ColPaliProcessor... that requires network/model download. Not possible.

Actually, could we avoid setting processor at all? If `self.processor` doesn't exist, `hasattr(self.processor, ...)` raises AttributeError. So we need it. Use `types.SimpleNamespace(image_seq_length=...)` or `SimpleNamespace()` (no image_seq_length → else branch 1024).

Also, the function needs `torch`. The import `from backend.colpali import SimMapGenerator` will import torch, colpali_engine, matplotlib, etc. Are those available? The task says use only standard library, the repository itself, and packages the repository already imports. colpali_engine may not be installed. Hmm. If colpali_engine is not installed, the import fails entirely and we can't run. But the task presumably has the environment set up. Let's assume it's importable. Actually the repo imports `colpali_engine.models` which imports transformers/torch. If unavailable, we'd need CANNOT RUN. But we can't know. Let's just write the code; if the import fails, that's the environment's issue. The instructions say "If the function cannot run here at all -- it needs network access... do not write code". The function itself doesn't need network; only the constructor does, and we bypass it. So we should write code.

Now design inputs. The function builds a tensor of shape (len(vespa_sim_maps), query_embs.size(0), n_patch, n_patch) and fills cells.

Realistic: from Vespa, similarity maps have "quantized": {"cells": [{"address": {"patch": ..., "querytoken": ...}, "value": ...}, ...]}. query_embs is a tensor of shape (num_query_tokens, dim) presumably. Actually in the repo, query_embs comes from get_query_embeddings_and_token_map. size(0) is number of tokens.

We need 8 cases with varied work: different numbers of maps, cells per map, n_patch, image_seq_length (with/without), patches beyond image_seq_length (skipped), duplicate cells (overwrites), etc.

Note the function's work is dominated by the loop over cells. Let's make cases with e.g. 20k-200k cells total. Each cell assignment is a scalar tensor assignment which is slow-ish. Let's estimate: ~1-10 microseconds per cell? Tensor indexing assignment overhead maybe ~2µs. 100k cells → 0.2s. Keep under 200ms per call ideally. Let's target 20k-100k cells.

Also building inputs must be under 10s and memory under 100MB. 100k cells as dicts is maybe 100k * ~300 bytes = 30MB. Fine.

Output size: tensor shape (num_maps, num_tokens, 32, 32) = for 4 maps, 16 tokens → 4*16*1024 = 65536 values. Under 100k. Careful: if num_maps * num_tokens * n_patch^2 > 100k, output too big. Let's keep it modest: e.g. num_maps up to 8, num_tokens up to 32, n_patch 32 → 8*32*1024 = 262144 > 100k. Hmm. But the output comparison is "the function returns in full" — tensor of 262k floats. The limit is about 100,000 values. So keep output small-ish. But the work comes from cells, not the tensor size. We can have many cells with a small tensor (overwrites). Actually the tensor allocation is part of the work too but small.

Let's design: n_patch=32 → 1024 cells per (map, token) plane. To have many cells without huge output, use fewer tokens/maps but many cells (with overwrites/duplicates). Real Vespa maps likely have cells = number of patches * tokens? Actually quantized cells represent the similarity of each query token to each patch, so up to image_seq_length * num_tokens cells. image_seq_length=1024 typically. So a real map could have 1024 * 16 = 16384 cells. With 4 maps → 65k cells, tensor 4*16*32*32=65536 values. That's realistic and within limits.

Let's plan cases:

1. "typical": 4 maps, 16 tokens, n_patch 32, image_seq_length 1024, each map ~8000 cells (random subset of 1024*16 addresses), values random floats. n_patch=32.
2. "many-maps": 8 maps, 8 tokens, cells 8000 each.
3. "dense-cells": 2 maps, 16 tokens, all 16384 addresses per map.
4. "no-image-seq-length": processor without image_seq_length (else branch 1024), 4 maps.
5. "small-image-seq-length": image_seq_length=256, so most patches skipped (patch >= 256 continue). Many skipped cells.
6. "duplicates": cells with repeated addresses (overwrites) — heavy writes to same location.
7. "large-n_patch": n_patch=64 → 4096 cells per plane; image_seq_length 4096? Actually n_patch is grid size, image_seq_length = n_patch^2 typically. Let's use n_patch=64, image_seq_length=4096, 2 maps, 16 tokens, cells 20000 each → tensor 2*16*64*64 = 131072 values > 100k. Hmm. Use 1 map? len(vespa_sim_maps)=1, 16 tokens, n_patch 64 → 65536. OK. But 1 map is less realistic. Or n_patch=48? Let's keep n_patch=64 with 1 map and 8 tokens → 32768 values. Cells 30000.
8. "single-token": query_embs with 1 token, many maps? 

Also need checks() with 2-3 edge inputs: empty vespa_sim_maps (len 0 → tensor shape (0, tokens, n, n)); empty cells in a map; zero query tokens (query_embs.size(0)=0 → tensor shape (maps,0,n,n), loop assigns to index query_token which would fail... but if cells empty it's fine). Let's do: empty list of maps; a map with empty cells; query_embs with 0 tokens and empty cells.

Careful: checks may raise, that's fine.

Now, the instance: we need `SimMapGenerator` instance without __init__. Use `object.__new__(SimMapGenerator)`. Then set `inst.n_patch = ...` and `inst.processor = SimpleNamespace(...)`.

But wait — `SimMapGenerator` might have `__slots__`? No, it's a normal class. `object.__new__` works.

However, is `object.__new__(SimMapGenerator)` considered a mock? It's not overriding anything. The class's __init__ loads a model which requires network. We're constructing an instance without initialization and setting fields. The rules say setting an object's fields is fine. I think it's acceptable and necessary. Alternatively we could call `SimMapGenerator.__new__(SimMapGenerator)`. Same.

Hmm, but there's a risk: the graders might consider bypassing __init__ as faking. But the alternative is network access. The instructions explicitly allow setting an object's fields. I'll go with it and note it in a comment.

Actually wait — maybe load_model could work offline if the model is cached. But we can't rely on that. Bypassing is safer and faster.

Another consideration: `self.processor` — the function calls `hasattr(self.processor, "image_seq_length")` inside the inner loop, for every cell. To be realistic, processor is a ColPaliProcessor which has `image_seq_length` attribute? In colpali_engine, ColPaliProcessor has `image_seq_length` property. We'll use SimpleNamespace.

Now, thunks must return fresh arguments each call? The function doesn't modify the input dicts or query_embs (it reads only). It creates a new tensor each call. So we can reuse the same data across calls. Good — build once at module level.

But careful: `query_embs.size(0)` — fine.

Now, the cells: each cell is a dict {"address": {"patch": int, "querytoken": int}, "value": float}. The function does int(cell["address"]["patch"]). Values can be floats.

Let's write a helper to generate cells.

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator

def _make_instance(n_patch, image_seq_length=None):
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst
```

Wait, `object.__new__(SimMapGenerator)` — SimMapGenerator's __new__ is object's. Fine.

Hmm, but the class might define `__init__` only. Fine.

Now cells generator:

```python
def _cells(n, n_tokens, image_seq_length, seed, dup=False):
    rng = random.Random(seed)
    cells = []
    if dup:
        pool = [(rng.randrange(image_seq_length), rng.randrange(n_tokens)) for _ in range(max(1, n // 10))]
        for _ in range(n):
            patch, qt = pool[rng.randrange(len(pool))]
            cells.append({"address": {"patch": patch, "querytoken": qt}, "value": rng.random()})
    else:
        for _ in range(n):
            patch = rng.randrange(image_seq_length)
            qt = rng.randrange(n_tokens)
            cells.append({"address": {"patch": patch, "querytoken": qt}, "value": rng.random()})
    return cells
```

Actually patch can be >= image_seq_length to hit the skip path. In case 5, we want many skipped: generate patch in range(image_seq_length * 2) so half skipped.

Let's define a more flexible generator.

Let me write module-level data:

```python
def _make_maps(n_maps, cells_per_map, n_tokens, image_seq_length, seed, patch_max=None):
    rng = random.Random(seed)
    if patch_max is None:
        patch_max = image_seq_length
    maps = []
    for _ in range(n_maps):
        cells = []
        for _ in range(cells_per_map):
            cells.append({
                "address": {
                    "patch": rng.randrange(patch_max),
                    "querytoken": rng.randrange(n_tokens),
                },
                "value": rng.random(),
            })
        maps.append({"quantized": {"cells": cells}})
    return maps
```

query_embs: torch.randn(n_tokens, 128). It's only used for size(0). But realistic.

Now the cases. Let's compute work: total cells across maps. Each cell does a few dict lookups, int(), hasattr, comparison, and a tensor assignment. Tensor assignment on CPU ~1-2 µs. So 50k cells ≈ 0.05-0.1s. Good.

Case list (8):

1. typical-4maps-16tokens: n_maps=4, tokens=16, n_patch=32, image_seq_length=1024, cells_per_map=8000. Total 32000 cells. Tensor 4*16*1024=65536.
2. many-maps: n_maps=8, tokens=8, n_patch=32, isl=1024, cells_per_map=6000 → 48000 cells. Tensor 8*8*1024=65536.
3. dense: n_maps=2, tokens=16, n_patch=32, isl=1024, cells_per_map=16000 (near full coverage 16384) → 32000 cells. Tensor 32768.
4. no-image-seq-length: processor without attribute → else 1024. n_maps=4, tokens=16, cells_per_map=8000.
5. truncated: image_seq_length=256, patch_max=1024 → ~75% skipped. n_maps=4, tokens=16, cells_per_map=20000 → 80000 cells, most skipped (still loop work). Tensor 65536.
6. duplicates: n_maps=4, tokens=16, isl=1024, cells_per_map=12000 with small address pool → overwrites. 48000 cells.
7. large-patch-grid: n_patch=64, image_seq_length=4096, n_maps=1, tokens=8, cells_per_map=30000. Tensor 1*8*4096=32768.
8. single-map-many-tokens: n_maps=1, tokens=64, n_patch=32, isl=1024, cells_per_map=20000. Tensor 1*64*1024=65536. cells 20000.

Hmm case 8 tokens=64, querytoken range 64, fine.

Alternatively vary n_patch smaller like 16. Let's include one with n_patch=16, image_seq_length=256.

Let's finalize 8 diverse:

1. "typical": 4 maps, 16 tokens, n_patch 32, isl 1024, 8000 cells/map.
2. "many-maps": 8 maps, 8 tokens, n_patch 32, isl 1024, 6000 cells/map.
3. "dense-full": 2 maps, 16 tokens, n_patch 32, isl 1024, 16000 cells/map (full).
4. "no-image-seq-length": 4 maps, 16 tokens, n_patch 32, no isl attr, 8000 cells/map.
5. "truncated-patches": 4 maps, 16 tokens, n_patch 32, isl 256, patch_max 1024, 20000 cells/map.
6. "duplicate-addresses": 4 maps, 16 tokens, n_patch 32, isl 1024, 12000 cells/map, small pool.
7. "large-grid": 1 map, 8 tokens, n_patch 64, isl 4096, 30000 cells.
8. "small-grid-many-tokens": 1 map, 64 tokens, n_patch 16, isl 256, 20000 cells.

Wait case 8: n_patch=16 → 256 cells per plane, 64 tokens → 16384 addresses. 20000 cells. Tensor 1*64*256=16384.

Output sizes all under 100k. Good.

Total cells: 32000+48000+32000+32000+80000+48000+30000+20000 = 322000 cells. Building dicts: maybe 322k * ~2µs = 0.6s. Fine.

Memory: 322k cells, each dict with nested dicts ~ 500 bytes → 160MB. Hmm, that might exceed 100MB. Let's reduce. Actually the limit is "Keep the data in memory under about 100 MB". 322k cells with nested dicts... A dict with 2 keys is ~184 bytes, plus inner dict 184 bytes, plus ints (small ints cached up to 256, larger ints 28 bytes each), plus string keys (interned, shared). So per cell: outer dict 184 + inner dict 184 + 2 int objects (patch up to 4096 → 28 bytes each, querytoken small cached) + float value 24 bytes ≈ 420 bytes. 322k * 420 ≈ 135MB. Slightly over. Let's trim to ~200k cells total.

Reduce: case 5 to 15000/map → 60000. case 6 to 8000 → 32000. case 7 to 20000. case 8 to 15000. Total: 32000+48000+32000+32000+60000+32000+20000+15000 = 271000. ~114MB. Still a bit high. Hmm.

Actually strings "address", "patch", "querytoken", "value", "quantized", "cells" are shared references (same string objects) — dict stores pointers. So per cell outer dict: 184 bytes + 2 pointers... Actually dict size for 2 entries is 184 bytes (CPython 3.11: 64-byte header + 8*... let me not be precise). Inner dict with 2 entries ~184. Python ints: patch for isl 1024 → values > 256 create new int objects, 28 bytes. querytoken < 64 cached. Float 24 bytes. Total ~420.

271k * 420 = 114 MB. Over 100MB. Let's cut more. Target ~150k cells total → 63MB.

But then work per call: 150k cells / 8 cases ≈ 19k per case → ~40ms per call. That's fine (1ms-200ms). Actually more work is better for measurement but within limits. Let's aim ~250k cells but reduce memory by... we can't easily.

Alternatively, note the memory limit is about data in memory. Let's be safe: ~200k cells → 84MB. 

Adjust:
1. typical: 4 maps × 6000 = 24000
2. many-maps: 8 × 4000 = 32000
3. dense: 2 × 16000 = 32000
4. no-isl: 4 × 6000 = 24000
5. truncated: 4 × 12000 = 48000
6. duplicates: 4 × 8000 = 32000
7. large-grid: 1 × 20000 = 20000
8. small-grid: 1 × 12000 = 12000
Total = 224000 → ~94MB. Hmm borderline.

Let's cut to ~180k:
1. 4×5000=20000
2. 8×3500=28000
3. 2×14000=28000
4. 4×5000=20000
5. 4×10000=40000
6. 4×6000=24000
7. 1×15000=15000
8. 1×10000=10000
Total = 185000 → ~78MB. Good.

Per call: 20k-40k cells → 40-80ms. Good range.

Hmm, but is the work dominated by tensor assignment? Let's think: for each cell, `vespa_sim_map_tensor[idx, query_token, patch // n_patch, patch % n_patch] = value`. This is a 4D advanced indexing assignment? Actually it's basic indexing with 4 integer indices → returns a view, then assignment. Overhead per assignment maybe 3-5 µs in PyTorch. So 40k cells → 0.2s. Might exceed 200ms for case 5 (40k). Let's keep case 5 at 10k/map = 40k... maybe reduce. Actually let's keep per-case total cells ≤ 30k to stay under ~150ms. But we don't know exact speed. Let's be moderate: total per case ~20k-30k.

Revised:
1. typical: 4×5000=20000
2. many-maps: 8×3000=24000
3. dense: 2×12000=24000
4. no-isl: 4×5000=20000
5. truncated: 4×7000=28000 (most skipped, so cheaper per cell)
6. duplicates: 4×6000=24000
7. large-grid: 1×20000=20000
8. small-grid: 1×15000=15000
Total = 175000 → ~74MB. 

Per call 15k-28k cells. Good.

Now, `hasattr(self.processor, "image_seq_length")` is called per cell — that's part of the work. Fine.

Also note: the function calls `torch.zeros` each time — tensor allocation. Fine.

Now checks:

```python
def checks():
    inst = _make_instance(32, 1024)
    return [
        ("empty-maps", lambda: (inst, torch.zeros(16, 128), [])),
        ("empty-cells", lambda: (inst, torch.zeros(16, 128), [{"quantized": {"cells": []}}])),
        ("zero-tokens", lambda: (inst, torch.zeros(0, 128), [{"quantized": {"cells": []}}])),
    ]
```

Wait, the function signature: `_prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps)`. So the thunk returns (inst, query_embs, vespa_sim_maps). Yes.

For "zero-tokens": tensor shape (1, 0, 32, 32), loop over empty cells, fine. Returns tensor. Good.

Actually "empty-maps": len=0, tensor shape (0,16,32,32), loop none. Fine.

Hmm, checks may raise — but these don't.

Now, the instance: each case needs an instance with the right n_patch and processor. Build at module level.

Let me write the helper to build a case:

```python
_instances = {}

def _case(n_maps, n_tokens, n_patch, image_seq_length, cells_per_map, seed, patch_max=None, dup_pool=None):
    inst = _make_instance(n_patch, image_seq_length)
    q = torch.randn(n_tokens, 128, generator=torch.Generator().manual_seed(seed))
    maps = _make_maps(n_maps, cells_per_map, n_tokens, image_seq_length, seed, patch_max, dup_pool)
    return inst, q, maps
```

Hmm, `torch.randn` with generator — simpler: `torch.randn(n_tokens, 128)` but that's non-deterministic across calls? It's built once at module level, so fine. But for reproducibility use a seed. Actually query_embs only matters via size(0). Use `torch.zeros(n_tokens, 128)` — but a real query embs would be random. Doesn't matter for the function's work. Use `torch.ones` or randn. Let's use `torch.randn` with manual seed for realism.

Actually simpler: `torch.zeros(n_tokens, 128)` — fine, the function doesn't read values. But "avoid uniformity that a simple trick could exploit" — the function doesn't use values. Use randn anyway.

Now, building all cases at module level. But careful: module-level code runs at import time, before timing. Good.

However, if we build everything at module level, the `cases()` function just returns thunks referencing prebuilt data. Good.

But wait: the function returns a new tensor each call, doesn't mutate inputs. So reuse is safe.

Let me also double check `object.__new__(SimMapGenerator)` works given the class might have a metaclass? No.

Potential issue: `SimMapGenerator` may have `__slots__`? No, defined as normal class.

Now the import: `from backend.colpali import SimMapGenerator`. This will execute the module, which imports colpali_engine. If colpali_engine isn't installed, ImportError. We can't control that. Assume it's available.

Also `colpali_engine.models` import may require torch etc. Fine.

Let me write the code.

```python
import random
import types

import torch
from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    """Build a SimMapGenerator without running __init__ (which downloads a model)."""
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_cells(n_cells, n_tokens, image_seq_length, seed, patch_max=None, dup_pool=None):
    rng = random.Random(seed)
    if patch_max is None:
        patch_max = image_seq_length
    cells = []
    if dup_pool is not None:
        pool_size = max(1, dup_pool)
        pool = [(rng.randrange(patch_max), rng.randrange(n_tokens)) for _ in range(pool_size)]
        for _ in range(n_cells):
            patch, qt = pool[rng.randrange(pool_size)]
            cells.append({
                "address": {"patch": patch, "querytoken": qt},
                "value": rng.random(),
            })
    else:
        for _ in range(n_cells):
            cells.append({
                "address": {
                    "patch": rng.randrange(patch_max),
                    "querytoken": rng.randrange(n_tokens),
                },
                "value": rng.random(),
            })
    return cells


def _make_maps(n_maps, n_cells, n_tokens, image_seq_length, seed, patch_max=None, dup_pool=None):
    return [
        {"quantized": {"cells": _make_cells(n_cells, n_tokens, image_seq_length, seed + i, patch_max, dup_pool)}}
        for i in range(n_maps)
    ]


def _build(n_maps, n_tokens, n_patch, image_seq_length, n_cells, seed, patch_max=None, dup_pool=None):
    inst = _make_instance(n_patch, image_seq_length)
    g = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, 128, generator=g)
    maps = _make_maps(n_maps, n_cells, n_tokens, image_seq_length, seed, patch_max, dup_pool)
    return inst, query_embs, maps
```

Wait: `_make_maps` uses `seed + i` for each map, good for diversity.

Then module-level prebuilt cases:

```python
_C1 = _build(4, 16, 32, 1024, 5000, 0)
_C2 = _build(8, 8, 32, 1024, 3000, 1)
_C3 = _build(2, 16, 32, 1024, 12000, 2)
_C4 = _build(4, 16, 32, None, 5000, 3)
_C5 = _build(4, 16, 32, 256, 7000, 4, patch_max=1024)
_C6 = _build(4, 16, 32, 1024, 6000, 5, dup_pool=64)
_C7 = _build(1, 8, 64, 4096, 20000, 6)
_C8 = _build(1, 64, 16, 256, 15000, 7)
```

Hmm, `_build` for case 4 with image_seq_length=None: `_make_cells` needs image_seq_length for patch_max. If None, patch_max would be None → error. Let's pass image_seq_length=1024 for cell generation but None for the instance. Adjust: separate param `cell_isl`. Simpler: in `_build`, if image_seq_length is None, use 1024 for cells.

Let me restructure: `_build(n_maps, n_tokens, n_patch, cell_isl, n_cells, seed, patch_max=None, dup_pool=None, processor_isl='same')`. Getting complicated. Let's just make `_build` take both `processor_isl` and `cell_isl`.

Actually simpler: pass `image_seq_length` for cells and a flag `has_image_seq_length` for the processor.

```python
def _build(n_maps, n_tokens, n_patch, image_seq_length, n_cells, seed, patch_max=None, dup_pool=None, processor_isl=True):
    inst = _make_instance(n_patch, image_seq_length if processor_isl else None)
    ...
```

Then case 4: processor_isl=False, image_seq_length=1024.

Now thunks return `(inst, query_embs, maps)`.

```python
def cases():
    return [
        ("typical-4maps-16tokens", lambda: _C1),
        ...
    ]
```

Wait — the thunk must return a tuple of positional args. `lambda: _C1` where `_C1` is already a tuple `(inst, q, maps)`. That works: the thunk returns the tuple. Yes.

But careful: the function returns a tensor, and the harness compares outputs. The arguments are rendered before and after to check mutation. The tensor `query_embs` is not mutated. Good.

However, reusing the same `maps` dict across many calls is fine since the function doesn't modify it.

Now, one concern: `torch.randn` with generator at module level — fine.

Another concern: the function's `hasattr(self.processor, "image_seq_length")` — SimpleNamespace with image_seq_length works.

Let me also think about whether `object.__new__` might be considered "faking the environment". The rule list: "no mocks, no monkeypatching, no unittest.mock, no assigning functions or lambdas to attributes, and no subclass that overrides a method". Creating an instance via `object.__new__` and setting fields is explicitly permitted ("Setting data (a module's configuration, an object's fields) to build an input is fine"). The processor object is a plain object with an attribute the function reads. The function only reads `image_seq_length` from it. I think it's fine.

Alternatively, could we call the real `__init__`? It calls `load_model` which downloads from HuggingFace → network. Not allowed. So bypass is required.

Hmm, but wait: maybe `get_torch_device("auto")` and `load_model` are called. If we bypass, we skip. Good.

Let me double-check the function doesn't use anything else from self. It uses `self.n_patch` and `self.processor`. Yes.

Now, is there any chance `SimMapGenerator` has `__slots__` or a custom `__new__`? No.

Let's also consider: the module `backend.colpali` imports `colpali_engine.models` which imports `transformers` etc. If these are heavy but installed, import takes time (not timed). Fine.

Now let's reconsider the memory. 175k cells. Let me estimate more carefully. In CPython 3.11, a dict with 2 entries: sys.getsizeof ~ 184 bytes. Inner dict with 2 entries ~184. So 368 per cell plus int/float objects. patch int for range 1024: values > 256 are new ints (28 bytes). querytoken < 64: cached small ints, no allocation. value float: 24 bytes. So ~420 bytes/cell. 175k * 420 = 73.5 MB. Plus the outer maps list, query tensors, etc. Under 100MB. OK.

But actually, dicts with 2 entries: the "compact dict" in 3.11: 8 bytes for ma_used etc... Let me just trust ~400 bytes. 70MB fine.

Actually, I realize the cells dicts have string keys "address", "querytoken", "patch", "value" — these are the same string objects referenced everywhere (interned literals). So no per-cell string memory. Good.

Now, building time: 175k cells with random calls. Each cell: 2 randrange + random.random + dict construction. Maybe 1.5µs → 0.26s. Fine.

Now the timing: 8 cases, each call maybe 20-40ms. Good.

Let me reconsider case 7: n_patch=64, image_seq_length=4096, 20000 cells, 8 tokens. Tensor 1*8*64*64 = 32768. Good. patch // 64 and patch % 64.

Case 8: n_patch=16, image_seq_length=256, 64 tokens, 15000 cells. Tensor 1*64*16*16 = 16384. Good. patch range 256, so patch//16 in [0,15].

Wait, for case 8, `image_seq_length` is used both for the processor and for patch_max. 256. Fine.

Now checks. Let's write:

```python
def checks():
    inst = _make_instance(32, 1024)
    inst_no_isl = _make_instance(32, None)
    q16 = torch.randn(16, 128, generator=torch.Generator().manual_seed(99))
    q0 = torch.zeros(0, 128)
    return [
        ("empty-maps", lambda: (inst, q16, [])),
        ("empty-cells", lambda: (inst, q16, [{"quantized": {"cells": []}}])),
        ("no-image-seq-length-empty", lambda: (inst_no_isl, q0, [{"quantized": {"cells": []}}])),
    ]
```

Hmm "no-image-seq-length-empty" with q0 (0 tokens) and empty cells. Fine.

Maybe better: a check with a cell whose patch is out of range and a single token. But checks are for edge behavior. Let's include one that exercises the skip path and one empty.

Actually let's do:
- empty-maps: [] → tensor shape (0,16,32,32)
- empty-cells: one map, no cells
- out-of-range-only: one map with cells all patch >= image_seq_length → all skipped, tensor all zeros.

That's 3 checks. Good.

```python
def checks():
    inst = _make_instance(32, 256)
    q = torch.randn(4, 128, generator=torch.Generator().manual_seed(7))
    skipped = [{"quantized": {"cells": [
        {"address": {"patch": 300 + i, "querytoken": i % 4}, "value": 1.0} for i in range(5)
    ]}}]
    return [
        ("empty-maps", lambda: (inst, q, [])),
        ("empty-cells", lambda: (inst, q, [{"quantized": {"cells": []}}])),
        ("all-out-of-range", lambda: (inst, q, skipped)),
    ]
```

Wait, `skipped` is a list of one map. The thunk returns (inst, q, skipped). Fine.

Note: these checks run on original and modified; they may raise. Fine.

Now let's also double check: the function's first arg is `self`, then `query_embs`, then `vespa_sim_maps`. The harness calls `SimMapGenerator._prepare_similarity_map_tensor(instance, ...)`. So thunk returns (instance, query_embs, vespa_sim_maps). Yes.

Now, one more consideration: the harness "renders arguments before and after each call to see whether it changed them". The tensor query_embs is rendered — fine. The maps list is rendered — 175k dicts, rendering might be slow but that's the harness's job. Hmm, "keep each input's data under about 1 000 000 values". 175k cells × ~4 values = 700k values. Under 1M. OK, but close. Actually each cell has patch, querytoken, value = 3 values, plus nested. 175k × 3 = 525k. Fine.

But rendering 175k dicts before and after each call could be slow. That's the harness's problem though. Maybe reduce a bit to be safe. Let's target ~120k cells total. Then per-case work ~15k cells → ~30-60ms. Fine.

Revised counts:
1. 4×4000=16000
2. 8×2500=20000
3. 2×10000=20000
4. 4×4000=16000
5. 4×6000=24000
6. 4×5000=20000
7. 1×15000=15000
8. 1×10000=10000
Total = 141000. ~59MB. Good.

Per call: 10k-24k cells. At ~3µs/cell → 30-72ms. Good.

Hmm, case 5: 24000 cells but ~75% skipped (patch_max=1024, isl=256 → 75% skipped). Skipped cells are cheaper (no tensor assignment). Good.

Let me finalize.

One more thought: should I worry that `torch.randn` at module level uses a lot of memory? 16×128 floats = tiny.

Also, the `torch.zeros` allocation in the function: for case 3, tensor 2*16*32*32 = 32768 floats = 128KB. Fine.

Now, potential issue with `object.__new__(SimMapGenerator)` if the class uses `__init_subclass__` or something. No.

Let me also consider: maybe the harness imports our module and the import of `backend.colpali` fails because colpali_engine isn't installed. Then we're stuck. But the task expects us to write code. I'll assume the environment has it.

Actually, wait. Let me reconsider: is there a risk that `from backend.colpali import SimMapGenerator` triggers `get_torch_device` at import? No, only inside __init__.

Also `matplotlib.cm` import — fine.

Let me write the final code.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    # Build the object without running __init__ (which would download the
    # ColPali model from the network).  The method under test only reads
    # ``self.n_patch`` and ``self.processor.image_seq_length``.
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_cells(n_cells, n_tokens, patch_max, seed, dup_pool=None):
    rng = random.Random(seed)
    cells = []
    if dup_pool is not None:
        pool = [(rng.randrange(patch_max), rng.randrange(n_tokens))
                for _ in range(dup_pool)]
        n_pool = len(pool)
        for _ in range(n_cells):
            patch, qt = pool[rng.randrange(n_pool)]
            cells.append({
                "address": {"patch": patch, "querytoken": qt},
                "value": rng.random(),
            })
    else:
        for _ in range(n_cells):
            cells.append({
                "address": {
                    "patch": rng.randrange(patch_max),
                    "querytoken": rng.randrange(n_tokens),
                },
                "value": rng.random(),
            })
    return cells


def _make_maps(n_maps, n_cells, n_tokens, patch_max, seed, dup_pool=None):
    return [
        {"quantized": {"cells": _make_cells(n_cells, n_tokens, patch_max, seed + 100 * i, dup_pool)}}
        for i in range(n_maps)
    ]


def _build(n_maps, n_tokens, n_patch, image_seq_length, n_cells, seed,
           patch_max=None, dup_pool=None, processor_isl=True):
    if patch_max is None:
        patch_max = image_seq_length
    inst = _make_instance(n_patch, image_seq_length if processor_isl else None)
    g = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, 128, generator=g)
    maps = _make_maps(n_maps, n_cells, n_tokens, patch_max, seed, dup_pool)
    return (inst, query_embs, maps)


_C_TYPICAL = _build(4, 16, 32, 1024, 4000, 0)
_C_MANY_MAPS = _build(8, 8, 32, 1024, 2500, 1)
_C_DENSE = _build(2, 16, 32, 1024, 10000, 2)
_C_NO_ISL = _build(4, 16, 32, 1024, 4000, 3, processor_isl=False)
_C_TRUNCATED = _build(4, 16, 32, 256, 6000, 4, patch_max=1024)
_C_DUPLICATES = _build(4, 16, 32, 1024, 5000, 5, dup_pool=48)
_C_LARGE_GRID = _build(1, 8, 64, 4096, 15000, 6)
_C_SMALL_GRID = _build(1, 64, 16, 256, 10000, 7)


def cases():
    return [
        ("typical-4maps-16tokens", lambda: _C_TYPICAL),
        ("many-maps-8", lambda: _C_MANY_MAPS),
        ("dense-two-maps", lambda: _C_DENSE),
        ("processor-without-image-seq-length", lambda: _C_NO_ISL),
        ("truncated-patches", lambda: _C_TRUNCATED),
        ("duplicate-addresses", lambda: _C_DUPLICATES),
        ("large-patch-grid", lambda: _C_LARGE_GRID),
        ("small-grid-many-tokens", lambda: _C_SMALL_GRID),
    ]


def checks():
    inst = _make_instance(32, 256)
    q = torch.randn(4, 128, generator=torch.Generator().manual_seed(7))
    skipped = [{"quantized": {"cells": [
        {"address": {"patch": 300 + i, "querytoken": i % 4}, "value": 1.0}
        for i in range(5)
    ]}}]
    return [
        ("empty-maps", lambda: (inst, q, [])),
        ("empty-cells", lambda: (inst, q, [{"quantized": {"cells": []}}])),
        ("all-out-of-range", lambda: (inst, q, skipped)),
    ]
```

Wait, `_C_NO_ISL` uses image_seq_length=1024 for cells but processor without attribute → else branch uses 1024. Same result as having it. That's fine; the difference is the hasattr branch.

Hmm, but the "no-image-seq-length" case with processor_isl=False: `_make_instance(32, None)` → SimpleNamespace() with no attribute. Good.

One issue: in `_build`, `patch_max = image_seq_length` — for `_C_NO_ISL`, image_seq_length=1024. Good.

Now, `_C_TRUNCATED`: image_seq_length=256, patch_max=1024. The processor has image_seq_length=256. Cells with patch in [0,1024), 75% ≥ 256 → skipped.

`_C_LARGE_GRID`: n_patch=64, image_seq_length=4096, patch_max=4096. 15000 cells, 8 tokens. Tensor 1*8*64*64=32768.

`_C_SMALL_GRID`: n_patch=16, image_seq_length=256, patch_max=256, 64 tokens, 10000 cells. Tensor 1*64*16*16=16384.

Now, let me double check the total cells: 4*4000=16000, 8*2500=20000, 2*10000=20000, 4*4000=16000, 4*6000=24000, 4*5000=20000, 1*15000=15000, 1*10000=10000 → 141000. Memory ~59MB. Good.

But wait, the harness keeps all 8 cases' data in memory simultaneously (since module-level). 141k cells total → ~59MB. Plus Python overhead. Under 100MB. Good.

Now, one thing: the harness runs "the original function and a modified version of it on your inputs, each input many times in a row". Reusing the same maps is fine.

Another concern: `torch.randn(n_tokens, 128, generator=g)` — for n_tokens=64, fine.

Now, is `types.SimpleNamespace` acceptable as `self.processor`? The function does `hasattr(self.processor, "image_seq_length")`. SimpleNamespace works. I think it's fine — it's data, not a mock of a method.

Hmm, but the rule: "no subclass that overrides a method of a repository or library class -- a subclass whose get returns canned data instead of making the request is a mock too." We're not subclassing; we're using a generic namespace object. The function only reads an attribute. I'll go with it.

Alternative: could we use the real ColPaliProcessor? It requires loading a model. No.

Let me also double check that `SimMapGenerator` doesn't define `__slots__` that would prevent setting attributes. It doesn't (no __slots__ shown). Fine.

Now, the thunks return the prebuilt tuple. But the harness might call the thunk and then pass `*args`. Yes.

One more: the harness compares outputs. The output tensor is `torch.zeros(...)` filled. For the modified version, output should match. Fine.

I think the code is good. Let me also consider whether the function might be called with keyword args? No.

Let me finalize. Also add a brief comment about why we bypass __init__.

Actually, one more consideration: the import `from backend.colpali import SimMapGenerator` — the task says "Import it as `from backend.colpali import SimMapGenerator`". Good.

Also, should I worry that `backend.colpali` module-level code might do something at import that requires network? Looking at imports: torch, PIL, numpy, typing, pathlib, base64, io, re, matplotlib.cm, colpali_engine..., functools, logging. No network at import. Good.

Final answer.

Wait, one detail: the function signature is `_prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps)`. The thunk returns (inst, query_embs, vespa_sim_maps) — three positional args. Good.

Let me also make sure `checks()` cases don't accidentally take too long. They're tiny.

I'll write the final code block.