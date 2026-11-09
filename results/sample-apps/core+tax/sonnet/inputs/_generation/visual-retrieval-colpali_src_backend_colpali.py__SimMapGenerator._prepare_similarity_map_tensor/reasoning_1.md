Let me analyze this function. It takes query_embs (torch.Tensor) and vespa_sim_maps (List[Dict]). It uses self.n_patch and self.processor (checks hasattr image_seq_length).

We need to construct a SimMapGenerator instance. But __init__ loads a model (network access, heavy). We can't call __init__ easily. But we can create the instance without calling __init__? The instructions say don't mock. But building an instance... Hmm. We can use `SimMapGenerator.__new__(SimMapGenerator)` and set attributes? That's setting data on an object's fields, which is allowed ("Setting data (a module's configuration, an object's fields) to build an input is fine").

Actually the instruction: "A method is called as a plain function: the thunk builds the instance and passes it as the first argument". Building the instance without __init__ via __new__ and setting fields is acceptable since it's just data setup. The alternative is calling __init__ which loads model from network - can't.

So: `obj = SimMapGenerator.__new__(SimMapGenerator)`, set `obj.n_patch = 32`, `obj.processor = <something with image_seq_length>`.

The processor: we need an object with `image_seq_length` attribute. Could use a simple object with that attribute. But is that a mock? It's just a data holder. We could use a real ColPaliProcessor? That requires loading from hub (network). So we use a simple namespace object. Hmm, but "no mocks". A simple object holding a field is data. I think it's fine.

Actually we could just not set processor... but hasattr check requires processor attribute to exist. If processor doesn't exist, hasattr raises AttributeError? No—hasattr(self.processor, ...) would raise AttributeError on self.processor itself. Actually self.processor must exist. So set it.

Let me use a types.SimpleNamespace(image_seq_length=1024) or a small class. Actually maybe better to make a tiny class defined in our source. That's fine.

Wait, but the checksum: the function reads self.processor.image_seq_length each iteration. Fine.

Now the workload: build vespa_sim_maps, a list of dicts with "quantized": {"cells": [ {"address": {"patch":..., "querytoken":...}, "value":...}, ... ]}.

query_embs: torch tensor with size(0) = number of query tokens (e.g. 32 or so). Actually in ColPali, query_embs shape is (num_query_tokens, dim). size(0) is number of tokens. The tensor output shape is (len(vespa_sim_maps), query_embs.size(0), n_patch, n_patch).

So query_token indexes into dim 1, must be < query_embs.size(0). patch indexes patch dimension.

n_patch = 32 typically, image_seq_length = 1024. patch // 32 and patch % 32, so patch in [0, 1024).

Let's design cases with varying sizes: number of maps (images), number of cells per map, query tokens, hit/miss ratio (patch >= image_seq_length to test continue path).

Note the output tensor is (num_maps, num_tokens, 32, 32) = num_maps * num_tokens * 1024 values. Keep under 100,000 values. So num_maps * num_tokens * 1024 < 100000 => num_maps * num_tokens < ~97. Hmm that's restrictive. E.g. num_maps=3, num_tokens=32 => 3*32*1024 = 98304, just under. num_maps=2, num_tokens=32 => 65536.

Hmm wait, "keep what it returns ... under about 100 000 values". So we need output small. So num_maps * num_tokens <= ~97.

But the input data (cells) can be large. Each cell is a dict. Keep input under 1,000,000 values. So we can have many cells, e.g. 100,000 cells. But cells write into the tensor; duplicates overwrite.

So the work is dominated by iterating cells. Let's make cells large: e.g. 50,000 cells per map, times 3 maps = 150,000 cells. That's substantial work.

But wait, the tensor is small so assigning is cheap; the loop over cells is the work. Each cell: dict access, int conversions, hasattr, comparisons, tensor indexing.

