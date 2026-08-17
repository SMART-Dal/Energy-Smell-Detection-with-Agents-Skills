def build(n):
    parts = []
    for i in range(n):
        parts.append("x" * 10)
    return len("".join(parts))

def workload():
    return build(400_000)
