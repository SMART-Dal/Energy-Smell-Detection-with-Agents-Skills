The function under test: `_prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps)`.

We need to build an instance of SimMapGenerator. But `__init__` loads a model — heavy, requires network/GPU. We can't call `__init__`. But we can construct an instance without calling `__init__` — e.g., `SimMapGenerator.__new__(SimMapGenerator)` and set `n_patch` and `processor` attributes. That's setting data on an object, which is allowed ("Setting data (a module's configuration, an object's fields) to build an input is fine").

The function reads `self.n_patch`, `self.processor` (hasattr image_seq_length). So we create a bare instance and set those attributes. The processor needs `image_seq_length` attribute — we can use a simple object with that attribute. Is that a mock? It's a data holder. The rule says no subclass overriding methods of a repository class. A simple namespace object with `image_seq_length` is fine — it's setting data.

Actually, we could use `types.SimpleNamespace(image_seq_length=1024)`. That's not mocking a method, just data.

Wait, but the function also uses `query_embs.size(0)` — needs a torch tensor.

Let's design the input: vespa_sim_maps is a list of dicts, each with `{"quantized": {"cells": [ {...}, ... ]}}`. Each cell: `{"address": {"patch": ..., "querytoken": ...}, "value": ...}`.

The tensor shape: (len(vespa_sim_maps), query_embs.size(0), n_patch, n_patch). With n_patch=32, query tokens ~ 10-30, and several maps. Output size = len * q * 32 * 32. Keep under 100k values. E.g., 5 maps * 32 tokens * 32 * 32 = 163840 — too many. 3 maps * 16 tokens * 1024 = 49152. Fine.

Actually the output values count: len(vespa_sim_maps) * query_embs.size(0) * n_patch * n_patch. Keep under 100,000. So combos: 2 maps * 16 tokens * 1024 = 32768. 4 maps * 24 tokens * 1024 = 98304. Let's keep moderate.

But wait — the work is dominated by the number of cells, not the tensor size. Each cell assignment is a torch index assignment which is slow-ish. To make it 1ms-200ms, we need many cells. Each cell assignment involves int conversions and torch indexing — maybe ~1-5 microseconds. For 100ms we'd need ~20k-100k cells. Hmm.

Let's think about scale realistically. In real Vespa response, cells are the top-k similarity cells. Perhaps hundreds to thousands per map. Let's do a few thousand cells per map to get meaningful work.

Let's estimate: torch tensor index assignment `t[idx, q, r, c] = value` — this is Python-level indexing on a tensor, maybe ~2-10 µs each. 5000 cells → 10-50ms. Good.

Let's design 8 cases with varying:
- number of maps
- number of query tokens
- cells per map
- fraction of cells with patch >= image_seq_length (skipped)
- duplicate addresses (overwrites)
- processor with image_seq_length vs without (fallback 1024)
- n_patch values

Wait — n_patch is on self, and the tensor shape depends on it. If we vary n_patch, we need different instances. That's fine — each thunk builds its own instance.

Let's keep n_patch = 32 mostly, maybe one with n_patch=16.

image_seq_length: processor.image_seq_length. If patch >= image_seq_length, skip. So to have work, patches should be < image_seq_length. With image_seq_length=1024 and n_patch=32, patch ranges 0..1023 → valid. To exercise the skip path, include some patches >= 1024.

Let's write a generator:

```python
def _make_map(n_cells, n_query_tokens, image_seq_length, rng, skip_ratio=0.0, dup=False):
    cells = []
    for _ in range(n_cells):
        if skip_ratio and rng.random() < skip_ratio:
            patch = rng.randrange(image_seq_length, image_seq_length + 500)
        else:
            patch = rng.randrange(image_seq_length)
        qt = rng.randrange(n_query_tokens)
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.random(),
        })
    return {"quantized": {"cells": cells}}
```

Wait, but query_token must be < query_embs.size(0) to not index out of bounds. Actually the tensor's dim 1 is query_embs.size(0). If query_token >= that, torch raises IndexError. So keep querytoken < n_query_tokens and query_embs has size(0) = n_query_tokens.

