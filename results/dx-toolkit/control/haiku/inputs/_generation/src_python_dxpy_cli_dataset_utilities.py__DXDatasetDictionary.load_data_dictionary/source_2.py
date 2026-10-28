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
        "entities": {"e": {"name": "e", "database": "main", "fields": [{"name": "f", "type": "string", "is_primary_key": True}]}},
        "global_primary_key": {"entity": "e", "field": "f"},
    }
    one_field_desc.join_info = [{"joins": [{"from": "db$e$f", "to": "db$e$f"}]}]

    return [
        ("empty", lambda: (object.__new__(DXDatasetDictionary), empty_desc)),
        ("zero-fields", lambda: (object.__new__(DXDatasetDictionary), zero_fields_desc)),
        ("one-field", lambda: (object.__new__(DXDatasetDictionary), one_field_desc)),
    ]
