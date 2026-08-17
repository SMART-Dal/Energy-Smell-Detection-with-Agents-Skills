def f(l: list):
    c = 0
    for x in l:
        c += x
    return c



import random

random.seed(42)
for i in range(3):
    a = f([random.randint(100_000, 1_000_000) for _ in range(5_000_000)])
