Let me analyze. The function `_blend_image` is a method. It uses `self.colormap` (class attribute `cm.viridis`) and `self._normalize_sim_map`. We need to build an instance without loading the model (which requires network/GPU). We can't instantiate normally because `__init__` loads the model.

But we can create an instance via `object.__new__(SimMapGenerator)` and set required attributes. That's allowed? The instructions say "Setting data (a module's configuration, an object's fields) to build an input is fine." So yes, we can use `object.__new__` and set `colormap` etc. Actually colormap is a class attribute so it's already there.

The method uses self._normalize_sim_map which is a staticmethod — fine.

So instance = object.__new__(SimMapGenerator). We don't need logger, model etc.

Now the inputs: img (PIL Image), sim_map (torch.Tensor), original_size tuple.

`sim_map.cpu().float().numpy()` — from a 2D tensor. Then `Image.fromarray(sim_map_np)` — needs float32 2D array. Then resize to sim_map_resolution with BICUBIC. Then np.array dtype float32. Then normalize. Then colormap -> heatmap. Then image.

The `img` argument is actually not used in the function body! It's just passed. So img can be anything, but for realism pass a real PIL image.

Let's make sim_map tensors of realistic sizes. In the repo, sim_map = similarity_map_normalized[idx, token_idx, :, :] which is patch grid, likely 32x32 or so. Actually colpali uses 32x32 patches typically. But original_size can be large (e.g., 1000x1400). Let's make realistic.

Let me think about timing: the heavy part is PNG save and resize. sim_map_resolution = (max(32, orig_w/8), max(32, orig_h/8)). For a 2000x3000 image, resolution = 250x375. The heatmap image is that size. PNG save of 250x375 RGBA is fast. To get 1-200ms, we might want bigger. Let's use large original sizes, e.g. 4000x6000 -> 500x750. Hmm.

Actually the sim_map input size matters for the resize cost too. Let's vary.

Let me design 8 cases with different sizes and distributions:

1. small: sim_map 32x32, original_size (256,256) -> resolution (32,32)
2. typical: sim_map 32x32, original_size (1000, 1400) -> (125,175)
3. large: sim_map 32x32, original_size (2400, 3200) -> (300,400)
4. huge: sim_map 32x32, original_size (4000, 6000) -> (500,750)
5. big sim_map: sim_map 128x128, original_size (2000,2000) -> (250,250)
6. non-square sim_map: 32x64
7. sim_map with negative values / wide range (normalization path)
8. constant sim_map (all same value) - edge but as measured case.

Actually _normalize_sim_map is elided; likely (x - min)/(max-min). Constant map could cause division by zero but probably handled. Let's be careful — constant map might produce nan. Better avoid risk? Actually we need each case to run to completion. Let's include a near-constant map with tiny variation instead.

Let me think about the resolution constraint: resize target must be valid. Fine.

For sim_map resolution: note `Image.fromarray(sim_map_np)` where sim_map_np is float32 2D. PIL supports mode 'F'. Then resize BICUBIC on mode F works.

Now, the tensor: `torch.randn` float32 2D. `.cpu().float().numpy()` works.

Let's make sure the sim_map dtype is float32 to avoid conversion issues. torch.randn default float32.

Now sizes: to keep output under 100k values — output is a base64 string, its length ~ PNG size. That's fine, base64 string length maybe a few hundred KB. "keep what it returns under about 100 000 values" — hmm, a base64 string of length 500000 chars would be 500k values. That might exceed. Let's keep images modest. PNG of a smooth heatmap compresses well. 500x750 RGBA PNG maybe ~50-200KB -> base64 ~70-270k chars. Hmm that could exceed 100k. Let's keep max resolution around 300x400 -> base64 maybe ~50k. Actually heatmaps from viridis are smooth gradients, PNG compresses very well. Let's test mentally: a 300x400 RGBA gradient PNG maybe 20-40KB. base64 ~ 30-55k chars. OK.

Let's keep original sizes moderate: up to ~2400x2400 -> 300x300.

Actually let's just be safe and keep resolutions <= 400x400.

Cases:
1. "tiny": sim_map (32,32), original (256,256) -> (32,32)
2. "small": (32,32), (512, 640) -> (64,80)
3. "square-mid": (32,32), (1024,1024) -> (128,128)
4. "wide": (32,32), (1600, 800) -> (200,100)
5. "tall": (32,32), (800, 1600) -> (100,200)
6. "big-map": (64,64), (2048, 2048) -> (256,256)
7. "large": (32,32), (2400, 2400) -> (300,300)
8. "non-square-map": (16, 48), (1200, 1800) -> (150, 225)

