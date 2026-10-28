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
Function under test: `SimMapGenerator._prepare_similarity_map_tensor` in `visual-retrieval-colpali/src/backend/colpali.py`
Import it as `from backend.colpali import SimMapGenerator`; the method is called as `SimMapGenerator._prepare_similarity_map_tensor(instance, ...)`.

## The function
```python
    def _prepare_similarity_map_tensor(
        self, query_embs: torch.Tensor, vespa_sim_maps: List[Dict]
    ) -> torch.Tensor:
        """
        Prepares a similarity map tensor from Vespa similarity maps.

        Args:
            query_embs (torch.Tensor): Query embeddings tensor.
            vespa_sim_maps (List[Dict]): List of Vespa similarity maps.

        Returns:
            torch.Tensor: The prepared similarity map tensor.
        """
        vespa_sim_map_tensor = torch.zeros(
            (len(vespa_sim_maps), query_embs.size(0), self.n_patch, self.n_patch)
        )
        for idx, vespa_sim_map in enumerate(vespa_sim_maps):
            for cell in vespa_sim_map["quantized"]["cells"]:
                patch = int(cell["address"]["patch"])
                query_token = int(cell["address"]["querytoken"])
                value = cell["value"]
                if hasattr(self.processor, "image_seq_length"):
                    image_seq_length = self.processor.image_seq_length
                else:
                    image_seq_length = 1024

                if patch >= image_seq_length:
                    continue
                vespa_sim_map_tensor[
                    idx,
                    query_token,
                    patch // self.n_patch,
                    patch % self.n_patch,
                ] = value
        return vespa_sim_map_tensor
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class SimMapGenerator:
    """
    Generates similarity maps based on query embeddings and image patches using the ColPali model.
    """
    colormap = cm.viridis  # Preload colormap for efficiency
    def __init__(
        self,
        logger: logging.Logger,
        model_name: str = "vidore/colpali-v1.2",
        n_patch: int = 32,
    ):
        """
        Initializes the SimMapGenerator class with a specified model and patch dimension.

        Args:
            model_name (str): The model name for loading the ColPali model.
            n_patch (int): The number of patches per dimension.
        """
        self.model_name = model_name
        self.n_patch = n_patch
        self.device = get_torch_device("auto")
        self.logger = logger
        self.logger.info(f"Using device: {self.device}")
        self.model, self.processor = self.load_model()
    def load_model(self) -> Tuple[ColPali, ColPaliProcessor]:
        """
        Loads the ColPali model and processor.

        Returns:
            Tuple[ColPali, ColPaliProcessor]: Loaded model and processor.
        """
        ...
    def gen_similarity_maps(
        self,
        query: str,
        query_embs: torch.Tensor,
        token_idx_map: Dict[int, str],
        images: List[Union[Path, str]],
        vespa_sim_maps: List[Dict],
    ) -> Generator[Tuple[int, str, str], None, None]:
        """
        Generates similarity maps for the provided images and query, and returns base64-encoded blended images.

        Args:
            query (str): The query string.
            query_embs (torch.Tensor): Query embeddings tensor.
            token_idx_map (dict): Mapping from indices to tokens.
            images (List[Union[Path, str]]): List of image paths or base64-encoded strings.
            vespa_sim_maps (List[Dict]): List of Vespa similarity maps.

        Yields:
            Tuple[int, str, str]: A tuple containing the image index, selected token, and base64-encoded image.
        """
        ...
    def _load_image(self, img: Union[Path, str]) -> Image:
        """
        Loads an image from a file path or a base64-encoded string.

        Args:
            img (Union[Path, str]): The image to load.

        Returns:
            Image: The loaded PIL image.
        """
        ...
    def _prepare_similarity_map_tensor(
        self, query_embs: torch.Tensor, vespa_sim_maps: List[Dict]
    ) -> torch.Tensor:
        """
        Prepares a similarity map tensor from Vespa similarity maps.

        Args:
            query_embs (torch.Tensor): Query embeddings tensor.
            vespa_sim_maps (List[Dict]): List of Vespa similarity maps.

        Returns:
            torch.Tensor: The prepared similarity map tensor.
        """
        vespa_sim_map_tensor = torch.zeros(
            (len(vespa_sim_maps), query_embs.size(0), self.n_patch, self.n_patch)
        )
        for idx, vespa_sim_map in enumerate(vespa_sim_maps):
            for cell in vespa_sim_map["quantized"]["cells"]:
                patch = int(cell["address"]["patch"])
                query_token = int(cell["address"]["querytoken"])
                value = cell["value"]
                if hasattr(self.processor, "image_seq_length"):
                    image_seq_length = self.processor.image_seq_length
                else:
                    image_seq_length = 1024

                if patch >= image_seq_length:
                    continue
                vespa_sim_map_tensor[
                    idx,
                    query_token,
                    patch // self.n_patch,
                    patch % self.n_patch,
                ] = value
        return vespa_sim_map_tensor
    def _blend_image(
        self, img: Image, sim_map: torch.Tensor, original_size: Tuple[int, int]
    ) -> str:
        """
        Blends an image with a similarity map and encodes it to base64.

        Args:
            img (Image): The original image.
            sim_map (torch.Tensor): The similarity map tensor.
            original_size (Tuple[int, int]): The original size of the image.

        Returns:
            str: The base64-encoded blended image.
        """
        ...
    @staticmethod
    def _normalize_sim_map(sim_map: np.ndarray) -> np.ndarray:
        """
        Normalizes a similarity map to range [0, 1].

        Args:
            sim_map (np.ndarray): The similarity map.

        Returns:
            np.ndarray: The normalized similarity map.
        """
        ...
    @staticmethod
    def should_filter_token(token: str) -> bool:
        """
        Determines if a token should be filtered out based on predefined patterns.

        The function filters out tokens that:

            - Start with '<' (e.g., '<bos>')
            - Consist entirely of whitespace
            - Are purely punctuation (excluding tokens that contain digits or start with '▁')
            - Start with an underscore '_'
            - Exactly match the word 'Question'
            - Are exactly the single character '▁'

        Output of test:
            Token: '2'         | False
            Token: '0'         | False
            Token: '2'         | False
            Token: '3'         | False
            Token: '▁2'        | False
            Token: '▁hi'       | False
            Token: 'norwegian' | False
            Token: 'unlisted'  | False
            Token: '<bos>'     | True
            Token: 'Question'  | True
            Token: ':'         | True
            Token: '<pad>'     | True
            Token: '\n'        | True
            Token: '▁'         | True
            Token: '?'         | True
            Token: ')'         | True
            Token: '%'         | True
            Token: '/)'        | True


        Args:
            token (str): The token to check.

        Returns:
            bool: True if the token should be filtered out, False otherwise.
        """
        ...
    @lru_cache(maxsize=128)
    def get_query_embeddings_and_token_map(
        self, query: str
    ) -> Tuple[torch.Tensor, dict]:
        """
        Retrieves query embeddings and a token index map.

        Args:
            query (str): The query string.

        Returns:
            Tuple[torch.Tensor, dict]: Query embeddings and token index map.
        """
        ...
```

