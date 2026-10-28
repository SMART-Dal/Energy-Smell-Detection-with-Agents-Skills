Let me analyze the function. It's a method `_prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps)`.

It uses `self.n_patch`, and `self.processor` (checks `hasattr(self.processor, "image_seq_length")`).

The instance is built via `SimMapGenerator.__init__` which loads a model — that requires network/downloading models. But we don't need to call `__init__`. We can build the instance without calling `__init__`, e.g. using `object.__new__(SimMapGenerator)` and setting attributes. Is that allowed? The instructions say: "A method is called as a plain function: the thunk builds the instance and passes it as the first argument". Setting data (an object's fields) to build an input is fine. So we can create an instance via `object.__new__` and set `n_patch` and `processor`.

The processor needs `image_seq_length` attribute (or not). We can use a simple object with `image_seq_length` set. But careful: "no subclass that overrides a method of a repository or library class". Creating a plain SimpleNamespace as a processor is fine — it's not a subclass, just a data holder. Actually the function only does `hasattr(self.processor, "image_seq_length")`. So a namespace works. But maybe better to use the real ColPaliProcessor? That would require loading a model. Not feasible. Using a simple object is fine — it's data, not a mock of a method.

Actually, could we avoid the processor entirely by setting `processor = None`? Then `hasattr(None, "image_seq_length")` is False → image_seq_length = 1024. That's a valid path. But we also want the other path. Let's have cases with a namespace having image_seq_length.

Let me write:

```python
import random
import types
import torch
from backend.colpali import SimMapGenerator

def _make_instance(n_patch=32, image_seq_length=None):
    obj = object.__new__(SimMapGenerator)
    obj.n_patch = n_patch
    if image_seq_length is None:
        obj.processor = None
    else:
        obj.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return obj
```

Wait — `hasattr(None, "image_seq_length")` → False. Good.

Now build vespa_sim_maps. Structure: list of dicts, each `{"quantized": {"cells": [ {"address": {"patch": ..., "querytoken": ...}, "value": ...}, ...]}}`.

query_embs: torch.Tensor with size(0) = number of query tokens. Use `torch.randn(n_tokens, dim)`.

n_patch = 32 typically. patch // 32 and patch % 32. image_seq_length typically 1024 (32*32). So patches 0..1023.

Let's make realistic workloads: multiple sim maps (images), each with cells. Cells count could be large. The loop is Python-level, so each cell iteration is costly. To get 1ms-200ms, we need maybe thousands to tens of thousands of cells.

Let's estimate: a Python loop iteration with dict lookups ~ 0.5-1 µs. 200ms → ~200k-400k iterations. Let's target up to ~100k cells total for the biggest case.

Let's design 8 cases:

1. Small typical: 4 images, 100 cells each, n_tokens=16, n_patch=32, image_seq_length=1024.
2. Many images: 50 images, 200 cells each = 10k cells.
3. Dense cells: 4 images, 5000 cells each = 20k cells, all valid patches.
4. Many invalid patches (patch >= image_seq_length) → continue path.
5. Different n_patch (e.g. 16) with image_seq_length 256.
6. processor without image_seq_length (None) → fallback 1024.
7. Large query tokens (size(0) large, e.g. 64).
8. Mixed: duplicates patches, values, etc.

Let's generate cells with a seeded RNG.

Cell generation function:

```python
def _make_map(rng, n_cells, n_query_tokens, max_patch, dup=False):
    cells = []
    for i in range(n_cells):
        patch = rng.randrange(max_patch)
        qt = rng.randrange(n_query_tokens)
        cells.append({
            "address": {"patch": str(patch), "querytoken": str(qt)},
            "value": rng.random(),
        })
    return {"quantized": {"cells": cells}}
```

Note patch and querytoken are converted with int() so strings work; the real Vespa returns strings probably. Let's use strings to be realistic.

Actually `int(cell["address"]["patch"])` — the real Vespa data likely has string values. Let's use str.

Let me think about size limits: output tensor is (len(vespa_sim_maps), n_tokens, n_patch, n_patch) floats. For 50 images * 16 tokens * 32*32 = 819200 elements. Under 100000 values? The instruction says keep what it returns under about 100 000 values. Hmm, that's a constraint. So output tensor should be under ~100k values.

