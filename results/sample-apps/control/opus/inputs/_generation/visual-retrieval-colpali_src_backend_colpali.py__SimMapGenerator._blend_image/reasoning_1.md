Let me analyze the function under test.

`_blend_image(self, img, sim_map, original_size)`.

It uses `self._normalize_sim_map` (staticmethod elided) and `self.colormap` (class attribute = cm.viridis).

We need to build a SimMapGenerator instance. But `__init__` loads a model (ColPali). That would require network/model download. We must avoid calling `__init__`. We can create the instance without calling `__init__` — e.g., `SimMapGenerator.__new__(SimMapGenerator)`. That's allowed? The instructions say no mocks/subclasses overriding methods. Creating an instance via `__new__` and setting fields is "setting data (an object's fields) to build an input is fine". We need `self.colormap` which is a class attribute, present on the class. And `self._normalize_sim_map` which is a staticmethod on the class. So `__new__` works.

Actually the task says "the method is called as `SimMapGenerator._blend_image(instance, ...)`". So we pass the instance.

But wait — `_normalize_sim_map` is elided. We don't know its body. It presumably normalizes. That's fine, it runs.

The `img` argument: is it actually used in `_blend_image`? Looking at the body: it computes sim_map stuff, creates heatmap_img, saves to buffer, returns base64. `img` is not used at all! Interesting. So `img` can be any PIL Image. But we still need a valid Image.

Actually `img` is unused in the body shown. So we can pass a small image.

Now the sim_map tensor: shape? In gen_similarity_maps, `sim_map = similarity_map_normalized[idx, token_idx, :, :]` — a 2D tensor of shape (n_patch, n_patch) presumably, e.g. 32x32. It's passed to `Image.fromarray(sim_map_np)`. For a 2D float array, `Image.fromarray` with mode inferred... For float32 2D array, PIL creates mode 'F'. Then `.resize(sim_map_resolution, BICUBIC)`. Then `np.array(sim_map_img, dtype=np.float32)`.

So sim_map is 2D, e.g., 32x32 floats in [0,1].

The `original_size` is the original image size (width, height)? Let's see: `sim_map_resolution = (max(32, int(original_size[0]/8)), max(32, int(original_size[1]/8)))`. Then resize to that. So original_size is (W, H) of the original image.

The resize resolution: for original_size like (1000, 700) -> (125, 87). Work is modest. To make it a real workload, use large original_size, e.g. (4000, 3000) -> (500, 375). The colormap call and PNG encoding dominate.

Hmm, but the sim_map input resolution is fixed at whatever we make it (32x32 from model). But the resize target is determined by original_size. Actually the input sim_map is what the model produces: n_patch x n_patch = 32x32. But we could vary it. Let's keep realistic: sim_map from `similarity_map_normalized[idx, token_idx, :, :]` which is n_patch x n_patch = 32x32.

Actually to make cases differ, vary original_size (which controls output resolution) and sim_map content (distribution).

The output is a base64 PNG string. Its size depends on resolution. For 500x375 RGBA PNG, maybe ~100-300 KB base64. That's one value, fine (under 100k values? It's a string, one value).

Wait: "keep what it returns (and anything it writes) under about 100 000 values". A string is a single value. Fine.

But the arguments are rendered before and after each call to see whether it changed them. The sim_map tensor — rendering a tensor... `sim_map.cpu().float().numpy()` — does it change sim_map? `.cpu()` on CPU tensor returns same. `.float()` returns same if already float. `.numpy()` shares memory. But we don't modify sim_map_np in place... `Image.fromarray(sim_map_np)` — hmm, does PIL copy? `Image.fromarray` may share memory for some modes. Then `.resize` creates new image. So sim_map not modified. Fine.

Rendering the tensor: the harness renders args. A 32x32 float tensor is 1024 values, fine.

Let me think about `Image.fromarray` with a float32 2D array. PIL supports mode 'F' (32-bit float). fromarray for float32 2D -> 'F' mode. Good.

Now, `_normalize_sim_map` is not shown. It might do something like `(sim_map - min)/(max-min)`. We don't know. It's a staticmethod on SimMapGenerator. Since we create instance via `__new__`, `self._normalize_sim_map` resolves to the class's staticmethod. Good.

