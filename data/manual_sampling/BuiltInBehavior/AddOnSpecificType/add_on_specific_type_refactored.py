class AB:
    def __init__(self, a):
        self.a = a

def add_on_specific_type(lst: list):
    res = 0
    for a in lst:
        if isinstance(a, AB):
            res += 1
    return res


lst = [AB(i) for i in range(1_000_000)]
for _ in range(150):
    a = add_on_specific_type(lst)
