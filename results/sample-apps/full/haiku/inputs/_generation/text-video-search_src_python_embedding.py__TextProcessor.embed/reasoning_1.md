The function uses CLIP model loading. `clip.load(model_name)` downloads model weights from network. That's a problem — no network access. Let me think.

`TextProcessor.__init__` calls `clip.load(model_name)` which downloads from OpenAI's CDN. Without network, this can't run. But maybe the model is cached locally? We can't rely on that.

Hmm, but the task says "A function whose work starts with a request to a server cannot run here". Here the function under test is `embed`, but the instance construction needs `clip.load` which downloads.

Actually, wait. Could we construct the TextProcessor without calling __init__? We could use `TextProcessor.__new__(TextProcessor)` and set `self.model` manually. But that would be "replacing code"? Setting object fields to build an input is fine: "Setting data (a module's configuration, an object's fields) to build an input is fine."

But we'd need a real CLIP model. We could build a fake model... but that would be mocking. Hmm.

Actually, could we create a real CLIP model without downloading? `clip.load` needs the checkpoint. Building a CLIP model from scratch requires the weights.

Alternatively, we could check if the model is already cached. But we can't know.

Hmm, this is tricky. Let me think about what's realistic here. The environment likely doesn't have network. `clip.load("ViT-B/32")` downloads ~350MB from openaipublic.azureedge.net.

Actually, maybe the grading environment has the model cached or network. But the instruction says no network access.

Let me reconsider. The safest approach: try to make it work. But if it can't, we should reply CANNOT RUN.

Actually, wait — the function under test is `embed`, which itself does `clip.tokenize(text)` and `self.model.encode_text(...)`. The `self.model` is a CLIP model. To build a real CLIP model we need weights.

Could we construct a CLIP model with random weights using `clip.build_model`? Yes! `clip.build_model(state_dict)` builds the model architecture from a state dict. We could create a state dict with random tensors matching the architecture... but that requires knowing the exact keys/shapes.

Actually, `clip.build_model` takes a state_dict and infers the architecture from keys. We could build a smaller architecture. Hmm, but that's basically substituting a model.

Hmm, but is that "mocking"? It's a real CLIP model with random weights. The function would run. But the output would be meaningless. The task says compare original vs modified outputs — as long as both run the same, it's fine.

But building the state dict requires knowing the model structure. Let me recall CLIP's `build_model`:

```python
def build_model(state_dict: dict):
    vit = "visual.proj" in state_dict
    if vit:
        vision_width = state_dict["visual.conv1.weight"].shape[0]
        vision_layers = len([k for k in state_dict.keys() if k.startswith("visual.") and k.endswith(".attn.in_proj_weight")])
        vision_patch_size = state_dict["visual.conv1.weight"].shape[-1]
        grid_size = round((state_dict["visual.positional_embedding"].shape[0] - 1) ** 0.5)
        image_resolution = vision_patch_size * grid_size
    else:
        counts: list = [len(set(k.split(".")[2] for k in state_dict if k.startswith(f"visual.layer{b}"))) for b in [1, 2, 3, 4]]
        ...
    ...
```

This is complex but doable. Actually, we only need the text encoder since `embed` calls `encode_text`. But `clip.load` builds the full model.

Wait, actually `build_model` requires both visual and text parts? Let me recall. It checks `vit = "visual.proj" in state_dict`. If not vit, it uses ResNet. Then it builds both. Actually the whole model is built.

Hmm, but we don't need to call `clip.load`. We can build the model ourselves with `clip.build_model` and set `instance.model` directly. That avoids downloading.

Let me construct a minimal CLIP state_dict. Actually, this is quite involved. Let me think about the text transformer architecture.

CLIP text encoder (Transformer):
- `token_embedding.weight`: [vocab_size, width]
- `positional_embedding`: [context_length, width]
- `ln_final.weight`, `ln_final.bias`: [width]
- `text_projection`: [width, embed_dim]
- per layer: `transformer.resblocks.{i}.ln_1.weight/bias`, `.attn.in_proj_weight` [3*width, width], `.attn.in_proj_bias` [3*width], `.attn.out_proj.weight/bias`, `.ln_2.weight/bias`, `.mlp.c_fc.weight/bias`, `.mlp.c_proj.weight/bias`

And visual:
- `visual.conv1.weight`: [width, 3, patch, patch]
- `visual.class_embedding`: [width]
- `visual.positional_embedding`: [num_pos, width]
- `visual.ln_pre.weight/bias`
- `visual.transformer.resblocks.{i}...`
- `visual.ln_post.weight/bias`
- `visual.proj`: [width, embed_dim]

build_model:
```python
def build_model(state_dict: dict):
    vit = "visual.proj" in state_dict

    if vit:
        vision_width = state_dict["visual.conv1.weight"].shape[0]
        vision_layers = len([k for k in state_dict.keys() if k.startswith("visual.") and k.endswith(".attn.in_proj_weight")])
        vision_patch_size = state_dict["visual.conv1.weight"].shape[-1]
        grid_size = round((state_dict["visual.positional_embedding"].shape[0] - 1) ** 0.5)
        image_resolution = vision_patch_size * grid_size
    else:
        counts: list = [len(set(k.split(".")[2] for k in state_dict if k.startswith(f"visual.layer{b}"))) for b in [1, 2, 3, 4]]
        vision_layers = tuple(counts)
        vision_width = state_dict["visual.layer1.0.conv1.weight"].shape[0]
        output_width = round((state_dict["visual.attnpool.positional_embedding"].shape[0] - 1) ** 0.5)
        vision_patch_size = None
        assert output_width ** 2 + 1 == state_dict["visual.attnpool.positional_embedding"].shape[0]
        image_resolution = output_width * 32

    embed_dim = state_dict["text_projection"].shape[1]
    context_length = state_dict["positional_embedding"].shape[0]
    vocab_size = state_dict["token_embedding.weight"].shape[0]
    transformer_width = state_dict["ln_final.weight"].shape[0]
    transformer_heads = transformer_width // 64
    transformer_layers = len(set(k.split(".")[2] for k in state_dict if k.startswith(f"transformer.resblocks")))

    model = CLIP(
        embed_dim,
        image_resolution, vision_layers, vision_width, vision_patch_size,
        context_length, vocab_size, transformer_width, transformer_heads, transformer_layers
    )

    for key in ["input_resolution", "context_length", "vocab_size"]:
        if key in state_dict:
            del state_dict[key]

    convert_weights(model)
    model.load_state_dict(state_dict)
    return model.eval()
```

