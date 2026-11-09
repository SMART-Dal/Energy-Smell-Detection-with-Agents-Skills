The ffmpeg backend isn't available for writing. imageio needs ffmpeg to write mp4. We could try using a different writer, but likely no ffmpeg installed. Let me think about alternatives.

Actually the error says "Could not find a backend to open ... with iomo..." — iomo = imageio mode. So writing mp4 fails because ffmpeg plugin isn't installed.

We need real .mp4 files? Or can we use a different format that imageio can read? The function calls `imageio.get_reader(video_path, fps=1)`. The fps=1 parameter — for formats that don't support fps, imageio might raise or ignore. Actually fps is a plugin-specific kwarg. For example, the "pillow" plugin doesn't accept fps. Hmm.

Let's check what plugins are available. We can't run code, but we can reason: imageio typically ships with pillow plugin, maybe ffmpeg if installed. The error suggests ffmpeg isn't there for writing.

Options:
1. Write GIF using pillow plugin, then read with imageio.get_reader(path, fps=1)? GIF reader may accept fps? Actually imageio GIF reader (pillow) — the fps kwarg might be accepted by the format's reader. Let me recall: imageio's pillow plugin reader accepts `fps`? Looking at imageio source, the PillowPlugin.reader accepts `loop`, `fps`... Actually I recall `fps` is a parameter for the GIF reader in imageio. Yes! imageio's pillow GIF reader supports `fps` to control playback speed. Let me recall: `imageio.get_reader('foo.gif', fps=5)`. Hmm, in imageio v2 the GIF-PIL plugin reader has `fps` parameter. Yes, I'm fairly confident: the GIF plugin's reader accepts `fps` (it's used for timing). Actually in imageio the `fps` is a parameter used by the GIF reader to set duration.

Let me check: imageio/plugins/pillow.py — the `GIFPlugin` reader class `GifImageFile` has `fps` in `_open(self, loop=0, duration=None, fps=None)`. Hmm not sure.

Actually there's a known usage: `imageio.mimread('file.gif')`. And `imageio.get_reader('file.gif', 'gif', fps=...)`.

Alternatively, maybe ffmpeg IS available for reading but not writing? The error was on get_writer. Let's just try a different approach: use imageio's built-in ability to write... but if ffmpeg is missing entirely, we can't write mp4.

Wait — actually, maybe we can generate an mp4 without imageio using... no, we can't use subprocess.

Hmm. What about using the pillow plugin to write a GIF and then read it back? The reader needs to accept `fps=1` kwarg.

Let me think about imageio's pillow plugin more carefully. In imageio v2 (which this repo likely uses given `imageio.get_reader`), plugins include `pillow` with formats like PNG, JPEG, GIF, etc. The GIF reader: `class GifImageFile(PillowImageFile)`? Actually there's a legacy `imageio.plugins.pillow_legacy` and a newer `imageio.plugins.pillow`.

In `imageio/plugins/pillow.py` (newer), the `GIFPlugin` has `_open(self, loop=0, duration=None, fps=None)`. Hmm.

Actually I recall in imageio v2.9+, the pillow plugin's GIF reader signature is `_open(self, loop=0, duration=None, fps=None)`. Let me just trust that fps works for GIF.

But wait, the task says the function reads .mp4 via imageio. We just need files that imageio can read with fps=1. If GIF works, great.

But there's a risk: `imageio.get_reader(path, fps=1)` — the fps kwarg is passed to the plugin. For the pillow plugin reading a GIF, `fps` sets the frame duration. Should be fine.

Actually, let me reconsider. The error message mentions "iomo" which is imageio mode. The error is from `imageio.get_writer`. So writing mp4 needs ffmpeg. Let's check if ffmpeg is available for reading... we can't check.

Safer: try to write a GIF with the pillow plugin. But if pillow isn't installed either, we're stuck.

Hmm, but the repo imports torch, torchvision, clip, vespa... a heavy environment. imageio is there. Pillow likely there too (torchvision needs it).

Let me think about what plugin imageio uses for GIF. `imageio.get_writer('x.gif')` uses the pillow plugin. That should work without ffmpeg.

Then `imageio.get_reader('x.gif', fps=1)` — does the GIF reader accept fps? Let me recall imageio source:

```python
class PillowPlugin(Plugin):
    ...
```

And in `imageio/plugins/pillow.py`:
```python
class GIFPlugin(PillowPlugin):
    ...
```

Hmm, I'm not 100% sure. Let me think of an alternative that definitely works.

Alternative: use imageio's `imwrite` / `mimwrite` with a format that... no.

Another alternative: The reader could be given a directory? No.

What about writing a sequence of PNGs and reading them? No, get_reader takes a single file.

Hmm, what about using the "ffmpeg" plugin but the ffmpeg binary might actually be available... The error says it couldn't find a backend, so no.

Wait, actually maybe the issue is that imageio's ffmpeg plugin needs `imageio_ffmpeg` package. If not installed, get_writer fails. But maybe there's another plugin for mp4? No.

Let me reconsider: maybe writing with the pillow plugin to a .gif and reading with fps works. Let me recall more concretely.

Actually I found it: In imageio's pillow plugin, the GIF reader:

```python
class GIFPlugin(PillowPlugin):
    def _open(self, loop=0, duration=None, fps=None):
        self._loop = loop
        self._duration = duration
        self._fps = fps
        ...
```

