import json,ast,sys
bad=[]
cache={}
def defs(path):
    if path in cache: return cache[path]
    t=ast.parse(open(path).read()); out={}
    def walk(n,pre):
        for c in ast.iter_child_nodes(n):
            if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef)):
                out[pre+c.name]=(c.lineno,c.end_lineno)
                # nested not units
            elif isinstance(c,ast.ClassDef):
                walk(c,pre+c.name+".")
            else:
                walk(c,pre)
    walk(t,"")
    cache[path]=out; return out
for l in open("step1.jsonl"):
    r=json.loads(l); p,q=r["unit"].split("::")
    d=defs(p)
    if q not in d: bad.append(r["unit"]); continue
    a,b=d[q]
    for s in r["suspicions"]:
        ls=s["lines"]
        if ls and not all(a-3<=x<=b+3 for x in ls): print("lines outside",r["unit"],s["label"],ls,(a,b))
print("BAD",bad)
