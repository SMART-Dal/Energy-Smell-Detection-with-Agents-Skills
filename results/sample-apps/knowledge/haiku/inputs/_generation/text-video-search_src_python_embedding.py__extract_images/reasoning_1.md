I need to write inputs for `extract_images(video_path, number_frames)`. It uses imageio.get_reader(video_path, fps=1) to read frames from an .mp4 file, then samples.

I need to create real .mp4 files under WORKDIR. imageio can write videos using imageio.get_writer with format 'mp4' (requires ffmpeg via imageio-ffmpeg). Let me check: imageio.get_writer(path, fps=...) with .mp4 extension — imageio uses the ffmpeg plugin if imageio-ffmpeg is installed. Repository uses imageio so likely available.

But wait — is imageio-ffmpeg available in the environment? The task says "Use only the standard library, the repository itself and packages the repository already imports." imageio is imported. imageio-ffmpeg might be a dependency. Risky though. Let's think about alternatives.

imageio.get_reader(video_path, fps=1) — the fps parameter... Actually imageio's get_reader signature: get_reader(uri, format=None, mode='?', **kwargs). The 'fps' kwarg is passed to the ffmpeg reader plugin. So it needs ffmpeg.

Alternatively, could we create the video with imageio.get_writer? For mp4, imageio needs ffmpeg plugin. If not available, we could fail. Hmm.

Actually, imageio v2 has a 'ffmpeg' plugin via imageio-ffmpeg package. Many environments have it. But there's a risk.

Another option: create a .mp4 file by writing raw bytes? No, must be a valid video.

Alternatively use imageio.get_writer with format='ffmpeg'. Same thing.

Hmm, we could also potentially use a different extension... but the function's param says .mp4, and get_reader with fps kwarg requires ffmpeg.

Let me think: could we write the video using imageio's own writer with plugin='ffmpeg'? If imageio-ffmpeg is installed, yes.

Let me check whether imageio provides a pure-python way to write mp4... no.

Actually, there's another thought: imageio v2.9+ has `imageio.get_writer(path, fps=...)`. For .mp4, the format is determined by extension → 'ffmpeg'. If imageio-ffmpeg isn't installed, it raises. 

I think the safest is to assume imageio-ffmpeg is available (it's a very common dependency, and the repo relies on imageio for mp4 reading). Let me write the code using imageio to generate videos.

Actually, can I generate videos at module level? Building all inputs under ~10 s. Generating a few mp4s with ffmpeg might take a couple seconds. Fine.

Let me plan the videos:
- Various sizes: small (30 frames), medium (300 frames), large (2000 frames).
- Different resolutions: small frames (e.g., 64x64), larger (320x240).
- number_frames: fewer than len(frames) (sampling path) vs more than len(frames) (returns all).

The function reads all frames with fps=1. Wait — `imageio.get_reader(video_path, fps=1)` — the fps=1 kwarg for the ffmpeg reader is the "fps" used to... Actually in imageio's ffmpeg plugin, `fps` sets the output frame rate for reading. Hmm, actually the ffmpeg reader has a `fps` parameter that resamples the video to the given fps. So with fps=1, a video at 30fps gets downsampled to 1 frame per second. That means the number of frames returned depends on video duration.

Hmm, let me recall: imageio's ffmpeg reader `read_frames` uses `self._fps` ... Actually the FFMPEGReader has parameter `fps` which if not None, "the number of frames per second to read" - it uses `-r` in ffmpeg output options? Let me recall the code:

```python
class FFMPEGReader(PluginBase):
    def __init__(self, request):
        ...
        self._fps = request.kwargs.get("fps", None)
        ...
        if self._fps:
            self._fps = float(self._fps)
```

And in `_read_frame`, there's `self._fps` used with a "timestamp" filter... Actually I recall:

```python
    def _read_frame(self):
        ...
```

And there's `_get_meta_data` etc. Hmm, there's also `_seek` and the `read_frames` method that uses `self._fps` to compute frame indices via `self._meta["fps"]`.

Actually in imageio ffmpeg plugin, `read_frames` does:

```python
        if self._fps:
            # Read frames at the given fps
            ...
```

Hmm, I'm not 100% sure. Let me think about the actual behavior: with `fps=1` on a 30fps video of 30 seconds, you'd get ~30 frames.

Actually I recall the implementation: in `FFMPEGReader.read_frames`, there's:

```python
        if self._fps:
            frame_index = ...
```

Hmm. Let me look at it differently: imageio's ffmpeg reader docs say: "fps : int or float. If set, the reader will read frames at the given fps (by skipping frames)." Something like that.

Actually the code I remember:

```python
    def read_frames(self):
        # Get number of frames, and other info
        ...
        # Create generator
        ...
        if self._fps:
            # compute frame numbers to read
            ...
```

Hmm, I think in newer versions:

```python
    def _read_frame(self):
```

Let me just consider it: whatever the behavior, the function reads all frames from the reader and samples. As long as we produce a valid mp4, it works. The number of frames returned by the reader depends on fps=1 and video duration. To get many frames, we need long videos. To get frames at all, video duration must be >= 1 second.

Hmm, but if fps=1 and the video is 1 second at 30fps, we get 1 frame. That's a problem for "substantial work".

Wait, let me reconsider. Actually I'm fairly confident the imageio ffmpeg reader's `fps` parameter means: the frame rate at which to *interpret* the video metadata, i.e., it overrides the reported fps. Let me recall the source more concretely.

From imageio/plugins/ffmpeg.py (v2.9):

```python
class FFMPEGReader(PluginBase):
    """The FFMPEG reader plugin.

    Implementation of :class:`imageio.core.Format.Reader` ...
    """

    def __init__(self, request):
        PluginBase.__init__(self, request)
        self.request = request

        # Get local variables
        self._filename = request.filename
        self._mode = request.mode
        self._fps = request.kwargs.get("fps", None)

        # Set up the ffmpeg process
        ...
```

and later:

```python
    def _read_frame_data(self):
        ...
```

and

```python
    def _get_meta_data(self):
        """Read meta data from the video stream"""
        ...
        # Get the frame rate
        ...
```

Hmm, and:

```python
    def get_meta_data(self):
        ...
```

I recall there's this in `_read_frame`:

```python
        # Get the frame
        ...
```

And in `read_frames`:

```python
    def read_frames(self):
        """Read all frames. FOR TESTING ONLY."""
        ...
```

Hmm. Actually I remember there's a `_fps` used in `_get_meta_data`:

```python
        if self._fps:
            meta["fps"] = self._fps
            meta["nframes"] = int(meta["duration"] * self._fps)
```

Hmm, that would mean it overrides metadata but not actual frames read... Actually no.

Let me search memory: imageio ffmpeg.py has:

```python
    def _read_frame(self):
        """Read a single frame."""
        ...
```

and

```python
    def _seek(self, index):
        ...
        if self._fps:
            target = index / self._fps
        else:
            target = index / self._meta["fps"]
```

Hmm... And there's `_get_meta_data`:

```python
        # Get fps
        ...
```

OK. I recall now more clearly: there's a `fps` kwarg documented as:

From imageio docs for ffmpeg plugin:
```
fps : int
    The number of frames per second to read. If None, ...
```

Hmm.

Actually, I found it. In imageio/plugins/ffmpeg.py:

```python
class FFMPEGReader(PluginBase):
    def __init__(self, request):
        ...
        self._fps = request.kwargs.get("fps", None)
        ...
        # Start the process
        ...
        if self._fps:
            self._fps = float(self._fps)
```

And:

```python
    def _get_meta_data(self):
        """Read meta data from the video stream"""
        ...
        # Get the fps
        ...
        # Get duration
        ...
```

And:

```python
    def _read_frame(self):
        """Read a single frame"""
        ...
```

And in the `read_frames` generator:

```python
    def read_frames(self):
        """Read all frames. FOR TESTING ONLY."""
        ...
```

Hmm, and there's this snippet I'm more sure about, in `_read_frame` or `_seek`:

```python
        # Seek
        if index == 0:
            ...
```

OK, I'll stop guessing. Let me consider a different approach: I'll just create mp4 files with imageio's writer and check the number of frames read. But I can't run code here.

Hmm, this is important. Let me think about what's most robust.

Actually — key insight: I recall the ffmpeg reader code:

```python
    def _read_frame(self):
        """Read a single frame"""
        # Read from the process
        ...
```

and

```python
    def get_length(self):
        ...
```

Hmm.

Let me try recalling from a different angle. There's a known imageio issue: "get_reader(fps=...)" — the fps argument. From the imageio docs (ffmpeg format):

```
fps : float
    The number of frames per second to read. If None, ...
```

Actually the docstring in imageio/plugins/ffmpeg.py:

```
    Parameters for reading
    ----------------------
    ...
    fps : int
        The number of frames per second to read. If None, the
        fps of the video is used.
```

Hmm, if that's the case, fps=1 would give 1 frame per second of video.

But wait, actually I recall the implementation uses ffmpeg's `-r` output option? No... Let me think about `_read_frame`:

```python
    def _read_frame(self):
        """Read a single frame"""
        # Read the next frame
        ...
```

Hmm, actually here's the real code from imageio 2.x ffmpeg.py (I'm fairly confident now):

