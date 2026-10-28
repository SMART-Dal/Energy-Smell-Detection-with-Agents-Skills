We need to write inputs for `_cleanup_empty_keys(json_spec)`. The function takes a JSON spec (dict) and removes empty keys. It uses regex sub on json.dumps, so we need realistic workflow specs with nested dicts, lists, empty values.

The function: `re.sub('\"\w*\": (null|\{\}|\"\"|\[\])(\,|)\s*','',json.dumps(json_spec)).replace(", }","}")` then json.loads.

Note the regex only matches keys that are word characters (no dots, no dashes, no spaces). So keys with dashes won't be cleaned. We should include such keys to exercise different paths.

We need 8 cases, realistic workflow specs from dxCompiler. Workflow specs have stages, inputs, outputs, etc. Let's build nested dicts with a mix of empty values (None, {}, "", []) and non-empty ones, keys with word chars and non-word chars, nested lists of dicts, etc.

Important: the function returns a new object (json.loads of the cleaned dump), so the input isn't mutated. But the thunk can return the same dict each time — since the function doesn't modify it. Actually it does json.dumps(json_spec) which doesn't modify. So we can reuse the same dict. But to be safe, we can return a copy? The instructions say if the function changes it, return a copy. It doesn't change. But it's cheap to return the same object. Let's just return the dict directly.

However, the arguments are rendered before and after each call to see if they changed. Rendering a big dict each call could be expensive but that's outside timing? Actually "Its arguments are rendered before and after each call" — that's part of the harness, not our timing. But it could be slow. Keep data under 1,000,000 values.

Let's design cases:

1. Typical workflow spec with many stages, each stage has empty fields.
2. Deeply nested spec.
3. Large flat dict with many empty keys.
4. Spec with keys containing dashes/dots (not matched by regex) plus empty values.
5. Spec with lists of dicts containing empties.
6. Spec with empty top-level keys.
7. Spec with repeated empty patterns and trailing commas issues.
8. Spec with strings that look like empty but shouldn't be removed (e.g., "null" string, "{}" string) — actually regex only matches `null`, `{}`, `""`, `[]` as literal values. A string value "null" would be `"null"` in JSON, which is `\"null\"` — the regex matches `null` not `"null"`. So a string "null" is safe. A string "{}" is `"{}"` — regex matches `\{\}` only unquoted. So safe.

Also keys with non-word characters like "foo-bar" won't be cleaned even if empty.

Let's write a generator for workflow specs.

We need to be careful about the regex behavior: it removes `"key": value` followed by optional comma and whitespace. The `.replace(", }", "}")` handles trailing commas. But if there are multiple empty keys in a row, the regex might leave issues? Let's test mentally: json.dumps({"a": None, "b": None}) -> `{"a": null, "b": null}`. Regex matches `"a": null, ` and removes it, leaving `{"b": null}`. Then replace does nothing. Fine.

What about `{"a": {}, "b": 1}` -> `{"a": {}, "b": 1}` -> removes `"a": {}, ` -> `{"b": 1}`. Fine.

What about `{"a": {"b": null}}` -> `{"a": {"b": null}}` -> removes `"b": null` -> `{"a": {}}`. Then the outer `"a": {}` is not removed because regex is applied once (re.sub replaces all non-overlapping matches in one pass, but the resulting `{}` from the inner removal is not rescanned). So nested empty dicts remain as `{}`. That's a known behavior. We should include such cases.

Let's build realistic dxCompiler workflow specs. A workflow spec looks like:
```json
{
  "name": "my_workflow",
  "version": "1.0.0",
  "stages": [
    {
      "id": "stage1",
      "name": "Stage 1",
      "executable": "applet-xxxx",
      "inputs": [...],
      "outputs": [...],
      "systemRequirements": {...},
      ...
    }
  ],
  ...
}
```

We can generate random specs with a seed.

Let's write a helper `_make_spec(seed, num_stages, depth, ...)`.

We need 8 cases with substantial work. Each call takes 1ms-200ms. json.dumps + regex + json.loads on a spec of maybe a few thousand nodes. Let's aim for specs with ~10k-100k values.

Let's write the code.

