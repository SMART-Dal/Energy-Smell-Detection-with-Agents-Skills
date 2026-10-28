Let me think about this. The function `_prepare_similarity_map_tensor` uses `self.n_patch`, `self.processor` (only checks `hasattr(self.processor, "image_seq_length")`). The class `__init__` loads a model which requires network/GPU. But we need an instance. We can't call `SimMapGenerator(...)` because it loads a model.

We can build an instance without calling `__init__`? The instructions say no mocks, no subclass overriding methods. But we can create an instance via `object.__new__(SimMapGenerator)` and set attributes — that's "setting data (an object's fields) to build an input is fine".

So: `inst = SimMapGenerator.__new__(SimMapGenerator)`, set `inst.n_patch = 32`, `inst.processor = <something with image_seq_length>`. The processor just needs `image_seq_length` attribute. We can use a simple object... but is that a mock? The instruction says "no assigning functions or lambdas to attributes, and no subclass that overrides a method". Setting a plain object with an attribute is fine—it's data. Actually the processor is only used via `hasattr(self.processor, "image_seq_length")` and reading it. We could use a real ColPaliProcessor? That would require loading model. Simpler: use a simple namespace or a small class instance. Hmm, "no mocks" refers to replacing code. A plain object holding data is data. I think it's acceptable.

Actually, we could use `types.SimpleNamespace(image_seq_length=1024)`. That's data.

Alternatively, omit the attribute so `hasattr` returns False and image_seq_length = 1024. That's a path too. But we want diverse cases.

Now the function body: builds a tensor of shape (len(vespa_sim_maps), query_embs.size(0), n_patch, n_patch). Then iterates cells.

query_embs: a torch.Tensor; only `size(0)` is used. So we can make a tensor of shape (num_query_tokens, dim). Realistically query embeddings have shape (num_tokens, 128). We can make a real torch tensor of random floats.

vespa_sim_maps: list of dicts, each with "quantized" -> "cells" -> list of dicts with "address" -> {"patch":..., "querytoken":...} and "value".

The workload: number of cells. Real Vespa sim maps: for each image, cells for each patch and query token. With n_patch=32, image_seq_length=1024, patches 0..1023, query tokens 0..num_tokens-1. Cells list could be large.

Let's design realistic: for each image, cells = list over patches (say all 1024) × query tokens? That may be huge. Actually Vespa returns top-k cells? Let's just generate a realistic number of cells per image.

Let's make cases with varying sizes: e.g., 1 image with 20k cells, 4 images with 5k cells each, etc. Total work per call should be ~1ms-200ms.

The loop per cell does several int() conversions and tensor indexing. Python-level loop, so ~1-2 µs per cell maybe. 100k cells → ~0.2s. Let's target tens of thousands cells.

Let's design 8 cases:

1. single image, many cells (e.g., 50_000 cells), patches spread over 0..1023, query tokens 0..31.
2. many images (8), moderate cells each (5_000), total 40_000.
3. cells with patches >= image_seq_length (out-of-range, skipped) — but processor.image_seq_length = 1024; patches >=1024 skipped. Make half skipped.
4. processor without image_seq_length attribute → fallback 1024.
5. duplicate addresses (overwrites) — many cells hitting same (patch, querytoken).
6. large query token count (e.g., 64 tokens) with n_patch=32.
7. different n_patch, e.g., 16, with image_seq_length 256.
8. dense full coverage: all patches × all query tokens for a few images.

Wait, but the thunk builds the instance and passes it as first arg. The instance has n_patch and processor. Different cases may use different n_patch — build separate instances.

But careful: `vespa_sim_map_tensor` shape depends on query_embs.size(0) and n_patch. If query_token >= query_embs.size(0), indexing would error. Ensure query_token < query_embs.size(0).

Also patch//n_patch must be < n_patch: patch < n_patch^2. With n_patch=32, patch < 1024. image_seq_length also 1024. Fine. With n_patch=16, patch < 256; set image_seq_length=256.

Let's also ensure value is a float.

Output size: tensor of shape (num_images, num_tokens, n_patch, n_patch). For case with 8 images, 32 tokens, 32x32 = 8*32*1024 = 262144 values. That's over 100,000 values limit! "keep what it returns ... under about 100 000 values". Hmm. The return tensor is compared in full. So we need to keep returned tensor under 100k values.

