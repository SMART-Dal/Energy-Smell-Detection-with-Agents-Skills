The tricky part: constructing a `SimMapGenerator` instance requires loading the ColPali model (network access / heavy). We can't call `__init__`. But the method only uses `self.n_patch` and `self.processor`. We can create an instance without calling `__init__` via `object.__new__(SimMapGenerator)` and set attributes. Is that "faking"? Setting data (an object's fields) to build an input is fine. The instruction says setting an object's fields to build an input is fine. So `obj = object.__new__(SimMapGenerator); obj.n_patch = 32; obj.processor = <something with image_seq_length>`. The processor is just read for `image_seq_length`. We could set processor to a simple object... but that might be seen as a mock. Hmm. Actually `hasattr(self.processor, "image_seq_length")` - we need a processor-like object. Using `types.SimpleNamespace(image_seq_length=1024)` is setting a field on a stand-in. It's borderline but the function only reads that attribute. The rule says no mocks that replace code — a subclass that overrides methods. Here processor isn't called at all, just attribute read. I think SimpleNamespace is acceptable as data. Alternatively we can just not set processor at all and let `hasattr` be False, taking the 1024 branch. That's the fallback path and requires no processor object. But then we only test one branch. We could do both: some cases with processor having image_seq_length, some without.

Actually to avoid mock concerns, we could use `object.__new__(SimMapGenerator)` and set `n_patch` and `processor`. For processor, we can use a SimpleNamespace. Hmm, but the rule "no assigning functions or lambdas to attributes" — SimpleNamespace with only data attribute is fine.

Actually even simpler: don't set processor at all → hasattr False → image_seq_length = 1024. That's a valid path. But we want diversity. Let's include some instances with processor set to SimpleNamespace(image_seq_length=...) to exercise the other branch. I think that's fine — it's data, not behavior.

Wait, but the class attribute `colormap` etc. is fine.

Also, importing `backend.colpali` imports colpali_engine, torch, PIL, matplotlib. Those must be installed. Presumably they are in the environment. Risky but the task says use packages the repository already imports.

Actually, can we avoid importing the module? No, we must import it as instructed.

Hmm, importing colpali_engine may be heavy but fine.

Now the tensor: `torch.zeros((len(vespa_sim_maps), query_embs.size(0), n_patch, n_patch))`. query_embs.size(0) is number of query tokens. In practice query_embs is a tensor of shape (num_tokens, dim). So query_token must be < query_embs.size(0) to avoid index error.

Let's design cases with realistic Vespa sim maps: each is a dict with "quantized" -> "cells", each cell has "address" -> {"patch": str, "querytoken": str}, "value": float.

n_patch default 32, image_seq_length 1024 → patches 0..1023, so patch//32 in 0..31.

Query tokens: real queries maybe 10-40 tokens. Let's use various sizes.

Output size: len(vespa_sim_maps) * num_tokens * 32 * 32. Keep under 100k values. E.g. 4 maps * 30 tokens * 1024 = 122880 — slightly over. Let's keep it modest: 4*20*1024 = 81920. Fine.

Actually the returned tensor is compared in full — 100k values limit. Let's keep to ~80k max.

Number of cells per map: real Vespa returns top-k cells per (query token, patch)? Actually Vespa sim maps contain cells for the top matches. Let's make each map have maybe 20k-50k cells to make it take ~1ms-200ms.

Let me estimate: the inner loop is pure Python, ~ maybe 1-2 µs per cell. 50k cells → ~50-100ms. Good.

Let's design 8 cases:
1. small typical: 1 map, 10 tokens, 5000 cells
2. many maps: 4 maps, 20 tokens, 10000 cells each
3. large cells: 1 map, 30 tokens, 80000 cells
4. patches beyond image_seq_length (continue path): many cells with patch >= 1024
5. processor without image_seq_length (fallback 1024)
6. processor with image_seq_length = 512 (smaller limit → more skips)
7. dense coverage: all patches covered, values varied
8. high query token count with sparse cells

Need distinct labels.

Also note: `hasattr(self.processor, ...)` is checked inside the loop for every cell — so it's part of the work. Fine.

Important: the function does not modify its arguments. query_embs and vespa_sim_maps are only read. So we can reuse the same objects across thunk calls. Good — but wait, thunks are called before each timed call; returning the same objects is fine since function doesn't mutate. To be safe we can rebuild... no, keep cheap. Actually the tensor returned is new each time. The inputs are not modified. Good.