```python
import random
import json

def _rand_key(rng, i):
    # mix of word keys and keys with dashes/dots
    styles = [
        f"key{i}",
        f"key_{i}",
        f"key-{i}",
        f"key.{i}",
        f"Key{i}",
    ]
    return rng.choice(styles)

def _rand_value(rng, depth, empty_prob):
    if depth <= 0:
        return rng.choice([None, {}, "", [], 0, 1, "x", "null", "{}"])
    r = rng.random()
    if r < empty_prob:
        return rng.choice([None, {}, "", []])
    if r < empty_prob + 0.2:
        return rng.randint(0, 10**6)
    if r < empty_prob + 0.4:
        return "".join(rng.choice("abcdefgh") for _ in range(rng.randint(1, 20)))
    if r < empty_prob + 0.6:
        return [_rand_value(rng, depth - 1, empty_prob) for _ in range(rng.randint(0, 5))]
    return {_rand_key(rng, i): _rand_value(rng, depth - 1, empty_prob) for i in range(rng.randint(0, 6))}

def _make_spec(seed, num_stages, depth, empty_prob):
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
        for _ in range(rng.randint(0, 5)):
            stage["inputs"].append({
                "name": f"in{rng.randint(0, 1000)}",
                "class": rng.choice(["File", "string", "int", "boolean"]),
                "optional": rng.choice([True, False, None]),
                "default": rng.choice([None, "", {}, []]),
            })
        for _ in range(rng.randint(0, 5)):
            stage["outputs"].append({
                "name": f"out{rng.randint(0, 1000)}",
                "class": rng.choice(["File", "string", "int"]),
                "optional": rng.choice([True, False, None]),
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
    # add some random nested stuff
    for i in range(rng.randint(0, 20)):
        spec[_rand_key(rng, i)] = _rand_value(rng, depth, empty_prob)
    return spec
```

But we need to ensure the function runs without error. The regex might produce invalid JSON in some cases? Let's consider: if an empty value is the last key in an object, e.g. `{"a": null}` -> regex matches `"a": null` (no comma) -> removes it -> `{}`. Good. If there's a trailing comma issue: `{"a": 1, "b": null}` -> `{"a": 1, "b": null}` -> removes `"b": null` -> `{"a": 1, }` -> replace `, }` -> `{"a": 1}`. Good.

What about nested: `{"a": {"b": null, "c": 1}}` -> `{"a": {"b": null, "c": 1}}` -> removes `"b": null, ` -> `{"a": {"c": 1}}`. Good.

What if an empty value is followed by another empty value? `{"a": null, "b": null}` -> regex matches both? The regex is `\"\w*\": (null|\{\}|\"\"|\[\])(\,|)\s*`. It matches `"a": null, ` and `"b": null`. After removing both, we get `{}`. Good.

Potential issue: The regex `\w*` matches word characters. Keys with dashes won't match. So `"key-1": null` won't be removed. That's fine, it stays.

Potential issue with `.replace(", }", "}")`: if there's a comma followed by space and then `}`. This could occur if an empty key was removed leaving a trailing comma. But what if a non-empty value is followed by `, }` naturally? JSON dumps never produces `, }` because it doesn't have trailing commas. So it's safe.

What about a string value that contains `, }`? E.g. `{"a": "hello, }"}`. json.dumps produces `{"a": "hello, }"}`. The replace would turn it into `{"a": "hello}"}` which is a bug! But that's the function's behavior. We should include such a case to test the original's behavior. The instructions say we compare outputs, so any input is fine as long as it doesn't raise. It won't raise, it will just produce a different string. But we need the function to run to completion. It will. So we can include strings with `, }` to exercise that path.

Also strings with `"` etc.

Let's make sure the inputs don't cause json.loads to fail. The regex could theoretically produce invalid JSON if a key with a word char is removed but leaves something weird. Let's think: `{"a": null, "b": 1}` -> `{"b": 1}`. Fine. `{"a": {"b": null}, "c": 1}` -> `{"a": {}, "c": 1}`. Fine. `{"a": [null, {}]}` -> the regex matches `null` and `{}` inside the list? The regex pattern is `\"\w*\": (null|\{\}|\"\"|\[\])` — it requires a key before. Inside a list, there's no key, so `null` and `{}` are not matched. So `{"a": [null, {}]}` stays as is. Fine.

What about a key that is empty string? `"": null` — `\w*` matches zero word chars, so it matches `"": null`. That could be removed. That's fine.

So the function seems robust enough.

Now, we need 8 cases. Let's design them to be diverse:

1. **Typical workflow**: moderate size, many stages, mixed empties.
2. **Large flat dict**: many keys with empty values (tests regex performance).
3. **Deeply nested**: depth 8-10, many empty leaves.
4. **Many non-word keys**: keys with dashes/dots, empty values that won't be removed.
5. **Lists of dicts**: stages with many inputs/outputs, each with empty fields.
6. **Strings with tricky content**: values containing `, }`, `"`, `null`, `{}`, `[]` as strings.
7. **Empty-heavy**: almost everything empty, tests the replace and regex heavily.
8. **Mixed large**: combination of everything, big size.

We need each call to take 1ms-200ms. Let's estimate: json.dumps and json.loads on a dict with ~100k values might take ~50-100ms. That's within range. We'll aim for sizes that produce ~10k-50k values.

Let's write a function to count values to ensure under 1,000,000.

We'll generate specs at module level so thunks are cheap.

Let's write the code carefully.

```python
import random
import json

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
        return [_rand_value(rng, depth - 1, empty_prob) for _ in range(rng.randint(0, 8))]
    return {_rand_key(rng, i): _rand_value(rng, depth - 1, empty_prob) for i in range(rng.randint(0, 8))}

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
```

Now let's define the 8 cases:

1. `("typical", lambda: (_make_spec(0, 20, 3, 0.3, 50),))` — 20 stages, depth 3, 30% empty, 50 extra keys.
2. `("large-flat", lambda: ({f"key{i}": (None if i % 2 == 0 else i) for i in range(5000)},))` — 5000 keys, half empty. But keys are word chars, so regex will match them. This tests regex on many matches.
3. `("deep-nested", lambda: (_make_spec(1, 5, 8, 0.5, 200),))` — deep nesting.
4. `("non-word-keys", lambda: ({f"key-{i}": None if i % 3 == 0 else i for i in range(3000)},))` — keys with dashes, so regex won't match them. Also mixed.
5. `("lists-of-dicts", lambda: ([{"a": None, "b": {}, "c": "", "d": [], "e": 1} for _ in range(3000)],))` — top-level list of dicts.
6. `("tricky-strings", lambda: ({f"k{i}": "x, }y" if i % 2 == 0 else None for i in range(3000)},))` — strings containing `, }` and empty values.
7. `("empty-heavy", lambda: (_make_spec(2, 30, 4, 0.9, 100),))` — 90% empty.
8. `("mixed-large", lambda: (_make_spec(3, 40, 5, 0.4, 500),))` — large mixed.

We need to ensure the thunks are cheap. `_make_spec` is called at module level? The instructions say "build large data once, in module-level code, and have the thunk return it". So we should build the specs at module level and have the thunks return them. But the thunks are lambdas that call `_make_spec(...)` each time? That would rebuild the data each call, which is not timed but still runs before timing. However, the harness runs the thunk before each call, so if the thunk rebuilds the data, it's fine (not timed) but it's wasteful and might be slow. The instruction says "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it". So we should build at module level.

Let's build the specs at module level:

```python
_SPEC_TYPICAL = _make_spec(0, 20, 3, 0.3, 50)
_SPEC_LARGE_FLAT = {f"key{i}": (None if i % 2 == 0 else i) for i in range(5000)}
_SPEC_DEEP = _make_spec(1, 5, 8, 0.5, 200)
_SPEC_NON_WORD = {f"key-{i}": None if i % 3 == 0 else i for i in range(3000)}
_SPEC_LISTS = [{"a": None, "b": {}, "c": "", "d": [], "e": 1} for _ in range(3000)]
_SPEC_TRICKY = {f"k{i}": "x, }y" if i % 2 == 0 else None for i in range(3000)}
_SPEC_EMPTY_HEAVY = _make_spec(2, 30, 4, 0.9, 100)
_SPEC_MIXED_LARGE = _make_spec(3, 40, 5, 0.4, 500)
```

Then thunks: `lambda: (_SPEC_TYPICAL,)` etc.

But wait: the function does `json.dumps(json_spec)` which doesn't modify. So returning the same object is fine. However, the harness renders arguments before and after to check mutation. Rendering a large dict might be slow, but it's not our concern.

Now, `checks()`: 2-3 small edge inputs. These may raise. Let's include:
- empty dict `{}`
- a dict with a key that is empty string `{"": None}`
- a list `[]`? The function expects a dict, but json.dumps works on list too. The function would work on a list. But maybe the function expects a dict. Let's include a non-dict to see if it raises? It won't raise, json.dumps works on list. But we want edge cases. Let's do:
  - `("empty-dict", lambda: ({},))`
  - `("empty-string-key", lambda: ({"": None},))`
  - `("none", lambda: (None,))` — json.dumps(None) -> "null", regex doesn't match, json.loads("null") -> None. Works.