Hmm, I genuinely am not certain. But I do recall that the old `imageio.plugins.pillow_legacy` GIF reader had `fps` parameter:

```python
class GifImageFile(PillowImageFile):
    def _open(self, loop=0, duration=None, fps=None):
        ...
        if fps is not None:
            ...
```

Yes! I'm now fairly confident. The legacy pillow plugin's GIF reader accepts `fps`. In imageio v2.10-ish, `imageio.plugins.pillow_legacy.GifImageFile._open(self, loop=0, duration=None, fps=None)`.

Hmm, but newer imageio (2.11+) replaced pillow_legacy with pillow. The new one... Let me recall `imageio/plugins/pillow.py`:

```python
class GIFPlugin(PillowPlugin):
    class Reader(PillowPlugin.Reader):
        def _open(self, loop=0, duration=None, fps=None):
```

I think it still accepts fps.

OK, but there's risk. Let me think of a more robust plan.

Actually — maybe the safest is to check whether ffmpeg is available at all. We can't. But the error clearly indicates it's not.

Hmm, what if we use a different container format that imageio can write without ffmpeg? The pillow plugin can write GIF, PNG, JPEG, etc. But `get_reader(path, fps=1)` needs a format whose reader accepts `fps`.

Which readers accept `fps`? The ffmpeg reader (obviously), the GIF reader (pillow), maybe the "avbin" reader. GIF is the main non-ffmpeg one.

Let me go with GIF.

Now, GIF frames: `writer.append_data(frame)` where frame is HxWx3 uint8. GIF is palettized (256 colors), so writing noise will quantize. That's fine — we just need frames.

But GIF files with 60+ frames of 64x64 might be large-ish but fine.

Also, reading a GIF with imageio gives frames. Good.

Wait, but the function under test is called with `video_path` — a .gif path. That's fine, it just passes to imageio.

Concern: does `imageio.get_reader(gif_path, fps=1)` actually produce all frames? Yes, GIF reader iterates frames.

Hmm, but another concern: the reader's `fps` might affect how many frames are yielded. No, it just sets timing metadata.

Actually wait. There's a subtlety: in imageio, `get_reader(uri, format=None, mode='?', **kwargs)`. The `fps` kwarg goes to the plugin. For GIF, `fps` sets the playback fps. It shouldn't drop frames.

Let me also consider: maybe the environment does have ffmpeg for reading but not writing? Unlikely given the error.

Alternatively, maybe `imageio_ffmpeg` is installed but the ffmpeg binary isn't. The error "Could not find a backend to open ... with iomo='r'" — hmm, "iomo" is imageio mode. The message format is from imageio's `get_reader`/`get_writer` when no plugin matches. Actually the exact message: `Could not find a backend to open {uri} with iomode {mode}`. Hmm.

Wait, actually the error says "with iomo..." truncated. This is imageio's error when no plugin can handle the file. It suggests ffmpeg plugin isn't registered/available.

OK so GIF it is.

But hold on — will the pillow plugin be available? imageio requires numpy and pillow for the pillow plugin. Pillow is likely installed. Let's go.

Actually, let me reconsider once more. There's another possibility: imageio's `get_writer` for mp4 might work if we pass `format='ffmpeg'`... no, same problem.

Let me also consider using the `imageio-ffmpeg`... not available.

Alright, GIF approach.

But there's a risk that `fps` kwarg isn't accepted by the GIF reader, causing an error like "unexpected keyword argument". If the GIF reader doesn't accept fps, then the whole thing fails.

Hmm. Let me think about whether there's a way to be more robust. 

What if I write the file as a .mp4 but using... no.

Alternative: What if imageio can read a GIF without fps, and the fps kwarg is just ignored? No, unexpected kwargs typically raise.

Let me search memory harder. imageio pillow plugin (v2.9.0, plugins/pillow.py):

Actually in imageio 2.9, the plugin was `pillow_legacy`. In 2.10+, `pillow` plugin was introduced and `pillow_legacy` deprecated. The new `pillow.py` (imageio 2.13):

```python
class GIFPlugin(PillowPlugin):
    """Plugin for GIF files."""

    class Reader(PillowPlugin.Reader):
        def _open(self, loop=0, duration=None, fps=None):
            self._loop = loop
            self._duration = duration
            self._fps = fps
            ...
```

Hmm, I think I recall `fps` being there. Actually let me recall the actual imageio v2 pillow GIF reader code:

```python
    class Reader(PillowPlugin.Reader):
        def _open(
            self,
            loop: int = 0,
            duration: Optional[float] = None,
            fps: Optional[float] = None,
        ):
            self._loop = loop
            self._duration = duration
            self._fps = fps
            ...
```

I'm reasonably confident. Also, the legacy one definitely had fps.

Alternatively, I could avoid GIF and use... hmm.

Actually, wait. Another thought: maybe ffmpeg IS available for reading (the ffmpeg plugin can be registered), and the write failure was because... no, the error is clear.

Hmm, actually let me reconsider the error: "Could not find a backend to open `.../v60_64x64.mp4` with iomo..." — this is `imageio.get_writer` failing. The message in imageio is:

```
Could not find a backend to open `{uri}` with iomode `{mode}`.
```