But careful: "Its arguments are rendered before and after each call to see whether it changed them" — rendering a 1M-value structure is slow. vespa_sim_maps with 80k cells each dict with nested dicts... rendering could be slow. Hmm. "keep each input's data under about 1,000,000 values". 80k cells × ~5 values = 400k. That's under 1M but rendering might be slow. Let's keep it moderate. Maybe max 30k cells per map, total across maps maybe 60k cells. That's ~300k values. Hmm rendering is done by their harness; fine.

Actually let's reconsider: how many cells does a real Vespa sim map have? The vespa sim map is typically the top-k per query token per patch. With image_seq_length 1024 patches and ~20 query tokens, could be large. But let's just choose realistic-ish.

Let me think about cell structure more precisely. In the repo, vespa_sim_maps come from Vespa response. Each cell: {"address": {"patch": "...", "querytoken": "..."}, "value": ...}. Actually the "quantized" key suggests the response has quantized cells.

Let's just build it.

Now the instance. We need it per case? The instance is passed as first arg. We can create module-level instances with different n_patch and processor settings.

Let's define:

```python
def _make_generator(n_patch=32, image_seq_length=None):
    gen = object.__new__(SimMapGenerator)
    gen.n_patch = n_patch
    gen.processor = types.SimpleNamespace(image_seq_length=image_seq_length) if image_seq_length is not None else types.SimpleNamespace()
    return gen
```

Hmm, if image_seq_length is None we set processor without the attribute → fallback branch. If we want no processor at all... SimpleNamespace() has no image_seq_length, hasattr False. Fine.

Actually is SimpleNamespace a mock? It's a plain data holder. The function never calls methods on processor. I'll go with it. Alternatively use a tiny class defined in our source. Same thing. I'll use SimpleNamespace.

Hmm, but the rule says "no subclass that overrides a method of a repository or library class". SimpleNamespace isn't a subclass. Fine.

Now n_patch: the class default is 32. Could use other values e.g. 16, 64 to vary. But query_embs size(0) must exceed query tokens.

Let's build cells generator:

```python
def _make_sim_map(n_cells, n_patches, n_tokens, seed, max_patch=None, value_scale=1.0):
    rng = random.Random(seed)
    cells = []
    for _ in range(n_cells):
        patch = rng.randrange(max_patch if max_patch else n_patches)
        qt = rng.randrange(n_tokens)
        cells.append({
            "address": {"patch": str(patch), "querytoken": str(qt)},
            "value": round(rng.uniform(-1, 1) * value_scale, 6),
        })
    return {"quantized": {"cells": cells}}
```

Note: `int(cell["address"]["patch"])` — strings. Real Vespa returns strings. Good.

Now query_embs: torch tensor of shape (n_tokens, 128). Values don't matter, only size(0). Use torch.randn? That's fine but for speed just torch.zeros. Actually the function only reads size(0). Use torch.zeros((n_tokens, 128)).

But rendering the tensor before/after: 30*128 = 3840 values. Fine.

Cases:

1. "single-map-small": gen default (n_patch=32, processor with image_seq_length=1024), 1 map, 5000 cells, 10 tokens.
2. "multi-map": 4 maps, 8000 cells each, 20 tokens.
3. "dense-cells": 1 map, 30000 cells, 25 tokens, patches up to 1024.
4. "oversized-patches": 1 map, 20000 cells, 15 tokens, patches up to 2048 (half skipped).
5. "no-image-seq-length": processor without attr, 1 map, 15000 cells, 20 tokens.
6. "small-image-seq-length": image_seq_length=512, 1 map, 20000 cells, 20 tokens, patches up to 1024 (half skipped).
7. "n-patch-16": n_patch=16, 2 maps, 10000 cells each, 30 tokens.
8. "many-tokens-sparse": 3 maps, 3000 cells each, 40 tokens.

Check output sizes:
1. 1*10*32*32 = 10240 ✓
2. 4*20*1024 = 81920 ✓
3. 1*25*1024 = 25600 ✓
4. 1*15*1024 = 15360 ✓
5. 1*20*1024 = 20480 ✓
6. 1*20*1024 = 20480 ✓
7. 2*30*16*16 = 15360 ✓
8. 3*40*1024 = 122880 ✗ over 100k. Reduce to 2 maps → 81920. Or 40 tokens with n_patch 32: 3*40*1024=122880. Use 2 maps → 81920 ✓.

Wait, but also cells with query_token >= n_tokens would crash. Ensure qt < n_tokens. Yes.