```python
    def _read_frame_data(self):
        """Reads and returns the data of the next frame."""
        ...
```

and

```python
    def _read_frame(self):
        """Reads and returns the next frame."""
        ...
```

and importantly:

```python
    def read_frames(self):
        """Read all frames. FOR TESTING ONLY."""
        # Get number of frames, and other info
        ...
```

Hmm.

OK here's another approach: I remember that imageio's ffmpeg reader `fps` param is used in `_get_meta_data`:

```python
        # Store fps
        if self._fps:
            self._meta["fps"] = self._fps
            self._meta["nframes"] = int(self._meta["duration"] * self._fps)
```

Wait no. Let me recall the actual `_get_meta_data`:

```python
    def _get_meta_data(self):
        """Read meta data from the video stream"""
        ...
        # Get the frame rate
        ...
        # Get the duration
        ...
        # Get the number of frames
        ...
```

Hmm.

Alright, let me consider: there IS a known behavior where imageio's ffmpeg reader with `fps=N` reads every Nth... no.

Actually! I now recall clearly. In imageio/plugins/ffmpeg.py:

```python
    def _seek(self, index):
        """Seek to the given frame index."""
        ...
        # Seek
        if self._fps:
            target = index / self._fps
        else:
            target = index / self._meta["fps"]
        ...
```

Hmm, that suggests fps is used for seeking. And:

```python
    def _read_frame(self):
        ...
```

And there's:

```python
    def get_meta_data(self):
        """Get meta data"""
        ...
```

Hmm, and there's this in `_get_meta_data`:

```python
        # Get the number of frames
        if self._fps:
            self._meta["nframes"] = int(self._meta["duration"] * self._fps)
```

Hmm, I keep going in circles.

Let me try yet another approach: search my memory of the actual file. imageio/plugins/ffmpeg.py, around line 300:

```python
class FFMPEGReader(PluginBase):
    """The FFMPEG reader plugin.

    Implementation of :class:`imageio.core.Format.Reader` that reads
    from a file using subprocess and ffmpeg.

    """

    def __init__(self, request):
        PluginBase.__init__(self, request)
        self.request = request

        # Get local variables
        self._filename = request.filename
        self._mode = request.mode
        self._fps = request.kwargs.get("fps", None)

        # Set up the process
        ...
        self._proc = None
        self._meta = None

    def _get_meta_data(self):
        """Read meta data from the video stream"""
        ...
        if not self._proc:
            self._proc = self._open()
        ...
        # Get the output of ffmpeg
        ...
        # Parse the output
        ...
        # Get the fps
        fps = ...
        self._meta = {
            "plugin": "ffmpeg",
            "nframes": ...,
            " fps": fps,
            "duration": duration,
            "size": size,
        }
        ...
```

Hmm.

OK, I remember now! There's this bit in `_get_meta_data`:

```python
        # Get the number of frames
        nframes = ...
```

Ugh.

Different tactic: I know that in imageio, `imageio.get_reader(video, fps=1)` is used in the wild to read one frame per second. Actually hmm, I've seen this exact usage in the sample-apps repo (this is the vespa sample-apps repo). The code is `imageio.get_reader(video_path, fps=1)`. And the comment says "Extract equally spaced frames from a video". So the author used fps=1 to reduce the number of frames read.

Hmm, but actually if fps=1 reduces frames, then reading a 10s video gives 10 frames. That's the intent I think.

Wait, actually let me reconsider. I'm now fairly confident about this code in imageio/plugins/ffmpeg.py:

```python
    def read_frames(self):
        """Read all frames. FOR TESTING ONLY."""
        # Get number of frames, and other info
        ...
```

and in `_read_frame`:

```python
    def _read_frame(self):
        """Read a single frame"""
        # Get the frame
        ...
```

Hmm hmm.

OK, alternative memory: I've definitely seen this in imageio ffmpeg.py:

```python
        # Get the frames
        if self._fps:
            # Read frames at the given fps
            ...
```

Hmm.

Let me just look at it from the perspective of what the ffmpeg command looks like. imageio's ffmpeg reader builds a command like:

```
ffmpeg -i input.mp4 -f rawvideo -pix_fmt rgb24 -vcodec rawvideo -
```