Wait but it says "with iomo" — truncated in the task. Probably "with iomode `wi`". So it's the writer.

OK.

Let me also think: is there a chance that the pillow plugin is not installed and GIF writing fails too? Then we're stuck. But pillow is a very common dependency.

Hmm, but actually, another idea: what if we don't create a video at all, and instead the "video" is something imageio can read... no, must be a real file.

Let me also consider: could we use `imageio.v3`? No, the function uses v2 API.

Let me just go with GIF and hope fps works. Actually, let me hedge: I could make the GIF and also... no, can't hedge.

Hmm, wait. Actually there's another important consideration. Let me reconsider whether the GIF reader's fps parameter exists. If it doesn't, we get a TypeError and all cases fail.

Let me think about imageio's `get_reader` signature: `get_reader(uri, format=None, mode="?", **kwargs)`. The kwargs are passed to the plugin's `read` or `_open`. For pillow plugin reader, the `_open` signature determines acceptance.

I'm going to search my memory for imageio 2.31 pillow.py:

```python
class GIFPlugin(PillowPlugin):
    """Plugin for GIF files.

    Parameters for reading
    ----------------------
    loop : int
        ...
    duration : float
        ...
    fps : float
        ...
    """

    class Reader(PillowPlugin.Reader):
        def _open(
            self,
            loop: int = 0,
            duration: float = None,
            fps: float = None,
        ):
```

Yes, I'm fairly confident this exists. The docstring for GIFPlugin lists `loop`, `duration`, `fps` as reading parameters.

OK, going with GIF.

Now let's design the videos. GIF frames: 64x64x3 uint8. Noise frames will be quantized to 256 colors but that's fine.

Actually, GIF writing with random noise — the palette quantization per frame. Pillow's GIF writer with `append_data` per frame... imageio's pillow writer for GIF uses `save_all=True` and appends frames. Should work.

Hmm, but there might be an issue: imageio's GIF writer might require `mode='I'` or specific handling. Let's just use `imageio.get_writer(path, mode='I')`? Actually for GIF, imageio's pillow writer... Let me use `imageio.get_writer(str(path))` and let it pick.

Actually, for multi-frame GIF, imageio recommends `imageio.mimwrite(path, frames, fps=...)` or `get_writer(path, mode='I')`. The default mode for GIF writer might be 'i' (single image). Let me use `mode='I'`.

Hmm, actually the pillow plugin's GIF writer: `_open(self, loop=0, duration=None, fps=20, palettesize=256, quantizer=0, subrectangles=False)`. And it writes multiple frames when you call append_data multiple times. The `mode` parameter... 

In imageio, `get_writer(uri, format=None, mode='?', **kwargs)`. For pillow plugin, mode 'i' = single image, 'I' = multiple images. For GIF, the writer should handle 'I'.

Let me just use `imageio.get_writer(str(path), mode='I', fps=1)`.

Hmm, but if the writer's `_open` doesn't accept `fps`... it does (fps=20 default in pillow GIF writer). Good.

Wait, actually, does the GIF *writer* accept fps? Let me recall: `imageio.get_writer('out.gif', fps=10)`. Yes, that's standard usage.

OK.

Now, one more consideration: the number of frames. GIF files with 240 frames of 64x64 — each frame maybe ~1-4KB, so ~500KB-1MB. Fine.

But generating 240 noise frames and quantizing to GIF palette could be slow-ish. Should be OK (under 10s total build).

Actually, GIF quantization of noise can be slow. Let me reduce: use fewer frames or smaller. Let's keep 240 frames at 64x64. Pillow's quantizer on 64x64 is fast.

Hmm, actually the default GIF quantizer in pillow is `Image.Quantize.MEDIANCUT` which is fast.

Let me reconsider the sizes to keep build time reasonable.

Let me now also handle: the function `extract_images` calls `imageio.get_reader(video_path, fps=1)`. For a GIF, this returns the reader. Then iterates. Good.

Now, `sample_images`: if number_frames < len(frames), samples; else returns all.

Let me design 8 cases:

1. 60 frames, sample 5
2. 240 frames, sample 6
3. 40 frames, sample 3
4. 6 frames, sample 6 (all)
5. 30 frames, sample 1
6. 50 frames wide (64x96), sample 4
7. 50 frames tall (96x64), sample 4
8. 12 frames 128x96, sample 2

Hmm, but GIF at 128x96 with 12 frames — fine.

Wait, but there's a concern about output size: case 4 returns 6 frames of 64x64x3 = 6*64*64*3 = 73728 values. Under 100k. Good. Case 8 returns 2 frames of 128x96x3 = 2*128*96*3 = 73728. Good.

Case 2: 6 frames of 64x64x3 = 73728. Good.

All fine.

Actually wait — for case 4, number_frames=6 and len(frames)=6, so `number_to_sample < len(images)` is False → returns all 6 frames. Good.

Now checks: 
- zero frames requested (number_frames=0): `0 < len(images)` → True, `np.linspace(0, len-1, 0)` → empty array, `np.array(images)[empty]` → shape (0, H, W, 3). Actually `np.array(images)` where images is a list of frames. With 6 frames, np.array gives (6,64,64,3). Indexing with empty int array gives (0,64,64,3). Fine.

