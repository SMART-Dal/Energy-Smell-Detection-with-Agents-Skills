Let me analyze the function.

`write_embeddings(id_to_index_map, embeddings, file_name)` writes to `os.path.join(data_dir, file_name)`. `data_dir` is a module global in train_mf. We need to set `train_mf.data_dir = str(WORKDIR)`.

The function takes:
- id_to_index_map: a dict mapping id -> index
- embeddings: something with `.tolist()` per row — a torch tensor or numpy array
- file_name: string

We need to build embeddings as torch tensor. The function does `embeddings[index].tolist()`.

The function writes a file. Repeated calls overwrite the same file. That's fine — same work each call. But careful: file_name must be under WORKDIR. Set data_dir.

For checks, we could use empty map, or single element.

Let me think about realistic scale. In the repo, user_map and news_map are dicts of id -> index, embeddings is a tensor. MIND dataset: news ~ 65000 news, users ~ maybe 100000+ users. Embedding size maybe 200. Let's keep under 100MB.

Each call writes lines. Output file could be large. The instructions say "keep what it returns (and anything it writes) under about 100 000 values". Hmm, the file written — number of lines * embedding dim. For 50000 news with embedding 200, that's 10 million values written. That might exceed. But the constraint about 100000 values is about output comparison. Actually it says "The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values." Hmm, but the function returns None. What it writes is a file. Does the harness compare the file? Probably not — it compares the return value. But to be safe, keep sizes moderate.

Actually the file is written to WORKDIR; the harness likely doesn't compare file contents. But let's be reasonable. Let's keep embedding dimension like 100-200 and number of ids up to a few thousand. Lines * dim under 100000 → e.g., 1000 ids * 100 dim = 100000. Hmm.

Actually let me reconsider: the constraint is about "values". A line "id\tv1,v2,..." with 100 dims = 101 values. 1000 lines = 101000. Slightly over. Let's target ~500 lines * 100 dims = 50000 values. That's fine and still gives ~1ms+ work.

But we want each call to take 1ms-200ms. Writing 500 lines with formatting is maybe ~1ms. Let's go bigger: 5000 ids * 200 dims = 1M values... too many maybe. Hmm.

The "under about 100 000 values" is a soft guideline. Let me aim for something in between, like 2000-5000 lines. Actually the timing requirement (1ms-200ms) matters more. Formatting 5000 lines of 200 floats each: 1M float formats, roughly 100-200ms. That's within range but big.

Let me balance: use embedding dims of 64-200 and ids 1000-4000.

Actually, the output comparison: the function returns None. The harness compares outputs — None == None. The file written isn't the return value. So the 100000 values constraint probably applies to return values and mutated arguments. The file is a side effect. I'll keep it reasonable anyway.

Let me design cases with variety:
- Different sizes of id_to_index_map
- Different embedding dimensions
- Different index orderings (indices not 0..n-1, shuffled)
- Integer vs string ids
- Negative indices? No, indices must be valid.

The map maps id -> index. The embeddings tensor is indexed by index. So indices should be within range of embeddings.

Variations:
1. Small typical: 1000 news, dim 200
2. Large: 5000 users, dim 200
3. Non-contiguous/shuffled indices
4. String ids vs int ids
5. Small dim
6. Large dim
7. Sparse index range (only few indices used out of large embeddings)
8. Duplicate index values (multiple ids mapping to same index)

Let me build a helper that creates embeddings tensor of shape (n, dim) and a map.

Use torch. Fixed seed. torch.manual_seed.

Actually embeddings needs `.tolist()` on rows. torch tensor works.

Let me write:

```python
import os
import random
import torch
import train_mf
from train_mf import write_embeddings

train_mf.data_dir = str(WORKDIR)
```

Wait — `data_dir` is defined at module import time as `sys.argv[1] if len(sys.argv) > 1 else "../../mind/"`. We override it. Good.

