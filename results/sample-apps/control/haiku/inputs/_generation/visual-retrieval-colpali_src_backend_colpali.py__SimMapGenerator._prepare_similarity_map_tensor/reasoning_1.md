Let me think about this. The function under test is `_prepare_similarity_map_tensor`. It needs `self.n_patch`, `self.processor` (with optional `image_seq_length`), `query_embs` (torch.Tensor with size(0) = number of query tokens), and `vespa_sim_maps` list of dicts.

The problem: constructing a real `SimMapGenerator` instance requires loading a ColPali model (heavy, possibly network). We must not mock. But we can build an instance without calling `__init__`? The instructions say "the thunk builds the instance and passes it as the first argument". Hmm, but building the instance via `SimMapGenerator(logger)` loads a model — network access likely. Actually the model `vidore/colpali-v1.2` would be downloaded from HuggingFace. That's network. Hmm.

But wait — can we avoid calling `__init__`? We can create an instance using `object.__new__(SimMapGenerator)` and set `n_patch` and `processor` attributes. Is that "mocking"? The rules say no mocks, no subclass overriding methods, no assigning functions/lambdas to attributes. Setting data (an object's fields) to build an input is fine. So creating an instance via `__new__` and setting `n_patch` and a fake `processor` object... The processor is used only for `hasattr(self.processor, "image_seq_length")` and reading `.image_seq_length`. We could set `processor` to a simple object with that attribute, or None (then hasattr is False → 1024 branch).

Hmm, but is setting `processor` to a stub "mocking"? It's setting an object's fields. The processor is a ColPaliProcessor in reality. Using a simple namespace object as a processor is borderline. But the function only reads `image_seq_length` from it. I think it's acceptable: "Setting data (a module's configuration, an object's fields) to build an input is fine."

Alternatively, we could avoid needing the model entirely by constructing via `__new__`.

Actually, can we just create the instance without __init__? `SimMapGenerator.__new__(SimMapGenerator)` gives an uninitialized instance. Then set `.n_patch = 32` and `.processor = SomeObj()` or a real processor? Loading real processor requires network.

Let me consider: Does the import of `backend.colpali` itself trigger model loading? No, only class definition; `load_model` is called in `__init__`. Importing colpali_engine may be heavy but should be available? The task says we can use packages the repository already imports. colpali_engine must be installed. Hmm, risky but presumably available in the environment.

Actually, we should be careful: importing backend.colpali imports colpali_engine, torch, matplotlib, PIL, numpy. If colpali_engine isn't installed, import fails → CANNOT RUN. But the task expects us to write code; presumably the environment has these.

Now, the key question: is creating the instance via `__new__` and setting `n_patch`/`processor` acceptable? I think yes. The alternative — loading the real model — requires network (downloading weights). That would make it CANNOT RUN. But the function itself doesn't need the model; only the instance's attributes. Since the task says setup is never timed and building inputs is fine, and we're setting fields, I'll go with `__new__`.

Hmm, but the instruction says "the thunk builds the instance and passes it as the first argument (a classmethod gets its class there...)". It doesn't forbid `__new__`.

Let me write:

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator

def _make_instance(n_patch=32, image_seq_length=None):
    obj = SimMapGenerator.__new__(SimMapGenerator)
    obj.n_patch = n_patch
    proc = types.SimpleNamespace()
    if image_seq_length is not None:
        proc.image_seq_length = image_seq_length
    obj.processor = proc
    return obj
```

Wait, if image_seq_length is None we want hasattr False → fallback 1024. Using SimpleNamespace without the attribute gives hasattr False. Good.

Hmm, but is SimpleNamespace as processor a "mock"? It's a plain data holder. The rule prohibits mocks that replace behavior/canned data for the function under test. Here `processor` is just an input data object whose only relevant field is `image_seq_length`. I think it's fine. Alternatively, use a real `ColPaliProcessor`? Requires download. No.

Actually, maybe better: use `types.SimpleNamespace(image_seq_length=...)`. Fine.

Now the vespa_sim_maps structure: list of dicts, each `{"quantized": {"cells": [ {"address": {"patch": int, "querytoken": int}, "value": float}, ... ]}}`.

query_embs: torch.Tensor of shape (num_query_tokens, dim). `query_embs.size(0)` = num query tokens.

The output tensor shape: (len(vespa_sim_maps), num_query_tokens, n_patch, n_patch). With n_patch=32, that's 1024 per map per token. If len(maps)=5 and tokens=32, output = 5*32*1024 = 163840 values > 100000 limit. Hmm, the output must be under ~100000 values. So keep the output small.

Wait, "keep what it returns ... under about 100 000 values". So shape product must be < 100k. Let's pick e.g. len(maps)=4, tokens=8, n_patch=32 → 4*8*1024 = 32768. Good.

Actually in the real repo, n_patch=32, query tokens ~ maybe 20-30, vespa_sim_maps = number of images (could be several). So output could be large... but that's the real workload. We need to keep under 100k. Let's use a few maps and moderate tokens.

Workload: the function's cost is the double loop over cells, doing int() conversions and tensor indexing. To make it take ~1ms-200ms, we need many cells.

Each cell assignment: `vespa_sim_map_tensor[idx, query_token, patch//n_patch, patch%n_patch] = value`. Cost per cell is small. To reach ~10ms we need maybe 100k+ cells.

Let's design: n_patch=32, image_seq_length=1024 (or processor with image_seq_length=1024). patch values in [0, image_seq_length). Cells per map: up to 1024 patches × tokens. If tokens=8, that's 8192 cells per map max. With 4 maps → ~32k cells. That's maybe a few ms.

For more stress, use more tokens and maps but keep output under 100k. Output = maps * tokens * 1024. Under 100k → maps*tokens < 97. E.g., maps=8, tokens=12 → 96 → 98304. Cells: 8 maps * 12 tokens * 1024 patches = 98304 cells max. That's decent.

Hmm, but we want varied cases. Let's think about the different code paths:
- `hasattr(self.processor, "image_seq_length")` True vs False (fallback 1024).
- `patch >= image_seq_length` → continue (skip). So cells with patch out of range are skipped. Different ratios of skipped cells.
- query_token values within range (must be < query_embs.size(0), else index error → would raise). Actually if query_token >= size(0), tensor indexing raises IndexError. So all query_token must be < size(0). Keep valid.
- duplicates: multiple cells writing to same (idx, query_token, row, col) — later overwrites. Real Vespa maps may have duplicates? Possibly. Include some.
- value types: floats.

Also note patch//n_patch and patch%n_patch: patch up to image_seq_length-1. If image_seq_length=1024 and n_patch=32, patch//32 in [0,31]. Good. But if image_seq_length > n_patch*n_patch, e.g., 1024 = 32*32, fine. If we set processor.image_seq_length = 2048, then patch//32 up to 63 → index out of range for dim of size 32 → IndexError. So keep image_seq_length <= n_patch^2 = 1024. Or use larger n_patch.

Actually careful: patch//n_patch must be < n_patch, i.e. patch < n_patch^2. So image_seq_length <= n_patch^2. With n_patch=32, that's 1024. Good.

So the "skip" path: patch >= image_seq_length. If image_seq_length < n_patch^2, e.g., image_seq_length = 512, then patches in [512, 1024) are skipped. Good for testing skip.

Now let's design 8 cases with varied:
1. Typical: 4 maps, 8 tokens, n_patch=32, image_seq_length via processor = 1024, full cells (all 1024 patches × 8 tokens = 8192 cells per map... wait cells per map = tokens*patches = 8*1024 = 8192). 4 maps → 32768 cells. Output 32768.

Hmm, but output = maps*tokens*1024 = 4*8*1024=32768. Good.

2. More maps, fewer tokens: 16 maps, 6 tokens → output 16*6*1024=98304. Cells 16*6*1024=98304.

3. Fallback branch (no image_seq_length attr): processor without attribute → image_seq_length=1024. Same as full.

4. Skip-heavy: image_seq_length=256, patches up to 1024, many skipped.

5. Dense duplicates: cells with duplicate addresses.

6. Sparse: few cells per map.

7. n_patch different, e.g., n_patch=16 → output maps*tokens*256. Can have more maps/tokens. image_seq_length=256.

8. Large tokens small maps.

Let's be careful about total values in arguments: vespa_sim_maps is a list of dicts with cells; each cell has a dict with 2 keys and a value. The argument rendering counts values... "keep each input's data under about 1 000 000 values". A cell = ~4 values (patch, querytoken, value, plus dict keys). 100k cells → 400k values. Fine.

Let's now think about the time. 100k cells with int() conversions and tensor indexing in Python — maybe 50-100 ms? Let's estimate: each iteration ~1µs? Actually Python loop with dict lookups and tensor indexing maybe 1-2µs. 100k → 0.1-0.2s. Hmm, that might exceed 200ms. Let's keep the biggest around 100k cells → maybe ~150ms. Risky. Let's target max ~50k-80k cells.

Actually tensor indexing `t[a,b,c,d] = value` is relatively slow (~2-3µs). 100k → 300ms. Too slow. Let's keep max cells ~30-40k.

Hmm. Let's reconsider. We want cases that take 1ms-200ms. Let's aim for ~20k-50k cells for the heavy ones.

Let me design cell counts:
- case1 typical: 4 maps × 8 tokens × 1024 patches = 32768 cells. Output 32768.
- case2 many maps: 12 maps × 4 tokens × 1024 = 49152 cells. Output 12*4*1024=49152.
- case3 fallback: 6 maps × 8 tokens × 1024 = 49152 cells. Output 49152.
- case4 skip-heavy: image_seq_length=256; patches 0..1023 all present → 768/1024 skipped. 8 maps × 8 tokens × 1024 cells generated but 75% skipped → 16384 assignments, 65536 iterations. Output 8*8*1024=65536.
- case5 duplicates: 8 maps × 8 tokens × 2048 cells (with duplicates) → output 65536.
- case6 sparse: 20 maps × 5 tokens × 100 cells = 10000 cells. Output 20*5*1024=102400 > 100k. Reduce: 16 maps × 6 tokens = 96 → 98304. Cells 16*6*100=9600.
- case7 n_patch=16: image_seq_length=256, 16 maps × 8 tokens × 256 = 32768 cells. Output 16*8*256=32768.
- case8 large: 8 maps × 12 tokens × 1024 = 98304 cells. Output 98304.

Hmm case8 98304 cells might be ~200ms+. Let's reduce to 8 maps × 8 tokens = 65536 cells, output 65536.

Let me be a bit conservative overall. Actually we don't know the machine. The selection keeps the 4 that do most work, so having a range is fine; the ones over 1s get dropped. Let's keep max around 60k cells.

Let me write a helper to generate vespa sim maps.

```python
def _make_cells(rng, n_cells, n_tokens, image_seq_length, max_patch, dup_frac=0.0, patch_pool=None):
    cells = []
    for _ in range(n_cells):
        if patch_pool is not None:
            patch = rng.choice(patch_pool)
        else:
            patch = rng.randrange(max_patch)
        qt = rng.randrange(n_tokens)
        value = rng.random()
        cells.append({"address": {"patch": patch, "querytoken": qt}, "value": value})
    return cells
```

Wait, but addresses must be strings? The function does `int(cell["address"]["patch"])`. So patch can be int or str. Real Vespa returns strings probably. Let's use strings to exercise int(). Actually `int()` on int works too. Using strings adds a bit of work. Let's use strings for patch and querytoken in some cases and ints in others — "odd type" variety. Hmm, but checks() may raise... Let's keep valid.

Actually to be safe and realistic, use strings (Vespa JSON addresses are strings). The function explicitly calls int(), suggesting strings. Let's use strings.

Now generating 98304 cells as dicts: each cell is a dict with nested dict. That's memory heavy: ~98304 * (dict ~200 bytes + nested) ≈ 40MB. Under 100MB. OK.

But building all 8 cases: total cells maybe 300k → ~120MB. Hmm, that's over 100MB for args? "Keep the data in memory under about 100 MB" — that's per input I think, and "building all inputs under about 10 s". Let's be mindful. Total across cases maybe 250k cells. Each cell: outer dict 2 entries (~184 bytes), inner address dict (~184), value float, strings. Say ~500 bytes per cell → 125MB total. Hmm. Might be OK but let's reduce.

Actually let's reduce cell counts a bit. The heavy cases dominate. Let's target total cells ~150k.

Alternatively, share cells between cases? Each case needs distinct data ideally. But we can reuse a base set of cells for different cases with different n_patch/processor. But cases should differ.

Let me just moderate: max ~50k cells per case, and reuse some structures.

Hmm, let me reconsider the realistic scale. In the repo, `gen_similarity_maps` is called with vespa_sim_maps from Vespa — one per image. Each map's cells: Vespa returns the top-k cells per query token? Actually the quantized cells might be all patches for each query token. Real: image_seq_length=1024 patches, query tokens ~20. So cells per map ~20*1024=20480. And maps = number of images, maybe 1-10.

So realistic heavy case: 10 maps × 20 tokens = 200 tokens*1024 = 204800 cells, output 204800 values > 100k. So we must cap output. Use fewer tokens.

OK let's just design within limits.

Let me now decide the final 8 cases:

Common: n_patch=32, image_seq_length=1024 (via processor attribute) for most.

Case A "typical-single-image": 3 maps, 10 tokens, all 1024 patches → 30720 cells, output 30720.
Case B "many-images": 15 maps, 6 tokens → output 92160, cells 15*6*1024=92160. Hmm 92k cells too many maybe. Let's do 12 maps × 6 tokens = 73728 cells, output 73728. Still a lot. Maybe 10 maps × 6 = 61440.

Hmm, I worry about time. Let's estimate more carefully. A Python loop body: dict index `cell["address"]["patch"]`, two int() calls, attribute lookup hasattr (cached? no, hasattr each iteration), comparison, then tensor setitem with 4 indices. Probably ~1.5-2.5 µs. 60k → 90-150ms. Acceptable. 90k → 150-225ms. Borderline. Keep max ~60k.

Let's finalize:

1. "typical": 4 maps, 8 tokens, full 1024 patches → 32768 cells, output 32768. processor.image_seq_length=1024.
2. "many-images": 12 maps, 5 tokens → output 61440, cells 61440. processor.image_seq_length=1024.
3. "fallback-1024": 6 maps, 8 tokens → output 49152, cells 49152. processor without image_seq_length (fallback 1024).
4. "skip-heavy": processor.image_seq_length=256, 8 maps, 8 tokens, all patches 0..1023 → 65536 iterations, 16384 assignments, output 65536.
5. "duplicates": 8 maps, 8 tokens, 40000 cells with many duplicate addresses (patch from a small pool) → output 65536.
6. "sparse": 16 maps, 6 tokens, 60 cells each → 9600 cells, output 98304.
7. "n_patch-16": n_patch=16, image_seq_length=256, 16 maps, 8 tokens, 256 patches → 32768 cells, output 16*8*256=32768.
8. "wide-tokens": 8 maps, 10 tokens → output 81920, cells 81920. Hmm too many. 8 maps × 8 tokens = 65536. Let's do 8 maps × 8 tokens.

Hmm, cases 4,5,8 all 8 maps × 8 tokens → output 65536. Fine, different content.

Actually let me reconsider case 8: use image_seq_length smaller? Or use string vs int addresses. Let's make case 8 use int addresses (patch and querytoken as ints) to vary.

Also vary value types: floats.

Let me also think about "value" — tensor is float32 by default (torch.zeros default dtype float32). Assigning Python float fine.

Now checks(): 2-3 small edge inputs.
- empty vespa_sim_maps: `[]` → output shape (0, tokens, 32, 32). Should work.
- empty cells in a map: one map with cells=[] → zeros.
- query_embs with 1 token, single cell.

Let's write checks:
1. ("no-maps", instance, torch.zeros(5, 8)? query_embs shape (num_tokens, dim)). Actually query_embs.size(0) is num tokens. Let's use torch.zeros((1, 128)) → size(0)=1.
   `lambda: (inst, torch.zeros(1,128), [])`.
2. ("empty-cells", one map with empty cells).
3. ("single-cell", one map, one cell).

Now, the instance creation. We need `SimMapGenerator.__new__(SimMapGenerator)`. But wait — is `__new__` without args OK? SimMapGenerator doesn't define __new__, so object.__new__ is used. `SimMapGenerator.__new__(SimMapGenerator)` works.

But careful: the class has class attribute `colormap = cm.viridis` which is set at class definition (import time). Fine.

Now, does importing backend.colpali require anything else? It imports colpali_engine. If that's installed, fine.

Let me also consider: maybe there's a risk that `SimMapGenerator.__new__` triggers something? No.

Alternatively, we could construct a real instance by calling `__init__` with a mocked load_model... no, that's monkeypatching. So `__new__` it is.

Hmm, but is setting `processor` to a SimpleNamespace "faking the environment"? No, it's just data.

Actually, wait. Let me reconsider: could we use a real `ColPaliProcessor`? It requires loading from HF hub → network. No.

I'll go with SimpleNamespace.

Let me write the code.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch=32, image_seq_length=1024):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    processor = types.SimpleNamespace()
    if image_seq_length is not None:
        processor.image_seq_length = image_seq_length
    inst.processor = processor
    return inst
```

Wait — but `hasattr(self.processor, "image_seq_length")`. With SimpleNamespace having the attr → True. Good.

Now cell generation:

```python
def _cells(rng, n_cells, n_tokens, patch_hi, patch_lo=0, as_str=True):
    cells = []
    for _ in range(n_cells):
        patch = rng.randrange(patch_lo, patch_hi)
        qt = rng.randrange(n_tokens)
        value = rng.uniform(-1.0, 1.0)
        if as_str:
            cells.append({"address": {"patch": str(patch), "querytoken": str(qt)}, "value": value})
        else:
            cells.append({"address": {"patch": patch, "querytoken": qt}, "value": value})
    return cells
```

For a full grid, generate all combinations plus shuffle:

```python
def _full_cells(rng, n_tokens, patch_hi, as_str=True):
    cells = []
    for qt in range(n_tokens):
        for p in range(patch_hi):
            ...
    rng.shuffle(cells)
```

But generating all combos: n_tokens * patch_hi. For 8 tokens × 1024 = 8192 per map. Fine.

Let me write a generic builder for a list of maps:

```python
def _sim_maps(rng, n_maps, cell_builder):
    return [{"quantized": {"cells": cell_builder(rng, i)}} for i in range(n_maps)]
```

Hmm, simpler to build inline.

Let me just define per-case functions.

Also query_embs: torch tensor with shape (n_tokens, dim). Use torch.zeros or randn with fixed seed. Use `torch.randn(n_tokens, 128, generator=...)`? Simpler: torch.zeros((n_tokens, 128)). The values don't matter. But "avoid patterns a trick could exploit" — the function only uses size(0). Use torch.randn with a seeded generator for realism.

Let me write:

```python
def _query_embs(n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_tokens, 128, generator=g)
```

Now build cases. Each case thunk returns `(inst, query_embs, vespa_sim_maps)`.

But careful: the function doesn't modify its arguments (it creates a new tensor). So we can reuse the same vespa_sim_maps object across calls. Good — no need to copy. Actually it reads only. Good.

But the instance: reused fine.

Now, one concern: the output tensor is created fresh each call (torch.zeros). Fine.

Let me now write the 8 cases.

Case 1 typical:
```python
def _case_full(n_maps, n_tokens, patch_hi, n_patch=32, image_seq_length=1024, seed=0, as_str=True):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, image_seq_length)
    q = _query_embs(n_tokens, seed)
    maps = []
    for _ in range(n_maps):
        cells = []
        for qt in range(n_tokens):
            for p in range(patch_hi):
                cells.append({"address": {"patch": str(p) if as_str else p,
                                          "querytoken": str(qt) if as_str else qt},
                              "value": rng.uniform(-1, 1)})
        rng.shuffle(cells)
        maps.append({"quantized": {"cells": cells}})
    return inst, q, maps
