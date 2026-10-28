We need to write inputs for `SimMapGenerator.gen_similarity_maps`. The instance is built via `SimMapGenerator.__init__`, which loads a ColPali model — that requires network access to download model from HuggingFace. Hmm. That's a problem: `load_model` loads `vidore/colpali-v1.2`. That requires network. Can we avoid it? The task says: "If the function cannot run here at all -- it needs network access ... and no input could avoid that, do not write code: reply with one line CANNOT RUN".

But wait — the method `gen_similarity_maps` itself doesn't need the model; it uses `self._load_image`, `self._prepare_similarity_map_tensor`, `self._blend_image`, `self.should_filter_token`. But `__init__` calls `load_model`. We must build the instance in the thunk. Building the instance requires loading the model → network.

Could we construct the instance without calling `__init__`? E.g. `SimMapGenerator.__new__(SimMapGenerator)` and set attributes manually? That's not a mock... Hmm, but it's avoiding the constructor. The rule says "no mocks, no monkeypatching". Creating an instance via `__new__` and setting fields is "Setting data (a module's configuration, an object's fields) to build an input is fine." Actually the instructions say: "Setting data (a module's configuration, an object's fields) to build an input is fine." So we could do `obj = SimMapGenerator.__new__(SimMapGenerator); obj.logger = ...; obj.n_patch = 32; ...` — but the methods `_load_image`, `_prepare_similarity_map_tensor`, `_blend_image` are elided; we don't know their bodies. They might use `self.model` or `self.processor`. `_load_image` probably just uses PIL. `_prepare_similarity_map_tensor` uses query_embs and vespa_sim_maps — probably just torch. `_blend_image` uses colormap, numpy, PIL.

Hmm, but also `normalize_similarity_map` from colpali_engine — that's a library function; is colpali_engine importable? It's imported at module top. If colpali_engine isn't installed, the import fails entirely. The task says we can use "packages the repository already imports". The environment presumably has them installed (since the function is under test). But colpali_engine may require torch, transformers etc. It's plausible installed.

The real problem: does `SimMapGenerator.__init__` get called? If we use `__new__` we skip model loading. Is that acceptable? It's a bit gray but the guidance explicitly permits setting object fields to build an input. However, "no subclass that overrides a method" — we're not subclassing. We're instantiating without init. Hmm.

But wait: the hidden methods' bodies are elided, so we don't know exactly what they need. Risk: `_load_image` might call `self.processor` for something? Unlikely — it's "Loads an image from a file path or a base64-encoded string", just PIL + base64. `_prepare_similarity_map_tensor` uses query_embs and vespa_sim_maps — constructing a tensor; may use `self.n_patch`. `_blend_image` uses `self.colormap`.

Actually, there's a real risk that the grader's "original function" is the actual repo code, and it works. Our job: produce inputs that run. If `__init__` requires network, then we should avoid `__init__`. Let me think about whether the model download would happen. `load_model` presumably does `ColPali.from_pretrained(model_name, ...)` which downloads from HF hub → network. So calling `__init__` would fail without network. Therefore we must bypass.

Alternatively, could we set `model_name` to something local? No, we can't change the code.

So: build instance via `object.__new__(SimMapGenerator)` and set needed attributes. That's "setting an object's fields". I think that's the intended path here, and it's the only way to run.

Hmm, but is it "faking the environment"? No. It's constructing an object for input. I'd say acceptable.

But there's another catch: the pipeline. `gen_similarity_maps` is a generator. Our thunk returns the arguments; the timing call is the function call. Since it's a generator function, calling it returns a generator without executing the body! Then the harness compares outputs — how? It says "The function's output is compared in full after every input". If they just call the function and compare, they'd get a generator object, which differs each call (different identity). Hmm. But that's the harness's problem; presumably the harness handles generators by consuming them? Unclear. Actually the timing "only that call" — for a generator, the work happens at iteration. Hmm, that would make the measurement meaningless.

Hmm, this is tricky. Maybe the harness materializes generators. We can't know. But we should design inputs so that the function's work is substantial, and hope the harness consumes.

Actually, wait. Let's re-read: "We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs." For a generator, presumably they do `list(result)` or similar. Many such benchmarks handle this. I'll assume they consume it.

Alternatively, we could make the thunk... no, the thunk returns args only.

OK. Let's think about what inputs look like.

`gen_similarity_maps(self, query, query_embs, token_idx_map, images, vespa_sim_maps)`.

- `query`: str
- `query_embs`: torch.Tensor — query embeddings, shape? In ColPali, query embeddings shape is (n_query_tokens, dim) e.g. (n_tokens, 128). 
- `token_idx_map`: Dict[int, str] mapping index → token.
- `images`: List[Path|str] — file paths or base64 strings.
- `vespa_sim_maps`: List[Dict] — Vespa similarity maps.

Let me recall the actual repo code for `_prepare_similarity_map_tensor` and `_blend_image`. This is from the colpali sample-app (vespa sample-apps). Let me try to recall:

```python
    def _prepare_similarity_map_tensor(
        self, query_embs: torch.Tensor, vespa_sim_maps: List[Dict]
    ) -> torch.Tensor:
        # Process similarity maps
        sim_map_tensor = torch.zeros(
            (len(vespa_sim_maps), query_embs.shape[0], self.n_patch, self.n_patch)
        )
        for img_idx, sim_map in enumerate(vespa_sim_maps):
            for token_idx, token_sim_map in sim_map.items():
                sim_map_tensor[img_idx, token_idx] = torch.tensor(token_sim_map)
        return sim_map_tensor
```

Something like that. The vespa_sim_maps is a list (per image) of dicts mapping token index → flattened similarity map (list of n_patch*n_patch floats). Actually I recall the Vespa response has `similarity_map` per image, as a dict of token index → list of floats of length 1024 (32x32).

And `_blend_image`:

```python
    def _blend_image(self, img, sim_map, original_size) -> str:
        sim_map = sim_map.cpu().numpy()
        sim_map = self._normalize_sim_map(sim_map)
        sim_map = (self.colormap(sim_map) * 255).astype(np.uint8)
        sim_map_img = Image.fromarray(sim_map[:, :, :3])
        sim_map_img = sim_map_img.resize(img.size, Image.BILINEAR)
        blended = Image.blend(img.convert("RGB"), sim_map_img, alpha=0.5)
        buffered = BytesIO()
        blended.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
```

Something like that. Also `_normalize_sim_map` normalizes to [0,1].

And `_load_image`: if str starts with something / is a path, open with PIL; else base64 decode.

Given the uncertainty, the safest approach: build inputs using real image files (PNG) written under WORKDIR, and vespa_sim_maps as lists of dicts of token index → list of floats of length n_patch*n_patch.

But we don't know the exact expected format of `vespa_sim_maps`. If the format is wrong, the original function raises, and the case is invalid. Risky. Let's try hard to recall the actual code.

The repo is vespa-engine/sample-apps, visual-retrieval-colpali. Let me recall `colpali.py`:

```python
import base64
import io
import logging
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Dict, Generator, List, Tuple, Union

import matplotlib.cm as cm
import numpy as np
import torch
from colpali_engine.interpretability.similarity_map_utils import normalize_similarity_map
from colpali_engine.models import ColPali, ColPaliProcessor
from colpali_engine.utils.torch_utils import get_torch_device
from PIL import Image
```

And:

```python
class SimMapGenerator:
    colormap = cm.viridis

    def __init__(self, logger, model_name="vidore/colpali-v1.2", n_patch=32):
        ...

    def load_model(self):
        model = ColPali.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map=self.device,
        ).eval()
        processor = ColPaliProcessor.from_pretrained(self.model_name)
        return model, processor
```

`_load_image`:

```python
    def _load_image(self, img: Union[Path, str]) -> Image:
        if isinstance(img, Path):
            return Image.open(img)
        # base64
        img_bytes = base64.b64decode(img)
        return Image.open(BytesIO(img_bytes))
```

Hmm, actually I recall something like:

```python
        if isinstance(img, str) and img.startswith("data:image"):
            ...
```

Not sure.

`_prepare_similarity_map_tensor`:

```python
    def _prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps):
        # Prepare the similarity map tensor
        sim_map_tensor = torch.zeros(
            (len(vespa_sim_maps), query_embs.shape[0], self.n_patch, self.n_patch),
            dtype=torch.float32,
        )
        for img_idx, sim_map in enumerate(vespa_sim_maps):
            for token_idx, token_sim_map in sim_map.items():
                sim_map_tensor[img_idx, int(token_idx)] = torch.tensor(
                    token_sim_map, dtype=torch.float32
                ).reshape(self.n_patch, self.n_patch)
        return sim_map_tensor
```

Hmm, I'm fairly unsure about the reshape. Let me think about what Vespa returns. In the Vespa app, the similarity map per token is a tensor of shape [32, 32]? Vespa returns `similarity_map` as a dict mapping token index → list of floats (flattened 1024). Actually I think the Vespa ranking feature returns `tensor` of type `tensor<float>(d0[32],d1[32])` maybe. Hmm.

Actually, in the vespa sample app "colpali" there's a `similarity_map` computed as a tensor. Let me think... The Vespa schema has:

```
rank-profile ... {
    function max_sim() { ... }
    ...
    match-features: ...
}
```

Hmm. I recall the Vespa response includes `similarity_map` as a tensor with dimension [n_query_tokens][32][32]? Or per token?

Let me consider: main.py does:

```python
    vespa_sim_maps = [hit["fields"]["similarity_map"] for hit in ...]
```

Hmm, I really can't recall. Let me think about the naming: `vespa_sim_maps: List[Dict]`. A list per image, each a Dict. The Dict presumably maps token index (str or int) to a list of floats. Then `_prepare_similarity_map_tensor` builds a tensor of shape (n_images, n_tokens, 32, 32).

Since it's a Dict, keys are token indices. In JSON from Vespa, keys would be strings. So probably `int(token_idx)` conversion.

Hmm, but maybe the values are already 2D lists. Then `torch.tensor(value)` would give a 32x32 tensor.