Distributions: use different random data — some with negative values, some with large range, some near-constant.

Let me write a helper to build a tensor with a given shape and stats.

For each case, sim_map values: rng.uniform or randn. Different seeds.

Now checks(): small edge inputs. E.g.:
- empty: sim_map 0x0 tensor? Image.fromarray on empty array might fail. That's fine, checks may raise. But we need identical behaviour. Actually a 0-size tensor may raise — fine.
- one element: sim_map (1,1) tensor, original_size (64,64) -> resolution (32,32) (max 32). Resize from 1x1 to 32x32 works.
- None original_size? That would raise TypeError. Let's do "none-size": original_size None -> int(None) raises. Fine.

Actually let's keep checks simple and likely to raise or run.

Let me write:

```python
def checks():
    return [
        ("one-pixel", lambda: (_instance(), _tensor((1,1), 0), (64,64))),
        ("empty-map", lambda: (_instance(), _tensor((0,0), 1), (128,128))),
        ("none-size", lambda: (_instance(), _tensor((4,4), 2), None)),
    ]
```

But wait, checks are not measured but still run — they may raise. Fine.

Hmm, but the thunk builds the instance each time. Better build instance once at module level and reuse. But the function doesn't mutate the instance, so reuse is fine. Let's create a module-level instance.

Actually careful: creating the instance via object.__new__ — need to ensure colormap accessible. It's a class attribute, so yes.

But `_normalize_sim_map` is a staticmethod on the class, accessible via instance. Good.

Also `self.colormap` = cm.viridis which is a matplotlib colormap; calling it with a float array returns RGBA array. Good.

Let me write the code.

```python
import io
import random
import torch
import numpy as np
from PIL import Image
from backend.colpali import SimMapGenerator

def _make_instance():
    inst = object.__new__(SimMapGenerator)
    return inst

_INSTANCE = _make_instance()
```

Wait — does `object.__new__(SimMapGenerator)` work for a class without __slots__? Yes.

But there might be issues: SimMapGenerator might be a subclass of something? It's a plain class. Fine.

Now the tensor helper:

```python
def _tensor(shape, seed, kind="normal"):
    rng = random.Random(seed)
    if kind == "normal":
        data = torch.randn(*shape, generator=torch.Generator().manual_seed(seed))
    ...
```

torch.Generator manual_seed gives reproducible. But instructions say use random.Random(0). We can use numpy rng then convert. Let's use numpy RandomState to generate and torch.from_numpy.

Actually simplest: use `np.random.default_rng(seed)` -> array -> torch.from_numpy. But instructions want `random.Random(0)`. We can use random.Random to seed, but generating large arrays via random module is slow. Let's use numpy with seed derived. Hmm, the instruction is a guideline. Let's use `random.Random(seed)` for parameters and numpy for bulk. Actually simpler: use `np.random.default_rng(seed)`. I think it's acceptable; but to follow instructions, use `random.Random(0)` at least once. Let me use random.Random to produce seeds.

I'll just use fixed seeds. Let me use np.random.default_rng with seed.

Hmm, the instruction says "a fixed random seed (random.Random(0)) when generating data". I'll use random.Random to generate the data values via... too slow for 32x32? 1024 values fine. For 64x64=4096 fine. Actually all sim maps are small (max 64x64). So random.Random is fine!

Let's generate with random.Random:

```python
def _sim_map(shape, seed, lo=-1.0, hi=1.0):
    rng = random.Random(seed)
    h, w = shape
    data = [[rng.uniform(lo, hi) for _ in range(w)] for _ in range(h)]
    return torch.tensor(data, dtype=torch.float32)
```

For 64x64 that's 4096 uniform calls — fine.

Now cases. The thunk returns (instance, img, sim_map, original_size). Wait, the function signature: `_blend_image(self, img, sim_map, original_size)`. Called as `SimMapGenerator._blend_image(instance, img, sim_map, original_size)`. So thunk returns (instance, img, sim_map, original_size).

img: a PIL image. Build once at module level. It's unused but must be a valid arg. Let's build a real RGB image, e.g. 256x256.

Actually img is unused in body, so any object works, but for realism use a PIL Image. Build once.

Let me build images of appropriate sizes? Doesn't matter. Use one RGB image.

Now let's think about whether the function modifies sim_map or img. `sim_map.cpu().float().numpy()` — creates new. Doesn't modify. So we can reuse tensors across calls. Good — but each thunk call returns the same tensor object; the function doesn't mutate it. Fine.