These are small and checked for identical behavior.

Now, let's verify the function's import. We need to import the module. The task says import it as `from dxpy.workflow_builder import _cleanup_empty_keys`. But the function under test is passed to the harness, so we don't need to import it ourselves? Actually, the harness likely imports it. The instructions say "Import the repository's modules exactly as shown in the task." So we should include the import? The example doesn't show importing the function under test; it shows importing the module for side effects (e.g., `import search.index`). But the task says "Import it as `from dxpy.workflow_builder import _cleanup_empty_keys`." That's probably for the harness. In our code, we might not need to import it, but we might need to set up module globals if the function reads them. `_cleanup_empty_keys` doesn't read any module globals. So we don't need to import the module. But to be safe, maybe we should import the module to ensure it's loaded? The harness will import it anyway. The example for `search.index` imports the module to set a global. Here, no globals needed.

However, the function's module imports a lot of stuff (dxpy, cli, etc.). Importing `dxpy.workflow_builder` might fail if dependencies aren't installed. But the task says we can import the repository's modules exactly as shown. The harness will import the function. So our code doesn't need to import it. We just write `checks()` and `cases()`.

Wait, the instructions: "Import the repository's modules exactly as shown in the task." That means if we need to access the module, we import it. But we don't need to. We just need to provide the inputs. The function under test is already imported by the harness. So we don't need to import anything from the repository. We only need `random` and `json` for building data.

But we should be careful: the function uses `re` and `json` inside. It imports `re` inside the function. So no issue.

Let's check if there's any risk of the regex causing a catastrophic failure. The regex is simple, no backtracking issues.

Now, let's think about the size. The function does `json.dumps` then regex sub then `json.loads`. For a spec with 5000 keys, json.dumps might take a few ms. For 40 stages with depth 5, it could be larger. Let's estimate the number of values in `_SPEC_MIXED_LARGE`. With 40 stages, each stage has up to 10 inputs and 10 outputs, each with 5 fields. That's 40 * 20 * 5 = 4000 values. Plus extra 500 keys with depth 5, each could have up to 8^5 = 32768 values? No, depth 5 with branching factor up to 8 could be huge. Let's control the size. Our `_rand_value` for dict uses `rng.randint(0, 8)` keys, and for list `rng.randint(0, 8)` elements. Depth 5 could explode. We need to keep it under 1,000,000 values. Let's cap the total size.

Actually, `_rand_value` with depth 5 and empty_prob 0.4: at each level, there's a chance of empty (0.4), scalar (0.15), string (0.2), list (0.2), dict (0.2). The expected branching factor for dict is 4, list 4. So depth 5 could be around 4^5 = 1024 per key. With 500 extra keys, that's 500k values. That might be too large. Let's reduce the branching factors or depth.

Let's modify `_rand_value` to have smaller branching factors: `rng.randint(0, 4)` for dict and list. And depth 5 is still 4^5 = 1024. 500 * 1024 = 512k. That's under 1M but might be slow (200ms+). Let's reduce extra_keys for the large case.

Better: we can measure the size by counting. Let's write a `_count_values` function and use it to ensure sizes are reasonable. But we can't run it here. We need to be conservative.

Let's set:
- `_SPEC_MIXED_LARGE`: num_stages=30, depth=4, empty_prob=0.4, extra_keys=200. With branching 4, depth 4 -> 4^4 = 256 per key. 200 * 256 = 51200. Plus stages: 30 * 20 * 5 = 3000. Total ~54k values. That's fine.
- `_SPEC_DEEP`: depth=7, but with branching 3. 3^7 = 2187 per key. extra_keys=50 -> 109k. Fine.
- `_SPEC_EMPTY_HEAVY`: empty_prob=0.9, so most are empty. Depth 4, branching 4. extra_keys=50. Size small.

Let's adjust `_rand_value`:

```python
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
```

Now, let's write the full code.

We need to ensure the function doesn't raise on any case. Let's think about `_SPEC_TRICKY`: keys `k0`, `k1`, etc. Values: for even i, `"x, }y"`, for odd i, `None`. The regex will match `"k1": null` and remove it. For `"k0": "x, }y"`, the value is a string, not matched. Then `.replace(", }", "}")` will replace the `, }` inside the string! So `"x, }y"` becomes `"x}y"`. That's fine, json.loads will parse it. No error.