Given the ambiguity, maybe I should design the input to be robust: make each value a nested list of 32 lists of 32 floats. If the code does `torch.tensor(v).reshape(32,32)`, nested works too (reshape on a 32x32 tensor gives same). If code does `torch.tensor(v)` and assigns to `sim_map_tensor[img_idx, token_idx]` which is 32x32, nested works, flat 1024 would fail. So nested is safer? Unless the code does something like `torch.tensor(v).view(self.n_patch, self.n_patch)` — works for both.

Actually if the code does `sim_map_tensor[img_idx, token_idx] = torch.tensor(token_sim_map)` and token_sim_map is flat 1024, that raises. If nested 32x32, works. If code does `.reshape(32,32)`, both work. So nested list is the safer choice. Hmm, but if the code does `np.array(v)` and expects flat... unlikely.

Hmm, wait. Actually I now more strongly recall the Vespa similarity map being returned as a tensor of shape [n_query_tokens, 32, 32] per image, and the Python code doing something like:

```python
    def _prepare_similarity_map_tensor(self, query_embs, vespa_sim_maps):
        sim_map_tensor = torch.zeros(
            (len(vespa_sim_maps), query_embs.shape[0], self.n_patch, self.n_patch)
        )
        for idx, sim_map in enumerate(vespa_sim_maps):
            for token_idx, token_sim_map in sim_map.items():
                sim_map_tensor[idx, int(token_idx)] = torch.tensor(token_sim_map)
        return sim_map_tensor
```

I'll go with nested lists of shape (32,32) — that works with both `torch.tensor(v)` direct assignment and with reshape.

Hmm, but actually there's another possibility: the value could be a flat list and the code does `torch.tensor(v).reshape(n_patch, n_patch)`. Nested also works there.

OK nested it is. Actually wait — what if the code does `torch.tensor(token_sim_map, dtype=torch.float32).reshape(self.n_patch, self.n_patch)`? Nested 32x32 reshaped to 32x32 = fine.

What if the code expects a flat list and does `np.array(v).reshape(...)`? Fine too.

So nested 32x32 lists are the most compatible. Good.

Now `query_embs`: shape (n_tokens, dim). The tensor shape's first dim is used for the number of tokens. token_idx_map keys must be < n_tokens. In the real flow, `idx_to_token` comes from the query tokenizer, and query_embs from the model. n_tokens ~ number of query tokens (including special tokens). Typically ~10-30.

Let me set query_embs as a random tensor of shape (n_tokens, 128) float32.

`token_idx_map`: dict {i: token} for i in range(n_tokens). Tokens should be realistic: some filtered (like "<bos>", "▁", "?", "Question"), some not.

Now images: we need real image files. Create PNGs under WORKDIR. Sizes: realistic — maybe a page image of ~800x1000. But `_blend_image` resizes the sim map to img.size and blends, then PNG-encodes. Larger images → more work. Let's use sizes like 600x800, 1000x1400, etc.

Number of images: `gen_similarity_maps` loops over images × tokens. Work = n_images × n_tokens × (blend + PNG encode). For 1ms-200ms per call, we need to balance. PNG encoding of a 800x1000 RGB image takes maybe 20-50 ms. So maybe 3-5 images × 10 tokens = 30-50 blends → too slow (over 1s). Hmm.

Wait, the loop yields for each (image, token) pair. Each `_blend_image` does a resize + blend + PNG encode. That's expensive. So with 2 images and 8 tokens = 16 blends → maybe 300ms+. Hmm.

Let's estimate: PNG encode of 800x1000 RGB ~ 30ms. Resize of 32x32 → 800x1000 with BILINEAR ~ few ms. Blend ~ few ms. So ~40ms per blend. 5 blends = 200ms. So keep total blends ≤ ~5-10.

Hmm, but that limits diversity. Let's use smaller images: 300x400 → PNG encode ~5ms. Then 20 blends = 100ms. That's reasonable.

Actually, the harness "keep the 4 that do the most work" — so we want a range.

But careful: total output values. The function yields tuples with base64 strings. "keep what it returns under about 100 000 values". The base64 strings are large; but "values" probably means elements. Each yield is a tuple of 4 → 4 values. With 20 yields = 80 values. Fine. Actually base64 strings of images could be big but they're single values.

Hmm, but "keep each input's data under about 1 000 000 values" — vespa_sim_maps with n_images × n_tokens × 1024 floats. With 4 images × 20 tokens × 1024 = 81920. Fine.

Let's now think about the images. We need to create PNG files. Use PIL to create them with random noise (fixed seed) so they aren't uniform. Actually uniform images compress very well in PNG (fast encode). Random noise makes PNG encoding slower and more realistic. Let's use random noise via numpy with fixed seed.

Hmm, but "Avoid uniformity or patterns ... that a simple trick could exploit". Random noise is good.

Now, how many images and tokens per case? Let's design 8 cases with varying:
- number of images (1..5)
- number of tokens (5..25)
- fraction of filtered tokens
- image sizes
- base64 vs path images

Let's target per-call times spread between ~5ms and ~200ms.

Let me reconsider: is `_blend_image` really doing PNG encode? Yes, returns base64-encoded blended image, and main.py writes it as PNG. So yes.

Also note: the loop `for idx, img in enumerate(original_images)` uses `original_images` which are copies. And `similarity_map_normalized[idx, token_idx, :, :]`.

Note also `normalize_similarity_map(vespa_sim_map_tensor.flatten(0, 1))` — normalizes over the flattened (images*tokens) dimension. This is from colpali_engine. It likely does min-max normalization per... hmm, `normalize_similarity_map` in colpali_engine:

```python
def normalize_similarity_map(similarity_map: torch.Tensor) -> torch.Tensor:
    if similarity_map.ndim != 3:
        raise ValueError(...)
    min_vals = similarity_map.min(dim=-1, keepdim=True)[0].min(dim=-2, keepdim=True)[0]
    max_vals = similarity_map.max(dim=-1, keepdim=True)[0].max(dim=-2, keepdim=True)[0]
    return (similarity_map - min_vals) / (max_vals - min_vals + 1e-6)
```

Something like that. Fine.

Now: the `should_filter_token` static method — it's given in the docstring with test outputs. We know its behavior. Good, we can pick tokens.

Now let's think about `_load_image`. It takes Path or str. If Path → open file. If str → maybe base64. To be safe, use Path objects for file-based images, and for base64 case use a str that's valid base64 of a PNG. But if `_load_image` treats str as a path... Hmm. The type hint is `Union[Path, str]` and main.py passes `img_paths` which are `os.path` strings (paths!). Look: `images=img_paths` where img_paths is a list of paths (strings). And main.py checks `os.path.exists(img_path)`. So strings are paths!

So `_load_image` probably: if isinstance(img, Path) or os.path.exists(img) → Image.open; else base64 decode. Hmm, or maybe:

```python
    def _load_image(self, img):
        if isinstance(img, Path):
            return Image.open(img)
        try:
            return Image.open(BytesIO(base64.b64decode(img)))
        except Exception:
            return Image.open(img)
```

I don't know. Safest: use `Path` objects for all images. That's unambiguous — a Path is definitely a file path. Actually wait, does `_load_image` handle Path? The docstring says "Loads an image from a file path or a base64-encoded string", and type is `Union[Path, str]`. So Path is handled. Good. Use Path objects everywhere. That avoids the base64-vs-path ambiguity.

Hmm, but then we lose the base64 input path diversity. That's fine; safer.

Hmm, actually let me reconsider — maybe `_load_image` is:

```python
    def _load_image(self, img):
        if isinstance(img, str) and img.startswith("data:image"):
            img = img.split(",")[1]
            return Image.open(BytesIO(base64.b64decode(img)))
        return Image.open(img)
```

Path works with Image.open. Good.

Now: `original_images.append(img_pil.copy())` and `original_sizes.append(img_pil.size)`. Note `processed_images` is unused. Fine.

Now, potential issue: PIL lazily loads images. `Image.open(path)` doesn't read pixel data until needed. `.copy()` forces load. Fine.

Now let's write the module-level setup:

```python
import base64
import io
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator
```

Wait, the import path: `visual-retrieval-colpali/src/backend/colpali.py`, and the task says import as `from backend.colpali import SimMapGenerator`. So the harness sets up sys.path presumably. We just use that import.

Hmm, but importing `backend.colpali` imports `colpali_engine`, which imports transformers etc. Should be fine if installed.

Now, building the instance without `__init__`:

```python
def _make_generator():
    gen = SimMapGenerator.__new__(SimMapGenerator)
    gen.model_name = "vidore/colpali-v1.2"
    gen.n_patch = 32
    gen.device = "cpu"
    gen.logger = logging.getLogger("simmap")
    gen.model = None
    gen.processor = None
    return gen
```

Hmm, is this "faking"? The instructions say "Setting data (a module's configuration, an object's fields) to build an input is fine." I'll do it. But I'm a bit worried the graders consider `__new__` a mock-like trick. Alternatively... is there any way to call `__init__` without network? No.

Hmm, wait. Actually, let me reconsider. `load_model` is a method of the class that's elided. It calls `ColPali.from_pretrained(self.model_name, ...)`. If the model is cached locally in HF cache, no network needed. But we can't rely on that.

Also, `get_torch_device("auto")` — fine.

Another thought: maybe the harness's environment has HF_HUB_OFFLINE and the model cached? Unlikely.

Given "If the function cannot run here at all -- it needs network access ... and no input could avoid that, do not write code". Hmm. Does the function need network? The function under test is `gen_similarity_maps`; it doesn't need network itself. Only the constructor does. And we can avoid the constructor. So we can run it. I'll go with `__new__`.

Hmm, but hold on. Is that within the spirit? The instruction 4 says "no mocks, no monkeypatching... no subclass that overrides a method". Using `__new__` and setting fields is explicitly allowed ("Setting data ... an object's fields ... is fine"). OK, proceed.

Actually, hmm, one more consideration: `SimMapGenerator.__new__(SimMapGenerator)` — the class has no `__slots__`, so we can set attributes. Good.

Now the data builders.

```python
N_PATCH = 32
_DIM = 128
```

Images: create a set of PNG files of various sizes at module level.

```python
def _make_image(path, w, h, seed):
    rng = np.random.default_rng(seed)
    arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
    Image.fromarray(arr, "RGB").save(path, format="PNG")
```

Random noise images: PNG size ~ w*h*3 bytes, so 800x1000 = 2.4MB. Several images → tens of MB. That's fine but let's keep total under 100MB. Actually the constraint is on input data values; images on disk count as files. Let's keep images moderate.