So num_images * num_tokens * n_patch^2 < 100_000. With n_patch=32, n_patch^2=1024. So num_images*num_tokens < ~97. E.g., 2 images × 32 tokens = 64 → 65536 values. OK. Or 1 image × 64 tokens = 65536.

Hmm, that limits. Let's use num_images small. Let's aim: cases with 1-3 images, query tokens 16-64.

Also "arguments are rendered before and after each call to see whether it changed them" — keep each input's data under 1,000,000 values. The cells list is the big argument. Each cell is a dict with nested dicts — many values. Hmm, "values" probably counts scalars/containers. Let's keep cells under ~100k entries to be safe. Actually 1,000,000 values; a cell dict has maybe 5 values. 50k cells → 250k values. Fine.

Let me plan cases:

Common: query_embs tensor shape (T, 128) with T query tokens.

Case 1: "single-image-dense": 1 image, T=32, cells = all 1024 patches × 32 tokens = 32768 cells. Output 32768 values.
Case 2: "two-images": 2 images, T=32, cells per image 20_000 random. Output 2*32*1024 = 65536.
Case 3: "many-tokens": 1 image, T=64, cells 40_000. Output 65536.
Case 4: "out-of-range-patches": 1 image, T=32, cells 30_000 where half patches >= 1024 (skipped). Output 32768.
Case 5: "no-image-seq-length": processor without attribute, 1 image, T=32, cells 30_000.
Case 6: "duplicates": 1 image, T=32, cells 40_000 all mapping to few addresses (overwrites).
Case 7: "n-patch-16": n_patch=16, image_seq_length=256, 2 images, T=32, cells 20_000 each. Output 2*32*256=16384.
Case 8: "large-cells": 1 image, T=32, cells 80_000 random.

Hmm but many cases have similar structure. Let's diversify.

Actually, let's reconsider what Vespa sim maps look like. In ColPali, similarity map cells: each cell has address with patch and querytoken, and value. Realistically, the number of cells per image = num_patches × num_query_tokens? Or only top ones? Given the code, cells likely cover all patches for each query token. Actually in the repo, the Vespa response gives quantized cells. Let's just make realistic-ish.

Let me think about performance: 80,000 cells → each iteration does int(), dict lookups, hasattr, tensor index assignment. Maybe ~1.5 µs → 0.12s. Good, under 200ms.

Actually the hasattr check inside the loop is done per cell — meaningful work.

Let me now think about building the instance. `SimMapGenerator.__new__(SimMapGenerator)` then set `n_patch` and `processor`. The processor: use a tiny class defined in our source? Instructions: "no subclass that overrides a method of a repository or library class". A plain new class isn't a subclass. But is it a mock? It's just an object holding `image_seq_length`. I think it's fine as data. Alternatively use `types.SimpleNamespace`. Let's use SimpleNamespace for the hasattr case, and for the no-attribute case, an empty SimpleNamespace.

Hmm, but "no mocks" — SimpleNamespace is a generic data holder, not a mock. Good.

Wait, actually there might be a concern: is `self.processor` supposed to be a real ColPaliProcessor? The function only reads image_seq_length. Using SimpleNamespace is fine.

Now, does the function need anything else from self? Only n_patch and processor. Good.

Let me write helper to build cells.

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator
```

Wait — importing backend.colpali imports colpali_engine, matplotlib, PIL etc. That should be fine if installed. The task says use packages the repository already imports. Assume available.

Building the instance:

```python
def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst
```

For the no-attribute case, `types.SimpleNamespace()`.

Query embeddings: `torch.randn(T, 128)`.

Cells generation:

```python
def _cells(n, n_patch, query_tokens, seed, max_patch=None, dup=False):
    rng = random.Random(seed)
    ...
```

Let me write each case's cells carefully.

Let me define a generic builder:

```python
def _make_cells(count, n_patch, num_tokens, seed, patch_hi=None, addresses=None):
    rng = random.Random(seed)
    if patch_hi is None:
        patch_hi = n_patch * n_patch
    cells = []
    for _ in range(count):
        if addresses is not None:
            patch, qt = addresses[rng.randrange(len(addresses))]
        else:
            patch = rng.randrange(patch_hi)
            qt = rng.randrange(num_tokens)
        cells.append({
            "address": {"patch": str(patch), "querytoken": str(qt)},
            "value": rng.random(),
        })
    return cells
