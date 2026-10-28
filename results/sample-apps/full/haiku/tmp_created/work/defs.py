import ast, sys
root = "/home/javad/energy-run/sample-apps/"
for path in sys.argv[1:]:
    tree = ast.parse(open(root + path, encoding="utf-8").read())
    def walk(node, prefix):
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = prefix + c.name
                if not isinstance(c, ast.ClassDef):
                    print(f"{path}::{q} {c.lineno}-{c.end_lineno}")
                walk(c, q + ".")
            else:
                walk(c, prefix)
    walk(tree, "")
