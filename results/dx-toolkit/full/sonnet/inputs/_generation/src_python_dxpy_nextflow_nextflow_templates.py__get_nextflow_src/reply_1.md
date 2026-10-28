```python
import random

from dxpy.nextflow.nextflow_templates import get_nextflow_src


def _make_inputs(n, seed, file_ratio=0.5, name_len=12):
    """Build a list of custom_inputs dicts as they come from a nextflow schema."""
    rng = random.Random(seed)
    classes = ["string", "int", "float", "boolean", "map"]
    inputs = []
    for i in range(n):
        name = "input_{}_{}".format(i, "x" * rng.randint(0, name_len))
        inp = {"name": name}
        if rng.random() < file_ratio:
            inp["class"] = "file"
        else:
            inp["class"] = rng.choice(classes)
        inputs.append(inp)
    return inputs


# Built once, reused by the thunks (the function only reads them).
_EMPTY = []
_FEW_FILE = _make_inputs(10, 1, file_ratio=1.0, name_len=8)
_MIXED_100 = _make_inputs(100, 2, file_ratio=0.5, name_len=15)
_FILES_200 = _make_inputs(200, 3, file_ratio=1.0, name_len=25)
_STRINGS_300 = _make_inputs(300, 4, file_ratio=0.0, name_len=30)
_MIXED_150 = _make_inputs(150, 5, file_ratio=0.7, name_len=12)
_MIXED_400 = _make_inputs(400, 6, file_ratio=0.5, name_len=20)
_FILES_400 = _make_inputs(400, 7, file_ratio=1.0, name_len=35)


def checks():
    return [
        ("none-args", lambda: (None,)),
        ("empty-list", lambda: (list(_EMPTY),)),
        ("single-file-input", lambda: ([{"name": "reads", "class": "file"}],)),
    ]


def cases():
    return [
        ("empty", lambda: (_EMPTY,)),
        ("profile-only", lambda: (_EMPTY, "test_profile")),
        ("few-file-inputs", lambda: (_FEW_FILE,)),
        ("mixed-100-with-resources", lambda: (_MIXED_100, "docker", "my_resources")),
        ("files-200", lambda: (_FILES_200,)),
        ("strings-300-abs-resources",
         lambda: (_STRINGS_300, "test_profile", "/abs/path/to/resources")),
        ("mixed-150-file-heavy", lambda: (_MIXED_150, "docker")),
        ("mixed-400-profile-resources",
         lambda: (_MIXED_400, "test_profile", "my_resources")),
    ]
```