So we need a full state dict. This is doable but tedious. Also `convert_weights` converts to half precision.

Hmm, this is a lot of work and risky. Let me reconsider whether the environment might actually have the model cached or network.

The task explicitly says: "no network access, no subprocesses". And "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here". The embed function itself doesn't make a request, but building the TextProcessor does via clip.load.

Hmm. But we can build the instance without __init__. The question is whether that's acceptable. The guidance says "Setting data (a module's configuration, an object's fields) to build an input is fine." And "no subclass that overrides a method" — we're not subclassing.

But we'd need a real CLIP model. Building one with random weights via `clip.build_model` — is that a mock? It's a real CLIP model object, just with random weights. I think that's borderline but arguably fine since it's a genuine model instance.

Actually, hmm, but there's a subtlety: `clip.tokenize` uses the BPE vocab file which is bundled with the clip package (bpe_simple_vocab_16e6.txt.gz). That's local, fine.

Let me think about whether building the model is feasible. Actually, maybe simpler: can we get the CLIP model architecture with random weights? We need to construct the state dict with correct shapes.

Actually, an easier approach: use `clip.build_model` with a hand-crafted state dict for a tiny CLIP model. But the shapes must be consistent and the forward pass must work.

Let me design a tiny ViT-B style model:
- embed_dim = 512
- vision_width = 768, vision_layers = 12, vision_patch_size = 32, image_resolution = 224
- context_length = 77, vocab_size = 49408, transformer_width = 512, transformer_heads = 8, transformer_layers = 12

That's the full ViT-B/32. Building random weights for that is ~150M params, fine memory-wise (~600MB in float32... hmm, actually ViT-B/32 CLIP is ~151M params, float32 = 600MB). That might exceed 100MB limit for inputs. But the model isn't an "input" per se... Actually the guidance about 100MB is about input data. Hmm.