Hmm, but `np.round(np.linspace(0, 5, 0)).astype(int)` → `linspace(0,5,0)` returns empty array. `.astype(int)` fine. OK.

- one frame video, number_frames=1: `1 < 1` False → returns np.array of 1 frame.
- missing file: imageio.get_reader raises. Both versions raise the same.

Hmm, but "missing file" — will imageio raise? `imageio.get_reader('nonexistent.mp4')` — it tries to open, raises. But the format detection: for a nonexistent file, imageio can't determine format from extension? It can from extension .mp4 → ffmpeg plugin → fails to open file → error. Or "Could not find a backend". Either way it raises. Good.

Actually, careful: if the ffmpeg plugin isn't available, `get_reader('x.mp4')` raises "Could not find a backend". That's still a raise. Fine, both versions raise.

Hmm, but actually it might be better to use a .gif missing file so the error is about the file not existing. Either way it raises. Let me use a .gif path to be safe (since gif plugin is available).

Actually, if the file doesn't exist, imageio's pillow plugin would raise FileNotFoundError. That's a clean raise. Let me use `str(WORKDIR / "does_not_exist.gif")`.

Hmm, but wait: does `imageio.get_reader` check file existence before choosing plugin? It uses the extension to pick the plugin, then the plugin opens the file and fails. So FileNotFoundError. Good.

Now, the big question remains: will the GIF approach work? Let me add a fallback... no, can't.

Hmm, let me reconsider. Is there any chance the environment has ffmpeg? The error says no backend for writing mp4. Let me trust that.

But actually, wait. Let me re-read the error: "Could not find a backend to open `.../v60_64x64.mp4` with iomo...". 

Hmm, "iomo" — maybe it's "iomode". The imageio error is:

```python
raise RuntimeError(
    "Could not find a backend to open `%s`` with iomode `%s`." % (uri, mode)
)
```

Hmm, but there's also a possibility this happens because the ffmpeg plugin requires `imageio_ffmpeg` package which isn't installed. Right.

So no ffmpeg at all. GIF is our best bet.

Actually, hold on. Let me reconsider: maybe there's another way to get frames into the reader. What about creating a directory of PNG files? imageio can't read a directory as a video.

What about using the `pillow` plugin to write a multi-page TIFF? Reading TIFF with fps? Probably doesn't accept fps.

GIF is the one.

Hmm, actually another thought: what if we write the GIF but the reader needs `format='gif'`? No, extension detection works.

Let me now also double check: `imageio.get_reader(gif_path, fps=1)` — if the GIF reader's `_open` accepts fps, great. If not... TypeError.

Let me look for more certainty. I'll recall the imageio pillow plugin source (version 2.34):

```python
class GIFPlugin(PillowPlugin):
    """Plugin for GIF files.

    Parameters for reading
    ----------------------
    loop : int
        The number of loops. Default 0 (infinite).
    duration : float
        The duration of each frame in seconds.
    fps : float
        The playback frame rate. If supplied, the duration is overwritten.
    ...
    """

    class Reader(PillowPlugin.Reader):
        def _open(
            self,
            loop: int = 0,
            duration: float = None,
            fps: float = None,
        ):
            self._loop = loop
            self._duration = duration
            self._fps = fps
            ...
```

Yes. I'm confident enough.

Hmm, wait, actually I want to double-check by recalling the legacy plugin:

```python
class GifImageFile(PillowImageFile):
    def _open(self, loop=0, duration=None, fps=None):
        ...
```

Yes, this is in `imageio/plugins/pillow_legacy.py`. And the new `pillow.py` GIFPlugin.Reader also has it.

OK, going with GIF.

Now let me think about whether writing GIF works with `imageio.get_writer(path, mode='I', fps=1)`. 

The pillow plugin's GIF writer `_open`:
```python
def _open(self, loop=0, duration=None, fps=20, palettesize=256, quantizer=0, subrectangles=False):
```

Hmm, does it accept `mode`? The `mode` is handled by the plugin framework, not `_open`. `get_writer(uri, format, mode, **kwargs)` → the plugin's `write` method handles mode. For pillow plugin, `write(ndimage, **kwargs)`.

Actually imageio's pillow plugin writer: `PillowPlugin.write(self, ndimage, mode, **kwargs)`? Hmm.

Let me just use `imageio.get_writer(str(path), mode="I", fps=1)`.

Actually, I recall that for multi-frame writing with imageio v2, you do:
```python
writer = imageio.get_writer('out.gif', mode='I', fps=10)
writer.append_data(frame)
writer.close()
```
Yes, this is documented.

Hmm, but the default `mode='?'` for GIF might already resolve to 'I'. Let me just be explicit with mode='I'.

Wait, actually there's a subtlety: imageio's `get_writer` with mode='I' for pillow GIF. Let me check: the pillow plugin's `Writer` class has `_open` and the plugin's `write` method. In imageio's `Plugin` base, `get_writer` calls `plugin.write(ndimage, **kwargs)` for each append? No...

Actually imageio v2 API: `writer = imageio.get_writer(uri, format=None, mode='?', **kwargs)`. This returns a `Writer` object. `writer.append_data(im)` calls the plugin's `write` method with the image.

For the pillow plugin, the `write` method handles both single and multi-image:
```python
def write(self, ndimage, mode, **kwargs):
    ...