```

Note the function does `int(cell["address"]["patch"])`. Vespa might return strings or ints; int() works on both. Use strings? Real Vespa JSON returns strings maybe. Let's use ints to be safe... Actually int() handles both. Let's use ints for simplicity, but maybe one case with strings to exercise int conversion. Hmm, int conversion is same cost. Let's use strings for some cases to be realistic? The code does int() explicitly which suggests they might be strings. Let's use strings in a couple cases.

Actually let's just use ints mostly; it doesn't matter.

Hmm, but "different paths through its code" — the main branches: patch >= image_seq_length (skip), hasattr true/false, duplicates. We cover those.

Now the vespa_sim_maps list: list of dicts each {"quantized": {"cells": [...]}}.

Let me write:

```python
def _sim_map(cells):
    return {"quantized": {"cells": cells}}
```

Now cases:

1. ("single-dense", 1 image, T=32, cells = full grid 1024×32 = 32768)
   - Build cells: for patch in range(1024): for qt in range(32): value. Use rng for values.
2. ("two-images", 2 images, T=32, 20000 cells each random)
3. ("many-tokens", 1 image, T=64, 40000 cells)
4. ("out-of-range", 1 image, T=32, 30000 cells, patch range up to 2048 (half skipped))
5. ("no-seq-length", processor without attr, 1 image, T=32, 30000 cells)
6. ("duplicates", 1 image, T=32, 40000 cells over 64 addresses)
7. ("n-patch-16", n_patch=16, seq_len=256, 2 images, T=32, 20000 cells each)
8. ("large", 1 image, T=32, 80000 cells)

Check output sizes:
1: 1*32*1024 = 32768 ✓
2: 2*32*1024 = 65536 ✓
3: 1*64*1024 = 65536 ✓
4: 32768 ✓
5: 32768 ✓
6: 32768 ✓
7: 2*32*256 = 16384 ✓
8: 32768 ✓

All under 100k. Good.

Input data sizes: case 8 has 80000 cells, each dict with nested dicts: ~6 values → 480k values. Under 1M. OK. Case 1: 32768 cells. Case 3: 40000. Fine.

Total cells across all: ~300k, building should be fast (<1s).

Now the thunk returns `(inst, query_embs, vespa_sim_maps)`. The function is called as `SimMapGenerator._prepare_similarity_map_tensor(inst, query_embs, vespa_sim_maps)`.

Since the method is called as a plain function with instance first, thunk returns `(inst, query_embs, vespa_sim_maps)`.

Does the function mutate arguments? It doesn't modify vespa_sim_maps or query_embs. It doesn't modify inst. So we can reuse the same data across calls. Good — thunk returns the same objects each time.

But wait: repeated calls create a new tensor each time; fine.

However, note `torch.zeros` default dtype float32; assigning `value` (a Python float) works.

Now, one concern: `int(cell["address"]["patch"])` where patch is a large int; fine.

Also `patch // self.n_patch` and `patch % self.n_patch` — for patch >= image_seq_length we skip. For patch < image_seq_length = n_patch^2, patch//n_patch < n_patch. Good.

For case 4 with patch up to 2048 and n_patch=32, seq_len=1024: patches 1024..2047 skipped. Good.

For case 7 n_patch=16, seq_len=256, patches up to 256. Good.

Now let's also consider `query_token` must be < query_embs.size(0). Ensure qt < num_tokens where query_embs has num_tokens rows.

Let me write module-level code building everything.

Let me structure:

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _cells_random(count, n_patch, num_tokens, seed, patch_hi=None, as_str=True):
    rng = random.Random(seed)
    if patch_hi is None:
        patch_hi = n_patch * n_patch
    cells = []
    for _ in range(count):
        patch = rng.randrange(patch_hi)
        qt = rng.randrange(num_tokens)
        cells.append({
            "address": {"patch": str(patch) if as_str else patch,
                        "querytoken": str(qt) if as_str else qt},
            "value": rng.random(),
        })
    return cells