```

Wait shuffle of lists of dicts — fine.

Case 1: _case_full(4, 8, 1024, seed=0) → 32768 cells.
Case 2: _case_full(12, 5, 1024, seed=1) → 61440 cells.
Case 3: _case_full(6, 8, 1024, image_seq_length=None, seed=2) → 49152 cells, fallback.
Case 4: skip-heavy: _case_full(8, 8, 1024, image_seq_length=256, seed=3) → 65536 cells.

Hmm, case 4 with 8*8*1024=65536 cells. That's a lot. Maybe reduce to 6 maps × 8 tokens = 49152.

Let me reduce: case 4: 6 maps, 8 tokens, 1024 patches, image_seq_length=256 → 49152 cells, 12288 assignments.

Case 5 duplicates: cells with patch from small pool, e.g., 8 maps, 8 tokens, 30000 cells with patch in [0,64). Output 65536.
Actually let's do 6 maps × 8 tokens = 49152 output, cells 30000 with duplicates.

Case 6 sparse: 16 maps, 6 tokens, 50 cells each → 4800 cells. Output 98304.
Hmm 16*6*1024 = 98304 output values. OK under 100k.

Case 7 n_patch=16: image_seq_length=256, 16 maps, 8 tokens, 256 patches → 32768 cells, output 32768.

Case 8 int-addresses: 8 maps, 8 tokens, full 1024 → 65536 cells. Too many; use 6 maps × 8 = 49152.

Let me finalize cell counts:
1. 4×8×1024 = 32768
2. 12×5×1024 = 61440
3. 6×8×1024 = 49152
4. 6×8×1024 = 49152 (75% skipped)
5. 6×8, 30000 cells (dups)
6. 16×6, 50 each = 4800
7. 16×8×256 = 32768
8. 6×8×1024 = 49152 (int addresses)

Total cells ≈ 32768+61440+49152+49152+30000+4800+32768+49152 = 309232. Memory heavy (~150MB?). Hmm.

Each cell dict: outer dict with 2 keys ("address", "value"): dict overhead ~184 bytes + 2 pointers. Inner "address" dict 2 keys: ~184 bytes. Two strings: each ~50 bytes. Float object ~24 bytes. Total ~500 bytes. 309k cells → 155MB. Over 100MB limit maybe (the limit says keep data under ~100MB — probably per input, but let's be safe).

Let's reduce. Use fewer cells. Also strings for numbers: "1023" small strings are interned? Not necessarily, but short strings ~50 bytes each.

Alternative: use integer patch/querytoken (no string allocation) for most cases, and strings only for one or two. Actually the function calls int() on them; using ints is valid and cheaper memory-wise (ints cached for small values? patch up to 1023 not cached, but int objects ~28 bytes).

Hmm. Let's just reduce counts.

Revised:
1. typical: 4 maps × 8 tokens × 1024 = 32768 cells. Keep.
2. many-images: 10 maps × 5 tokens × 1024 = 51200. 
3. fallback: 5 maps × 8 tokens × 1024 = 40960.
4. skip-heavy: 5 maps × 8 tokens × 1024 = 40960 (75% skip).
5. duplicates: 5 maps × 8 tokens, 20000 cells.
6. sparse: 16 maps × 6 tokens × 40 = 3840.
7. n_patch16: 12 maps × 8 tokens × 256 = 24576.
8. int addresses: 5 maps × 8 tokens × 1024 = 40960.

Total ≈ 32768+51200+40960+40960+20000+3840+24576+40960 = 255264 cells. Still ~128MB.

Hmm. Let's use ints for addresses mostly, and reduce further. Actually, maybe memory is fine — "under about 100 MB" is approximate. But let's try to be safe.

Alternative approach: generate cells lazily? No, must be built before timing.

Let's reduce cell counts more aggressively. The function's per-cell cost is what matters; we want heavy but not huge.

Let's target total ~150k cells.

1. typical: 4×8×1024 = 32768
2. many-images: 8×5×1024 = 40960
3. fallback: 4×8×1024 = 32768
4. skip-heavy: 4×8×1024 = 32768
5. duplicates: 4×8, 15000 cells
6. sparse: 16×6×40 = 3840
7. n_patch16: 12×8×256 = 24576
8. int: 4×8×1024 = 32768

Total ≈ 215k cells. ~107MB. Hmm.

Let's use ints for addresses in cases 1,2,3,4,8 and strings only in case 5 maybe. Ints: patch int object 28 bytes, querytoken int (small, cached for <257). Outer dict + inner dict ~ 400 bytes. 215k × 420 ≈ 90MB. Borderline.

Actually, dicts dominate. Let me reduce to ~150k total.

Hmm, actually let me reconsider: do we need full 1024 patches per token? The realistic Vespa map might have fewer cells. Let's use patch_hi = 1024 but not full grid; use random subset. But full grid gives max work.

I think a reasonable compromise: total cells ~150k.

Let me set:
1. typical: 3 maps × 8 tokens × 1024 = 24576
2. many-images: 8 maps × 5 tokens × 1024 = 40960
3. fallback: 4 maps × 8 tokens × 1024 = 32768
4. skip-heavy: 4 maps × 8 tokens × 1024 = 32768
5. duplicates: 4 maps × 8 tokens, 12000 cells
6. sparse: 16 maps × 6 tokens × 40 = 3840
7. n_patch16: 12 maps × 8 tokens × 256 = 24576
8. int: 4 maps × 8 tokens × 1024 = 32768

Total ≈ 194k. ~95MB. OK-ish.

Hmm, I keep going back and forth. Let's just accept ~200k cells; it's "about 100MB". Actually the guidance says "Keep the data in memory under about 100 MB". Let's aim lower to be safe: ~150k.

Reduce case 2 to 6 maps × 5 tokens = 30720. Case 8 to 3 maps × 8 = 24576.

Final:
1. 3×8×1024 = 24576
2. 6×5×1024 = 30720
3. 4×8×1024 = 32768
4. 4×8×1024 = 32768
5. 4 maps × 8 tokens, 12000 cells
6. 16×6×40 = 3840
7. 12×8×256 = 24576
8. 3×8×1024 = 24576

Total = 24576+30720+32768+32768+12000+3840+24576+24576 = 185824. ~90MB. Fine.

Now the outputs:
1. 3*8*1024 = 24576
2. 6*5*1024 = 30720
3. 4*8*1024 = 32768
4. 32768
5. 4*8*1024 = 32768
6. 16*6*1024 = 98304
7. 12*8*256 = 24576
8. 3*8*1024 = 24576

All under 100k. Good.

Now time: heaviest ~32768 cells → maybe 50-80ms. Plus torch.zeros allocation of 32768 floats — trivial. Good, within 1ms-200ms? The lightest, case 6, 3840 cells → maybe 8ms. Fine. All ≥1ms hopefully. Case 6 with 3840 cells ~ 6-10ms. OK.

Hmm, but if all are fast, fine.

Now, let me double check the skip logic: patch >= image_seq_length → continue. In case 4, image_seq_length=256, patches 0..1023, so 768/1024 skipped. Good.

But wait: for case 4, patch//n_patch for patch<256 → 0..7, valid. Good.

For case 7, n_patch=16, image_seq_length=256, patches 0..255, patch//16 = 0..15 valid.

Now for the fallback case (case 3), processor without image_seq_length → 1024, patches 0..1023, patch//32=0..31 valid.

Now let's write the code.

One more consideration: the thunk must return the arguments tuple. For a method called as `SimMapGenerator._prepare_similarity_map_tensor(instance, query_embs, vespa_sim_maps)`, thunk returns `(inst, q, maps)`.

Let me write the module-level builders.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch=32, image_seq_length=1024):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    processor = types.SimpleNamespace()
    if image_seq_length is not None:
        processor.image_seq_length = image_seq_length
    inst.processor = processor
    return inst


def _query_embs(n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_tokens, 128, generator=g)


def _full_map(rng, n_tokens, patch_hi, as_str):
    cells = []
    for qt in range(n_tokens):
        for p in range(patch_hi):
            cells.append({
                "address": {
                    "patch": str(p) if as_str else p,
                    "querytoken": str(qt) if as_str else qt,
                },
                "value": rng.uniform(-1.0, 1.0),
            })
    rng.shuffle(cells)
    return {"quantized": {"cells": cells}}
```