Hmm, but random noise PNGs are big and slow to encode. Encoding 800x1000 noise PNG ~ maybe 100ms. That's part of setup (not timed) — fine. But `_blend_image` also encodes the blended image (blend of noise image with colormap → still noisy). So encoding time in the timed call is significant.

Let's pick image sizes: 320x400, 480x600, 640x800, 800x1000, 256x256.

Number of images per case: 1 to 4.

Tokens: n_tokens = query_embs.shape[0]. token_idx_map = {i: token}. Vespa sim maps: list of dicts, one per image, each dict mapping token_idx → 32x32 nested list of floats.

Note: in `_prepare_similarity_map_tensor`, the tensor is zero-initialized of shape (n_images, n_query_tokens, 32, 32) and filled from the dict. If some token indices are missing from the dict, those stay zero. In real Vespa, all tokens present? Probably. Let's include all token indices in each dict to be realistic. But then `normalize_similarity_map` normalizes each (image, token) map separately (per the colpali_engine implementation, which normalizes per-map over spatial dims). Hmm, actually let me reconsider: `normalize_similarity_map(vespa_sim_map_tensor.flatten(0, 1))` gives shape (n_images*n_tokens, 32, 32), then normalize over last two dims per map. So each map normalized independently. Then reshape back.

OK. So values in the dict can be arbitrary floats; normalization handles it.

Now, the number of yields = n_images × n_unfiltered_tokens. Each yield produces a base64 string of the blended PNG.

Let me now design 8 cases:

1. "single-image-few-tokens": 1 image (320x400), 8 tokens, 2 filtered → 6 yields.
2. "multi-image": 3 images (256x256, 320x400, 480x600), 10 tokens → ~10 yields each.
3. "many-tokens": 1 image (480x600), 25 tokens → 25 yields.
4. "large-image": 1 image (800x1000), 6 tokens → 6 yields.
5. "many-images": 4 images (256x256), 8 tokens → 32 yields.
6. "all-filtered": 2 images, tokens all filtered → 0 yields (fast). Hmm, that's not "substantial work". Maybe skip; but it's a different path. Actually it would be very fast (~1ms). It's a valid edge but maybe not useful. Let's instead do "mostly-filtered": 2 images, 12 tokens of which 9 filtered → 6 yields.
7. "big-combo": 2 images (640x800, 480x600), 15 tokens → 30 yields.
8. "tall-image": 1 image (500x1200), 12 tokens → 12 yields.

Let me estimate times. PNG encoding noise images: roughly proportional to pixels. 320x400=128k px → ~10ms? Let's say ~8ms. 800x1000=800k px → ~60ms.

Case 1: 6 yields × (resize+blend+encode 320x400) ≈ 6 × 12ms = 72ms. Hmm, a bit high but OK.
Case 3: 25 yields × 480x600 (288k px, ~20ms) = 500ms. Too slow! Reduce.

Hmm. Let me reduce token counts. The dominant cost is per-yield blend+encode.

Let's target: total yields × per-yield cost ≈ 20-150ms.

Let me use smaller images mostly: 200x260 (~52k px, ~4ms encode). Then 25 yields = 100ms.

Hmm, but is 200x260 realistic? The repo processes document page images, which are large (e.g., 1000+ px). But we can't afford many large ones. Let's mix.

Actually, maybe I'm overestimating PNG encode cost. PIL PNG encoding of a 320x400 RGB noise image: let's think. zlib compress of 384KB raw → maybe 30-60ms? Hmm, actually PIL's PNG encoder is reasonably fast, maybe 10-20ms for 128k pixels. Hard to say.

Let me be conservative and use moderate sizes with moderate counts.

Plan (images sizes, n_images, n_tokens, yields):

1. small-single: 1 img 240x320, 10 tokens (2 filtered) → 8 yields. Est ~8×6ms=48ms.
2. medium-single: 1 img 480x640, 8 tokens (1 filtered) → 7 yields. Est ~7×20ms=140ms.
3. multi-small: 3 imgs 200x260, 8 tokens (2 filtered) → 18 yields. Est ~18×4ms=72ms.
4. many-tokens: 1 img 320x400, 20 tokens (5 filtered) → 15 yields. Est ~15×10ms=150ms.
5. large-image: 1 img 800x1000, 5 tokens (0 filtered) → 5 yields. Est ~5×60ms=300ms. Too slow. Use 640x800 → 5×40=200ms. Hmm still. Use 4 tokens → 160ms.

Hmm, this is guesswork. Let's just aim for a spread and accept that one or two might exceed; the harness drops cases >1s and keeps the 4 heaviest. Actually it says "Inputs where one call takes over 1 s are dropped." So exceeding 1s is bad (dropped). Let's keep everything comfortably under ~300ms.

Let me be more careful. I'll use smaller images overall.

Let me reconsider: what's the actual image size in the sample app? They're PDF page renders, likely ~1000x1300. And the sample app processes maybe 10 images × ~20 tokens = 200 blends → 10+ seconds. That's a real workload but too slow for us.

OK, our cases are scaled down. Fine.

Let me define image sizes: 200x260, 260x340, 320x420, 400x520, 480x640, 640x800.

Case design:

1. "single-small": 1 img 320x420, 8 tokens (1 filtered) → 7 yields.
2. "single-medium": 1 img 480x640, 6 tokens (0 filtered) → 6 yields.
3. "three-small": 3 imgs (200x260, 260x340, 320x420), 6 tokens (1 filtered) → 15 yields.
4. "many-tokens": 1 img 260x340, 18 tokens (4 filtered) → 14 yields.
5. "large-image": 1 img 640x800, 4 tokens → 4 yields.
6. "two-medium": 2 imgs (400x520, 320x420), 8 tokens (2 filtered) → 12 yields.
7. "four-images": 4 imgs (200x260 ×2, 260x340, 320x420), 5 tokens (0 filtered) → 20 yields.
8. "tall-image": 1 img 300x900, 8 tokens (2 filtered) → 6 yields.

Hmm, these are all similar in cost. Let's diversify more: some with many filtered tokens (fast path), some with none.

Also diversity in the vespa_sim_maps content: some with all token indices present, some with sparse (missing indices → zeros). Also different value distributions: some with negative values, some with large ranges, some uniform.

Also diversity in image content: noise, gradient, solid-ish with shapes.

Actually — careful — "Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes." Random noise is good.

Hmm, but a pure random-noise image is not realistic for a document page. But it's fine for stress.

Let me also consider: does `_blend_image` maybe use `img.convert("RGB")`? If images are RGB already, fine.

Now, one more important thing: the function is a generator. If the harness doesn't consume it, no work is done and all cases are ~0ms. Nothing we can do about that. But we should make sure the arguments are correct so that consuming works.

Hmm, actually — should we worry that the harness calls the function and compares outputs directly (generator objects)? Then all outputs would be "different" each time... They probably handle it. Let's not worry.

Now let's write the code.

```python
import base64
import io
import itertools
import logging
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator
```

Wait — `WORKDIR` is provided. Use it for image files.

Module-level:

```python
_N_PATCH = 32
_EMB_DIM = 128
```

Image creation:

```python
def _write_image(name, width, height, seed, kind="noise"):
    path = WORKDIR / name
    rng = np.random.default_rng(seed)
    if kind == "noise":
        arr = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    elif kind == "gradient":
        x = np.linspace(0, 255, width, dtype=np.float32)
        y = np.linspace(0, 255, height, dtype=np.float32)
        gx, gy = np.meshgrid(x, y)
        arr = np.stack([gx, gy, (gx + gy) / 2], axis=-1).astype(np.uint8)
    else:
        arr = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    Image.fromarray(arr, "RGB").save(path, format="PNG")
    return path
```

Hmm, but images are created at module level — that's fine (setup not timed). But total module-level time must be < 10s. Creating ~10 images with noise: encoding 640x800 noise PNG ~ maybe 200ms. Total maybe 1-2s. Fine.

Actually, to reduce disk usage, reuse images across cases. Let's create a pool of images and reuse.

Let me create:
- img_200x260_a, img_200x260_b (noise, different seeds)
- img_260x340
- img_320x420
- img_400x520
- img_480x640
- img_640x800
- img_300x900 (tall)
- img_256x256

Total pixels: 52k+52k+88k+134k+208k+307k+512k+270k+65k ≈ 1.7M px → raw 5MB. PNG files maybe 5MB total. Fine.

Now the generator instance:

```python
def _new_generator():
    gen = SimMapGenerator.__new__(SimMapGenerator)
    gen.model_name = "vidore/colpali-v1.2"
    gen.n_patch = _N_PATCH
    gen.device = "cpu"
    gen.logger = logging.getLogger("sim_map_generator")
    gen.model = None
    gen.processor = None
    return gen
```

Hmm, `gen.logger.info(...)` — not called in gen_similarity_maps. Fine.

Now token maps. Realistic ColPali tokens: e.g. "▁What", "▁is", "▁the", "▁total", "▁revenue", "?", "<bos>", "▁", "▁in", "▁2023", ":", "<pad>", "▁of", "▁Q3", "▁figures", "▁Norwegian", "▁kroner", "▁million", "▁USD", "▁compared", "▁to", "▁last", "▁year", "▁growth", "▁percent", "%", "▁and", "▁profit", "▁margin", "▁was", "▁higher", "▁than", "▁expected", "▁by", "▁analysts", "▁according", "▁to", "▁Reuters", "▁data", "▁from", "▁the", "▁company", "▁report", "▁showed", "▁today", "▁in", "▁Oslo", "▁Norway", "▁the", "▁shares", "▁rose", "▁by", "▁2", ".", "3", "▁%", "▁to", "▁close", "▁at", "▁NOK", "▁1", "2", "3", ".", "4", "5", "▁per", "▁share", "▁on", "▁Friday", "▁.", "▁The", "▁company", "▁said", "▁it", "▁expects", "▁to", "▁report", "▁a", "▁profit", "▁of", "▁around", "▁NOK", "▁1", "▁billion", "▁for", "▁the", "▁full", "▁year", "▁." 

That's a lot. We'll build token maps from a pool.

Filtered tokens (should_filter_token returns True): tokens starting with '<', all whitespace, purely punctuation (no digits, not starting with '▁'), starting with '_', exactly 'Question', exactly '▁'.