And with fps, it might add `-r 1` before the output. Actually! I recall:

```python
        # Set up the command
        cmd = [ffmpeg_exe, "-i", self._filename, ...]
        if self._fps:
            cmd += ["-r", str(self._fps)]
```

Hmm, but that would be an output option `-r` which resamples.

Hmm, actually I do recall something like:

```python
    def _open(self):
        """Open the ffmpeg process"""
        ...
```

Let me think about `_read_frame` implementation with timestamps:

Actually! Here's the real code I'm now recalling with more confidence:

```python
    def _read_frame(self):
        """Read a single frame"""
        # Read the data
        ...
```

and

```python
    def _seek(self, index):
        """Seek to the given index"""
        ...
```

Nope.

Let me take a totally different approach and just be safe: I'll generate videos where the frame count is large regardless. If fps=1 downsamples, I need long videos (many seconds). If fps=1 doesn't downsample, I get all frames.

Hmm, but if fps=1 downsamples to 1 fps, then a video with 300 frames at 30fps = 10 seconds → 10 frames. To get 300 frames I'd need a 300-second video at 30 fps = 9000 frames to encode. That's slow to generate.

Alternatively I can write the video at 1 fps! If I create the video with fps=1 in the writer, then each frame is 1 second apart, and reading with fps=1 gives all frames. That's a great trick: write with fps=1 so the video's native fps is 1.

Hmm, but does the ffmpeg writer accept fps=1? Yes, `imageio.get_writer(path, fps=1)`. Then the video is 1 fps, and reading with fps=1 preserves all frames (if fps param means resample) or gives all frames (if it just overrides metadata).

Wait but if fps=1 means "read at 1 fps" and the video is 1 fps, we get all frames. If fps=1 means "override the reported fps metadata to 1", then reading all frames gives all frames. Either way, we get all frames. 

But hold on: if the video's native fps is 1 and imageio's reader with fps=1 does resampling via ffmpeg `-r 1`, output frames = input frames. Good.

Hmm, but there's a subtlety: with ffmpeg `-r` resampling and a 1fps input, output is the same. Good.

Actually wait, there might be an issue with very low fps videos and ffmpeg. Should be fine.

Hmm, but actually another concern: does imageio's writer for mp4 with fps=1 work? Yes.

OK but actually, let me reconsider: maybe simpler to write with a normal fps like 5 or 10 and accept whatever. Let me think about which is more robust.

Actually, let's reconsider the whole thing. The risk: if the reader with fps=1 returns very few frames, then the function does little work (fast), which is fine for the benchmark as long as it's not too fast... but we want 1ms-200ms. Reading frames from ffmpeg involves decoding, which is slow-ish. Even 10 frames of 320x240 might take a few ms.

But the bigger risk: if `fps=1` combined with a 1fps video causes weird behavior.

Hmm, let me think about what imageio actually does once more. I'm going to try to recall the actual source text of ffmpeg.py `_get_meta_data`:

```python
    def _get_meta_data(self):
        """Read meta data from the video stream"""
        # Check if we have a process
        if self._proc is None:
            self._proc = self._open()
        ...
```

and `_open`:

```python
    def _open(self):
        """Open the ffmpeg process"""
        # Get the ffmpeg exe
        ...
        # Create the command
        cmd = [self._exe, "-i", self._filename]
        ...
        if self._fps:
            cmd += ["-r", str(self._fps)]
        ...
```

Hmm, I really think there is something like that. Actually, hold on. I recall in imageio ffmpeg.py there's:

```python
        # Set the fps
        if self._fps:
            self._fps = float(self._fps)
```

and in `_read_frame`:

```python
    def _read_frame(self):
        """Read a single frame"""
        ...
```

and in `_get_meta_data`:

```python
        # Get the fps
        fps = ...
        if self._fps:
            fps = self._fps
```

Hmm.

You know what, there's a well-known imageio behavior: the `fps` kwarg to `get_reader` for ffmpeg is documented in imageio docs as:

```
fps : int
    The number of frames per second to read. If None, the fps of the video is used.
```

Hmm, but I also recall reading the source where `_fps` is used to compute `nframes` and to seek.

Let me just go with the safe approach: write videos at 1 fps (so native fps = 1), and also make them of reasonable duration. Then regardless of interpretation, we read all frames.

Hmm, wait. But if `fps=1` is an output `-r 1` option and the input is 1 fps, ffmpeg outputs all frames. Good.

But hmm, one concern: writing a video at fps=1 with many frames — the writer's ffmpeg command uses `-r 1`. Fine.

Actually, there's another concern: if the video is 1 fps and has 300 frames, duration = 300 seconds. ffmpeg reading with `-r 1` outputs 300 frames. Fine.

Hmm, but if the reader's fps param means "read at this fps" and it uses seeking based on `index / fps`... no, it reads sequentially.

OK. Another consideration: maybe I should avoid relying on fps semantics entirely by making videos where both interpretations give many frames. Writing at fps=1 achieves that only if the reader preserves. Hmm, if reader's fps=1 means "downsample to 1 fps", and the video is 1 fps, we get all frames. If reader's fps=1 means nothing (just metadata), we get all frames. Both give all frames. 

What if the reader's fps=1 means "upsample"? No.

OK, let's go with fps=1 videos.

Hmm, wait. Actually, hold on. Let me reconsider. I want to double check the semantics because it matters for realism. Actually you know what — the repo's own usage is `imageio.get_reader(video_path, fps=1)` on real .mp4 videos (probably 30fps). The author clearly intended to sample frames at 1 fps to reduce work. So the semantics is likely "read at 1 fps" → downsample. So for a 30fps video, we get duration-in-seconds frames.

Given that, writing at 1 fps gives us all frames read. Good, consistent.

Hmm, but actually, hmm: if imageio resamples with ffmpeg `-r 1`, and the input is already 1 fps, ffmpeg might still output the same number of frames. Yes.

Alright. But actually there's a subtlety with `-r` and image2/rawvideo output... it should be fine.

Hmm, let me reconsider once more. Actually I now strongly recall the imageio ffmpeg reader code:

```python
    def _get_meta_data(self):
        """Read meta data from the video stream"""
        ...
        # Get the meta data
        ...
        # Get the number of frames
        if self._fps:
            self._meta["nframes"] = int(self._meta["duration"] * self._fps)
```

and

```python
    def _seek(self, index):
        """Seek to the given index"""
        ...
        # Get the time to seek to
        if self._fps:
            t = index / self._fps
        else:
            t = index / self._meta["fps"]
```

Hmm and `_read_frame` reads sequentially. And `read_frames`/iteration uses `_read_frame` sequentially. So the fps param would only affect seeking and nframes metadata, not sequential reading!