Let's aim for ~1ms-200ms. 150k cells should be maybe ~50ms? Let's estimate: each iteration maybe ~1-2 microseconds in Python => 150k * 1.5us = 0.2s. Hmm might be near 200ms. Let's keep moderate.

Actually the tensor indexing assignment `tensor[idx, query_token, a, b] = value` is relatively slow (~1-2 us). Plus dict accesses. So maybe 2-3 us per cell. 100k cells => 0.2-0.3s. Let's keep to ~50k-80k cells total per case.

Let me plan 8 cases with diverse characteristics:

1. "small-typical": 2 maps, 32 tokens, 5000 cells each (10000 total).
2. "many-cells": 1 map, 32 tokens, 60000 cells.
3. "many-maps": 3 maps, 32 tokens, 10000 cells each (30000).
4. "misses": cells with patch >= image_seq_length (all skipped) - tests continue path heavily.
5. "few-tokens-many-cells": 1 map, 8 tokens, 80000 cells.
6. "duplicates": cells with same address repeated - overwriting.
7. "large-values": values are floats.
8. "high-token": 3 maps, 32 tokens, varied.

Wait output size constraint: num_maps * num_tokens * 1024 <= 100000. So num_maps*num_tokens <= 97. With 32 tokens, num_maps <= 3. With 8 tokens, num_maps <= 12.

Let's be careful: keep num_maps*num_tokens <= 90.

Case designs:
1. typical: maps=2, tokens=32 => 64 => 65536 values. cells/map=4000 => 8000 cells.
2. many-cells: maps=1, tokens=32 => 32768. cells=60000.
3. many-maps: maps=3, tokens=32 => 98304 (slightly under 100k). cells/map=6000 => 18000.
4. all-miss: maps=1, tokens=32, cells=50000 all with patch>=1024.
5. few-tokens: maps=1, tokens=8 => 8192. cells=80000.
6. duplicates: maps=2, tokens=32, cells=40000 all same few addresses.
7. mixed-ratio: maps=2, tokens=32, cells=30000, 50% misses.
8. large-maps-tokens: maps=2, tokens=16 => 32768, cells=50000.

Hmm let's also consider the hasattr branch: processor with image_seq_length vs without. If processor lacks image_seq_length, image_seq_length=1024. We could make one case where processor has a large image_seq_length (e.g. 4096) so more cells pass. But processor is set on instance; we can create different instances per case. Good - diversity.

Actually careful: the processor attribute check is `hasattr(self.processor, "image_seq_length")`. We can set image_seq_length to different values.

Let me create instances in thunks. Each case builds a fresh instance (cheap) and data.

Data building: use random.Random(seed).

Let me write a helper to build cells.

Cell structure:
```python
{"address": {"patch": int, "querytoken": int}, "value": float}
```

vespa_sim_map = {"quantized": {"cells": [...]}}

Let's write:

```python
import random
import torch
from backend.colpali import SimMapGenerator

class _Processor:
    def __init__(self, image_seq_length=None):
        if image_seq_length is not None:
            self.image_seq_length = image_seq_length

def _make_instance(n_patch=32, image_seq_length=1024):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = _Processor(image_seq_length)
    return inst
```

Hmm, but is defining a class that stands in for the processor a mock? It's a data holder; the function only reads an attribute. I think acceptable. Alternatively use types.SimpleNamespace. Let's use SimpleNamespace for clarity - it's a plain data object. Actually a class is fine too. I'll use a small class.

Wait, "no subclass that overrides a method of a repository or library class". _Processor doesn't subclass anything. Fine.

Now query_embs: torch tensor of shape (num_tokens, dim). size(0)=num_tokens. Use torch.randn? Need deterministic. Use torch.manual_seed? Actually query_embs values don't matter, only size(0). We can use torch.zeros((n, 128)). Fine.

Now cells generation:

```python
def _cells(n, n_tokens, image_seq_length, seed, miss_ratio=0.0, dup=False):
    rng = random.Random(seed)
    cells = []
    for i in range(n):
        if dup:
            patch = rng.randrange(0, min(64, image_seq_length))
            qt = rng.randrange(n_tokens)
        else:
            qt = rng.randrange(n_tokens)
            if rng.random() < miss_ratio:
                patch = rng.randrange(image_seq_length, image_seq_length + 1000)
            else:
                patch = rng.randrange(0, image_seq_length)
        cells.append({"address": {"patch": patch, "querytoken": qt}, "value": rng.random()})
    return cells
```

Wait for dup, we want few distinct addresses so many overwrites. Let's make patch in small range and qt small.

Now build vespa_sim_maps: list of dicts.

Let me write cases. Each thunk returns (instance, query_embs, vespa_sim_maps) since it's a method called as plain function with instance first.

Wait, the task says: "the method is called as `SimMapGenerator._prepare_similarity_map_tensor(instance, ...)`". So thunk returns (instance, query_embs, vespa_sim_maps).

Now, does the function modify its arguments? It doesn't modify vespa_sim_maps or query_embs. So we can reuse the same data across calls. But the thunk is called before each timed call, and we should keep thunk cheap. Building 60000 cells per thunk call would be slow (setup not timed but repeated many times... "setup is never timed" but it runs before timing). Actually the thunk runs before each timed call, and building data each time would be expensive but not timed. However the guidance says "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy if the function changes it."

The function doesn't change the input, so we can build once at module level and have thunk return the same. But instances: we can also build once. So module-level build all data, thunks just return references.

But careful: output tensor created fresh each call, fine.

So module-level: build data structures, store in globals, thunks return them.

Let me structure: define a function `_build_case(...)` returning (instance, query_embs, vespa_sim_maps), call at module level, store in variables.

Actually simpler: define module-level lists.

Let me write it.

```python
import random
import torch
from backend.colpali import SimMapGenerator


class _Processor:
    def __init__(self, image_seq_length):
        self.image_seq_length = image_seq_length


def _instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    inst.processor = _Processor(image_seq_length)
    return inst


def _query_embs(n_tokens):
    return torch.zeros((n_tokens, 128), dtype=torch.float32)


def _cells(n, n_tokens, image_seq_length, seed, miss_ratio=0.0, dup=False):
    rng = random.Random(seed)
    cells = []
    for i in range(n):
        if dup:
            patch = rng.randrange(0, 32)
            qt = rng.randrange(0, min(n_tokens, 4))
        else:
            qt = rng.randrange(n_tokens)
            if rng.random() < miss_ratio:
                patch = rng.randrange(image_seq_length, image_seq_length + 512)
            else:
                patch = rng.randrange(0, image_seq_length)
        cells.append(
            {"address": {"patch": patch, "querytoken": qt}, "value": rng.random()}
        )
    return cells


def _sim_maps(n_maps, n_cells, n_tokens, image_seq_length, seed, miss_ratio=0.0, dup=False):
    return [
        {"quantized": {"cells": _cells(n_cells, n_tokens, image_seq_length, seed + i, miss_ratio, dup)}}
        for i in range(n_maps)
    ]
```

Then build cases at module level.

Case definitions:

1. typical: n_patch=32, image_seq_length=1024, maps=2, tokens=32, cells=4000 each => 8000 cells.
2. many-cells: maps=1, tokens=32, cells=60000.
3. many-maps: maps=3, tokens=32, cells=6000 each => 18000.
4. all-miss: maps=1, tokens=32, cells=50000, miss_ratio=1.0.
5. few-tokens-many-cells: maps=1, tokens=8, cells=80000.
6. duplicates: maps=2, tokens=32, cells=40000, dup=True.
7. mixed: maps=2, tokens=32, cells=30000, miss_ratio=0.5.
8. large-image-seq: image_seq_length=4096, maps=2, tokens=16, cells=40000, miss_ratio=0.2.