Then per-case builders.

Actually, I realize I should double check: `rng.shuffle(cells)` on list of dicts works.

Let me write a generic function:

```python
def _build(n_maps, n_tokens, patch_hi, n_patch=32, image_seq_length=1024,
           seed=0, as_str=True, full=True, cells_per_map=None, patch_pool=None):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, image_seq_length)
    q = _query_embs(n_tokens, seed)
    maps = []
    for _ in range(n_maps):
        if full:
            m = _full_map(rng, n_tokens, patch_hi, as_str)
        else:
            cells = []
            for _ in range(cells_per_map):
                if patch_pool is not None:
                    p = rng.choice(patch_pool)
                else:
                    p = rng.randrange(patch_hi)
                qt = rng.randrange(n_tokens)
                cells.append({
                    "address": {
                        "patch": str(p) if as_str else p,
                        "querytoken": str(qt) if as_str else qt,
                    },
                    "value": rng.uniform(-1.0, 1.0),
                })
            m = {"quantized": {"cells": cells}}
        maps.append(m)
    return inst, q, maps
```

Case 5 duplicates: patch_pool = list(range(64)), cells_per_map=3000, n_maps=4, n_tokens=8. 12000 cells.

Case 6 sparse: full=False, patch_pool=None, patch_hi=1024, cells_per_map=40, n_maps=16, n_tokens=6.