We could use a smaller model. Let's use a tiny one:
- embed_dim = 32
- vision_width = 32, vision_layers = 2, vision_patch_size = 32, image_resolution = 64 (grid_size 2)
- context_length = 77, vocab_size = 49408, transformer_width = 32, transformer_heads = 1 (32//64 = 0! problem)

transformer_heads = transformer_width // 64. So transformer_width must be >= 64. Let's use transformer_width = 64, heads = 1.

Hmm wait, but heads must divide width. 64//64 = 1, ok.

Actually let me reconsider: is this too clever/risky? The task says "simple inputs that run are better than clever ones that do not."

Alternative: Maybe the grading environment actually does have network or a cached model. But I shouldn't rely on it.

Hmm, let me reconsider the whole thing. The instructions say if the function cannot run here, reply CANNOT RUN. But here the function CAN run if we build the model ourselves. The question is whether building a model without clip.load counts as legitimate.

I think the cleanest legitimate approach that actually runs: build a real CLIP model via `clip.build_model` with random weights, set it on the instance created via `__new__`. This is "setting an object's field to build an input" and using the repository's own library (clip) to construct a genuine model.

Hmm, but actually... is `clip.load` the only way? Let me reconsider. There might be a way to make clip.load work offline if we provide a checkpoint file. `clip.load` signature: `clip.load(name, device=..., jit=False, download_root=...)`. It calls `_download(url, download_root, ...)` which checks if the file exists in download_root. If we put a valid checkpoint at the expected path, it would load without network!

The expected filename: for "ViT-B/32", `_MODELS["ViT-B/32"]` = "https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt". The download filename is `os.path.basename(url)` = "ViT-B-32.pt". And download_root defaults to `os.path.expanduser("~/.cache/clip")`.

But we can't control the default download_root unless we set it... `clip.load` doesn't take download_root from a global. Actually we could create the file at `~/.cache/clip/ViT-B-32.pt`. But writing to home dir... The task says files must go under WORKDIR. Hmm. And we'd need to produce a valid checkpoint file, which is exactly the state dict we'd build anyway.

Actually `_download`:
```python
def _download(url: str, root: str, in_memory: bool) -> Union[bytes, str]:
    os.makedirs(root, exist_ok=True)
    filename = os.path.basename(url)
    download_target = os.path.join(root, filename)
    if os.path.exists(download_target) and not os.path.isfile(download_target):
        raise RuntimeError(f"{download_target} exists and is not a regular file")
    if os.path.isfile(download_target):
        ...
        return download_target
    ...
```

So if we write a torch.save'd state dict to `~/.cache/clip/ViT-B-32.pt`, clip.load will load it locally. But it would need to be a proper state dict for the full ViT-B/32 architecture (since clip.load calls build_model on it). We could save a tiny model's state dict and it would build a tiny model — but then `self.model_name = model_name` and the model would be tiny. That works!

But writing to `~/.cache/clip` violates "Anything the function writes must go under WORKDIR" — but we're writing the input, not the function. Hmm, "Files: if the function reads files, create them under WORKDIR". clip.load reads the checkpoint. So it should be under WORKDIR. But clip.load's download_root defaults to ~/.cache/clip. We can't change that for the TextProcessor.__init__ call... unless we set it.

Hmm, actually we could monkeypatch... no, not allowed.

OK so option: create instance via `__new__` and set `self.model` to a model built by `clip.build_model` from random weights. This avoids all file issues.

But `clip.build_model` requires a state dict with visual keys (vit detection). Let's just build a full tiny model.

Wait, actually, could we avoid build_model and construct the CLIP model directly? `clip.model.CLIP(...)` is public-ish. `clip.clip.CLIP`? Actually `CLIP` class is in `clip.model`. We can do `from clip.model import CLIP`. Then construct with args and random init. Then `model.eval()`. That's simpler than build_model!

But `encode_text` requires the text transformer. CLIP's __init__ builds both visual and text. Let's just construct with small dims.

Let me recall CLIP.__init__:
```python
class CLIP(nn.Module):
    def __init__(self,
                 embed_dim: int,
                 # vision
                 image_resolution: int,
                 vision_layers: Union[Tuple[int, int, int, int], int],
                 vision_width: int,
                 vision_patch_size: int,
                 # text
                 context_length: int,
                 vocab_size: int,
                 transformer_width: int,
                 transformer_heads: int,
                 transformer_layers: int
                 ):
        super().__init__()
        self.context_length = context_length

        if isinstance(vision_layers, (tuple, list)):
            vision_heads = vision_width * 32 // 64
            self.visual = ModifiedResNet(...)
        else:
            vision_heads = vision_width // 64
            self.visual = VisionTransformer(
                input_resolution=image_resolution,
                patch_size=vision_patch_size,
                width=vision_width,
                layers=vision_layers,
                heads=vision_heads,
                output_dim=embed_dim
            )

        self.transformer = Transformer(
            width=transformer_width,
            layers=transformer_layers,
            heads=transformer_heads,
            attn_mask=self.build_attention_mask()
        )

        self.vocab_size = vocab_size
        self.token_embedding = nn.Embedding(vocab_size, transformer_width)
        self.positional_embedding = nn.Parameter(torch.empty(self.context_length, transformer_width))
        self.ln_final = LayerNorm(transformer_width)

        self.text_projection = nn.Parameter(torch.empty(transformer_width, embed_dim))
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

        self.initialize_parameters()

    def initialize_parameters(self):
        nn.init.normal_(self.token_embedding.weight, std=0.02)
        nn.init.normal_(self.positional_embedding, std=0.01)
        ...
```

So we can construct directly. 

Then `encode_text`:
```python
def encode_text(self, text):
    x = self.token_embedding(text).type(self.dtype)  # [batch_size, n_ctx, d_model]
    x = x + self.positional_embedding.type(self.dtype)
    x = x.permute(1, 0, 2)  # NLD -> LND
    x = self.transformer(x)
    x = x.permute(1, 0, 2)  # LND -> NLD
    x = self.ln_final(x).type(self.dtype)
    x = x[torch.arange(x.shape[0]), text.argmax(dim=-1)] @ self.text_projection
    return x
```

`self.dtype` — CLIP has a `dtype` property returning the dtype of the conv weight or token embedding. Fine.

`clip.tokenize(text)` returns a tensor of shape [1, 77] with int64. It uses `SimpleTokenizer` which needs the BPE vocab file bundled with clip. That should be present.

OK so plan:
```python
import torch
import clip
from clip.model import CLIP
from embedding import TextProcessor

def _make_model():
    model = CLIP(embed_dim=32, image_resolution=64, vision_layers=2, vision_width=64, vision_patch_size=32,
                 context_length=77, vocab_size=49408, transformer_width=64, transformer_heads=1, transformer_layers=2)
    model.eval()
    return model

_MODEL = _make_model()

def _instance():
    tp = TextProcessor.__new__(TextProcessor)
    tp.model = _MODEL
    tp.model_name = "ViT-B/32"
    return tp
```

Hmm wait, but `__new__` — is that "replacing code"? It's constructing an object without calling __init__. Setting fields. I think it's acceptable as "setting an object's fields to build an input".

Hmm, but honestly, this is quite hacky. Let me reconsider whether it's better to just try `clip.load` and see. No, we can't test.

Actually, wait. Let me reconsider. Is there a risk that `clip` package isn't installed? The task says "packages the repository already imports" — clip is imported. So it's available.

But hold on — does the environment have the CLIP model weights cached? If the grading harness expects the function to run and the reference solution... Hmm. Actually the task is generated automatically; the reference solution presumably also had to deal with this. Maybe they allow building the model.

Hmm, but actually, there's a real concern: maybe the environment DOES have network or cached weights and the intended solution is just `TextProcessor("ViT-B/32")`. But that's a 350MB download and slow.

I'll go with the build-model approach but make it robust: try clip.load first? No — deterministic is better.

Hmm, actually, let me reconsider once more. The concern with `__new__`: the guidance says "no subclass that overrides a method of a repository or library class". We're not subclassing. "Setting data ... an object's fields ... is fine." Creating via __new__ and setting fields is essentially setting fields. I'll go with it.

Actually, hmm, but is constructing a CLIP model with random weights "faking the environment"? It's not faking — it's a genuine CLIP model object. The function's real work (tokenize, encode_text, normalize) all happens for real.

Actually, let me reconsider: maybe better to use `clip.build_model` with a proper state dict so it's more "real". But direct construction is simpler and less error-prone. I'll use direct construction.

Wait, one more consideration: `transformer_heads = 1` with width 64. In Transformer, `resblocks` use MultiheadAttention(width, heads). heads=1, width=64, head_dim=64. Fine.

VisionTransformer with width=64, heads=64//64=1, layers=2, patch_size=32, input_resolution=64 → grid 2x2 = 4 patches + 1 class = 5 positional embeddings. Fine.

embed_dim=32. text_projection: [64, 32]. Fine.

Now, does `clip.tokenize` need anything special? It returns `torch.LongTensor`. The default context_length is 77. Good.

Now let's think about the actual cases. The function takes `text` (a string). Real usage: `text_processor.embed(query)` where query is a user search query. So realistic inputs are short text strings.

But the task wants "stressful inputs", 1ms-200ms. embed with a tiny model is fast. With the real ViT-B/32 model it'd be ~10ms on GPU or ~50ms on CPU. With our tiny model it's much faster, maybe <1ms. Hmm, that violates "roughly 1 ms to 200 ms".

Hmm. That's a problem. Our tiny model makes it too fast. We could use a bigger model to make it slower. But bigger model = more memory for building (fine, it's not input data).