Now query_embs: torch.randn(n_query_tokens, dim)? The function only uses size(0). We can use torch.randn(n_query_tokens, 128) or just torch.zeros(n_query_tokens). Keep it small. Actually to be realistic, embeddings are (n_tokens, 128). But it doesn't matter; size(0) is what's used. Let's use torch.randn(n_query_tokens, 128) with fixed seed.

Hmm, but the arguments are rendered before and after each call to see if changed. query_embs is a tensor; rendering a large tensor is fine but keep it modest. torch.randn(16, 128) = 2048 values. Fine.

Actually rendering: 2048 values per call, fine.

Now the instance: 

```python
def _make_instance(n_patch=32, image_seq_length=1024):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst
```

For the fallback case (no image_seq_length attribute), use `types.SimpleNamespace()`.

Note: `hasattr(self.processor, "image_seq_length")` is checked inside the loop for every cell. Fine.

Now careful about the "same work on every call" rule: the function creates a new tensor each call, doesn't modify inputs. So we can reuse the same vespa_sim_maps list across calls. Good — build once at module level.

But wait: does the function modify vespa_sim_maps? No. query_embs? No. So reuse is fine.

However, the instance — no state changes. Fine.

Let me now think about realistic scale. The repository: `gen_similarity_maps` is called with vespa_sim_maps from Vespa. Number of images typically small (a few pages), query tokens maybe 10-30, cells per map... Vespa returns quantized similarity maps, probably top-k cells. Hard to know. Let's just make varied sizes.

Let me set up 8 cases:

1. "small-typical": 3 maps, 16 query tokens, 500 cells each, image_seq_length=1024, n_patch=32. Output = 3*16*1024 = 49152 values. Cells total 1500.
2. "many-cells": 2 maps, 16 tokens, 4000 cells each → 8000 cells. Output 2*16*1024=32768.
3. "many-maps": 6 maps, 8 tokens, 800 cells each → 4800 cells. Output 6*8*1024=49152.
4. "skip-heavy": 4 maps, 16 tokens, 3000 cells each with skip_ratio 0.5 → output 4*16*1024=65536. Cells 12000 but half skipped.
5. "duplicates": 3 maps, 16 tokens, 3000 cells each but drawn from a small pool of addresses → many overwrites. Output 49152.
6. "no-image-seq-length": processor without image_seq_length → fallback 1024. 3 maps, 16 tokens, 2000 cells.
7. "n_patch-16": n_patch=16, image_seq_length=256, 4 maps, 16 tokens, 2000 cells. Output = 4*16*256=16384.
8. "large": 4 maps, 24 tokens, 5000 cells each → 20000 cells. Output 4*24*1024=98304 (under 100k). Good.

Hmm output 98304 is close to 100k but under. OK.

Let me reconsider timing. 20000 cells with torch indexing... each maybe 3µs → 60ms. Good.

Let's double check the tensor indexing: `vespa_sim_map_tensor[idx, query_token, patch // self.n_patch, patch % self.n_patch] = value`. This is a 4-D index assignment. In PyTorch, `t[i,j,k,l] = v` involves creating a view/select operations — quite slow, maybe ~5-15 µs. So 20000 cells could be 100-300ms. Hmm, might exceed 200ms. But we keep the 4 fastest of 8, so fine.

Actually the selection: "We run them on the original function and keep the 4 that do the most work." So we want variety.

Let me be a bit careful to not exceed 1s. 20000 cells * 15µs = 300ms. OK, under 1s.

Let's make the largest ~20000 cells. Fine.

Now, the value: `value = cell["value"]` — a float. Assigning float into a float tensor. Real values are quantized... probably floats. Use rng.random() or rng.uniform(-1,1). Fine.

Now checks(): 2-3 small edge inputs.
- empty vespa_sim_maps: `[]` → tensor shape (0, q, 32, 32). Should work.
- one map with empty cells: `[{"quantized": {"cells": []}}]`.
- query_embs with 0 tokens: size(0)=0 → tensor shape (n, 0, 32, 32), and cells with querytoken... would fail if any cell. Use empty cells. Actually with 0 query tokens and 0 cells it works. Let's include a case where patch >= image_seq_length only (all skipped) — but that's not really an edge.

Let's do:
1. "empty-maps": ([], query_embs(8))
2. "empty-cells": ([{"quantized": {"cells": []}}], query_embs(8))
3. "zero-tokens": ([{"quantized": {"cells": []}}], query_embs(0))