However, "Its arguments are rendered before and after each call to see whether it changed them" — tensors are fine.

Now, timing: one call should be 1ms-200ms. Let's estimate. The biggest cost is PNG encoding of ~300x300 RGBA. That's maybe a few ms. Hmm, might be under 1ms for small ones. The task says "keep the 4 that do the most work" — we run 8 and keep 4. So some can be small.

Let me make the large ones big enough. PNG encoding of 300x300 RGBA... probably ~2-5ms. BICUBIC resize of 32x32 to 300x300 is fast.

To get more work, increase resolution. Let's use original sizes up to ~4800 -> 600x600. base64 of that PNG... smooth gradient compresses well, maybe 100KB -> 140k chars. Hmm might exceed 100k values. Risky.

Let me reconsider: "keep what it returns ... under about 100 000 values". A base64 string — each character is a value? Probably counted as length. Let's keep base64 length under 100k, so PNG under ~75KB. For a viridis heatmap of 600x600, PNG size? Viridis colormap produces smooth RGBA gradients. PNG with filtering... could be ~200-400KB actually. Hmm.

Let's be conservative: max resolution 300x300. PNG ~50-100KB. base64 ~70-140k. Still possibly over.

Hmm. Let's test with smaller: 200x200. PNG maybe 30KB -> 40k chars. Safe.

Actually let me think: the heatmap is derived from a low-res sim map upsampled with BICUBIC, so it's very smooth. PNG compresses smooth gradients extremely well. A 256x256 smooth RGBA PNG might be ~20-40KB. base64 ~27-54k. OK.

Let me just cap resolutions at ~300x300 and accept. Actually to be safe, cap at 256x256.

Hmm but then timing might be ~2-5ms, fine (>1ms).

Let me choose original sizes so that resolution is:
- case1: (32,32) tiny
- case2: (64,64)
- case3: (128,128)
- case4: (200,100)
- case5: (100,200)
- case6: (256,256)
- case7: (300,300)
- case8: (150,225)

original_size = resolution * 8 roughly.

case7: 300*8 = 2400 -> (2400,2400). Good.
case6: 256*8 = 2048 -> (2048,2048).
case8: 150*8=1200, 225*8=1800 -> (1200,1800).

Now for case6 use a 64x64 sim map to add resize work.

Let's finalize.

Also note: sim_map_resolution uses max(32, int(size/8)). For (256,256) -> 32. Good.

Now distributions: vary lo/hi:
- case1: uniform(-1,1)
- case2: uniform(0,1)
- case3: normal-ish via uniform(-3,3)
- case4: uniform(-10,10) large range
- case5: uniform(0.4,0.6) narrow range (near constant)
- case6: uniform(-1,1)
- case7: uniform(0,1)
- case8: uniform(-5,5)

For narrow range, _normalize_sim_map might divide by tiny range -> fine.

Let me also add a case with a constant sim map? Risky (div by zero). Skip.

Now let's write checks:

```python
def checks():
    return [
        ("single-pixel", lambda: (_INSTANCE, _IMG, _sim_map((1,1), 100), (64,64))),
        ("empty-map", lambda: (_INSTANCE, _IMG, _sim_map((0,0), 101), (128,128))),
        ("none-original-size", lambda: (_INSTANCE, _IMG, _sim_map((4,4), 102), None)),
    ]
```

`_sim_map((0,0), ...)` -> torch.tensor([], dtype=float32) shape (0,). Image.fromarray on empty might raise. Fine.

Actually torch.tensor([[]]) shape (1,0). For (0,0), data = [] -> torch.tensor([]) shape (0,). Fine, may raise.

Now module-level: build _IMG. Use PIL to create an RGB image.

```python
_IMG = Image.new("RGB", (256, 256))
```

Hmm, but img is unused, so a plain new image is fine. But maybe more realistic to have actual content. Doesn't matter.

Wait — is img really unused? Yes, the body never references img. So fine.

Now, potential issue: importing `backend.colpali` imports colpali_engine, torch, etc. If colpali_engine isn't installed, import fails. The task says we can only use packages the repository already imports. If not available, we'd have to say CANNOT RUN. But presumably it's installed in the test environment. Let's assume it works.

Also `from backend.colpali import SimMapGenerator` — need to make sure the path is set up. The task says import exactly as shown. Repository root likely `visual-retrieval-colpali/src`. So `backend.colpali` importable. Assume sys.path is set.