Important: we must ensure the sim_map values are such that normalization doesn't produce NaN etc. But we don't know the implementation. Let's use values in a reasonable range like [0,1] with some variation, avoiding constant maps (which might cause division by zero). Actually constant map could be a check case. Hmm, risky. Let's use varied values.

Let me now think about how many values in the sim_map. The harness says keep each input's data under 1,000,000 values. 32x32 = 1024. Fine.

To make cases heavy, we can use larger sim_map input too? Realistic is 32x32. But maybe some other shapes. Let's vary original_size to control the resize target and thus the workload.

Actually the dominant cost: `self.colormap(sim_map_normalized)` where sim_map_normalized is shape (H', W') float. For 500x375 = 187500 values, colormap returns (H', W', 4). Then `(heatmap*255).astype(uint8)`, `Image.fromarray(...).convert("RGBA")`, PNG save.

Actually wait — colormap input is 2D array, returns RGBA. Then `(heatmap * 255).astype(np.uint8)` gives (H',W',4) uint8. `Image.fromarray` on that gives RGBA mode. `.convert("RGBA")` no-op. Save PNG.

So workload scales with H'*W' = (W/8)*(H/8).

For 1ms-200ms: 500x375 -> ~187k pixels, PNG encoding maybe 20-50ms. Good.

Let's design 8 cases with different original_size (resolutions) and sim_map distributions.

Let me consider: sim_map input is 32x32 typically. But `Image.fromarray(sim_map_np).resize(sim_map_resolution)`. If sim_map_resolution is smaller than 32, it upscales... Actually for small original_size, resolution is max(32,...) = 32. So resize 32x32 -> 32x32.

Let's make resolutions vary from ~100x100 to ~800x600.

Cases:
1. Small original_size (e.g., 256x256) -> 32x32 resolution, 32x32 sim_map. Small workload.
2. Medium 1024x768 -> 128x96.
3. Large 4000x3000 -> 500x375.
4. Very large 6000x4000 -> 750x500.
5. Non-square extreme aspect 8000x1000 -> 1000x125.
6. sim_map with different distribution (e.g., all near 0, or bimodal).
7. sim_map different shape input, e.g., 64x48 (if model used different n_patch).
8. sim_map with negative values / wide range.

Hmm, but we want the 4 heaviest to be kept. Fine.

Let me also consider `img` — unused but must be a PIL Image. Build once at module level, e.g., `Image.new("RGB", (64,64))`. But wait, if the harness renders args, an Image is fine.

Actually, could `img` be used by a modified version? The modified version might use img. But we just provide a valid image. Let's make it realistic: a real image of the original_size? That could be big memory. original_size like 6000x4000 RGB = 72MB. Too much maybe. But img is unused in original. To be safe and realistic, create a smaller image. Hmm. Actually for realism, the img would be the original image at original_size. But since it's unused, and memory limit ~100MB, let's create images of moderate size. Let's create an image matching original_size but downscaled? 

Actually let's just create a modest RGB image (e.g., 512x512) for all cases; the function doesn't use it. But if a modified version uses img, it'd still work. Keep memory low.

Hmm, but "prepare the way the repository's own callers do". The caller passes `img` = loaded image at original size. But we can't hold 6000x4000 images for 8 cases (that's 8*72MB = way over). Let's use smaller original_size values so images fit, or just use a single shared image.

Better: create one shared image per case at a moderate size, or reuse. Since img unused, I'll create one module-level image and reuse for all cases. But then cases differ only in sim_map and original_size. That's fine.

Actually, let me make original_size values more modest to keep images realistic: but resolution = original/8. To get 500x375 we need 4000x3000. Image at that size 36MB RGB. One shared image is fine (36MB). But we have 8 cases; if all share the same image, memory fine.

Hmm, but if the image is shared and unused, no problem. Let me just create a single 4000x3000 image? That's 36MB. Plus we need it. Actually let's not overthink; create a modest image 800x600 and use for all. The function doesn't use img.

But wait, will the harness render the image args? It says "Its arguments are rendered before and after each call". Rendering a PIL Image... probably repr. Fine.

Let me reconsider: maybe safer to make img small.