Actually, wait — the "work" measured is the function call. If it's too fast, the measurement may be noisy. But the guidance says "roughly 1ms to 200ms". Let's aim for a model size that gives ~1-10ms.

Actually, the real ViT-B/32 text encoder has 12 layers, width 512. On CPU, encoding a single 77-token sequence takes maybe 10-20ms. Let's build a model closer to that: transformer_width=512, transformer_layers=12, heads=8, context_length=77, vocab_size=49408.

The token embedding is [49408, 512] = 25M params = 100MB float32. Hmm, that's a lot but it's the model, not input. Memory limit is for inputs. Still, building might take time. Actually 25M params random init ~ fast.

But total model: text transformer 12 layers × (4×512² attn + 2×512×2048 mlp) ≈ 12 × (1M + 2M) = 36M params. Plus vision. Fine.

Hmm, but the vision part with image_resolution 224 and patch 32 → 49 patches, width 768, 12 layers → ~86M params. That's big and unnecessary since we only use text. Let's make vision tiny: vision_width=64, vision_layers=1, vision_patch_size=32, image_resolution=32 → grid 1x1 = 1 patch + class = 2 positional. embed_dim must match text_projection output; text_projection is [transformer_width, embed_dim]. embed_dim can be small, say 512? Actually embed_dim is independent. Let's set embed_dim=512.

Wait, but `encode_text` computes `x @ self.text_projection` where x is [1, transformer_width] and text_projection is [transformer_width, embed_dim]. So output dim = embed_dim. The real ViT-B/32 has embed_dim=512. Let's use 512.

So:
- embed_dim=512
- vision_width=64, vision_layers=1, vision_patch_size=32, image_resolution=32
- context_length=77, vocab_size=49408, transformer_width=512, transformer_heads=8, transformer_layers=12

Token embedding [49408, 512] float32 = 101MB. Hmm. That's memory but not "input data". Should be OK but let's reduce vocab_size? No — tokenize produces token IDs up to 49407, so vocab_size must be ≥ 49408 for embedding lookup. Actually tokenize returns ids in [0, 49407]. So vocab_size must be 49408. OK.

Hmm, 101MB for token embedding. Plus overhead. Total maybe 150MB. The limit says "Keep the data in memory under about 100 MB" — that's about input data. The model is infrastructure. I think it's OK but let's be mindful.

Actually, we could reduce transformer_width to 256 → token embedding 50MB, 12 layers. Still decent work. Let's use transformer_width=256, heads=4, transformer_layers=12. Token embedding 49408×256×4 = 50MB. Good.

Hmm, will that give ~1ms+? 12 layers of width 256 on seq len 77 on CPU: each layer ~ 4×256²×77 + 2×256×1024×77 ≈ 20M + 40M = 60M FLOPs... times 12 = 720M FLOPs. On CPU maybe 10-50ms. Good enough.

Actually let's just go with width 512, 12 layers — more realistic and slower. Token embedding 100MB. Hmm, borderline. Let's compromise: width=384? Must be divisible by 64 for heads. 384/64=6 heads. Token embedding 49408×384×4 = 76MB. 12 layers. OK.

Actually, you know, let me not over-engineer. Let me use width=512, layers=12, heads=8 but reduce... no.

Hmm, actually the memory concern: the model params are float32. 49408×512 = 25.3M params × 4 bytes = 101MB. Plus 12 layers × ~3.7M = 44M params = 177MB... wait: per layer: attn in_proj 3×512×512=786k, out_proj 512×512=262k, mlp c_fc 512×2048=1.05M, c_proj 2048×512=1.05M → ~3.15M params/layer × 12 = 37.8M = 151MB. Total model ~250MB. Hmm, that's a lot but probably fine on a machine.

Let me reduce: width=256, heads=4, layers=6. Token embedding 49408×256×4=50MB. Per layer: 3×256²+256²+256×1024+1024×256 = 196k+65k+262k+262k = 786k ×6 = 4.7M = 19MB. Total ~70MB. Work: 6 layers × 256 width × 77 tokens... maybe 5-15ms. 

Hmm, but "stressful inputs" — with a small model the differences between inputs are minor. The main variation is text length and content.

Actually, let me reconsider. The real question: does the input text length matter? `clip.tokenize` always produces a 77-token sequence (padded). So the model work is constant regardless of text! So all inputs do the same amount of model work. The only variation is tokenization cost, which is tiny.

Hmm. That means all cases are basically identical in work. That's fine — we just need 8 diverse inputs. The "4 that do the most work" — they'll all be similar.

OK. So the cases vary in text content: short query, long text, unicode, many tokens, etc.

Let me now write the code.

Actually, wait. I realize there might be an issue with `clip.tokenize` — it truncates to context_length (77). So long text is truncated. Fine.

