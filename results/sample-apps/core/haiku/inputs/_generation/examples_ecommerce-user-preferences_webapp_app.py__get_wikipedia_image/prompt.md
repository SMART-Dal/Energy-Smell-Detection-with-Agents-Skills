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
Function under test: `get_wikipedia_image` in `examples/ecommerce-user-preferences/webapp/app.py`
Import it as `from app import get_wikipedia_image`.

## The function
```python
def get_wikipedia_image(make, model):
    """Fetch a relevant image URL from Wikipedia for a given make and model"""
    try:
        # Create a cache key
        cache_key = f"{make}_{model}".lower().replace(" ", "_")
        
        # Check if we already have this in the cache
        if cache_key in IMAGE_CACHE:
            print(f"Using cached image for {make} {model}")
            return IMAGE_CACHE[cache_key]
            
        print(f"Fetching image for {make} {model}")
        # Try direct search for car model first
        search_query = f"{make} {model} car"
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": search_query,
            "format": "json",
            "origin": "*"
        }
        
        print(f"Searching Wikipedia for: {search_query}")
        search_response = requests.get(
            search_url, params=search_params, headers=WIKIPEDIA_HEADERS, timeout=5
        )
        search_data = search_response.json()
        
        # If no search results, try a simpler query
        if not search_data.get("query", {}).get("search"):
            print(f"No results for {search_query}, trying just {make}")
            search_query = f"{make} car"
            search_params["srsearch"] = search_query
            search_response = requests.get(
                search_url, params=search_params, headers=WIKIPEDIA_HEADERS, timeout=5
            )
            search_data = search_response.json()
            
            if not search_data.get("query", {}).get("search"):
                print(f"No results for {search_query} either")
                return None
            
        # Get the first search result's page ID
        page_id = search_data["query"]["search"][0]["pageid"]
        print(f"Found Wikipedia page ID: {page_id}")
        
        # Get images from the page
        image_params = {
            "action": "query",
            "prop": "images",
            "pageids": page_id,
            "format": "json",
            "origin": "*"
        }
        
        image_response = requests.get(
            search_url, params=image_params, headers=WIKIPEDIA_HEADERS, timeout=5
        )
        image_data = image_response.json()
        
        # Check if we have any images
        images = image_data.get("query", {}).get("pages", {}).get(str(page_id), {}).get("images", [])
        if not images:
            print(f"No images found on page {page_id}")
            return None
            
        print(f"Found {len(images)} images on page")
        
        # Direct check for car images
        car_image_keywords = ["car", "vehicle", "automobile", "sedan", "suv", "truck", make.lower(), model.lower()]
        for image in images:
            title = image.get("title", "").lower()
            if any(keyword in title for keyword in car_image_keywords):
                # Get the actual image URL
                image_url_params = {
                    "action": "query",
                    "prop": "imageinfo",
                    "titles": image.get("title"),
                    "iiprop": "url",
                    "format": "json",
                    "origin": "*"
                }
                
                url_response = requests.get(
                    search_url,
                    params=image_url_params,
                    headers=WIKIPEDIA_HEADERS,
                    timeout=5,
                )
                url_data = url_response.json()
                
                # Extract the actual image URL
                pages = url_data.get("query", {}).get("pages", {})
                for page in pages.values():
                    if "imageinfo" in page and page["imageinfo"]:
                        image_url = page["imageinfo"][0].get("url")
                        if image_url:
                            print(f"Found image URL: {image_url}")
                            # Store in cache
                            IMAGE_CACHE[cache_key] = image_url
                            return image_url
        
        # If we didn't find a specific car image, try any image
        print("No car-specific images found, trying any image")
        for image in images:
            if not image.get("title", "").lower().endswith(('.svg', '.png', '.gif')):
                # Prefer JPG/JPEG images as they're more likely to be photos
                image_url_params = {
                    "action": "query",
                    "prop": "imageinfo",
                    "titles": image.get("title"),
                    "iiprop": "url",
                    "format": "json",
                    "origin": "*"
                }
                
                url_response = requests.get(
                    search_url,
                    params=image_url_params,
                    headers=WIKIPEDIA_HEADERS,
                    timeout=5,
                )
                url_data = url_response.json()
                
                # Extract the actual image URL
                pages = url_data.get("query", {}).get("pages", {})
                for page in pages.values():
                    if "imageinfo" in page and page["imageinfo"]:
                        image_url = page["imageinfo"][0].get("url")
                        if image_url and not image_url.lower().endswith(('.svg', '.png', '.gif')):
                            print(f"Found fallback image URL: {image_url}")
                            # Store in cache
                            IMAGE_CACHE[cache_key] = image_url
                            return image_url
        
        # Check if we have a generic fallback for this make
        make_key = make.lower().replace(" ", "_")
        for cached_key in IMAGE_CACHE:
            if cached_key.startswith(make_key + "_"):
                print(f"Using similar make image for {make} {model}")
                # Store this in the cache for this specific model too
                IMAGE_CACHE[cache_key] = IMAGE_CACHE[cached_key]
                return IMAGE_CACHE[cached_key]
        
        print(f"No images found for {make} {model}")
        return None
    except requests.exceptions.Timeout:
        print(f"Timeout while fetching image for {make} {model}")
        return None
    except Exception as e:
        print(f"Error fetching Wikipedia image for {make} {model}: {e}")
        return None
```