Let me now also worry about the `__new__` approach and whether the harness's "rendered before and after" would break. It renders args: instance, img, sim_map, original_size. Rendering the instance — repr of SimMapGenerator object, fine.

Now `_normalize_sim_map` — we don't know. Let's just trust it.

Let me think about potential issue: `Image.fromarray(sim_map_np)` where sim_map_np is float32 2D. In newer PIL, fromarray with float32 gives mode 'F'. resize with BICUBIC on 'F' mode works. Good.

Now, sim_map is a torch.Tensor. We create via `torch.rand(...)`. Need `sim_map.cpu().float().numpy()`.

Let me generate diverse sim_maps:
- Case A: uniform random [0,1] 32x32.
- Case B: smooth gradient (structured).
- Case C: bimodal (values near 0 or 1).
- Case D: larger 48x48.
- Case E: values in [-5, 5].
- Case F: mostly constant with a few spikes.

But careful: constant maps might break normalization (div by zero). Avoid pure constant.

Let's write helper.

```python
import base64
import io
import random

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

_INSTANCE = SimMapGenerator.__new__(SimMapGenerator)

def _image(w, h):
    rng = random.Random(0)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    ...
```

Hmm, creating a real image with random content. Let's just do `Image.new("RGB", (w,h))` or a gradient. Keep small.

Actually, let me reconsider whether `img` must have a particular size. Since unused, no.

Let me create a shared image: `_IMG = Image.new("RGB", (640, 480), (128, 128, 128))`. Hmm but rendering... fine.

Wait, but should img size relate to original_size? For realism yes, but memory. Let's create per-case images at a reduced size? No — just use one small image.

Hmm, actually maybe better: create images with random noise to be realistic, size 512x512. One shared.

Let me now write sim_map generators.

```python
def _rand_map(h, w, seed, low=0.0, high=1.0):
    rng = np.random.default_rng(seed)
    return torch.from_numpy(rng.uniform(low, high, size=(h, w)).astype(np.float32))
```

Use np.random.default_rng with fixed seed — deterministic. Good. Or use random.Random(0) as instructed "use a fixed random seed (random.Random(0))". Let's use random.Random for generating values to comply, but numpy is fine too. I'll use random.Random(0) with a helper.

Actually simpler: use `random.Random(seed)` and build lists then np.array. For 32x32 that's fine.

Let me do:

```python
def _map_from_rng(h, w, seed, transform):
    rng = random.Random(seed)
    data = [[transform(rng.random()) for _ in range(w)] for _ in range(h)]
    return torch.tensor(data, dtype=torch.float32)
```

Hmm transform per element. Fine.

Let me define cases:

1. "tiny-32" : original_size (256,256) -> resolution (32,32). sim_map 32x32 uniform.
2. "square-1k": (1024,1024) -> (128,128). sim_map 32x32.
3. "landscape-4k": (4000,3000) -> (500,375). sim_map 32x32.
4. "portrait-4k": (3000,4000) -> (375,500). sim_map 32x32.
5. "panorama": (8000,1200) -> (1000,150). sim_map 32x32.
6. "tall": (1200,8000) -> (150,1000). sim_map 32x32.
7. "bigmap": (4000,3000) -> (500,375), sim_map 64x64 smooth gradient.
8. "wide-range": (6000,4000) -> (750,500), sim_map values in [-5,5].

Hmm the resolutions: 1000x150 = 150k pixels. 750x500=375k. 500x375=187k.

PNG encoding of 375k RGBA pixels ~ maybe 50-100ms. OK.

Let me reduce risk of >1s: keep max around 750x500.

Now, the 4 heaviest will be kept by the harness. Fine.

Let me also think: does `_normalize_sim_map` possibly take long? Unknown. Probably fast.

Now `checks()`: 2-3 small edge inputs.
- empty sim_map? A 0x0 tensor. `Image.fromarray` on empty array would fail. Hmm, that would raise — checks may raise. But we should ensure the original doesn't crash in a way... checks are "checked only for identical behaviour, never measured. These may raise." So raising is fine as long as original and modified behave identically. But if it raises, does the harness compare exceptions? Presumably it compares. Let's include safe-ish ones.