```
Hmm, actually the pillow plugin's `write` signature is `write(self, ndimage, **kwargs)` and it uses `self._image` / `self._images`.

OK, I'll trust the documented usage.

Hmm, actually, let me reconsider. There's a known gotcha: imageio's pillow GIF writer requires `mode='I'` to write multiple frames. Yes.

Let me write the code.

Actually, one more important thing: GIF frames are quantized to 256 colors. When read back, imageio returns RGB frames. Fine.

Also, GIF frame count: when you append 60 frames, the reader yields 60 frames. Good.

But careful: some GIF readers might yield the frames with a different count due to how pillow handles the first frame. Generally it's exact.

Now, let me also think about whether the GIF reader yields frames as numpy arrays of shape (H, W, 3). Yes.

OK.

Now, build time: writing GIFs with noise. Pillow quantizes each frame. For 240 frames of 64x64, that's 240 quantizations — fast, maybe 0.5s.

Total: 8 videos, ~500 frames total. Fine.

Hmm, but actually noise frames quantize poorly and might produce large GIFs. 64x64 noise quantized to 256 colors — each frame maybe 3-6KB. 240 frames → ~1MB. Fine.

Let me reduce the 240-frame one to be safe? It's fine.

Actually, let me reconsider the sizes. The task says one call should take 1ms-200ms. Reading a 240-frame GIF and decoding... GIF decoding of 240 frames of 64x64. Should be maybe 50-100ms. Fine.

Reading 60 frames → ~15-30ms. Fine.

Hmm, the 6-frame one might be ~2ms. Fine.

Now let me write the final code.

One more consideration: the module-level code runs when the source is imported. If GIF writing fails, the whole source fails to load. That's the risk. But we have no choice.

Actually, hmm, wait. Let me reconsider: could I make the video files with `imageio.mimwrite`? Same plugin. No difference.

Let me also think: is there a chance that the pillow plugin isn't installed and only ffmpeg-based plugins are? No — pillow is a core imageio dependency for many formats. Actually, imageio's pillow plugin requires Pillow. If Pillow isn't installed, `imageio.get_writer('x.gif')` fails. But torchvision requires Pillow, and the repo uses torchvision. So Pillow is installed.

Good.

Let me write it.

```python
import numpy as np
import imageio

_VIDEO_DIR = WORKDIR / "extract_images_videos"
_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _frame(kind, i, height, width, rng):
    if kind == "noise":
        return rng.randint(0, 256, size=(height, width, 3)).astype(np.uint8)
    if kind == "gradient":
        xs = np.linspace(0.0, 255.0, width)
        ys = np.linspace(0.0, 255.0, height)
        gx, gy = np.meshgrid(xs, ys)
        r = ((gx + 5.0 * i) % 256.0).astype(np.uint8)
        g = gy.astype(np.uint8)
        b = (((gx + gy) * 0.5 + 3.0 * i) % 256.0).astype(np.uint8)
        return np.stack([r, g, b], axis=-1)
    c = np.array([(37 * i) % 256, (91 * i) % 256, (53 * i) % 256], dtype=np.uint8)
    return np.broadcast_to(c, (height, width, 3)).copy()


def _make_video(name, n_frames, height, width, seed, kind="noise"):
    path = _VIDEO_DIR / name
    rng = np.random.RandomState(seed)
    writer = imageio.get_writer(str(path), mode="I", fps=1)
    try:
        for i in range(n_frames):
            writer.append_data(_frame(kind, i, height, width, rng))
    finally:
        writer.close()
    return str(path)
```

Hmm, `rng.randint(0, 256, size=(h,w,3))` returns int64 by default; `.astype(np.uint8)` — but the writer expects uint8. Let me do `rng.randint(0, 256, size=(height, width, 3), dtype=np.uint8)`. RandomState.randint supports dtype. Yes.

Now, GIF writer with fps=1: the `fps` kwarg. And mode='I'.

Hmm, actually I realize there might be an issue: `imageio.get_writer(str(path), mode="I", fps=1)` — the pillow plugin's GIF writer `_open` signature. Let me recall:

```python
class GIFPlugin(PillowPlugin):
    class Writer(PillowPlugin.Writer):
        def _open(self, loop=0, duration=None, fps=20, palettesize=256, quantizer=0, subrectangles=False):
```

Hmm, does it accept `fps`? I believe the GIF writer accepts `fps` to set frame duration. Yes.

OK.

Now, will `mode="I"` work? The pillow plugin's `write` method:
```python
def write(self, ndimage, mode, **kwargs):
```
Hmm, actually in imageio the plugin's `write` signature is `write(self, ndimage, **kwargs)` and mode is passed... Let me recall imageio's `Writer.append_data`:

```python
def append_data(self, im, meta=None):
    ...
    self._checkClosed()
    ...
    # Get metadata
    ...
    # Write
    self._format.write(im, self._meta, **self._kwargs)
```

Hmm, in imageio v2, `Format.write(im, meta, **kwargs)`.

The pillow plugin's `write`:
```python
def write(self, ndimage, meta, **kwargs):
    ...
```

And the plugin's `_open` is called with the kwargs during `get_writer`. The `mode` is used by the plugin framework to select the writer.

Actually, in imageio's `get_writer`:
```python
def get_writer(uri, format=None, mode="?", **kwargs):
    ...
    plugin = ...
    return plugin.writer(uri, format, mode, **kwargs)
