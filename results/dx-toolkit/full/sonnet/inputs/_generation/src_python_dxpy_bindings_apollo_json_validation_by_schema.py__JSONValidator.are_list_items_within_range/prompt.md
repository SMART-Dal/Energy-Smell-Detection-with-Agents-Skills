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

Repository: dx-toolkit
Function under test: `JSONValidator.are_list_items_within_range` in `src/python/dxpy/bindings/apollo/json_validation_by_schema.py`
Import it as `from dxpy.bindings.apollo.json_validation_by_schema import JSONValidator`; the method is called as `JSONValidator.are_list_items_within_range(instance, ...)`.

## The function
```python
    def are_list_items_within_range(
        self,
        input_json,
        key,
        start_subkey,
        end_subkey,
        window_width=250000000,
        check_each_separately=False,
    ):
        """
        This won't run by default when calling .validate() on a JSONValidator object. Run it separately when necessary
        """

        for item in input_json[key]:
            if int(item[end_subkey]) <= int(item[start_subkey]):
                self.error_handler(
                    "{} cannot be less than or equal to the {}".format(
                        end_subkey, start_subkey
                    )
                )

            if check_each_separately:
                if item[end_subkey] - item[start_subkey] > window_width:
                    self.error_handler(
                        "Range of {} and {} cannot be greater than {} for each item in {}".format(
                            start_subkey, end_subkey, window_width, key
                        )
                    )
        if not check_each_separately:
            # Check will be done across all items in the list
            # the entire search would be limited to window_width
            start_values = [int(item[start_subkey]) for item in input_json[key]]
            end_values = [int(item[end_subkey]) for item in input_json[key]]

            if max(end_values) - min(start_values) > window_width:
                self.error_handler(
                    "Range cannot be greater than {} for {}".format(window_width, key)
                )
```

## Its class, and the classes it inherits from here (other method bodies elided)
```python
class JSONValidator(object):
    """
    JSON validator class to validate a JSON against a schema.

    The schema is a dictionary with the following structure:

    {
        "key1": {
            "type": dict,
            "properties": {
                "name": {"type": str, "required": True},
                "attribute": {"type": str}
            }
        },
        "key2": {
            "type": dict,
            "properties": {
                "xyz": {"type": str},
                "abc": {"type": list}
            },
            "conflicting_keys": [["xyz", "abc"]]
        },
        "list_key_example": {
            "type": list,
            "items": {
                "type": dict,
                "properties": {
                    "nested_key1": {"type": str, "required": True},
                    "nested_key2": {"type": str}
                }
            }
        },
        "id": {
            "type": list,
        },
        "conflicting_keys": [["key1", "key2"]],
        "dependent_conditional_keys": {
            "list_key_example": ["key1", "key2"]
        }
    }

    Key types can be defined via the "type" key

    Required keys can be defined via the "required" key

    Conflicting keys can be defined via the "conflicting_keys" key, where the value is a list of lists of keys that are mutually exclusive.
    Conflicting keys can be defined at the level of the schema for the entire JSON or at key-level.
    In the example above, within "key2" the keys "xyz" and "abc" are mutually exclusive and cannot be present together.
    Similarly, at the level of the whole JSON, "key1" and "key2" are mutually exclusive and cannot be present together.

    Conditional key combinations can be defined via the dependent_conditional_keys at the level of the schema. These should be defined as a dict where the value is a list.
    In the example above, dependent_conditional_keys is defined as {"list_key_example": ["key1", "key2"]}, which means whenever list_key_example is present, either "key1"
    or "key2" has to be also present.

    Currently the maximum level of nestedness supported for validation is as deep as shown in the example above via the "list_key_example" key.

    This is an example of a valid JSON that satisfies all the conditions defined in the schema above:

    {
        "key1": {
            "name": "test",
        },
        "list_key_example": [
            {"nested_key1": "1", "nested_key2": "2"},
            {"nested_key1": "3", "nested_key2": "4"},
            {"nested_key1": "5"}
        ],
        "id": ["id_1", "id_2"]
    }

    """
    def __init__(self, schema, error_handler=print):
        self.schema = schema
        self.error_handler = error_handler

        if not isinstance(schema, dict) or not schema:
            error_handler("Schema must be a non-empty dict.")
    def validate(self, input_json):
        ...
    def validate_types(self, input_dict):
        ...
    def validate_properties(self, properties, input_dict):
        ...
    def validate_list_items(self, item_schema, input_list, key_name):
        ...
    def check_incompatible_subkeys(self, input_json, current_key):
        ...
    def check_incompatible_keys(self, input_json):
        ...
    def check_dependent_key_combinations(
        self, input_json, enforce_one_associated_key=False
    ):
        ...
    def error_on_invalid_keys(self, input_json):
        ...
    def are_list_items_within_range(
        self,
        input_json,
        key,
        start_subkey,
        end_subkey,
        window_width=250000000,
        check_each_separately=False,
    ):
        """
        This won't run by default when calling .validate() on a JSONValidator object. Run it separately when necessary
        """

        for item in input_json[key]:
            if int(item[end_subkey]) <= int(item[start_subkey]):
                self.error_handler(
                    "{} cannot be less than or equal to the {}".format(
                        end_subkey, start_subkey
                    )
                )

            if check_each_separately:
                if item[end_subkey] - item[start_subkey] > window_width:
                    self.error_handler(
                        "Range of {} and {} cannot be greater than {} for each item in {}".format(
                            start_subkey, end_subkey, window_width, key
                        )
                    )
        if not check_each_separately:
            # Check will be done across all items in the list
            # the entire search would be limited to window_width
            start_values = [int(item[start_subkey]) for item in input_json[key]]
            end_values = [int(item[end_subkey]) for item in input_json[key]]

            if max(end_values) - min(start_values) > window_width:
                self.error_handler(
                    "Range cannot be greater than {} for {}".format(window_width, key)
                )
```