So len(maps) * n_tokens * n_patch^2 <= ~100000.

With n_patch=32, n_patch^2=1024. So len(maps)*n_tokens <= ~97. E.g., 6 images * 16 tokens = 96 → 98304 values. OK.

Hmm, that limits. Let's keep outputs modest.

Actually maybe "100 000 values" is a soft guideline. Let's stay under.

Let's design:
- Case A: 4 maps, 16 tokens, n_patch=32 → 4*16*1024 = 65536 values. Cells per map: 2000 → 8000 cells.
- Case B: 6 maps, 16 tokens, n_patch=32 → 98304 values. Cells per map: 1500 → 9000 cells.
- Case C: 2 maps, 8 tokens, n_patch=32 → 16384 values. Cells per map: 40000 → 80000 cells (heavy loop).
- Case D: 4 maps, 16 tokens, n_patch=16 → 4*16*256 = 16384. image_seq_length=256. Cells per map 5000 → 20000.
- Case E: invalid patches heavy: 4 maps, 16 tokens, n_patch=32, image_seq_length=1024, cells with patch in [1024, 4096) mostly → continue. 4*20000 = 80000 cells.
- Case F: processor None (fallback 1024). 4 maps, 16 tokens, n_patch=32, cells 3000 each → 12000 cells.
- Case G: large query tokens: 1 map, 64 tokens, n_patch=32 → 65536 values. Cells 3000.
- Case H: duplicate patches (many cells same patch, overwriting). 4 maps, 16 tokens, cells 5000 each with patch range small (e.g. 64) → many overwrites.

Total cells across cases: 8000+9000+80000+20000+80000+12000+3000+20000 = 232000. Building fine.

Wait, but case C with 80000 cells and 2 maps*8 tokens output 16384 values — fine.

Hmm, but the timing: 80000 cells ~ maybe 80ms. Good.

Let me be careful about `query_embs.size(0)`. We create query_embs as torch.randn(n_tokens, dim). n_tokens is size(0).

Now the instance: we need `n_patch` and `processor`. Since `object.__new__` bypasses `__init__`, that's fine.

Is `object.__new__(SimMapGenerator)` allowed? It's not mocking. It's building an instance without running the heavy init. Hmm, instructions say "The thunk builds the instance and passes it as the first argument". It doesn't say we must call __init__. But maybe they'd prefer calling the real constructor. The real constructor loads a model from HuggingFace — network. Not feasible. So we must bypass. Setting fields is fine ("Setting data ... an object's fields ... is fine").

Alternatively, we could avoid the instance entirely by... no, the method needs self.

Let's use `object.__new__`.

Actually, could we use `SimMapGenerator.__new__(SimMapGenerator)`? Same thing.

Now the processor: use `types.SimpleNamespace(image_seq_length=1024)`. That's a plain data object, not a mock of a repository class. Should be acceptable. The function only checks hasattr and reads the attribute.

Hmm, but is there a risk the grader considers SimpleNamespace a mock? "no subclass that overrides a method of a repository or library class". SimpleNamespace isn't a subclass. It's fine.

Now, each thunk returns `(instance, query_embs, vespa_sim_maps)`.

Important: the function doesn't modify its arguments. It creates a new tensor. So we can reuse the same data across calls. Good.

But wait — the tensor created each call is new, fine.

Now checks(): 2-3 small edge inputs.
- Empty vespa_sim_maps: `[]` → tensor shape (0, n_tokens, 32, 32). Should work.
- Empty cells: one map with no cells.
- query_embs with size(0)=0? Then tensor shape (n, 0, 32, 32), cells with querytoken 0 would index error... Actually if a cell has querytoken=0 and size(0)=0, indexing fails. Let's avoid. Use a case where query_embs is 1 token and a cell with patch >= image_seq_length only.

Let's do checks:
1. empty list of maps.
2. one map with empty cells.
3. processor without image_seq_length and a single cell with patch beyond → continue.

Actually checks may raise; fine.

Let me write the code.

Careful about imports: `from backend.colpali import SimMapGenerator`. The module imports colpali_engine etc. That must be installed. The task says import as shown. Assume available. If not, it'd fail at import — but we follow instructions.

Actually wait — `backend.colpali` imports `from colpali_engine.models import ColPali, ColPaliProcessor`. If those aren't installed, import fails. But the task says to import exactly as shown. Presumably the environment has it. We'll go with it.