Each thunk must return (id_to_index_map, embeddings, file_name). The function doesn't modify the map or embeddings (it only reads). So we can reuse the same objects. But file_name — the function opens the file in "w" mode, truncating. Repeated calls overwrite. Fine, same work.

However, we should ensure the file is removed first? The function opens with "w", which truncates/creates. So no need to remove. But if file exists, opening "w" truncates. Same work. Good.

But wait: if the file_name is the same across calls, no issue. Each case uses its own file_name to avoid interference? Actually cases are run separately; but the same file could be reused. Let's give distinct file names per case.

Now `id_to_index_map.items()` — dict iteration order is insertion order. Fine.

Let me create the data at module level.

Helper:

```python
def _make(n, dim, seed, id_prefix="n", shuffle=True, index_range=None, dup=False):
    rng = random.Random(seed)
    torch.manual_seed(seed)
    if index_range is None:
        index_range = n
    embeddings = torch.randn(max(index_range, n), dim)
    ...
```

Hmm, let me think about what makes "different paths". The function is simple: iterate items, format. Different work = different number of lines, different dims, different id types.

Let me define cases:

1. "news-typical": 3000 news, dim 200, ids like "N12345"
2. "users-large": 5000 users, dim 200, ids like "U12345"
3. "small-dim": 4000 items, dim 8
4. "large-dim": 1000 items, dim 512
5. "int-ids": 3000 items, int ids
6. "shuffled-indices": 3000 items, indices shuffled 0..n-1
7. "sparse": 2000 items, indices sampled from range 0..20000 (embeddings 20000 x 200 = 4M floats = 16MB, ok)
8. "duplicate-indices": 3000 ids mapping to only 500 distinct indices

Let me compute memory: 5000*200 = 1M floats = 4MB. Fine. 20000*200 = 4M floats = 16MB. Fine.

Timing: formatting 3000 lines * 200 floats = 600k float formats. `"%.6f" % i` is somewhat slow. 600k might be ~150ms. Hmm, that's near the top. Let's reduce dims a bit. Actually let's estimate: Python `"%.6f" % x` ~ 200ns? Then 600k = 120ms. Plus join and write. That's within 200ms but close. Let me use dim 128 and n 2000 → 256k formats ~ 50ms. Good.

Let me reconsider: to be safe, target ~2000-3000 lines with dim 64-128.

Actually the original function in the repo: MIND news has ~65000 news with embedding size... Let's check MF init: embedding_size. Probably 200. But writing 65000 lines would be way over 200ms and over output limits. The task says inputs where one call takes over 1s are dropped, and keep outputs under 100000 values. So we scale down.

Let me pick:
1. news-typical: n=2000, dim=128, string ids
2. users-large: n=3000, dim=64
3. small-dim: n=4000, dim=16
4. large-dim: n=500, dim=512
5. int-ids: n=2000, dim=128
6. shuffled: n=2000, dim=128
7. sparse: n=2000, dim=64, index range 20000
8. duplicates: n=3000, dim=64, 500 distinct indices

Each line output values: n*(dim+1). For n=2000,dim=128: 258000 values. Over 100000 but function returns None. Hmm.

I'll not worry too much — the return is None. But the instruction is explicit. Let me reduce to keep each under ~100000 values written. n*(dim+1) < 100000.

- n=2000, dim=48 → 98000. 
- n=3000, dim=32 → 99000.
- n=4000, dim=16 → 68000.
- n=500, dim=192 → 96500.
- n=2000, dim=48.
- n=2000, dim=48.
- n=2000, dim=32 → 66000.
- n=3000, dim=32.

Hmm but these are smaller; timing might be <1ms. 2000 lines * 48 floats = 96000 formats ~ 20ms. OK that's >1ms. Fine.

Actually, the "100 000 values" guidance is about comparison overhead. Since return is None and file isn't compared, I think we have freedom. But let's respect it reasonably.

Let me use dims around 64 and n around 1500-2500.

Actually let me just be pragmatic: keep n*dim under ~100k.