Hmm, but that contradicts the intent... Actually no — if fps only affects metadata, then `get_reader(video, fps=1)` wouldn't reduce frames at all, and the repo's code would read all frames. That seems wrong for the repo's intent but possible.

Hmm. Actually wait, I think I recall now that imageio's ffmpeg reader DOES use `-r` in the ffmpeg command. Let me recall the `_open` method:

```python
    def _open(self):
        """Open the ffmpeg process"""
        ...
        # Get the command
        cmd = [self._exe]
        cmd += ["-i", self._filename]
        ...
        # Set the output fps
        if self._fps:
            cmd += ["-r", str(self._fps)]
        ...
        cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
```

Hmm, I have a feeling about `-r`. Actually! Yes — I'm now fairly confident: imageio's ffmpeg reader has:

```python
        if self._fps:
            cmd += ["-r", str(self._fps)]
```

Hmm no...

OK. Decision: write videos at fps=1. This is safe under both interpretations. Let's go.

Hmm, but one more concern: with fps=1 and a 1fps video, if the reader uses `-r 1` output, we get all frames. If the reader uses metadata-based seeking, we get all frames. 

But there's a risk: some ffmpeg versions with `-r 1` on a 1fps input might duplicate/drop frames weirdly. Unlikely.

Now, let's think about the actual video content. Frames are numpy arrays of shape (H, W, 3) uint8. The function returns np.array(images)[idx] — a numpy array of frames. Size: number_frames × H × W × 3 bytes. Must keep output under 100,000 values. Hmm! "keep what it returns ... under about 100 000 values". A numpy array of frames: e.g., 20 frames of 64×64×3 = 20*12288 = 245,760 values. Too many!

Hmm. That's a constraint. The output is a numpy array; "values" probably means elements. So we need number_frames * H * W * 3 < 100,000.

If number_frames = 8 and H=W=64: 8*64*64*3 = 98,304. Just under. Hmm, tight.

If we use smaller frames, e.g., 32×32: 8 * 32*32*3 = 24,576. Better.

Hmm, but small frames mean less work. But the work is mostly in ffmpeg decoding.

Let's think: the output comparison is done in full — comparing numpy arrays. With 100k values it's fine.

Let's design: frames of size 64×64 → 12288 values each. number_frames up to 8 → 98304. OK.

Or 48×64 → 9216 each, 10 frames = 92160.

Hmm, but also "Its arguments are rendered before and after each call to see whether it changed them" — arguments are video_path (string) and number_frames (int). Cheap.

So the output size constraint is the binding one. Let's aim for total output elements ≤ ~100k.

Alternatively use different resolutions per case.

Also note: if number_frames >= len(frames), the function returns ALL frames. So we must ensure len(frames) is small in that case, or number_frames < len(frames).

Let's design cases:

1. Small video (30 frames, 64×64), number_frames=5 → 5*12288 = 61,440. 
2. Medium video (120 frames, 64×64), number_frames=8 → 98,304. 
3. Video with odd resolution, e.g., 48×64 (3072*3=9216 per frame)... wait 48*64*3 = 9216. number_frames=10 → 92,160.
4. number_frames larger than frames → returns all: video with 6 frames of 64×64 → 6*12288=73,728.
5. number_frames=1 → 1 frame.
6. Larger resolution but few frames: 128×128 (49152 per frame) × 2 = 98,304.
7. number_frames=3 with 60 frames.
8. etc.

Hmm, but wait: how many frames does the reader actually yield? If we write a video with 120 frames at fps=1, the reader yields 120 frames. Then sample_images with number_frames=8 gives 8 frames. Good.

But hold on — if the reader's fps=1 does downsample and our video is 1 fps... fine.

Hmm, but actually, wait. There's a risk with writing at fps=1: ffmpeg might produce a video with weird timestamps. Let's just try.

Hmm, actually, let me reconsider: maybe write at fps=1 but that makes duration long. For 120 frames → 120 seconds. Encoding 120 frames is fast. Fine.

Alternatively, write at fps=30 and rely on... no, if fps=1 downsamples we'd get 4 frames from 120. Then number_frames=8 > 4 → returns all 4 frames. That changes the path. Hmm.

Let's just use fps=1 in the writer. Safe.

Hmm, hmm. But actually there's another thought: what if imageio's ffmpeg reader with fps=1 on a 1fps video... the `-r 1` output option. With input 1fps and output `-r 1`, ffmpeg outputs all frames. Yes.

OK wait, actually, I realize I should double check whether imageio's mp4 writer requires the `fps` to be an int or float. `fps=1` is fine.

Now, another consideration: imageio's ffmpeg writer for .mp4 uses libx264 by default? The default codec for mp4 in imageio is 'libx264' with pixel format yuv420p. Actually imageio's ffmpeg writer: for .mp4 files, `codec` defaults to... Let me recall: `imageio.get_writer('out.mp4', fps=30)` works and uses libx264. Yes, imageio handles mp4 with libx264 by default (it sets `-pix_fmt yuv420p` for compatibility).

Hmm, but there's a catch: libx264 requires even dimensions for yuv420p. So use even width/height. 64×64, 48×64, 128×128 all even. Good.

Now, generating video frames: create random-ish but deterministic content. Use numpy RandomState.

Let's write:

```python
import numpy as np
import imageio

def _make_video(path, n_frames, height, width, seed):
    rng = np.random.RandomState(seed)
    writer = imageio.get_writer(str(path), fps=1, macro_block_size=1)
    for i in range(n_frames):
        frame = rng.randint(0, 256, (height, width, 3), dtype=np.uint8)
        writer.append_data(frame)
    writer.close()
```

`macro_block_size=1` avoids resizing to multiples of 16. Good — otherwise imageio might resize frames to 16-multiples. With macro_block_size=1, dimensions preserved. Actually the default macro_block_size=16 causes imageio to resize the video to a multiple of 16, which would change the frame size and thus the output array shape. Since the function's output shape depends on the actual decoded frame size, and we compare outputs between original and modified versions, it doesn't matter for correctness, but for the size budget it does. Let's set macro_block_size=1 to keep exact sizes... but then libx264 with yuv420p needs even dims — 64, 48, 128 are even. OK.

Hmm, actually with macro_block_size=1 and odd dimensions, x264 would fail. We use even dims.

Hmm, but does imageio's writer accept macro_block_size? Yes, it's an ffmpeg writer parameter.

Now, will the decoded frames exactly match? Not necessarily (lossy compression), but that's fine — the function's output is compared between original and modified versions on the same input, and both read the same file. Actually, the file is generated once at module level and read each time. The decoded frames should be deterministic. Good.

Hmm, wait: is decoding deterministic? Yes for the same file and same ffmpeg.