Hmm, but there's risk. The instructions: "If the function cannot run here at all -- it needs network access... and no input could avoid that, do not write code". The function itself doesn't need network; only __init__ does, and we bypass it. So we should write code.

Now let's write module-level data building.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = None
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_cells(rng, n_cells, n_query_tokens, patch_choices):
    cells = []
    for _ in range(n_cells):
        patch = rng.choice(patch_choices)
        qt = rng.randrange(n_query_tokens)
        cells.append({
            "address": {"patch": str(patch), "querytoken": str(qt)},
            "value": rng.random(),
        })
    return cells


def _make_maps(seed, n_maps, n_cells, n_query_tokens, patch_choices):
    rng = random.Random(seed)
    return [{"quantized": {"cells": _make_cells(rng, n_cells, n_query_tokens, patch_choices)}}
            for _ in range(n_maps)]
```

patch_choices can be a range or list; rng.choice on a range works? `random.Random.choice` requires a sequence (supports len and indexing) — range works.

For invalid patches, patch_choices = range(1024, 4096).

Let's build query_embs: `torch.randn(n_tokens, 128)`. Use seeded generator for determinism? torch.manual_seed. Not strictly needed but let's set seed.

Actually the values of query_embs don't affect the function except size(0). So any tensor works.

Let's write cases.

Case list:

```python
def cases():
    return [
        ("typical-4imgs", lambda: (_i1, _q16, _maps_a)),
        ...
    ]
```

Build everything at module level.

Let me define module-level constants.

```python
_I32_1024 = _make_instance(32, 1024)
_I16_256 = _make_instance(16, 256)
_I32_none = _make_instance(32, None)

_Q16 = torch.randn(16, 128)
_Q64 = torch.randn(64, 128)
_Q8 = torch.randn(8, 128)
```

Maps:

```python
_MAPS_A = _make_maps(0, 4, 2000, 16, range(1024))          # 8000 cells, valid
_MAPS_B = _make_maps(1, 6, 1500, 16, range(1024))          # 9000 cells
_MAPS_C = _make_maps(2, 2, 40000, 8, range(1024))          # 80000 cells
_MAPS_D = _make_maps(3, 4, 5000, 16, range(256))           # 20000 cells, n_patch 16
_MAPS_E = _make_maps(4, 4, 20000, 16, range(1024, 4096))   # 80000 cells, all skipped
_MAPS_F = _make_maps(5, 4, 3000, 16, range(1024))          # 12000 cells, fallback
_MAPS_G = _make_maps(6, 1, 3000, 64, range(1024))          # 3000 cells, 64 tokens
_MAPS_H = _make_maps(7, 4, 5000, 16, range(64))            # 20000 cells, duplicates
```

Wait for case D: n_patch=16, image_seq_length=256, patches 0..255 → patch//16 in 0..15, patch%16. Good.

Case E: image_seq_length 1024, patches 1024..4095, all skipped. Good, tests continue path.

Case C: n_patch=32, image_seq_length=1024, 8 tokens, 2 maps. Output 2*8*1024=16384.

Case G: 1 map, 64 tokens, n_patch 32 → 1*64*1024 = 65536. Good.

Case H: patch range 64 → many overwrites on same cells. Output 4*16*1024=65536.

Check output sizes: A: 4*16*1024=65536. B: 6*16*1024=98304. C: 16384. D: 4*16*256=16384. E: 4*16*1024=65536. F: 65536. G: 65536. H: 65536. All under 100k. Good.

Input values: cells are dicts, each cell has 3 entries roughly. Total cells ~ 8000+9000+80000+20000+80000+12000+3000+20000 = 232000 cells. Each cell dict with nested dict → maybe ~5 objects. Under 1,000,000 values? Probably. Each cell ~ 4 values (patch, querytoken, value, plus keys). 232000*4 ≈ 1M. Hmm borderline. The limit is "keep each input's data under about 1 000 000 values". Let's reduce a bit.

Actually per input (per case), not total. Each case: max 80000 cells * ~4 = 320k values. Fine.

But memory: 232000 cells total in memory. Each cell dict maybe 300 bytes → 70MB. Plus nested. Could be ~100MB total. Hmm. Let's reduce to be safe.

Let me reduce: C: 30000 cells, E: 30000 cells, others smaller.

Actually let's estimate more carefully. A dict with 1 key `{"quantized": {...}}` for map. Cell: `{"address": {"patch": "123", "querytoken": "5"}, "value": 0.5}`. That's 2 dicts + 3 strings + float. ~ 200 bytes for inner dict, 200 for outer dict, strings ~50 each. So ~500 bytes per cell. 232000 * 500 = 116 MB. Too much.

Reduce total cells to ~100k → 50MB. Let's do:

- A: 4 maps, 1500 cells = 6000
- B: 6 maps, 1500 = 9000
- C: 2 maps, 25000 = 50000
- D: 4 maps, 4000 = 16000
- E: 4 maps, 15000 = 60000
- F: 4 maps, 2500 = 10000
- G: 1 map, 3000 = 3000
- H: 4 maps, 4000 = 16000

Total = 170000. Still ~85MB. Hmm.

Let's cut more. The heaviest loop cases: C and E. Let's make C 20000, E 20000. Then total = 6000+9000+20000+16000+20000+10000+3000+16000 = 100000 cells → ~50MB. Good.

Timing: 20000 cells ~ 20-30ms. Fine, within 1ms-200ms. Actually the smallest case A with 6000 cells ~ 6ms. Good.

Hmm, but "One call should take roughly 1 ms to 200 ms". 6000 cells at ~0.7µs = 4ms. Good.

Let me also consider that `torch.zeros` allocation for (6,16,32,32)=98304 floats is fast.

OK.

Now checks:

```python
def checks():
    inst = _make_instance(32, 1024)
    inst_none = _make_instance(32, None)
    q = torch.randn(4, 128)
    return [
        ("empty-maps", lambda: (inst, q, [])),
        ("empty-cells", lambda: (inst, q, [{"quantized": {"cells": []}}])),
        ("no-seq-len-skip", lambda: (inst_none, q, [{"quantized": {"cells": [{"address": {"patch": "2000", "querytoken": "0"}, "value": 0.5}]}}])),
    ]