Hmm, but checks may raise. Fine.

Actually maybe include a case with a cell whose patch >= image_seq_length (skipped) — that's normal behavior. Let's keep simple.

Now, careful: the thunk returns args for `SimMapGenerator._prepare_similarity_map_tensor(instance, query_embs, vespa_sim_maps)`. Since it's an instance method called as a plain function, thunk returns `(instance, query_embs, vespa_sim_maps)`.

Now module-level setup: build instances and data once. But note: different cases use different instances with different n_patch/image_seq_length. Build them at module level.

Let me write helper functions.

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator
```

Wait — the import path. The task says import as `from backend.colpali import SimMapGenerator`. So we do that. But does importing `backend.colpali` work? It imports colpali_engine etc. The task says the module imports those; presumably they're installed. We must trust it. But if colpali_engine isn't installed, the import fails. The task says "If the function cannot run here at all... reply CANNOT RUN". But we're told to import as shown. Let's assume it works.

Hmm, but importing backend.colpali also imports matplotlib, PIL, numpy, torch, colpali_engine. Should be fine.

Potential issue: `from backend.colpali import SimMapGenerator` — the module path `backend.colpali` relative to `visual-retrieval-colpali/src`. The task gives the import line, so use it.

Now, the function under test accesses `self.processor` and `self.n_patch`. Using `SimMapGenerator.__new__(SimMapGenerator)` avoids `__init__`. Good.

But wait: is `SimMapGenerator.__new__` allowed? It's standard. Yes.

Now, one concern: the rule about "no subclass that overrides a method". We're not subclassing. SimpleNamespace for processor is just data. Good.

Let me write the code.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch=32, image_seq_length=1024):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_query_embs(n_tokens, dim=128, seed=0):
    rng = random.Random(seed)
    data = [[rng.uniform(-1.0, 1.0) for _ in range(dim)] for _ in range(n_tokens)]
    return torch.tensor(data, dtype=torch.float32)
```

Hmm, for n_tokens=0, torch.tensor([]) gives shape (0,) not (0,128). Let's handle: `torch.zeros((n_tokens, dim))` if n_tokens==0. Actually `torch.tensor([[]])`... Let's just do:

```python
def _make_query_embs(n_tokens, dim=128, seed=0):
    rng = random.Random(seed)
    t = torch.empty((n_tokens, dim), dtype=torch.float32)
    for i in range(n_tokens):
        for j in range(dim):
            t[i, j] = rng.uniform(-1.0, 1.0)
    return t
```

That's slow for large but n_tokens small. Fine. Actually simpler: use torch.randn with a manual seed? torch.manual_seed is global state — fine but let's avoid. Use rng and torch.tensor on nested list.

For n_tokens=0: `torch.tensor([], dtype=torch.float32)` shape (0,). size(0)=0. Good enough.

Let me use:
```python
def _make_query_embs(n_tokens, dim=128, seed=0):
    rng = random.Random(seed)
    data = [[rng.random() for _ in range(dim)] for _ in range(n_tokens)]
    return torch.tensor(data, dtype=torch.float32)
```
For n_tokens=0, data=[] → torch.tensor([], dtype=float32) shape (0,). size(0)=0. Fine.

Now the map builder:

```python
def _make_sim_map(n_cells, n_query_tokens, image_seq_length, rng, skip_ratio=0.0, address_pool=None, value_scale=1.0):
    cells = []
    for _ in range(n_cells):
        if address_pool is not None:
            patch, qt = address_pool[rng.randrange(len(address_pool))]
        else:
            if skip_ratio > 0.0 and rng.random() < skip_ratio:
                patch = rng.randrange(image_seq_length, image_seq_length + 1000)
            else:
                patch = rng.randrange(image_seq_length)
            qt = rng.randrange(n_query_tokens)
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.uniform(-value_scale, value_scale),
        })
    return {"quantized": {"cells": cells}}
```

For duplicates case: build an address pool of e.g. 200 addresses, and each map draws from it.

Now define cases at module level, building data once.

Let me define a helper to build a case's data:

```python
def _build_case(n_maps, n_query_tokens, n_cells, n_patch=32, image_seq_length=1024,
                skip_ratio=0.0, dup_pool=None, seed=0):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, image_seq_length)
    query_embs = _make_query_embs(n_query_tokens, seed=seed + 1)
    if dup_pool is not None:
        pool = [(rng.randrange(image_seq_length), rng.randrange(n_query_tokens))
                for _ in range(dup_pool)]
    else:
        pool = None
    maps = [_make_sim_map(n_cells, n_query_tokens, image_seq_length, rng,
                          skip_ratio=skip_ratio, address_pool=pool)
            for _ in range(n_maps)]
    return inst, query_embs, maps
```

Wait, for the no-image_seq_length case, image_seq_length param for building patches should still be 1024 (the fallback used by the function). Pass image_seq_length=1024 for building but instance processor has no attribute. Let me handle: `_build_case(..., image_seq_length=1024, inst_image_seq_length=None)`. Hmm, simpler: add parameter `processor_seq_length` defaulting to image_seq_length.

Let me restructure: `_build_case(..., image_seq_length=1024, processor_seq_length='same')`. Eh.

Simpler: build instance separately.

Let me just write each case's data at module level explicitly.

Actually let me use a function that returns (instance, query_embs, maps) and takes `processor_seq_length` param:

```python
def _build(n_maps, n_query_tokens, n_cells, n_patch=32, patch_range=1024,
           processor_seq_length=1024, skip_ratio=0.0, dup_pool=None, seed=0):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, processor_seq_length)
    query_embs = _make_query_embs(n_query_tokens, seed=seed)
    pool = None
    if dup_pool is not None:
        pool = [(rng.randrange(patch_range), rng.randrange(n_query_tokens)) for _ in range(dup_pool)]
    maps = [_make_sim_map(n_cells, n_query_tokens, patch_range, rng, skip_ratio, pool) for _ in range(n_maps)]
    return inst, query_embs, maps
```

where processor_seq_length=None means no attribute.

Now the cases:

```python
_C1 = _build(3, 16, 500, seed=1)
_C2 = _build(2, 16, 4000, seed=2)
_C3 = _build(6, 8, 800, seed=3)
_C4 = _build(4, 16, 3000, skip_ratio=0.5, seed=4)
_C5 = _build(3, 16, 3000, dup_pool=150, seed=5)
_C6 = _build(3, 16, 2000, processor_seq_length=None, seed=6)
_C7 = _build(4, 16, 2000, n_patch=16, patch_range=256, processor_seq_length=256, seed=7)
_C8 = _build(4, 24, 5000, seed=8)
```

Output values:
C1: 3*16*32*32 = 49152
C2: 2*16*1024 = 32768
C3: 6*8*1024 = 49152
C4: 4*16*1024 = 65536
C5: 3*16*1024 = 49152
C6: 3*16*1024 = 49152
C7: 4*16*16*16 = 16384
C8: 4*24*1024 = 98304

All under 100k. Good.

Cells totals: C1 1500, C2 8000, C3 4800, C4 12000 (half skipped → 6000 effective), C5 9000, C6 6000, C7 8000, C8 20000.

Now the thunks return `(inst, query_embs, maps)`.

But wait — the function creates a new tensor each call, doesn't mutate inputs. So reuse is fine.

One concern: the arguments are rendered before and after. Rendering `maps` (9000 dicts) each call — that could be slow but it's outside timing? "Its arguments are rendered before and after each call to see whether it changed them" — that's part of the harness, probably not timed. But it says keep each input's data under about 1,000,000 values. C8 has 20000 cells each with a few fields → maybe 100k values. Fine.

Hmm, rendering 20000 dicts repeatedly could be slow overall but acceptable.

Actually, could reduce cells but increase... no, it's fine.

Let me reconsider: is there a risk that torch indexing 20000 cells takes >1s? Let's think. `t[idx, q, r, c] = v` in PyTorch: it does `t.__setitem__((idx,q,r,c), v)` which internally uses `select`/`narrow` then `copy_`. Each maybe 10-20µs. 20000 * 20µs = 400ms. OK.

Actually for the largest, C8 might be ~400ms. Under 1s. Good. But if it's over 1s it gets dropped. We have 8 cases; we keep 4. Fine.

Now checks:

```python
def checks():
    inst = _make_instance(32, 1024)
    q8 = _make_query_embs(8, seed=100)
    q0 = _make_query_embs(0, seed=101)
    return [
        ("empty-maps", lambda: (inst, q8, [])),
        ("empty-cells", lambda: (inst, q8, [{"quantized": {"cells": []}}])),
        ("zero-tokens", lambda: (inst, q0, [{"quantized": {"cells": []}}])),
    ]
```

Hmm, but "empty-maps" gives tensor shape (0, 8, 32, 32) = 0 values. Returns fine.

Wait, `torch.zeros((0, 8, 32, 32))` works.

Let me double check `_make_query_embs(0)` → torch.tensor([], dtype=torch.float32), size(0) = 0. Then tensor shape (1, 0, 32, 32). Works.

Now, potential issue: `SimMapGenerator.__new__(SimMapGenerator)` — SimMapGenerator is a plain class (no __slots__), fine.

Another thought: does the class have a metaclass or __init_subclass__? No.

Now the import: `from backend.colpali import SimMapGenerator`. The module `backend.colpali` — will Python find `backend` package? The repository is `visual-retrieval-colpali/src/backend/colpali.py`. The task says import as `from backend.colpali import SimMapGenerator`. Presumably the working directory/sys.path is set so that `backend` is importable. Trust the task.

Let me also double-check: `self.processor.image_seq_length` is read inside the loop via hasattr. For SimpleNamespace with image_seq_length=1024, hasattr True. Good.

Now write final code.

One more: value assignment — tensor is float32 default. `value` is a Python float. Fine.

Also patch // n_patch and patch % n_patch: for patch up to 1023 and n_patch=32 → 0..31. Good. For C7, patch_range=256, n_patch=16 → 0..15. Good.

For skip cells: patch in [image_seq_length, image_seq_length+1000) → skipped, so index not computed. Good.

Let me also ensure querytoken < query_embs.size(0) = n_query_tokens. In `_make_sim_map`, qt = rng.randrange(n_query_tokens). Good. For dup pool, same.

Edge: n_query_tokens could be 0 in checks but cells empty there.

Now finalize.

Actually, let me reconsider the "value" for realism: Vespa quantized similarity values might be ints (quantized). `cell["value"]` assigned to float tensor. Real code likely gets floats. Use rng.uniform(-1,1). Fine.

Let me write it.

I'll add a small note: build all data at module level.

Final code:

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch=32, processor_seq_length=1024):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if processor_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=processor_seq_length)
    return inst


def _make_query_embs(n_tokens, dim=128, seed=0):
    rng = random.Random(seed)
    data = [[rng.uniform(-1.0, 1.0) for _ in range(dim)] for _ in range(n_tokens)]
    return torch.tensor(data, dtype=torch.float32)


def _make_sim_map(n_cells, n_query_tokens, patch_range, rng, skip_ratio=0.0, address_pool=None):
    cells = []
    for _ in range(n_cells):
        if address_pool is not None:
            patch, qt = address_pool[rng.randrange(len(address_pool))]
        else:
            if skip_ratio > 0.0 and rng.random() < skip_ratio:
                patch = rng.randrange(patch_range, patch_range + 1000)
            else:
                patch = rng.randrange(patch_range)
            qt = rng.randrange(n_query_tokens)
        cells.append({
            "address": {"patch": patch, "querytoken": qt},
            "value": rng.uniform(-1.0, 1.0),
        })
    return {"quantized": {"cells": cells}}


def _build(n_maps, n_query_tokens, n_cells, n_patch=32, patch_range=1024,
           processor_seq_length=1024, skip_ratio=0.0, dup_pool=None, seed=0):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, processor_seq_length)
    query_embs = _make_query_embs(n_query_tokens, seed=seed)
    pool = None
    if dup_pool is not None:
        pool = [(rng.randrange(patch_range), rng.randrange(n_query_tokens))
                for _ in range(dup_pool)]
    maps = [
        _make_sim_map(n_cells, n_query_tokens, patch_range, rng, skip_ratio, pool)
        for _ in range(n_maps)
    ]
    return inst, query_embs, maps


_C1 = _build(3, 16, 500, seed=1)
...
```

Good. Write final.

Wait, one thing about `_make_query_embs` with n_tokens=0: `torch.tensor([], dtype=torch.float32)` — shape (0,). size(0)=0. Fine.

Also in checks, `_make_instance` is used, that's fine.

Let me finalize the answer.