Check output sizes:
1. 2*32*1024 = 65536 ok.
2. 1*32*1024 = 32768 ok.
3. 3*32*1024 = 98304 ok (<100k).
4. 32768.
5. 1*8*1024=8192.
6. 65536.
7. 65536.
8. 2*16*1024=32768.

All under 100k. Good.

Input values: total cells across all cases: 8000+60000+18000+50000+80000+40000+30000+40000 = 326000 cells. Each cell dict has ~4 values (patch, qt, value, plus nested). Under 1M values. Fine. Memory: 326k dicts with nested dicts ~ maybe 100MB? Each cell: dict ~ 200 bytes + nested dict ~ 200 + address dict... Actually two nested dicts per cell. Let's estimate ~500 bytes per cell => 163MB. Hmm might exceed 100MB. Let's reduce.

Hmm, "Keep the data in memory under about 100 MB". 326k cells * ~500 bytes = 163MB. Too much. Let's reduce cell counts.

Actually let's estimate more carefully: a dict with 2 keys is ~184 bytes (empty dict 64 + entries). Actually CPython dict minimum 64 bytes, with 2 entries maybe 184. Nested: cell dict has "address" and "value" => ~184 bytes. address dict has "patch","querytoken" => ~184. Plus ints (28 bytes each, small ints cached for <256), floats 24 bytes. So per cell ~ 184+184+24+ maybe ints. ~400-500 bytes.

To stay under 100MB, keep total cells <= ~200k. Let's target ~150k total.

Let me reduce:
1. typical: 2 maps, 4000 cells => 8000
2. many-cells: 1 map, 40000 cells
3. many-maps: 3 maps, 4000 each => 12000
4. all-miss: 1 map, 30000
5. few-tokens: 1 map, 40000
6. duplicates: 2 maps, 20000 each => 40000
7. mixed: 2 maps, 15000 each => 30000
8. large-image-seq: 2 maps, 15000 each => 30000

Total = 8000+40000+12000+30000+40000+40000+30000+30000 = 230000. Still a bit high. Let's trim.

Hmm actually maybe reduce duplicates to 10000 each and mixed to 10000 each.

Let me just aim total ~150k.

1. typical: 2 maps * 4000 = 8000
2. many-cells: 1 * 40000 = 40000
3. many-maps: 3 * 3000 = 9000
4. all-miss: 1 * 25000 = 25000
5. few-tokens: 1 * 30000 = 30000
6. duplicates: 2 * 8000 = 16000
7. mixed: 2 * 10000 = 20000
8. large: 2 * 10000 = 20000

Total = 8000+40000+9000+25000+30000+16000+20000+20000 = 168000. ~80MB maybe. Acceptable-ish. Let's reduce a bit more to be safe: many-cells 30000, few-tokens 25000.

Total = 8000+30000+9000+25000+25000+16000+20000+20000 = 153000. ~75MB. OK.

Timing: 30000 cells case => maybe 30000*2us = 60ms. Good. many-cells 30000 => 60ms. Good.

Now, we run all 8 on original and keep 4 that do most work. Fine.

checks(): 2-3 small edge inputs.

- empty vespa_sim_maps: `SimMapGenerator._prepare_similarity_map_tensor(inst, query_embs, [])`. Returns tensor of shape (0, tokens, 32,32). Fine.
- one cell.
- processor without image_seq_length? That's the else branch. Let's include one.

Actually checks may raise. Let's do:
1. "empty-maps": ([],) - empty list.
2. "single-cell": one map with one cell.
3. "no-image-seq-length": processor without image_seq_length attribute.

For #3, our _Processor always sets image_seq_length. Need a variant. Let's make _Processor accept None and not set.

Let me write _Processor:

```python
class _Processor:
    def __init__(self, image_seq_length=None):
        if image_seq_length is not None:
            self.image_seq_length = image_seq_length
```

