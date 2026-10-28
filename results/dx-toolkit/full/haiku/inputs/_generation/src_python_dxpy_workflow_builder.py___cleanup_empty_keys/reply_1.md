```python
import random

def _rand_key(rng, i):
    styles = [
        f"key{i}",
        f"key_{i}",
        f"key-{i}",
        f"key.{i}",
        f"Key{i}",
        f"k{i}",
    ]
    return rng.choice(styles)

def _rand_scalar(rng):
    return rng.choice([
        None, True, False, 0, 1, -1, 3.14,
        "", "a", "hello world", "null", "{}", "[]", "\"",
        "x, }y", "a,b", "  ", "\n",
    ])

def _rand_value(rng, depth, empty_prob):
    if depth <= 0:
        return _rand_scalar(rng)
    r = rng.random()
    if r < empty_prob:
        return rng.choice([None, {}, "", []])
    if r < empty_prob + 0.15:
        return _rand_scalar(rng)
    if r < empty_prob + 0.35:
        return "".join(rng.choice("abcdefghij") for _ in range(rng.randint(1, 30)))
    if r < empty_prob + 0.55:
        return [_rand_value(rng, depth - 1, empty_prob) for _ in range(rng.randint(0, 4))]
    return {_rand_key(rng, i): _rand_value(rng, depth - 1, empty_prob) for i in range(rng.randint(0, 4))}

def _make_spec(seed, num_stages, depth, empty_prob, extra_keys=0):
    rng = random.Random(seed)
    stages = []
    for s in range(num_stages):
        stage = {
            "id": f"stage{s}",
            "name": f"Stage {s}",
            "executable": f"applet-{rng.randint(0, 10**6)}",
            "inputs": [],
            "outputs": [],
            "systemRequirements": {},
            "folder": None,
            "ignoreReuse": None,
        }
        for _ in range(rng.randint(0, 10)):
            stage["inputs"].append({
                "name": f"in{rng.randint(0, 1000)}",
                "class": rng.choice(["File", "string", "int", "boolean"]),
                "optional": rng.choice([True, False, None]),
                "default": rng.choice([None, "", {}, []]),
                "help": rng.choice([None, "", "some help text"]),
            })
        for _ in range(rng.randint(0, 10)):
            stage["outputs"].append({
                "name": f"out{rng.randint(0, 1000)}",
                "class": rng.choice(["File", "string", "int"]),
                "optional": rng.choice([True, False, None]),
                "help": rng.choice([None, "", "some help text"]),
            })
        stages.append(stage)
    spec = {
        "name": f"workflow_{seed}",
        "version": "1.0.0",
        "stages": stages,
        "outputs": {},
        "inputs": {},
        "description": "",
        "developerNotes": None,
        "categories": [],
    }
    for i in range(extra_keys):
        spec[_rand_key(rng, i)] = _rand_value(rng, depth, empty_prob)
    return spec

# Build all inputs at module level so thunks are cheap.
_SPEC_TYPICAL = _make_spec(0, 20, 3, 0.3, 50)
_SPEC_LARGE_FLAT = {f"key{i}": (None if i % 2 == 0 else i) for i in range(5000)}
_SPEC_DEEP = _make_spec(1, 5, 6, 0.5, 30)
_SPEC_NON_WORD = {f"key-{i}": None if i % 3 == 0 else i for i in range(3000)}
_SPEC_LISTS = [{"a": None, "b": {}, "c": "", "d": [], "e": 1} for _ in range(3000)]
_SPEC_TRICKY = {f"k{i}": "x, }y" if i % 2 == 0 else None for i in range(3000)}
_SPEC_EMPTY_HEAVY = _make_spec(2, 30, 4, 0.9, 100)
_SPEC_MIXED_LARGE = _make_spec(3, 30, 4, 0.4, 200)

def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("empty-string-key", lambda: ({"": None},)),
        ("none", lambda: (None,)),
    ]

def cases():
    return [
        ("typical", lambda: (_SPEC_TYPICAL,)),
        ("large-flat", lambda: (_SPEC_LARGE_FLAT,)),
        ("deep-nested", lambda: (_SPEC_DEEP,)),
        ("non-word-keys", lambda: (_SPEC_NON_WORD,)),
        ("lists-of-dicts", lambda: (_SPEC_LISTS,)),
        ("tricky-strings", lambda: (_SPEC_TRICKY,)),
        ("empty-heavy", lambda: (_SPEC_EMPTY_HEAVY,)),
        ("mixed-large", lambda: (_SPEC_MIXED_LARGE,)),
    ]
```