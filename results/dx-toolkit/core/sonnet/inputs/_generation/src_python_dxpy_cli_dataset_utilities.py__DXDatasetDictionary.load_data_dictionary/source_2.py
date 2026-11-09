import random
import types
from dxpy.cli.dataset_utilities import DXDatasetDictionary

_instance = DXDatasetDictionary.__new__(DXDatasetDictionary)


def _build_descriptor(num_entities, fields_per_entity, num_joins, coding_ratio=0.0, seed=0):
    rng = random.Random(seed)
    entities = {}
    join_paths = {}
    for i in range(num_entities):
        entity_name = f"entity_{i}"
        fields = {}
        join_field_idx = i % fields_per_entity if fields_per_entity > 0 else 0
        field_names = []
        for j in range(fields_per_entity):
            field_name = f"field_{j}"
            field_names.append(field_name)
            field = {
                "name": field_name,
                "type": "string",
                "is_primary_key": (j == 0),
                "coding": None,
                "description": f"description for {entity_name}.{field_name}",
            }
            if rng.random() < coding_ratio:
                field["coding"] = f"coding_{i}_{j}"
            if num_joins > 0 and j == join_field_idx:
                field["join"] = {
                    "database": "db",
                    "table": f"table_{i}",
                    "column": field_name,
                }
                join_paths[entity_name] = f"db$table_{i}${field_name}"
            fields[field_name] = field
        entities[entity_name] = {
            "name": entity_name,
            "fields": fields,
            "primary_key": [field_names[0]] if field_names else [],
            "description": f"entity {entity_name}",
        }
    global_primary_key = {"entity": "entity_0", "field": "field_0"}
    join_info = []
    if num_joins > 0 and entities:
        entity_names = list(entities.keys())
        joined = [n for n in entity_names if n in join_paths]
        for _ in range(num_joins):
            if len(joined) < 1:
                break
            src = rng.choice(joined)
            dst = rng.choice(joined)
            while dst == src and len(joined) > 1:
                dst = rng.choice(joined)
            src_path = join_paths[src]
            dst_path = join_paths[dst]
            join_info.append({
                "joins": [{
                    "from": src_path,
                    "to": dst_path,
                }],
                "relationship": "many-to-one",
            })
    return types.SimpleNamespace(
        model={"entities": entities, "global_primary_key": global_primary_key},
        join_info=join_info,
    )


_desc_small = _build_descriptor(10, 100, 0, coding_ratio=0.0, seed=1)
_desc_medium = _build_descriptor(20, 100, 20, coding_ratio=0.2, seed=2)
_desc_large = _build_descriptor(50, 100, 50, coding_ratio=0.3, seed=3)
_desc_many_entities = _build_descriptor(200, 20, 50, coding_ratio=0.1, seed=4)
_desc_many_fields = _build_descriptor(10, 500, 10, coding_ratio=0.5, seed=5)
_desc_many_joins = _build_descriptor(30, 100, 300, coding_ratio=0.2, seed=6)
_desc_dense_coding = _build_descriptor(20, 150, 30, coding_ratio=0.9, seed=7)
_desc_dense_join = _build_descriptor(20, 150, 150, coding_ratio=0.1, seed=8)

_desc_empty = types.SimpleNamespace(
    model={"entities": {}, "global_primary_key": {"entity": "", "field": ""}},
    join_info=[],
)
_desc_single = _build_descriptor(1, 1, 0, coding_ratio=0.0, seed=10)
_desc_empty_fields = types.SimpleNamespace(
    model={
        "entities": {
            "entity_0": {"name": "entity_0", "fields": {}, "primary_key": [], "description": ""}
        },
        "global_primary_key": {"entity": "entity_0", "field": "field_0"},
    },
    join_info=[],
)


def checks():
    return [
        ("empty-entities", lambda: (_instance, _desc_empty)),
        ("single-field", lambda: (_instance, _desc_single)),
        ("empty-fields", lambda: (_instance, _desc_empty_fields)),
    ]


def cases():
    return [
        ("small", lambda: (_instance, _desc_small)),
        ("medium", lambda: (_instance, _desc_medium)),
        ("large", lambda: (_instance, _desc_large)),
        ("many-entities", lambda: (_instance, _desc_many_entities)),
        ("many-fields", lambda: (_instance, _desc_many_fields)),
        ("many-joins", lambda: (_instance, _desc_many_joins)),
        ("dense-coding", lambda: (_instance, _desc_dense_coding)),
        ("dense-join", lambda: (_instance, _desc_dense_join)),
    ]
