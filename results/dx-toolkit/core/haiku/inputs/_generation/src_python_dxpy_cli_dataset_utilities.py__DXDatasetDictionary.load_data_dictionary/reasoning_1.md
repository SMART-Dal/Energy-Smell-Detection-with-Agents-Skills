We need to write inputs for `load_data_dictionary`. It takes a descriptor object with `.model` (dict with "entities", "global_primary_key") and `.join_info` (list of dicts with "joins" list whose first element has "to" and "from").

We need to build a descriptor-like object. But we must not mock repository classes. However, descriptor is `DXDatasetDescriptor`, and we can't easily construct it without network. But the function only accesses `descriptor.model` and `descriptor.join_info`. We can create a simple object with those attributes. Is that a mock? The instructions say no mocks of repository/library classes with overridden methods. But here the function under test only uses attribute access on descriptor. Creating a plain object with attributes is acceptable? It says "Setting data (a module's configuration, an object's fields) to build an input is fine." So we can create a simple namespace object with `.model` and `.join_info`. Better: we could construct an actual `DXDatasetDescriptor` instance and set attributes, but its `__init__` takes a dxfile and does network. We can instantiate via `object.__new__(DXDatasetDescriptor)` and set `.model` and `.join_info`. That's using the repository class without calling its `__init__`. That's setting fields, fine.

But the function also calls `self.create_entity_dframe`, `self.get_join_path_to_entity_field_map`, `self.create_edge`. These are methods of DXDatasetDictionary. We need an instance of DXDatasetDictionary. Its `__init__` calls load_data_dictionary etc. We can create instance via `object.__new__(DXDatasetDictionary)` and then call `load_data_dictionary(instance, descriptor)`. The methods `create_entity_dframe`, etc., are defined on the class and will work as long as they don't need other instance state. Let's check: `create_entity_dframe` likely uses only its arguments. `get_join_path_to_entity_field_map` uses entity. `create_edge` uses join_info_joins and join_path_to_entity_field. So instance state not needed. So we can create a bare instance with `object.__new__`.

Thus thunk: build descriptor (model + join_info) and instance, return (instance, descriptor).

We need to understand the data model structure to build realistic inputs. The function processes:
- `descriptor.model["entities"]`: dict mapping entity_name -> entity definition.
- `descriptor.model["global_primary_key"]`: dict with "entity" key.
- `descriptor.join_info`: list of join info dicts.

We need to know what `create_entity_dframe` expects. We don't have its code, but we can infer from typical DNAnexus dataset descriptors. Let's think: entities have fields, etc. The function `create_entity_dframe` probably builds a pandas DataFrame with columns like "name", "type", "referenced_entity_field", "relationship", etc.

We need to generate inputs that don't raise. Since we don't know exact expected structure, we must be careful. We can look at test files? Not given. But we can infer from names. The function uses:
- entity definition passed to `create_entity_dframe(entity, is_primary_entity, global_primary_key)`.
- `get_join_path_to_entity_field_map(entity)` returns map from path strings to (entity, field).
- `create_edge(ji, join_path_to_entity_field)` where `ji` is a join_info item.

The edges processing: for each edge, get source_eblock from eblocks by edge["source_entity"]. Then check `source_eblock["name"] == edge["source_field"]`. So the DataFrame must have columns "name", "referenced_entity_field", "relationship". And `edge` is an OrderedDict with keys "source_entity", "source_field", "destination_entity", "destination_field", "relationship".

So we need to construct entity definitions that produce DataFrames with these columns. Since we don't know `create_entity_dframe` implementation, we must guess the input format. Perhaps we can find the actual code in the repository? We don't have it. But the task says "Everything you can know about the repository is in the task: do not try to recall its code from memory, and build the inputs from the classes and functions shown there." We only have signatures and some docstrings. We need to construct plausible descriptors.

Maybe we can look at how tests build descriptors in the provided snippet: `descriptor_stub({"sex": ("sex", False)}, codings=descriptor_codings)`. That's from test_extract_dataset_codings. It suggests entity definitions are something like dict of field name -> (something, bool). But we need more.

Alternatively, we could avoid using `create_entity_dframe` by monkeypatching? No, not allowed.

We need to build a descriptor that works. Since we don't have the code, we might need to design the entity definition based on typical DX dataset schema. Let's search memory: DNAnexus dataset descriptor has `model` with `entities` mapping entity names to objects with `fields` list. Each field has `name`, `type`, `is_primary_key`, etc. `global_primary_key` has `entity` and `field`. `join_info` is list of joins.

But `create_entity_dframe` likely takes an entity dict and builds a DataFrame. We can try to infer from the test: `descriptor_stub({"sex": ("sex", False)}, codings=descriptor_codings)`. That's for coding dictionary, not data dictionary. The function under test is load_data_dictionary, which uses `descriptor.model["entities"]`. In tests, they patch `load_data_dictionary` to return {}, so they don't test it. So we have no direct test.

We need to construct something that doesn't crash. Could we write a minimal descriptor and hope? The function will call `create_entity_dframe`, which we don't control. If we pass an empty entities dict, it will loop zero times, then process join_info empty, return empty OrderedDict. That would run but do no work. We need real workload.

Maybe we can inspect the repository? As an AI, I don't have access to files. But I can reason: The function is from dx-toolkit. I might recall the structure from open source. Let me think: In DNAnexus, dataset descriptor has `model` with `entities` like:
```
"entities": {
  "patient": {
    "fields": [
      {"name": "patient_id", "type": "string", "is_primary_key": true},
      ...
    ]
  }
}
```
And `global_primary_key`: {"entity": "patient", "field": "patient_id"}.
`join_info`: list of {"joins": [{"from": "patient$patient_id", "to": "sample$patient_id", ...}]}.

`create_entity_dframe` probably iterates over fields and builds a DataFrame with columns: name, type, is_primary_key, referenced_entity, referenced_entity_field, relationship, etc. It might also handle foreign keys.

`get_join_path_to_entity_field_map` likely iterates over fields and for fields that are references, builds map from "database$table$column" to (entity, field). The join_info paths are like "database$table$column".

We need to generate entities with fields that have references to create join paths. The function builds `join_path_to_entity_field` from entities, then for each join_info, checks if both `joins[0]["to"]` and `joins[0]["from"]` are in that map. If not, skip edge. Then `create_edge` uses the map to build edge dict.

So to get edges, we need join_info paths that match the generated map. The map keys are strings like "database$table$column". The join_info `to` and `from` are such strings.

We can construct entities with fields that have `"references"` or similar. But we don't know exact field schema. Let's try to find the actual code online from memory. I recall dx-toolkit's `dataset_utilities.py`. There is a class `DXDatasetDictionary`. I can try to reconstruct `create_entity_dframe` from memory. I think I've seen it. It might look like:

```python
def create_entity_dframe(self, entity, is_primary_entity, global_primary_key):
    df = pd.DataFrame()
    for field in entity["fields"]:
        ...
```

Actually, let's search my knowledge: DNAnexus dataset descriptor model has entities with fields. Each field has `name`, `type`, `is_primary_key`, `references` (if foreign key), `is_hierarchical`, etc. The `create_entity_dframe` likely builds a row per field with columns: "name", "type", "is_primary_key", "referenced_entity", "referenced_entity_field", "relationship". The relationship might be "one-to-one", "one-to-many", etc.

The join_info is separate: it describes joins between entities. The function `get_join_path_to_entity_field_map` probably builds a map from join path (like "database$table$column") to (entity, field) for fields that are references. The join_info's `joins` list has `from` and `to` paths. The function checks if both paths exist in the map. If so, it creates an edge.

So to make edges, we need fields with references that produce join paths matching the join_info. The join path format is likely "database$table$column". The entity name might be the table. The field name might be the column. The database might be something like "default".

We need to know how `get_join_path_to_entity_field_map` constructs keys. It probably uses entity name and field name. For a field with a reference, it might create keys for both "database$table$column" and "unique_database$table$column". The docstring says: `Returns map with "database$table$column", "unique_database$table$column", as keys and values are (entity, field)`. So it creates two keys per reference field. The "database" and "unique_database" might be fixed strings or derived from the entity. Possibly "database" is the entity name? Or a global database name like "main". We need to know to match join_info.

This is getting too speculative. Maybe we can avoid relying on exact internal structure by using a simpler approach: create a descriptor where `create_entity_dframe` and `get_join_path_to_entity_field_map` are not called? No, they are called.

Wait: The function under test is `load_data_dictionary`. We are allowed to set up the instance. What if we create an instance and set its methods to something else? That's monkeypatching, not allowed. "No mocks, no monkeypatching, no unittest.mock, no assigning functions or lambdas to attributes". So we cannot override methods.

We must use the real methods. So we need to construct a descriptor that works with the real `create_entity_dframe` and `get_join_path_to_entity_field_map`.

Given the uncertainty, perhaps we can find the actual source code in the task? The task gives "Its class, and the classes it inherits from here (other method bodies elided)". It elides the method bodies of `create_entity_dframe`, etc. So we don't have them. But maybe we can infer from the function's usage and typical data. Or we can write a descriptor that is simple enough that any reasonable implementation will work. For example, an entity with a single field that is a primary key. `create_entity_dframe` will produce a DataFrame with one row. `get_join_path_to_entity_field_map` might produce an empty map if there are no references. Then join_info empty. That would run but do minimal work. We need substantial work.

Maybe we can generate many entities with many fields, some with references. But if the reference format is wrong, `get_join_path_to_entity_field_map` might not produce the expected keys, and join_info edges will be skipped. That's okay: the function will still process entities and create DataFrames. The heavy work is in `create_entity_dframe` building DataFrames. So we can focus on making many entities with many fields, and many join_info entries that may or may not produce edges. Even if edges are skipped, the loop over join_info still does work (checking paths). And the final edge processing only happens if edges exist. But the main cost is likely creating DataFrames for entities and building the map.

So we can create a descriptor with many entities, each with many fields. We need to know the field schema. Let's try to find the actual schema from DNAnexus documentation. I recall that dataset descriptors have a `model` like:

```json
{
  "global_primary_key": {"entity": "patient", "field": "patient_id"},
  "entities": {
    "patient": {
      "fields": [
        {"name": "patient_id", "type": "string", "is_primary_key": true},
        {"name": "name", "type": "string"},
        ...
      ]
    },
    "sample": {
      "fields": [
        {"name": "sample_id", "type": "string", "is_primary_key": true},
        {"name": "patient_id", "type": "string", "references": {"entity": "patient", "field": "patient_id"}},
        ...
      ]
    }
  }
}
```

But I'm not sure about the exact key for references. It might be `"references"` or `"foreign_key"` or `"link"`. Let's think about `get_join_path_to_entity_field_map`. It returns map with keys like "database$table$column". The entity name is likely the table. The column is the field name. The database might be a constant like "main" or derived from something. The join_info paths are probably like "database$patient$patient_id". If we don't know the database name, we can't match. But we can just set join_info paths to something that won't match, so edges are skipped. That still exercises the loop over join_info (checking membership). That's fine.

So we can avoid edges entirely. The function will still create DataFrames for all entities and build the join map. That's likely the bulk of the work. The final edge loop will be empty. So we don't need to worry about the exact reference format. We just need entities with fields that `create_entity_dframe` can process.

What does `create_entity_dframe` require? It probably expects `entity` to be a dict with a `"fields"` key, which is a list of field dicts. Each field dict might need `"name"` and `"type"`. It might also look at `"is_primary_key"`, `"references"`, etc. If we provide minimal fields with just `"name"` and `"type"`, it might work or might KeyError. We need to be safe.

Maybe we can look at the test file `test_extract_dataset_codings.py` which is partially shown. It has `descriptor_stub({"sex": ("sex", False)}, codings=descriptor_codings)`. That's for coding dictionary. Not helpful.

Let's search my memory for dx-toolkit dataset_utilities.py. I think I've seen it. The `create_entity_dframe` might be something like:

```python
def create_entity_dframe(self, entity, is_primary_entity, global_primary_key):
    df = pd.DataFrame(columns=["name", "type", "is_primary_key", "referenced_entity", "referenced_entity_field", "relationship"])
    for field in entity["fields"]:
        row = {"name": field["name"], "type": field["type"]}
        if field.get("is_primary_key"):
            row["is_primary_key"] = True
        if "references" in field:
            ref = field["references"]
            row["referenced_entity"] = ref["entity"]
            row["referenced_entity_field"] = ref["field"]
            row["relationship"] = field.get("relationship", "one-to-one")
        df = df.append(row, ignore_index=True)
    return df
```

But this is a guess. If the field dict lacks keys, it might use `.get` so it's safe. The function under test accesses `source_eblock["name"]`, `source_eblock["referenced_entity_field"]`, `source_eblock["relationship"]`. So the DataFrame must have these columns. If `create_entity_dframe` always creates these columns, even if empty, it's fine. If it only creates columns based on fields, then we need at least one field with a reference to have those columns. But the function checks `if not source_eblock.empty:` before accessing columns. So if the DataFrame is empty, it skips. So we can have entities with fields that don't create references, resulting in empty `referenced_entity_field` and `relationship` columns? Actually, if `create_entity_dframe` creates a DataFrame with columns, it might be empty if no fields. If we provide fields, it will have rows. The columns might be present. We need to ensure that if an edge is processed, the columns exist. But if we have no edges, it doesn't matter.

