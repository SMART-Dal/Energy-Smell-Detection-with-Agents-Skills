import json, importlib, sys
sys.path.insert(0, "/tmp/energy-scratch")
D = {}
for m in ["dec_part1","dec_part2","dec_part3","dec_part4","dec_part5","dec_part6","dec_part7"]:
    mod = importlib.import_module(m)
    D.update(getattr(mod, "D"))
step1 = [json.loads(l) for l in open("/home/javad/energy-run/sample-apps/step1.jsonl")]
missing = []
for r in step1:
    for s in r["suspicions"]:
        if (r["unit"], s["label"]) not in D:
            missing.append((r["unit"], s["label"], s["root_cause"]))
print("missing decisions:", len(missing))
for m in missing: print("  ", m)
print("units:", len(step1))