Hmm but with random patch in [0,1024) and image_seq_length=1024, all valid.

Now, cases list. Each thunk calls `_build(...)` — but that would rebuild each call! No — the thunk is called before each timed call. If the thunk builds the data, it's rebuilt every time, but that's not timed (only the function call is timed). However, "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it". Building 30k cells takes maybe 30ms, comparable to the call. It's not timed but it slows the overall run. Better to build at module level.

So: build all cases' data at module level, store in a dict/list, and thunks just return them.

But module-level code runs at import. Fine.

Let me structure:

```python
_CASES = {}
def _register(label, args):
    _CASES[label] = args
```

Actually simpler: build a list of (label, args) at module level, and cases() returns [(label, (lambda a=args: a)) for ...]. Careful with lambda closure.

```python
_BUILT = [
    ("typical", _build(3, 8, 1024, seed=0)),
    ...
]

def cases():
    return [(label, (lambda a=args: a)) for label, args in _BUILT]
```

Wait, the thunk must return a tuple of positional args. `_build` returns a tuple `(inst, q, maps)`. So `lambda a=args: a` returns that tuple. Good.

But careful: the function doesn't modify args, so returning the same objects each time is fine.

Hmm, one subtlety: `torch.zeros` output — the function creates new tensor each call. Good.

