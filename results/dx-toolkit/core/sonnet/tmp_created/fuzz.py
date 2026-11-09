import json, random, sys, importlib, re, string as S
sys.path.insert(0,"src/python")
subs={json.loads(l)["id"]:json.loads(l) for l in open("submissions.jsonl")}
def load(id, modname, qual):
    mod=importlib.import_module(modname)
    ns=dict(mod.__dict__)
    code=list(subs[id]["changed"].values())[0]
    exec(code, ns)
    return getattr(mod, qual), ns[qual.split(".")[-1]]
random.seed(1)
# resolver
o,n=load("resolver-split","dxpy.utils.resolver","split_unescaped")
o2,n2=load("resolver-first-pos","dxpy.utils.resolver","get_first_pos_of_char")
o3,n3=load("resolver-last-pos","dxpy.utils.resolver","get_last_pos_of_char")
al=list("ab:/\\ =")
for _ in range(20000):
    s="".join(random.choice(al) for _ in range(random.randint(0,12)))
    for ch in ":/ =":
        for inc in (False,True):
            assert o(ch,s,inc)==n(ch,s,inc),(ch,s,inc)
        assert o2(ch,s)==n2(ch,s),(ch,s)
        assert o3(ch,s)==n3(ch,s)
print("resolver ok")
# flatten
o,n=load("pp-flatten","dxpy.utils.pretty_print","flatten_json_array")
import json as J
for _ in range(3000):
    d={"patterns":[random.choice(["a","b,c","x y"]) for _ in range(random.randint(0,6))],"k":[1,2,3][:random.randint(0,3)],"o":{"patterns":["p"]*random.randint(0,3)}}
    for ind in (2,4):
        t=J.dumps(d,indent=ind)
        for nl in ("\n","\r\n"):
            t2=t.replace("\n",nl)
            assert o(t2,"patterns")==n(t2,"patterns"),(t2,)
print("flatten ok")
# spell
o,n=load("spell-edits2","dxpy.utils.spelling_corrector","_known_edits2")
from dxpy.utils.spelling_corrector import _train
words=["find-data","find-apps","describe","upload","download","ls","cd","mkdir","run","watch","ssh","new","rm","mv","cp","Foo","a-b","tree","build","cat","head","env","pwd","help"]
nw=_train(words)
al2=list("abcdefghijklmnopqrstuvwxyz-A ")
for _ in range(1500):
    w="".join(random.choice(al2) for _ in range(random.randint(0,9)))
    if random.random()<0.6:
        base=random.choice(words); i=random.randrange(len(base)+1)
        w=base[:i]+random.choice(al2)+base[i:]
        if random.random()<.5: w=w[:-1]
    assert o(w,nw)==n(w,nw),(w)
print("spell ok")
# dxlog
import dxpy.dxlog as dl
h=dl.DXLogHandler.__new__(dl.DXLogHandler)
oo=dl.DXLogHandler.truncate_message
ns=dict(dl.__dict__); exec(subs["dxlog-bsearch"]["changed"][list(subs["dxlog-bsearch"]["changed"])[0]],ns)
nn=ns["truncate_message"]
for _ in range(60):
    chars="abé中\U0001F600\n\"\\\x01"
    m="".join(random.choice(chars) for _ in range(random.randint(0,12000)))
    assert oo(h,m)==nn(h,m)
print("dxlog ok")