Cases:
1. news-typical: n=2000, dim=32, string ids "N%05d"
2. users-large: n=3000, dim=16, string ids "U%05d"
3. small-dim: n=4000, dim=8
4. large-dim: n=400, dim=200 (80k)
5. int-ids: n=2000, dim=32
6. shuffled-indices: n=2000, dim=32
7. sparse: n=1500, dim=32, range 20000
8. duplicates: n=3000, dim=16, 300 distinct indices

Hmm, dim 16-32 is small compared to real 200. But fine.

Actually, let me reconsider the output constraint. The function writes to a file, not returning values. The harness "compares output in full" — for this function output is None. The "anything it writes" phrase suggests they may capture file writes? Unlikely — they'd need to know which files. I think it's fine to go bigger. But to be safe, moderate.

I'll go with dims 32-128 and n 1000-3000.

Let me write the code.

```python
import os
import random
import torch
import train_mf
from train_mf import write_embeddings

train_mf.data_dir = str(WORKDIR)


def _embeddings(n_rows, dim, seed):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(n_rows, dim, generator=g)


def _string_ids(n, seed, prefix):
    rng = random.Random(seed)
    return [f"{prefix}{rng.randrange(10**7):07d}" for _ in range(n)]
```

Wait, ids should be unique for a dict map. Use a set or generate distinct. Let's make distinct ids.

Actually simpler: ids = [f"{prefix}{i}" for i in range(n)] but that's uniform/pattern. The instruction says avoid patterns that a simple trick could exploit. But the function is trivially simple; patterns don't matter much. Still, let's make ids random-ish but distinct.

```python
def _ids(n, seed, prefix):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        x = rng.randrange(10**9)
        s = f"{prefix}{x}"
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out
```

For int ids, just rng.randrange.

Now building the map: for typical case, indices 0..n-1 shuffled? In the repo, `data_loader.users()` returns a map. Let's just use index = i for straightforward, and shuffled for the shuffled case.

Let me define a builder:

```python
def _build(n, dim, seed, id_prefix="N", id_type=str, index_map=None, n_rows=None):
    emb = _embeddings(n_rows or n, dim, seed)
    ids = _ids(n, seed + 1, id_prefix) if id_type is str else _int_ids(n, seed + 1)
    if index_map is None:
        index_map = list(range(n))
    d = {ids[i]: index_map[i] for i in range(n)}
    return d, emb
```

Then thunk returns (d, emb, filename).

But careful: the function does `embeddings[index]`. If index_map has values >= n_rows, error. Ensure n_rows > max index.

For shuffled: index_map = list(range(n)); random.Random(seed).shuffle(index_map). n_rows = n.

For sparse: n=1500, n_rows=20000, index_map = random sample of 1500 distinct indices from range(20000).

For duplicates: index_map = [rng.randrange(300) for _ in range(n)], n_rows=300.

Now file names: distinct per case. "user_embeddings.tsv", "news_embeddings.tsv", etc. Use distinct names.

Since the function opens with "w", repeated calls just rewrite. No need to remove.

But wait — the harness renders arguments before and after each call to see whether it changed them. The dict and tensor are not modified. Good. But file_name is a string, unchanged.

One concern: the harness may render embeddings tensor (a torch tensor) — rendering a large tensor could be slow but that's harness's concern. Actually "Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values." So embeddings with n_rows*dim under 1M. For sparse: 20000*32 = 640k. OK. For large-dim: 400*200 = 80k. Fine.

Let me keep n_rows*dim < 1M everywhere. Sparse 20000*32=640000 ok.

Let me finalize sizes:

1. news-typical: n=2000, dim=32, n_rows=2000, prefix "N", indices 0..n-1 (maybe shuffled slightly)
2. users-large: n=3000, dim=16, n_rows=3000, prefix "U"
3. small-dim: n=4000, dim=8, n_rows=4000
4. large-dim: n=500, dim=256, n_rows=500 → 128k values, 128000*... wait n*dim = 128000 values written. And tensor 500*256=128000. Fine.
5. int-ids: n=2000, dim=32
6. shuffled-indices: n=2000, dim=32, shuffled index map
7. sparse: n=1500, dim=64, n_rows=8000 → tensor 512000, written 1500*65=97500
8. duplicates: n=3000, dim=32, n_rows=400 → written 3000*33=99000, tensor 12800