Then _instance with image_seq_length=None gives no attribute.

Now checks thunks build small data.

Let me write the code.

One concern: `SimMapGenerator.__new__(SimMapGenerator)` - does the class define __new__? No, default. Fine.

Also colormap = cm.viridis at class level requires matplotlib import - it's imported in module. Fine.

Also importing backend.colpali imports colpali_engine etc. Should be available per task. Assume installed.

Let me also make sure torch is imported.

Now, another concern: the function reads `self.processor.image_seq_length` inside the loop for every cell. With our instance, fine.

Let me write final code.

For cases, I'll build data at module level via helper calls, then thunks return tuples.

Let me define a builder:

```python
def _build(n_patch, image_seq_length, n_maps, n_cells, n_tokens, seed, miss_ratio=0.0, dup=False):
    inst = _instance(n_patch, image_seq_length)
    embs = _query_embs(n_tokens)
    maps = _sim_maps(n_maps, n_cells, n_tokens, image_seq_length if image_seq_length else 1024, seed, miss_ratio, dup)
    return inst, embs, maps
```

Wait if image_seq_length is None (no attr), the else branch uses 1024. For cells generation, use 1024. Fine.

Then:

```python
_C1 = _build(32, 1024, 2, 4000, 32, 0)
...
def cases():
    return [
        ("typical", lambda: _C1),
        ...
    ]
```

Thunk returns tuple (inst, embs, maps). Good.

But wait - the function receives (instance, query_embs, vespa_sim_maps). Our thunk returns (inst, embs, maps). Correct.

Now checks:

```python
def checks():
    inst = _instance(32, 1024)
    embs = _query_embs(8)
    single = [{"quantized": {"cells": [{"address": {"patch": 5, "querytoken": 1}, "value": 0.5}]}}]
    inst_no = _instance(32, None)
    return [
        ("empty-maps", lambda: (inst, embs, [])),
        ("single-cell", lambda: (inst, embs, single)),
        ("no-image-seq-length", lambda: (inst_no, embs, single)),
    ]
```

These build instances at module level for checks? checks() is called once, so building inside is fine. But thunks need to be re-runnable; fine.

Actually for checks, if the same inst is reused across thunks, no mutation. Fine.

Now the "no-image-seq-length" case: inst_no.processor has no image_seq_length, so hasattr is False, image_seq_length=1024. patch=5 < 1024, so set. Fine.

Let me double check the dup case: patch in [0,32), qt in [0, min(n_tokens,4)). With n_patch=32, patch//32=0, patch%32=patch. Fine.

Now, potential issue: query_token must be < query_embs.size(0) = n_tokens. In dup we use min(n_tokens,4), fine.

Also in _cells non-dup, qt = rng.randrange(n_tokens). Good.

Edge: n_tokens must be >0.

Let me also verify output value count for case 3: 3*32*1024 = 98304 < 100000. Good but close. Fine.

Now write it out.

Also need `import torch` at top.

Let me finalize.

One more thought: should I worry that _Processor is considered a mock? The guidance says no mocks / no subclass overriding methods. _Processor is a plain data holder, not a subclass. I'll add a comment. Alternatively use types.SimpleNamespace. Let me use SimpleNamespace to be extra safe - it's a standard library plain data object.

Actually the processor in real code is a ColPaliProcessor, but loading it needs network. We can't. Using SimpleNamespace with image_seq_length is setting data. Fine.

But hasattr on SimpleNamespace works. Good.

Let me use types.SimpleNamespace.

```python
import types
def _instance(n_patch, image_seq_length):
    inst = SimMapGenerator.__new__(SimMapGenerator)
    inst.n_patch = n_patch
    if image_seq_length is None:
        inst.processor = types.SimpleNamespace()
    else:
        inst.processor = types.SimpleNamespace(image_seq_length=image_seq_length)
    return inst
```

Good.

Now finalize code.