```

Hmm, using str for all is fine.

For dense grid case:

```python
def _cells_grid(n_patch, num_tokens, seed, value_scale=1.0):
    rng = random.Random(seed)
    cells = []
    for patch in range(n_patch * n_patch):
        for qt in range(num_tokens):
            cells.append({
                "address": {"patch": str(patch), "querytoken": str(qt)},
                "value": rng.random() * value_scale,
            })
    return cells
```

For duplicates:

```python
def _cells_duplicates(count, n_patch, num_tokens, seed, n_addresses=64):
    rng = random.Random(seed)
    addrs = [(rng.randrange(n_patch*n_patch), rng.randrange(num_tokens)) for _ in range(n_addresses)]
    cells = []
    for _ in range(count):
        patch, qt = addrs[rng.randrange(len(addrs))]
        cells.append({"address": {"patch": str(patch), "querytoken": str(qt)}, "value": rng.random()})
    return cells
```

Query embeddings: `torch.randn(num_tokens, 128)`.

Now build at module level.

Let me define:

```python
_EMB_32 = torch.randn(32, 128)
_EMB_64 = torch.randn(64, 128)
```

Actually query_embs.size(0) is the only thing used, but keep realistic shape.

Now let's assemble cases.

Case 1 single-dense:
```python
_inst1 = _make_instance(32, 1024)
_cells1 = _cells_grid(32, 32, 0)
_map1 = [{"quantized": {"cells": _cells1}}]
```

Wait output shape (1, 32, 32, 32) = 32768 values. Good.

Case 2 two-images:
```python
_inst2 = _make_instance(32, 1024)
_map2 = [{"quantized": {"cells": _cells_random(20000, 32, 32, 1)}},
         {"quantized": {"cells": _cells_random(20000, 32, 32, 2)}}]
```

Case 3 many-tokens:
```python
_inst3 = _make_instance(32, 1024)
_map3 = [{"quantized": {"cells": _cells_random(40000, 32, 64, 3)}}]
```

Case 4 out-of-range:
```python
_inst4 = _make_instance(32, 1024)
_map4 = [{"quantized": {"cells": _cells_random(30000, 32, 32, 4, patch_hi=2048)}}]
```

Case 5 no-seq-length:
```python
_inst5 = SimMapGenerator.__new__(SimMapGenerator)
_inst5.n_patch = 32
_inst5.processor = types.SimpleNamespace()
_map5 = [{"quantized": {"cells": _cells_random(30000, 32, 32, 5)}}]
```

Case 6 duplicates:
```python
_inst6 = _make_instance(32, 1024)
_map6 = [{"quantized": {"cells": _cells_duplicates(40000, 32, 32, 6)}}]
```

Case 7 n-patch-16:
```python
_inst7 = _make_instance(16, 256)
_map7 = [{"quantized": {"cells": _cells_random(20000, 16, 32, 7)}},
         {"quantized": {"cells": _cells_random(20000, 16, 32, 8)}}]
