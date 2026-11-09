import random
from dxpy.cli.dataset_utilities import DXDatasetDictionary


class Descriptor:
    def __init__(self, model, join_info):
        self.model = model
        self.join_info = join_info


def make_descriptor(num_entities, fields_per_entity, num_edges, valid_ratio, seed, duplicate_refs=False):
    rng = random.Random(seed)
    entities = {}
    all_refs = []
    entity_names = [f"entity_{i}" for i in range(num_entities)]
    global_primary_key = None
    for i, ename in enumerate(entity_names):
        fields = []
        for j in range(fields_per_entity):
            fname = f"field_{j}"
            is_ref = rng.random() < 0.3
            ref = None
            if is_ref:
                if duplicate_refs and all_refs and rng.random() < 0.2:
                    ref = rng.choice(all_refs)[2]
                else:
                    ref = f"db{i}$table{j}$col{j}"
                all_refs.append((ename, fname, ref))
            field = {
                "name": fname,
                "type": rng.choice(["string", "int", "float", "boolean"]),
                "is_primary_key": False,
                "references": ref,
                "description": f"description {j}",
                "is_optional": rng.choice([True, False]),
                "is_multi": rng.choice([True, False]),
            }
            fields.append(field)
        if i == 0:
            fields[0]["is_primary_key"] = True
            global_primary_key = {"entity": ename, "field": fields[0]["name"]}
        entities[ename] = {"name": ename, "fields": fields}
    model = {
        "entities": entities,
        "global_primary_key": global_primary_key,
    }
    join_info = []
    if all_refs:
        for k in range(num_edges):
            if rng.random() < valid_ratio and len(all_refs) >= 2:
                ref1 = rng.choice(all_refs)
                ref2 = rng.choice(all_refs)
                while ref1 == ref2 and len(all_refs) > 1:
                    ref2 = rng.choice(all_refs)
                from_ref = ref1[2]
                to_ref = ref2[2]
            else:
                from_ref = f"invalid_from_{k}"
                to_ref = f"invalid_to_{k}"
            join_info.append({
                "joins": [{
                    "from": from_ref,
                    "to": to_ref,
                    "relationship": rng.choice(["one-to-one", "one-to-many", "many-to-one"]),
                }]
            })
    return Descriptor(model, join_info)


_INSTANCE = DXDatasetDictionary.__new__(DXDatasetDictionary)

_CASE1 = make_descriptor(8, 150, 400, 1.0, 0)
_CASE2 = make_descriptor(12, 300, 1200, 1.0, 1)
_CASE3 = make_descriptor(20, 400, 2000, 1.0, 2)
_CASE4 = make_descriptor(50, 100, 1500, 1.0, 3)
_CASE5 = make_descriptor(5, 1600, 1000, 1.0, 4)
_CASE6 = make_descriptor(15, 300, 3000, 0.5, 5)
_CASE7 = make_descriptor(10, 400, 1500, 1.0, 6, duplicate_refs=True)
_CASE8 = make_descriptor(10, 500, 5000, 1.0, 7)


def checks():
    empty_model = {"entities": {}, "global_primary_key": {"entity": "", "field": ""}}
    empty_desc = Descriptor(empty_model, [])
    one_model = {
        "entities": {
            "e": {
                "name": "e",
                "fields": [{
                    "name": "f",
                    "type": "string",
                    "is_primary_key": True,
                    "references": None,
                    "description": "",
                    "is_optional": True,
                    "is_multi": False,
                }]
            }
        },
        "global_primary_key": {"entity": "e", "field": "f"},
    }
    one_desc = Descriptor(one_model, [])
    inv_desc = Descriptor(one_model, [{"joins": [{"from": "x", "to": "y", "relationship": "one-to-one"}]}])
    return [
        ("empty", lambda: (_INSTANCE, empty_desc)),
        ("one-field", lambda: (_INSTANCE, one_desc)),
        ("invalid-join", lambda: (_INSTANCE, inv_desc)),
    ]


def cases():
    return [
        ("case1-small", lambda: (_INSTANCE, _CASE1)),
        ("case2-medium", lambda: (_INSTANCE, _CASE2)),
        ("case3-large", lambda: (_INSTANCE, _CASE3)),
        ("case4-many-entities", lambda: (_INSTANCE, _CASE4)),
        ("case5-many-fields", lambda: (_INSTANCE, _CASE5)),
        ("case6-mixed-edges", lambda: (_INSTANCE, _CASE6)),
        ("case7-duplicate-refs", lambda: (_INSTANCE, _CASE7)),
        ("case8-dense-edges", lambda: (_INSTANCE, _CASE8)),
    ]