## Imports of its module
```python
from __future__ import print_function
```

## Where the repository calls it or builds its class
```python
# src/python/test/test_extract_expression.py:213
    #

    def common_negative_filter_test(self, json_name, expected_error_message):
        input_json = CLIEXPRESS_TEST_INPUT["malformed"][json_name]
        validator = JSONValidator(
            self.json_schema, error_handler=self.json_error_handler
        )

        with self.assertRaises(ValueError) as cm:
            validator.validate(input_json)

# src/python/test/test_extract_expression.py:225

    def common_positive_filter_test(self, json_name):
        input_json = CLIEXPRESS_TEST_INPUT["valid"][json_name]

        validator = JSONValidator(
            self.json_schema, error_handler=self.json_error_handler
        )

        validator.validate(input_json)


# src/python/dxpy/cli/dataset_utilities.py:1557

    # In case --sql flag is provided but no input json, function should return all data
    if user_filters_json:
        # Validate filters JSON provided by the user according to a predefined schema
        input_json_validator = JSONValidator(
            schema=EXTRACT_ASSAY_EXPRESSION_JSON_SCHEMA, error_handler=err_exit
        )
        input_json_validator.validate(input_json=user_filters_json)



# src/python/dxpy/cli/dataset_utilities.py:1601
                "location"
            ]["max_item_limit"] = None
        else:
            # Genomic range adding together across multiple contigs should be smaller than 250 Mbps
            input_json_validator.are_list_items_within_range(
                input_json=user_filters_json,
                key="location",
                start_subkey="starting_position",
                end_subkey="ending_position",
                window_width=250000000,
                check_each_separately=False,
            )
    input_json_parser = JSONFiltersValidator(
        input_json=user_filters_json,
        schema=filter_schema,
```

Write `checks()` and `cases()` for `JSONValidator.are_list_items_within_range`. Remember: setup in the thunk or at module level, never timed.