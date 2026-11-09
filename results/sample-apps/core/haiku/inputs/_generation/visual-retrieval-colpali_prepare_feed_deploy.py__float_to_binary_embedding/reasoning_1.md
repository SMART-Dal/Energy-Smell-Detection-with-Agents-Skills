The function converts float embeddings to binary embeddings. Input is a dict mapping keys to vectors (lists or arrays of floats). In the repo, embedding_dict = {k: v for k, v in enumerate(embedding)} where embedding is a numpy array from generate_embeddings. Actually embedding is np.ndarray of shape (num_patches, dim). So v is a row of floats.

We need realistic scale. ColPali embeddings: typically 1030 patches per image, dim 128. So dict with 1030 keys, each a list of 128 floats.

We need 8 cases. Let's make varied sizes and dims.

Note: the function returns dict of lists of int8. Output size = num_vectors * (dim/8). Keep under 100k values. 1030 * 16 = 16480, fine.

Input data under 1,000,000 values: 1030*128 = 131840, fine.

Let's build cases:
1. Typical ColPali: 1030 patches x 128 dims.
2. Larger: 2048 patches x 128.
3. Different dim: 512 patches x 768.
4. Small: 32 patches x 128.
5. Many patches: 4096 x 128 (524288 values, ok).
6. dim 64: 2000 x 64.
7. dim 1024: 1000 x 1024 (1,024,000 values - slightly over 1M; use 900 x 1024 = 921600).
8. All positive/negative mix, zeros.

Use random.Random(0) with gauss for floats. Include zeros to test the >0 threshold.

Let's write it. Values as lists of floats (v is a row of numpy array, so list works with np.array(v)). Actually in repo v is np.ndarray row. We can pass numpy arrays too. Let's pass lists to be safe? np.array(v) works either way. Let's use lists.

Thunks: return dict. Function doesn't modify input, so we can reuse the same dict across calls. Actually it only reads. So build once at module level and return the same dict. That's fine.

Let me write module-level builder.

def _emb(n, dim, seed): rng = random.Random(seed); return {i: [rng.gauss(0,1) for _ in range(dim)] for i in range(n)}

Building 4096*128 = 524288 gauss calls, plus others. Total maybe ~1.5M gauss calls — under 10s? gauss is a bit slow, maybe 1-2 µs each → ~2-3 s. Fine.

Actually case 7: 900*1024 = 921600. Case 6: 2000*64=128000. Case 5: 4096*128=524288. Case 2: 2048*128=262144. Case 1: 131840. Case 3: 512*768=393216. Case 4: 4096. Total ~2.36M gauss → maybe 4-5s. Acceptable but let's be a bit careful. Could use rng.uniform or random() instead which is faster. Let's use rng.uniform(-1,1) — fast. But gauss is more realistic. Let's use uniform to be safe on time. Actually a mix: use uniform. Realistic embeddings are roughly normal but uniform is fine for energy measurement.

Hmm, but the >0 threshold matters: uniform(-1,1) gives ~50% positive. Good.

Add some zeros to test edge — but that's checks.

Let me include sparsity variation: one case with mostly negative, one with mostly positive. That changes packbits output but not work much. Still fine.

Let's write.

checks():
- empty dict: lambda: ({},)
- single vector: lambda: ({0: [1.0]},)
- zeros: lambda: ({0: [0.0, 0.0, 0.0]},)

These run fine actually. Should be fine.

Let me write the code.

For dims not multiple of 8, packbits handles. dim 128 multiple of 8.

Cases: I'll make 8.

1. "colpali-typical": 1030 x 128
2. "colpali-large": 2048 x 128
3. "dim-768": 512 x 768
4. "dim-64": 3000 x 64
5. "dim-1024": 900 x 1024
6. "many-patches": 4096 x 128
7. "small-batch": 32 x 128
8. "mixed-sparse": 1500 x 128 with mostly negative values

Let me write.

For the sparse one, use rng.random() < 0.1 to decide positive else negative.

Code:

import random

def _embedding(n, dim, seed, positive_ratio=None):
    rng = random.Random(seed)
    if positive_ratio is None:
        return {i: [rng.uniform(-1.0, 1.0) for _ in range(dim)] for i in range(n)}
    return {i: [(rng.uniform(0.0,1.0) if rng.random() < positive_ratio else rng.uniform(-1.0,0.0)) for _ in range(dim)] for i in range(n)}

Build at module level.

Note keys: repo uses enumerate so int keys. We'll use ints.

Write final.