```

Wait, for empty maps, tensor shape (0, 4, 32, 32). Fine.

For "empty-cells", one map with no cells → zeros tensor.

Third: processor None → image_seq_length=1024, patch 2000 >= 1024 → continue. Fine.

Hmm, but checks should be "small edge inputs (empty, one element, None, an odd type)". Ours are fine.

Now, one concern: the function reads `self.processor` — with processor=None, `hasattr(None, "image_seq_length")` is False. Good.

Now let me double-check `object.__new__(SimMapGenerator)` — SimMapGenerator is a plain class (inherits object). Works.

Now the thunk returns `(instance, query_embs, vespa_sim_maps)`. The function signature is `(self, query_embs, vespa_sim_maps)`, so calling `SimMapGenerator._prepare_similarity_map_tensor(instance, query_embs, maps)`.

Wait — the task says "the method is called as `SimMapGenerator._prepare_similarity_map_tensor(instance, ...)`". So the harness calls the function with the thunk's returned args. Good.

Now let's also make sure query_embs is a torch.Tensor. Yes.

One more thought: does the function mutate vespa_sim_maps? No. query_embs? No. So we can reuse.

Let me write final code.

Also need to be careful: module-level code runs when the module is imported. The import of backend.colpali might be heavy (colpali_engine). Fine.

Let me also set torch seed for reproducibility: `torch.manual_seed(0)`. Not necessary but ok.

Let me write it.

```python
import random
import types

import torch

from backend.colpali import SimMapGenerator


def _make_instance(n_patch, image_seq_length):
    inst = object.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = None
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst


def _make_cells(rng, n_cells, n_query_tokens, patch_choices):
    cells = []
    for _ in range(n_cells):
        patch = rng.choice(patch_choices)
        qt = rng.randrange(n_query_tokens)
        cells.append(
            {
                "address": {"patch": str(patch), "querytoken": str(qt)},
                "value": rng.random(),
            }
        )
    return cells


def _make_maps(seed, n_maps, n_cells, n_query_tokens, patch_choices):
    rng = random.Random(seed)
    return [
        {"quantized": {"cells": _make_cells(rng, n_cells, n_query_tokens, patch_choices)}}
        for _ in range(n_maps)
    ]