Wait for sparse, n_rows=8000, dim=64 → 512000 values in tensor, under 1M. Good.

Hmm actually rendering a 8000x64 tensor before and after each call might be slow for the harness but that's their problem; constraint is 1M.

Let me also make sure each case's file_name differs and the file is under WORKDIR.

For checks:
- empty map with empty embeddings: `({}, torch.zeros(0, 4), "empty.tsv")` — function writes nothing. Returns None.
- single element: `({"a": 0}, torch.zeros(1, 3), "single.tsv")`
- maybe an odd type: id_to_index_map with int keys? Or embeddings as numpy array? The function calls `.tolist()` on rows, numpy arrays support that. Let's use a numpy array for one check to test odd type. Actually numpy is imported in the module. Use numpy.zeros((2,3)).

Checks may raise; fine.

Let me write checks:
```python
def checks():
    return [
        ("empty", lambda: ({}, torch.zeros(0, 4), "check_empty.tsv")),
        ("single", lambda: ({"N1": 0}, torch.zeros(1, 3), "check_single.tsv")),
        ("numpy-array", lambda: ({"a": 0, "b": 1}, numpy.zeros((2, 3)), "check_numpy.tsv")),
    ]
```

Need to import numpy.

Now, the function uses `embeddings[index].tolist()`. For a torch tensor, `embeddings[index]` gives a 1D tensor, `.tolist()` gives list of floats. Good.

Now careful: torch.zeros(0,4) — embeddings empty, map empty, no indexing. Good.

Now the file is written to os.path.join(data_dir, file_name). data_dir = str(WORKDIR). Good.

Let me write the module-level data building.

Actually, one thing: `torch.randn` with generator. Let me use `torch.manual_seed` then `torch.randn`. Simpler.

Let me write:

```python
import random
import numpy
import torch
import train_mf
from train_mf import write_embeddings

train_mf.data_dir = str(WORKDIR)


def _ids(n, seed, prefix, as_int=False):
    rng = random.Random(seed)
    if as_int:
        return rng.sample(range(10**9), n)
    seen = set()
    out = []
    while len(out) < n:
        s = "%s%d" % (prefix, rng.randrange(10**9))
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _build(n, dim, seed, prefix="N", as_int=False, n_rows=None, index_map=None):
    torch.manual_seed(seed)
    rows = n_rows if n_rows is not None else n
    emb = torch.randn(rows, dim)
    ids = _ids(n, seed + 1000, prefix, as_int)
    if index_map is None:
        index_map = list(range(n))
    d = {ids[i]: index_map[i] for i in range(n)}
    return d, emb
```

For shuffled: index_map = list(range(n)); random.Random(seed).shuffle(index_map).

For sparse: index_map = random.Random(seed).sample(range(n_rows), n).

For duplicates: index_map = [random.Random(seed).randrange(k) for _ in range(n)].

Let me build module-level data:

```python
_NEWS_MAP, _NEWS_EMB = _build(2000, 32, 1, "N")
_USERS_MAP, _USERS_EMB = _build(3000, 16, 2, "U")

_small_dim_map, _small_dim_emb = _build(4000, 8, 3, "S")
_large_dim_map, _large_dim_emb = _build(500, 256, 4, "L")

_int_map, _int_emb = _build(2000, 32, 5, as_int=True, prefix="I")

_shuf_idx = list(range(2000))
random.Random(6).shuffle(_shuf_idx)
_shuf_map, _shuf_emb = _build(2000, 32, 7, "H", index_map=_shuf_idx)

_sparse_idx = random.Random(8).sample(range(8000), 1500)
_sparse_map, _sparse_emb = _build(1500, 64, 9, "P", n_rows=8000, index_map=_sparse_idx)

_dup_idx = [random.Random(10).randrange(400) for _ in range(3000)]
_dup_map, _dup_emb = _build(3000, 32, 11, "D", n_rows=400, index_map=_dup_idx)
```