## Imports of its module
```python
import torch
from PIL import Image
import numpy as np
from typing import Generator, Tuple, List, Union, Dict
from pathlib import Path
import base64
from io import BytesIO
import re
import io
import matplotlib.cm as cm
from colpali_engine.models import ColPali, ColPaliProcessor
from colpali_engine.utils.torch_utils import get_torch_device
from colpali_engine.interpretability.similarity_map_utils import normalize_similarity_map
from functools import lru_cache
import logging
```

## Where the repository calls it or builds its class
```python
# visual-retrieval-colpali/src/main.py:129


@app.on_event("startup")
def load_model_on_startup():
    app.sim_map_generator = SimMapGenerator(logger=logger)
    return



# visual-retrieval-colpali/src/backend/colpali.py:90
            original_images.append(img_pil.copy())
            original_sizes.append(img_pil.size)
            processed_images.append(img_pil)

        vespa_sim_map_tensor = self._prepare_similarity_map_tensor(
            query_embs, vespa_sim_maps
        )
        similarity_map_normalized = normalize_similarity_map(
            vespa_sim_map_tensor.flatten(0, 1)
        ).reshape(vespa_sim_map_tensor.shape)
```

Write `checks()` and `cases()` for `SimMapGenerator._prepare_similarity_map_tensor`. Remember: setup in the thunk or at module level, never timed.