```

Case 8 large:
```python
_inst8 = _make_instance(32, 1024)
_map8 = [{"quantized": {"cells": _cells_random(80000, 32, 32, 9)}}]
```

Total cells: 32768 + 40000 + 40000 + 30000 + 30000 + 40000 + 40000 + 80000 = 332768. Each cell ~ dict of 2 dicts, 3 scalars. Building ~ fine.

Memory: 332k cells * maybe 300 bytes = 100MB? Hmm, might be a bit much. Each cell: outer dict (small), address dict, two strings, value float. Python dict overhead ~ 184 bytes for 2-entry dict... Let's estimate: each cell maybe ~500 bytes total. 332k * 500 = 166 MB. That's over 100MB. Hmm.

The limit says "Keep the data in memory under about 100 MB". Let's reduce cell counts.

Reduce: case1 grid 32768, case2 2×10000=20000, case3 25000, case4 20000, case5 20000, case6 25000, case7 2×10000=20000, case8 40000. Total ~ 202k cells. ~100MB still borderline.

Hmm. Maybe strings are costly. Let's use ints instead of strings for patch/querytoken to save memory. ints small are cached/interned? Small ints -5..256 cached; larger ints are objects ~28 bytes each. Strings of 1-4 chars ~ 50 bytes. Using ints saves.

Actually rng.randrange returns int; for values < 256 cached. patch up to 1024 mostly not cached. Still ints are smaller than strings.

Let's use ints. Then each cell: dict {address: dict{patch:int, querytoken:int}, value: float}. Two dicts ~ 184+184? No, a 2-key dict is 184 bytes? Actually sys.getsizeof({}) = 64, dict with 2 items = 184? Let me recall: empty dict 64 bytes, 1 item 184? No. CPython dict: 64 bytes for empty, then 224 for up to 5 items? Roughly. A small dict with 2 entries ~ 184 bytes. Two dicts = 368, plus int objects ~ 28 each for non-cached, plus float 24. So ~ 450 bytes/cell. 200k cells → 90MB. Borderline.

Let's cut further. Target total ~120k cells → ~55MB.

Revised:
1. grid 32×32 = 1024 patches × 32 tokens = 32768. Hmm that's a lot. Maybe reduce tokens to 16 for grid? But output shape then (1,16,32,32)=16384. Fine. Grid 32768 cells is the big one. Alternatively make grid partial.

Let me reconsider: the heavy work is per-cell. We want each call ~1ms-200ms. 32768 cells maybe ~50ms. Good.

Let's set:
1. dense grid: 1024 patches × 16 tokens = 16384 cells, T=16, output 16384.
2. two images: 2 × 8000 = 16000, T=32, output 65536.
3. many tokens: T=64, 20000 cells, output 65536.
4. out-of-range: 16000 cells (patch_hi 2048), T=32, output 32768.
5. no-seq-length: 16000 cells, T=32.
6. duplicates: 20000 cells, T=32.
7. n-patch-16: 2 × 8000 = 16000, T=32, output 16384.
8. large: 30000 cells, T=32, output 32768.

Total cells: 16384+16000+20000+16000+16000+20000+16000+30000 = 150384. ~70MB. Still a bit. Hmm.

Maybe reduce further. Actually let's estimate more carefully. sys.getsizeof for a dict with 2 items: I believe 184 bytes. Let me just be conservative and target ~100k cells.

Hmm, but we want substantial work. 100k cells across 8 cases = 12.5k avg per case. Each cell ~1.5µs → 12.5k cells ~ 19ms per call. That's fine (1ms-200ms range). Actually good.

But wait, the timing: they run each case many times. 20ms per call is good.

Let me reduce:
1. dense grid: 1024 × 16 = 16384 (T=16)
2. two images: 2 × 6000 = 12000
3. many tokens: 15000
4. out-of-range: 12000
5. no-seq-length: 12000
6. duplicates: 15000
7. n-patch-16: 2 × 6000 = 12000
8. large: 20000

Total = 114384. ~55MB. OK-ish.

Hmm, honestly the memory limit is "about 100 MB", so 70MB is fine. Let me not over-optimize. But the "values" count limit: "keep each input's data under about 1 000 000 values". For case 8 with 20000 cells, values: each cell ~ 5 values (2 dicts counted? probably scalars). 20000*5 = 100k. Fine.

Actually, if they count dict entries as values, 20000 cells * (2 address entries + 2 dicts + value) ~ 100k. Fine.

Let me go with moderate sizes. I'll use:

1. grid: 1024 patches × 32 tokens = 32768 cells, T=32. That's the dense one. Hmm, 32768 cells ~ 15MB. Fine actually.

Let me just compute total memory roughly: total cells ~ 150k * 450 bytes = 67MB. Acceptable.

Actually I realize the rendering "before and after each call" of arguments — rendering 150k cells list to a string could be huge but that's their problem; they said keep under 1M values. 150k cells * ~5 = 750k values. Borderline under 1M. Hmm, risky. Let me reduce to be safe: total cells ~ 100k → 500k values.

Let me finalize:

1. "dense-grid": T=32, grid 1024×32 = 32768 cells. values ~ 32768*5 = 164k. Fine.
2. "two-images": 2 images × 6000 = 12000 cells, T=32.
3. "many-tokens": T=64, 15000 cells.
4. "out-of-range": 12000 cells, patch_hi=2048, T=32.
5. "no-seq-length": 12000 cells, T=32.
6. "duplicates": 15000 cells, T=32.
7. "n-patch-16": 2 × 6000 = 12000 cells, T=32, n_patch=16.
8. "large": 20000 cells, T=32.

Total cells = 32768+12000+15000+12000+12000+15000+12000+20000 = 130768. Values ~ 650k. OK.

Hmm the dense grid is the biggest. Maybe reduce grid tokens to 16 → 16384 cells and T=16. Then output (1,16,32,32)=16384. That reduces total to 114384.

Let's do grid with 16 tokens.

Actually wait, the dense grid covers all patches — that's a distinct path (full coverage). Good.

Final:
1. dense-grid: n_patch=32, T=16, cells = 1024*16 = 16384.
2. two-images: n_patch=32, T=32, 2×6000=12000.
3. many-tokens: n_patch=32, T=64, 15000.
4. out-of-range: n_patch=32, T=32, 12000, patch_hi=2048.
5. no-seq-length: n_patch=32, T=32, 12000.
6. duplicates: n_patch=32, T=32, 15000 over 64 addresses.
7. n-patch-16: n_patch=16, seq_len=256, T=32, 2×6000=12000.
8. large: n_patch=32, T=32, 20000.

Total cells = 16384+12000+15000+12000+12000+15000+12000+20000 = 114384. Good.

Now checks(): 2-3 small edge inputs.

- empty: `([], [])`? Wait signature: (query_embs, vespa_sim_maps). Empty vespa_sim_maps with a query_embs tensor. Output shape (0, T, n_patch, n_patch). Works. 
- one cell: single cell.
- empty cells list: `vespa_sim_maps=[{"quantized": {"cells": []}}]`.

Also maybe query_embs with 1 token.

Let's do:
```python
def checks():
    inst = _make_instance(32, 1024)
    emb1 = torch.randn(1, 128)
    return [
        ("no-images", lambda: (inst, torch.zeros(4, 128), [])),
        ("empty-cells", lambda: (inst, torch.zeros(4, 128), [{"quantized": {"cells": []}}])),
        ("single-cell", lambda: (inst, torch.zeros(4, 128), [{"quantized": {"cells": [{"address": {"patch": 0, "querytoken": 0}, "value": 1.0}]}}])),
    ]