Actually careful: if a check raises, maybe the harness handles it. The spec says they may raise. Let's include:
- ("single-pixel-map", sim_map 1x1, original_size (256,256))
- ("zero-size", original_size (0,0)) -> resolution (32,32) via max. sim_map 32x32. That works.
- ("none-image", img=None)? The function doesn't use img so it'd still work. But modified might. Hmm, "odd type". Let's do img=None — original returns fine since img unused. Actually risky if the modified version uses img; but the comparison is on original vs modified with same inputs, and they just need to behave identically. If modified uses img, it'd raise while original doesn't -> mismatch. But we don't know the modified version. The modified version is presumably an optimized version of the same function, likely still not using img. Hmm, but to be safe, maybe avoid None image.

Let's do checks:
- ("1x1-map", 1x1 sim_map, (256,256))
- ("zero-size", 32x32 map, (0,0))
- ("single-row", 1x32 map, (1024,1024))

Hmm, 1x32 map resized... fine.

Actually a 1x1 float map: `Image.fromarray(np.array([[0.5]], dtype=float32))` -> mode 'F' 1x1. resize to (32,32) bicubic. Fine.

Let me keep checks simple.

Now, one concern: `SimMapGenerator.__new__(SimMapGenerator)` — does that work given the class has no __slots__? Yes.

But the harness calls `SimMapGenerator._blend_image(instance, img, sim_map, original_size)`. Our thunk returns `(instance, img, sim_map, original_size)`.

Since `_blend_image` is an instance method, calling `SimMapGenerator._blend_image(instance, ...)` works.

Now, `self.colormap` = cm.viridis (class attribute). Good, available.

`self._normalize_sim_map` staticmethod. Good.

Let me double check: does creating instance via `__new__` skip `__init__`? Yes, `__new__` alone doesn't call `__init__` unless you call it. `SimMapGenerator.__new__(SimMapGenerator)` returns object without __init__. Good.

But wait — could `__new__` be overridden? Unlikely.

Now the module import: `from backend.colpali import SimMapGenerator`. The task says import as `from backend.colpali import SimMapGenerator`. But the repo path is `visual-retrieval-colpali/src/backend/colpali.py`. So sys.path must include `visual-retrieval-colpali/src`. The harness presumably sets it up. The task says "Import the repository's modules exactly as shown in the task." So just `from backend.colpali import SimMapGenerator`.

But importing that module imports `colpali_engine` etc. Those may not be installed... but the task says it's the function under test, so presumably the environment has it. Hmm, `colpali_engine` is a third-party package. If not available, import fails. But we're told to import exactly as shown. Let's trust.

Actually, importing backend.colpali triggers `from colpali_engine.models import ColPali, ColPaliProcessor`. If colpali_engine isn't installed, the whole thing fails. The task expects it works. Also `matplotlib` import. OK.

Now, memory: torch, numpy imported.

Let me write the code.

```python
import random

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

_INSTANCE = SimMapGenerator.__new__(SimMapGenerator)

_IMG = Image.new("RGB", (512, 512), (120, 140, 160))


def _tensor_from_values(values):
    return torch.tensor(values, dtype=torch.float32)


def _uniform_map(h, w, seed, low=0.0, high=1.0):
    rng = random.Random(seed)
    data = [[rng.uniform(low, high) for _ in range(w)] for _ in range(h)]
    return _tensor_from_values(data)
```

Hmm using rng.uniform. Fine.

For a smooth gradient map:

```python
def _gradient_map(h, w):
    ys = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
    data = (ys * 0.6 + xs * 0.4)
    return torch.from_numpy(data.astype(np.float32))
```

For bimodal:

```python
def _bimodal_map(h, w, seed):
    rng = random.Random(seed)
    data = [[0.0 if rng.random() < 0.5 else 1.0 for _ in range(w)] for _ in range(h)]
    return _tensor_from_values(data)
```

Now cases. Let me define a list of (label, thunk).

```python
def cases():
    return [
        ("small-square", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 0), (256, 256))),
        ("medium-square", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 1), (1024, 1024))),
        ("landscape-4k", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 2), (4000, 3000))),
        ("portrait-4k", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 3), (3000, 4000))),
        ("panorama", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 4), (8000, 1200))),
        ("tall", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 5), (1200, 8000))),
        ("gradient-bigmap", lambda: (_INSTANCE, _IMG, _gradient_map(64, 64), (4000, 3000))),
        ("wide-range", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 6, -5.0, 5.0), (6000, 4000))),
    ]
```