## Imports of its module
```python
from flask import Flask, render_template, request, jsonify, session
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import requests
```

## Definitions it uses from the same module
```python
IMAGE_CACHE = {
    # Pre-populate with hardcoded fallbacks for common car makes and models
    'toyota_camry': 'https://upload.wikimedia.org/wikipedia/commons/a/ac/2018_Toyota_Camry_%28ASV70R%29_Ascent_sedan_%282018-08-27%29_01.jpg',
    'tesla_model_3': 'https://upload.wikimedia.org/wikipedia/commons/9/91/2019_Tesla_Model_3_Performance_AWD_Front.jpg',
    'opel_corsa': 'https://upload.wikimedia.org/wikipedia/commons/6/69/2012_Opel_Corsa_%28CO%29_Enjoy_5-door_hatchback_%282015-11-11%29_01.jpg',
    'audi_a6': 'https://upload.wikimedia.org/wikipedia/commons/b/be/1998_Audi_A6_%284B%29_2.8_quattro_sedan_%282015-07-03%29.jpg',
    'audi_a3': 'https://upload.wikimedia.org/wikipedia/commons/a/a9/1997_Audi_A3_1.6_Front.jpg',
    'audi_q5': 'https://upload.wikimedia.org/wikipedia/commons/e/e4/2009-2010_Audi_Q5_%288R%29_2.0_TDI_quattro_wagon_01.jpg',
    'audi_a1': 'https://upload.wikimedia.org/wikipedia/commons/8/83/2013_Audi_A1_%288X_MY14%29_1.4_TFSI_Sport_S_line_Sportback_5-door_hatchback_%282015-08-07%29_01.jpg',
    'hyundai_i10': 'https://upload.wikimedia.org/wikipedia/commons/1/1c/2017_Hyundai_Grand_i10_Sedan.jpg',
    'ford_fiesta': 'https://upload.wikimedia.org/wikipedia/commons/e/e7/-68_Niclas_Gr%C3%B6nholm_-_Ford_Fiesta_ST_Supercar_-_World_Rallycross_2016_-_Lydden_Hill_%2826707937963%29.jpg',
    'opel_viva': 'https://upload.wikimedia.org/wikipedia/commons/a/aa/2016_Vauxhall_Viva_SE_1.0.jpg',
    'volkswagen_beetle': 'https://upload.wikimedia.org/wikipedia/commons/5/59/1949_VW_Beetle.jpg',
    'volkswagen_id._polo': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Volkswagen_ID._Polo_IAA_2025_DSC_1387.jpg',
}

WIKIPEDIA_HEADERS = {
    "User-Agent": "ecommerce-user-preferences/1.0 (contact: devnull@example.com)"
}
```

## Everything else its module defines (headers only)
```python
def load_system_prompt():
def extract_json_from_response(response):
def query_vespa(preferences, facet_filters=None):
def query_vespa_facets(preferences, facet_filters=None):
@app.route('/')
def index():
@app.route('/api/chat', methods=['POST'])
def chat():
@app.route('/api/update_preferences', methods=['POST'])
def update_preferences():
@app.route('/api/reset', methods=['POST'])
def reset_conversation():
@app.route('/api/car_image/<make>/<model>', methods=['GET'])
def get_car_image(make, model):
```

## Where the repository calls it or builds its class
```python
# examples/ecommerce-user-preferences/webapp/app.py:569
            return jsonify({"image_url": IMAGE_CACHE[cache_key], "from_cache": True})
        
        # Not in cache, try to get an image from Wikipedia
        print(f"Cache miss for {make} {model}, fetching from Wikipedia")
        image_url = get_wikipedia_image(make, model)
        
        if image_url:
            # Store in cache for future use
```

Write `checks()` and `cases()` for `get_wikipedia_image`. Remember: setup in the thunk or at module level, never timed.