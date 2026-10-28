You are a performance testing expert. You will write the inputs for an energy measurement of one Python function from a real repository. We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs.

# What to write
Python source defining two functions, `checks()` and `cases()`. Each returns a list of `(label, thunk)` pairs with distinct labels. A thunk takes no arguments and returns a tuple of positional arguments for the function, e.g. `lambda: (rows, 3)`. For keyword arguments the thunk returns `call(...)`, e.g. `lambda: call(rows, sep=",")`; `call` is provided, do not import or define it. A method is called as a plain function: the thunk builds the instance and passes it as the first argument (a classmethod gets its class there, a staticmethod nothing; the task says which).
**The thunk returns the arguments; it never calls the function under test.** We call the function with them, and time only that call.

# Instructions
1. **Setup is never timed**: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed.

2. **`cases()`: exactly 8 measured inputs.** We run them on the original function and keep the 4 that do the most work.
    - Define a real workload: the kind of data this function gets in this repository (see where the repository calls it). Use realistic scale and complexity, and a fixed random seed (`random.Random(0)`) when generating data.
    - Generate stressful inputs: complex, time-consuming, as diverse as possible. Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths.
    - Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes.
    - One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped. Keep the data in memory under about 100 MB, and building all inputs under about 10 s.
    - The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values.
    - Every case must run to completion on the original function without raising.

3. **`checks()`: 2 or 3 small edge inputs** (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise.

4. **Build real inputs; never replace code.** No mocks, no monkeypatching, no `unittest.mock`, no assigning functions or lambdas to attributes, and no subclass that overrides a method of a repository or library class -- a subclass whose `get` returns canned data instead of making the request is a mock too. Setting data (a module's configuration, an object's fields) to build an input is fine. No network access, no subprocesses. Do not fake the environment either: no stand-in programs on `PATH`, no fake system files.
    - Module globals the function reads must be set on the repository's own module (`import pricing; pricing.args = ...`, `hyperlink.slugs.update(...)`); a variable of the same name in your source is a different variable and the function never sees it.
    - Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk.

5. **Files**: if the function reads files, create them under `WORKDIR` (a provided `pathlib.Path`; do not define it), in module-level code or in the thunk. Anything the function writes must go under `WORKDIR` too.

6. **Same work on every call**: the call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts. So keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy (`list(data)`, `dict(data)`) if the function changes it (adds to a dict, sorts or fills a list in place). Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys (e.g. with `itertools.count()`), so every call takes the same path. If it creates files, have the thunk remove them first. No time-dependent or unseeded random behaviour.

7. Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports. Everything you can know about the repository is in the task: do not try to recall its code from memory, and build the inputs from the classes and functions shown there.

8. **If the function cannot run here at all** -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`. A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer.

Decide on the inputs and write the code: simple inputs that run are better than clever ones that do not.

# Output format
Exactly one ```python block holding the complete source. An example for a function `summarize(rows, top=10)`:
```python
import random

def _rows(n, columns, seed):
    rng = random.Random(seed)
    return [{f"c{j}": rng.randint(0, 10**6) for j in range(columns)} for _ in range(n)]

def checks():
    return [
        ("empty",      lambda: ([],)),                            # summarize([])
        ("none-value", lambda: ([{"c0": None}],)),
    ]

def cases():
    return [
        ("typical",    lambda: (_rows(2_000, 4, 0),)),            # summarize(rows)
        ("top-100",    lambda: call(_rows(5_000, 4, 1), top=100)), # summarize(rows, top=100)
        # ... 8 in total
    ]
```
A second example, for a method `Index.lookup(self, words)` of `search/index.py`. The instance is built in the thunk and passed first; the vocabulary file it reads is created under `WORKDIR`; a module setting it reads is set on the repository's own module; and because it records the words it has seen in `self.seen`, every thunk call gets words of its own, so that every call takes the same path:
```python
import itertools
import random
import search.index
from search.index import Index

search.index.CASE_SENSITIVE = False                  # a setting the method reads: data, set on its module
_VOCAB = WORKDIR / "vocab.txt"                       # a file it reads
_VOCAB.write_text("\n".join(f"w{i}" for i in range(50_000)))
_batch = itertools.count()

def _words(n, hit_ratio, seed):
    rng = random.Random(seed)
    b = next(_batch)                                 # fresh misses for every thunk call
    return [f"w{rng.randrange(50_000)}" if rng.random() < hit_ratio else f"x{b}_{i}"
            for i in range(n)]

def checks():
    return [("no-words", lambda: (Index(_VOCAB), []))]

def cases():
    return [
        ("mostly-hits",   lambda: (Index(_VOCAB), _words(20_000, 0.9, 0))),
        ("mostly-misses", lambda: (Index(_VOCAB), _words(20_000, 0.1, 1))),
        # ... 8 in total
    ]
```


=== USER ===

Repository: sample-apps
Function under test: `main` in `visual-retrieval-colpali/tests/huggingface_smoke.py`
Import it as `from huggingface_smoke import main`.

## The function
```python
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--load-model", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    # Resolve before changing into the source directory.
    env_file = args.env_file.resolve() if args.env_file else None
    if env_file and not env_file.is_file():
        parser.error(f"--env-file {args.env_file} does not exist")
    os.chdir(source)
    sys.path.insert(0, str(source))

    from dotenv import load_dotenv

    # Verify the Space SDK can be imported too.
    import gradio  # noqa: F401
    from starlette.testclient import TestClient
    import torch

    if env_file:
        load_dotenv(env_file)
    else:
        os.environ.update(
            {
                "USE_MTLS": "false",
                "VESPA_APP_TOKEN_URL": "https://example.invalid",
                "VESPA_CLOUD_SECRET_TOKEN": "test-token",
                "GEMINI_API_KEY": "test-key",
            }
        )

    with ExitStack() as stack:
        if not args.env_file:
            stack.enter_context(
                patch("vespa.application.Vespa.wait_for_application_up")
            )
        import main as app_module

        if not args.load_model:
            stack.enter_context(
                patch.object(
                    app_module, "SimMapGenerator", return_value=SimpleNamespace()
                )
            )
        with TestClient(app_module.app) as client:
            for route in ["/", "/about-this-demo", "/search"]:
                response = client.get(route)
                assert response.status_code == 200, route
            if args.load_model:
                # Mismatched transformers/colpali-engine versions can skip the
                # ColPali adapter weights, leaving the LoRA B matrices at zero.
                model = app_module.app.sim_map_generator.model
                lora_b = [p for n, p in model.named_parameters() if "lora_B" in n]
                assert lora_b and all(p.abs().sum() > 0 for p in lora_b), (
                    "ColPali adapter weights were not loaded"
                )
                embeddings, tokens = (
                    app_module.app.sim_map_generator.get_query_embeddings_and_token_map(
                        "return on investment"
                    )
                )
                assert embeddings.ndim == 2 and embeddings.shape[1] == 128
                assert torch.isfinite(embeddings).all() and tokens
    print("Hugging Face requirements install and app startup passed.")
    print("Gradio SDK:", importlib.metadata.version("gradio"))
    print("Real model loaded:", args.load_model)
```

## Imports of its module
```python
import argparse
from contextlib import ExitStack
import importlib.metadata
import os
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import patch
```

## Where the repository calls it or builds its class
```python
# visual-retrieval-colpali/tests/huggingface_smoke.py:84
    print("Real model loaded:", args.load_model)


if __name__ == "__main__":
    main()
```

Write `checks()` and `cases()` for `main`. Remember: setup in the thunk or at module level, never timed.