Also `clip.tokenize` uses `gzip` to read the bpe file. Fine.

Let me also consider: `self.model.encode_text(text_tokens)` — text_tokens is int64 tensor [1,77]. `self.model.dtype` — CLIP.dtype property:
```python
@property
def dtype(self):
    return self.visual.conv1.weight.dtype
```
VisionTransformer has conv1. Good, float32.

Now `text_features.tolist()[0]` returns a list of 512 floats. Under 100k values. Good.

Now checks(): 2-3 small edge inputs. E.g. empty string, single char, None (would raise). Actually None → clip.tokenize(None) raises. That's fine for checks.

Hmm, but checks must run on original and modified and compare — if it raises, both raise, fine.

Let me write:

```python
import random
import torch
import clip
from clip.model import CLIP
from embedding import TextProcessor

def _build_model():
    model = CLIP(
        embed_dim=512,
        image_resolution=32,
        vision_layers=1,
        vision_width=64,
        vision_patch_size=32,
        context_length=77,
        vocab_size=49408,
        transformer_width=512,
        transformer_heads=8,
        transformer_layers=12,
    )
    model.eval()
    return model

_MODEL = _build_model()
_PROCESSOR = TextProcessor.__new__(TextProcessor)
_PROCESSOR.model = _MODEL
_PROCESSOR.model_name = "ViT-B/32"
```

Wait — `TextProcessor.__new__(TextProcessor)` — TextProcessor inherits object, so __new__ works.

Hmm, but actually, is setting `_PROCESSOR.model` on a module-level object and reusing it across calls OK? The function doesn't mutate the model. Yes.

But the thunk must return the instance as first arg. Since the function doesn't mutate the instance, we can reuse. Good.

Now the texts. Let me generate realistic search queries and some long texts.

Actually, since model work is constant, all cases do ~same work. To differentiate, maybe vary... hmm. There's really not much variation. But that's fine.

Wait, actually — is there variation? `clip.tokenize` for a short text still pads to 77. The transformer processes all 77 tokens. So constant. Unless... the attention mask. CLIP's build_attention_mask creates a causal mask of size 77×77, always. So constant.

OK so all 8 cases do essentially the same work. The "4 that do the most work" selection will pick arbitrarily among near-equal. Fine.

Let me write diverse texts:
1. Short query: "a dog running in the park"
2. Longer sentence
3. Very long text (truncated)
4. Text with special chars / unicode
5. Text with many punctuation
6. Single word
7. Repeated words
8. Numbers/code-like

Let me use random.Random(0) for generating some.

Actually the guidance says use fixed seed when generating data. Let's do that for some generated texts.

Let me write:

```python
def _random_words(rng, n):
    vocab = ["dog", "cat", "running", "park", "video", "clip", "search", "frame",
             "sunset", "beach", "city", "night", "car", "tree", "mountain", "river",
             "person", "walking", "sky", "blue", "red", "green", "fast", "slow"]
    return " ".join(rng.choice(vocab) for _ in range(n))
```

Cases:
- "short-query": "a dog running in the park"
- "medium-sentence": a ~30 word sentence
- "long-text": 2000 words (truncated to 77 tokens)
- "unicode": text with accented chars, emoji
- "punctuation": lots of punctuation
- "single-word": "cat"
- "numbers": digits and symbols
- "random-words": generated

Let me now think about whether the model construction is fast enough at import. Building 12-layer 512-width model: ~200M params random init. That might take a few seconds. Under 10s hopefully.

Hmm, the guidance: "building all inputs under about 10 s". Model building is setup. Let's keep it reasonable.

Let me reduce to transformer_layers=8, width=512. Or keep 12. I'll do 12 layers, width 512 — realistic ViT-B text encoder size.

Actually, memory: 49408×512×4 = 101MB for token embedding alone. Plus 12 layers ~150MB. ~250MB. Probably fine but let me reduce a bit to be safe: width=384, heads=6, layers=12. Token emb 49408×384×4=76MB. Layers: per layer 3×384²+384²+384×1536+1536×384 = 442k+147k+590k+590k=1.77M ×12=21M=85MB. Total ~165MB. OK.

Hmm, but heads = 384//64 = 6. Good.

Actually, let me just use width=512, heads=8, layers=12, and accept ~250MB. It's a model, not input data. Most machines have GBs.

Hmm, the instruction "Keep the data in memory under about 100 MB" — I'll interpret as input data. The model is unavoidable infrastructure.

Hmm, but to be safe, maybe width=256, heads=4, layers=12. Token emb 50MB, layers 12×(3×256²+256²+256×1024+1024×256)=12×(196k+65k+262k+262k)=12×785k=9.4M=38MB. Total ~90MB. And work is still decent.

Actually the timing: with width 256 and 12 layers, seq 77, the compute is ~12 × (4×256²×77 + 2×256×1024×77) ≈ 12 × (20M + 40M) = 720M MACs = 1.4 GFLOPs. On CPU ~50-200ms? Hmm, maybe. Actually torch on CPU with small matrices... could be around 10-30ms. Good range.

Let me go with width=256, heads=4, layers=12, embed_dim=512.

Wait, embed_dim=512 but transformer_width=256, text_projection [256, 512]. Output 512-dim. Realistic. Good.

Hmm, actually let me reconsider: the real model outputs 512-dim for ViT-B/32. Good.

Now, one concern: `CLIP.__init__` calls `self.build_attention_mask()` which uses `self.context_length`. Fine.

Another: `initialize_parameters` uses `nn.init.normal_` etc. Fine.

Another: VisionTransformer with input_resolution=32, patch_size=32 → grid_size=1, num_positions=1+1=2. conv1: Conv2d(3, 64, 32, 32). Fine. width=64, heads=64//64=1. layers=1.