```

And `Plugin.writer` → `Writer(self, uri, format, mode, **kwargs)` → `self._open(**kwargs)`.

Hmm, the `mode` is passed to the Writer constructor, which resolves '?' to 'i' or 'I' based on the format's capabilities.

So `imageio.get_writer(path, mode="I", fps=1)` should work.

Actually, I realize for GIF the default mode might already be 'I' since GIF is a multi-image format. But being explicit is fine.

Hmm, but wait — does specifying mode='I' cause issues? Let me think. In imageio, `Writer.__init__(self, plugin, uri, format, mode, **kwargs)`. It validates mode against the format's `modes`. For GIF, modes might be `["i", "I"]`. So 'I' is valid.

OK.

Now let me reconsider: maybe I should not pass `fps` to the writer to avoid issues, and instead rely on... no, fps is fine for GIF writer.

Actually, hmm, one concern: if I pass `fps=1` to the GIF writer, and the reader reads with `fps=1`, fine.

Let me finalize.

Actually, let me reconsider the whole approach once more. Is there a risk that GIF reading with `fps=1` yields fewer frames? No.

Hmm, but actually — here's a thought. What if the GIF reader's `fps` parameter, when set, causes imageio to drop duplicate frames or something? No, that's not a thing.

OK.

Let me also reconsider: maybe I should make the videos smaller in frame count to reduce risk of long build. Let's keep as planned.

Let me now write the checks and cases.

checks():
1. ("zero-frames", lambda: (_V_6, 0))
2. ("one-frame-video", lambda: (_V_1, 1))
3. ("missing-file", lambda: (str(_VIDEO_DIR / "nope.gif"), 4))

Hmm, for "zero-frames", `np.linspace(0, 5, 0)` → array([]). `np.round(...)` → array([]). `.astype(int)` → array([], dtype=int). `np.array(images)[array([],dtype=int)]` → shape (0,64,64,3). OK, returns empty array. Fine.

Wait, but does `np.linspace(0, len(images)-1, 0)` work when number_to_sample=0? `np.linspace(0, 5, 0)` returns `array([], dtype=float64)`. Yes.

And `0 < 6` is True. Good.

cases(): 8 as planned.

Let me write it out.

Actually, let me reconsider the frame sizes to make sure output < 100k values.

Case "all-6-frames": returns 6 frames of 64x64x3 = 73728. OK.
Case "hires-2-of-12": 2 frames of 128x96x3 = 73728. OK.
Case "wide-4-of-50": 4 frames of 64x96x3 = 73728. OK.
Case "tall-4-of-50": 4 frames of 96x64x3 = 73728. OK.
Case "sample-5-of-60": 5*64*64*3 = 61440. OK.
Case "sample-6-of-240": 6*64*64*3 = 73728. OK.
Case "sample-3-of-40": 3*64*64*3 = 36864. OK.
Case "single-frame": 1*64*64*3 = 12288. OK.

Good.

Now, the argument rendering: the video path is a string. Fine.

Let me write the final source.

One thing: `_make_video` uses `imageio.get_writer`. If GIF writing isn't supported... we're stuck. Let's go.

Actually, hold on. Let me reconsider whether I should use `format="GIF"` explicitly. `imageio.get_writer(str(path), format="GIF", mode="I", fps=1)`. Extension .gif should auto-detect. I'll rely on extension.

Hmm, but there's a subtlety: imageio's format detection for writing uses the extension. `.gif` → GIF. Good.

Let me write.

Also let me double check `np.random.RandomState.randint(0, 256, size=(h,w,3), dtype=np.uint8)`. RandomState.randint signature: `randint(low, high=None, size=None, dtype='l')`. Yes, dtype supported. Good.

Final code:

```python
import numpy as np
import imageio

_VIDEO_DIR = WORKDIR / "extract_images_videos"
_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _frame(kind, i, height, width, rng):
    if kind == "noise":
        return rng.randint(0, 256, size=(height, width, 3), dtype=np.uint8)
    if kind == "gradient":
        xs = np.linspace(0.0, 255.0, width)
        ys = np.linspace(0.0, 255.0, height)
        gx, gy = np.meshgrid(xs, ys)
        r = ((gx + 5.0 * i) % 256.0).astype(np.uint8)
        g = gy.astype(np.uint8)
        b = (((gx + gy) * 0.5 + 3.0 * i) % 256.0).astype(np.uint8)
        return np.stack([r, g, b], axis=-1)
    c = np.array([(37 * i) % 256, (91 * i) % 256, (53 * i) % 256], dtype=np.uint8)
    return np.broadcast_to(c, (height, width, 3)).copy()


def _make_video(name, n_frames, height, width, seed, kind="noise"):
    path = _VIDEO_DIR / name
    rng = np.random.RandomState(seed)
    writer = imageio.get_writer(str(path), mode="I", fps=1)
    try:
        for i in range(n_frames):
            writer.append_data(_frame(kind, i, height, width, rng))
    finally:
        writer.close()
    return str(path)