torch.manual_seed(0)

_INST_32_1024 = _make_instance(32, 1024)
_INST_16_256 = _make_instance(16, 256)
_INST_32_FALLBACK = _make_instance(32, None)

_Q8 = torch.randn(8, 128)
_Q16 = torch.randn(16, 128)
_Q64 = torch.randn(64, 128)

_MAPS_TYPICAL = _make_maps(0, 4, 1500, 16, range(1024))
_MAPS_MANY_IMGS = _make_maps(1, 6, 1500, 16, range(1024))
_MAPS_DENSE = _make_maps(2, 2, 20000, 8, range(1024))
_MAPS_SMALL_PATCH = _make_maps(3, 4, 4000, 16, range(256))
_MAPS_SKIPPED = _make_maps(4, 4, 20000, 16, range(1024, 4096))
_MAPS_FALLBACK = _make_maps(5, 4, 2500, 16, range(1024))
_MAPS_LONG_QUERY = _make_maps(6, 1, 3000, 64, range(1024))
_MAPS_DUPLICATES = _make_maps(7, 4, 4000, 16, range(64))


def checks():
    q = torch.randn(4, 128)
    return [
        ("empty-maps", lambda: (_INST_32_1024, q, [])),
        ("empty-cells", lambda: (_INST_32_1024, q, [{"quantized": {"cells": []}}])),
        (
            "fallback-skip",
            lambda: (
                _INST_32_FALLBACK,
                q,
                [{"quantized": {"cells": [{"address": {"patch": "2000", "querytoken": "0"}, "value": 0.5}]}}],
            ),
        ),
    ]


def cases():
    return [
        ("typical", lambda: (_INST_32_1024, _Q16, _MAPS_TYPICAL)),
        ("many-images", lambda: (_INST_32_1024, _Q16, _MAPS_MANY_IMGS)),
        ("dense-few-tokens", lambda: (_INST_32_1024, _Q8, _MAPS_DENSE)),
        ("small-patch-grid", lambda: (_INST_16_256, _Q16, _MAPS_SMALL_PATCH)),
        ("mostly-skipped", lambda: (_INST_32_1024, _Q16, _MAPS_SKIPPED)),
        ("fallback-seq-len", lambda: (_INST_32_FALLBACK, _Q16, _MAPS_FALLBACK)),
        ("long-query", lambda: (_INST_32_1024, _Q64, _MAPS_LONG_QUERY)),
        ("duplicate-patches", lambda: (_INST_32_1024, _Q16, _MAPS_DUPLICATES)),
    ]
```

Wait, the "duplicate-patches" case with patch range 64 and n_patch 32: patch//32 in {0,1}, patch%32 in 0..31. So only rows 0 and 1 of the 32x32 grid get written. Fine — lots of overwrites.

Hmm, one issue: for the "dense-few-tokens" case, query tokens = 8, and cells use qt in range(8). Good.

For "long-query", 64 tokens, cells qt in range(64). Good.

Check output size for many-images: 6*16*1024 = 98304 < 100000. OK barely.

Let me double check the "small-patch-grid": n_patch=16, image_seq_length=256, patches 0..255. patch//16 range 0..15. Good. Output 4*16*256=16384.

Now, potential issue: `rng.choice(range(1024, 4096))` — range supports indexing and len, so choice works.

Now the input value count: each case max 20000 cells * ~4 = 80k values. Fine.

Total memory: 100000 cells * ~500 bytes = 50MB. Plus torch tensors small. OK.

Let me reconsider whether `types.SimpleNamespace` might be flagged. The rule: "no subclass that overrides a method of a repository or library class -- a subclass whose get returns canned data instead of making the request is a mock too." SimpleNamespace is not a subclass. And the function only reads an attribute. I think it's fine. Alternatively, I could use the real processor... not feasible without loading model.

Hmm, could I use `ColPaliProcessor` without loading? It's a class; instantiating requires config. Too complex. SimpleNamespace is the pragmatic choice.

Actually, wait. Is there a risk that the harness's "render arguments before and after" chokes on SimpleNamespace or the instance? Probably fine.

Another thought: maybe I should set more attributes on the instance to look realistic? Not needed.

Let me finalize. One more consideration: the thunk returns the same objects every call. The function doesn't mutate them. Good.

I'll write the final answer.