Wait, VisionTransformer heads = vision_width // 64 = 64//64 = 1. Good.

Now `CLIP.__init__` computes `vision_heads = vision_width // 64`. Good.

Alright.

Let me also double check `clip.tokenize` signature: `clip.tokenize(text, context_length=77, truncate=False)`. Returns tensor. It calls `_tokenizer.encode(text)` then `_tokenizer.encode("<|endoftext|>")`. For a single string it returns [1, 77].

Actually `tokenize`:
```python
def tokenize(texts, context_length=77, truncate=False):
    if isinstance(texts, str):
        texts = [texts]
    sot_token = _tokenizer.encoder["<|startoftext|>"]
    eot_token = _tokenizer.encoder["<|endoftext|>"]
    all_tokens = [[sot_token] + _tokenizer.encode(text) + [eot_token] for text in texts]
    result = torch.zeros(len(all_tokens), context_length, dtype=torch.long)
    for i, tokens in enumerate(all_tokens):
        if len(tokens) > context_length:
            if truncate:
                tokens = tokens[:context_length]
                tokens[-1] = eot_token
            else:
                raise RuntimeError(...)
        result[i, :len(tokens)] = torch.tensor(tokens)
    return result
```

Important: if text is too long and truncate=False, it RAISES RuntimeError! So long texts will raise. So our "long text" case must not exceed 77 tokens... or the function will raise, which is not allowed for cases ("Every case must run to completion on the original function without raising").

So long text cases must be ≤ 76 tokens (plus sot/eot = 77 max... actually tokens = 1 + len(encode) + 1 ≤ 77 → len(encode) ≤ 75).

So I need to keep texts short enough. Let's cap at ~70 words max. Hmm, but words get split into subwords. Common English words are 1 token. Let's keep long text to ~50 words to be safe.

Actually, let me be careful. Let me generate texts and check token count... but I can't run. Safer: keep texts to ≤ 40 words. Or use `clip.tokenize` inside the thunk to verify? No, the thunk returns args; we could compute token length there but it's part of setup (not timed) — actually we could just build texts that are safe.

Hmm, but a "stressful" input would be near the 77-token limit. Let's aim for texts around 60-70 tokens. To be safe, I'll generate from a known word list where each word is one token, and keep count ≤ 70.

Common single-token words: "dog", "cat", "the", "a", "running", "park", etc. Most simple lowercase words are single tokens in CLIP BPE. But some might split. Risky.

Alternative: use `clip.tokenize` in the thunk to validate and pad. But if it raises during thunk... the thunk runs before timing, and an exception in the thunk would fail the case. Hmm, but actually the thunk is called to get args; if it raises, the case fails.

Better: in module-level code, generate candidate texts and filter to those with token count ≤ 75 using clip.tokenize. That's setup, fine.

Let me do that: build a pool of texts, filter by token length.

Actually simpler: I'll just use `clip.tokenize` at module level to check and truncate the text to a safe length. But truncating text by words... Let me just do:

```python
def _safe_text(words):
    text = " ".join(words)
    while len(clip.tokenize(text, truncate=True)[0]) ... 
```

Hmm, `clip.tokenize(text, truncate=True)` won't raise but returns 77 tokens always. Not helpful for counting.

Let me directly use the tokenizer: `clip.tokenize` internal `_tokenizer`. Not public. Hmm.

Alternative approach: build text word by word, checking `clip.tokenize` doesn't raise:
```python
def _build_text(words):
    text = ""
    for w in words:
        candidate = (text + " " + w).strip()
        try:
            clip.tokenize(candidate)  # raises if too long
            text = candidate
        except RuntimeError:
            break
    return text
```
This is O(n) tokenize calls at setup — fine.

That guarantees the text tokenizes without raising. 

Now, all cases will produce ≤77 tokens, all doing the same model work. Fine.

Let me now write the final code.

```python
import random

import torch
import clip
from clip.model import CLIP

from embedding import TextProcessor


def _build_model():
    model = CLIP(
        embed_dim=512,
        image_resolution=32,
        vision_layers=1,
        vision_width=64,
        vision_patch_size=32,
        context_length=77,
        vocab_size=49408,
        transformer_width=256,
        transformer_heads=4,
        transformer_layers=12,
    )
    model.eval()
    return model


_MODEL = _build_model()

_PROCESSOR = TextProcessor.__new__(TextProcessor)
_PROCESSOR.model = _MODEL
_PROCESSOR.model_name = "ViT-B/32"


def _fit(words):
    """Join words into the longest prefix that clip.tokenize accepts (<77 tokens)."""
    text = ""
    for word in words:
        candidate = (text + " " + word).strip()
        try:
            clip.tokenize(candidate)
        except RuntimeError:
            break
        text = candidate
    return text


_RNG = random.Random(0)

_VOCAB = ["dog", "cat", "running", "park", "video", "clip", "search", "frame",
          "sunset", "beach", "city", "night", "car", "tree", "mountain", "river",
          "person", "walking", "sky", "blue", "red", "green", "fast", "slow",
          "train", "bird", "water", "street", "house", "music", "dance", "food"]

_RANDOM_WORDS = _fit([_RNG.choice(_VOCAB) for _ in range(200)])
```

Hmm, `_fit` with 200 random words will stop at ~70. Good.

Now define the case texts:

```python
_TEXT_SHORT = "a dog running in the park"
_TEXT_MEDIUM = _fit("a group of people walking along a busy city street at night with bright neon signs and cars".split())
_TEXT_LONG = _fit([...])  # ~70 words
_TEXT_UNICODE = "café au lait à Paris, señor, naïve résumé, 日本語のテキスト, emoji 🐶🎬"
_TEXT_PUNCT = "Wait... what?! Really?? Yes -- no; maybe: 'quotes' (parens) [brackets] {braces} #hash @at &amp; 100%."
_TEXT_SINGLE = "cat"
_TEXT_NUMBERS = "video 2023 12 31 99.5 % $100 #42 3.14e10 0x1F"
_TEXT_REPEAT = "very " * 60  # hmm, "very very very..." might tokenize oddly
```

Careful with unicode: CLIP's BPE tokenizer might handle unicode by byte-encoding. Should be fine, might produce many tokens. `_fit` ensures safety. Let me wrap unicode in _fit too.

Actually `_fit` works on words split by space. For unicode text, splitting on space is fine.

Let me use _fit for all texts to be safe. For "cat", _fit(["cat"]) = "cat".

Hmm, but _fit on a text with punctuation — splitting on space keeps punctuation attached. Fine.

Let me restructure: define a helper `_mk(text)` that runs `_fit(text.split())`.

Now cases() returns 8:

```python
def cases():
    return [
        ("short-query", lambda: (_PROCESSOR, _TEXT_SHORT)),
        ("medium-sentence", lambda: (_PROCESSOR, _TEXT_MEDIUM)),
        ("long-caption", lambda: (_PROCESSOR, _TEXT_LONG)),
        ("random-words", lambda: (_PROCESSOR, _TEXT_RANDOM)),
        ("unicode", lambda: (_PROCESSOR, _TEXT_UNICODE)),
        ("punctuation", lambda: (_PROCESSOR, _TEXT_PUNCT)),
        ("single-word", lambda: (_PROCESSOR, _TEXT_SINGLE)),
        ("numbers-symbols", lambda: (_PROCESSOR, _TEXT_NUMBERS)),
    ]
```

checks():
```python
def checks():
    return [
        ("empty", lambda: (_PROCESSOR, "")),
        ("single-char", lambda: (_PROCESSOR, "a")),
        ("none", lambda: (_PROCESSOR, None)),
    ]
```

Wait, does empty string work? `clip.tokenize("")` → tokens = [sot, eot] = 2 tokens. Works. Output fine.

None → `clip.tokenize(None)`: `isinstance(None, str)` False, so `texts = [None]`... then `_tokenizer.encode(None)` → likely AttributeError/TypeError. Raises. Fine for checks.

Hmm, but wait — is `_PROCESSOR` reused across checks and cases? Yes, module-level. The function doesn't mutate it. Good.

Now, potential issue: `torch.no_grad()` — fine.

Another issue: the output `text_features.tolist()[0]` — 512 floats. Good.

Now, does the modified version of the function potentially produce different output? We compare outputs. Fine.

Let me double-check the CLIP constructor argument order:
```
CLIP(embed_dim, image_resolution, vision_layers, vision_width, vision_patch_size,
     context_length, vocab_size, transformer_width, transformer_heads, transformer_layers)
```
Yes.

Now, `from clip.model import CLIP` — is CLIP exported there? In the clip package, `clip/model.py` defines CLIP. Yes.

Also `clip.model` might import fine.

One more: `clip.__init__` imports `from .clip import *` which imports model. Fine.

Now about device: model is on CPU, text_tokens on CPU. Fine.

Potential issue: `self.model.dtype` — for CLIP, `dtype` property returns `self.visual.conv1.weight.dtype` = float32. And `encode_text` does `self.token_embedding(text).type(self.dtype)`. Fine.

Let me also double check `VisionTransformer.__init__` signature: (input_resolution, patch_size, width, layers, heads, output_dim). Yes.

And `Transformer(width, layers, heads, attn_mask)`. Yes.

Now, memory: token_embedding 49408×256×4 = 50.6MB. transformer 12 layers: per layer MultiheadAttention: in_proj_weight 3×256×256=196608, in_proj_bias 768, out_proj 256×256=65536+256; MLP: c_fc 256×1024=262144+1024, c_proj 1024×256=262144+256. Total ~787k params/layer ×12 = 9.4M ×4 = 37.8MB. Plus positional 77×256. Plus vision tiny. Total ~90MB. OK.

Now let me reconsider whether using `TextProcessor.__new__` might be considered "replacing code". The rule: "no subclass that overrides a method of a repository or library class". We're not doing that. "Setting data (a module's configuration, an object's fields) to build an input is fine." Creating an object and setting its fields is arguably fine.

Hmm, but is there a risk the harness checks that `TextProcessor.embed` is called on a properly constructed instance? No, it just calls the function with our args.

I'm fairly comfortable. But let me reconsider: is there a simpler legitimate path? What if `clip.load` actually works offline because the model is cached in the test environment? If the reference solution used `TextProcessor("ViT-B/32")`, then the environment must have network or cache. But we're told no network. And relying on cache is fragile.

I'll go with the __new__ approach. Actually... hmm, let me reconsider using `clip.build_model` instead, since that's the "official" way to build a model from a state dict, and it produces a model with `input_resolution`, `context_length`, `vocab_size` attributes. But direct CLIP construction is equivalent and simpler. Both are fine.

Hmm, one thought: maybe I should also try to make it work if `clip.load` is possible... no, keep it simple.

Actually, wait. Let me reconsider the risk that constructing CLIP directly fails due to some attribute needed. `encode_text` uses `self.token_embedding`, `self.positional_embedding`, `self.transformer`, `self.ln_final`, `self.text_projection`. All set in __init__. Good.

`self.dtype` uses `self.visual.conv1.weight`. VisionTransformer has `self.conv1`. Good.

OK. Also `clip.tokenize` is a module-level function. Good.

