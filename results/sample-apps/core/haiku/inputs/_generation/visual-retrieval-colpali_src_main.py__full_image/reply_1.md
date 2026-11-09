```python
import random
import main
from main import full_image

# Redirect IMG_DIR to a writable location under WORKDIR
main.IMG_DIR = WORKDIR / "full_images"
main.IMG_DIR.mkdir(parents=True, exist_ok=True)


def _write_file(doc_id, size, seed):
    rng = random.Random(seed)
    try:
        data = rng.randbytes(size)
    except AttributeError:
        data = bytes(rng.getrandbits(8) for _ in range(size))
    path = main.IMG_DIR / f"{doc_id}.jpg"
    with open(path, "wb") as f:
        f.write(data)
    return doc_id


# Create files for the measured cases (varied sizes -> varied base64 work)
_CASE_SIZES = [
    ("doc_64k", 64 * 1024),
    ("doc_128k", 128 * 1024),
    ("doc_256k", 256 * 1024),
    ("doc_512k", 512 * 1024),
    ("doc_1m", 1024 * 1024),
    ("doc_2m", 2 * 1024 * 1024),
    ("doc_4m", 4 * 1024 * 1024),
    ("doc_8m", 8 * 1024 * 1024),
]
for i, (doc_id, size) in enumerate(_CASE_SIZES):
    _write_file(doc_id, size, i)

# Create files for the edge-case checks
for doc_id, data in [("", b""), ("doc with spaces", b"x"), ("café", b"hello")]:
    path = main.IMG_DIR / f"{doc_id}.jpg"
    with open(path, "wb") as f:
        f.write(data)


def checks():
    return [
        ("empty-doc-id", lambda: ("",)),
        ("spaces", lambda: ("doc with spaces",)),
        ("unicode", lambda: ("café",)),
    ]


def cases():
    return [
        ("64KB", lambda: ("doc_64k",)),
        ("128KB", lambda: ("doc_128k",)),
        ("256KB", lambda: ("doc_256k",)),
        ("512KB", lambda: ("doc_512k",)),
        ("1MB", lambda: ("doc_1m",)),
        ("2MB", lambda: ("doc_2m",)),
        ("4MB", lambda: ("doc_4m",)),
        ("8MB", lambda: ("doc_8m",)),
    ]
```