_V_60_64 = _make_video("v60_64x64.gif", 60, 64, 64, 0, "noise")
...
```

Wait, but there's a risk: the GIF writer with `fps=1` — the frame duration would be 1 second. That's fine.

Hmm, actually, I want to reconsider: does the imageio GIF writer accept `fps`? Let me think about the error we might get. If `_open` doesn't accept fps, we get TypeError at module load → source fails to load. That's the same failure mode.

I'm fairly confident it does. `imageio.mimsave('x.gif', frames, fps=10)` is standard.

Actually, `mimsave` passes fps to the writer. Yes.

OK.

Let me also think: `mode="I"` — is it needed? For GIF, imageio might default to 'I'. But explicit is safer. Actually, hmm, what if 'I' isn't a valid mode for the GIF format in this imageio version? Then error. 

In imageio, the GIF format's modes: `"i"` (single) and `"I"` (multiple). Yes, standard.

Hmm, actually I recall imageio's pillow plugin GIF writer: `class GIFPlugin(PillowPlugin)` with `Writer` having `_open` and the format registration includes modes. Let me just trust.

Alternatively, use the default mode and let imageio figure it out: `imageio.get_writer(str(path), fps=1)`. For GIF, default mode '?' resolves to... For formats that support multiple, '?' → 'I'? Actually imageio's `Writer` resolves '?' to the first mode in the format's modes list. For GIF, modes are `("i", "I")`? Then '?' → 'i', which would only write one frame.

Hmm. So explicit mode='I' is important.

Actually, I recall that for GIF, imageio's default mode is 'I' because... hmm. Let me just be explicit.

Hmm, wait. Actually, in imageio, `get_writer` with mode='?' for a format: `Writer.__init__` does:
```python
if mode == "?":
    mode = self._format.modes[0]
```
Hmm, or it picks based on... Let me recall. In imageio/core/format.py:

```python
class Format:
    def __init__(self, name, description, extensions=None, modes=None, ...):
        ...
        self._modes = modes
```

And Writer:
```python
class Writer:
    def __init__(self, plugin, uri, format, mode, **kwargs):
        ...
        if mode == "?":
            mode = self._format.modes[0] if self._format.modes else "?"
```

Hmm, I'm not sure. For GIF in pillow plugin, the modes might be `["i", "I"]`. So '?' → 'i'. Then only one frame written. Bad.

Actually, I recall that for GIF the modes are `("i", "I")` and imageio's `mimsave` explicitly uses mode 'I'. And `get_writer('x.gif')` default... Let me just use mode='I'.

OK, going with mode='I'.

Hmm, but actually, hmm. Let me reconsider: maybe imageio's GIF format modes are `["I"]` only? Because GIF is inherently multi-frame. In that case '?' → 'I'. Either way, explicit 'I' works.

Alright.

Let me finalize. Actually, let me reduce risk further: what if I use `imageio.mimwrite`? Same thing.

Let me write the final answer.

Actually, one more thought: instead of GIF, could I use the "pillow" plugin to write a multi-frame PNG? No, PNG is single frame.

What about APNG? imageio's pillow plugin might support APNG writing but reading with fps? Unlikely.

GIF it is.

Hmm, let me reconsider one more time whether there's a chance ffmpeg IS available and the issue was something else. The error: "Could not find a backend to open `...mp4` with iomo...". 

Actually, hmm, "iomo" might be a truncation of "iomode". The full imageio error message is:

```python
raise RuntimeError(
    "Could not find a backend to open `%s`` with iomode `%s`." % (uri, mode)
)
```

Hmm, actually I think the message is in `imageio.core.request.Request` or `imageio.core.findlib`. Let me recall:

```python
def get_reader(uri, format=None, mode="?", **kwargs):
    ...
```

and in `imageio/core/imopen.py` there's:
```python
raise RuntimeError(
    "Could not find a backend to open `%s`` with iomode `%s`." % (uri, mode)
)
```

Hmm, actually I think the message is:
```
Could not find a backend to open `{uri}` with iomode `{mode}`.
```
Hmm, but the task shows "with iomo..." — maybe "iomode `wi`" truncated to "iomo". Whatever.

So it's the writer failing to find a backend for mp4. Confirms no ffmpeg.

Hmm, but wait: could it be that the ffmpeg plugin exists but requires `imageio_ffmpeg` and the error is different? The error "Could not find a backend" is generic — happens when no plugin's `can_write` returns True for the URI.

OK. GIF.

Actually, hmm, one more alternative that might be more robust: what if the environment has `imageio_ffmpeg` but not the ffmpeg binary on PATH? Then get_writer would fail with a different error. Anyway.

Let me also consider: what if imageio's pillow plugin is registered but the GIF format isn't available because Pillow lacks GIF support? Pillow always has GIF. Fine.

Final answer time.

Let me write cleanly.

Actually, I realize I should double check: does `imageio.get_reader(gif_path, fps=1)` work, or does the fps kwarg need to be passed differently? `get_reader(uri, format=None, mode="?", **kwargs)` — kwargs go to the plugin's reader `_open`. So `fps=1` → `_open(fps=1)`. Good.

Let me write.

Also, should I worry that the GIF reader yields frames as RGBA (4 channels) instead of RGB? Pillow's GIF frames are 'P' mode (palette). imageio converts to RGB. So (H,W,3). Good.

Hmm, actually imageio's pillow plugin might return RGBA for GIF? Let me think. The pillow plugin's reader `_get_data` does:
```python
im = self._image
if im.mode == "P":
    im = im.convert("RGBA")  # or "RGB"