Total cell counts: 5000 + 32000 + 30000 + 20000 + 15000 + 20000 + 20000 + 6000 = 148000 cells. Each cell ~4 values → ~600k values total. Under 1M. Hmm, that's total across all inputs, and the harness renders each input before/after each call. 148k cells rendering... could be slow but let's reduce a bit. Actually rendering is per-input, and each input rendered twice per call, many calls. Hmm, that could be very slow.

But the instructions say keep under 1M values. Let's reduce cell counts to be safer: total maybe 80k cells.

Let me reconsider timing: 1-2µs per cell → 80k cells ≈ 100ms. Ok.

Let's reduce:
1. 4000 cells
2. 4 maps × 5000 = 20000
3. 20000
4. 15000
5. 10000
6. 12000
7. 2 × 6000 = 12000
8. 2 × 3000 = 6000

Total 95000 cells. Hmm still. Each cell has 3 dicts + 2 strings + value → maybe 6 values → 570k. Under 1M. OK.

Actually, wait — rendering probably uses repr, which for nested dicts is slow. 95k cells → repr could take ~1s. Times many calls... The harness presumably handles it. But to be safe, let's cut further. Let's aim ~50k cells total.

1. 3000
2. 4 × 3000 = 12000
3. 12000
4. 8000
5. 6000
6. 8000
7. 2 × 3000 = 6000
8. 2 × 2000 = 4000

Total 59000 cells. Timing: ~60-120ms for the big ones, small ones ~6ms. The requirement is 1ms-200ms. Small ones: 3000 cells ≈ 5ms. Fine.

Hmm, but "keep the 4 that do the most work" — the harness picks. Fine.

Let me make the big ones bigger to ensure substantial work: case 2 with 4 maps × 8000 = 32000 cells ≈ 50ms. Let's do that. And case 3: 20000 cells.

Revised:
1. single map, 3000 cells, 10 tokens → ~5ms
2. 4 maps × 8000 = 32000 cells, 20 tokens → ~50ms
3. 1 map, 20000 cells, 25 tokens → ~30ms
4. 1 map, 12000 cells with patches up to 2048 (half skipped), 15 tokens → ~20ms
5. no image_seq_length, 1 map, 10000 cells, 20 tokens
6. image_seq_length=512, 1 map, 15000 cells patches up to 1024, 20 tokens
7. n_patch=16, 2 maps × 6000, 30 tokens
8. 2 maps × 3000, 40 tokens

Total cells: 3000+32000+20000+12000+10000+15000+12000+6000 = 110000. Hmm. That's a lot of rendering.

Let me trim to ~70k: 
1. 3000
2. 4×6000=24000
3. 15000
4. 10000
5. 8000
6. 12000
7. 2×4000=8000
8. 2×2500=5000
Total 75000.

Ok. I'll go with something like this.

Actually, hold on. Rendering of arguments: "Its arguments are rendered before and after each call". If rendering takes 0.5s per call and there are many calls, this could be brutal but it's the harness's problem. Still, let's be reasonable. 75k cells.

Hmm, actually maybe I should reduce more. The output tensor is also compared in full — up to 81920 floats. That's fine.

Let me just go with moderate sizes.

Now the checks():
- empty vespa_sim_maps list: returns tensor of shape (0, n_tokens, 32, 32). Works.
- empty cells: map with no cells.
- query_embs with size(0)=0? Then tensor shape (1,0,32,32) and any cell write would index query_token out of range → error. That's a check that may raise. Actually a cell with querytoken 0 would raise IndexError. Let's include: single map with one cell and query_embs of 0 tokens → raises. Good as an edge/odd case.

Hmm but checks "may raise" — fine.

Let's write checks:
1. ("empty-maps", lambda: (gen, torch.zeros((5,128)), []))
2. ("empty-cells", lambda: (gen, torch.zeros((5,128)), [{"quantized": {"cells": []}}]))
3. ("zero-tokens", lambda: (gen, torch.zeros((0,128)), [{"quantized": {"cells": [{"address": {"patch": "0", "querytoken": "0"}, "value": 1.0}]}}]))

Wait, for check 1, output is shape (0,5,32,32) — that's a valid tensor with 0 elements. Fine.

Now, module-level: importing backend.colpali. The path: `visual-retrieval-colpali/src/backend/colpali.py`. Import as `from backend.colpali import SimMapGenerator`. So `src` must be on sys.path. Presumably the harness sets it up. The task says "Import the repository's modules exactly as shown in the task." So just do `from backend.colpali import SimMapGenerator`.

But wait — importing colpali imports colpali_engine which may try to download models? No, importing is fine. `get_torch_device` from torch_utils. Fine.

Also the module imports `matplotlib.cm`. Fine.

One concern: `SimMapGenerator` class body has `colormap = cm.viridis` — fine.

