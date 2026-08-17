def build(n):
    s = ""
    for i in range(n):
        s += "x" * 10
    return len(s)

def workload():
    return build(400_000)