```

These may raise? no-images: torch.zeros((0,4,32,32)) works. Fine.

Now let's make sure imports work. `from backend.colpali import SimMapGenerator` — the module path is `visual-retrieval-colpali/src/backend/colpali.py`. The task says import as `from backend.colpali import SimMapGenerator`. So presumably sys.path includes src. We just use that import.

But importing backend.colpali imports colpali_engine and get_torch_device etc. Should be installed.

Potential issue: `SimMapGenerator.__new__(SimMapGenerator)` — class defines `colormap = cm.viridis` at class level, fine.

Now, is using `types.SimpleNamespace` for processor acceptable? The function only checks hasattr and reads attribute. Yes.

Alternatively, we could avoid the processor entirely by not setting it, but then hasattr(self.processor,...) raises AttributeError since self.processor missing. So must set something. SimpleNamespace is fine.

Let me write the code.

One more consideration: the thunk returns the same objects each call; the function doesn't mutate them. Good.

But note: `vespa_sim_map_tensor` created fresh each call. Fine.

Also `torch.zeros` returns float32. Assigning float values fine.

Let me also double check: for case 4, patch_hi=2048, patches 0..2047. image_seq_length=1024, so patches >=1024 skipped. patch//32 for patch<1024 gives 0..31. Good. But for skipped ones we `continue` before indexing. Good.

For case 7, n_patch=16, seq_len=256, patch_hi = 256 default. Good.

Now write final code.

Let me also seed torch? Not needed since only size(0) used, but values don't matter. Use torch.randn with generator? Not needed. Actually to be deterministic, torch.manual_seed(0) at module level. Fine.

Let me write:

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_instance_no_seq_len(n_patch):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace()
    return inst


def _cells_random(count, n_patch, num_tokens, seed, patch_hi=None):
    rng = random.Random(seed)
    if patch_hi is None:
        patch_hi = n_patch * n_patch
    cells = []
    for _ in range(count):
        patch = rng.randrange(patch_hi)
        qt = rng.randrange(num_tokens)
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.random(),
        })
    return cells


def _cells_grid(n_patch, num_tokens, seed):
    rng = random.Random(seed)
    cells = []
    for patch in range(n_patch * n_patch):
        for qt in range(num_tokens):
            cells.append({
                "address": {"patch": patch, "querytoken": qt},
                "value": rng.random(),
            })
    return cells


def _cells_duplicates(count, n_patch, num_tokens, seed, n_addresses=64):
    rng = random.Random(seed)
    addrs = [(rng.randrange(n_patch * n_patch), rng.randrange(num_tokens))
             for _ in range(n_addresses)]
    cells = []
    for _ in range(count):
        patch, qt = addrs[rng.randrange(len(addrs))]
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.random(),
        })
    return cells


def _sim_map(cells):
    return {"quantized": {"cells": cells}}
```