Note: '▁' is filtered but '▁2' is not (starts with '▁' → not purely punctuation). Careful with our token pool: '▁' alone is filtered.

Let me create a token pool with a mix:

```python
_TOKENS = [
    "▁What", "▁is", "▁the", "▁total", "▁revenue", "▁for", "▁Q3", "▁2023", "?",
    "<bos>", "▁", "<pad>", ":", "▁in", "▁Norwegian", "▁kroner", "▁million",
    "▁USD", "▁compared", "▁to", "▁last", "▁year", "▁growth", "▁percent", "%",
    "▁and", "▁profit", "▁margin", "▁was", "▁higher", "▁than", "▁expected",
    "▁by", "▁analysts", "▁according", "▁Reuters", "▁data", "▁from", "▁company",
    "▁report", "▁showed", "▁today", "▁Oslo", "▁Norway", "▁shares", "▁rose",
    "▁2", ".", "3", "▁NOK", "▁1", "5", "▁per", "▁share", "▁on", "▁Friday",
    "▁The", "▁said", "▁it", "▁expects", "▁a", "▁around", "▁billion", "▁full",
    "Question", "▁_", "_x", "\n", "▁(", "/)", "▁9", "▁8", "▁7", "▁6",
]
```

Hmm, careful: is '▁(' purely punctuation? It starts with '▁' so not purely punctuation → not filtered. And '▁_' starts with '▁' → not filtered? The rule "Start with an underscore '_'" — '▁_' starts with '▁' not '_'. Hmm, the rule says tokens that "start with an underscore '_'". '▁' is not '_'. So '▁_' is not filtered. Whatever — we don't need to be exact; the function decides. We just need a mix.

Let me just include a variety and let the function filter.

Actually, to be safe about the exact filtering behavior, I'll pick tokens that are clearly filtered and clearly not:
- Clearly filtered: "<bos>", "<pad>", "Question", "▁", ":", "?", "%", "\n", "/)", "_foo"
- Clearly not filtered: "▁What", "▁revenue", "▁2", "▁NOK", "▁percent", "▁2023", "2", "3"

Wait, "2" is not filtered (digits). ":" is filtered. "%" filtered. "/)" filtered.

OK.

Now: I want different cases to have different filtered ratios.

Let's write a helper that builds a token_idx_map from a list of tokens.

```python
def _token_map(tokens):
    return {i: t for i, t in enumerate(tokens)}
```

And query_embs: torch.randn(n_tokens, _EMB_DIM, generator=torch.Generator().manual_seed(seed)).

Now vespa_sim_maps: list of dicts, one per image. Each dict: {token_idx: 32x32 nested list}.

Build with numpy rng:

```python
def _sim_map(rng, n_patch=32):
    return rng.random((n_patch, n_patch)).tolist()
```

Wait — but the values need to be JSON-like floats. `.tolist()` gives nested lists of Python floats. Good.

But careful: `torch.tensor(nested_list)` works.

Hmm, what if `_prepare_similarity_map_tensor` does something like `np.array(v)` then `torch.from_numpy`? Works with nested too.

What if it expects a flat list and does `torch.tensor(v).view(32,32)`? Works with nested too (view on 32x32 → 32x32).

What if it does `torch.tensor(v).flatten()`? Fine.

OK.

Now, should every token index appear in each image's dict? In Vespa, the similarity map is computed for all query tokens. Let's include all indices for most cases, but one case with a sparse dict (some indices missing) to exercise the zero-fill path. Hmm, but if the code does `sim_map_tensor[idx, token_idx] = ...` for present ones, missing ones stay zero. Fine.

Actually risk: if the code builds the tensor by iterating over the dict and requires all tokens... no, it zero-inits. Fine.

Hmm, but there's a risk the code does something like:

```python
sim_map_tensor = torch.tensor([list(sim_map.values()) for sim_map in vespa_sim_maps])
```

Then dict ordering matters and keys are ignored. In that case, our dicts must have keys in order 0..n-1 and all present. To be safe, always include all token indices 0..n_tokens-1 in order. Hmm. But then the sparse case is risky.

Hmm. Which is more likely? Given the signature `List[Dict]` and the docstring "List of Vespa similarity maps", and the code needs to index by token_idx... I'd guess dict keyed by token index.

Hmm, let me think about the actual Vespa response. In the Vespa colpali app, the schema returns a `similarity_map` field which is a tensor of type `tensor<float>(query_token{}, x[32], y[32])`? Hmm, actually I don't think Vespa supports string-mapped dims in a way that maps to a dict...

Hmm, actually I now recall more specifically. Let me think about the Vespa app "visual-retrieval-colpali". The schema:

```
field colbert type tensor<int8>(patch{}, v[128]) {
    indexing: attribute | index
}
```

And the rank profile computes `max_sim` and also `similarity_map`... Hmm.

Actually, I recall the Python code in main.py:

```python
        vespa_sim_maps = [
            hit["fields"]["similarity_map"] for hit in response.hits
        ]
```

Hmm, and Vespa returns tensors as dicts with string keys for mapped dimensions. E.g. `{"0": [...], "1": [...]}`.

Hmm, or maybe the similarity map is returned as a nested structure.

Let me think about it differently: `vespa_sim_maps: List[Dict]` — a list of dicts. If Vespa returned a tensor with a mapped dimension, the JSON would be a dict. So keys are token indices as strings. Then `_prepare_similarity_map_tensor` does:

```python
for img_idx, sim_map in enumerate(vespa_sim_maps):
    for token_idx, token_sim_map in sim_map.items():
        sim_map_tensor[img_idx, int(token_idx)] = torch.tensor(token_sim_map)
```

That fits. And the values would be the flattened 32x32 tensor... which in Vespa JSON for a 2D tensor would be a nested list. Hmm.

Actually hold on. Let me reconsider. In Vespa, a tensor `tensor<float>(query_token{}, x[32], y[32])` — hmm, but actually I think the similarity map is computed per token as a separate ranking feature. Hmm.

Honestly, I recall the actual code now... Let me try:

```python
    def _prepare_similarity_map_tensor(
        self, query_embs: torch.Tensor, vespa_sim_maps: List[Dict]
    ) -> torch.Tensor:
        sim_map_tensor = torch.zeros(
            (len(vespa_sim_maps), query_embs.shape[0], self.n_patch, self.n_patch)
        )
        for img_idx, sim_map in enumerate(vespa_sim_maps):
            for token_idx, token_sim_map in sim_map.items():
                sim_map_tensor[img_idx, int(token_idx)] = torch.tensor(
                    token_sim_map
                ).reshape(self.n_patch, self.n_patch)
        return sim_map_tensor
```

I'm fairly confident about the `.reshape(self.n_patch, self.n_patch)` part actually... no, not confident.

Given uncertainty, nested 32x32 lists work with `.reshape(32,32)` too. And they work with direct assignment. So nested is strictly safer. Unless the code does `torch.tensor(token_sim_map).flatten()` then reshape — still fine.

What if the code does `np.array(token_sim_map, dtype=np.float32)` and then `.reshape`? Fine.

What if the value is expected to be a flat list of 1024 and the code does `torch.tensor(v)` directly into a 32x32 slot (no reshape)? Then nested fails? No — nested 32x32 into a 32x32 slot works, flat 1024 would fail. So nested is safe.

What if the code does `torch.tensor(v).reshape(-1)` and then something? Unlikely.

OK, nested.

Hmm, one more: what if the values are expected to be strings like "0.5,0.3,..."? No.

Let's go with nested.

Now, also: what if `vespa_sim_maps` is actually a list of dicts where the dict maps token index to a *list of floats* and the code does `torch.tensor(token_sim_map).view(self.n_patch, self.n_patch)`? Nested works.

Good.

Now, `query_embs.shape[0]` must equal the number of tokens. And `token_idx_map` keys should be within range.

Let me now write the cases.

I'll define a builder:

```python
def _case(images, tokens, seed, sparse=False, scale=1.0):
    n_tokens = len(tokens)
    gen = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, _EMB_DIM, generator=gen)
    token_idx_map = {i: t for i, t in enumerate(tokens)}
    rng = np.random.default_rng(seed)
    vespa = []
    for _ in images:
        d = {}
        for i in range(n_tokens):
            if sparse and i % 3 == 2:
                continue
            d[i] = (rng.random((_N_PATCH, _N_PATCH)) * scale).tolist()
        vespa.append(d)
    return query_embs, token_idx_map, list(images), vespa
```

Hmm, but the thunk must return `(instance, query, query_embs, token_idx_map, images, vespa_sim_maps)` since it's called as `SimMapGenerator.gen_similarity_maps(instance, ...)`.

The instance: create once at module level and reuse? The function doesn't mutate self (I think). `should_filter_token` is static. `_load_image`, `_blend_image` don't mutate. So a single instance is fine. But to be safe, create it in the thunk (cheap).

Actually, creating in the thunk is cheap and safer. But `SimMapGenerator.__new__` is cheap. Let's create at module level once and reuse — no, actually let's just create in the thunk; it's a few attribute sets.

Hmm, but "keep a thunk cheap next to one call" — attribute setting is negligible.

Now, the images list: `list(images)` — the function doesn't modify the list. Actually it iterates. Fine. But it does `original_images.append(img_pil.copy())` — that's a local list. Fine.

Also the function doesn't modify vespa_sim_maps. But to be safe, return it as-is (no copy) since it's not mutated. Actually `_prepare_similarity_map_tensor` iterates only. Fine.

Hmm, but "Its arguments are rendered before and after each call to see whether it changed them" — if we pass the same list object each time, and it's not modified, fine.

Now let's write the 8 cases.

Let me define the token lists:

```python
_TOKENS_FULL = [
    "▁What", "▁is", "▁the", "▁total", "▁revenue", "▁for", "▁Q3", "▁2023", "?",
    "<bos>", "▁", "<pad>", ":", "▁in", "▁Norwegian", "▁kroner", "▁million",
    "▁USD", "▁compared", "▁to", "▁last", "▁year", "▁growth", "▁percent", "%",
    "▁and", "▁profit", "▁margin", "▁was", "▁higher", "▁than", "▁expected",
    "▁by", "▁analysts", "▁according", "▁Reuters", "▁data", "▁from", "▁company",
    "▁report", "▁showed", "▁today", "▁Oslo", "▁Norway", "▁shares", "▁rose",
    "▁2", ".", "3", "▁NOK", "▁1", "5", "▁per", "▁share", "▁on", "▁Friday",
    "▁The", "▁said", "▁it", "▁expects", "▁a", "▁around", "▁billion", "▁full",
]
```