Wait, the tensor is created fresh each thunk call — that's fine and cheap (32x32). But the instruction says build large data once at module level. 32x32 is tiny. Fine. But creating it each call is cheap. However, "Same work on every call" — yes, same.

Actually, better to build at module level and return same tensor. But since the function might not modify it, reuse is fine. But creating fresh is also fine and guarantees no mutation carryover. Let's build at module level for the big ones? They're small. I'll build at module level to be clean and cheap.

Hmm, but each thunk returns the same tensor object across calls; if the function mutates it... it doesn't. Fine.

Let me build module-level constants.

Actually careful: `_uniform_map` uses random.Random seeded — deterministic. Good.

Let me reconsider the "wide-range" case: values in [-5,5]. `_normalize_sim_map` unknown; if it does min-max scaling, fine. If it does something like clip, fine.

Concern: what if `_normalize_sim_map` divides by std or something producing inf/nan with uniform data? Unlikely.

Actually, hmm, we don't know `_normalize_sim_map`. Let me think about what it likely is. In colpali_engine there's `normalize_similarity_map`. The static method probably wraps it. It likely does min-max normalization to [0,1]. Something like:

```python
@staticmethod
def _normalize_sim_map(sim_map):
    return (sim_map - sim_map.min()) / (sim_map.max() - sim_map.min())
```

If constant, div by zero -> nan. Our data is varied. Good.

Now the colormap: `cm.viridis(sim_map_normalized)` where normalized in [0,1]. If out of range (nan or >1), matplotlib clips/returns... Actually colormap with NaN returns bad color (0,0,0,0) maybe. Fine.

Let's ensure normalized values within [0,1] by construction. Since we don't know normalize, but if it's min-max, output is [0,1].

OK.

Now let me reconsider the `img` argument. Is it truly unused? Yes in the shown body. Good.

Let me also double-check the output size for the largest: 750x500 RGBA PNG. Base64 maybe ~500KB-1MB string. That's one value. Fine.

Memory: 8 cases, each producing a base64 string. But only 4 kept. And they're not stored simultaneously necessarily... Actually the harness runs each case. Fine.

Now, an issue: the harness "runs them on the original function and keep the 4 that do the most work". Then compares original vs modified. The base64 output must match. PNG encoding is deterministic. Good.

Now let me write checks:

```python
def checks():
    return [
        ("single-pixel-map", lambda: (_INSTANCE, _IMG, _uniform_map(1, 1, 10), (256, 256))),
        ("zero-size", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 11), (0, 0))),
        ("single-row-map", lambda: (_INSTANCE, _IMG, _uniform_map(1, 32, 12), (1024, 768))),
    ]
```

Hmm, `_uniform_map(1,1,10)` gives [[v]]. Image.fromarray of 1x1 float32 -> mode 'F'. resize to (32,32). Fine.

zero-size: original_size (0,0) -> max(32, 0)=32. Works.

single-row: 1x32 map -> resize. Fine.

Alternatively include an odd type: img=None. Let's include one with img=None since function ignores it? Risky for modified. I'll skip.

Actually let's reconsider: what if the modified version is a "faster" version that still ignores img. Then None is fine. But if they added img use... The task says "We run the original function and a modified version of it on your inputs". The modified version is likely a semantically-equivalent optimization. Probably still ignores img. But to be safe, keep img valid.

Let me finalize.

One more thought: should I worry that `SimMapGenerator.__new__` requires args? No.

Also `_INSTANCE` is shared across all cases; the function doesn't mutate self. Good.

Let me also double check import of numpy as np — the module imports numpy; we import it too for gradient. Fine.

Let me write final code.

Actually, one concern about `Image.fromarray` with float32: In some PIL versions, `fromarray` for float32 2D uses mode 'F'. Yes. Good.

But what about the resize of mode 'F' with BICUBIC — supported. Yes.

Now write it.

