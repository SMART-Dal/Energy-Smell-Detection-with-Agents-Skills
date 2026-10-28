```python
import random
import main
from main import full_image

# The function reads IMG_DIR / f"{doc_id}.jpg". Point it at a writable dir under
# WORKDIR and set it on the exact function's globals so the file-exists branch
# (the real local work: read + base64-encode) is taken every call.
_IMG_DIR = WORKDIR / "full_images"
_IMG_DIR.mkdir(parents=True, exist_ok=True)

main.IMG_DIR = _IMG_DIR
try:
    full_image.__globals__["IMG_DIR"] = _IMG_DIR
except Exception:
    pass


def _rand_bytes(rng, n):
    try:
        return rng.randbytes(n)
    except AttributeError:
        return bytes(rng.getrandbits(8) for _ in range(n))


def _make(doc_id, size, seed):
    rng = random.Random(seed)
    with open(_IMG_DIR / f"{doc_id}.jpg", "wb") as f:
        f.write(_rand_bytes(rng, size))
    return doc_id


# Eight varied, realistic image sizes -> varied base64-encode workloads.
_CASE_SIZES = [
    ("doc_64k", 64 * 1024),
    ("doc_192k", 192 * 1024),
    ("doc_384k", 384 * 1024),
    ("doc_768k", 768 * 1024),
    ("doc_1m", 1024 * 1024),
    ("doc_2m", 2 * 1024 * 1024),
    ("doc_3m", 3 * 1024 * 1024),
    ("doc_5m", 5 * 1024 * 1024),
]
for _i, (_doc_id, _size) in enumerate(_CASE_SIZES):
    _make(_doc_id, _size, _i)

# Edge-case files (small) for behavioural checks.
for _doc_id, _data in [("", b""), ("doc with spaces", b"x"), ("café", b"hello")]:
    with open(_IMG_DIR / f"{_doc_id}.jpg", "wb") as _f:
        _f.write(_data)


def checks():
    return [
        ("empty-doc-id", lambda: ("",)),
        ("spaces", lambda: ("doc with spaces",)),
        ("unicode", lambda: ("café",)),
    ]


def cases():
    return [
        ("64KB", lambda: ("doc_64k",)),
        ("192KB", lambda: ("doc_192k",)),
        ("384KB", lambda: ("doc_384k",)),
        ("768KB", lambda: ("doc_768k",)),
        ("1MB", lambda: ("doc_1m",)),
        ("2MB", lambda: ("doc_2m",)),
        ("3MB", lambda: ("doc_3m",)),
        ("5MB", lambda: ("doc_5m",)),
    ]
```