Wait for _dup_idx, using same Random each time — need one rng instance. Let me do:

```python
_rng = random.Random(10)
_dup_idx = [_rng.randrange(400) for _ in range(3000)]
```

Similarly for sparse use one rng.

Now cases:

```python
def cases():
    return [
        ("news-typical", lambda: (_NEWS_MAP, _NEWS_EMB, "news_embeddings.tsv")),
        ("users-large", lambda: (_USERS_MAP, _USERS_EMB, "user_embeddings.tsv")),
        ("small-dim", lambda: (_small_dim_map, _small_dim_emb, "small_dim.tsv")),
        ("large-dim", lambda: (_large_dim_map, _large_dim_emb, "large_dim.tsv")),
        ("int-ids", lambda: (_int_map, _int_emb, "int_ids.tsv")),
        ("shuffled-indices", lambda: (_shuf_map, _shuf_emb, "shuffled.tsv")),
        ("sparse-indices", lambda: (_sparse_map, _sparse_emb, "sparse.tsv")),
        ("duplicate-indices", lambda: (_dup_map, _dup_emb, "duplicates.tsv")),
    ]
```

These thunks return the same objects each call. Function doesn't mutate. Good.

One concern: the file is written repeatedly to the same path, truncating. Fine.

But: the harness may check that arguments are unchanged by rendering. Rendering a torch tensor — fine.

Also, the harness runs the original and modified versions. The modified version might write to a different file? Not our concern.

Potential issue: `data_dir` — is it used as a global inside write_embeddings? Yes, `data_dir` is read from module globals. Setting `train_mf.data_dir` works.

Let me double check that WORKDIR exists — it's provided. We don't need to create it.

Also `os.path.join(data_dir, file_name)` — data_dir is str(WORKDIR). Good.

Now, one more: the task says "if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk." The main() sets data_dir via sys.argv. We set it directly.

Let me also ensure the imports work: `import train_mf` will execute the module, which imports mind_data, metrics, torch, numpy. mind_data may need files? Importing should be fine. It imports torch etc. Should be available.

Actually, train_mf imports `from mind_data import MindData` — mind_data module import. That might import pandas etc. Should be fine in the repo environment.

Also `data_dir = sys.argv[1] if len(sys.argv) > 1 else "../../mind/"` — at import time, sys.argv may have args from the harness. That's fine, we override.

Now about numpy import in checks — numpy is available (module imports it). I'll import numpy at top.

Let me finalize. I should also consider that torch.randn with manual_seed gives deterministic values. Good.

One more consideration: the file write. Each call writes the whole file. If the harness measures energy over many repetitions, the file is rewritten each time. Fine.

Let me also make sure that the values written are reasonable (floats). torch.randn gives floats around 0. "%.6f" formats them. Good.

Edge: duplicate indices — multiple ids map to same index, so same embedding row written multiple times. Fine.

I think this is good. Let me write the final code.

Actually, let me reconsider the output size constraint more carefully. "keep what it returns (and anything it writes) under about 100 000 values". The function writes to a file. If the harness captures file writes... it can't easily. I'll keep sizes moderate anyway: n*dim:

- news: 2000*32 = 64000
- users: 3000*16 = 48000
- small-dim: 4000*8 = 32000
- large-dim: 500*256 = 128000 — slightly over. Reduce to dim 192: 96000. Or n=400, dim=200 = 80000.
- int: 64000
- shuffled: 64000
- sparse: 1500*64 = 96000
- duplicates: 3000*32 = 96000

large-dim: let's do n=400, dim=200 → 80000. Tensor 400*200=80000.

Good.

Let me finalize with these numbers.

Actually for timing, dim 8 with 4000 rows = 32000 formats ~ maybe 7ms. Fine.

Let me write it.