Now, creating instances without __init__: `object.__new__(SimMapGenerator)`. Since SimMapGenerator has no custom __new__ or __setattr__, this works.

Let's write it.

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator

_N_TOKENS_DIM = 128

def _make_gen(n_patch=32, image_seq_length=1024):
    gen = object.__new__(SimMapGenerator)
    gen.n_patch = n_patch
    if image_seq_length is None:
        gen.processor = types.SimpleNamespace()
    else:
        gen.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return gen

def _sim_map(n_cells, n_tokens, seed, max_patch=1024, value_scale=1.0):
    rng = random.Random(seed)
    cells = []
    for _ in range(n_cells):
        cells.append({
            "address": {
                "patch": str(rng.randrange(max_patch)),
                "querytoken": str(rng.randrange(n_tokens)),
            },
            "value": round(rng.uniform(-value_scale, value_scale), 6),
        })
    return {"quantized": {"cells": cells}}

def _embs(n_tokens):
    return torch.zeros((n_tokens, _N_TOKENS_DIM))
```

Wait — `torch.zeros` for query_embs: the function only uses size(0). Fine, and cheap.

Hmm, but is using zeros "avoiding patterns"? It doesn't matter; the values are unused.

Now module-level build all data.

```python
_GEN_DEFAULT = _make_gen(32, 1024)
_GEN_FALLBACK = _make_gen(32, None)   # processor without image_seq_length
_GEN_SMALL_SEQ = _make_gen(32, 512)
_GEN_P16 = _make_gen(16, 1024)
```

Wait, for _GEN_FALLBACK I set image_seq_length=None → SimpleNamespace() without attribute → hasattr False. Good.

Now cases:

```python
def cases():
    return [
        ("single-map-small", lambda: (_GEN_DEFAULT, _EMBS_A, [_MAP_A])),
        ...
    ]
