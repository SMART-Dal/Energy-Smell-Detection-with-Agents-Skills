```python
import random
import main
from main import full_image

# The function reads IMG_DIR from its own module; point it at a writable
# directory under WORKDIR so we can create the image files it expects.
IMG_DIR = WORKDIR / "full_images"
IMG_DIR.mkdir(parents=True, exist_ok=True)
main.IMG_DIR = IMG_DIR


def _make_file(doc_id, size, seed=0):
    rng = random.Random(seed)
    data = rng.randbytes(size)
    path = IMG_DIR / f"{doc_id}.jpg"
    path.write_bytes(data)
    return doc_id


# Pre-create the files for the measured cases.  Sizes are chosen so that a
# single call (read + base64 encode) takes between roughly 1 ms and 200 ms.
_case_specs = [
    ("tiny", 1_000, 0),
    ("small", 10_000, 1),
    ("medium", 50_000, 2),
    ("large", 100_000, 3),
    ("xlarge", 200_000, 4),
    ("xxlarge", 500_000, 5),
    ("huge", 800_000, 6),
    ("max", 1_500_000, 7),
]
_case_ids = {}
for name, size, seed in _case_specs:
    doc_id = f"doc_{name}"
    _make_file(doc_id, size, seed)
    _case_ids[name] = doc_id

# Edge cases for checks().
_check_specs = [
    ("one-byte", "doc_onebyte", 1, 10),
    ("empty-doc-id", "", 0, 11),
    ("unicode-doc-id", "döc_ünicode", 10, 12),
]
for name, doc_id, size, seed in _check_specs:
    _make_file(doc_id, size, seed)


def checks():
    return [
        ("one-byte", lambda: (_check_specs[0][1],)),
        ("empty-doc-id", lambda: (_check_specs[1][1],)),
        ("unicode-doc-id", lambda: (_check_specs[2][1],)),
    ]


def cases():
    return [
        (name, lambda doc_id=_case_ids[name]: (doc_id,))
        for name, _, _ in _case_specs
    ]
```