What about `_SPEC_LISTS`: top-level is a list. json.dumps produces `[{"a": null, "b": {}, "c": "", "d": [], "e": 1}, ...]`. The regex matches `"a": null, `, `"b": {}, `, `"c": "", `, `"d": []` (no comma after because it's followed by `, "e"`? Wait: `"d": [], "e": 1` -> regex matches `"d": [], `? The pattern is `\"\w*\": (null|\{\}|\"\"|\[\])(\,|)\s*`. For `"d": []`, it matches `"d": []` and optionally a comma. Here after `[]` there is a comma, so it matches `"d": [], ` and removes it. Then we have `{"e": 1}`. Good.

What about `"c": ""`? The pattern `\"\"` matches empty string. So `"c": ""` is matched. Good.

What about `"b": {}`? Matched.

What about `"a": null`? Matched.

So the list of dicts will become `[{"e": 1}, ...]`. Fine.

Now, what about `_SPEC_LARGE_FLAT`: `{f"key{i}": (None if i % 2 == 0 else i) for i in range(5000)}`. Keys are `key0`, `key1`, etc. All word chars. Half are None. The regex will match `"key0": null, ` etc. It will remove them. The result will be a dict with only odd keys. That's a lot of matches. This tests regex performance.

What about `_SPEC_NON_WORD`: keys like `key-0`. The regex `\w*` matches `key` then expects `": "` but sees `-`, so it fails. So none of these empty values are removed. The function will just dump and load. This tests the path where regex doesn't match.

Now, checks: 
- `("empty-dict", lambda: ({},))`
- `("empty-string-key", lambda: ({"": None},))`
- `("none", lambda: (None,))`

These are small.

Let's write the final code. We need to import `random` and `json`? We use `json`? Actually we don't use `json` in our code except maybe for nothing. We use `random`. So just `import random`.

Wait, we need to ensure the thunks return a tuple. For a single argument, `lambda: (spec,)` is correct. The example shows `lambda: (rows,)` for a single argument. Yes.

Let's write the code.

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
_SPEC_DEEP = _make_spec(1, 5, 7, 0.5, 50)
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

Let's double-check the regex behavior with `_SPEC_TRICKY`. The key `k0` has value `"x, }y"`. json.dumps produces `{"k0": "x, }y", "k1": null, ...}`. The regex matches `"k1": null, ` and removes it. Then `.replace(", }", "}")` replaces the `, }` inside `"x, }y"` with `}`. So the string becomes `"x}y"`. That's fine. No error.

What about `_SPEC_LISTS`? The list contains dicts. json.dumps of a list of dicts. The regex will match keys inside the dicts. It will remove `"a": null, ` etc. Then the `.replace` might affect strings? There are no strings with `, }` in that spec. Fine.

What about `_SPEC_EMPTY_HEAVY`? empty_prob=0.9, so most values are empty. The regex will remove many. Fine.

Now, one concern: the function `_cleanup_empty_keys` uses `re.sub` with pattern `'\"\w*\": (null|\{\}|\"\"|\[\])(\,|)\s*'`. Note the pattern is a string with escaped quotes. In the function, it's `'\"\w*\": ...'`. The `\w` matches word chars. The `*` means zero or more. So it matches `""` as key too. Our `_SPEC_EMPTY_STRING_KEY` in checks uses `{"": None}`. The regex will match `"": null` and remove it, resulting in `{}`. That's fine.

Now, is there any case where the regex produces invalid JSON? Let's think: if an empty key is the only key, it becomes `{}`. If it's the last key, the trailing comma is removed by replace. If it's in the middle, the comma is consumed by the regex. What if there are two empty keys in a row? `{"a": null, "b": null, "c": 1}` -> regex matches `"a": null, ` and `"b": null, ` -> removes both -> `{"c": 1}`. Fine.

What if an empty key is followed by a non-empty key without a comma? That can't happen in JSON.

What if the value is `[]` and it's followed by `}`? `{"a": []}` -> regex matches `"a": []` (no comma) -> removes it -> `{}`. Fine.

What if the value is `""` and it's followed by `,`? `{"a": "", "b": 1}` -> regex matches `"a": "", ` -> removes it -> `{"b": 1}`. Fine.

So the function is robust.

Now, we need to ensure that the thunks return a tuple. For `_SPEC_LISTS`, it's a list, so `lambda: (_SPEC_LISTS,)` passes the list as the first argument. The function does `json.dumps(json_spec)`. json.dumps works on a list. So it's fine.

One more thing: the instructions say "The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values." Our outputs are the cleaned JSON, which is smaller than the inputs. The inputs themselves are under 1,000,000 values. Let's estimate the largest: `_SPEC_LARGE_FLAT` has 5000 keys. `_SPEC_LISTS` has 3000 dicts * 5 keys = 15000 values. `_SPEC_TRICKY` has 3000 keys. `_SPEC_MIXED_LARGE` with 30 stages, 200 extra keys, depth 4. Let's roughly estimate: 200 extra keys, each could have up to 4^4 = 256 values, so 51200. Plus stages: 30 * (20 * 5) = 3000. Total ~54k. That's fine. `_SPEC_DEEP` depth 7, 50 extra keys, branching 4: 4^7 = 16384 per key, 50 * 16384 = 819200. That's over 1,000,000? Actually 819,200 is close to 1M. But it's under 1M. However, it might be slow to build and the function might take >200ms. Let's reduce depth to 6 or reduce extra_keys. Let's set `_SPEC_DEEP` to depth 6, extra_keys=30. 4^6 = 4096. 30 * 4096 = 122880. That's safer. Also, the branching factor is random between 0 and 4, so the expected number of children is 2. So 2^6 = 64 per key. 30 * 64 = 1920. Actually, the expected branching factor for dict is `rng.randint(0, 4)` which has mean 2. So expected size is much smaller. The worst-case is 4^6 = 4096. So with 30 keys, worst-case 122880, expected much less. That's fine.

Let's adjust `_SPEC_DEEP` to `_make_spec(1, 5, 6, 0.5, 30)`.

Also `_SPEC_MIXED_LARGE`: depth 4, extra_keys=200. Worst-case 4^4 = 256, 200 * 256 = 51200. Expected much less. Fine.

Now, let's ensure the function runs without error on all cases. We can't run it, but we can reason. The only potential error is if json.loads fails due to invalid JSON produced by the regex. We've reasoned it's safe. But let's consider a case where a key contains a word char and the value is `null`, but the key is immediately followed by something that makes the regex match too much? The regex `\"\w*\": (null|\{\}|\"\"|\[\])(\,|)\s*` is greedy on `\w*` but that's fine. It matches the key and the value. It doesn't cross key boundaries.

What about a string value that contains `": null, `? For example, `{"a": "b\": null, c"}`. json.dumps would escape the quote: `{"a": "b\": null, c"}`. The regex looks for `"` followed by word chars followed by `": `. In the string, there is `\"` which is an escaped quote. The regex might match `"b\": null, `? Let's see: the pattern starts with `\"` which matches a literal double quote. In the JSON string, the escaped quote is `\"` which in the actual string is a backslash followed by a quote. The regex `\"` matches just the quote, not the backslash. So it might match the quote before `b`, then `\w*` matches `b`, then `\": ` expects `": ` but sees `\`? Actually the JSON string is `"b\": null, c"`. The characters are: `"` (start of string value), `b`, `\`, `"`, `:`, ` `, `n`, `u`, `l`, `l`, `,`, ` `, `c`, `"`. The regex `\"` matches the first `"` (start of string value). Then `\w*` matches `b`. Then `\": ` expects `"` followed by `:` followed by space. But the next characters are `\`, `"`, `:`. So `\"` would match the `"` after the backslash? Actually the pattern has `\"` which is a literal double quote. In the regex engine, `\"` is just `"`. So it would try to match `"` at the position after `b`. But the next character is `\`, not `"`. So it fails. It might backtrack? `\w*` could match zero characters, then `\"` matches the first `"`, then `\": ` expects `"` but sees `b`. So no match. So it's safe.

What about a string value that is exactly `null`? `{"a": "null"}` -> json.dumps: `{"a": "null"}`. The regex looks for `"a": null` (no quotes around null). It sees `"a": "null"` so the value is `"null"` not `null`. The pattern `(null|\{\}|\"\"|\[\])` matches `null` but the actual text is `"null"`, so the first character after `: ` is `"`, not `n`. So no match. Safe.

What about a key that is `null`? `{"null": 1}` -> regex looks for `"null": ` but the value is 1, not an empty value. So no match.

So the function is safe.

Now, let's write the final code. We'll include the import of `random` only. We don't need to import the function under test.

One more thing: the instructions say "For keyword arguments the thunk returns `call(...)`". We have no keyword arguments.

Also, "A method is called as a plain function: the thunk builds the instance and passes it as the first argument". This is a plain function, so just the argument.

Let's produce the final answer.