```

But careful — the thunk returns a tuple of positional args: (instance, query_embs, vespa_sim_maps). The method is called as `SimMapGenerator._prepare_similarity_map_tensor(instance, ...)`. Hmm — how does the harness handle the method? The task says "the method is called as `SimMapGenerator._prepare_similarity_map_tensor(instance, ...)`". So the thunk should return (instance, query_embs, vespa_sim_maps)? Or does the harness pass instance separately?

The instructions: "A method is called as a plain function: the thunk builds the instance and passes it as the first argument". So yes, thunk returns (instance, query_embs, vespa_sim_maps).

Good.

Now let me define the module-level data.

Case 1: single map, 3000 cells, 10 tokens.
Case 2: 4 maps × 6000 cells, 20 tokens.
Case 3: 1 map, 15000 cells, 25 tokens.
Case 4: 1 map, 10000 cells, max_patch=2048, 15 tokens.
Case 5: fallback gen, 1 map, 8000 cells, 20 tokens.
Case 6: small seq 512, 1 map, 12000 cells, max_patch=1024, 20 tokens.
Case 7: n_patch 16, 2 maps × 4000, 30 tokens.
Case 8: 2 maps × 2500, 40 tokens.

Output shapes:
1. 1*10*32*32 = 10240
2. 4*20*1024 = 81920
3. 1*25*1024 = 25600
4. 1*15*1024 = 15360
5. 1*20*1024 = 20480
6. 1*20*1024 = 20480
7. 2*30*256 = 15360
8. 2*40*1024 = 81920

All under 100k. 

Now, potential issue: for case 8 with 40 tokens and 2 maps, cells 2500 each — many (patch, querytoken) collisions, fine.

Another consideration: `vespa_sim_map_tensor[idx, query_token, patch//n_patch, patch%n_patch] = value` — value is a Python float, fine.

Now, will the function mutate vespa_sim_maps? No. So reuse across calls is fine.

But wait: the tensor assignment with a float value — torch will handle.

Let me also double check `int(cell["address"]["patch"])` works with str. Yes.

Now let's write the final code.

One more thought: should I worry that `object.__new__(SimMapGenerator)` might be considered "faking"? The alternative is calling __init__ which loads a model from HuggingFace (network). Not possible. The instructions say setting an object's fields to build an input is fine. Good.

Also logger attribute not needed.

Let me write it out.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


_EMB_DIM = 128


def _make_generator(n_patch=32, image_seq_length=1024):
    gen = object.__new__(SimMapGenerator)
    gen.n_patch = n_patch
    if image_seq_length is None:
        gen.processor = types.SimpleNamespace()
    else:
        gen.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return gen


def _make_sim_map(n_cells, n_tokens, seed, max_patch=1024, value_scale=1.0):
    rng = random.Random(seed)
    cells = []
    for _ in range(n_cells):
        cells.append(
            {
                "address": {
                    "patch": str(rng.randrange(max_patch)),
                    "querytoken": str(rng.randrange(n_tokens)),
                },
                "value": round(rng.uniform(-value_scale, value_scale), 6),
            }
        )
    return {"quantized": {"cells": cells}}


def _make_embs(n_tokens):
    return torch.zeros((n_tokens, _EMB_DIM))


_GEN_DEFAULT = _make_generator(32, 1024)
_GEN_FALLBACK = _make_generator(32, None)
_GEN_SMALL_SEQ = _make_generator(32, 512)
_GEN_P16 = _make_generator(16, 1024)

_EMBS_10 = _make_embs(10)
_EMBS_15 = _make_embs(15)
_EMBS_20 = _make_embs(20)
_EMBS_25 = _make_embs(25)
_EMBS_30 = _make_embs(30)
_EMBS_40 = _make_embs(40)

_MAP_1 = _make_sim_map(3000, 10, 0)
_MAPS_2 = [_make_sim_map(6000, 20, 1 + i) for i in range(4)]
_MAP_3 = _make_sim_map(15000, 25, 10)
_MAP_4 = _make_sim_map(10000, 15, 11, max_patch=2048)
_MAP_5 = _make_sim_map(8000, 20, 12)
_MAP_6 = _make_sim_map(12000, 20, 13, max_patch=1024)
_MAPS_7 = [_make_sim_map(4000, 30, 14 + i) for i in range(2)]
_MAPS_8 = [_make_sim_map(2500, 40, 20 + i) for i in range(2)]


def checks():
    return [
        ("empty-maps", lambda: (_GEN_DEFAULT, _make_embs(5), [])),
        ("empty-cells", lambda: (_GEN_DEFAULT, _make_embs(5), [{"quantized": {"cells": []}}])),
        ("zero-tokens", lambda: (
            _GEN_DEFAULT,
            _make_embs(0),
            [{"quantized": {"cells": [{"address": {"patch": "0", "querytoken": "0"}, "value": 1.0}]}}],
        )),
    ]


def cases():
    return [
        ("single-map-small", lambda: (_GEN_DEFAULT, _EMBS_10, [_MAP_1])),
        ("four-maps", lambda: (_GEN_DEFAULT, _EMBS_20, _MAPS_2)),
        ("dense-single-map", lambda: (_GEN_DEFAULT, _EMBS_25, [_MAP_3])),
        ("oversized-patches", lambda: (_GEN_DEFAULT, _EMBS_15, [_MAP_4])),
        ("no-image-seq-length", lambda: (_GEN_FALLBACK, _EMBS_20, [_MAP_5])),
        ("small-image-seq-length", lambda: (_GEN_SMALL_SEQ, _EMBS_20, [_MAP_6])),
        ("n-patch-16", lambda: (_GEN_P16, _EMBS_30, _MAPS_7)),
        ("many-tokens", lambda: (_GEN_DEFAULT, _EMBS_40, _MAPS_8)),
    ]
```

Wait — `_make_embs` in checks is called each thunk call; that's cheap and fine. But building torch.zeros in checks is fine.

Hmm, one issue: in checks, the "zero-tokens" case — query_embs.size(0)=0, so tensor shape (1,0,32,32), and writing at index [0,0,...] raises IndexError. Good, it may raise.

Actually, wait: does it raise? `vespa_sim_map_tensor[0, 0, 0, 0] = value` on a tensor of shape (1,0,32,32) → IndexError. Yes.

Another concern: the "empty-maps" check returns a tensor of shape (0,5,32,32) — fine.

Now, `_MAPS_2` uses seeds 1,2,3,4. Fine.

One more concern: the harness renders arguments. `_EMBS_*` tensors are 10-40 × 128 = up to 5120 floats. Fine.

Potential issue: `torch.zeros` default dtype float32; assigning Python float works.

Another potential issue: importing backend.colpali requires `colpali_engine` installed. If not, we cannot run. But the task expects it. I'll assume available.

Actually — should I double-check whether importing colpali_engine at module import triggers heavy stuff? `from colpali_engine.models import ColPali, ColPaliProcessor` — imports transformers etc. Should be fine, no network.

Let me finalize. Also add `import torch` at top — the module imports torch anyway but we use it directly.

I think this is good. One thing: the instruction says "Use only the standard library, the repository itself and packages the repository already imports." torch is imported by the repo module. types and random are stdlib. Good.

Final answer.