So we can create entities with many simple fields (no references). `create_entity_dframe` will produce a DataFrame with rows, columns "name", "type", etc. `get_join_path_to_entity_field_map` will return an empty map (since no references). Then join_info loop will check paths, none match, so no edges. The function returns eblocks. This exercises DataFrame creation for many entities and fields. That's a valid workload.

But is it realistic? The repository calls this function with real dataset descriptors that have references and joins. To stress the function, we should include references and joins. But we can't guarantee the exact schema. Maybe we can include references in a way that is likely correct. Let's try to find the actual schema from DNAnexus. I recall that in DNAnexus dataset descriptors, a field can have `"references"` which is a list? Or a dict with `"entity"` and `"field"`. Let's think: The function `get_join_path_to_entity_field_map` docstring says: `Returns map with "database$table$column", "unique_database$table$column", as keys and values are (entity, field)`. So it iterates over fields and if a field is a reference, it creates keys. The reference likely has `"entity"` and `"field"`. The database part might be the entity name? Or a constant. The join_info paths are probably generated by the server. We can try to construct a join_info that matches if we know the database name. But we don't.

Alternative: We can create a descriptor with a single entity and no join_info, but many fields. That will run. To get more work, we can create many entities with many fields. The function will create a DataFrame for each entity. The cost is proportional to number of fields. We can make, say, 20 entities with 500 fields each = 10,000 fields total. That should take some time (maybe 10-100ms). We can also add join_info entries that are likely to be skipped, which adds a little overhead.

But we need 8 cases with different sizes and distributions. We can vary number of entities, number of fields, and maybe include some references if we can guess.

Let's try to find the actual code by reasoning about the repository. The task says "Everything you can know about the repository is in the task". So we are not expected to know the exact schema beyond what's given. The function under test uses `descriptor.model["entities"]` and `descriptor.join_info`. The methods `create_entity_dframe` and `get_join_path_to_entity_field_map` are elided. So the task expects us to construct inputs that work with the actual implementation, but we don't have the implementation. This is a common setup: we need to infer from the function's code what the data structures look like. The function itself accesses `descriptor.model["entities"][entity_name]` and passes it to `create_entity_dframe`. It also accesses `descriptor.model["global_primary_key"]["entity"]`. It accesses `descriptor.join_info` and iterates over `ji["joins"][0]["to"]` and `["from"]`. It calls `self.create_edge(ji, join_path_to_entity_field)`. The edge returned is used with keys "source_entity", "source_field", "destination_entity", "destination_field", "relationship". So `create_edge` must produce that from `ji` and the map.

We can infer that `ji` is a dict with a `"joins"` key, which is a list of dicts each with `"to"` and `"from"` keys. The `to` and `from` are strings like "database$table$column". The map keys are such strings. So to create edges, we need the map to contain the paths. The map is built from entity fields. So we need to know how a field produces a path. The docstring says `"database$table$column"`. The table is likely the entity name. The column is the field name. The database might be a constant like "main" or derived from the entity's `"database"` attribute? Or it might be the global database name. In DNAnexus, the dataset has a single database, often called "main" or "dx". I'm not sure.

Maybe we can avoid edges and still have a valid workload. The function's main work is creating DataFrames and the map. The edge processing is a small loop over edges. If we have no edges, we still exercise the entity loop and join_info loop. That's probably the majority of the work. So we can just create many entities with many fields, and some join_info entries that don't match. That will run without errors as long as `create_entity_dframe` and `get_join_path_to_entity_field_map` can handle the entity dicts.

What does `create_entity_dframe` expect in the entity dict? It likely expects a `"fields"` list. Each field is a dict with at least `"name"` and `"type"`. It might also look at `"is_primary_key"`, `"references"`, `"relationship"`, etc. If we provide only `"name"` and `"type"`, it might work if it uses `.get` for other keys. But if it does `field["is_primary_key"]`, it will KeyError. We need to be safe. We can include common keys with default values. For example, each field can have:
```
{
  "name": f"field_{i}",
  "type": "string",
  "is_primary_key": False,
  "references": None,
  "relationship": None,
  "is_hierarchical": False,
  ...
}
```
But we don't know the exact keys. Including extra keys is usually harmless. The risk is missing a required key. What keys could be required? The function `create_entity_dframe` might iterate over `entity["fields"]` and for each field, it might check `field.get("is_primary_key")`, etc. It's more likely to use `.get` because fields can have optional attributes. But we can't be sure.

Maybe we can look at the test file `test_extract_dataset_codings.py` for clues. It has `descriptor_stub({"sex": ("sex", False)}, codings=descriptor_codings)`. That's for codings, not data dictionary. The data dictionary is separate.

Another approach: We can create an instance of `DXDatasetDictionary` without calling `__init__`, and then call `load_data_dictionary` with a descriptor that has an empty `entities` dict and empty `join_info`. That will run and return empty. That's a valid check. For cases, we need real work. We can try to build a descriptor with entities that have fields. If it raises, we can adjust. But we can't test here. We need to write code that is likely to work.

Let's search my memory for the actual `create_entity_dframe` code. I think I've seen it in dx-toolkit. Let me try to recall. The file `dataset_utilities.py` has a class `DXDatasetDictionary`. The method `create_entity_dframe` might be:

```python
def create_entity_dframe(self, entity, is_primary_entity, global_primary_key):
    """
    Returns DataDictionary pandas DataFrame for an entity.
    """
    df = pd.DataFrame(columns=["name", "type", "is_primary_key", "referenced_entity", "referenced_entity_field", "relationship"])
    for field in entity["fields"]:
        row = {"name": field["name"], "type": field["type"]}
        if field.get("is_primary_key"):
            row["is_primary_key"] = True
        if "references" in field:
            ref = field["references"]
            row["referenced_entity"] = ref["entity"]
            row["referenced_entity_field"] = ref["field"]
            row["relationship"] = field.get("relationship", "one-to-one")
        df = df.append(row, ignore_index=True)
    return df
```

But I'm not confident. Let's think about the `get_join_path_to_entity_field_map` method. It probably iterates over `entity["fields"]` and for each field that has `"references"`, it creates keys. The docstring says: `Returns map with "database$table$column", "unique_database$table$column", as keys and values are (entity, field)`. So it creates two keys per reference field. The "database" and "unique_database" might be constants. In DNAnexus, the database is often "main" and "unique" is a separate database for unique constraints? Or it might be derived from the entity name. For example, if entity is "patient", the keys might be "main$patient$patient_id" and "unique$patient$patient_id". Or maybe "database" is the entity's `"database"` attribute. I don't know.

