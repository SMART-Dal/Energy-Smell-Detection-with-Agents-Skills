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
Function under test: `full_image` in `visual-retrieval-colpali/src/main.py`
Import it as `from main import full_image`.

## The function
```python
@app.get("/full_image")
async def full_image(doc_id: str):
    """
    Endpoint to get the full quality image for a given result id.
    """
    img_path = IMG_DIR / f"{doc_id}.jpg"
    if not os.path.exists(img_path):
        image_data = await vespa_app.get_full_image_from_vespa(doc_id)
        # image data is base 64 encoded string. Save it to disk as jpg.
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(image_data))
        logger.debug(f"Full image saved to disk for doc_id: {doc_id}")
    else:
        with open(img_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    return Img(
        src=f"data:image/jpeg;base64,{image_data}",
        alt="something",
        cls="result-image w-full h-full object-contain",
    )
```

## Imports of its module
```python
import asyncio
import base64
import os
import time
import uuid
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from google import genai
from google.genai import types
from fastcore.parallel import threaded
from fasthtml.common import (
    Aside,
    Div,
    FileResponse,
    HighlightJS,
    Img,
    JSONResponse,
    Link,
    Main,
    P,
    RedirectResponse,
    Script,
    StreamingResponse,
    fast_app,
)
from PIL import Image
from shad4fast import ShadHead
from vespa.application import Vespa
from backend.colpali import SimMapGenerator
from backend.vespa_app import VespaQueryClient
from frontend.app import (
    AboutThisDemo,
    ChatResult,
    Home,
    Search,
    SearchBox,
    SearchResult,
    SimMapButtonPoll,
    # ... (truncated)
```

## Definitions it uses from the same module
```python
logger = logging.getLogger("vespa_app")

vespa_app: Vespa = VespaQueryClient(logger=logger)

IMG_DIR = STATIC_DIR / "full_images"

@rt("/")
def get(session):
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return Layout(Main(Home()), is_home=True)
```

## Everything else its module defines (headers only)
```python
@app.on_event("startup")
def load_model_on_startup():
@app.on_event("startup")
async def keepalive():
def generate_query_id(query, ranking_value):
@rt("/static/{filepath:path}")
def serve_static(filepath: str):
def get_results_children(result):
async def poll_vespa_keepalive():
@threaded
def get_and_store_sim_maps(
    query_id, query: str, q_embs, ranking, idx_to_token, doc_ids
):
@app.get("/get_sim_map")
async def get_sim_map(query_id: str, idx: int, token: str, token_idx: int):
@rt("/suggestions")
async def get_suggestions(query: str = ""):
async def message_generator(query_id: str, query: str, doc_ids: list):
@app.get("/get-message")
async def get_message(query_id: str, query: str, doc_ids: str):
```

## Signatures of what its module imports from the repository
```python
# from backend.colpali import SimMapGenerator
class SimMapGenerator:
    colormap = cm.viridis  # Preload colormap for efficiency
    def __init__(
        self,
        logger: logging.Logger,
        model_name: str = "vidore/colpali-v1.2",
        n_patch: int = 32,
    ):
        """Initializes the SimMapGenerator class with a specified model and patch dimension."""
        ...
    def load_model(self) -> Tuple[ColPali, ColPaliProcessor]:
        """Loads the ColPali model and processor."""
        ...
    def gen_similarity_maps(
        self,
        query: str,
        query_embs: torch.Tensor,
        token_idx_map: Dict[int, str],
        images: List[Union[Path, str]],
        vespa_sim_maps: List[Dict],
    ) -> Generator[Tuple[int, str, str], None, None]:
        """Generates similarity maps for the provided images and query, and returns base64-encoded blended images."""
        ...
    @staticmethod
    def should_filter_token(token: str) -> bool:
        """Determines if a token should be filtered out based on predefined patterns."""
        ...
    @lru_cache(maxsize=128)
    def get_query_embeddings_and_token_map(
        self, query: str
    ) -> Tuple[torch.Tensor, dict]:
        """Retrieves query embeddings and a token index map."""
        ...

# from backend.vespa_app import VespaQueryClient
class VespaQueryClient:
    MAX_QUERY_TERMS = 64
    VESPA_SCHEMA_NAME = "pdf_page"
    SELECT_FIELDS = "id,title,url,blur_image,page_number,snippet,text"
    def __init__(self, logger: logging.Logger):
        """Initialize the VespaQueryClient by loading environment variables and establishing a connection to the Vespa application."""
        ...
    def get_fields(self, sim_map: bool = False):
        ...
    def format_query_results(
        self, query: str, response: VespaQueryResponse, hits: int = 5
    ) -> dict:
        """Format the Vespa query results."""
        ...
    async def query_vespa_bm25(
        self,
        query: str,
        q_emb: torch.Tensor,
        hits: int = 3,
        timeout: str = "10s",
        sim_map: bool = False,
        **kwargs,
    ) -> dict:
        """Query Vespa using the BM25 ranking profile."""
        ...
    def float_to_binary_embedding(self, float_query_embedding: dict) -> dict:
        """Convert float query embeddings to binary embeddings."""
        ...
    def create_nn_query_strings(
        self, binary_query_embeddings: dict, target_hits_per_query_tensor: int = 20
    ) -> Tuple[str, dict]:
        """Create nearest neighbor query strings for Vespa."""
        ...
    def format_q_embs(self, q_embs: torch.Tensor) -> dict:
        """Convert query embeddings to a dictionary of lists."""
        ...
    async def get_result_from_query(
        self,
        query: str,
        q_embs: torch.Tensor,
    # ... (truncated)

# from frontend.app import AboutThisDemo
def AboutThisDemo():
    ...

# from frontend.app import ChatResult
def ChatResult(query_id: str, query: str, doc_ids: Optional[list] = None):
    ...

# from frontend.app import Home
def Home():
    ...

# from frontend.app import Search
def Search(request, search_results=[]):
    ...

# from frontend.app import SearchBox
def SearchBox(with_border=False, query_value="", ranking_value="hybrid"):
    ...

# from frontend.app import SearchResult
def SearchResult(
    results: list,
    query: str,
    query_id: Optional[str] = None,
    search_time: float = 0,
    total_count: int = 0,
):
    ...

# from frontend.app import SimMapButtonPoll
def SimMapButtonPoll(query_id, idx, token, token_idx):
    ...

# from frontend.app import SimMapButtonReady
def SimMapButtonReady(query_id, idx, token, token_idx, img_src):
    ...

# from frontend.layout import Layout
def Layout(*c, is_home=False, **kwargs):
    ...
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `full_image`. Remember: setup in the thunk or at module level, never timed.