Then module-level data.

```python
torch.manual_seed(0)

_EMB_16 = torch.randn(16, 128)
_EMB_32 = torch.randn(32, 128)
_EMB_64 = torch.randn(64, 128)

_I32 = _make_instance(32, 1024)
_I32_NOSEQ = _make_instance_no_seq_len(32)
_I16 = _make_instance(16, 256)

_MAP_DENSE = [_sim_map(_cells_grid(32, 16, 0))]
_MAP_TWO = [
    _sim_map(_cells_random(6000, 32, 32, 1)),
    _sim_map(_cells_random(6000, 32, 32, 2)),
]
_MAP_MANYTOK = [_sim_map(_cells_random(15000, 32, 64, 3))]
_MAP_OOR = [_sim_map(_cells_random(12000, 32, 32, 4, patch_hi=2048))]
_MAP_NOSEQ = [_sim_map(_cells_random(12000, 32, 32, 5))]
_MAP_DUP = [_sim_map(_cells_duplicates(15000, 32, 32, 6))]
_MAP_NP16 = [
    _sim_map(_cells_random(6000, 16, 32, 7)),
    _sim_map(_cells_random(6000, 16, 32, 8)),
]
_MAP_LARGE = [_sim_map(_cells_random(20000, 32, 32, 9))]
```

Cases:

```python
def cases():
    return [
        ("dense-grid", lambda: (_I32, _EMB_16, _MAP_DENSE)),
        ("two-images", lambda: (_I32, _EMB_32, _MAP_TWO)),
        ("many-tokens", lambda: (_I32, _EMB_64, _MAP_MANYTOK)),
        ("out-of-range-patches", lambda: (_I32, _EMB_32, _MAP_OOR)),
        ("no-image-seq-length", lambda: (_I32_NOSEQ, _EMB_32, _MAP_NOSEQ)),
        ("duplicate-addresses", lambda: (_I32, _EMB_32, _MAP_DUP)),
        ("n-patch-16", lambda: (_I16, _EMB_32, _MAP_NP16)),
        ("large", lambda: (_I32, _EMB_32, _MAP_LARGE)),
    ]
```

Wait for n-patch-16: query_embs has 32 tokens, n_patch=16, output shape (2,32,16,16)=16384. Good. Cells patch in 0..255, qt 0..31. Good.

For many-tokens: T=64, cells qt 0..63. Output (1,64,32,32)=65536.

For two-images: output (2,32,32,32)=65536.

All good.

Now checks.

Note: label distinct.

Let me write checks:

```python
def checks():
    return [
        ("no-images", lambda: (_I32, torch.zeros(4, 128), [])),
        ("empty-cells", lambda: (_I32, torch.zeros(4, 128), [_sim_map([])])),
        ("single-cell", lambda: (_I32, torch.zeros(4, 128), [_sim_map([{"address": {"patch": 0, "querytoken": 0}, "value": 1.0}])])),
    ]
```

These may raise? no. Fine.

Wait, in checks, "no-images" with empty list: `len(vespa_sim_maps)=0`, tensor shape (0,4,32,32). Returns fine.

Hmm, but does `torch.zeros` with 0 dim work? Yes.

One concern: the function under test is called with instance as first arg — the harness presumably calls `SimMapGenerator._prepare_similarity_map_tensor(*args)` where args = (inst, query_embs, vespa_sim_maps). Good.

Let me double check the import: `from backend.colpali import SimMapGenerator`. We use that.

I think the code is ready. Let me also consider whether `torch` import is needed — yes for tensors.

One more: the module-level building of cells happens at import time of our file; fine.

Potential issue: `SimMapGenerator.__new__(SimMapGenerator)` — if the class uses __slots__? No.

Alright.

Also consider that the harness might import our file where WORKDIR is defined; we don't use it.

Let me finalize.