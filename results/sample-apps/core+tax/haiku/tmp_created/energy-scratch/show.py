import ast, sys
# usage: show.py path::qualname [path::qualname ...]  (prints source with line numbers)
for spec in sys.argv[1:]:
    path, qual = spec.split("::", 1)
    src = open(path, encoding="utf-8").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    node_found = None
    def walk(node, prefix):
        global node_found
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                if name == qual and not isinstance(child, ast.ClassDef):
                    node_found = child
                walk(child, name + ".")
            else:
                walk(child, prefix)
    walk(tree, "")
    print(f"===== {spec}")
    if node_found is None:
        print("  (not found)")
        continue
    start = node_found.lineno
    if node_found.decorator_list:
        start = min(d.lineno for d in node_found.decorator_list)
    for i in range(start, node_found.end_lineno + 1):
        print(f"{i:5d} {lines[i-1]}")
