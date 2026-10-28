import ast, json, sys
root = sys.argv[1]
bad = 0
defs = {}
def walk(node, prefix, path):
    for ch in ast.iter_child_nodes(node):
        if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
            q = prefix + ch.name
            defs.setdefault(path, set()).add(q)
            walk(ch, q + ".", path)
        elif isinstance(ch, ast.ClassDef):
            walk(ch, prefix + ch.name + ".", path)
        else:
            walk(ch, prefix, path)
for line in open(sys.argv[2]):
    rec = json.loads(line)
    for s in rec["suspicions"]:
        pass
    p, q = rec["unit"].split("::")
    if p not in defs:
        try:
            tree = ast.parse(open(root + "/" + p).read())
        except Exception as e:
            print("PARSE", p, e); bad += 1; continue
        defs[p] = set()
        walk(tree, "", p)
    if q not in defs[p]:
        print("MISSING", rec["unit"]); bad += 1
print("checked; problems:", bad)