That's 64 tokens. Good for many-tokens cases.

Filtered ones among these: "?", "<bos>", "▁", "<pad>", ":", "%", "." — 7 filtered. Hmm, "." is purely punctuation → filtered. "5" is a digit → not filtered. "3" not filtered.

I want cases with high filter ratios too. Let's make a token list with many filtered:

```python
_TOKENS_FILTER_HEAVY = [
    "<bos>", "▁What", "<pad>", ":", "▁", "?", "▁revenue", "%", "▁", "\n",
    "/)", "▁total", "Question", "_x", "▁2023", "▁", "▁profit", "▁",
]
```

Wait "▁" repeated — but token_idx_map is a dict keyed by index, so duplicates are fine (different indices, same token). Realistic? In ColPali, "▁" might appear multiple times. OK.

Hmm, but duplicates in the token map: the function yields `(idx, token, token_idx, b64)`. Fine.

Let me count filtered in that list: "<bos>" T, "▁What" F, "<pad>" T, ":" T, "▁" T, "?" T, "▁revenue" F, "%" T, "▁" T, "\n" T, "/)" T, "▁total" F, "Question" T, "_x" T, "▁2023" F, "▁" T, "▁profit" F, "▁" T. So 12 filtered, 6 not. Good — 6 yields per image.

OK.

Now let me finalize the cases. I'll define images as Path objects.

Images pool (created at module level):

```python
_IMG = {}
def _build_images():
    specs = {
        "a": (200, 260, 1),
        "b": (200, 260, 2),
        "c": (260, 340, 3),
        "d": (320, 420, 4),
        "e": (400, 520, 5),
        "f": (480, 640, 6),
        "g": (640, 800, 7),
        "h": (300, 900, 8),
        "i": (256, 256, 9),
    }
    for name, (w, h, seed) in specs.items():
        p = WORKDIR / f"simmap_{name}_{w}x{h}.png"
        rng = np.random.default_rng(seed)
        arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        Image.fromarray(arr, "RGB").save(p, format="PNG")
        _IMG[name] = p
```

Module-level call `_build_images()`.

Hmm, that's ~1.7M pixels of noise → PNG encode at maybe 100 MB/s → ~1s. Fine.

Now cases:

1. "single-small": images=[_IMG["d"]], tokens=_TOKENS_FULL[:10] (10 tokens, filtered: "?" and ":" → wait _TOKENS_FULL[:10] = ["▁What","▁is","▁the","▁total","▁revenue","▁for","▁Q3","▁2023","?","<bos>"] → filtered: "?", "<bos>" → 8 yields on 320x420.

2. "single-medium": images=[_IMG["f"]], tokens=_TOKENS_FULL[10:20] = ["▁","<pad>",":","▁in","▁Norwegian","▁kroner","▁million","▁USD","▁compared","▁to"] → filtered: "▁","<pad>",":" → 7 yields on 480x640. ~7×25ms=175ms.

3. "three-small": images=[a,b,c], tokens=_TOKENS_FULL[20:28] = ["▁last","▁year","▁growth","▁percent","%","▁and","▁profit","▁margin"] → filtered: "%" → 7 yields × 3 imgs = 21 yields, small images. ~21×5ms=105ms.

4. "many-tokens": images=[_IMG["c"]], tokens=_TOKENS_FULL[:30] → filtered: "?", "<bos>", "▁", "<pad>", ":" → 25 yields on 260x340. ~25×8ms=200ms. Hmm.

Let me reduce to _TOKENS_FULL[:24] → filtered 5 → 19 yields. OK.

5. "large-image": images=[_IMG["g"]], tokens=_TOKENS_FULL[30:36] = ["▁higher","▁than","▁expected","▁by","▁analysts","▁according"] → 0 filtered → 6 yields on 640x800. ~6×50ms=300ms. Hmm, maybe reduce to 4 tokens. Let's use _TOKENS_FULL[30:34] → 4 yields ~200ms.

Hmm, but then case 2 (480x640, 7 yields) might be ~175ms. OK.

6. "filter-heavy": images=[_IMG["d"], _IMG["e"]], tokens=_TOKENS_FILTER_HEAVY → 6 unfiltered × 2 imgs = 12 yields on 320x420 and 400x520. ~12×12ms=144ms.

7. "four-images": images=[a,b,i,c], tokens=_TOKENS_FULL[36:42] = ["▁Reuters","▁data","▁from","▁company","▁report","▁showed"] → 0 filtered → 6×4=24 yields on small images. ~24×5ms=120ms.

8. "tall-sparse": images=[_IMG["h"]], tokens=_TOKENS_FULL[42:52] = ["▁today","▁Oslo","▁Norway","▁shares","▁rose","▁2",".","3","▁NOK","▁1"] → filtered: "." → 9 yields on 300x900. ~9×30ms=270ms. Hmm, tall image 300x900 = 270k px. Maybe reduce tokens to 6 → ~180ms.

Hmm, I'm making all cases similar in the 100-300ms range. That's fine — the harness keeps the 4 heaviest. But we want diversity in "work done". Let's have a couple of cheaper ones (~10-30ms) and a couple heavier.

Let me redo with a clearer spread:

1. "tiny-single": 1 img 200x260, 6 tokens (2 filtered) → 4 yields. ~15ms.
2. "small-single": 1 img 320x420, 10 tokens (2 filtered) → 8 yields. ~60ms.
3. "medium-single": 1 img 480x640, 10 tokens (3 filtered) → 7 yields. ~150ms.
4. "large-single": 1 img 640x800, 5 tokens (1 filtered) → 4 yields. ~150ms.
5. "three-small": 3 imgs (200x260, 260x340, 320x420), 8 tokens (1 filtered) → 21 yields. ~90ms.
6. "many-tokens": 1 img 260x340, 24 tokens (5 filtered) → 19 yields. ~130ms.
7. "filter-heavy": 2 imgs (320x420, 400x520), 18 tokens (12 filtered) → 12 yields. ~120ms.
8. "four-images": 4 imgs (200x260, 200x260, 256x256, 260x340), 6 tokens (0 filtered) → 24 yields. ~100ms.

Hmm, still clustered. Whatever — real workloads vary. Let's also add a "sparse vespa map" case.

Actually, let me reconsider whether the per-yield cost is really that high. Let me estimate PIL PNG save for a 320x420 RGB noise image. PIL uses zlib with default compression. Raw data 403KB. zlib compress level 6 on random data → maybe 5-15 ms. Plus the resize from 32x32 to 320x420 (bilinear) ~1ms, blend ~1ms, base64 encode ~0.5ms. So ~10ms per yield. 

For 480x640: raw 921KB → ~20ms.
For 640x800: raw 1.5MB → ~35ms.

OK so my estimates hold roughly.

Now, one concern: `normalize_similarity_map` from colpali_engine — is it expensive? It operates on (n_images*n_tokens, 32, 32) — cheap.

Another concern: `torch.tensor(nested_list)` for each token — cheap.

OK.

Now, let me also double check: `_blend_image(img, sim_map, original_size)` — `sim_map` is a torch tensor of shape (32,32) (float32). It probably does `.cpu().numpy()`. Fine.

Now, `original_size` is `img_pil.size` = (width, height). And `_blend_image` may resize the sim map to `original_size` or to `img.size`. Either way fine.

Hmm, one potential issue: if `_blend_image` does `Image.fromarray(...)` with a colormap array of shape (32,32,4) and takes [:,:,:3] → RGB. Fine.

Now let's also handle: what if `_load_image` returns an image in mode "RGB"? Our PNGs are RGB. Good.

Let me now also think about `checks()`. 2-3 small edge inputs, never measured, may raise.

Edge cases:
- Empty images list: `images=[]`, `vespa_sim_maps=[]`, query_embs shape (5,128), token_idx_map with 5 tokens. The function would loop over zero images → no yields. `_prepare_similarity_map_tensor` with empty list → tensor of shape (0, 5, 32, 32). `normalize_similarity_map` on shape (0, 32, 32)... might raise. That's OK (may raise).
- Empty token map: `token_idx_map={}` → no yields.
- None / odd type: maybe pass an empty list of tokens.

Let's do:
```python
def checks():
    return [
        ("no-images", lambda: (_gen(), "q", _embs(4), {i: t for i, t in enumerate(_TOKENS_FULL[:4])}, [], [])),
        ("no-tokens", lambda: (_gen(), "q", _embs(0), {}, [_IMG["a"]], [{}])),
        ("empty-query", lambda: (_gen(), "", _embs(0), {}, [], [])),
    ]
```

Hmm, `_embs(0)` gives shape (0, 128). `_prepare_similarity_map_tensor` with query_embs.shape[0]=0 → tensor shape (1, 0, 32, 32). `normalize_similarity_map` on (0, 32, 32)... might raise. OK.

Actually, for "no-tokens", images has 1 image but vespa_sim_maps has [{}] — the tensor is (1,0,32,32). Fine.

These may raise; that's allowed.

Hmm, but careful: checks are run and compared between original and modified. If they raise, both raise presumably the same way. Fine.

Now let me write the actual code carefully.

```python
import logging
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator


_N_PATCH = 32
_EMB_DIM = 128
```

Wait — does the function use `self.n_patch`? Yes in `_prepare_similarity_map_tensor` probably. We set it to 32.

Now images:

```python
_IMAGE_SPECS = {
    "a": (200, 260, 1),
    "b": (200, 260, 2),
    "c": (260, 340, 3),
    "d": (320, 420, 4),
    "e": (400, 520, 5),
    "f": (480, 640, 6),
    "g": (640, 800, 7),
    "h": (300, 900, 8),
    "i": (256, 256, 9),
}

_IMG = {}


def _build_images():
    for name, (w, h, seed) in _IMAGE_SPECS.items():
        path = WORKDIR / f"simmap_img_{name}.png"
        rng = np.random.default_rng(seed)
        arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        Image.fromarray(arr, "RGB").save(path, format="PNG")
        _IMG[name] = path


_build_images()
```

Hmm, `WORKDIR` is a provided `pathlib.Path`. It's available at module level. Good.

Now the instance:

```python
def _generator():
    gen = SimMapGenerator.__new__(SimMapGenerator)
    gen.model_name = "vidore/colpali-v1.2"
    gen.n_patch = _N_PATCH
    gen.device = "cpu"
    gen.logger = logging.getLogger("sim-map-generator")
    gen.model = None
    gen.processor = None
    return gen
```

Now tokens:

```python
_TOKENS = [
    "▁What", "▁is", "▁the", "▁total", "▁revenue", "▁for", "▁Q3", "▁2023",
    "?", "<bos>", "▁", "<pad>", ":", "▁in", "▁Norwegian", "▁kroner",
    "▁million", "▁USD", "▁compared", "▁to", "▁last", "▁year", "▁growth",
    "▁percent", "%", "▁and", "▁profit", "▁margin", "▁was", "▁higher",
    "▁than", "▁expected", "▁by", "▁analysts", "▁according", "▁Reuters",
    "▁data", "▁from", "▁company", "▁report", "▁showed", "▁today", "▁Oslo",
    "▁Norway", "▁shares", "▁rose", "▁2", ".", "3", "▁NOK", "▁1", "5",
    "▁per", "▁share", "▁on", "▁Friday", "▁The", "▁said", "▁it", "▁expects",
    "▁a", "▁around", "▁billion", "▁full", "▁year", "▁end", "▁2024",
    "▁outlook", "▁remains", "▁strong", "▁despite", "▁market", "▁volatility",
    "▁and", "▁currency", "▁headwinds", "▁in", "▁the", "▁region",
]
```

Hmm, that's 76 tokens. Fine.

Filter-heavy list:

```python
_TOKENS_FILTER_HEAVY = [
    "<bos>", "▁What", "<pad>", ":", "▁", "?", "▁revenue", "%", "▁", "\n",
    "/)", "▁total", "Question", "_x", "▁2023", "▁", "▁profit", "▁",
]
```

Now the builder:

```python
def _build_case(image_names, tokens, seed, scale=1.0, sparse=False):
    n_tokens = len(tokens)
    gen = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, _EMB_DIM, generator=gen)
    token_idx_map = {i: t for i, t in enumerate(tokens)}
    rng = np.random.default_rng(seed)
    vespa = []
    for _ in image_names:
        d = {}
        for i in range(n_tokens):
            if sparse and (i % 4 == 3):
                continue
            d[i] = (rng.random((_N_PATCH, _N_PATCH)) * scale).tolist()
        vespa.append(d)
    images = [_IMG[n] for n in image_names]
    return query_embs, token_idx_map, images, vespa
```

Hmm, `rng.random(...) * scale` — for scale diversity.

Now thunks:

```python
def _thunk(query, query_embs, token_idx_map, images, vespa):
    return lambda: (_generator(), query, query_embs, token_idx_map, images, vespa)
```

Wait, the function signature is `gen_similarity_maps(self, query, query_embs, token_idx_map, images, vespa_sim_maps)`. So the args tuple is `(instance, query, query_embs, token_idx_map, images, vespa_sim_maps)`. Good.

Now cases. Let me precompute at module level so thunks are cheap:

```python
_CASES_DATA = {}


def _make_case(label, image_names, tokens, seed, scale=1.0, sparse=False):
    data = _build_case(image_names, tokens, seed, scale, sparse)
    _CASES_DATA[label] = data
```

Hmm, simpler: just build in module-level code with variables.

Let me write:

```python
_C1 = _build_case(["d"], _TOKENS[0:10], 11)
_C2 = _build_case(["f"], _TOKENS[10:20], 12)
_C3 = _build_case(["a", "b", "c"], _TOKENS[20:28], 13)
_C4 = _build_case(["c"], _TOKENS[0:24], 14)
_C5 = _build_case(["g"], _TOKENS[30:34], 15)
_C6 = _build_case(["d", "e"], _TOKENS_FILTER_HEAVY, 16)
_C7 = _build_case(["a", "b", "i", "c"], _TOKENS[36:42], 17)
_C8 = _build_case(["h"], _TOKENS[42:48], 18, sparse=True)
```

Then:

```python
def cases():
    return [
        ("single-320x420-10tok", lambda: (_generator(), "What is the total revenue for Q3 2023?", *_C1)),
        ...
    ]
```

Wait, `*_C1` unpacks the 4-tuple into the lambda's return tuple. That works: `lambda: (a, *tup)`. Yes, valid Python 3.5+. But careful: it must be a tuple. `(_generator(), "q", *_C1)` → tuple. Good.

Hmm, but the thunk "returns a tuple of positional arguments". So `(_generator(), query, *_C1)` where _C1 = (query_embs, token_idx_map, images, vespa). Good.

Actually, let me be explicit for clarity.

Let me now reconsider case sizes once more, aiming for a spread and safety.

Actually, I realize I should double-check: does the harness maybe call the generator function and then compare `list(result)`? If it compares the generator object itself, outputs would never match. Let's assume they materialize.

Hmm, actually, there's a subtlety: if the harness does `result = func(*args)` and then `repr(result)` to compare... generators have default repr with id. That would differ. But then the benchmark would be broken for any generator function. Presumably they handle it.

OK.

Now, another consideration: the function's returned base64 strings — comparing them requires deterministic output. Our inputs are deterministic (fixed seeds). Good.

But: `torch.randn` with a fixed generator — deterministic. Good.

Now, potential nondeterminism: PIL PNG encoding is deterministic. Good.

Now let me reconsider the "sparse" case (C8). If the code does `torch.tensor([list(sim_map.values()) for sim_map in vespa_sim_maps])`, sparse would break (different lengths). Risk. Let me drop sparse to be safe? Hmm, but it exercises the zero-fill path.

Actually, the risk is that the original function raises → case is dropped. The harness "keep the 4 that do the most work" — but a raising case is invalid. Hmm, "Every case must run to completion on the original function without raising." So a risky case could invalidate.

Let me weigh: how likely is the code to iterate dict values in order rather than by key? Given the dict is keyed by token index and the tensor is indexed by token_idx, iterating items() and using the key is the natural implementation. I'd say 80% likely. And even if it iterates values in order, our dicts for non-sparse cases have keys 0..n-1 in insertion order, so values order matches. Only the sparse case breaks.

Hmm, but if the code iterates values in order and our dict has keys 0..n-1 in order, it works. So sparse is the only risk. Let me keep sparse but... hmm.

Alternative: make the sparse case have all keys but with some zero-valued maps? That doesn't exercise the same path.

I'll keep one sparse case — it's a realistic scenario? Actually in Vespa, would some tokens be missing? Probably not. Hmm.

Actually, let's think again. In Vespa, the similarity map for a query token that doesn't appear in the document... The ColBERT max-sim is computed for all query tokens. So all present. So sparse isn't realistic.

I'll drop sparse and instead vary the value distributions (scale) and use different numbers of tokens. Safer.

Hmm, but then all cases are "all keys present". Fine.

Actually wait, one more realistic variation: Vespa might return the similarity map only for tokens that pass some threshold. Eh. Let's not.

Let me instead make case 8 use a different value distribution: e.g., values in [-1, 1] (negative similarities). Use `rng.uniform(-1, 1, ...)`. That exercises normalization with negatives.

Let me add a `dist` parameter to `_build_case`.

OK, let me finalize.

Final case list (8):

1. `("single-small", img d=320x420, tokens 0:10 (8 unfiltered))` — 8 yields.
2. `("single-medium", img f=480x640, tokens 10:20 (7 unfiltered))` — 7 yields.
3. `("three-small", imgs a,b,c, tokens 20:28 (7 unfiltered))` — 21 yields.
4. `("many-tokens", img c=260x340, tokens 0:24 (19 unfiltered))` — 19 yields.
5. `("large-image", img g=640x800, tokens 30:34 (4 unfiltered))` — 4 yields.
6. `("filter-heavy", imgs d,e, _TOKENS_FILTER_HEAVY (6 unfiltered))` — 12 yields.
7. `("four-images", imgs a,b,i,c, tokens 36:42 (6 unfiltered))` — 24 yields.
8. `("tall-negative", img h=300x900, tokens 42:48 (6 unfiltered))` — 6 yields, negative values.

Hmm, case 8: 300x900 = 270k px → ~25ms each × 6 = 150ms.

Let me double check the filtered counts.

_TOKENS[0:10] = ["▁What","▁is","▁the","▁total","▁revenue","▁for","▁Q3","▁2023","?","<bos>"]
Filtered: "?" (punct, no digits, not ▁) → True; "<bos>" → True. So 8 unfiltered. ✓

_TOKENS[10:20] = ["▁","<pad>",":","▁in","▁Norwegian","▁kroner","▁million","▁USD","▁compared","▁to"]
Filtered: "▁" True, "<pad>" True, ":" True. → 7 unfiltered. ✓

_TOKENS[20:28] = ["▁last","▁year","▁growth","▁percent","%","▁and","▁profit","▁margin"]
Filtered: "%" True. → 7 unfiltered. ✓

_TOKENS[0:24] = indices 0..23: adds "▁in","▁Norwegian","▁kroner","▁million" to the first 20. So filtered: "?", "<bos>", "▁", "<pad>", ":" → 5 filtered → 19 unfiltered. ✓

_TOKENS[30:34] = ["▁than","▁expected","▁by","▁analysts"] → 0 filtered → 4. ✓

_TOKENS_FILTER_HEAVY: filtered = "<bos>", "<pad>", ":", "▁", "?", "%", "▁", "\n", "/)", "Question", "_x", "▁", "▁" → let me count: indices 0("<bos>")T, 1("▁What")F, 2("<pad>")T, 3(":")T, 4("▁")T, 5("?")T, 6("▁revenue")F, 7("%")T, 8("▁")T, 9("\n")T, 10("/)")T, 11("▁total")F, 12("Question")T, 13("_x")T, 14("▁2023")F, 15("▁")T, 16("▁profit")F, 17("▁")T. → 13 filtered, 5 unfiltered. Hmm, 5 unfiltered × 2 imgs = 10 yields. Fine.

Wait: is "_x" filtered? Starts with "_" → yes. Is "▁2023" filtered? Starts with "▁", contains digits → not purely punctuation → not filtered. ✓. Is "▁revenue" not filtered ✓.

Hmm, what about "▁" — "Are exactly the single character '▁'" → True. ✓

OK, 5 unfiltered.

_TOKENS[36:42] = ["▁data","▁from","▁company","▁report","▁showed","▁today"] → 0 filtered → 6 × 4 imgs = 24 yields. ✓

_TOKENS[42:48] = ["▁Oslo","▁Norway","▁shares","▁rose","▁2","."] → filtered: "." → 5 unfiltered. Hmm, I said 6. Let me recount: "▁Oslo"F, "▁Norway"F, "▁shares"F, "▁rose"F, "▁2"F, "."T → 5 unfiltered. OK, 5 yields.

Now, wait: I need to double check my _TOKENS list indexing. Let me write it out with indices:

0: ▁What
1: ▁is
2: ▁the
3: ▁total
4: ▁revenue
5: ▁for
6: ▁Q3
7: ▁2023
8: ?
9: <bos>
10: ▁
11: <pad>
12: :
13: ▁in
14: ▁Norwegian
15: ▁kroner
16: ▁million
17: ▁USD
18: ▁compared
19: ▁to
20: ▁last
21: ▁year
22: ▁growth
23: ▁percent
24: %
25: ▁and
26: ▁profit
27: ▁margin
28: ▁was
29: ▁higher
30: ▁than
31: ▁expected
32: ▁by
33: ▁analysts
34: ▁according
35: ▁Reuters
36: ▁data
37: ▁from
38: ▁company
39: ▁report
40: ▁showed
41: ▁today
42: ▁Oslo
43: ▁Norway
44: ▁shares
45: ▁rose
46: ▁2
47: .
48: 3
49: ▁NOK
...

Good. So _TOKENS[30:34] = ["▁than","▁expected","▁by","▁analysts"] ✓
_TOKENS[36:42] = ["▁data","▁from","▁company","▁report","▁showed","▁today"] ✓
_TOKENS[42:48] = ["▁Oslo","▁Norway","▁shares","▁rose","▁2","."] ✓

Good.

Now the query strings: use realistic query text.

Now let's write the final code.

One more consideration: `_generator()` is called in each thunk. It creates a new instance each time. That's cheap. But is `SimMapGenerator.__new__` OK? Yes.

Hmm, actually — maybe safer to create the instance once at module level and reuse it, since `__new__` + attribute setting is trivially fast either way. But creating it once avoids any weirdness. Actually, if the harness renders the instance's repr... no, it renders arguments. Hmm, "Its arguments are rendered before and after each call to see whether it changed them". The instance is an argument. Rendering it — `repr(gen)` → `<backend.colpali.SimMapGenerator object at 0x...>`. That's stable for the same object. If we create a new one each thunk call, the repr changes between calls but the harness compares before/after each call, so it's fine.

Hmm, but actually if they compare before/after, and the object doesn't change, fine either way.

Let me create one shared instance at module level and reuse. Simpler and cheaper.

Actually, careful: `lru_cache` on `get_query_embeddings_and_token_map` — not used here. OK.

Let me use a single module-level instance.

Hmm, but if the function mutates self... it doesn't. OK.

Actually, let's create a fresh one per thunk anyway — no. Single instance. Fine.

Wait, there's a subtlety with the harness rendering arguments: if the same instance object is passed each call, and it's rendered, fine.

OK, single instance `_GEN = _generator()`.

Now writing final code.

```python
import logging
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator

_N_PATCH = 32
_EMB_DIM = 128

_IMAGE_SPECS = {
    "a": (200, 260, 1),
    "b": (200, 260, 2),
    "c": (260, 340, 3),
    "d": (320, 420, 4),
    "e": (400, 520, 5),
    "f": (480, 640, 6),
    "g": (640, 800, 7),
    "h": (300, 900, 8),
    "i": (256, 256, 9),
}

_IMG = {}


def _build_images():
    for name, (w, h, seed) in _IMAGE_SPECS.items():
        path = WORKDIR / f"simmap_img_{name}.png"
        rng = np.random.default_rng(seed)
        arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        Image.fromarray(arr, "RGB").save(path, format="PNG")
        _IMG[name] = path


_build_images()
```

Hmm — `Image.fromarray(arr, "RGB")` — the second positional arg is `mode`. In newer Pillow, `Image.fromarray(obj, mode=None)`. Passing "RGB" is fine.

Now tokens and builder.

```python
def _generator():
    gen = SimMapGenerator.__new__(SimMapGenerator)
    gen.model_name = "vidore/colpali-v1.2"
    gen.n_patch = _N_PATCH
    gen.device = "cpu"
    gen.logger = logging.getLogger("simmap")
    gen.model = None
    gen.processor = None
    return gen


_GEN = _generator()
```

Now:

```python
def _build_case(image_names, tokens, seed, low=-0.0, high=1.0):
    n_tokens = len(tokens)
    gen = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, _EMB_DIM, generator=gen)
    token_idx_map = {i: t for i, t in enumerate(tokens)}
    rng = np.random.default_rng(seed + 1000)
    vespa = []
    for _ in image_names:
        d = {}
        for i in range(n_tokens):
            d[i] = rng.uniform(low, high, size=(_N_PATCH, _N_PATCH)).tolist()
        vespa.append(d)
    return query_embs, token_idx_map, [_IMG[n] for n in image_names], vespa
```

Hmm, `rng.uniform(low, high, size=(32,32)).tolist()` → nested lists of floats. Good.

Note: `torch.randn(n, dim, generator=gen)` requires n >= 0. For checks with n=0, fine.

Now build cases:

```python
_CASE_1 = _build_case(["d"], _TOKENS[0:10], 101)
...
```

Then:

```python
def cases():
    return [
        ("single-small-320x420", lambda: (_GEN, "What is the total revenue for Q3 2023?", *_CASE_1)),
        ...
    ]
```

Hmm, `*_CASE_1` inside a tuple literal — valid.

But wait: is `_CASE_1` a tuple of 4? Yes: (query_embs, token_idx_map, images, vespa). So `(_GEN, query, *_CASE_1)` gives 6 elements: instance, query, query_embs, token_idx_map, images, vespa. 

Now checks:

```python
def checks():
    return [
        ("no-images", lambda: (_GEN, "revenue", _build_case([], _TOKENS[0:4], 201)[0], {i: t for i, t in enumerate(_TOKENS[0:4])}, [], [])),
        ...
    ]
```

Hmm, `_build_case([], ...)` returns vespa=[] and images=[]. Let me just write it inline:

```python
def checks():
    embs4 = torch.zeros(4, _EMB_DIM)
    tok4 = {i: t for i, t in enumerate(_TOKENS[:4])}
    return [
        ("no-images", lambda: (_GEN, "q", embs4, tok4, [], [])),
        ("no-tokens", lambda: (_GEN, "q", torch.zeros(0, _EMB_DIM), {}, [_IMG["a"]], [{}])),
        ("empty-query", lambda: (_GEN, "", torch.zeros(0, _EMB_DIM), {}, [], [])),
    ]
```

Hmm, `torch.zeros(0, _EMB_DIM)` — shape (0,128). In `_prepare_similarity_map_tensor`, `query_embs.shape[0]` = 0 → tensor shape (1, 0, 32, 32). Then `normalize_similarity_map(tensor.flatten(0,1))` → shape (0, 32, 32). The colpali_engine function might raise on empty. That's OK for checks.

Hmm, but "These may raise." Fine.

Actually, maybe safer for checks to not raise in weird ways that differ... they said may raise. OK.

Let me reconsider "no-images": images=[], vespa_sim_maps=[]. `_prepare_similarity_map_tensor` → tensor shape (0, 4, 32, 32). `normalize_similarity_map` on (0, 32, 32) → might raise (min on empty dim). Then the generator raises on first next(). If the harness materializes, it raises. That's fine for checks.

Hmm, but actually if it raises during iteration, does the harness consider it "identical behaviour"? They compare original vs modified — both raise the same exception presumably. Should be fine.

Actually, hmm, `normalize_similarity_map` in colpali_engine:

```python
def normalize_similarity_map(similarity_map: torch.Tensor) -> torch.Tensor:
    if similarity_map.ndim != 3:
        raise ValueError("The input tensor must have 3 dimensions...")
    ...
```

With shape (0,32,32), ndim=3 OK. Then min over dims -1,-2 of an empty tensor... `tensor.min(dim=-1)` on a (0,32,32) tensor gives shape (0,32) — works. So no raise; result shape (0,32,32). Then reshape to (0,4,32,32). Then loop over 0 images → no yields. So "no-images" yields nothing. Fine.

"no-tokens": images=[a], vespa_sim_maps=[{}]. tensor shape (1, 0, 32, 32). flatten(0,1) → (0, 32, 32). normalize → fine. reshape → (1,0,32,32). Loop over 1 image, token_idx_map empty → no yields. Fine.

"empty-query": images=[], vespa=[]. Same as no-images.

Hmm, these all yield nothing. That's fine for checks.

Maybe add one check with an odd type: e.g., images containing a nonexistent path → raises FileNotFoundError. Let's add:

```python
("missing-file", lambda: (_GEN, "q", embs4, tok4, [WORKDIR / "does_not_exist.png"], [{}])),
```

That would raise when `_load_image` opens it. Good edge case.

Let's include 3 checks: no-images, no-tokens, missing-file.

Hmm, "2 or 3 small edge inputs (empty, one element, None, an odd type)". OK.

Now let me finalize the token list and write everything.

One more thought on `_build_case` for the "negative" case: use low=-1.0, high=1.0.

Also diversity: maybe one case with very large values (scale 1e3) to test normalization. Let's make case 5 (large-image) use low=0, high=1000? Hmm, normalization handles it. Let's use one case with values in [-1,1] and another with large range.

Let me assign:
- C1: uniform(0,1)
- C2: uniform(0,1)
- C3: uniform(0,1)
- C4: uniform(-0.5, 0.5)
- C5: uniform(0, 1000)  (large range)
- C6: uniform(0,1)
- C7: uniform(-1, 1)
- C8: uniform(0,1)

Hmm, but wait: `normalize_similarity_map` does min-max per map, so the range doesn't matter much for output. But it does affect the numerics slightly. Fine.

Actually, careful: if a map is constant (max == min), the normalization divides by (max-min+1e-6) → 0. Our random maps are never constant. Fine.

Now, one more risk: `_blend_image` might call `self.colormap(sim_map)` where sim_map is normalized [0,1]. Fine.

Let me now write the final code.

Actually, one more thought about `_load_image` and Path: if `_load_image` does `if isinstance(img, str): ... else: Image.open(img)`, Path works. If it does `Image.open(img)` for everything, Path works. Good.

But what if it does `img.startswith(...)` on a Path → AttributeError. Hmm. The type hint says `Union[Path, str]`, so Path must be handled. In main.py, `img_paths` are strings from `os.path.join`? Let's check: main.py line 281 passes `images=img_paths`. And earlier `if not all([os.path.exists(img_path) for img_path in img_paths])`. So they're strings (paths). So the repo passes strings that are paths.

Hmm! So maybe `_load_image` is:

```python
    def _load_image(self, img):
        if isinstance(img, str):
            if img.startswith("data:image") or len(img) > 500:
                # base64
                ...
            return Image.open(img)
        return Image.open(img)
```

Hmm. To be safest, should I pass strings (paths) since that's what the repo does? The repo passes `img_paths` which are... let's see, in main.py they probably come from the Vespa response or from a directory listing. `os.path.join(SIM_MAP_DIR, ...)`. Actually `img_paths` likely come from `IMAGE_DIR / f"{query_id}_{i}.png"` or similar.

Hmm, given the repo passes strings, and `_load_image`'s docstring mentions base64 strings too, the function must distinguish. A common implementation:

```python
    def _load_image(self, img):
        if isinstance(img, Path):
            return Image.open(img)
        if os.path.exists(img):
            return Image.open(img)
        return Image.open(BytesIO(base64.b64decode(img)))
```

or

```python
        try:
            return Image.open(img)
        except (OSError, ValueError):
            return Image.open(BytesIO(base64.b64decode(img)))
```

Hmm. Passing a Path is the most unambiguous. I'll pass Path objects. If `_load_image` checks `isinstance(img, str)` first and then falls through to `Image.open(img)`, Path works.

Actually, hmm, what if it's:
```python
    def _load_image(self, img):
        if isinstance(img, str) and not os.path.exists(img):
            img = base64.b64decode(img)
        return Image.open(img)
```
Path works.

I'm fairly confident Path works. But to hedge, I could pass strings that are absolute paths — since `os.path.exists` would be True, it'd open as a file. But if the check is `isinstance(img, str)` → treat as base64, then a path string would fail to decode... Actually `base64.b64decode("/tmp/...")` might not raise (it ignores invalid chars) but would produce garbage → Image.open fails.

Hmm. Which is riskier? The repo passes path strings, so string paths must work. And Path is in the type hint. Both should work. I'll go with Path since the type hint explicitly lists it... 

Hmm, actually wait. Let me reconsider: the type hint is `List[Union[Path, str]]`. If the repo always passes strings, why include Path? Maybe because `_load_image` was written to accept both. I'll use Path.

Hmm, but actually — risk assessment. If `_load_image` is:

```python
    def _load_image(self, img):
        if isinstance(img, Path):
            img = str(img)
        if os.path.exists(img):
            return Image.open(img)
        ...
```

Both work.

OK, Path it is.

Hmm, hold on, let me reconsider once more. There's a real possibility the implementation is:

```python
    def _load_image(self, img: Union[Path, str]) -> Image:
        if isinstance(img, Path):
            return Image.open(img)
        # Otherwise, assume base64
        return Image.open(BytesIO(base64.b64decode(img)))
```

In this case, string paths would NOT work... but the repo passes string paths! Contradiction. Unless main.py converts to Path. Let me re-read: `images=img_paths` and `os.path.exists(img_path)`. `os.path.exists` works with both str and Path. Hmm.

Hmm, maybe img_paths are Paths. `os.path.exists` accepts Path. So can't tell.

OK whatever. Path is safe in both interpretations except the weird "isinstance(str) → base64" one, which would break the repo's own usage if img_paths were strings. So Path is safe.

Actually no — if the implementation is `if isinstance(img, str): base64` and the repo passes strings... that would break the repo. So either the repo passes Paths, or the implementation handles string paths. Either way, Path works. 

Now let me write it all out.

Let me also double check `_prepare_similarity_map_tensor` might use `self.n_patch` — we set it. Good. Might use `self.device`? We set "cpu". Fine.

Let me write the code.

```python
import logging
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator


_N_PATCH = 32
_EMB_DIM = 128


# ---------------------------------------------------------------- images ----
_IMAGE_SPECS = {
    "a": (200, 260, 1),
    "b": (200, 260, 2),
    "c": (260, 340, 3),
    "d": (320, 420, 4),
    "e": (400, 520, 5),
    "f": (480, 640, 6),
    "g": (640, 800, 7),
    "h": (300, 900, 8),
    "i": (256, 256, 9),
}

_IMG = {}


def _build_images():
    for name, (w, h, seed) in _IMAGE_SPECS.items():
        path = WORKDIR / f"simmap_img_{name}.png"
        rng = np.random.default_rng(seed)
        arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        Image.fromarray(arr, "RGB").save(path, format="PNG")
        _IMG[name] = path


_build_images()
```

Then the generator instance, tokens, builder, cases, checks.

Let me write the whole thing now.

For the query strings, use realistic ones.

Final check on lambda syntax: `lambda: (_GEN, "text", *_C1)` — the `*` unpacking in a tuple display inside a lambda body. Valid.

Let me write it.

Also note: the thunk returns the args tuple; the harness calls `SimMapGenerator.gen_similarity_maps(*args)`. So the first element must be the instance. ✓

Let me write out.

One last thing: should I worry that `_GEN` created at module level with `__new__` might be considered "faking"? I'll add a comment explaining why. Actually comments are fine.

Let me produce the final code.

def _build_case(image_names, tokens, seed, low=0.0, high=1.0):
    n_tokens = len(tokens)
    gen = torch.Generator().manual_seed(seed)
    query_embs = torch.randn(n_tokens, _EMB_DIM, generator=gen)
    token_idx_map = {i: t for i, t in enumerate(tokens)}
    rng = np.random.default_rng(seed + 7919)
    vespa_sim_maps = []
    for _ in image_names:
        sim_map = {}
        for i in range(n_tokens):
            sim_map[i] = rng.uniform(low, high, size=(_N_PATCH, _N_PATCH)).tolist()
        vespa_sim_maps.append(sim_map)
    images = [_IMG[name] for name in image_names]
    return query_embs, token_idx_map, images, vespa_sim_maps

Good.

Now cases. Let me name the case data variables.

_C1 = _build_case(["d"], _TOKENS[0:10], 101)
_C2 = _build_case(["f"], _TOKENS[10:20], 102)
_C3 = _build_case(["a", "b", "c"], _TOKENS[20:28], 103)
_C4 = _build_case(["c"], _TOKENS[0:24], 104, low=-0.5, high=0.5)
_C5 = _build_case(["g"], _TOKENS[30:34], 105, low=0.0, high=1000.0)
_C6 = _build_case(["d", "e"], _TOKENS_FILTER_HEAVY, 106)
_C7 = _build_case(["a", "b", "i", "c"], _TOKENS[36:42], 107, low=-1.0, high=1.0)
_C8 = _build_case(["h"], _TOKENS[42:48], 108)

Queries:
1. "What is the total revenue for Q3 2023?"
2. "How much did revenue grow compared to last year?"
3. "What was the profit margin in Norwegian kroner?"
4. "What is the total revenue for Q3 2023?"
5. "Was the profit higher than expected by analysts?"
6. "What is the total profit in 2023?"
7. "What data did the company report today?"
8. "How much did the shares rise in Oslo?"

Fine.

Now write it all.

Wait, one concern about `torch.randn(n, dim, generator=gen)` — the `generator` kwarg requires torch >= 1.6 or so. Fine.

Also `torch.Generator().manual_seed(seed)` — fine.

Let me write the final answer.

Actually, let me reconsider the total work once more. The harness keeps the 4 heaviest of the 8. If all 8 are in the 50-200ms range, good. My estimates: C1 ~8×10=80ms, C2 ~7×22=154ms, C3 ~21×6=126ms, C4 ~19×8=152ms, C5 ~4×35=140ms, C6 ~10×15=150ms, C7 ~24×5=120ms, C8 ~5×25=125ms. All comfortably in range. Good.

Hmm, but if PNG encoding is slower than I think (say 3x), C2 would be 450ms — still under 1s. And the setup (building images) ~1-3s. OK.

Actually, wait: setup time includes building all the vespa_sim_maps: total tensors = sum over cases of n_images*n_tokens*1024 floats. C1: 1*10*1024=10k. C2: 10k. C3: 3*8*1024=24k. C4: 24k. C5: 4k. C6: 2*18*1024=36k. C7: 4*6*1024=24k. C8: 6*1024=6k. Total ~140k floats. Trivial.

And image building: 1.7M pixels noise → PNG encode. Maybe 2s total. Fine.

OK, writing.

Actually one more: `rng.uniform(low, high, size=(32,32)).tolist()` — numpy float64 → Python floats. `torch.tensor(list_of_lists_of_floats)` → float64 tensor. Then `sim_map_tensor[img_idx, token_idx] = <float64 tensor>` where sim_map_tensor is float32 → assignment casts. Fine.

Hmm, but if `_prepare_similarity_map_tensor` creates the tensor as float32 and assigns float64, torch handles the cast. Fine.

But what if it does `torch.tensor(token_sim_map)` and then `torch.cat`? Fine.

OK.

Let me also consider: should the values be float32-representable? `.tolist()` gives float64; torch converts. Fine.

Write it.

Also, I should double-check: `_TOKENS_FILTER_HEAVY` contains "▁" multiple times. In a dict keyed by index, that's fine.

Final code:

```python
import logging

import numpy as np
import torch
from PIL import Image

from backend.colpali import SimMapGenerator
```

Note: we don't need `Path` import since WORKDIR is a Path and we use `/`. Actually we don't reference Path. Fine, drop it.

Let me write it out fully now.