Now: "Same work on every call" — the thunk returns the path and number_frames. The function opens the reader, reads, closes. No state persists... Actually, `imageio.get_reader` — does imageio cache readers? There's `imageio.core` with a "keep reading" ... Actually imageio has a global `config` and readers are not cached across get_reader calls (each creates a new FFMPEGReader). Hmm, but there might be a plugin instance cache. I don't think frames are cached.

Hmm, actually imageio does have a mechanism: `imageio.core.util._get_plugin_instance`? No. Each `get_reader` call creates a new reader object. Fine.

But there's one thing: imageio's ffmpeg reader might leave the process running if not closed. The function doesn't close the reader! `reader = imageio.get_reader(...)` and never closes. So each call spawns an ffmpeg process that... when the reader is garbage collected, `__del__` closes it. Hmm, that could accumulate processes. But GC should handle it. Actually, imageio's FFMPEGReader has `__del__` that calls `self.close()`. And after reading all frames, the process has finished anyway.

Hmm, but the reader object stays referenced until the function returns... it's a local, so after return it's garbage. Fine.

Potential issue: many repeated calls spawn many ffmpeg processes; if not cleaned up, we could exhaust resources. But Python refcounting frees them immediately after the function returns. OK.

Now let's think about timing. Each call: spawn ffmpeg, decode N frames, close. Spawning ffmpeg takes ~50-100ms maybe. Decoding 120 frames of 64×64 is fast. So each call maybe 100-200ms. Hmm, that might exceed 200ms. Let's keep videos modest: 30-150 frames.

Actually process spawn overhead is significant. Let's keep frame counts moderate.

Hmm, but "One call should take roughly 1 ms to 200 ms". Process spawn ~30-80ms. Fine.

Let me now design 8 cases with variety:

1. "short-64x64-sample5": 30 frames, 64×64, number_frames=5 → output 5 frames = 61,440 values. 
2. "medium-64x64-sample8": 120 frames, 64×64, number_frames=8 → 98,304 values. Hmm, right at the limit. Maybe use 7 → 86,016. Let's do 8 but with 64x64 = 12288*8 = 98304 < 100000. OK, acceptable ("under about 100 000"). Let's be safe and use 6 → 73,728.
3. "all-frames-fewer": 6 frames, 64×64, number_frames=10 → returns all 6 frames = 73,728.
4. "single-frame": 20 frames, 64×64, number_frames=1 → 12,288.
5. "wide-96x64": 40 frames, 96×64 (18432 each), number_frames=5 → 92,160.
6. "tall-64x96": 40 frames, 64×96, number_frames=5 → 92,160.
7. "big-res-128x128": 15 frames, 128×128 (49152 each), number_frames=2 → 98,304. Hmm, 2 frames. Or 1 frame → 49,152.
8. "long-video-200": 200 frames, 64×64, number_frames=4 → 49,152.
9. "number_frames-equals-len": 10 frames, 64×64, number_frames=10 → returns all 10 = 122,880. Too many. Use 6 frames, number_frames=6 → 73,728. That's the `number_to_sample == len` case → else branch.

Let me pick 8:

1. "typical-sample": 60 frames, 64×64, n=5 → 61,440
2. "long-video": 240 frames, 64×64, n=6 → 73,728
3. "all-frames-fewer": 5 frames, 64×64, n=12 → 61,440 (else branch)
4. "exact-count": 8 frames, 64×64, n=8 → 98,304 (else branch, since 8 < 8 is False)
5. "single-frame": 30 frames, 64×64, n=1 → 12,288
6. "wide": 50 frames, 96×64, n=5 → 92,160
7. "tall": 50 frames, 64×96, n=5 → 92,160
8. "high-res": 12 frames, 128×128, n=2 → 98,304

Hmm, 98,304 is close to 100,000. Let's use n=2 for high-res → 98,304. Or 1 → 49,152. Let's do 2, it's fine.

Hmm, actually maybe reduce: use 128×96 → 36864 each; n=2 → 73,728.

Let's simplify and keep everything comfortably under.

Also need variety in "different paths": the sampling branch vs the all branch, various n relative to len.

Also duplicates/distributions: frame content — random noise vs gradient vs solid. Let's vary content: some videos with random noise (harder to compress, more decode work? Actually decode is same), some with gradients.

Let's make content varied: random noise, smooth gradient, solid colors, checkerboard.

Now `checks()`: 2-3 small edge inputs. E.g.:
- number_frames=0: sample_images(frames, 0) → 0 < len → idx = round(linspace(0, len-1, 0)) = empty array → np.array(images)[empty] → shape (0, H, W, 3). Works. But wait, the video must exist. Use a small video.
- number_frames=1 with a 1-frame video.
- Actually edge cases might raise? "These may raise." 

Let's do:
- ("one-frame-video", lambda: (str(_V1), 1)) where _V1 is a video with 1 frame. Hmm, reading a 1-frame video at 1fps: duration 1 second? A single frame at 1 fps... ffmpeg might produce 1 frame. Should be OK.
- ("zero-frames", lambda: (str(_V1), 0)) → returns empty array.
- ("nonexistent", lambda: (str(WORKDIR/"nope.mp4"), 4)) → raises. That's allowed for checks.

Hmm, but checks are "checked only for identical behaviour, never measured. These may raise." So raising is fine as long as both versions behave the same. A nonexistent file raising is a good edge case. But it might hang? No, ffmpeg errors out quickly. Hmm, but imageio might raise an error. Both versions raise the same. OK.

Actually, careful: the original and modified versions both call imageio.get_reader on a nonexistent path. imageio's ffmpeg reader might raise on open. Fine.

Hmm, but there's a risk it hangs waiting. Unlikely.

Let me keep checks simple and safe:
- empty-ish: number_frames=0 on a small video → empty array.
- one frame: number_frames=1 on a video with 1 frame.
- nonexistent path → raises.

Hmm, actually for number_frames=0: `np.round(np.linspace(0, len-1, 0)).astype(int)` → array([], dtype=int). Then `np.array(images)[[]]` → shape (0, H, W, 3). Fine.

But careful: if the video has 0 frames... a video always has ≥1.

Let me also consider: does `np.array(images)` work when images is a list of numpy arrays? Yes, stacks them.

Now, module-level video generation. Building all inputs under ~10s. Encoding ~400 frames total across videos — fast (a few seconds). Let's count total frames: 60+240+5+8+30+50+50+12 = 455, plus checks videos ~2. Should encode in a couple seconds.

Hmm, 240 frames at 64x64 — x264 encoding is quick. Fine.

Now, the videos must be created under WORKDIR.

Let me write the code.

```python
import numpy as np
import imageio
from embedding import extract_images

WORKDIR = ...  # provided
```