Now checks(): small edge inputs, built at module level too.

```python
def checks():
    inst = _make_instance(32, 1024)
    q1 = torch.zeros(1, 128)
    empty_map = {"quantized": {"cells": []}}
    single = {"quantized": {"cells": [{"address": {"patch": "0", "querytoken": "0"}, "value": 0.5}]}}
    return [
        ("no-maps", lambda: (inst, q1, [])),
        ("empty-cells", lambda: (inst, q1, [empty_map])),
        ("single-cell", lambda: (inst, q1, [single])),
    ]
```

Wait, "no-maps" gives tensor shape (0,1,32,32). Fine.

Also maybe an odd type check: patch as a non-numeric string would raise ValueError. That's allowed in checks. But let's keep it simple; maybe add one odd: querytoken out of range → IndexError. Actually checks "may raise". Let's include one: a cell with patch = "abc" → int() raises ValueError. Hmm, but that's a weird input. Let's include it as the odd-type check.

Actually the instructions: "2 or 3 small edge inputs (empty, one element, None, an odd type)". Let's do:
1. empty list of maps
2. one map with empty cells
3. a cell with patch as a string "0" and querytoken "0" — normal single.

Maybe better odd type: value as an int (not float) — works. Or patch as float string "3.0" → int("3.0") raises ValueError. That's an odd type. Let's do that as the third.