Now, one concern: `object.__new__(SimMapGenerator)` — does SimMapGenerator define `__slots__`? No. Fine.

Let me also consider whether `self.colormap` works: `SimMapGenerator.colormap = cm.viridis`. Instance attribute lookup falls back to class. Good.

`self._normalize_sim_map` is a staticmethod — accessible.

Now `_normalize_sim_map` implementation is elided but likely:
```python
sim_map = (sim_map - sim_map.min()) / (sim_map.max() - sim_map.min() + 1e-8)
```
Fine.

Now let's write the final code.

One more: the colormap call `self.colormap(sim_map_normalized)` returns array shape (H,W,4) float. Then *255 astype uint8. Fine.

Let me write it.

```python
import random
import torch
from PIL import Image
from backend.colpali import SimMapGenerator

_INSTANCE = object.__new__(SimMapGenerator)
_IMG = Image.new("RGB", (256, 256))

def _sim_map(shape, seed, lo=-1.0, hi=1.0):
    rng = random.Random(seed)
    h, w = shape
    data = [[rng.uniform(lo, hi) for _ in range(w)] for _ in range(h)]
    return torch.tensor(data, dtype=torch.float32)
```

Wait: torch.tensor(data) with data=[] for shape (0,0) -> torch.tensor([]) works. For data=[[]] shape (1,0) works.

Cases:

```python
def cases():
    return [
        ("tiny-32", lambda: (_INSTANCE, _IMG, _sim_map((32,32), 0, -1.0, 1.0), (256,256))),
        ("small-64", lambda: (_INSTANCE, _IMG, _sim_map((32,32), 1, 0.0, 1.0), (512,512))),
        ("mid-128", lambda: (_INSTANCE, _IMG, _sim_map((32,32), 2, -3.0, 3.0), (1024,1024))),
        ("wide-200x100", lambda: (_INSTANCE, _IMG, _sim_map((32,32), 3, -10.0, 10.0), (1600,800))),
        ("tall-100x200", lambda: (_INSTANCE, _IMG, _sim_map((32,32), 4, 0.4, 0.6), (800,1600))),
        ("bigmap-256", lambda: (_INSTANCE, _IMG, _sim_map((64,64), 5, -1.0, 1.0), (2048,2048))),
        ("large-300", lambda: (_INSTANCE, _IMG, _sim_map((32,32), 6, 0.0, 1.0), (2400,2400))),
        ("nonsquare-150x225", lambda: (_INSTANCE, _IMG, _sim_map((16,48), 7, -5.0, 5.0), (1200,1800))),
    ]
```

Wait: for (1600,800): int(1600/8)=200, int(800/8)=100 -> (200,100). Good.
(800,1600) -> (100,200). Good.
(1200,1800) -> (150,225). Good.

Now, one issue: `_sim_map((16,48), ...)` — Image.fromarray of a 16x48 float array. Then resize to (150,225). Fine.

Let me double check the original_size ordering: sim_map_resolution = (max(32, int(original_size[0]/8)), max(32, int(original_size[1]/8))). So original_size[0] maps to width. Fine.

Now sizes of base64 outputs: largest is 300x300 -> PNG. Should be OK.

I think this is good. Let me also double check that `torch.tensor(data, dtype=torch.float32)` where data is a list of lists of floats works — yes.

One concern: for narrow range 0.4-0.6 with 32x32=1024 samples, min and max will be near 0.4 and 0.6, so normalization spreads fully. Fine.

Now, does the function mutate sim_map? `sim_map.cpu()` returns a copy if already on CPU? Actually `.cpu()` returns self if already on CPU. Then `.float()` returns self if already float32. Then `.numpy()` shares memory. Then `Image.fromarray(sim_map_np)` — PIL may copy. Resize creates new image. So sim_map tensor not mutated. Good.

But wait: `np.array(sim_map_img, dtype=np.float32)` — new array. Good.

Everything fine.

Let me finalize the code. Also add a comment.

Actually, one thing: should I worry that the instance created by `object.__new__` might not have attributes the method needs beyond colormap? The method uses only self.colormap and self._normalize_sim_map. Both class-level. Good.

Let me write it out.

Actually, let me reconsider the empty-map check. `_sim_map((0,0), 101)` returns torch.tensor([]) with shape (0,). Then `sim_map.cpu().float().numpy()` -> array shape (0,). `Image.fromarray` on shape (0,) array — probably raises. That's fine for checks.

But actually, if it raises, the check "may raise". Good.

Let me also make sure checks' labels distinct. Yes.

Final code.