Wait, WORKDIR is provided — "a provided `pathlib.Path`; do not define it". So I just use it.

Let me write:

```python
import numpy as np
import imageio

_VIDEO_DIR = WORKDIR / "videos"
_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _frame_content(kind, i, h, w, rng):
    if kind == "noise":
        return rng.randint(0, 256, (h, w, 3), dtype=np.uint8)
    if kind == "gradient":
        x = np.linspace(0, 255, w, dtype=np.uint8)
        y = np.linspace(0, 255, h, dtype=np.uint8)
        gx, gy = np.meshgrid(x, y)
        shift = (i * 7) % 256
        return np.stack([(gx.astype(np.int32) + shift) % 256,
                         gy.astype(np.int32),
                         ((gx.astype(np.int32) + gy.astype(np.int32)) // 2) % 256],
                        axis=-1).astype(np.uint8)
    if kind == "solid":
        c = [(i * 37) % 256, (i * 91) % 256, (i * 13) % 256]
        return np.full((h, w, 3), c, dtype=np.uint8)
    # checker
    ...
```

Hmm, keep it simple. Let's do noise and gradient and solid.

Actually simpler: one helper that makes a video given n frames, h, w, seed, and a content kind.

```python
def _make_video(name, n_frames, height, width, seed, kind="noise"):
    path = _VIDEO_DIR / name
    rng = np.random.RandomState(seed)
    writer = imageio.get_writer(str(path), fps=1, macro_block_size=1, quality=8)
    try:
        for i in range(n_frames):
            writer.append_data(_frame(kind, i, height, width, rng))
    finally:
        writer.close()
    return path
```

Hmm, `quality=8` for ffmpeg writer — it maps to CRF-ish. Default quality is 5. Let's not pass quality to avoid issues. Actually the ffmpeg writer's `quality` param exists. Skip it.

Hmm, `macro_block_size=1`: with libx264 and yuv420p, dimensions must be even. Our dims are even. Good.

Wait, does imageio's ffmpeg writer use libx264 by default for .mp4? Let me recall: `imageio.plugins.ffmpeg` writer: `codec` param default None → determined by `_get_default_codec`? Actually:

```python
        # Get the codec
        if self.request.kwargs.get("codec", None):
            ...
        elif self.request.extension in (".mp4", ".m4v", ".mov"):
            self._codec = "libx264"
            ...
```

Hmm, I believe imageio's ffmpeg writer defaults: for mp4 it uses "libx264" and pixel format "yuv420p". Yes — in `FFMPEGWriter._open`, there's:

```python
        if self._codec is None:
            ...
            if self._filename.endswith(".mp4"):
                self._codec = "libx264"
                ...
                self._pix_fmt = "yuv420p"
```

Something like that. Good.

Hmm, actually I recall imageio's ffmpeg writer code:

```python
        # Set the codec
        if self.request.kwargs.get("codec", None):
            self._codec = self.request.kwargs["codec"]
        elif self.request.kwargs.get("output_params", None):
            ...
        else:
            self._codec = "libx264"
            if self.request.extension in (".mov", ".mp4", ".m4v"):
                ...
```

Whatever — libx264 for mp4 is standard.

Hmm, one risk: the environment might not have libx264 enabled in ffmpeg. imageio-ffmpeg ships a static ffmpeg with libx264. Should be fine.

Alternatively, to be safer, use `.avi` with mpeg4? But the function's param says .mp4 and the reader works on any path. Hmm, but the task says use realistic data — .mp4. Let's use .mp4.

Hmm, but actually — what if imageio-ffmpeg is NOT installed and imageio falls back to... nothing for mp4. Then this fails entirely and I should answer CANNOT RUN. But the repo imports imageio and uses it for mp4, so it must be installed. I'll go with it.

Now, another consideration: does imageio's ffmpeg writer require the frames to be the same size? Yes, all frames same size.

Let me now think about whether the reader returns frames in the expected count. I'll just trust.

Hmm, actually, wait. I realize there might be an issue with `fps=1` in the writer: imageio's ffmpeg writer passes `-r 1`. With `-r 1` output and input frames appended via stdin... Actually the writer pipes raw frames to ffmpeg with `-r 1` before `-i -`? Let's see: the command is like:

```
ffmpeg -y -f rawvideo -vcodec rawvideo -s WxH -pix_fmt rgb24 -r 1 -i - -an -vcodec libx264 -pix_fmt yuv420p out.mp4
```

So `-r 1` on input. That gives a 1fps video. Good.

Then reading with `fps=1`: if the reader adds `-r 1` on output, we get all frames.

Hmm, but if the reader's fps handling instead uses `-vf fps=1`... same result.

OK.

Now, one more: the number of frames the reader yields. If the video has 240 frames at 1 fps, duration 240s. Reading with fps=1 → 240 frames. Good.

Hmm, but what if the reader's fps semantics resample using `-r 1` and the input timestamps are exactly 1s apart — output should be identical frame count. Fine.

Let me now also double check: `imageio.get_reader(video_path, fps=1)` — the `fps` kwarg. If the plugin doesn't accept `fps`... it would raise TypeError. But the repo uses it, so it's accepted.

Now the outputs. `sample_images` returns `np.array(images)[idx]` — a view/copy of shape (n, H, W, 3). Comparisons fine.

Now let's think about total output values again:
1. 60 frames, 64×64, n=5 → 5*12288 = 61,440 ✓
2. 240 frames, 64×64, n=6 → 73,728 ✓
3. 5 frames, 64×64, n=12 → all 5 → 61,440 ✓
4. 8 frames, 64×64, n=8 → all 8 → 98,304 (borderline). Let's use 6 frames n=6 → 73,728. Hmm but then same as case 3 in size. Fine, different branch though (n==len → else). Actually with 5 frames and n=12, also else branch. Let's differentiate: case 3: 5 frames n=12; case 4: 7 frames n=7 → 86,016. Hmm.

Let's just do: case 4: 4 frames, 64×64, n=4 → 49,152, else branch (4 < 4 false).

Hmm, I want variety. Let's finalize:

1. "noise-60f-64x64-n5": 60 frames, 64×64, noise, n=5 → 61,440
2. "noise-240f-64x64-n6": 240 frames, 64×64, noise, n=6 → 73,728
3. "gradient-40f-64x64-n3": 40 frames, 64×64, gradient, n=3 → 36,864
4. "solid-8f-64x64-n8": 8 frames, 64×64, solid, n=8 → 98,304 → hmm.

Let me reduce: "solid-6f-64x64-n6" → 73,728 (else branch, n==len).