Let me reconsider making the workload heavier to be safe within 1ms-200ms. The smallest case (256x256 -> 32x32) is tiny, maybe <1ms. That's fine, it's a case; the harness keeps the 4 heaviest. But the spec says "One call should take roughly 1 ms to 200 ms". Small cases might be under 1ms. Let's bump the smallest to something like (512,512) -> (64,64). Fine.

Let me set:
1. ("square-512", (512,512) -> 64x64)
2. ("square-1k", (1024,1024) -> 128x128)
3. ("landscape-4k", (4000,3000) -> 500x375)
4. ("portrait-4k", (3000,4000) -> 375x500)
5. ("panorama", (8000,1200) -> 1000x150)
6. ("tall", (1200,8000) -> 150x1000)
7. ("gradient-bigmap", (4000,3000) -> 500x375, 64x64 map)
8. ("wide-range", (6000,4000) -> 750x500, [-5,5])

Good, diverse.

Write module-level constants for maps.

Final code:

```python
import random

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

# Build the instance without running __init__ (which loads the ColPali model).
_INSTANCE = SimMapGenerator.__new__(SimMapGenerator)

# The original image is unused by _blend_image, but callers always pass a real PIL image.
_IMG = Image.new("RGB", (512, 512), (120, 140, 160))


def _uniform_map(h, w, seed, low=0.0, high=1.0):
    rng = random.Random(seed)
    data = [[rng.uniform(low, high) for _ in range(w)] for _ in range(h)]
    return torch.tensor(data, dtype=torch.float32)


def _gradient_map(h, w):
    ys = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
    data = (ys * 0.6 + xs * 0.4).astype(np.float32)
    return torch.from_numpy(data)


_MAP_A = _uniform_map(32, 32, 0)
_MAP_B = _uniform_map(32, 32, 1)
_MAP_C = _uniform_map(32, 32, 2)
_MAP_D = _uniform_map(32, 32, 3)
_MAP_E = _uniform_map(32, 32, 4)
_MAP_F = _uniform_map(32, 32, 5)
_MAP_G = _gradient_map(64, 64)
_MAP_H = _uniform_map(32, 32, 6, -5.0, 5.0)


def checks():
    return [
        ("single-pixel-map", lambda: (_INSTANCE, _IMG, _uniform_map(1, 1, 10), (256, 256))),
        ("zero-size", lambda: (_INSTANCE, _IMG, _uniform_map(32, 32, 11), (0, 0))),
        ("single-row-map", lambda: (_INSTANCE, _IMG, _uniform_map(1, 32, 12), (1024, 768))),
    ]


def cases():
    return [
        ("square-512", lambda: (_INSTANCE, _IMG, _MAP_A, (512, 512))),
        ("square-1k", lambda: (_INSTANCE, _IMG, _MAP_B, (1024, 1024))),
        ("landscape-4k", lambda: (_INSTANCE, _IMG, _MAP_C, (4000, 3000))),
        ("portrait-4k", lambda: (_INSTANCE, _IMG, _MAP_D, (3000, 4000))),
        ("panorama", lambda: (_INSTANCE, _IMG, _MAP_E, (8000, 1200))),
        ("tall", lambda: (_INSTANCE, _IMG, _MAP_F, (1200, 8000))),
        ("gradient-bigmap", lambda: (_INSTANCE, _IMG, _MAP_G, (4000, 3000))),
        ("wide-range", lambda: (_INSTANCE, _IMG, _MAP_H, (6000, 4000))),
    ]
```

Wait — the same tensor object is returned each call. If the function modifies it... it doesn't. But the harness renders args before and after; comparing tensors is fine.

Hmm, but there's a subtlety: `sim_map.cpu().float().numpy()` shares memory with the tensor if it's already CPU float32. Then `Image.fromarray(sim_map_np)` — for mode 'F', PIL may or may not copy. If it doesn't copy and then resize... resize produces new image, doesn't modify source. So sim_map unchanged. Good.

Actually, `np.array(sim_map_img, dtype=np.float32)` reads the resized image. Fine.

I think this is good. Let me double check the `_uniform_map(1,1,...)` for checks — torch.tensor([[v]]) shape (1,1). Good.

One last concern: `Image.fromarray` on a (1,1) float32 array — works, mode 'F'.

Also `_uniform_map(1,32,...)` shape (1,32). Good.

I'm fairly confident. Write it.