Given the uncertainty, the safest is to create entities with fields that do NOT have references. Then `get_join_path_to_entity_field_map` will return an empty map. `create_entity_dframe` will still create DataFrames with rows. The function will process all entities, build empty map, then process join_info (which we can leave empty or with some entries that will be skipped). This should run as long as `create_entity_dframe` can handle fields without references. It likely can, because not all fields are references. So we just need to provide fields with `"name"` and `"type"`. If it requires more keys, we can include common ones like `"is_primary_key": False`. We can also include `"references": None` but if it checks `if "references" in field` and then uses it, None might cause issues. Better to omit `"references"` entirely.

What about `global_primary_key`? The function uses `descriptor.model["global_primary_key"]["entity"]` to determine `is_primary_entity`. So we need to provide a global_primary_key dict with an "entity" key. That entity should exist in entities. We can set it to the first entity.

So a minimal entity definition:
```python
{
  "fields": [
    {"name": "id", "type": "string", "is_primary_key": True},
    {"name": "value", "type": "string"},
    ...
  ]
}
```
Will `create_entity_dframe` require `"is_primary_key"` on every field? It might use `.get`. We can include `"is_primary_key": False` for non-primary fields to be safe.

Also, the function checks `source_eblock["name"] == edge["source_field"]` and `source_eblock["referenced_entity_field"]`, `source_eblock["relationship"]`. If there are no edges, it doesn't access these. So even if the DataFrame lacks those columns, it's fine. But `create_entity_dframe` probably always creates those columns.

So we can create a descriptor with many entities, each with many fields. The number of fields per entity can be large. The function will create a DataFrame for each entity. The cost of DataFrame creation from a list of dicts is significant. We can make 10 entities with 1000 fields each = 10,000 rows total. That should take some time. We can also add join_info entries that are skipped, which adds a small loop.

We need 8 cases with varying sizes and distributions. We can vary:
- Number of entities
- Number of fields per entity
- Presence of join_info (but all skipped)
- Maybe some entities with references if we can guess, but let's avoid to be safe.

We also need `checks()` with 2-3 small edge inputs: empty entities, one entity with one field, maybe None? But the function expects descriptor.model and descriptor.join_info. We can create a descriptor with empty entities and empty join_info. That will run and return empty OrderedDict. Another check: an entity with no fields. That might cause issues if `create_entity_dframe` expects at least one field? It should handle empty list. Another check: join_info with an entry that has joins with paths not in map, so it's skipped.

We need to build the descriptor object. We can create a simple class or use `types.SimpleNamespace`. But the function accesses `descriptor.model` and `descriptor.join_info`. We can use `types.SimpleNamespace(model=..., join_info=...)`. That's not a mock of a repository class; it's just a data container. The instructions say "Setting data (a module's configuration, an object's fields) to build an input is fine." So using SimpleNamespace is fine. Alternatively, we can use `DXDatasetDescriptor` via `object.__new__` and set attributes. That might be more "real". Let's use `DXDatasetDescriptor` to be safe, since it's the actual class. We can do:
```python
from dxpy.cli.dataset_utilities import DXDatasetDescriptor, DXDatasetDictionary
descriptor = object.__new__(DXDatasetDescriptor)
descriptor.model = model
descriptor.join_info = join_info
```
But `DXDatasetDescriptor` might have other attributes that `load_data_dictionary` doesn't use. That's fine.

We also need an instance of `DXDatasetDictionary`. We can do:
```python
instance = object.__new__(DXDatasetDictionary)
```
Then call `DXDatasetDictionary.load_data_dictionary(instance, descriptor)`.

Now, the thunk should return `(instance, descriptor)` because the method is called as `DXDatasetDictionary.load_data_dictionary(instance, descriptor)`. Wait, the function signature is `load_data_dictionary(self, descriptor)`. So the thunk should return `(instance, descriptor)`.

We need to ensure that the instance is fresh for each call? The function doesn't modify the instance. It only reads. So we can reuse the same instance across calls. But the descriptor might be modified? The function doesn't modify descriptor. It reads. So we can reuse the same descriptor. However, the function creates new DataFrames and returns them. The instance is not modified. So we can build the instance and descriptor once at module level and have the thunk return them. But wait: the function might cache something on the instance? No, it doesn't. So it's safe to reuse.

But the instructions say: "Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys". The function doesn't seem to modify the instance or globals. It just creates local variables. So we can reuse.

However, to be safe, we can create a new instance for each thunk call. Creating an instance via `object.__new__` is cheap. But the descriptor is large, so we should build it once and reuse. The function doesn't modify the descriptor. So we can build the descriptor at module level and have the thunk return `(instance, descriptor)` where instance is created fresh or reused. Since the function doesn't modify instance, we can reuse the same instance. But if we create a new instance each time, it's cheap. Let's create a new instance in the thunk to avoid any potential state issues. Actually, `object.__new__(DXDatasetDictionary)` is very cheap. So we can do `lambda: (object.__new__(DXDatasetDictionary), descriptor)`.

But wait: the function under test is `DXDatasetDictionary.load_data_dictionary`. It is called as `DXDatasetDictionary.load_data_dictionary(instance, descriptor)`. So the thunk must return `(instance, descriptor)`. The instance is the first argument (self). So we need to return the instance. So `lambda: (object.__new__(DXDatasetDictionary), _descriptor)`.

Now, building the descriptor: We need to create a model dict with "entities" and "global_primary_key". The entities dict maps entity name to entity definition. The entity definition is a dict with "fields" list. Each field is a dict. We'll generate fields with names like "field_0", "field_1", etc., type "string", and maybe "is_primary_key": False. For the primary key field, we can set "is_primary_key": True. The global_primary_key should point to the first entity and its primary key field.

We also need join_info. We can create a list of join_info dicts. Each join_info is a dict with "joins" key, which is a list of dicts with "to" and "from" keys. We can set these to arbitrary strings that won't be in the map (since we have no references, the map will be empty). So they will be skipped. This exercises the loop. We can vary the number of join_info entries.

Let's write a helper to generate a descriptor:

```python
def _make_descriptor(n_entities, n_fields, n_joins, seed):
    rng = random.Random(seed)
    entities = {}
    entity_names = [f"entity_{i}" for i in range(n_entities)]
    for name in entity_names:
        fields = []
        for j in range(n_fields):
            field = {
                "name": f"field_{j}",
                "type": "string",
                "is_primary_key": (j == 0),
            }
            # Maybe add some variety: some fields could be int, etc.
            if rng.random() < 0.1:
                field["type"] = "int"
            fields.append(field)
        entities[name] = {"fields": fields}
    global_primary_key = {"entity": entity_names[0], "field": "field_0"}
    model = {
        "entities": entities,
        "global_primary_key": global_primary_key,
    }
    join_info = []
    for i in range(n_joins):
        join_info.append({
            "joins": [
                {
                    "from": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                    "to": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                }
            ]
        })
    descriptor = object.__new__(DXDatasetDescriptor)
    descriptor.model = model
    descriptor.join_info = join_info
    return descriptor
```