```
Hmm. Actually I recall imageio's pillow reader converts to RGB or RGBA depending. For GIF, it might be RGB.

Hmm, this affects the output shape but that's fine — both original and modified versions return the same thing. The task compares outputs between original and modified, so shape consistency between them is what matters, not the absolute shape.

But it does affect the size: RGBA is 4 channels → 6*64*64*4 = 98304 < 100k. OK, still fine. But let me be a bit careful with the larger ones.

Case "hires-2-of-12": 2*128*96*4 = 98304. Just under 100k. Hmm, cutting it close. Let me reduce to 2 frames of 128x96 → if RGBA, 98304. Still under 100000. OK but risky if it's actually more.

Let me reduce the hires case to 2 frames of 96x80 or just use 2 frames of 128x96... Actually let me make it 2 frames of 100x80: 2*100*80*4 = 64000. Safer.

Hmm, but "keep what it returns under about 100 000 values". 98304 is under. Fine. But let me just reduce slightly to be safe.

Actually, let me reconsider all sizes assuming 4 channels:
- 5 frames 64x64x4 = 81920 OK
- 6 frames 64x64x4 = 98304 OK (close)
- 3 frames 64x64x4 = 49152 OK
- 6 frames 64x64x4 = 98304 OK
- 1 frame 64x64x4 = 16384 OK
- 4 frames 64x96x4 = 98304 OK
- 4 frames 96x64x4 = 98304 OK
- 2 frames 128x96x4 = 98304 OK

All under 100k. OK, acceptable.

Hmm, but if it's RGBA and the array is (N,H,W,4), the count is N*H*W*4. All ≤ 98304. Fine.

Actually, to be safer, let me reduce the frame counts a bit for the bigger ones. E.g., 6 frames → 5 frames. But the case "all-6-frames" needs number_frames == len(frames) for the "else" branch. I could use a 5-frame video and sample 5.

Let me restructure:
- "all-frames" case: 5-frame video, sample 5 → 5*64*64*4 = 81920. Good.

And "sample-6-of-240" → sample 5 of 240: 5*64*64*4 = 81920. Good.

Let me adjust: use 5 instead of 6 for those.

Actually, let me just reduce all to be comfortably under. Let me use:
- sample 4 of 60 → 4*64*64*4 = 65536
- sample 5 of 240 → 81920
- sample 3 of 40 → 49152
- all 5 of 5 → 81920
- single frame → 16384
- wide 4 of 50 → 4*64*96*4 = 98304 → reduce to 3 → 73728
- tall 3 of 50 → 3*96*64*4 = 73728
- hires 2 of 12 → 2*128*96*4 = 98304 → reduce to 1? No, sample 2 of 12 is fine but let me use 96x80: 2*96*80*4 = 61440

Hmm, this is getting fiddly. Let me just use modest sizes.

Let me finalize:

Videos:
- A: 60 frames 64x64 noise
- B: 240 frames 64x64 noise
- C: 40 frames 64x64 gradient
- D: 5 frames 64x64 solid
- E: 30 frames 64x64 noise
- F: 50 frames 64x96 noise
- G: 50 frames 96x64 gradient
- H: 12 frames 96x80 noise

Cases:
1. sample-4-of-60: (A, 4)
2. sample-5-of-240: (B, 5)
3. sample-3-of-40-gradient: (C, 3)
4. all-5-frames: (D, 5)
5. single-frame: (E, 1)
6. wide-3-of-50: (F, 3)
7. tall-3-of-50: (G, 3)
8. hires-2-of-12: (H, 2)

Output sizes (RGBA worst case):
1. 4*64*64*4 = 65536
2. 5*64*64*4 = 81920
3. 3*64*64*4 = 49152
4. 5*64*64*4 = 81920
5. 1*64*64*4 = 16384
6. 3*64*96*4 = 73728
7. 3*96*64*4 = 73728
8. 2*96*80*4 = 61440

All good.

Checks:
- zero-frames: (D, 0) → 0 frames
- one-frame-video: (V_1, 1)
- missing-file: (str(_VIDEO_DIR / "nope.gif"), 4)

Let me finalize the code.

Wait, D is 5 frames of solid color. For "all-5-frames", number_frames=5 == len=5 → else branch. Good.

Also, for checks "zero-frames" with D (5 frames): `0 < 5` → True → linspace(0,4,0) empty → returns empty array. Good.

OK writing now.

Actually, one concern about solid-color frames in GIF: all frames same color → GIF might collapse? No, GIF stores each frame.

Hmm, but actually with solid frames and GIF's disposal, the reader should still yield 5 frames. Let me make the solid frames slightly different per frame (I already do: color depends on i). Good.

Let me write the final code.

Also, I should double-check: `np.broadcast_to(c, (height, width, 3)).copy()` — c is shape (3,), broadcast to (h,w,3). Good.

Final.

Let me also make sure the module-level `_make_video` calls don't take too long. 60+240+40+5+30+50+50+12+1 = 488 frames total. Each frame quantized by Pillow. Should be a few seconds at most. OK.

Hmm, 240 frames of noise GIF quantization — Pillow's median cut on 64x64=4096 pixels. Fast. OK.

Writing the answer.