5. "single-30f-64x64-n1": 30 frames, 64×64, noise, n=1 → 12,288
6. "wide-50f-96x64-n5": 50 frames, 96×64, noise, n=5 → 5*18432 = 92,160 → borderline. Use n=4 → 73,728.
7. "tall-50f-64x96-n5": 50 frames, 64×96, gradient, n=5 → 92,160 → use n=4 → 73,728.
8. "hires-12f-128x128-n2": 12 frames, 128×128, noise, n=2 → 98,304 → use n=1 → 49,152. Hmm, or 128×96 → 36864 each, n=2 → 73,728.

Let me use 128×96 for hires, n=2 → 73,728.

Hmm, all outputs around 60-75k. That's fine.

Actually, let me reconsider the size budget: "keep what it returns (and anything it writes) under about 100 000 values". 73k is fine.

Now, is 64×64 too small for realism? Real videos are 1920×1080. But the budget forces small. It's fine — the constraint is explicit.

Hmm, but with tiny frames, the decode work is small; the dominant cost is ffmpeg startup. That's realistic enough.

Let me reconsider: maybe use larger frames with fewer sampled frames. E.g., 320×240 = 230,400 per frame — too big even for 1 frame. 160×120 = 57,600 per frame → 1 frame max. Hmm.

So 64×64 with 5-6 frames is a reasonable compromise.

OK. Now let's write the module-level code.

```python
import numpy as np
import imageio

_VIDEO_DIR = WORKDIR / "extract_images_videos"
_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _frame(kind, i, h, w, rng):
    if kind == "noise":
        return rng.randint(0, 256, size=(h, w, 3), dtype=np.uint8)
    if kind == "gradient":
        xs = np.linspace(0, 255, w)
        ys = np.linspace(0, 255, h)
        gx, gy = np.meshgrid(xs, ys)
        r = ((gx + i * 5) % 256).astype(np.uint8)
        g = gy.astype(np.uint8)
        b = (((gx + gy) / 2 + i * 3) % 256).astype(np.uint8)
        return np.stack([r, g, b], axis=-1)
    # solid
    c = np.array([(i * 37) % 256, (i * 91) % 256, (i * 53) % 256], dtype=np.uint8)
    return np.broadcast_to(c, (h, w, 3)).copy()


def _make_video(name, n_frames, h, w, seed, kind="noise"):
    path = _VIDEO_DIR / name
    if not path.exists():
        rng = np.random.RandomState(seed)
        writer = imageio.get_writer(str(path), fps=1, macro_block_size=1)
        try:
            for i in range(n_frames):
                writer.append_data(_frame(kind, i, h, w, rng))
        finally:
            writer.close()
    return str(path)
```

Hmm, `np.broadcast_to(...).copy()` gives a contiguous array. Fine.

Note: `writer.append_data` expects a numpy array of shape (h, w, 3) uint8. Good.

Now build videos at module level:

```python
_V_60_64 = _make_video("v60_64.mp4", 60, 64, 64, 0, "noise")
_V_240_64 = _make_video("v240_64.mp4", 240, 64, 64, 1, "noise")
_V_40_64 = _make_video("v40_64.mp4", 40, 64, 64, 2, "gradient")
_V_6_64 = _make_video("v6_64.mp4", 6, 64, 64, 3, "solid")
_V_30_64 = _make_video("v30_64.mp4", 30, 64, 64, 4, "noise")
_V_50_96 = _make_video("v50_96.mp4", 50, 96, 64, 5, "noise")
_V_50_64t = _make_video("v50_64t.mp4", 50, 64, 96, 6, "gradient")
_V_12_128 = _make_video("v12_128.mp4", 12, 128, 96, 7, "noise")
```

Wait, `_make_video(name, n_frames, h, w, ...)` — careful with the order of h and w in the frame shape. `rng.randint(0,256,(h,w,3))` → shape (h, w, 3). And imageio writer expects (h, w, 3). Good.

For "wide" I want width > height: h=64, w=96 → _make_video(..., 64, 96, ...). Let me rename params to (height, width).

Let me redo:

```python
_V_60_64 = _make_video("v60_64x64.mp4", 60, 64, 64, 0, "noise")
_V_240_64 = _make_video("v240_64x64.mp4", 240, 64, 64, 1, "noise")
_V_40_64 = _make_video("v40_64x64.mp4", 40, 64, 64, 2, "gradient")
_V_6_64 = _make_video("v6_64x64.mp4", 6, 64, 64, 3, "solid")
_V_30_64 = _make_video("v30_64x64.mp4", 30, 64, 64, 4, "noise")
_V_50_wide = _make_video("v50_64x96.mp4", 50, 64, 96, 5, "noise")
_V_50_tall = _make_video("v50_96x64.mp4", 50, 96, 64, 6, "gradient")
_V_12_hi = _make_video("v12_128x96.mp4", 12, 128, 96, 7, "noise")
```

Now cases:

```python
def cases():
    return [
        ("sample-5-of-60", lambda: (_V_60_64, 5)),
        ("sample-6-of-240", lambda: (_V_240_64, 6)),
        ("sample-3-of-40-gradient", lambda: (_V_40_64, 3)),
        ("all-6-frames", lambda: (_V_6_64, 6)),
        ("single-frame", lambda: (_V_30_64, 1)),
        ("wide-4-of-50", lambda: (_V_50_wide, 4)),
        ("tall-4-of-50", lambda: (_V_50_tall, 4)),
        ("hires-2-of-12", lambda: (_V_12_hi, 2)),
    ]
```

Output sizes:
1. 5*12288 = 61,440
2. 6*12288 = 73,728
3. 3*12288 = 36,864
4. 6*12288 = 73,728
5. 1*12288 = 12,288
6. 4*(64*96*3=18432) = 73,728
7. 4*(96*64*3=18432) = 73,728
8. 2*(128*96*3=36864) = 73,728

All good.

checks():

```python
def checks():
    return [
        ("zero-frames", lambda: (_V_6_64, 0)),
        ("one-frame-video", lambda: (_V_1_64, 1)),
        ("missing-file", lambda: (str(WORKDIR / "does_not_exist.mp4"), 4)),
    ]
```

Need a 1-frame video: `_V_1_64 = _make_video("v1_64x64.mp4", 1, 64, 64, 8, "noise")`.

Hmm, a 1-frame video at 1 fps: duration 1 second? ffmpeg might report 1 frame. Reading with fps=1... might give 1 frame. Should be fine.

Hmm, but there's risk: with a single frame, ffmpeg's `-r 1` output might produce 0 or 1 frames. If 0 frames, then `sample_images([], 1)`: `1 < 0` is False → `np.array([])` → empty array. Both versions same. Fine.

Actually, wait: for "zero-frames" check with _V_6_64 and n=0: `sample_images(frames, 0)` → `0 < 6` → idx = round(linspace(0,5,0)) = empty → `np.array(images)[empty]` → shape (0,64,64,3). Fine.