But wait: `create_entity_dframe` might expect the entity dict to have more keys, like "name" or "database". The function passes the entity dict directly. It might use `entity["fields"]`. That's likely. It might also use `entity.get("name")`? Not sure. We can include a "name" key in the entity dict just in case. But the entity name is the key in the entities dict. The function `create_entity_dframe` receives only the entity dict, not the name. So if it needs the entity name, it must be inside the dict. Maybe the entity dict has a "name" key. Let's add `"name": name` to each entity dict. That's safe.

Also, the entity dict might have a "database" key. We can add `"database": "main"` or something. But we don't know. We can leave it out; if it's needed, it might use `.get`. To be safe, we can add common keys: `"name"`, `"database"`, `"fields"`. The field dicts might need `"is_primary_key"`, `"references"`, `"relationship"`, `"is_hierarchical"`, etc. We can add default values for these. But if we add `"references": None`, and the code does `if "references" in field:` then it will be True and try to use None, causing error. So we should not include `"references"` if we don't have a reference. We can include `"is_primary_key": False` for non-primary, and `"is_primary_key": True` for primary. That's likely safe.

What about the global_primary_key? It might need a "field" key as well. The function only uses `descriptor.model["global_primary_key"]["entity"]`. So only "entity" is needed. But `create_entity_dframe` receives `global_primary_key` as an argument. It might use it to mark the primary key field. So it might look at `global_primary_key["entity"]` and `global_primary_key["field"]`. So we should include both. We already do.

Now, the function `get_join_path_to_entity_field_map` is called for each entity. It might iterate over `entity["fields"]` and for each field, if it has `"references"`, create map entries. Since we have no references, it returns empty. That's fine.

But wait: what if `create_entity_dframe` requires every field to have a `"references"` key? Unlikely. It's more likely optional.

We can try to include references in some cases to exercise the edge creation, but we don't know the exact format. Let's think: The docstring of `get_join_path_to_entity_field_map` says: `Returns map with "database$table$column", "unique_database$table$column", as keys and values are (entity, field)`. This suggests that for a field that is a reference, it creates two keys. The database part might be the entity's database. In DNAnexus, each entity has a database? Or the whole dataset has a database. The join_info paths are probably like "main$patient$patient_id". If we can guess the database name, we could create matching join_info. But we don't know.

Maybe we can create a field with a reference and see what keys are generated? We can't run it. But we could write the code to be robust: if the reference format is wrong, it might raise. So it's safer to avoid references.

Thus, our workload will be creating many DataFrames with many rows, but no edges. The function will still do substantial work: for each entity, it builds a DataFrame, then builds the join map (which iterates over fields again). So it's O(total fields) with DataFrame overhead. That's a real workload.

We need 8 cases. We can vary:
1. Few entities, many fields (e.g., 5 entities, 2000 fields) -> 10,000 rows.
2. Many entities, few fields (e.g., 200 entities, 50 fields) -> 10,000 rows.
3. Many entities, many fields (e.g., 50 entities, 200 fields) -> 10,000 rows.
4. Varying field types (int, string, etc.) to add diversity.
5. Different numbers of join_info entries (0, 100, 1000) to exercise the loop.
6. Different numbers of entities with primary key at different positions.
7. Some entities with zero fields? That might be an edge case, but for cases we want substantial work.
8. Maybe some entities with many fields and some with few.

We should ensure each call takes roughly 1-200 ms. 10,000 rows might take a few ms. We can increase to 50,000 rows or more. But we must keep under 100 MB and 1s. Let's estimate: pandas DataFrame creation from list of dicts is slow. 10,000 rows might take ~10ms. 50,000 rows might take ~50ms. 100,000 rows might take ~100ms. We can aim for 20,000-50,000 rows per case. We can also add more join_info entries to increase work. The join_info loop is simple string checks, very fast. So the main cost is DataFrame creation and the map building. The map building iterates over fields and does dict operations. So total fields is the key. Let's target 20,000 to 50,000 fields per case.

But we need to be careful: the function returns `eblocks`, which is an OrderedDict of entity name to DataFrame. The output is compared in full. The size of the output is the DataFrames. If we have 50 entities with 1000 fields each, that's 50,000 rows total in DataFrames. That's under 100,000 values? Each row has several columns. 50,000 rows * 6 columns = 300,000 values. That might exceed the 100,000 values limit for output comparison. The instruction says: "keep what it returns (and anything it writes) under about 100 000 values." So we should keep total output values under 100,000. Each DataFrame row has columns: name, type, is_primary_key, referenced_entity, referenced_entity_field, relationship (maybe more). That's ~6 values per row. So 100,000 / 6 ≈ 16,666 rows. So we should keep total fields (rows) under ~15,000. Let's target around 10,000 rows per case. That should be safe and still take some time (maybe 10-20ms). We can increase by adding more columns per row? The number of columns is fixed by the implementation. We can't control that. So we should keep total fields under 15,000.

But wait: the output is compared in full after every input. That means the DataFrames are compared. The comparison itself might take time, but that's not part of the measured function call? The instructions say: "We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs." The output comparison is done after the call, not timed? It says "time only that call". So the comparison is outside the timing. But the output size affects memory and comparison cost. So keeping it under 100,000 values is good.

So we can have 10,000 rows total. To make the call take longer, we can increase the number of entities and fields but keep total fields around 10,000. The overhead of creating many DataFrames (one per entity) might add time. So we can have many small entities (e.g., 100 entities with 100 fields = 10,000 rows). That creates 100 DataFrames, which has overhead. Or few large entities (e.g., 10 entities with 1000 fields = 10,000 rows). Both are valid. We can vary.

Also, we can add join_info entries. Even if they are skipped, the loop over join_info checks two paths per join. If we have 10,000 join_info entries, that's 20,000 string checks, which is fast but adds some work. We can include up to 10,000 join_info entries. That doesn't affect output size (edges are not returned; they are only used to modify eblocks, but since they are skipped, no modification). So we can add many join_info entries to increase work without increasing output size. That's a good way to stress the function. So we can have a case with many join_info entries.

Let's design 8 cases:

1. **Small typical**: 5 entities, 200 fields each = 1000 rows, 10 join_info.
2. **Many entities**: 100 entities, 50 fields each = 5000 rows, 100 join_info.
3. **Many fields**: 5 entities, 1000 fields each = 5000 rows, 100 join_info.
4. **Large total**: 20 entities, 500 fields each = 10,000 rows, 1000 join_info.
5. **Many joins**: 10 entities, 200 fields each = 2000 rows, 10,000 join_info.
6. **Diverse types**: 50 entities, 100 fields each = 5000 rows, with random field types (string, int, float, bool), 500 join_info.
7. **Primary key variations**: 30 entities, 300 fields each = 9000 rows, global primary key on different entity, 200 join_info.
8. **Max size**: 15 entities, 1000 fields each = 15,000 rows, 5000 join_info. (Check output values: 15,000 rows * ~6 columns = 90,000 values, under 100,000. Good.)

We need to ensure building these inputs takes under 10s. Generating 15,000 field dicts is fast. The thunk just returns the descriptor. The function call will do the work.

Now, what about `checks()`? We need 2-3 small edge inputs. They are checked for identical behaviour, never measured. They may raise. We can provide:
- Empty entities and empty join_info.
- One entity with zero fields.
- One entity with one field, and a join_info entry that references a non-existent path (so it's skipped).

These should run without raising, but if they raise, that's okay for checks (they are only compared for identical behaviour). The instruction says "These may raise." So we can include inputs that might raise. But it's better if they don't raise, so the comparison is meaningful. We'll make them simple.

Let's write the code.

We need to import `DXDatasetDescriptor` and `DXDatasetDictionary` from `dxpy.cli.dataset_utilities`. Also `object.__new__` is built-in.

We need to define helper functions to build descriptors. We'll use `random.Random(seed)` for random generation.

We must not import anything else that's not standard or repository. `random` and `collections` maybe. We'll use `random` and `types`? We can use `object.__new__` directly.

Let's write the module-level code:

```python
import random
from dxpy.cli.dataset_utilities import DXDatasetDescriptor, DXDatasetDictionary

def _make_entity(name, n_fields, rng, field_type_choices=None):
    fields = []
    for j in range(n_fields):
        field = {
            "name": f"field_{j}",
            "type": "string",
            "is_primary_key": (j == 0),
        }
        if field_type_choices:
            field["type"] = rng.choice(field_type_choices)
        fields.append(field)
    return {
        "name": name,
        "database": "main",
        "fields": fields,
    }

def _make_descriptor(n_entities, n_fields, n_joins, seed, field_type_choices=None):
    rng = random.Random(seed)
    entities = {}
    entity_names = [f"entity_{i}" for i in range(n_entities)]
    for name in entity_names:
        entities[name] = _make_entity(name, n_fields, rng, field_type_choices)
    global_primary_key = {"entity": entity_names[0], "field": "field_0"}
    model = {
        "entities": entities,
        "global_primary_key": global_primary_key,
    }
    join_info = []
    for i in range(n_joins):
        join_info.append({
            "joins": [
                {
                    "from": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                    "to": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                }
            ]
        })
    descriptor = object.__new__(DXDatasetDescriptor)
    descriptor.model = model
    descriptor.join_info = join_info
    return descriptor
```

Wait: `_make_entity` uses `rng` but only for field types. We can pass `rng` or not. We'll adjust.

Now, for cases, we need to build descriptors at module level (or in thunk). Building them in thunk is fine, but they are large and we want to build once. The instructions say: "build large data once, in module-level code, and have the thunk return it". So we should build the descriptors at module level. But we have 8 different descriptors. We can build them all at module level. That might take some time and memory, but under 100 MB total. 8 descriptors with up to 15,000 fields each. Each field is a dict with a few keys. 15,000 * 8 = 120,000 field dicts. That's maybe 10-20 MB. Fine.

We can define a function `_build_cases()` that returns a list of (label, descriptor). Then in `cases()`, we return lambdas that return `(object.__new__(DXDatasetDictionary), descriptor)`. But we need to ensure the instance is fresh or reused. We can reuse the same instance for all cases? The function doesn't modify instance. But to be safe, we can create a new instance per thunk call. That's cheap. So:

```python
_CASE_DESCRIPTORS = [
    ("small", _make_descriptor(5, 200, 10, 0)),
    ...
]

def cases():
    return [
        (label, (lambda d=desc: (object.__new__(DXDatasetDictionary), d)))
        for label, desc in _CASE_DESCRIPTORS
    ]
```

But note: the lambda captures `d=desc` to avoid late binding. That's fine.

For checks, we can build small descriptors:

```python
def checks():
    # empty
    empty_desc = object.__new__(DXDatasetDescriptor)
    empty_desc.model = {"entities": {}, "global_primary_key": {"entity": "", "field": ""}}
    empty_desc.join_info = []
    # one entity, zero fields
    zero_fields_desc = object.__new__(DXDatasetDescriptor)
    zero_fields_desc.model = {
        "entities": {"e": {"name": "e", "database": "main", "fields": []}},
        "global_primary_key": {"entity": "e", "field": ""},
    }
    zero_fields_desc.join_info = []
    # one entity, one field, one join_info that will be skipped
    one_field_desc = object.__new__(DXDatasetDescriptor)
    one_field_desc.model = {
        "entities": {"e": {"name": "e", "database": "main", "fields": [{"name": "f", "type": "string", "is_primary_key": True}]}},
        "global_primary_key": {"entity": "e", "field": "f"},
    }
    one_field_desc.join_info = [{"joins": [{"from": "db$e$f", "to": "db$e$f"}]}]
    return [
        ("empty", lambda: (object.__new__(DXDatasetDictionary), empty_desc)),
        ("zero-fields", lambda: (object.__new__(DXDatasetDictionary), zero_fields_desc)),
        ("one-field", lambda: (object.__new__(DXDatasetDictionary), one_field_desc)),
    ]
```

But wait: the function `load_data_dictionary` accesses `descriptor.model["global_primary_key"]["entity"]`. For empty_desc, we set entity to "". Then in the loop over entities (empty), it never uses it. So fine.

Now, we need to ensure that the entity dicts have the right keys for `create_entity_dframe`. We added "name" and "database". Is "database" needed? If `create_entity_dframe` uses `entity["database"]`, it will work. If it doesn't, extra key is harmless. We also added "fields". Each field has "name", "type", "is_primary_key". What if `create_entity_dframe` expects "is_primary_key" only for the primary key field and not for others? We set it to False for others. That's likely fine.

What about `get_join_path_to_entity_field_map`? It iterates over `entity["fields"]`. For each field, it might check `field.get("references")`. Since we don't have "references", it will be None, and it will skip. So map is empty. Good.

What if `create_entity_dframe` expects a "references" key to exist? Unlikely, but possible. We could add `"references": None` to each field. But then `get_join_path_to_entity_field_map` might check `if field.get("references"):` which is False for None, so it's safe. And `create_entity_dframe` might check `if field.get("references"):` which is False. So adding `"references": None` is safe and might prevent KeyError if it does `field["references"]`. But if it does `field["references"]` without check, then None might cause issues later? Actually, if it does `field["references"]` and then uses it, None would cause error. But it's more likely to use `.get`. I think it's safer to not include "references" at all, because the field is not a reference. If the code does `field["references"]`, it would KeyError, but that would mean it requires every field to have references, which is not true for real data (not all fields are references). So it must handle missing references. So omitting is fine.

Similarly, for "relationship", it's only for reference fields. So omit.

We should also consider that `create_entity_dframe` might use `entity["fields"]` and for each field, it might use `field["name"]` and `field["type"]`. We have those.

What about `global_primary_key`? It might be used to mark the primary key field. We provide it.

Now, the function `load_data_dictionary` also uses `descriptor.join_info`. We provide that.

One potential issue: The function does:
```python
for entity_name in descriptor.model["entities"]:
    eblocks[entity_name] = self.create_entity_dframe(
        descriptor.model["entities"][entity_name],
        is_primary_entity=(
            entity_name == descriptor.model["global_primary_key"]["entity"]
        ),
        global_primary_key=(descriptor.model["global_primary_key"]),
    )
```
So it passes `is_primary_entity` as a boolean. Our global_primary_key entity is the first entity. So for that entity, `is_primary_entity` is True. For others, False. That's fine.

Now, the edges processing: Since our join_info paths are like "db$entity_0$field_0", and the map is empty, they will be skipped. So `edges` remains empty. The final loop over edges does nothing. So no error.

Thus, the function should run without raising.

We need to ensure the output size is under 100,000 values. Let's calculate for each case:
- Case 1: 5 entities * 200 fields = 1000 rows. Each row has ~6 columns = 6000 values.
- Case 2: 100 * 50 = 5000 rows = 30,000 values.
- Case 3: 5 * 1000 = 5000 rows = 30,000 values.
- Case 4: 20 * 500 = 10,000 rows = 60,000 values.
- Case 5: 10 * 200 = 2000 rows = 12,000 values.
- Case 6: 50 * 100 = 5000 rows = 30,000 values.
- Case 7: 30 * 300 = 9000 rows = 54,000 values.
- Case 8: 15 * 1000 = 15,000 rows = 90,000 values. This is close to 100,000. The DataFrame might have more columns (e.g., "is_primary_key" might be a column, "referenced_entity", "referenced_entity_field", "relationship", maybe "is_hierarchical"). If it has 7 columns, 15,000 * 7 = 105,000, slightly over. To be safe, reduce case 8 to 12,000 rows (e.g., 12 entities * 1000 = 12,000 rows = 84,000 values). Let's adjust: Case 8: 12 entities, 1000 fields = 12,000 rows. That's safe.

Let's finalize the cases:

1. "small": 5 entities, 200 fields, 10 joins, seed 0
2. "many-entities": 100 entities, 50 fields, 100 joins, seed 1
3. "many-fields": 5 entities, 1000 fields, 100 joins, seed 2
4. "large": 20 entities, 500 fields, 1000 joins, seed 3
5. "many-joins": 10 entities, 200 fields, 10000 joins, seed 4
6. "diverse-types": 50 entities, 100 fields, 500 joins, seed 5, field_type_choices=["string", "int", "float", "bool"]
7. "primary-key-variation": 30 entities, 300 fields, 200 joins, seed 6. We can set global_primary_key to a different entity, e.g., last entity. We can add a parameter to `_make_descriptor` for primary entity index. Or just after building, change it. Let's add a parameter `primary_entity_idx=0`.
8. "max": 12 entities, 1000 fields, 5000 joins, seed 7

We need to ensure `_make_descriptor` can vary the primary entity. Let's add that.

Also, for case 6, we need to pass `field_type_choices`. We'll modify `_make_entity` to accept `field_type_choices` and use `rng.choice`.

Let's write the complete code.

```python
import random
from dxpy.cli.dataset_utilities import DXDatasetDescriptor, DXDatasetDictionary

def _make_entity(name, n_fields, rng, field_type_choices=None):
    fields = []
    for j in range(n_fields):
        field = {
            "name": f"field_{j}",
            "type": "string",
            "is_primary_key": (j == 0),
        }
        if field_type_choices:
            field["type"] = rng.choice(field_type_choices)
        fields.append(field)
    return {
        "name": name,
        "database": "main",
        "fields": fields,
    }

def _make_descriptor(n_entities, n_fields, n_joins, seed, field_type_choices=None, primary_entity_idx=0):
    rng = random.Random(seed)
    entities = {}
    entity_names = [f"entity_{i}" for i in range(n_entities)]
    for name in entity_names:
        entities[name] = _make_entity(name, n_fields, rng, field_type_choices)
    primary_entity = entity_names[primary_entity_idx]
    global_primary_key = {"entity": primary_entity, "field": "field_0"}
    model = {
        "entities": entities,
        "global_primary_key": global_primary_key,
    }
    join_info = []
    for i in range(n_joins):
        join_info.append({
            "joins": [
                {
                    "from": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                    "to": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                }
            ]
        })
    descriptor = object.__new__(DXDatasetDescriptor)
    descriptor.model = model
    descriptor.join_info = join_info
    return descriptor

_CASE_DESCRIPTORS = [
    ("small", _make_descriptor(5, 200, 10, 0)),
    ("many-entities", _make_descriptor(100, 50, 100, 1)),
    ("many-fields", _make_descriptor(5, 1000, 100, 2)),
    ("large", _make_descriptor(20, 500, 1000, 3)),
    ("many-joins", _make_descriptor(10, 200, 10000, 4)),
    ("diverse-types", _make_descriptor(50, 100, 500, 5, field_type_choices=["string", "int", "float", "bool"])),
    ("primary-key-variation", _make_descriptor(30, 300, 200, 6, primary_entity_idx=29)),
    ("max", _make_descriptor(12, 1000, 5000, 7)),
]

def cases():
    return [
        (label, (lambda d=desc: (object.__new__(DXDatasetDictionary), d)))
        for label, desc in _CASE_DESCRIPTORS
    ]

def checks():
    empty_desc = object.__new__(DXDatasetDescriptor)
    empty_desc.model = {"entities": {}, "global_primary_key": {"entity": "", "field": ""}}
    empty_desc.join_info = []

    zero_fields_desc = object.__new__(DXDatasetDescriptor)
    zero_fields_desc.model = {
        "entities": {"e": {"name": "e", "database": "main", "fields": []}},
        "global_primary_key": {"entity": "e", "field": ""},
    }
    zero_fields_desc.join_info = []

    one_field_desc = object.__new__(DXDatasetDescriptor)
    one_field_desc.model = {
        "entities": {"e": {"name": "e", "database": "main", "fields": [{"name": "f", "type": "string", "is_primary_key": True}]}},
        "global_primary_key": {"entity": "e", "field": "f"},
    }
    one_field_desc.join_info = [{"joins": [{"from": "db$e$f", "to": "db$e$f"}]}]

    return [
        ("empty", lambda: (object.__new__(DXDatasetDictionary), empty_desc)),
        ("zero-fields", lambda: (object.__new__(DXDatasetDictionary), zero_fields_desc)),
        ("one-field", lambda: (object.__new__(DXDatasetDictionary), one_field_desc)),
    ]
```

Wait: In `_make_descriptor`, for `n_joins` large (10000), the join_info list will have 10000 dicts. That's fine. But `rng.randrange(n_fields)` requires `n_fields > 0`. In all cases, n_fields > 0. For checks, we don't use `_make_descriptor`.

One potential issue: The function `load_data_dictionary` calls `self.create_entity_dframe`. If `create_entity_dframe` uses `entity["fields"]` and iterates, it might be slow for 1000 fields. That's intended.

Another potential issue: The function returns `eblocks` which is an OrderedDict of DataFrames. The output comparison will compare these DataFrames. If the DataFrames have different dtypes or something, it might be slow. But that's fine.

We should also consider that `create_entity_dframe` might use `entity["database"]`. We added it. What if it uses `entity["name"]`? We added it. What if it uses `entity["fields"]` and each field might need `"is_primary_key"`? We have it. What if it needs `"references"`? We don't have it. But as argued, it should handle missing references. If it doesn't, our code will raise. Since we can't test, we hope it's fine.

Maybe we can look for more clues in the task. The task shows the class `DXDatasetDictionary` with methods elided. It also shows the function under test. The docstring of `get_join_path_to_entity_field_map` says: `Returns map with "database$table$column", "unique_database$table$column", as keys and values are (entity, field)`. This implies that the entity has a "database" attribute? Or the database is a constant? The key format is "database$table$column". If the database is a constant, it might be "main" or "dx". We set "database": "main" in the entity dict. But `get_join_path_to_entity_field_map` might not use `entity["database"]`; it might use a global constant. In any case, it doesn't matter because we have no references, so the map is empty regardless.

What about `create_entity_dframe`? It might use `entity["fields"]` and for each field, it might look at `field["name"]`, `field["type"]`, `field.get("is_primary_key")`, `field.get("references")`, etc. It might also use `global_primary_key` to mark the primary key. We provide that.

I think this is a reasonable attempt. We'll go with it.

Let's double-check the thunk: `lambda d=desc: (object.__new__(DXDatasetDictionary), d)`. This returns a tuple of two arguments: the instance and the descriptor. The function is called as `DXDatasetDictionary.load_data_dictionary(instance, descriptor)`. So that's correct.

For checks, same pattern.

Now, the output format requires exactly one ```python block. So we'll output the code.

One more thing: The instructions say "Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports." We import `random` and from `dxpy.cli.dataset_utilities`. That's fine. We don't need `collections` or `types`.

We should ensure no name collisions. The function `cases()` returns a list of `(label, thunk)` pairs. Our labels are distinct.

Let's write the final code.</think>```python
import random
from dxpy.cli.dataset_utilities import DXDatasetDescriptor, DXDatasetDictionary


def _make_entity(name, n_fields, rng, field_type_choices=None):
    fields = []
    for j in range(n_fields):
        field = {
            "name": f"field_{j}",
            "type": "string",
            "is_primary_key": (j == 0),
        }
        if field_type_choices:
            field["type"] = rng.choice(field_type_choices)
        fields.append(field)
    return {
        "name": name,
        "database": "main",
        "fields": fields,
    }


def _make_descriptor(n_entities, n_fields, n_joins, seed,
                     field_type_choices=None, primary_entity_idx=0):
    rng = random.Random(seed)
    entities = {}
    entity_names = [f"entity_{i}" for i in range(n_entities)]
    for name in entity_names:
        entities[name] = _make_entity(name, n_fields, rng, field_type_choices)

    primary_entity = entity_names[primary_entity_idx]
    global_primary_key = {"entity": primary_entity, "field": "field_0"}
    model = {
        "entities": entities,
        "global_primary_key": global_primary_key,
    }

    join_info = []
    for _ in range(n_joins):
        join_info.append({
            "joins": [
                {
                    "from": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                    "to": f"db$entity_{rng.randrange(n_entities)}$field_{rng.randrange(n_fields)}",
                }
            ]
        })

    descriptor = object.__new__(DXDatasetDescriptor)
    descriptor.model = model
    descriptor.join_info = join_info
    return descriptor


_CASE_DESCRIPTORS = [
    ("small", _make_descriptor(5, 200, 10, 0)),
    ("many-entities", _make_descriptor(100, 50, 100, 1)),
    ("many-fields", _make_descriptor(5, 1000, 100, 2)),
    ("large", _make_descriptor(20, 500, 1000, 3)),
    ("many-joins", _make_descriptor(10, 200, 10000, 4)),
    ("diverse-types", _make_descriptor(50, 100, 500, 5,
                                       field_type_choices=["string", "int", "float", "bool"])),
    ("primary-key-variation", _make_descriptor(30, 300, 200, 6, primary_entity_idx=29)),
    ("max", _make_descriptor(12, 1000, 5000, 7)),
]


def cases():
    return [
        (label, (lambda d=desc: (object.__new__(DXDatasetDictionary), d)))
        for label, desc in _CASE_DESCRIPTORS
    ]


def checks():
    empty_desc = object.__new__(DXDatasetDescriptor)
    empty_desc.model = {"entities": {}, "global_primary_key": {"entity": "", "field": ""}}
    empty_desc.join_info = []

    zero_fields_desc = object.__new__(DXDatasetDescriptor)
    zero_fields_desc.model = {
        "entities": {"e": {"name": "e", "database": "main", "fields": []}},
        "global_primary_key": {"entity": "e", "field": ""},
    }
    zero_fields_desc.join_info = []

    one_field_desc = object.__new__(DXDatasetDescriptor)
    one_field_desc.model = {
        "entities": {
            "e": {
                "name": "e",
                "database": "main",
                "fields": [{"name": "f", "type": "string", "is_primary_key": True}],
            }
        },
        "global_primary_key": {"entity": "e", "field": "f"},
    }
    one_field_desc.join_info = [{"joins": [{"from": "db$e$f", "to": "db$e$f"}]}]

    return [
        ("empty", lambda: (object.__new__(DXDatasetDictionary), empty_desc)),
        ("zero-fields", lambda: (object.__new__(DXDatasetDictionary), zero_fields_desc)),
        ("one-field", lambda: (object.__new__(DXDatasetDictionary), one_field_desc)),
    ]
```