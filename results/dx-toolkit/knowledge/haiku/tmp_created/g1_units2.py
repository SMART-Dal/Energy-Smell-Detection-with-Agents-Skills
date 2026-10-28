import ast, sys
src = open(sys.argv[1], encoding='utf-8').read()
tree = ast.parse(src)
units = []
def walk(node, qual, parent_is_func):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            q = (qual + '.' + child.name) if qual else child.name
            # a function is a unit unless it is nested directly inside another function
            if not parent_is_func:
                units.append((q, child.lineno, child.end_lineno))
            walk(child, q, True)
        elif isinstance(child, ast.ClassDef):
            q = (qual + '.' + child.name) if qual else child.name
            walk(child, q, False)
        else:
            walk(child, qual, parent_is_func)
walk(tree, '', False)
for q, a, b in units:
    print(a, b, q)
print('TOTAL', len(units))
