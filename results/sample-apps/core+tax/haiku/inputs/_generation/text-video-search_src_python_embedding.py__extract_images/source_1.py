import numpy as np
import imageio

# ---------------------------------------------------------------------------
# Real .mp4 files, written under WORKDIR (the function reads them with imageio)
# ---------------------------------------------------------------------------
_VIDEO_DIR = WORKDIR / "extract_images_videos"
_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _frame(kind, i, height, width, rng):
    """Build one deterministic frame of the requested flavour."""
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
    # "solid": a flat colour that changes from frame to frame
    c = np.array([(37 * i) % 256, (91 * i) % 256, (53 * i) % 256], dtype=np.uint8)
    return np.broadcast_to(c, (height, width, 3)).copy()


def _make_video(name, n_frames, height, width, seed, kind="noise"):
    """Encode a real mp4 at 1 fps so that imageio's fps=1 reader yields every frame."""
    path = _VIDEO_DIR / name
    rng = np.random.RandomState(seed)
    writer = imageio.get_writer(str(path), fps=1, macro_block_size=1)
    try:
        for i in range(n_frames):
            writer.append_data(_frame(kind, i, height, width, rng))
    finally:
        writer.close()
    return str(path)


# 8 measured workloads (all kept small enough that the returned array of frames
# stays well below ~100k values, while the decoding work is real).
_V_60_64 = _make_video("v60_64x64.mp4", 60, 64, 64, 0, "noise")
_V_240_64 = _make_video("v240_64x64.mp4", 240, 64, 64, 1, "noise")
_V_40_64 = _make_video("v40_64x64.mp4", 40, 64, 64, 2, "gradient")
_V_6_64 = _make_video("v6_64x64.mp4", 6, 64, 64, 3, "solid")
_V_30_64 = _make_video("v30_64x64.mp4", 30, 64, 64, 4, "noise")
_V_50_wide = _make_video("v50_64x96.mp4", 50, 64, 96, 5, "noise")
_V_50_tall = _make_video("v50_96x64.mp4", 50, 96, 64, 6, "gradient")
_V_12_hi = _make_video("v12_128x96.mp4", 12, 128, 96, 7, "noise")

# small helper videos used only by checks()
_V_1_64 = _make_video("v1_64x64.mp4", 1, 64, 64, 8, "noise")


def checks():
    return [
        # number_frames == 0 -> empty sample (still goes through the sampling branch)
        ("zero-frames", lambda: (_V_6_64, 0)),
        # a one frame video, asking for one frame
        ("one-frame-video", lambda: (_V_1_64, 1)),
        # missing file: both versions must fail the same way
        ("missing-file", lambda: (str(WORKDIR / "does_not_exist.mp4"), 4)),
    ]


def cases():
    return [
        # sampling branch, moderate video, moderate sample
        ("sample-5-of-60", lambda: (_V_60_64, 5)),
        # long video (240 frames decoded), 6 sampled frames
        ("sample-6-of-240", lambda: (_V_240_64, 6)),
        # gradient content, small sample from 40 frames
        ("sample-3-of-40-gradient", lambda: (_V_40_64, 3)),
        # number_frames == len(frames) -> the "return everything" branch
        ("all-6-frames", lambda: (_V_6_64, 6)),
        # number_frames == 1 -> single frame out of 30
        ("single-frame", lambda: (_V_30_64, 1)),
        # wide frames (64x96)
        ("wide-4-of-50", lambda: (_V_50_wide, 4)),
        # tall frames (96x64)
        ("tall-4-of-50", lambda: (_V_50_tall, 4)),
        # higher resolution (128x96), few sampled frames
        ("hires-2-of-12", lambda: (_V_12_hi, 2)),
    ]
