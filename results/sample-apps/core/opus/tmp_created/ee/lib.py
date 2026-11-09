import ast, textwrap, json
ROOT = "/home/javad/energy-run/sample-apps/"
def src(path, qual):
    text = open(ROOT + path).read()
    tree = ast.parse(text)
    parts = qual.split(".")
    node = tree
    for p in parts:
        for n in ast.iter_child_nodes(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == p:
                node = n; break
        else:
            raise KeyError(qual)
    lines = text.splitlines(True)
    start = (node.decorator_list[0].lineno if node.decorator_list else node.lineno) - 1
    s = "".join(lines[start:node.end_lineno])
    return textwrap.dedent(s.expandtabs(4)) if "\t" in s else textwrap.dedent(s)
def edit(path, qual, *pairs):
    s = src(path, qual)
    def ded(t):
        return "\n".join(l[4:] if l.startswith("    ") else l for l in t.split("\n"))
    for a, b in pairs:
        if "." in qual:
            a, b = ded(a), ded(b)
        assert s.count(a) == 1, (qual, a, s.count(a))
        s = s.replace(a, b)
    compile(s, "x", "exec")
    return s