Hmm, but the third might raise — that's fine for checks.

Let me do:
1. ("no-maps", ...)
2. ("empty-cells", ...)
3. ("odd-patch-type", patch="3.0") → raises ValueError. Both original and modified raise the same.

Actually, wait: we compare outputs; if both raise, presumably they compare the exception. Should be fine.

Hmm, but is it safe? If the modified version handles it differently... well, we can't know. Let's keep it simple and safe: use a valid single cell. Actually the instructions explicitly want edge cases that may raise. I'll include one that raises (odd type) — it tests identical behavior.

Let me include all three: empty, single valid, odd type.

Now, another thought: `from backend.colpali import SimMapGenerator` — does importing backend.colpali work in the test environment? The task says import exactly as shown. OK.

But there's a risk: `backend.colpali` imports `colpali_engine` which may require torch etc. Should be installed.

Also, `cm.viridis` at class definition requires matplotlib. Fine.

Now let me double-check the instance creation. `SimMapGenerator.__new__(SimMapGenerator)` — object.__new__ requires no extra args. Works.

But hold on: is it acceptable per the rules? "No mocks, no monkeypatching... no subclass that overrides a method". We're not subclassing. We're creating an instance without __init__ and setting fields. The rules say "Setting data (a module's configuration, an object's fields) to build an input is fine." Yes.

