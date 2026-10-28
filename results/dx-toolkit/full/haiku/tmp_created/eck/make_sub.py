import ast, json, sys, textwrap
# usage: make_sub.py SPEC.json  -> prints one submission line (JSON) to stdout
spec = json.load(open(sys.argv[1]))
path, qual = spec["unit"].split("::")
src = open(spec["repo"] + "/" + path).read()
lines = src.splitlines(keepends=True)
tree = ast.parse(src)
def find(node, prefix):
    for ch in ast.iter_child_nodes(node):
        if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            q = prefix + ch.name
            if isinstance(ch, ast.ClassDef):
                r = find(ch, q + ".")
                if r: return r
            elif q == qual:
                return ch
            else:
                r = find(ch, q + ".")
                if r: return r
    return None
node = find(tree, "")
assert node is not None, "unit not found"
start = min([d.lineno for d in node.decorator_list] + [node.lineno]) - 1
end = node.end_lineno
text = "".join(lines[start:end])
# column zero, as the submission format asks
text = textwrap.dedent(text)
for old, new, count in spec["edits"]:
    n = text.count(old)
    assert n == count, f"expected {count} of {old!r}, found {n}"
    text = text.replace(old, new)
ast.parse(text)  # must still be valid python
sub = {"id": spec["id"], "root_cause": spec["root_cause"], "unit": spec["unit"],
       "changed": {spec["unit"]: text}, "sole_caller_evidence": spec["evidence"],
       "notes": spec["notes"]}
print(json.dumps(sub))