Let me also handle: `_fit` calls `clip.tokenize(candidate)` which for a very long candidate raises RuntimeError. Good. But it also might raise for other reasons. Fine.

Actually, potential performance: `_fit` on 200 words calls tokenize up to ~70 times. Each tokenize is fast. Fine.

Let me now also think: should the texts be more "diverse" in terms of work? Since work is constant, no. But diversity in token content is good for exercising the tokenizer.

Hmm, actually — wait. Is the work really constant? The transformer processes 77 tokens regardless. But attention mask is causal, all 77. Yes constant. The only variation: tokenizer time (negligible) and `.tolist()` (constant).

So the 4 "most work" will be essentially random. That's fine; the harness picks 4.

Hmm, but this makes the energy measurement dominated by constant model compute. That's actually good for a clean comparison.

Let me finalize.

One more consideration: the harness "runs the original function and a modified version". The modified version might be a refactored embed. Our inputs must be valid.

Also: "Its arguments are rendered before and after each call to see whether it changed them". Our args: the instance and a string. The function doesn't change them. Good. Rendering the instance — it's a TextProcessor with a nn.Module. Rendering might be expensive? "rendered" probably means repr. repr of the instance is default object repr. Fine. Actually, if they render the model... `repr(TextProcessor instance)` → `<embedding.TextProcessor object at 0x...>`. Fine.

Hmm, but wait — torch tensors in the model. repr of the instance doesn't include them. Good.

OK, writing final code.

Actually, let me reconsider the number of transformer layers for timing. If too fast (<1ms), measurement is noisy. Let me keep 12 layers, width 256. Should be several ms.

Hmm, let me estimate more carefully. A single forward pass of 12-layer transformer with d=256, seq=77, batch=1: FLOPs ≈ 12 × (attention: 4×d²×L + 2×L²×d) + MLP 2×d×4d×L. 
- 4×256²×77 = 20.2M
- 2×77²×256 = 3.0M
- MLP: 2×256×1024×77 = 40.4M
Total per layer ≈ 63.6M MACs. ×12 = 763M MACs ≈ 1.5 GFLOPs. CPU at ~10 GFLOPS → ~150ms. Hmm, that might be on the higher side but within 200ms. Actually torch CPU single-thread might be slower. Could be 100-300ms. Risky for the 1s limit? No, fine.

Actually, with batch=1 and small matrices, PyTorch overhead dominates; probably ~20-50ms. Good.

Let me keep it.

Hmm, but the token embedding lookup of 49408×256: negligible.

OK final.

Wait, actually one thing: `torch.no_grad()` and the model in eval mode — no dropout issues. Good. Even without eval, no dropout in CLIP. Fine.

Let me write it out.

Also need to make sure `embedding` module imports OK — it imports vespa, imageio, tenacity, etc. If those aren't installed... but the task says the repo imports them, so they're available. Actually `import embedding` triggers `from vespa.package import ...`. If vespa isn't installed, import fails. But the task says to import it as shown, so presumably it works.

Hmm, but actually the task's "Imports of its module" lists them; the environment must have them.

OK.

Let me write the final source.

```python
import random

import torch
import clip
from clip.model import CLIP

from embedding import TextProcessor


def _build_model():
    model = CLIP(
        embed_dim=512,
        image_resolution=32,
        vision_layers=1,
        vision_width=64,
        vision_patch_size=32,
        context_length=77,
        vocab_size=49408,
        transformer_width=256,
        transformer_heads=4,
        transformer_layers=12,
    )
    model.eval()
    return model


_MODEL = _build_model()

_PROCESSOR = TextProcessor.__new__(TextProcessor)
_PROCESSOR.model = _MODEL
_PROCESSOR.model_name = "ViT-B/32"


def _fit(text):
    words = text.split()
    out = ""
    for word in words:
        candidate = (out + " " + word).strip()
        try:
            clip.tokenize(candidate)
        except RuntimeError:
            break
        out = candidate
    return out


_RNG = random.Random(0)
_VOCAB = [...]
_TEXT_RANDOM = _fit(" ".join(_RNG.choice(_VOCAB) for _ in range(300)))
...
```

Let me define all texts.

_TEXT_SHORT = "a dog running in the park"
_TEXT_MEDIUM = _fit("a group of people walking along a busy city street at night with bright neon signs and a yellow taxi passing by")
_TEXT_LONG = _fit(" ".join(...)) — generate ~300 words from vocab, _fit truncates.
_TEXT_UNICODE = _fit("café au lait à Paris señor naïve résumé 日本語のテキスト emoji 🐶 🎬 naïve")
_TEXT_PUNCT = _fit("Wait ... what ?! Really ?? Yes -- no ; maybe : 'quotes' (parens) [brackets] {braces} #hash @at &amp; 100 % + - = / \\ |")
_TEXT_SINGLE = "cat"
_TEXT_NUMBERS = _fit("video 2023 12 31 99.5 % $100 #42 3.14e10 0x1F 1,000,000")

Hmm, careful: `_fit` with punctuation-only words might produce a candidate that tokenizes fine. OK.

For the unicode one, `_fit` splits on space; each chunk tokenized. Emoji might be multi-token. Fine.

Now, is there a risk `_fit` returns "" for some? For _TEXT_PUNCT starting with "Wait" it's fine.

Let me make sure _TEXT_RANDOM uses the RNG seeded. Good.

Let me finalize.

Actually, I realize I should double check: does `clip.tokenize` raise `RuntimeError` for too-long? Yes: `raise RuntimeError(f"Input is too long for context length {context_length}")`. Good.

But there's a subtlety: `_fit` builds incrementally; each candidate is checked. Good.

Final code below.

One more: I should ensure `torch` import isn't strictly needed but it's fine (clip imports torch anyway).

Let me write it.