The processor being a SimpleNamespace: it's an object whose field `image_seq_length` is set. The function only reads that. Acceptable.

Hmm, but is there a concern that the "modified version" might behave differently? Not our concern.

Let me now also double check the tensor indexing: `vespa_sim_map_tensor[idx, query_token, patch // self.n_patch, patch % self.n_patch] = value`. query_token must be < query_embs.size(0) = n_tokens. We generate qt in [0, n_tokens). Good.

Now writing final code.

One more: the `_build` for full maps with as_str — for case 8 we use as_str=False (int addresses).

Let me write it out.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    processor = types.SimpleNamespace()
    if image_seq_length is not None:
        processor.image_seq_length = image_seq_length
    inst.processor = processor
    return inst


def _query_embs(n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_tokens, 128, generator=g)


def _cell(rng, patch, qt, as_str):
    return {
        "address": {
            "patch": str(patch) if as_str else patch,
            "querytoken": str(qt) if as_str else qt,
        },
        "value": rng.uniform(-1.0, 1.0),
    }


def _build(n_maps, n_tokens, patch_hi, n_patch=32, image_seq_length=1024,
           seed=0, as_str=True, full=True, cells_per_map=None, patch_pool=None):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, image_seq_length)
    q = _query_embs(n_tokens, seed)
    maps = []
    for _ in range(n_maps):
        if full:
            cells = [_cell(rng, p, qt, as_str)
                     for qt in range(n_tokens) for p in range(patch_hi)]
            rng.shuffle(cells)
        else:
            cells = []
            for _ in range(cells_per_map):
                p = rng.choice(patch_pool) if patch_pool is not None else rng.randrange(patch_hi)
                cells.append(_cell(rng, p, rng.randrange(n_tokens), as_str))
        maps.append({"quantized": {"cells": cells}})
    return inst, q, maps
```

Wait, `_query_embs` uses seed; for case 3 with image_seq_length=None, seed=2. Fine.

Now build the list:

```python
_BUILT = [
    ("typical", _build(3, 8, 1024, seed=0)),
    ("many-images", _build(6, 5, 1024, seed=1)),
    ("fallback-seq-len", _build(4, 8, 1024, image_seq_length=None, seed=2)),
    ("skip-heavy", _build(4, 8, 1024, image_seq_length=256, seed=3)),
    ("duplicates", _build(4, 8, 1024, seed=4, full=False, cells_per_map=3000, patch_pool=list(range(64)))),
    ("sparse-many-maps", _build(16, 6, 1024, seed=5, full=False, cells_per_map=40)),
    ("n-patch-16", _build(12, 8, 256, n_patch=16, image_seq_length=256, seed=6)),
    ("int-addresses", _build(3, 8, 1024, seed=7, as_str=False)),
]
```

Check case 6: full=False, cells_per_map=40, patch_pool=None → patch = rng.randrange(1024). Good.

Case 5: patch_pool=list(range(64)), 3000 cells per map, 4 maps = 12000 cells. Output 4*8*1024=32768.

Hmm, wait: for case 5, duplicates with patch in [0,64): patch//32 in {0,1}. Fine.

Now, memory: total cells = 24576+30720+32768+32768+12000+3840+24576+24576 = 185824. OK.

Now cases():

```python
def cases():
    return [(label, (lambda args=args: args)) for label, args in _BUILT]
```

checks():

```python
def checks():
    inst = _make_instance(32, 1024)
    q = torch.zeros(1, 128)
    return [
        ("no-maps", lambda: (inst, q, [])),
        ("empty-cells", lambda: (inst, q, [{"quantized": {"cells": []}}])),
        ("single-cell", lambda: (inst, q, [{"quantized": {"cells": [
            {"address": {"patch": "0", "querytoken": "0"}, "value": 0.5}]}}])),
    ]