Hmm, but is that an "edge input"? Yes.

Now, one concern about the missing-file check: imageio might print errors to stderr and raise. Both versions raise identically. But could it hang? imageio's ffmpeg reader `_open` runs ffmpeg with the file; ffmpeg fails immediately and imageio raises RuntimeError. Should be quick.

Hmm, but actually, imageio might raise during `get_reader` itself (when opening the file to read metadata). Either way it raises.

Hmm, actually there's a risk: imageio's `get_reader` for a nonexistent file might raise a `FileNotFoundError` or an ffmpeg error. Fine.

Hmm, but I worry it could be slow (ffmpeg retries?). No.

Actually, let me reconsider — maybe safer to avoid the missing file and use another edge case. But the instructions say checks may raise. A missing file is a classic edge case. I'll keep it but... hmm, what if it raises a different exception type in the two versions? Both call the same imageio code, so same exception. Fine.

Let me keep it.

Now, about `WORKDIR` — it's provided as a module-level name. I use it at module level. Good.

One thing: the task says "Files: if the function reads files, create them under WORKDIR". Done.

Now, potential issue: the function is called many times; each call spawns ffmpeg. If the videos directory is created once at import, fine.

Another potential issue: imageio's ffmpeg reader might warn "IMAGEIO FFMPEG_WRITER WARNING: input image is not divisible by macro_block_size=16". We set macro_block_size=1, so no warning.

Hmm, actually: does `macro_block_size=1` work with libx264/yuv420p? x264 requires even dimensions for yuv420p (not multiples of 16). 64, 96, 128 are all even. Good. But imageio might still pad... with macro_block_size=1 it won't resize.

Hmm, actually imageio's writer uses `macro_block_size` to resize the input frames so that width and height are multiples of macro_block_size. With 1, no resize. Good.

Wait, but actually I recall imageio's ffmpeg writer has a check: if the image size isn't divisible by macro_block_size, it resizes with skimage or numpy. With macro_block_size=1, no resize needed.

OK.

Now let me double check `imageio.get_writer(str(path), fps=1, macro_block_size=1)` — the `fps` param for the ffmpeg writer. Yes, it's required-ish (default None → 10?). Actually imageio's ffmpeg writer default fps is 10 if not given? Let's pass fps=1 explicitly.

Hmm, one thought: with fps=1, the video's duration for 240 frames = 240 seconds. That's fine.

Hmm, but ffmpeg with `-r 1` and libx264... should be fine.

Now, will reading with `fps=1` give exactly 240 frames? If the reader applies `-r 1` output resampling on a 1fps input, yes.

Hmm, but here's a subtle thing: if the reader's `fps` param makes ffmpeg output at 1 fps, and the input is 1 fps, output = input frames. Good.

But what if the reader's fps param means something else entirely (e.g., it sets the input framerate to 1, so a 240-frame video at 1fps... same). Fine.

I'm reasonably confident.

Hmm, actually hold on. Let me reconsider whether imageio's ffmpeg reader even accepts `fps`. If it doesn't, `get_reader` would... Actually, imageio's `get_reader` passes kwargs to the plugin. The ffmpeg reader's `__init__` does `self._fps = request.kwargs.get("fps", None)`. So it accepts it. And the repo uses it. Good.

Now let me also double check: does the ffmpeg reader need `-r` handling... whatever.

Let me also handle the possibility that writing fails (no ffmpeg). Then the module-level code raises at import → the whole thing fails. Nothing I can do; I'll assume it works.

Hmm, actually, should I add a fallback? No — can't fake.

One more consideration: the "240 frames" video generation — encoding 240 frames of 64×64 noise. Fast.

Total frames encoded: 60+240+40+6+30+50+50+12+1 = 489. Fine.

Now, memory: each video file is small (64×64 noise compresses poorly, maybe ~50KB/frame → 240 frames → 12MB). Hmm, noise at 64×64 with libx264 at default CRF... maybe 3-5 KB/frame. Fine, well under 100MB.

Now let me write the final code.

One more detail: the thunk returns a tuple of positional args: `(video_path, number_frames)`. The function signature is `extract_images(video_path, number_frames)`. So positional works.

Let me write it.

```python
import numpy as np
import imageio

from embedding import extract_images  # not needed actually
```

Actually we don't need to import the function; the harness does. But importing is harmless. Actually, the task says "Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports." The task shows `from embedding import extract_images`. I don't need to import it since the harness calls it. But importing embedding might trigger heavy imports (torch, clip, vespa). Hmm — importing `embedding` imports torch, clip, vespa... that's heavy but the harness presumably does it already.

I'll not import embedding to avoid side effects. Actually, do I need it? No. The thunks just return args. So skip.

Hmm, but wait — the harness imports it. OK.

Let me write final code.

Actually, one concern: `_frame` for "gradient" — `gx` and `gy` from meshgrid with float linspace. `(gx + i*5) % 256` → float, astype uint8. Fine.

Let me make sure the arrays are uint8 C-contiguous for the writer.

`np.stack([r,g,b], axis=-1)` where r,g,b are uint8 → result uint8, contiguous. Good.

For solid: `np.broadcast_to(c, (h,w,3)).copy()` → uint8 contiguous. Good.

Now writing.

Also: should I worry that `imageio.get_writer` with a str path of a Path — fine.

Let me also add `if not path.exists()` guard so re-running the module doesn't rewrite. Actually the module is imported once. But harmless.

Hmm, one issue: if a previous run left a partial file, `exists()` would skip regeneration. Better to always write. But the harness runs once. I'll always write (overwrite).

Actually, "Anything the function writes must go under WORKDIR too" — the function doesn't write.

Let me finalize.

Wait, one more: the thunk for `checks` with the missing file — `str(WORKDIR / "does_not_exist.mp4")`. This path is not created. Good.

Also for checks, maybe add a `number_frames` larger than frames for a 1-frame video: n=5 on a 1-frame video → returns all 1 frame. Eh.

Let's finalize with 3 checks.

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
    writer = imageio.get_writer(str(path), fps=1, macro_block_size=1)
    try:
        for i in range(n_frames):
            writer.append_data(_frame(kind, i, height, width, rng))
    finally:
        writer.close()
    return str(path)
```

Hmm — `writer.append_data` with a non-contiguous array? They're contiguous.

Then videos.

OK, writing it all out now.

One last consideration on `macro_block_size`: if imageio's ffmpeg writer doesn't accept `macro_block_size` for some version... it does (it's a documented kwarg). Fine.

Actually, hmm, in older imageio the kwarg might be `macro_block_size` — yes, it's been there since 2.x. Good.

Let me write the final answer.