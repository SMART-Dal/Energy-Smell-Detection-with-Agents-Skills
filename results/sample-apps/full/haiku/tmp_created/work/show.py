import ast, sys
# usage: show.py path::qualname [path::qualname ...]   (paths relative to repo root)
root = "/home/javad/energy-run/sample-apps/"
cache = {}
for spec in sys.argv[1:]:
    path, _, qual = spec.partition("::")
    if path not in cache:
        src = open(root + path, encoding="utf-8").read()
        cache[path] = (src.splitlines(), ast.parse(src))
    lines, tree = cache[path]
    parts = qual.split(".") if qual else []
    def walk(node, names):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if names and child.name == names[0]:
                    if len(names) == 1:
                        yield child
                    else:
                        yield from walk(child, names[1:])
                else:
                    yield from walk(child, names)
            else:
                yield from walk(child, names)
    found = list(walk(tree, parts)) if parts else [tree]
    if not found:
        print(f"!! not found: {spec}")
        continue
    for node in found:
        start = node.lineno
        end = node.end_lineno
        print(f"===== {path}::{qual}  (lines {start}-{end})")
        for i in range(start - 1, end):
            print(f"{i+1:5d}  {lines[i]}")