```

Hmm, "single-cell" with patch "0" and querytoken "0" — fine.

Should I add an odd type that raises? Let's add a 4th? No, max 3. Let's replace "single-cell" with an odd type? The instructions say checks: 2 or 3 small edge inputs (empty, one element, None, an odd type). Three is fine: empty maps, empty cells, single cell. That covers empty and one element. Maybe make the third an odd type: patch as float string. Let's do:

3. ("odd-patch", patch="1.5") → int("1.5") raises ValueError.

That tests identical exception behavior. I'll include it. Actually, to be safe maybe keep a valid one too... but only 3 allowed. I'll do empty maps, empty cells, odd patch type.

Hmm, "empty cells" and "empty maps" both empty-ish. Let's do: no-maps, single-cell (one element), odd-patch (odd type). That's more diverse.

Final checks:
1. ("no-maps", [])
2. ("single-cell", one map one cell)
3. ("odd-patch-type", patch="1.5")

Let me write.

Actually wait — for the odd patch type, `int("1.5")` raises ValueError. Good, both versions raise.

Now, one concern about `_make_instance` being called at module level and the instance being shared across all calls. The function doesn't modify self. Good.

Another concern: `torch.randn(n_tokens, 128, generator=g)` — the default dtype float32. Fine.

Let me also double check: `query_embs.size(0)` = n_tokens. Good.

I think we're set. Let me also verify the output tensor dtype: torch.zeros default float32. Assigning float values. Fine.

One more: the function is `_prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps)`. Called as `SimMapGenerator._prepare_similarity_map_tensor(inst, q, maps)`. So the thunk returns `(inst, q, maps)`. Yes.

Let me finalize.

Actually, let me reconsider whether creating the instance via `__new__` might be considered problematic. The alternative would be to call `SimMapGenerator(logger=...)` which downloads the model — network access → CANNOT RUN. Since the function under test doesn't need the model, using `__new__` and setting the two attributes it reads is the right approach. The task explicitly allows setting an object's fields.

I'm fairly confident.

Let me write the final code block.

Double-check imports: random, types, torch, backend.colpali. That's it.

Final code:

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    processor = types.SimpleNamespace()
    if image_seq_length is not None:
        processor.image_seq_length = image_seq_length
    inst.processor = processor
    return inst


def _query_embs(n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_tokens, 128, generator=g)


def _cell(rng, patch, qt, as_str):
    return {
        "address": {
            "patch": str(patch) if as_str else patch,
            "querytoken": str(qt) if as_str else qt,
        },
        "value": rng.uniform(-1.0, 1.0),
    }


def _build(n_maps, n_tokens, patch_hi, n_patch=32, image_seq_length=1024,
           seed=0, as_str=True, full=True, cells_per_map=None, patch_pool=None):
    rng = random.Random(seed)
    inst = _make_instance(n_patch, image_seq_length)
    q = _query_embs(n_tokens, seed)
    maps = []
    for _ in range(n_maps):
        if full:
            cells = [_cell(rng, p, qt, as_str)
                     for qt in range(n_tokens) for p in range(patch_hi)]
            rng.shuffle(cells)
        else:
            cells = []
            for _ in range(cells_per_map):
                p = rng.choice(patch_pool) if patch_pool is not None else rng.randrange(patch_hi)
                cells.append(_cell(rng, p, rng.randrange(n_tokens), as_str))
        maps.append({"quantized": {"cells": cells}})
    return inst, q, maps


_BUILT = [
    ("typical", _build(3, 8, 1024, seed=0)),
    ("many-images", _build(6, 5, 1024, seed=1)),
    ("fallback-seq-len", _build(4, 8, 1024, image_seq_length=None, seed=2)),
    ("skip-heavy", _build(4, 8, 1024, image_seq_length=256, seed=3)),
    ("duplicates", _build(4, 8, 1024, seed=4, full=False, cells_per_map=3000, patch_pool=list(range(64)))),
    ("sparse-many-maps", _build(16, 6, 1024, seed=5, full=False, cells_per_map=40)),
    ("n-patch-16", _build(12, 8, 256, n_patch=16, image_seq_length=256, seed=6)),
    ("int-addresses", _build(3, 8, 1024, seed=7, as_str=False)),
]


def cases():
    return [(label, (lambda args=args: args)) for label, args in _BUILT]


def checks():
    inst = _make_instance(32, 1024)
    q = torch.zeros(1, 128)
    return [
        ("no-maps", lambda: (inst, q, [])),
        ("single-cell", lambda: (inst, q, [{"quantized": {"cells": [
            {"address": {"patch": "0", "querytoken": "0"}, "value": 0.5}]}}])),
        ("odd-patch-type", lambda: (inst, q, [{"quantized": {"cells": [
            {"address": {"patch": "1.5", "querytoken": "0"}, "value": 0.5}]}}])),
    ]
```

Wait, in checks "single-cell", query_embs has 1 token, querytoken "0" → index 0 valid. patch "0" → 0. Good.

I think this is good. One last check on case 3: image_seq_length=None → processor has no attribute → fallback 1024. patch_hi=1024, patches 0..1023 < 1024. Good.

Case 4: image_seq_length=256, patch_hi=1024. patches 0..1023; those >=256 skipped. patch//32 for patch<256 → 0..7. Good.

Case 7: n_patch=16, image_seq_length=256, patch_hi=256. patch 0..255; patch//16 → 0..15 < 16. Good.

All good.